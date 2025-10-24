"""
Adverse effects renderer (extracted).
Delegates to ui_results.render_adverse_effects if available.
"""
from typing import Sequence, Mapping, Any

def render_adverse_effects(st, picked_keys: Sequence[str]|None, DRUG_DB: Mapping[str, dict]|None) -> None:
    try:
        # Prefer existing implementation in ui_results to avoid divergence
        try:
            from ui_results import render_adverse_effects as _legacy_render
        except Exception:
            _legacy_render = None
        if _legacy_render:
            _legacy_render(st, picked_keys, DRUG_DB)
        # If there's additional phase-2 custom rendering to add, place below
        # (kept empty now to avoid double-rendering).
    except Exception:
        # Never break the outer UI
        return None
