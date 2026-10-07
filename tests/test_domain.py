from workflow_ai.domain.models import CaseRecord, ContractLineItem, WorkflowKind


def test_idempotency_is_stable_for_formatting():
    a = CaseRecord(process_id="20.22-001", commitment_number="2026NE001", supplier_document="12.345")
    b = CaseRecord(process_id="20 22 001", commitment_number="2026-NE-001", supplier_document="12 345")
    assert a.idempotency_key(WorkflowKind.PORTAL_A_SUBMISSION) == b.idempotency_key(
        WorkflowKind.PORTAL_A_SUBMISSION
    )


def test_workflows_have_different_keys():
    r = CaseRecord(process_id="P1")
    assert r.idempotency_key(WorkflowKind.PORTAL_A_SUBMISSION) != r.idempotency_key(
        WorkflowKind.PORTAL_B_PUBLICATION
    )


def test_portal_b_idempotency_is_process_level():
    a = CaseRecord(
        process_id="P-001",
        supplier_document="111",
        items=[ContractLineItem(supplier_document="111", value="10")],
    )
    b = CaseRecord(
        process_id="P001",
        supplier_document="999",
        items=[ContractLineItem(supplier_document="999", value="20")],
    )
    assert a.idempotency_key(WorkflowKind.PORTAL_B_PUBLICATION) == b.idempotency_key(
        WorkflowKind.PORTAL_B_PUBLICATION
    )


def test_case_record_round_trip_restores_typed_items():
    original = CaseRecord(
        process_id="P1",
        items=[
            ContractLineItem(
                item_number="1",
                supplier_document="11122233344",
                supplier_name="Fornecedor A",
                value="10,00",
            ),
            ContractLineItem(
                item_number="2",
                supplier_document="55566677788",
                supplier_name="Fornecedor B",
                value="20,00",
            ),
        ],
    )
    rebuilt = CaseRecord.from_dict(
        {
            "process_id": original.process_id,
            "items": [
                {
                    "item_number": item.item_number,
                    "supplier_document": item.supplier_document,
                    "supplier_name": item.supplier_name,
                    "value": item.value,
                }
                for item in original.items
            ],
        }
    )
    assert len(rebuilt.items) == 2
    assert isinstance(rebuilt.items[0], ContractLineItem)
    assert rebuilt.items[1].supplier_name == "Fornecedor B"
