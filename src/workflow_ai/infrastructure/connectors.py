from __future__ import annotations

import importlib
from dataclasses import dataclass

from workflow_ai.connectors.portal_a import PortalAConfig, PortalAConnector
from workflow_ai.domain.models import Job, StepResult, WorkflowKind
from workflow_ai.infrastructure.settings import settings
from workflow_ai.ports.connectors import PortalConnector


@dataclass(slots=True)
class DemoConnector:
    kind: WorkflowKind

    def run_step(self, step_name: str, job: Job) -> StepResult:
        record = job.payload
        external = ""
        if step_name in {"basic_data", "locate"}:
            external = f"DEMO-{record.process_id[-8:]}" if record.process_id else "DEMO"
        return StepResult(ok=True, message=f"Etapa demo concluída: {step_name}", external_id=external)


def load_private_connectors(package_name: str) -> dict[WorkflowKind, PortalConnector]:
    try:
        module = importlib.import_module(package_name)
    except ModuleNotFoundError:
        return {}
    builder = getattr(module, "build_connectors", None)
    if not callable(builder):
        return {}
    return builder()


def build_connector_registry(package_name: str, *, development: bool = False):
    """Build connectors only on the local execution agent.

    The hosted API does not need browser connectors to enqueue jobs.
    """
    connectors = load_private_connectors(package_name)
    if connectors:
        return connectors

    portal_a = PortalAConfig()
    if portal_a.create_url:
        from workflow_ai.infrastructure.browser import attach_to_chrome
        from workflow_ai.infrastructure.selenium_browser import SeleniumBrowser

        driver = attach_to_chrome(settings.chrome_debug_host, settings.chrome_debug_port)
        browser = SeleniumBrowser(driver)
        connectors[WorkflowKind.PORTAL_A_SUBMISSION] = PortalAConnector(browser, portal_a)

    if development and WorkflowKind.PORTAL_A_SUBMISSION not in connectors:
        connectors[WorkflowKind.PORTAL_A_SUBMISSION] = DemoConnector(WorkflowKind.PORTAL_A_SUBMISSION)
    if development and WorkflowKind.PORTAL_B_PUBLICATION not in connectors:
        connectors[WorkflowKind.PORTAL_B_PUBLICATION] = DemoConnector(WorkflowKind.PORTAL_B_PUBLICATION)
    return connectors
