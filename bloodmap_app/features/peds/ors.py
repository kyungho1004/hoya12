"""
Pediatric ORS / dehydration quick guide (non-intrusive).
- No overlap with care_log ORS logic; pure guidance UI.
"""
from __future__ import annotations

def render_peds_ors(st):
    try:
        with st.expander("소아 ORS·탈수 가이드 (β)", expanded=False):
            st.markdown("- **목표**: 탈수 예방, 소량씩 자주")
            st.markdown("- **기본량**: 구토 없는 경우 **50–100 mL/kg/24h** 범위에서 분할")
            st.markdown("- **구토 동반**: 5~10분 간격 소량씩(5–10 mL) 반복 → 내성 생기면 양 증가")
            st.markdown("- **주의**: 2시간 지난 음식/음료 재섭취 지양, 살균/멸균 제품 권장")
            st.markdown("- **연락 필요**: 축늘어짐·소변감소·눈물 감소·고열(≥38.5°C)·혈변/검은변")
    except Exception:
        pass
