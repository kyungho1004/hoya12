"""
Special Tests — migrated wrapper:
- Initializes robust key namespace
- Calls legacy special_tests.special_tests_ui() once per render
- Skips if already rendered (session flag)
- Fallback: minimal checklist UI (safe)
"""
from __future__ import annotations
from typing import List

def render_special_tests_migrated(st):
    try:
        ss = st.session_state
        if ss.get("_stests_rendered"):
            return
        # initialize strong keys
        try:
            from features.special_tests_keys import set_call_namespace as _setns
            _setns()
        except Exception:
            pass

        lines: List[str] = []
        err = None
        try:
            import special_tests as _st
            if hasattr(_st, "special_tests_ui"):
                with st.expander("🧪 특수검사 (이관, β)", expanded=False):
                    try:
                        out = _st.special_tests_ui()
                        if isinstance(out, list):
                            lines = out
                    except Exception as e:
                        err = e
            else:
                err = RuntimeError("legacy UI not found")
        except Exception as e:
            err = e

        if err is not None:
            # Fallback, very small checkboxes with unique keys
            with st.expander("🧪 특수검사 (이관-폴백, β)", expanded=False):
                cols = st.columns(3)
                checks = [
                    ("DIC 스크리닝", "PT/aPTT↑, D-dimer↑, PLT↓"),
                    ("TNM/이미징 추적", "CT/MRI/PET 일정 확인"),
                    ("감염 평가", "혈액배양/CRP/ANC"),
                ]
                for (name, tip), c in zip(checks, cols):
                    with c:
                        st.checkbox(name, key=f"st_mig_{name}")
                        st.caption(tip)
        ss["_stests_rendered"] = True
    except Exception:
        pass
