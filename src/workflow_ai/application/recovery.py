from __future__ import annotations

from datetime import datetime, timedelta, timezone

from workflow_ai.application.workflows import WORKFLOWS
from workflow_ai.domain.models import Job, JobStatus, StepStatus
from workflow_ai.ports.repositories import JobRepository


def is_irreversible(job: Job, step_name: str) -> bool:
    return any(
        step.name == step_name and step.irreversible
        for step in WORKFLOWS[job.workflow]
    )


def recover_stale_jobs(
    repo: JobRepository,
    *,
    stale_after_seconds: int,
    limit: int = 1000,
    now: datetime | None = None,
) -> list[str]:
    """Recover jobs abandoned by a crashed agent.

    Reversible work is safely requeued. A stale irreversible step is never
    retried automatically because the external side effect may already have
    happened.
    """
    if stale_after_seconds <= 0:
        return []

    current = now or datetime.now(timezone.utc)
    cutoff = current - timedelta(seconds=stale_after_seconds)
    recovered: list[str] = []

    for job in repo.list(limit=limit):
        if job.status not in {JobStatus.CLAIMED, JobStatus.RUNNING}:
            continue
        if job.updated_at > cutoff:
            continue

        if job.current_step and is_irreversible(job, job.current_step):
            job.status = JobStatus.NEEDS_REVIEW
            job.error = (
                "Agente deixou de atualizar o job durante uma ação irreversível. "
                "Verifique o portal antes de qualquer nova tentativa."
            )
            repo.record_step(
                job.id,
                job.current_step,
                StepStatus.UNCERTAIN,
                job.error,
            )
        else:
            job.status = JobStatus.QUEUED
            job.current_step = ""
            job.claimed_by = ""
            job.error = ""

        job.updated_at = current
        repo.update(job)
        recovered.append(job.id)

    return recovered
