from workflow_ai.connectors.portal_b.config import PortalBConfig
from workflow_ai.connectors.portal_b.connector import PortalBConnector
from workflow_ai.connectors.portal_b.steps import PortalBSteps, _date_br, _money4
from workflow_ai.domain.models import CaseRecord


def test_portal_b_helpers():
    assert _money4("1234,5") == "1.234,5000"
    assert _date_br("2026-06-15 00:00:00") == "15/06/2026"


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
