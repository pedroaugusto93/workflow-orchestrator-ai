from __future__ import annotations

import json

import httpx

from workflow_ai.domain.models import CaseRecord, Job, JobStatus, StepStatus, WorkflowKind
from workflow_ai.infrastructure.http_repo import HttpJobRepository
from workflow_ai.infrastructure.serialization import job_from_dict, job_to_dict


def test_job_serialization_roundtrip():
    original = Job(
        workflow=WorkflowKind.PORTAL_B_PUBLICATION,
        payload=CaseRecord(process_id="P1"),
        status=JobStatus.CLAIMED,
        approved=True,
        claimed_by="agent-1",
    )

    restored = job_from_dict(job_to_dict(original))

    assert restored.id == original.id
    assert restored.workflow == original.workflow
    assert restored.payload.process_id == "P1"
    assert restored.approved is True
    assert restored.claimed_by == "agent-1"


def test_http_repository_agent_operations():
    job = Job(
        workflow=WorkflowKind.PORTAL_A_SUBMISSION,
        payload=CaseRecord(process_id="P1"),
        status=JobStatus.CLAIMED,
    )
    calls: list[tuple[str, str, dict | None]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content) if request.content else None
        calls.append((request.method, request.url.path, body))

        if request.url.path == "/api/agent/next":
            return httpx.Response(200, json={"job": job_to_dict(job)})
        if request.url.path.endswith("/completed-steps"):
            return httpx.Response(200, json={"steps": ["prepare", "basic_data"]})
        if request.url.path.endswith("/state"):
            return httpx.Response(200, json={"ok": True})
        if request.url.path.endswith("/steps"):
            return httpx.Response(200, json={"ok": True})
        if request.url.path == f"/api/agent/jobs/{job.id}":
            return httpx.Response(200, json={"job": job_to_dict(job)})
        return httpx.Response(404)

    client = httpx.Client(
        base_url="https://example.test",
        headers={"X-Agent-Token": "token"},
        transport=httpx.MockTransport(handler),
    )
    repo = HttpJobRepository(
        "https://example.test",
        "token",
        client=client,
    )

    claimed = repo.claim_next("agent-1")
    assert claimed is not None
    assert claimed.id == job.id
    assert repo.completed_steps(job.id) == {"prepare", "basic_data"}

    claimed.status = JobStatus.RUNNING
    repo.update(claimed)
    repo.record_step(job.id, "items", StepStatus.SUCCEEDED, "ok")

    assert any(path.endswith("/state") for _, path, _ in calls)
    assert any(path.endswith("/steps") for _, path, _ in calls)
