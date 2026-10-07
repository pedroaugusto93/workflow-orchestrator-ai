from __future__ import annotations

from typing import Protocol

from workflow_ai.domain.models import CaseRecord, StepResult, WorkflowKind


class PortalConnector(Protocol):
    kind: WorkflowKind

    def run_step(self, step_name: str, record: CaseRecord) -> StepResult:
        """Execute one idempotent workflow step."""
        ...
