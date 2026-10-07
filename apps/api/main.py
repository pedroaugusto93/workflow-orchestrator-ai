from __future__ import annotations

import secrets
from pathlib import Path

from fastapi import Depends, FastAPI, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from workflow_ai.application.orchestrator import DuplicateJobError, Orchestrator
from workflow_ai.domain.models import CaseRecord, Job, JobStatus, StepStatus, WorkflowKind
from workflow_ai.infrastructure.serialization import job_to_dict
from workflow_ai.infrastructure.settings import settings
from workflow_ai.infrastructure.sqlite_repo import SQLiteJobRepository

BASE = Path(__file__).resolve().parent
app = FastAPI(title="Workflow Orchestrator AI", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
templates = Jinja2Templates(directory=BASE / "templates")
security = HTTPBasic()

repo = SQLiteJobRepository(settings.database_url.removeprefix("sqlite:///"))
orchestrator = Orchestrator(
    repo,
    {},
    approval_required=settings.approval_required,
    allow_force_reprocess=settings.allow_force_reprocess,
)


def require_user(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    ok_user = secrets.compare_digest(credentials.username, settings.app_username)
    ok_pass = secrets.compare_digest(credentials.password, settings.app_password)
    if not (ok_user and ok_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


def require_agent(request: Request) -> None:
    token = request.headers.get("X-Agent-Token", "")
    if not secrets.compare_digest(token, settings.agent_token):
        raise HTTPException(status_code=401, detail="Agente não autorizado")


@app.middleware("http")
async def privacy_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Robots-Tag"] = "noindex, nofollow, noarchive"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@app.get("/robots.txt", response_class=PlainTextResponse, include_in_schema=False)
def robots():
    return "User-agent: *\nDisallow: /\n"


@app.get("/health", response_class=PlainTextResponse)
def health():
    return "ok"


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, _: str = Depends(require_user)):
    jobs = repo.list(limit=100)
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={"jobs": jobs, "workflows": list(WorkflowKind)},
    )


@app.post("/jobs")
def create_job(
    process_id: str = Form(...),
    workflow: WorkflowKind = Form(...),
    title: str = Form(""),
    supplier_document: str = Form(""),
    commitment_number: str = Form(""),
    _: str = Depends(require_user),
):
    job = Job(
        workflow=workflow,
        payload=CaseRecord(
            process_id=process_id.strip(),
            title=title.strip(),
            supplier_document=supplier_document.strip(),
            commitment_number=commitment_number.strip(),
        ),
    )
    try:
        orchestrator.enqueue(job)
    except DuplicateJobError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return RedirectResponse("/", status_code=303)


@app.post("/jobs/{job_id}/approve")
def approve_job(job_id: str, _: str = Depends(require_user)):
    job = repo.approve(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    return RedirectResponse("/", status_code=303)


@app.get("/api/agent/next")
def agent_next(request: Request, agent_id: str):
    require_agent(request)
    job = repo.claim_next(agent_id)
    return {"job": job_to_dict(job) if job else None}


@app.get("/api/agent/jobs/{job_id}")
def agent_get_job(job_id: str, request: Request):
    require_agent(request)
    job = repo.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    return {"job": job_to_dict(job)}


class AgentState(BaseModel):
    status: JobStatus
    current_step: str = ""
    external_id: str = ""
    error: str = ""


class AgentStep(BaseModel):
    step_name: str
    status: StepStatus
    message: str = ""


def _apply_agent_state(job_id: str, body: AgentState) -> None:
    job = repo.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    job.status = body.status
    job.current_step = body.current_step
    job.external_id = body.external_id
    job.error = body.error
    repo.update(job)


@app.post("/api/agent/jobs/{job_id}/state")
def agent_state(job_id: str, body: AgentState, request: Request):
    require_agent(request)
    _apply_agent_state(job_id, body)
    return {"ok": True}


@app.post("/api/agent/jobs/{job_id}/result")
def agent_result(job_id: str, body: AgentState, request: Request):
    """Backward-compatible alias for older agents."""
    require_agent(request)
    _apply_agent_state(job_id, body)
    return {"ok": True}


@app.post("/api/agent/jobs/{job_id}/steps")
def agent_step(job_id: str, body: AgentStep, request: Request):
    require_agent(request)
    if not repo.get(job_id):
        raise HTTPException(status_code=404, detail="Job não encontrado")
    repo.record_step(
        job_id,
        body.step_name,
        body.status,
        body.message,
    )
    return {"ok": True}


@app.get("/api/agent/jobs/{job_id}/completed-steps")
def agent_completed_steps(job_id: str, request: Request):
    require_agent(request)
    if not repo.get(job_id):
        raise HTTPException(status_code=404, detail="Job não encontrado")
    return {"steps": sorted(repo.completed_steps(job_id))}


def main() -> None:
    import uvicorn

    uvicorn.run(
        "apps.api.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=False,
    )


if __name__ == "__main__":
    main()
