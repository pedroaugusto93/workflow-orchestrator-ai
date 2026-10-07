from __future__ import annotations

from dataclasses import dataclass, field

from workflow_ai.connectors.portal_b.config import PortalBConfig
from workflow_ai.connectors.portal_b.steps import PortalBSteps
from workflow_ai.domain.models import Job, StepResult, WorkflowKind
from workflow_ai.ports.browser import BrowserPort


@dataclass(slots=True)
class PortalBConnector:
    browser: BrowserPort
    config: PortalBConfig
    kind: WorkflowKind = WorkflowKind.PORTAL_B_PUBLICATION
    steps: PortalBSteps = field(init=False)

    def __post_init__(self) -> None:
        self.steps = PortalBSteps(self.browser, self.config)

    def run_step(self, step_name: str, job: Job) -> StepResult:
        if step_name not in {"initial_data", "locate"}:
            self.steps.ensure_edit_context(job.payload)
        handler = getattr(self.steps, step_name, None)
        if not callable(handler):
            return StepResult(ok=False, message=f"Etapa desconhecida: {step_name}")
        return handler(job.payload)
