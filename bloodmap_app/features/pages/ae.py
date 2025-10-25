"""
Modular AE page (non-intrusive): renders AE main + explainer chips.
"""
from __future__ import annotations

def render(st, picked_keys, DRUG_DB):
    try:
        # Prefer our AE full section; fallback no-op
        try:
            from features.adverse_effects import render_ae_full as _ae_full
            _ae_full(st, picked_keys, DRUG_DB)
        except Exception:
            pass
        # Keyword-triggered chips
        try:
            from features.explainer import render_explainer_chips as _chips
            _chips(st, picked_keys, DRUG_DB, max_chips=6)
        except Exception:
            pass
    except Exception:
        pass
