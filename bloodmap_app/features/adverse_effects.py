"""
Adverse effects renderer (extracted).
Default: delegate to ui_results.render_adverse_effects (backward compatible).
Fallback: render a compact summary table when upstream is missing/unavailable.
"""
from __future__ import annotations
from typing import Sequence, Mapping, Any

def _harvest_text_for_key(drug_db: Mapping[str, Any], key: str) -> str:
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
        import pandas as pd
        rows = []
        for k in keys:
            txt = _harvest_text_for_key(drug_db or {}, k)
            snippet = (txt[:180] + "…") if txt and len(txt) > 180 else (txt or "")
            rows.append({"Drug": str(k), "Summary": snippet})
        if rows:
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True)
    except Exception:
        pass

def render_adverse_effects(st, picked_keys: Sequence[str]|None, DRUG_DB: Mapping[str, dict]|None) -> None:
    try:
        try:
            from ui_results import render_adverse_effects as _legacy_render
        except Exception:
            _legacy_render = None
        if _legacy_render:
            _legacy_render(st, picked_keys, DRUG_DB)
            return
    except Exception:
        pass
    _fallback_render(st, picked_keys, DRUG_DB)

# ---- Phase 8: Structured AE table renderer (safe, schema-agnostic) ----
def _rows_from_text(text: str):
    import re
    if not text or not text.strip():
        return []
    s = re.sub(r"\s+", " ", text).strip()
    parts = re.split(r"[.;\n\r\t]+\s*", s)
    rows = []
    for p in parts:
        t = p.strip()
        if not t:
            continue
        sev = ""
        if re.search(r"중증|경고|위험|severe|grade\s*[34]|응급|출혈|실신|호흡곤란|혈전", t, re.I):
            sev = "⚠︎"
        event = t[:20] + ("…" if len(t) > 20 else "")
        typical = "" if sev else "○"
        note = t[:80] + ("…" if len(t) > 80 else "")
        rows.append([event, typical, sev, note])
        if len(rows) >= 60:
            break
    return rows

def render_ae_table(st, picked_keys: Sequence[str]|None, DRUG_DB: Mapping[str, dict]|None) -> None:
    try:
        keys = list(picked_keys or [])
        if not keys:
            return
        from utils.db_access import concat_ae_text as _concat
        text = _concat(DRUG_DB or {}, keys)
        if not text.strip():
            return
        with st.expander("항암제 부작용 표 (β)", expanded=False):
            import pandas as pd
            rows = _rows_from_text(text)
            if not rows:
                st.info("표로 변환할 내용이 충분하지 않습니다.")
                return
            df = pd.DataFrame(rows, columns=["이벤트", "일반", "중증", "메모(요약)"])
            st.dataframe(df, use_container_width=True)
            st.caption("※ 자동 변환 표입니다. 실제 진료 지침/라벨을 우선하세요.")
    except Exception:
        pass

# ---- Phase 8: AE summary renderer (bullet-style, beta) ----
def _bullets_from_text(text: str, max_items: int = 12):
    import re
    if not text or not text.strip():
        return []
    s = re.sub(r"\s+", " ", text).strip()
    parts = re.split(r"[.;\n\r\t]+\s*", s)
    out = []
    for p in parts:
        t = p.strip(" -•·")
        if not t:
            continue
        # Keep concise bullet: first clause up to ~80 chars
        if len(t) > 80:
            t = t[:80] + "…"
        out.append("• " + t)
        if len(out) >= max_items:
            break
    return out

def render_ae_summary(st, picked_keys: Sequence[str]|None, DRUG_DB: Mapping[str, dict]|None) -> None:
    try:
        keys = list(picked_keys or [])
        if not keys:
            return
        from utils.db_access import concat_ae_text as _concat
        text = _concat(DRUG_DB or {}, keys)
        if not text.strip():
            return
        with st.expander("항암제 부작용 요약 (β)", expanded=False):
            bullets = _bullets_from_text(text)
            if bullets:
                st.markdown("\n".join(bullets))
                st.caption("※ 자동 요약입니다. 실제 라벨/가이드를 우선하세요.")
    except Exception:
        pass

# ---- Phase 8: AE cards renderer (drug-wise, beta) ----
def render_ae_cards(st, picked_keys: Sequence[str]|None, DRUG_DB: Mapping[str, dict]|None) -> None:
    try:
        keys = list(picked_keys or [])
        if not keys:
            return
        from utils.db_access import concat_ae_text as _concat
        import textwrap as _tw
        with st.expander("항암제 카드(요약) (β)", expanded=False):
            for k in keys:
                txt = _concat({k: (DRUG_DB or {}).get(k, {})}, [k])
                if not txt.strip():
                    continue
                # Keep concise capsule
                snippet = txt[:220] + ("…" if len(txt) > 220 else "")
                st.markdown(f"#### {k}")
                st.write(_tw.dedent(snippet))
    except Exception:
        pass
