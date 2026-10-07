from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from hashlib import sha256
from typing import Any
from uuid import uuid4


class WorkflowKind(StrEnum):
    PORTAL_A_SUBMISSION = "portal_a_submission"
    PORTAL_B_PUBLICATION = "portal_b_publication"


class JobStatus(StrEnum):
    QUEUED = "queued"
    CLAIMED = "claimed"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"
    WAITING_APPROVAL = "waiting_approval"


@dataclass(slots=True)
class CaseRecord:
    process_id: str
    title: str = ""
    object_text: str = ""
    supplier_document: str = ""
    supplier_name: str = ""
    value: str = ""
    execution_term: str = ""
    start_date: str = ""
    end_date: str = ""
    commitment_year: str = ""
    commitment_number: str = ""
    commitment_value: str = ""
    source_link: str = ""
    file_path: str = ""
    responsible_document: str = ""
    responsible_email: str = ""
    authority_name: str = ""
    authority_document: str = ""
    authority_email: str = ""
    act_date: str = ""
    ordering_officer: str = ""
    extras: dict[str, Any] = field(default_factory=dict)

    def idempotency_key(self, workflow: WorkflowKind) -> str:
        raw = "|".join(
            [
                workflow.value,
                self._canon(self.process_id),
                self._canon(self.commitment_number),
                self._canon(self.supplier_document),
            ]
        )
        return sha256(raw.encode("utf-8")).hexdigest()

    @staticmethod
    def _canon(value: str) -> str:
        return "".join(ch for ch in str(value or "") if ch.isalnum()).upper()


@dataclass(slots=True)
class Job:
    workflow: WorkflowKind
    payload: CaseRecord
    id: str = field(default_factory=lambda: str(uuid4()))
    status: JobStatus = JobStatus.QUEUED
    current_step: str = ""
    external_id: str = ""
    error: str = ""
    approved: bool = False
    claimed_by: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def idempotency_key(self) -> str:
        return self.payload.idempotency_key(self.workflow)


@dataclass(slots=True)
class StepResult:
    ok: bool
    message: str = ""
    external_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
