from workflow_ai.domain.models import CaseRecord, WorkflowKind


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
