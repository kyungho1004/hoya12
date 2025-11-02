# ==== PATCH • Special Tests Fallback (self-contained & non-destructive) ====
from __future__ import annotations
import re

try:
    import streamlit as st
except Exception:  # pragma: no cover
    st = None  # type: ignore

def _ns() -> str:
    if st is None:
        return "sp3v1|no-st"
    who = str(st.session_state.get("key", "guest#PIN"))
    uid = str(st.session_state.get("_uid") or who or "anon")
    route = str(st.session_state.get("_route", "dx"))
    tab = str(st.session_state.get("_tab_active", "특수검사"))
    return f"sp3v1|{uid}|{route}|{tab}"

def _k(*parts: str) -> str:
    return "|".join([_ns(), *map(str, parts)])

def _counts():
    return st.session_state.setdefault("_sp_key_counts", {}) if st else {}

def _uniq(base: str) -> str:
    if not st:
        return base
    c = _counts()
    n = int(c.get(base, 0)); c[base] = n + 1
    return base if n == 0 else f"{base}#{n}"

def _norm(label: str) -> str:
    return re.sub(r"[^0-9a-zA-Z]+", "_", str(label)).strip("_").lower()

def _auto_wire_inputs():
    # Wrap a few common widgets to auto‑inject unique keys
    if st is None: return
    if not hasattr(st, "_orig_selectbox"):
        st._orig_selectbox = st.selectbox
        def _selectbox(label, options, *a, **kw):
            if "key" not in kw or not kw.get("key"):
                kw["key"] = _uniq(_k("sel", _norm(label)))
            return st._orig_selectbox(label, options, *a, **kw)
        st.selectbox = _selectbox
    if not hasattr(st, "_orig_number_input"):
        st._orig_number_input = st.number_input
        def _number_input(label, *a, **kw):
            if "key" not in kw or not kw.get("key"):
                kw["key"] = _uniq(_k("num", _norm(label)))
            return st._orig_number_input(label, *a, **kw)
        st.number_input = _number_input
    if not hasattr(st, "_orig_text_input"):
        st._orig_text_input = st.text_input
        def _text_input(label, *a, **kw):
            if "key" not in kw or not kw.get("key"):
                kw["key"] = _uniq(_k("txt", _norm(label)))
            return st._orig_text_input(label, *a, **kw)
        st.text_input = _text_input
    if not hasattr(st, "_orig_slider"):
        st._orig_slider = st.slider
        def _slider(label, *a, **kw):
            if "key" not in kw or not kw.get("key"):
                kw["key"] = _uniq(_k("sld", _norm(label)))
            return st._orig_slider(label, *a, **kw)
        st.slider = _slider

def _try_import_special():
    # Try normal and guarded imports, aliasing if needed
    try:
        import special_tests as _sp  # type: ignore
        return _sp
    except Exception:
        try:
            import special_tests_import_guard  # type: ignore
            import special_tests as _sp  # retry
            return _sp
        except Exception:
            return None

def _fallback_ui() -> list[str]:
    # Minimal placeholder UI so the tab is never blank
    st.subheader("🔬 특수검사 (안전 모드)")
    st.caption("모듈을 찾지 못해 간이 UI로 표시됩니다. 기능 검사 중…")
    col1, col2 = st.columns(2)
    with col1:
        alb = st.selectbox("Albumin (알부민뇨)", ["없음","+","++","+++"], index=0)
        glu = st.selectbox("Glucose (당뇨)", ["없음","+","++","+++"], index=0)
    with col2:
        ket = st.selectbox("Ketone (케톤뇨)", ["없음","+","++","+++"], index=0)
        nit = st.selectbox("Nitrite (아질산염)", ["없음","+","++","+++"], index=0)
    note = st.text_input("비고/메모")
    lines = [
        f"• 요검사: ALB={alb}, GLU={glu}, KET={ket}, NIT={nit}",
    ]
    if note:
        lines.append(f"• 메모: {note}")
    st.success("특수검사(안전모드) 입력이 임시로 저장되었습니다.")
    return lines

def force_render_special_tab():
    if st is None:
        return
    _auto_wire_inputs()

    # Already rendered by main app?
    if st.session_state.get("_sp3v1_special_rendered"):
        return

    # Try real module first
    _sp = _try_import_special()

    # Always present a Special tab, isolated if the main tab wiring failed
    t_special_fallback, = st.tabs(["특수검사"])
    with t_special_fallback:
        st.session_state.setdefault("_route", "dx")
        st.session_state["_tab_active"] = "특수검사"
        try:
            if _sp and hasattr(_sp, "special_tests_ui"):
                lines = _sp.special_tests_ui()
            else:
                lines = _fallback_ui()
        except Exception as e:
            st.warning(f"특수검사 UI 로딩 오류: {e}")
            lines = _fallback_ui()

        if isinstance(lines, list):
            st.session_state["special_tests_lines"] = lines
        st.session_state["_sp3v1_special_rendered"] = True

    # Try to stitch report at least once
    try:
        if _sp and hasattr(_sp, "special_section"):
            _ = _sp.special_section()
    except Exception:
        pass
# ==== /PATCH END ====