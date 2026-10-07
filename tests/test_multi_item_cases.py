from pathlib import Path

from workflow_ai.domain.models import CaseRecord, ContractLineItem, Job, WorkflowKind
from workflow_ai.importers.excel import consolidate_by_process
from workflow_ai.infrastructure.sqlite_repo import SQLiteJobRepository


def test_consolidate_rows_into_one_case():
    rows = [
        CaseRecord(
            process_id="P1",
            title="Curso",
            object_text="Objeto",
            start_date="01/01/2026",
            commitment_date="31/01/2026",
            supplier_document="111",
            supplier_name="Fornecedor A",
            value="10",
            item_number="1",
        ),
        CaseRecord(
            process_id="P1",
            title="Curso",
            object_text="Objeto",
            start_date="01/01/2026",
            commitment_date="31/01/2026",
            supplier_document="222",
            supplier_name="Fornecedor B",
            value="20",
            item_number="2",
        ),
    ]
    cases = consolidate_by_process(rows)
    assert len(cases) == 1
    assert len(cases[0].items) == 2
    assert cases[0].items[1].supplier_name == "Fornecedor B"


def test_sqlite_roundtrip_preserves_nested_items(tmp_path: Path):
    repo = SQLiteJobRepository(str(tmp_path / "jobs.db"))
    case = CaseRecord(
        process_id="P1",
        items=[ContractLineItem(item_number="1", supplier_document="111", value="10")],
    )
    job = repo.create(Job(workflow=WorkflowKind.PORTAL_B_PUBLICATION, payload=case))
    loaded = repo.get(job.id)
    assert loaded is not None
    assert isinstance(loaded.payload.items[0], ContractLineItem)
    assert loaded.payload.items[0].supplier_document == "111"
