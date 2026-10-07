from pathlib import Path

from workflow_ai.application.workflows import WORKFLOWS
from workflow_ai.connectors.portal_b.config import PortalBConfig
from workflow_ai.connectors.portal_b.connector import PortalBConnector
from workflow_ai.connectors.portal_b.steps import PortalBSteps, _date_br, _date_input, _money4
from workflow_ai.domain.models import CaseRecord, ContractLineItem, Job, WorkflowKind
from workflow_ai.infrastructure.sqlite_repo import SQLiteJobRepository


def test_portal_b_helpers():
    assert _money4("1234,5") == "1.234,5000"
    assert _date_br("2026-06-15 00:00:00") == "15/06/2026"
    assert _date_input("2026-06-15", month_first=False) == "15/06/2026"
    assert _date_input("2026-06-15", month_first=True) == "06/15/2026"


def test_portal_b_connector_builds_with_slots():
    class Browser:
        pass

    connector = PortalBConnector(Browser(), PortalBConfig())
    assert connector.steps is not None


def test_initial_data_requires_private_justification_before_browser():
    class Browser:
        pass

    steps = PortalBSteps(Browser(), PortalBConfig(justification=""))
    result = steps.initial_data(
        CaseRecord(
            process_id="P1",
            title="T",
            object_text="O",
            start_date="01/01/2026",
            end_date="02/01/2026",
        )
    )
    assert not result.ok
    assert "justification" in result.message


def test_portal_b_workflow_starts_with_initial_data_and_ends_irreversible():
    steps = WORKFLOWS[WorkflowKind.PORTAL_B_PUBLICATION]
    assert steps[0].name == "initial_data"
    assert [step.name for step in steps] == [
        "initial_data",
        "locate",
        "basic_data",
        "additional_data",
        "items",
        "attachments",
        "responsibles",
        "publish",
    ]
    assert steps[-1].irreversible is True


def test_sqlite_roundtrip_preserves_multiple_items(tmp_path: Path):
    repo = SQLiteJobRepository(str(tmp_path / "multi.db"))
    case = CaseRecord(
        process_id="P-1",
        title="Teste",
        items=[
            ContractLineItem(
                item_number="1",
                supplier_document="11111111111",
                supplier_name="Fornecedor 1",
                value="10",
            ),
            ContractLineItem(
                item_number="2",
                supplier_document="22222222222",
                supplier_name="Fornecedor 2",
                value="20",
            ),
        ],
    )
    job = repo.create(Job(workflow=WorkflowKind.PORTAL_B_PUBLICATION, payload=case))
    loaded = repo.get(job.id)
    assert loaded is not None
    assert len(loaded.payload.items) == 2
    assert loaded.payload.items[0].supplier_name == "Fornecedor 1"
    assert loaded.payload.items[1].value == "20"


def test_portal_b_config_reads_environment(monkeypatch):
    monkeypatch.setenv("PORTAL_B_URL", "https://example.test/portal")
    monkeypatch.setenv("PORTAL_B_JUSTIFICATION", "Justificativa local")
    cfg = PortalBConfig()
    assert cfg.target_url == "https://example.test/portal"
    assert cfg.justification == "Justificativa local"
