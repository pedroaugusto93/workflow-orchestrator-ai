from workflow_ai.domain.models import CaseRecord
from workflow_ai.importers.excel import consolidate_by_process


def test_consolidate_rows_into_one_process_with_multiple_items():
    rows = [
        CaseRecord(
            process_id="P1",
            title="Curso",
            object_text="Objeto comum",
            start_date="01/10/2026",
            commitment_date="31/10/2026",
            supplier_document="11122233344",
            supplier_name="Fornecedor A",
            value="100",
            source_link="https://example.invalid/process",
            file_path="ato.pdf",
            responsible_document="11111111111",
            authority_document="22222222222",
        ),
        CaseRecord(
            process_id="P1",
            title="Curso",
            object_text="Objeto comum",
            start_date="01/10/2026",
            commitment_date="31/10/2026",
            supplier_document="55566677788",
            supplier_name="Fornecedor B",
            value="200",
            source_link="https://example.invalid/process",
            file_path="ato.pdf",
            responsible_document="11111111111",
            authority_document="22222222222",
        ),
    ]

    cases = consolidate_by_process(rows)

    assert len(cases) == 1
    assert cases[0].process_id == "P1"
    assert len(cases[0].items) == 2
    assert cases[0].items[0].supplier_name == "Fornecedor A"
    assert cases[0].items[1].supplier_name == "Fornecedor B"


def test_consolidate_rejects_conflicting_process_metadata():
    rows = [
        CaseRecord(process_id="P1", title="A", source_link="link-1"),
        CaseRecord(process_id="P1", title="B", source_link="link-2"),
    ]

    import pytest

    with pytest.raises(ValueError):
        consolidate_by_process(rows)
