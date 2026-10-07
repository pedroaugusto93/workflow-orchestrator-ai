from pathlib import Path

from workflow_ai.application.orchestrator import Orchestrator
from workflow_ai.domain.models import CaseRecord, Job, JobStatus, WorkflowKind
from workflow_ai.infrastructure.connectors import DemoConnector
from workflow_ai.infrastructure.sqlite_repo import SQLiteJobRepository


def test_resume_waits_for_approval(tmp_path: Path):
    repo = SQLiteJobRepository(str(tmp_path / "test.db"))
    kind = WorkflowKind.PORTAL_A_SUBMISSION
    connector = DemoConnector(kind)
    orch = Orchestrator(repo, {kind: connector}, approval_required=True)
    job = orch.enqueue(Job(workflow=kind, payload=CaseRecord(process_id="P1")))

    result = orch.execute(job)
    assert result.status == JobStatus.WAITING_APPROVAL
    assert result.current_step == "submit"

    repo.approve(job.id)
    approved = repo.get(job.id)
    result = orch.execute(approved)
    assert result.status == JobStatus.SUCCEEDED
