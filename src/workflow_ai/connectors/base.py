from __future__ import annotations

from abc import ABC, abstractmethod

from workflow_ai.domain.models import CaseRecord, StepResult, WorkflowKind


class BasePortalConnector(ABC):
    kind: WorkflowKind

    @abstractmethod
    def run_step(self, step_name: str, record: CaseRecord) -> StepResult:
        raise NotImplementedError

    @staticmethod
    def require(record: CaseRecord, *fields: str) -> None:
        missing = [name for name in fields if not str(getattr(record, name, "") or "").strip()]
        if missing:
            raise ValueError(f"Campos obrigatórios ausentes: {', '.join(missing)}")
