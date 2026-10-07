from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from workflow_ai.domain.models import CaseRecord, Job, JobStatus, StepStatus, WorkflowKind


class SQLiteJobRepository:
    def __init__(self, db_path: str = "./data/app.db") -> None:
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    workflow TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL,
                    status TEXT NOT NULL,
                    current_step TEXT NOT NULL DEFAULT '',
                    external_id TEXT NOT NULL DEFAULT '',
                    error TEXT NOT NULL DEFAULT '',
                    approved INTEGER NOT NULL DEFAULT 0,
                    claimed_by TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
                CREATE INDEX IF NOT EXISTS idx_jobs_idempotency ON jobs(idempotency_key);

                CREATE TABLE IF NOT EXISTS job_steps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL,
                    step_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    message TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL,
                    UNIQUE(job_id, step_name)
                );
                """
            )

    def create(self, job: Job) -> Job:
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO jobs
                (id, workflow, payload_json, idempotency_key, status, current_step,
                 external_id, error, approved, claimed_by, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                self._params(job),
            )
        return job

    def get(self, job_id: str) -> Job | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        return self._row_to_job(row) if row else None

    def list(self, limit: int = 100) -> list[Job]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [self._row_to_job(row) for row in rows]

    def find_existing_by_idempotency(self, key: str) -> Job | None:
        """Return a succeeded or active equivalent job.

        Failed/cancelled jobs do not block a clean retry with a new job id.
        """
        with self._connect() as conn:
            row = conn.execute(
                """SELECT * FROM jobs
                WHERE idempotency_key = ?
                  AND status NOT IN (?, ?)
                ORDER BY updated_at DESC LIMIT 1""",
                (
                    key,
                    JobStatus.FAILED.value,
                    JobStatus.CANCELLED.value,
                ),
            ).fetchone()
        return self._row_to_job(row) if row else None

    def update(self, job: Job) -> None:
        with self._connect() as conn:
            conn.execute(
                """UPDATE jobs SET workflow=?, payload_json=?, idempotency_key=?,
                status=?, current_step=?, external_id=?, error=?, approved=?,
                claimed_by=?, created_at=?, updated_at=? WHERE id=?""",
                self._params(job)[1:] + (job.id,),
            )

    def claim_next(self, agent_id: str) -> Job | None:
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT id FROM jobs WHERE status = ? ORDER BY created_at LIMIT 1",
                (JobStatus.QUEUED.value,),
            ).fetchone()
            if not row:
                return None
            conn.execute(
                "UPDATE jobs SET status=?, claimed_by=?, updated_at=? WHERE id=?",
                (
                    JobStatus.CLAIMED.value,
                    agent_id,
                    datetime.now(timezone.utc).isoformat(),
                    row["id"],
                ),
            )
        return self.get(row["id"])

    def record_step(
        self, job_id: str, step_name: str, status: StepStatus, message: str = ""
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO job_steps(job_id, step_name, status, message, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(job_id, step_name) DO UPDATE SET
                    status=excluded.status,
                    message=excluded.message,
                    updated_at=excluded.updated_at""",
                (job_id, step_name, status.value, message, datetime.now(timezone.utc).isoformat()),
            )

    def completed_steps(self, job_id: str) -> set[str]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT step_name FROM job_steps WHERE job_id=? AND status=?",
                (job_id, StepStatus.SUCCEEDED.value),
            ).fetchall()
        return {row["step_name"] for row in rows}

    def approve(self, job_id: str) -> Job | None:
        job = self.get(job_id)
        if not job or job.status != JobStatus.WAITING_APPROVAL:
            return None
        job.approved = True
        job.status = JobStatus.QUEUED
        job.error = ""
        job.updated_at = datetime.now(timezone.utc)
        self.update(job)
        return job

    @staticmethod
    def _params(job: Job) -> tuple:
        payload = json.dumps(asdict(job.payload), ensure_ascii=False)
        return (
            job.id,
            job.workflow.value,
            payload,
            job.idempotency_key,
            job.status.value,
            job.current_step,
            job.external_id,
            job.error,
            int(job.approved),
            job.claimed_by,
            job.created_at.isoformat(),
            job.updated_at.isoformat(),
        )

    @staticmethod
    def _row_to_job(row: sqlite3.Row) -> Job:
        payload = CaseRecord.from_dict(json.loads(row["payload_json"]))
        return Job(
            id=row["id"],
            workflow=WorkflowKind(row["workflow"]),
            payload=payload,
            status=JobStatus(row["status"]),
            current_step=row["current_step"],
            external_id=row["external_id"],
            error=row["error"],
            approved=bool(row["approved"]),
            claimed_by=row["claimed_by"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
