from fastapi.testclient import TestClient

import apps.api.main as api
from workflow_ai.domain.models import CaseRecord, Job, JobStatus, WorkflowKind
from workflow_ai.infrastructure.sqlite_repo import SQLiteJobRepository


def _client_with_repo(tmp_path, monkeypatch):
    repo = SQLiteJobRepository(str(tmp_path / "api.db"))
    monkeypatch.setattr(api, "repo", repo)
    return TestClient(api.app), repo


def test_agent_cannot_start_irreversible_step_without_approval(tmp_path, monkeypatch):
    client, repo = _client_with_repo(tmp_path, monkeypatch)
    job = repo.create(
        Job(
            workflow=WorkflowKind.PORTAL_A_SUBMISSION,
            payload=CaseRecord(process_id="P1"),
            status=JobStatus.CLAIMED,
        )
    )
    headers = {"X-Agent-Token": api.settings.agent_token}

    response = client.post(
        f"/api/agent/jobs/{job.id}/steps",
        headers=headers,
        json={
            "step_name": "submit",
            "status": "running",
            "message": "",
        },
    )

    assert response.status_code == 409


def test_agent_cannot_report_success_without_approval(tmp_path, monkeypatch):
    client, repo = _client_with_repo(tmp_path, monkeypatch)
    job = repo.create(
        Job(
            workflow=WorkflowKind.PORTAL_B_PUBLICATION,
            payload=CaseRecord(process_id="P1"),
            status=JobStatus.CLAIMED,
        )
    )
    headers = {"X-Agent-Token": api.settings.agent_token}

    response = client.post(
        f"/api/agent/jobs/{job.id}/state",
        headers=headers,
        json={
            "status": "succeeded",
            "current_step": "",
            "external_id": "",
            "error": "",
        },
    )

    assert response.status_code == 409


def test_human_approval_only_accepts_waiting_jobs(tmp_path, monkeypatch):
    client, repo = _client_with_repo(tmp_path, monkeypatch)
    job = repo.create(
        Job(
            workflow=WorkflowKind.PORTAL_A_SUBMISSION,
            payload=CaseRecord(process_id="P1"),
            status=JobStatus.NEEDS_REVIEW,
        )
    )

    response = client.post(
        f"/jobs/{job.id}/approve",
        auth=(api.settings.app_username, api.settings.app_password),
        follow_redirects=False,
    )

    assert response.status_code == 409
    assert repo.get(job.id).status == JobStatus.NEEDS_REVIEW


def test_agent_cannot_mutate_needs_review_job(tmp_path, monkeypatch):
    client, repo = _client_with_repo(tmp_path, monkeypatch)
    job = repo.create(
        Job(
            workflow=WorkflowKind.PORTAL_A_SUBMISSION,
            payload=CaseRecord(process_id="P1"),
            status=JobStatus.NEEDS_REVIEW,
            approved=True,
        )
    )
    headers = {"X-Agent-Token": api.settings.agent_token}

    response = client.post(
        f"/api/agent/jobs/{job.id}/state",
        headers=headers,
        json={
            "status": "running",
            "current_step": "submit",
            "external_id": "",
            "error": "",
        },
    )

    assert response.status_code == 409
    assert repo.get(job.id).status == JobStatus.NEEDS_REVIEW
