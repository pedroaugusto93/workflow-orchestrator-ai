from pathlib import Path

from workflow_ai.domain.models import CaseRecord, ContractLineItem, Job, WorkflowKind
from workflow_ai.infrastructure.sqlite_repo import SQLiteJobRepository


def test_sqlite_round_trip_preserves_multi_item_case(tmp_path: Path):
    repo = SQLiteJobRepository(str(tmp_path / "multi.db"))
    job = Job(
        workflow=WorkflowKind.PORTAL_B_PUBLICATION,
        payload=CaseRecord(
            process_id="P1",
            title="Curso",
            items=[
                ContractLineItem(supplier_document="11122233344", value="10"),
                ContractLineItem(supplier_document="55566677788", value="20"),
            ],
        ),
    )

    repo.create(job)
    loaded = repo.get(job.id)

    assert loaded is not None
    assert loaded.payload.process_id == "P1"
    assert len(loaded.payload.items) == 2
    assert loaded.payload.items[1].supplier_document == "55566677788"
