"""
Pediatric respiratory quick helper — sputum & wheeze levels.
- Matches project plan: '가래'와 '쌕쌕거림(천명)' 4단계(없음/조금/보통/심함)
"""
from __future__ import annotations

LEVELS = ["없음", "조금", "보통", "심함"]

def render_peds_resp(st):
    try:
        with st.expander("소아 호흡기(가래·쌕쌕) (β)", expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                sputum = st.radio("가래 정도", LEVELS, key="peds_sputum")
            with c2:
                wheeze = st.radio("쌕쌕(천명) 정도", LEVELS, key="peds_wheeze")
            tips = []
            if wheeze in ("보통","심함"):
                tips.append("쌕쌕이 지속/악화 시 즉시 연락 • 흉부 함몰/청색증 시 응급")
            if sputum in ("보통","심함"):
                tips.append("수분섭취·가습·코세척, 증상 악화 시 병원 문의")
            if tips:
                st.markdown("**가이드**")
                for t in tips:
                    st.markdown(f"- {t}")
    except Exception:
        pass
