from __future__ import annotations

from dataclasses import dataclass, field

from workflow_ai.connectors.portal_a.config import PortalAConfig
from workflow_ai.connectors.portal_a.steps import PortalASteps
from workflow_ai.domain.models import Job, StepResult, WorkflowKind
from workflow_ai.ports.browser import BrowserPort


@dataclass(slots=True)
class PortalAConnector:
    browser: BrowserPort
    config: PortalAConfig
    kind: WorkflowKind = WorkflowKind.PORTAL_A_SUBMISSION
    steps: PortalASteps = field(init=False)

    def __post_init__(self) -> None:
        self.steps = PortalASteps(self.browser, self.config)

    def run_step(self, step_name: str, job: Job) -> StepResult:
        if step_name == "prepare":
            return self.steps.prepare(job.payload, job.external_id)
        handler = getattr(self.steps, step_name, None)
        if not callable(handler):
            return StepResult(ok=False, message=f"Etapa desconhecida: {step_name}")
        return handler(job.payload)
