"""
Adverse effects renderer (extracted). Keep app.py thin by delegating here.
Initially a pass-through; migrate implementation here step by step.
"""
from typing import Sequence, Mapping, Any

def render_adverse_effects(st, picked_keys: Sequence[str]|None, DRUG_DB: Mapping[str, dict]|None) -> None:
    """
    Render adverse effects UI for selected drugs.
    This function is intended to fully replace the old in-app implementation over time.
    For now, it's safe to call even if empty.
    """
    try:
        # TODO: progressively move the actual rendering code here.
        # For now, do nothing (non-destructive).
        return None
    except Exception:
        # Never break the outer UI
        return None
