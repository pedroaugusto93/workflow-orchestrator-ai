from __future__ import annotations

from typing import Protocol

from workflow_ai.domain.models import Job, StepResult, WorkflowKind


class PortalConnector(Protocol):
    kind: WorkflowKind

    def run_step(self, step_name: str, job: Job) -> StepResult:
        """Execute one workflow step using the whole job context."""
        ...
