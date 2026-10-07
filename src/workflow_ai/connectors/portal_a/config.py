from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class PortalAConfig:
    create_url: str = os.getenv("PORTAL_A_CREATE_URL", "")
    search_url: str = os.getenv("PORTAL_A_SEARCH_URL", "")
    typology_value: str = os.getenv("PORTAL_A_TYPOLOGY_VALUE", "30")
    item_lot_value: str = os.getenv("PORTAL_A_ITEM_LOT_VALUE", "1")
    legal_basis_value: str = os.getenv("PORTAL_A_LEGAL_BASIS_VALUE", "61")
    price_registration_value: str = os.getenv("PORTAL_A_PRICE_REGISTRATION_VALUE", "false")
    unit_value: str = os.getenv("PORTAL_A_UNIT_VALUE", "37")
    document_act_value: str = os.getenv("PORTAL_A_DOCUMENT_ACT_VALUE", "1")
    document_type_value: str = os.getenv("PORTAL_A_DOCUMENT_TYPE_VALUE", "5")
    commitment_unit_code: str = os.getenv("PORTAL_A_COMMITMENT_UNIT_CODE", "")
    document_required: bool = os.getenv("PORTAL_A_DOCUMENT_REQUIRED", "true").lower() in {"1", "true", "yes", "sim"}
    receipt_dir: Path = Path(os.getenv("PORTAL_A_RECEIPT_DIR", "./artifacts/receipts"))
