"""
Small debug helpers (render-only). Safe to call multiple times.
"""
from __future__ import annotations

def render_debug_panel(st, ae_source_text: str, picked_keys):
    try:
        with st.expander("디버그: 키워드 매칭 상태", expanded=False):
            st.caption("▼ 검사 텍스트(앞 300자 미리보기)")
            st.write((ae_source_text or "")[:300])
            st.caption("선택 약물 키")
            st.write(picked_keys or [])
    except Exception:
        pass
