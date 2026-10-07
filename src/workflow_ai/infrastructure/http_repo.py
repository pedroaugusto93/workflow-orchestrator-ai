from __future__ import annotations

from typing import Any

import httpx

from workflow_ai.domain.models import Job, StepStatus
from workflow_ai.infrastructure.serialization import job_from_dict


class HttpJobRepository:
    """JobRepository adapter used by a Windows agent against a hosted API."""

    def __init__(
        self,
        base_url: str,
        token: str,
        *,
        timeout: float = 30.0,
        client: httpx.Client | None = None,
    ) -> None:
        if not base_url.strip():
            raise ValueError("URL da API remota não configurada.")
        if not token.strip():
            raise ValueError("Token do agente não configurado.")
        self._owns_client = client is None
        self.client = client or httpx.Client(
            base_url=base_url.rstrip("/"),
            timeout=timeout,
            headers={"X-Agent-Token": token},
        )

    def close(self) -> None:
        if self._owns_client:
            self.client.close()

    def create(self, job: Job) -> Job:
        raise NotImplementedError("O agente remoto não cria jobs; a API é a autoridade da fila.")

    def get(self, job_id: str) -> Job | None:
        response = self.client.get(f"/api/agent/jobs/{job_id}")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return job_from_dict(response.json()["job"])

    def list(self, limit: int = 100) -> list[Job]:
        raise NotImplementedError("Listagem administrativa pertence à API/painel.")

    def find_existing_by_idempotency(self, key: str) -> Job | None:
        raise NotImplementedError("Idempotência de enqueue pertence à API/painel.")

    def update(self, job: Job) -> None:
        response = self.client.post(
            f"/api/agent/jobs/{job.id}/state",
            json={
                "status": job.status.value,
                "current_step": job.current_step,
                "external_id": job.external_id,
                "error": job.error,
            },
        )
        response.raise_for_status()

    def claim_next(self, agent_id: str) -> Job | None:
        response = self.client.get("/api/agent/next", params={"agent_id": agent_id})
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        job_data = data.get("job")
        return job_from_dict(job_data) if job_data else None

    def record_step(
        self,
        job_id: str,
        step_name: str,
        status: StepStatus,
        message: str = "",
    ) -> None:
        response = self.client.post(
            f"/api/agent/jobs/{job_id}/steps",
            json={
                "step_name": step_name,
                "status": status.value,
                "message": message,
            },
        )
        response.raise_for_status()

    def completed_steps(self, job_id: str) -> set[str]:
        response = self.client.get(f"/api/agent/jobs/{job_id}/completed-steps")
        response.raise_for_status()
        return set(response.json().get("steps", []))
