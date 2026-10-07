from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Any

from workflow_ai.domain.models import CaseRecord, Job, JobStatus, WorkflowKind


def job_to_dict(job: Job) -> dict[str, Any]:
    data = asdict(job)
    data["workflow"] = job.workflow.value
    data["status"] = job.status.value
    data["created_at"] = job.created_at.isoformat()
    data["updated_at"] = job.updated_at.isoformat()
    return data


def job_from_dict(data: dict[str, Any]) -> Job:
    return Job(
        id=str(data["id"]),
        workflow=WorkflowKind(data["workflow"]),
        payload=CaseRecord.from_dict(dict(data["payload"])),
        status=JobStatus(data["status"]),
        current_step=str(data.get("current_step") or ""),
        external_id=str(data.get("external_id") or ""),
        error=str(data.get("error") or ""),
        approved=bool(data.get("approved", False)),
        claimed_by=str(data.get("claimed_by") or ""),
        created_at=_dt(data.get("created_at")),
        updated_at=_dt(data.get("updated_at")),
    )


def _dt(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))
