"""
Adverse effects renderer (extracted).
Default: delegate to ui_results.render_adverse_effects (backward compatible).
Fallback: render a compact summary table when upstream is missing/unavailable.
"""
from __future__ import annotations
from typing import Sequence, Mapping, Any

def _harvest_text_for_key(drug_db: Mapping[str, Any], key: str) -> str:
    """Return concatenated AE text for a single drug key, tolerant to schema differences."""
    try:
        from utils.db_access import concat_ae_text as _concat
        return _concat({key: drug_db.get(key, {})}, [key])
    except Exception:
        return ""

def _fallback_render(st, picked_keys: Sequence[str]|None, drug_db: Mapping[str, Any]|None) -> None:
    try:
        keys = list(picked_keys or [])
        if not keys:
            return
        st.markdown("### 항암제 부작용 요약 (fallback)")
        # Simple table: Drug | Summary(앞 180자)
        import pandas as pd
        rows = []
        for k in keys:
            txt = _harvest_text_for_key(drug_db or {}, k)
            if txt:
                snippet = (txt[:180] + "…") if len(txt) > 180 else txt
            else:
                snippet = ""
            rows.append({"Drug": str(k), "Summary": snippet})
        if rows:
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True)
    except Exception:
        # never break the parent UI
        pass

def render_adverse_effects(st, picked_keys: Sequence[str]|None, DRUG_DB: Mapping[str, dict]|None) -> None:
    """
    Try upstream renderer first; if it fails or is absent, use a compact fallback.
    """
    # 1) Prefer upstream implementation
    try:
        try:
            from ui_results import render_adverse_effects as _legacy_render
        except Exception:
            _legacy_render = None
        if _legacy_render:
            _legacy_render(st, picked_keys, DRUG_DB)
            return
    except Exception:
        # fall through to fallback
        pass

    # 2) Fallback rendering (non-intrusive)
    _fallback_render(st, picked_keys, DRUG_DB)
