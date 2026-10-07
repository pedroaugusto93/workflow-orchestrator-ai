from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class PortalBConfig:
    target_url: str = os.getenv("PORTAL_B_URL", "")
    justification: str = os.getenv("PORTAL_B_JUSTIFICATION", "")
    category_label: str = os.getenv("PORTAL_B_CATEGORY", "Serviços")
    contract_type_label: str = os.getenv("PORTAL_B_CONTRACT_TYPE", "Dispensa de licitação")
    dispute_mode_label: str = os.getenv("PORTAL_B_DISPUTE_MODE", "Não se aplica")
    legal_law_label: str = os.getenv("PORTAL_B_LEGAL_LAW", "LEI 14.133/2021")
    legal_article_label: str = os.getenv("PORTAL_B_LEGAL_ARTICLE", "Art. 75")
    legal_clause_prefix: str = os.getenv("PORTAL_B_LEGAL_CLAUSE_PREFIX", "Inciso II:")
    pca_status: str = os.getenv("PORTAL_B_PCA_STATUS", "Em Execução")
    catalog_code: str = os.getenv("PORTAL_B_CATALOG_CODE", "")
    catalog_text: str = os.getenv("PORTAL_B_CATALOG_TEXT", "")
    resource_label: str = os.getenv("PORTAL_B_RESOURCE_LABEL", "Estadual")
    attachment_type_label: str = os.getenv(
        "PORTAL_B_ATTACHMENT_TYPE", "Ato que autoriza a Contratação Direta"
    )
    responsible_role_label: str = os.getenv(
        "PORTAL_B_RESPONSIBLE_ROLE", "Responsável pela contratação direta"
    )
    authority_role_label: str = os.getenv("PORTAL_B_AUTHORITY_ROLE", "Autoridade competente")
    receipt_dir: Path = Path(os.getenv("PORTAL_B_RECEIPT_DIR", "./artifacts/receipts_b"))
