from pathlib import Path

from workflow_ai.connectors.portal_a.config import PortalAConfig
from workflow_ai.connectors.portal_a.steps import PortalASteps, _date_br, _money
from workflow_ai.domain.models import CaseRecord


def test_money_and_date_normalization():
    assert _money("1234,5", 2) == "1.234,50"
    assert _money("1234.5", 4) == "1.234,5000"
    assert _date_br("2026-06-15 00:00:00") == "15/06/2026"


def test_document_required_fails_before_browser(tmp_path: Path):
    class Browser:
        pass

    step = PortalASteps(Browser(), PortalAConfig(document_required=True))
    result = step.documents(CaseRecord(process_id="P1", file_path=""))
    assert not result.ok
    assert "obrigatório" in result.message


def test_connector_builds_with_slots():
    from workflow_ai.connectors.portal_a.connector import PortalAConnector

    class Browser:
        pass

    connector = PortalAConnector(Browser(), PortalAConfig())
    assert connector.steps is not None
