# ==== PATCH • app: Special tab render-once guard (non-destructive) ====
import streamlit as st
st.session_state.setdefault("_route", "dx")
st.session_state["_tab_active"] = "특수검사"
st.session_state.setdefault("_route_token", "r0")

if not st.session_state.get("_sp3v1_special_rendered"):
    try:
        import special_tests as _sp
        _sp_lines_tmp = _sp.special_tests_ui() if hasattr(_sp, "special_tests_ui") else []
    except Exception as e:
        st.warning(f"특수검사 UI 로딩 오류: {e}")
        _sp_lines_tmp = []
    if isinstance(_sp_lines_tmp, list):
        st.session_state["special_tests_lines"] = _sp_lines_tmp
    st.session_state["_sp3v1_special_rendered"] = True
else:
    _sp_lines_tmp = st.session_state.get("special_tests_lines", [])

# 보고서 섹션이 비어도 사라지지 않도록 한 번 트리거
try:
    import special_tests as _sp
    if hasattr(_sp, "special_section"):
        _ = _sp.special_section()
except Exception:
    pass
# ==== /PATCH END ====