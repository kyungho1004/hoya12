"""
Explainer chips: show concise definitions only when specific terms are present.
"""
from __future__ import annotations

def render_explainer_chips(st, picked_keys, DRUG_DB, max_chips: int = 4):
    try:
        from utils.db_access import concat_ae_text as _concat
        from features.explainer_rules import compile_rules as _compile
    except Exception:
        return
    try:
        text = _concat(DRUG_DB or {}, list(picked_keys or []))
        if not text or not text.strip():
            return
        chips = []
        for name, pats, html in _compile():
            if any(p.search(text) for p in pats):
                chips.append(html)
            if len(chips) >= max_chips:
                break
        if chips:
            with st.expander("용어 풀이(자동, β)", expanded=False):
                st.markdown(" ".join(chips), unsafe_allow_html=True)
    except Exception:
        pass
