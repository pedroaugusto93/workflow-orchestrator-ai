from __future__ import annotations

from dataclasses import dataclass

from workflow_ai.domain.models import WorkflowKind


@dataclass(frozen=True, slots=True)
class WorkflowStep:
    name: str
    irreversible: bool = False


WORKFLOWS: dict[WorkflowKind, tuple[WorkflowStep, ...]] = {
    WorkflowKind.PORTAL_A_SUBMISSION: (
        WorkflowStep("basic_data"),
        WorkflowStep("items"),
        WorkflowStep("documents"),
        WorkflowStep("commitments"),
        WorkflowStep("verify"),
        WorkflowStep("submit", irreversible=True),
    ),
    WorkflowKind.PORTAL_B_PUBLICATION: (
        WorkflowStep("locate"),
        WorkflowStep("basic_data"),
        WorkflowStep("additional_data"),
        WorkflowStep("items"),
        WorkflowStep("attachments"),
        WorkflowStep("responsibles"),
        WorkflowStep("publish", irreversible=True),
    ),
}
