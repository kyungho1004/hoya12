"""
Pediatric symptom quick guides — diarrhea classify & stomatitis.
Implements user's plan: simple classification without heavy calcs; adds disclaimer.
"""
from __future__ import annotations

def render_peds_diarrhea(st):
    try:
        with st.expander("소아 설사 분류 (β)", expanded=False):
            color = st.selectbox("변 색상", ["노란색", "녹색", "피 섞임", "검은색", "기타"], key="peds_stool_color")
            texture = st.selectbox("질감", ["묽음", "거품", "점액", "보통"], key="peds_stool_tex")
            freq = st.selectbox("횟수(일)", ["<4회", "4~7회", "8회 이상"], key="peds_stool_freq")
            st.markdown("**간단 판단(참고용)**")
            tips = []
            if freq != "<4회":
                tips.append("탈수 위험 ↑ → ORS 소량씩 자주, 기저질환 있으면 연락 고려")
            if color in ("피 섞임", "검은색"):
                tips.append("혈변/흑변: 즉시 의료진 연락")
            if color == "녹색" or texture in ("거품",):
                tips.append("바이러스성 장염 가능성 — 위생 철저, 식이 조절")
            if not tips:
                tips.append("대부분 가벼운 경과 — 수분 보충과 휴식")
            for t in tips:
                st.markdown(f"- {t}")
            st.caption("※ 이 해석은 참고용이며, 정확한 진단은 의료진 판단에 따릅니다.")
    except Exception:
        pass

def render_peds_stomatitis(st):
    try:
        with st.expander("소아 구내염 가이드 (β)", expanded=False):
            st.markdown("- **통증 관리**: 처방받은 가글/진통제 지시대로 사용")
            st.markdown("- **위생**: 부드러운 칫솔, 자극적 음식 피하기")
            st.markdown("- **수분·영양**: 미지근한 물, 부드러운 음식(죽/요거트)")
            st.markdown("- **연락 필요**: 고열, 침흘림/연하곤란, 탈수 징후, 혈액질환 환아에서 악화")
            st.caption("※ 참고용 가이드입니다. 정확한 진단/치료는 의료진 판단을 따르세요.")
    except Exception:
        pass

def render_peds_symptom_guides(st):
    try:
        render_peds_diarrhea(st)
        render_peds_stomatitis(st)
    except Exception:
        pass
