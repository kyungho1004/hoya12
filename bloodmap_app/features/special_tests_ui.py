"""
Wrapper for special_tests.special_tests_ui() with safe key namespace and summary.
"""
from __future__ import annotations
from typing import List

def render_special_tests_panel(st):
    if st.session_state.get("_stests_rendered"):
        return
    try:
        import special_tests as _st  # legacy UI
    except Exception:
        _st = None
    try:
        from features.special_tests_keys import set_call_namespace as _setns
        from features.special_tests_core import normalize_lines as _norm
    except Exception:
        _setns = None
        _norm = lambda x: []

    try:
        with st.expander("🧪 특수검사 (분리 모듈, β)", expanded=False):
            if _setns:
                _setns()  # guarantee unique keys per render
            lines: List[str] = []
            if _st and hasattr(_st, "special_tests_ui"):
                try:
                    lines = _st.special_tests_ui() or []
                except Exception:
                    lines = []
            pairs = _norm(lines)
            if pairs:
                st.markdown("**요약**")
                for level, msg in pairs:
                    if level == "risk":
                        st.markdown("🚨 - " + msg)
                    elif level == "warn":
                        st.markdown("⚠️ - " + msg)
                    else:
                        st.markdown("- " + msg)
    except Exception:
        pass
