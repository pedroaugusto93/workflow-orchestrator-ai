from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class PortalAConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="PORTAL_A_",
        extra="ignore",
    )

    create_url: str = ""
    search_url: str = ""
    typology_value: str = "30"
    item_lot_value: str = "1"
    legal_basis_value: str = "61"
    price_registration_value: str = "false"
    unit_value: str = "37"
    document_act_value: str = "1"
    document_type_value: str = "5"
    commitment_unit_code: str = ""
    document_required: bool = True
    receipt_dir: Path = Path("./artifacts/receipts_a")
