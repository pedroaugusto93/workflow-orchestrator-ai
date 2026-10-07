from __future__ import annotations

from datetime import datetime, timezone

from workflow_ai.application.workflows import WORKFLOWS
from workflow_ai.domain.models import Job, JobStatus, StepStatus, WorkflowKind
from workflow_ai.ports.connectors import PortalConnector
from workflow_ai.ports.repositories import JobRepository


class DuplicateJobError(RuntimeError):
    pass


class ConnectorNotConfiguredError(RuntimeError):
    pass


class Orchestrator:
    def __init__(
        self,
        repo: JobRepository,
        connectors: dict[WorkflowKind, PortalConnector],
        *,
        approval_required: bool = True,
        allow_force_reprocess: bool = False,
    ) -> None:
        self.repo = repo
        self.connectors = connectors
        self.approval_required = approval_required
        self.allow_force_reprocess = allow_force_reprocess

    def enqueue(self, job: Job, *, force: bool = False) -> Job:
        previous = self.repo.find_existing_by_idempotency(job.idempotency_key)
        if previous:
            active = previous.status in {
                JobStatus.QUEUED,
                JobStatus.CLAIMED,
                JobStatus.RUNNING,
                JobStatus.WAITING_APPROVAL,
                JobStatus.NEEDS_REVIEW,
            }
            if active or not (force and self.allow_force_reprocess):
                raise DuplicateJobError(
                    "Job equivalente já existe: "
                    f"{previous.id} ({previous.status.value})"
                )
        return self.repo.create(job)

    def execute(self, job: Job) -> Job:
        connector = self.connectors.get(job.workflow)
        if connector is None:
            job.status = JobStatus.FAILED
            job.error = f"Conector não configurado para {job.workflow.value}"
            self._touch(job)
            self.repo.update(job)
            raise ConnectorNotConfiguredError(job.error)

        completed = self.repo.completed_steps(job.id)
        job.status = JobStatus.RUNNING
        self._touch(job)
        self.repo.update(job)

        for step in WORKFLOWS[job.workflow]:
            if step.name in completed:
                continue

            if step.irreversible and self.approval_required and not job.approved:
                job.status = JobStatus.WAITING_APPROVAL
                job.current_step = step.name
                self._touch(job)
                self.repo.record_step(
                    job.id, step.name, StepStatus.WAITING_APPROVAL,
                    "Aguardando aprovação para ação irreversível.",
                )
                self.repo.update(job)
                return job

            job.current_step = step.name
            self.repo.record_step(job.id, step.name, StepStatus.RUNNING)
            self._touch(job)
            self.repo.update(job)

            try:
                result = connector.run_step(step.name, job)
            except Exception as exc:
                return self._mark_step_failure(
                    job,
                    step.name,
                    f"{type(exc).__name__}: {exc}",
                    irreversible=step.irreversible,
                )

            if not result.ok:
                return self._mark_step_failure(
                    job,
                    step.name,
                    result.message or f"Falha na etapa {step.name}",
                    irreversible=step.irreversible,
                )

            if result.external_id:
                job.external_id = result.external_id

            self.repo.record_step(
                job.id, step.name, StepStatus.SUCCEEDED, result.message
            )

        job.status = JobStatus.SUCCEEDED
        job.current_step = ""
        job.error = ""
        self._touch(job)
        self.repo.update(job)
        return job

    def resolve_review(self, job_id: str, *, completed: bool) -> Job:
        job = self.repo.get(job_id)
        if not job:
            raise ValueError("Job não encontrado.")
        if job.status != JobStatus.NEEDS_REVIEW:
            raise ValueError("Job não está aguardando revisão humana.")

        irreversible = next(
            (
                step
                for step in WORKFLOWS[job.workflow]
                if step.name == job.current_step and step.irreversible
            ),
            None,
        )
        if irreversible is None:
            raise ValueError("Step em revisão não é uma ação irreversível conhecida.")

        if completed:
            self.repo.record_step(
                job.id,
                job.current_step,
                StepStatus.SUCCEEDED,
                "Conclusão confirmada manualmente após reconciliação.",
            )
            job.status = JobStatus.SUCCEEDED
            job.current_step = ""
            job.error = ""
        else:
            job.status = JobStatus.QUEUED
            job.approved = False
            job.current_step = ""
            job.error = ""

        self._touch(job)
        self.repo.update(job)
        return job

    def _mark_step_failure(
        self,
        job: Job,
        step_name: str,
        message: str,
        *,
        irreversible: bool,
    ) -> Job:
        if irreversible:
            job.status = JobStatus.NEEDS_REVIEW
            step_status = StepStatus.UNCERTAIN
            job.error = (
                "Resultado de ação irreversível precisa de revisão humana: "
                + message
            )
        else:
            job.status = JobStatus.FAILED
            step_status = StepStatus.FAILED
            job.error = message

        self.repo.record_step(
            job.id,
            step_name,
            step_status,
            job.error,
        )
        self._touch(job)
        self.repo.update(job)
        return job

    @staticmethod
    def _touch(job: Job) -> None:
        job.updated_at = datetime.now(timezone.utc)
