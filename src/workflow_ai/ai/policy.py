from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AIPolicy:
    """Policy boundary: AI can advise, but cannot bypass workflow guards."""

    can_extract_documents: bool = True
    can_suggest_mapping: bool = True
    can_validate_consistency: bool = True
    can_choose_workflow: bool = True
    can_click_irreversible_actions: bool = False
    can_disable_idempotency: bool = False
    can_reveal_secrets: bool = False
