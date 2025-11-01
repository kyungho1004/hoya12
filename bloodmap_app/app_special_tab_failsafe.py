# ==== PATCH • Failsafe Special Tab (non-destructive) ====
from __future__ import annotations
import streamlit as st

# If the main app already rendered the special tab once, do nothing.
if not st.session_state.get("_sp3v1_special_rendered"):
    try:
        import special_tests as _sp
    except Exception as _e:
        # Import guard may not have run; try to activate and retry
        try:
            import special_tests_import_guard  # type: ignore
            import special_tests as _sp  # retry
        except Exception:
            _sp = None

    # Create an isolated tab so the user can access Special Tests
    t_special_fallback, = st.tabs(["특수검사"])
    with t_special_fallback:
        st.session_state.setdefault("_route", "dx")
        st.session_state["_tab_active"] = "특수검사"
        try:
            lines = _sp.special_tests_ui() if (_sp and hasattr(_sp, "special_tests_ui")) else []
        except Exception as e:
            st.warning(f"특수검사 UI 로딩 오류: {e}")
            lines = []
        if isinstance(lines, list):
            st.session_state["special_tests_lines"] = lines
        st.session_state["_sp3v1_special_rendered"] = True

# Ensure report section is stitched at least once
try:
    import special_tests as _sp2
except Exception:
    _sp2 = None
try:
    if _sp2 and hasattr(_sp2, "special_section"):
        _ = _sp2.special_section()
except Exception:
    pass
# ==== /PATCH END ====