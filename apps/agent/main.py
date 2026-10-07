from __future__ import annotations

import socket
import time

from workflow_ai.application.orchestrator import Orchestrator
from workflow_ai.domain.models import JobStatus
from workflow_ai.infrastructure.connectors import build_connector_registry
from workflow_ai.infrastructure.settings import settings
from workflow_ai.infrastructure.sqlite_repo import SQLiteJobRepository


def run_local_mode() -> None:
    """MVP: API and agent share the same SQLite file on one machine."""
    repo = SQLiteJobRepository(settings.database_url.removeprefix("sqlite:///"))
    connectors = build_connector_registry(
    settings.connector_package, development=settings.app_env == "development"
)
    orchestrator = Orchestrator(
        repo,
        connectors,
        approval_required=settings.approval_required,
        allow_force_reprocess=settings.allow_force_reprocess,
    )
    agent_id = socket.gethostname()
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


def main() -> None:
    run_local_mode()


if __name__ == "__main__":
    main()
