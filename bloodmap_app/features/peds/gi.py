"""
Pediatric GI quick-guides (constipation / diarrhea / vomiting).
Non-intrusive renderers meant to be called from app in an expander.
"""
from __future__ import annotations

def render_constipation_guide(st):
    try:
        with st.expander("소아 변비 관리 (보호자용, β)", expanded=False):
            st.markdown(
                "- **수분 섭취**: 미지근한 물 자주. 섬유소(과일·채소·통곡물) 천천히 늘리기.\n"
                "- **활동 유도**: 가능한 범위에서 걷기/가벼운 스트레칭.\n"
                "- **배변 습관**: 매일 같은 시간(식후 15~30분) 화장실 앉기.\n"
                "- **피하기**: 우유·치즈 과다, 과자류 위주 식사.\n"
                "- **연락 필요**: 혈변/검은변, 심한 복통·구토, 1주 이상 지속."
            )
    except Exception:
        pass

def render_diarrhea_guide(st):
    try:
        with st.expander("소아 설사 관리 (보호자용, β)", expanded=False):
            st.markdown(
                "- **수분 보충**: ORS 권장. 한 번에 조금씩 자주.\n"
                "- **식사**: 미음·죽 등 부담 적게. 기름지거나 매운 음식 피함.\n"
                "- **위생**: 손 씻기, 조리도구 구분.\n"
                "- **경고 신호**: 혈변/고열(≥38.5°C)/심한 탈수(축늘어짐·소변감소) → 즉시 연락.\n"
                "- **주의**: 2시간 지난 음식 재섭취 지양."
            )
    except Exception:
        pass

def render_vomiting_guide(st):
    try:
        with st.expander("소아 구토 관리 (보호자용, β)", expanded=False):
            st.markdown(
                "- **수분 보충**: 5~10분 간격 소량씩. 잦은 구토 시 ORS 소량 반복.\n"
                "- **자세**: 옆으로 눕혀 기도 보호.\n"
                "- **식사**: 일시적 금식 후 맑은 유동식 → 미음/죽 순.\n"
                "- **연락 필요**: 반복적 담즙/혈성 구토, 심한 복통/탈수, 의식 저하."
            )
    except Exception:
        pass

def render_peds_gi_all(st):
    try:
        render_constipation_guide(st)
        render_diarrhea_guide(st)
        render_vomiting_guide(st)
    except Exception:
        pass
