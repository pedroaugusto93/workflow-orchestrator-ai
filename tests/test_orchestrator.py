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


def test_duplicate_active_job_is_blocked(tmp_path: Path):
    import pytest

    from workflow_ai.application.orchestrator import DuplicateJobError

    repo = SQLiteJobRepository(str(tmp_path / "duplicate.db"))
    kind = WorkflowKind.PORTAL_A_SUBMISSION
    orch = Orchestrator(
        repo,
        {kind: DemoConnector(kind)},
        allow_force_reprocess=True,
    )
    payload = CaseRecord(
        process_id="P1",
        commitment_number="NE1",
        supplier_document="123",
    )

    orch.enqueue(Job(workflow=kind, payload=payload))

    with pytest.raises(DuplicateJobError):
        orch.enqueue(Job(workflow=kind, payload=payload), force=True)
