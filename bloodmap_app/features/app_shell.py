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
