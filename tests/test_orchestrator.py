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


def test_irreversible_failure_requires_review(tmp_path: Path):
    from workflow_ai.domain.models import StepResult

    class Connector:
        kind = WorkflowKind.PORTAL_A_SUBMISSION

        def run_step(self, step_name, job):
            if step_name == "submit":
                return StepResult(ok=False, message="confirmação não observada")
            return StepResult(ok=True)

    repo = SQLiteJobRepository(str(tmp_path / "uncertain.db"))
    kind = WorkflowKind.PORTAL_A_SUBMISSION
    orch = Orchestrator(
        repo,
        {kind: Connector()},
        approval_required=False,
    )
    job = orch.enqueue(
        Job(
            workflow=kind,
            payload=CaseRecord(
                process_id="P1",
                commitment_number="NE1",
                supplier_document="123",
            ),
        )
    )

    result = orch.execute(job)

    assert result.status == JobStatus.NEEDS_REVIEW
    assert result.current_step == "submit"
    assert "revisão humana" in result.error
