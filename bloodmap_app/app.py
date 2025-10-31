
# === PATCH: Special tests callsite guard (patch-only) ===
# Use this block around your special tests call in app.py to avoid NameError and stabilize behavior.
# Place it ONLY where you call special_tests_ui(); do not delete existing features.

import streamlit as st

def _safe_render_special_tests(special_tests_ui_func):
    st.subheader("🔬 특수검사")
    lines = []
    try:
        lines = special_tests_ui_func() or []
    except Exception as e:
        st.error(f"특수검사 UI 실행 중 오류가 발생했습니다: {e}")
        lines = []
    # Ensure report section gets a defined list
    st.session_state["special_interpretations"] = lines
    return lines

# Example usage in app.py:
# lines = _safe_render_special_tests(special_tests_ui)
# if not lines:
#     st.info("특수검사 해석이 없습니다. 값을 입력해보세요.")
# === /PATCH ===
