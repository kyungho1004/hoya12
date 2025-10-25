"""
App shell (sidebar & header) with Lean Mode toggle.
- Patch-only: does not remove legacy; just offers a user-facing control.
"""
from __future__ import annotations

def render_sidebar(st):
    try:
        with st.sidebar:
            st.markdown("## ⚙️ 설정")
            lean = st.toggle("경량 모드(모듈만 우선)", value=bool(st.session_state.get("_lean_mode", True)), key="_lean_mode_toggle")
            st.session_state["_lean_mode"] = bool(lean)
            st.caption("※ 경량 모드: 모듈 라우터만 우선 렌더하고, 레거시 중복 출력은 최대한 억제합니다.")
            st.markdown("---")
            st.markdown("### 빠른 이동")
            st.write("- AE / 용어칩")
            st.write("- 특수검사")
            st.write("- 내보내기")
            st.write("- 소아")
    except Exception:
        pass
# --- Phase 27: 섹션 표시 토글 + 탭 선택 ---
try:
    st.markdown("### 섹션 표시")
    col1, col2 = st.columns(2)
    with col1:
        st.checkbox("AE", key="_show_ae", value=st.session_state.get("_show_ae", True))
        st.checkbox("특수검사", key="_show_special", value=st.session_state.get("_show_special", True))
    with col2:
        st.checkbox("내보내기", key="_show_exports", value=st.session_state.get("_show_exports", True))
        st.checkbox("소아", key="_show_peds", value=st.session_state.get("_show_peds", True))
    st.markdown("---")
    st.markdown("### 탭")
    tab = st.radio("보여줄 탭", ["전체", "AE", "특수검사", "내보내기", "소아"], key="_router_tab", horizontal=True)
    st.session_state["_router_tab"] = tab
except Exception:
    pass
