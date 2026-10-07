from __future__ import annotations

import importlib
from dataclasses import dataclass

from workflow_ai.domain.models import CaseRecord, StepResult, WorkflowKind
from workflow_ai.ports.connectors import PortalConnector


@dataclass(slots=True)
class DemoConnector:
    kind: WorkflowKind

    def run_step(self, step_name: str, record: CaseRecord) -> StepResult:
        external = ""
        if step_name in {"basic_data", "locate"}:
            external = f"DEMO-{record.process_id[-8:]}" if record.process_id else "DEMO"
        return StepResult(ok=True, message=f"Etapa demo concluída: {step_name}", external_id=external)


def load_private_connectors(package_name: str) -> dict[WorkflowKind, PortalConnector]:
    """
    Loads a local connector pack ignored by Git.

    Expected module contract:
        def build_connectors() -> dict[WorkflowKind, PortalConnector]
    """
    try:
        module = importlib.import_module(package_name)
    except ModuleNotFoundError:
        return {}
    builder = getattr(module, "build_connectors", None)
    if not callable(builder):
        return {}
    return builder()


def build_connector_registry(package_name: str, *, development: bool = False):
    connectors = load_private_connectors(package_name)
    if connectors or not development:
        return connectors
    return {
        WorkflowKind.PORTAL_A_SUBMISSION: DemoConnector(WorkflowKind.PORTAL_A_SUBMISSION),
        WorkflowKind.PORTAL_B_PUBLICATION: DemoConnector(WorkflowKind.PORTAL_B_PUBLICATION),
    }
