from __future__ import annotations

import socket
import time
from typing import Any

from workflow_ai.application.orchestrator import Orchestrator
from workflow_ai.domain.models import JobStatus
from workflow_ai.infrastructure.connectors import build_connector_registry
from workflow_ai.infrastructure.http_repo import HttpJobRepository
from workflow_ai.infrastructure.settings import settings
from workflow_ai.infrastructure.sqlite_repo import SQLiteJobRepository


def build_repository():
    if settings.agent_api_url.strip():
        return HttpJobRepository(
            settings.agent_api_url,
            settings.agent_token,
        )
    return SQLiteJobRepository(
        settings.database_url.removeprefix("sqlite:///")
    )


def run() -> None:
    repo = build_repository()
    connectors = build_connector_registry(
        settings.connector_package,
        development=settings.app_env == "development",
    )
    remote_mode = bool(settings.agent_api_url.strip())
    orchestrator = Orchestrator(
        repo,
        connectors,
        approval_required=True if remote_mode else settings.approval_required,
        allow_force_reprocess=settings.allow_force_reprocess,
    )
    agent_id = socket.gethostname()

    try:
        while True:
            job = repo.claim_next(agent_id)
            if not job:
                time.sleep(settings.poll_interval_seconds)
                continue

            try:
                orchestrator.execute(job)
            except Exception as exc:
                job.status = JobStatus.FAILED
                job.error = f"{type(exc).__name__}: {exc}"
                repo.update(job)
    finally:
        close = getattr(repo, "close", None)
        if callable(close):
            close()


def main() -> None:
    run()


if __name__ == "__main__":
    main()
