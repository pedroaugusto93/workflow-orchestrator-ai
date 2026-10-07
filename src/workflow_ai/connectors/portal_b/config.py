from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class PortalBConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="PORTAL_B_",
        populate_by_name=True,
        extra="ignore",
    )

    target_url: str = Field(default="", validation_alias="PORTAL_B_URL")
    justification: str = ""
    category_label: str = Field(
        default="Serviços",
        validation_alias="PORTAL_B_CATEGORY",
    )
    contract_type_label: str = Field(
        default="Dispensa de licitação",
        validation_alias="PORTAL_B_CONTRACT_TYPE",
    )
    dispute_mode_label: str = Field(
        default="Não se aplica",
        validation_alias="PORTAL_B_DISPUTE_MODE",
    )
    legal_law_label: str = Field(
        default="LEI 14.133/2021",
        validation_alias="PORTAL_B_LEGAL_LAW",
    )
    legal_article_label: str = Field(
        default="Art. 75",
        validation_alias="PORTAL_B_LEGAL_ARTICLE",
    )
    legal_clause_prefix: str = Field(
        default="Inciso II:",
        validation_alias="PORTAL_B_LEGAL_CLAUSE_PREFIX",
    )
    pca_status: str = "Em Execução"
    catalog_code: str = ""
    catalog_text: str = ""
    resource_label: str = "Estadual"
    attachment_type_label: str = Field(
        default="Ato que autoriza a Contratação Direta",
        validation_alias="PORTAL_B_ATTACHMENT_TYPE",
    )
    responsible_role_label: str = Field(
        default="Responsável pela contratação direta",
        validation_alias="PORTAL_B_RESPONSIBLE_ROLE",
    )
    authority_role_label: str = Field(
        default="Autoridade competente",
        validation_alias="PORTAL_B_AUTHORITY_ROLE",
    )
    receipt_dir: Path = Path("./artifacts/receipts_b")
