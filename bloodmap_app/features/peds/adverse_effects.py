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

# ---- Phase 14: AE main renderer wrapper (legacy-compatible) ----
def render_ae_main(st, picked_keys: Sequence[str] | None, DRUG_DB: Mapping[str, dict] | None) -> None:
    """
    Preferred entry point for AE rendering.
    - Delegates to ui_results.render_adverse_effects if present.
    - Sets a guard in session_state to avoid duplicate rendering by upstream blocks.
    - Never breaks outer UI.
    """
    try:
        ss = st.session_state
        try:
            from ui_results import render_adverse_effects as _legacy_main
        except Exception:
            _legacy_main = None
        if _legacy_main:
            _legacy_main(st, picked_keys, DRUG_DB)
            ss["_ae_main_rendered"] = True
            return
        # Fallback: minimal bullet summary (uses same concat util as other helpers)
        from utils.db_access import concat_ae_text as _concat
        text = _concat(DRUG_DB or {}, list(picked_keys or []))
        if text.strip():
            with st.expander("항암제 부작용(기본 렌더, β)", expanded=True):
                for line in _bullets_from_text(text, max_items=16):
                    st.markdown(line)
                st.caption("※ 자동 요약입니다. 실제 라벨/가이드를 우선하세요.")
            ss["_ae_main_rendered"] = True
    except Exception:
        pass

from typing import Sequence, Mapping

def _get(db: Mapping, k: str, d=None):
    try:
        return db.get(k, d) if hasattr(db, "get") else d
    except Exception:
        return d

def _str(v):
    try:
        return str(v) if v is not None else ""
    except Exception:
        return ""

def _drug_display_name(rec: Mapping, key: str) -> str:
    # Try common fields: "name", "kor", "ko", "label"
    for f in ("name","kor","ko","label","display"):
        val = rec.get(f) if isinstance(rec, dict) else None
        if val:
            return f"{key} ({val})"
    return key

def _infer_ae_text(rec: Mapping) -> str:
    # Try common fields to find AE text
    if not isinstance(rec, dict):
        return _str(rec)
    for f in ("ae","AEs","adverse","effects","부작용","desc","text"):
        if rec.get(f):
            return _str(rec.get(f))
    # join lists if any
    for f in ("list","lines","bullets"):
        v = rec.get(f)
        if isinstance(v, (list,tuple)):
            return "; ".join(map(_str, v))
    return ""

def _contains_any(text: str, needles):
    t = (text or "").lower()
    return any(n.lower() in t for n in needles)

def _summarize_flags(text: str):
    flags = []
    if _contains_any(text, ["qt", "torsades"]):
        flags.append("QT 연장 — ECG 추적")
    if _contains_any(text, ["hand-foot", "hfs", "손발"]):
        flags.append("손발증후군 — 보습·마찰 줄이기")
    if _contains_any(text, ["differentiation", "atra", "분화", "ra 증후군", "ra증후군"]):
        flags.append("RA/분화 증후군 — 발열/호흡곤란 시 즉시 연락")
    if _contains_any(text, ["myelosup", "neutropen", "골수", "호중구"]):
        flags.append("골수억제 — 발열 시 즉시 연락")
    if _contains_any(text, ["cardio", "lvef", "심근", "구혈률"]):
        flags.append("심근독성 — 호흡곤란/부종/흉통 시 평가")
    return flags

def render_ae_main2(st, picked_keys: Sequence[str] | None, DRUG_DB: Mapping[str, dict] | None):
    """
    Enhanced AE section: if legacy renderer is present, it runs first (Phase 14),
    this adds a compact '항암제 요약 (영/한 + 부작용)' section beneath.
    """
    try:
        keys = list(picked_keys or [])
        if not keys:
            return
        with st.expander("## 항암제 요약 (영/한 + 부작용)", expanded=False):
            for k in keys:
                rec = _get(DRUG_DB or {}, k, {}) or {}
                name = _drug_display_name(rec, k)
                text = _infer_ae_text(rec)
                st.markdown(f"### {name}")
                if text:
                    st.markdown(f"- **요약**: {_str(text)[:300]}{'…' if len(_str(text))>300 else ''}")
                flags = _summarize_flags(text)
                if flags:
                    st.markdown("**핵심 주의**")
                    for f in flags:
                        st.markdown(f"- {f}")
                else:
                    st.caption("추가 주의 키워드가 감지되지 않았습니다.")
    except Exception:
        pass

# ---- Phase 19: Full AE section (legacy-first, compact table after) ----
from typing import Sequence, Mapping

def _safe_get(db: Mapping, k: str, d=None):
    try:
        return db.get(k, d) if hasattr(db, "get") else d
    except Exception:
        return d

def _first(*vals):
    for v in vals:
        if v:
            return v
    return ""

def _disp_name(rec: Mapping, key: str) -> str:
    if isinstance(rec, dict):
        return _first(rec.get("label"), rec.get("name"), rec.get("kor"), rec.get("ko"), key) or key
    return key

def _ae_text(rec: Mapping) -> str:
    if not isinstance(rec, dict):
        return str(rec)
    for f in ("ae","AEs","adverse","effects","부작용","desc","text"):
        if rec.get(f):
            return str(rec.get(f))
    for f in ("list","lines","bullets"):
        v = rec.get(f)
        if isinstance(v, (list,tuple)):
            return "; ".join(map(str, v))
    return ""

def _shorten(s: str, n: int = 240) -> str:
    s = (s or "").strip()
    return s if len(s) <= n else s[:n] + "…"

def render_ae_full(st, picked_keys: Sequence[str] | None, DRUG_DB: Mapping[str, dict] | None):
    """
    - Step 1: call legacy renderer if present (avoids regressions)
    - Step 2: show a compact AE table (영/한 + 요약) under expander
    """
    try:
        # legacy first
        try:
            from ui_results import render_adverse_effects as _legacy_main
            _legacy_main(st, picked_keys, DRUG_DB)
        except Exception:
            pass

        keys = list(picked_keys or [])
        if not keys:
            return
        rows = []
        for k in keys:
            rec = _safe_get(DRUG_DB or {}, k, {}) or {}
            rows.append((k, _disp_name(rec, k), _shorten(_ae_text(rec))))
        with st.expander("항암제 부작용(영/한 + 요약, compact)", expanded=False):
            for eng, disp, txt in rows:
                st.markdown(f"### {eng} ({disp})")
                if txt:
                    st.markdown(f"- **요약**: {txt}")
                else:
                    st.caption("요약 정보 없음(추가 데이터 필요)")
    except Exception:
        pass
