
# -*- coding: utf-8 -*-
"""
peds_symptoms_ui.py
- 소아 증상별 대처법 안내 (보호자 친화)
- 강한 네임스페이스(key_prefix) + 자동 prefix로 충돌 방지
"""
from typing import Optional, Dict, List, Tuple
import streamlit as st

# 증상 목록과 안내문 (간단 요약 + 가정관리 + 병원/응급 경고)
SYMPTOMS: Dict[str, Dict[str, str]] = {
    "고열(≥38.5℃)": {
        "home": "미온수 닦기, 얇게 입히기, 수분 섭취. 해열제는 체중기반 용량 준수(아세트아미노펜 10–15mg/kg, 이부프로펜 10mg/kg; 생후 6개월 미만 이부프로펜 지양).",
        "seek": "48시간 이상 지속, 처짐/경련/의식저하 동반, 탈수 의심 시 빠른 진료.",
        "er":   "의식저하/경련/호흡곤란 동반 시 응급실."
    },
    "호흡곤란/가슴통증": {
        "home": "휴식, 상체 세우기, 실내 공기 환기.",
        "seek": "호흡수 증가, 청색증(입술/손톱), 기침/쌕쌕거림 지속 시 빠른 진료.",
        "er":   "숨 쉬기 힘듦, 말하기 어려움, 가슴 통증 심함 → 즉시 응급실."
    },
    "구토/설사(탈수 의심)": {
        "home": "소량씩 자주 수분(ORS). 우유/기름진 음식 피하기.",
        "seek": "소변량 감소, 입마름, 눈물 감소, 지속 구토 시 진료.",
        "er":   "피섞인 구토/설사, 심한 무기력/의식저하 → 응급실."
    },
    "복통": {
        "home": "금식은 필요치 않음. 자극적 음식 피하고 미지근한 물.",
        "seek": "국소 통증 지속, 발열 동반, 구토로 수분 섭취 불가 시 진료.",
        "er":   "우하복부 지속 통증(충수염 의심), 배가 단단/팽만, 피 섞인 변 → 응급실."
    },
    "발진/점상출혈": {
        "home": "가려움은 냉습포/저자극 보습.",
        "seek": "광범위 확산, 열 동반, 자반/점상출혈(압박 불소실) 시 진료.",
        "er":   "자반성 발진 + 발열/복통/관절통 동반 → 응급실 고려."
    },
    "혈변/흑색변/혈뇨": {
        "home": "수분 유지, 자극성 음식 피하기.",
        "seek": "반복적 혈변/혈뇨, 어지럼 동반 시 진료.",
        "er":   "검붉거나 타르색 변(흑색변), 덩어리 피 다량 → 즉시 진료/응급실."
    },
    "두통/번개두통/시야 이상": {
        "home": "조용한 환경, 수분/휴식.",
        "seek": "구토 동반, 아침에 심함, 시야 이상 지속 시 진료.",
        "er":   "벼락같이 갑작스런 심한 두통, 의식/신경학적 이상 → 응급실."
    },
}

def _pill(text: str, color: str = "#f3f4f6"):
    st.markdown(f"<span style='display:inline-block;padding:4px 10px;border-radius:9999px;background:{color};font-size:0.9rem'>{text}</span>", unsafe_allow_html=True)

def render_peds_symptoms_page(key_prefix: Optional[str] = None):
    # 자동 prefix (충돌 방지)
    if key_prefix is None:
        cnt = st.session_state.get("_peds_symptoms_ui_inst", 0)
        key_prefix = f"peds_sym_{cnt}"
        st.session_state["_peds_symptoms_ui_inst"] = cnt + 1

    st.header("🧒 소아 증상별 대처법")
    st.caption("보호자 친화 안내 · 참고용 · 위급 시 119/응급실")

    # 증상 선택(복수)
    picks = st.multiselect("해당하는 증상을 모두 선택하세요", list(SYMPTOMS.keys()),
                           key=f"{key_prefix}_picks")

    if not picks:
        st.info("상단에서 증상을 하나 이상 선택하면 안내가 표시됩니다.")
        return

    # 요약 카드 (오른쪽) + 설명 (왼쪽)
    left, right = st.columns([2,1])
    with left:
        for name in picks:
            with st.container(border=True):
                st.subheader(f"• {name}")
                data = SYMPTOMS[name]
                st.markdown("**가정관리**")
                st.write(data["home"])
                st.markdown("**이럴 땐 병원**")
                _pill(data["seek"])
                st.markdown("**응급실 즉시**")
                st.error(data["er"])

    with right:
        st.markdown("#### 요약 권고")
        # 간단 스코어: 응급 문구가 하나라도 있으면 상향
        severity = 0
        for name in picks:
            if "응급" in SYMPTOMS[name]["er"] or "즉시" in SYMPTOMS[name]["er"]:
                severity = max(severity, 2)
            else:
                severity = max(severity, 1)
        if severity >= 2:
            st.error("🔴 위험 신호 가능성 — 응급실/즉시 진료 고려")
        elif severity == 1:
            st.warning("🟠 주의 — 빠른 외래 + 증상 모니터링")
        else:
            st.success("🟢 안정 — 가정관리와 안내문 참고")

        # 공유/내보내기
        try:
            from pdf_export import export_md_to_pdf  # type: ignore
            txt = "증상별 대처 요약\n\n" + "\n\n".join([f"[{n}]\n- 가정관리: {SYMPTOMS[n]['home']}\n- 병원: {SYMPTOMS[n]['seek']}\n- 응급: {SYMPTOMS[n]['er']}" for n in picks])
            pdf_bin = export_md_to_pdf(txt)
            st.download_button("PDF로 저장", data=pdf_bin, file_name="peds_symptoms_guide.pdf",
                               mime="application/pdf", key=f"{key_prefix}_pdf")
        except Exception:
            st.caption("PDF 모듈이 없으면 TXT만 제공됩니다.")
            st.download_button("TXT로 저장", data=txt.encode("utf-8"),
                               file_name="peds_symptoms_guide.txt", mime="text/plain",
                               key=f"{key_prefix}_txt")
