from __future__ import annotations

from dataclasses import dataclass, field, fields
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
    NEEDS_REVIEW = "needs_review"
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
    UNCERTAIN = "uncertain"


@dataclass(slots=True)
class ContractLineItem:
    """One commercial/result line that belongs to a process-level case."""

    item_number: str = ""
    title: str = ""
    description: str = ""
    supplier_document: str = ""
    supplier_name: str = ""
    value: str = ""
    unit_value: str = ""
    quantity: str = "1"
    alias: str = ""
    extras: dict[str, Any] = field(default_factory=dict)

    @property
    def effective_value(self) -> str:
        return self.unit_value or self.value

    @property
    def effective_alias(self) -> str:
        candidate = (self.alias or self.supplier_name or self.item_number or "Item").strip()
        return candidate[:20]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ContractLineItem":
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass(slots=True)
class CaseRecord:
    """Process-level aggregate used by both workflows."""

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
    commitment_date: str = ""
    commitment_number: str = ""
    commitment_value: str = ""
    commitment_unit_code: str = ""
    item_number: str = "1"
    quantity: str = "1"
    source_link: str = ""
    file_path: str = ""
    responsible_document: str = ""
    responsible_email: str = ""
    authority_name: str = ""
    authority_document: str = ""
    authority_email: str = ""
    act_date: str = ""
    ordering_officer: str = ""
    ordering_officer_document: str = ""
    items: list[ContractLineItem] = field(default_factory=list)
    extras: dict[str, Any] = field(default_factory=dict)

    def idempotency_key(self, workflow: WorkflowKind) -> str:
        if workflow == WorkflowKind.PORTAL_B_PUBLICATION:
            parts = [workflow.value, self._canon(self.process_id)]
        else:
            parts = [
                workflow.value,
                self._canon(self.process_id),
                self._canon(self.commitment_number),
                self._canon(self.supplier_document),
            ]
        return sha256("|".join(parts).encode("utf-8")).hexdigest()

    def effective_items(self) -> list[ContractLineItem]:
        if self.items:
            return self.items
        return [
            ContractLineItem(
                item_number=self.item_number,
                title=self.title,
                description=self.object_text,
                supplier_document=self.supplier_document,
                supplier_name=self.supplier_name,
                value=self.value,
                unit_value=self.value,
                quantity=self.quantity,
            )
        ]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CaseRecord":
        payload = dict(data)
        payload["items"] = [
            item if isinstance(item, ContractLineItem) else ContractLineItem.from_dict(item)
            for item in payload.get("items", [])
        ]
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in payload.items() if k in known})

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
