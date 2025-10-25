"""
Pediatric mini jumpbar (non-intrusive).
- Shows quick access buttons (no hard routing change).
- Complements nav guards; sets a soft flag for DX stickiness when used.
"""
from __future__ import annotations

SECTIONS = [
    ("해열제", "peds_fever"),
    ("ORS·탈수", "peds_ors"),
    ("호흡기", "peds_resp"),
    ("설사 분류", "peds_diarrhea"),
    ("구내염", "peds_stoma"),
    ("내보내기(소아)", "peds_export"),
]

def render_peds_jumpbar(st):
    try:
        with st.expander("소아 빠른 이동 (β)", expanded=False):
            cols = st.columns(len(SECTIONS))
            for (label, key), col in zip(SECTIONS, cols):
                with col:
                    if st.button(label, key=f"jb_{key}"):
                        st.session_state["_dx_active"] = True  # keep dx sticky
                        st.session_state["_peds_focus"] = key  # soft focus hint
                        st.toast(f"소아 {label} 섹션으로 이동 힌트가 설정되었습니다.", icon="👶")
    except Exception:
        pass
