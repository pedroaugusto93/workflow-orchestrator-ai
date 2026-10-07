from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    app_username: str = "admin"
    app_password: str = "change-me"
    app_access_token: str = "change-me"
    agent_token: str = "change-me-agent"
    database_url: str = "sqlite:///./data/app.db"
    approval_required: bool = True
    allow_force_reprocess: bool = False
    connector_package: str = "private_connectors"
    portal_a_url: str = ""
    portal_b_url: str = ""
    chrome_debug_host: str = "127.0.0.1"
    chrome_debug_port: int = 9222
    poll_interval_seconds: int = 5


settings = Settings()
