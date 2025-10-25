"""
Wrapper for special_tests.special_tests_ui() to integrate as a non-intrusive panel.
- Calls upstream UI, then shows a compact summary of emitted lines (if any).
- Never breaks the app (full try/except).
"""
from __future__ import annotations
from typing import List

def render_special_tests_panel(st):
    try:
        import special_tests as _st  # existing module in project root
    except Exception:
        _st = None

    try:
        with st.expander("🧪 특수검사 (분리 모듈, β)", expanded=False):
            lines: List[str] = []
            if _st and hasattr(_st, "special_tests_ui"):
                try:
                    lines = _st.special_tests_ui() or []
                except Exception:
                    lines = []
            # Compact summary (if upstream emitted lines)
            if lines:
                st.markdown("**요약**")
                for kind, msg in [l.split("|", 1) if "|" in l else ("info", l) for l in lines]:
                    bullet = f"- {msg.strip()}"
                    if "risk" in kind:
                        st.markdown("🚨 " + bullet)
                    elif "warn" in kind:
                        st.markdown("⚠️ " + bullet)
                    else:
                        st.markdown(bullet)
    except Exception:
        pass
