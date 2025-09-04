
# -*- coding: utf-8 -*-
import streamlit as st
from .utils import to_float, is_pos, digits_only

st.set_page_config(page_title="피수치 가이드 / BloodMap (Sarcoma)", layout="centered")

SARC_SUBTYPES = [
    "연부조직육종 (Soft tissue sarcoma)",
    "골육종 (Osteosarcoma)",
    "유잉육종 (Ewing sarcoma)",
    "지방육종 (Liposarcoma)",
    "평활근육종 (Leiomyosarcoma)",
    "기타/미분류"
]

ANTICANCERS = [
    ("Doxorubicin", "독소루비신 (Doxorubicin)"),
    ("Ifosfamide", "이포스파미드 (Ifosfamide)"),
    ("Gemcitabine", "젬시타빈 (Gemcitabine)"),
    ("Docetaxel", "도세탁셀 (Docetaxel)"),
    ("Pazopanib", "파조파닙 (Pazopanib)"),
    ("Trabectedin", "트라벡테딘 (Trabectedin)"),
    ("Eribulin", "에리불린 (Eribulin)"),
]

ANTIBIOTIC_CATEGORIES = [
    "페니실린/베타락탐계",
    "세팔로스포린계",
    "카바페넴계",
    "퀴놀론계",
    "매크롤라이드계",
    "아미노글리코사이드계",
    "글리코펩타이드계(반코마이신/테이코플라닌)",
    "옥사졸리디논계(리네졸리드)",
    "설폰아미드/트리메토프림",
    "테트라사이클린계",
]

def apply_css():
    st.markdown('<link rel="stylesheet" href="bloodmap_app/style.css">', unsafe_allow_html=True)

def id_row():
    c1, c2 = st.columns([1.2, 0.8])
    nick = c1.text_input("별명", placeholder="예: 민수엄마")
    pin_raw = c2.text_input("PIN 4자리 (중복 방지)", placeholder="0000", max_chars=4)
    pin = digits_only(pin_raw, 4)
    if pin_raw and pin != pin_raw:
        st.caption("※ 숫자만 허용됩니다. 자동 정리됨.")
    return (nick or "").strip(), pin

def sarcoma_selector():
    st.subheader("1️⃣ 육종 카테고리 (진단명으로 분리)")
    st.markdown('<span class="badge">육종 전용</span> 다른 암종은 숨김 처리했습니다.', unsafe_allow_html=True)
    return st.selectbox("육종 아형 선택", options=SARC_SUBTYPES, index=0)

def anticancer_section():
    st.subheader("2️⃣ 항암제 (한글 표기)")
    labels = [ko for _, ko in ANTICANCERS]
    sel = st.multiselect("복용/투여 중인 항암제 선택", options=labels)
    key_by_label = {ko: en for en, ko in ANTICANCERS}
    doses = {}
    if sel:
        for ko in sel:
            key = key_by_label[ko]
            amt = st.number_input(f"{ko} — 용량 (mg 또는 mg/m²)", min_value=0.0, step=1.0, format="%.2f", key=f"dose_{key}")
            doses[key] = to_float(amt, 0.0)
        if any(is_pos(v) for v in doses.values()):
            st.warning("약물 투여 중: 간수치 상승, 혈구감소, 심장독성(독소루비신) 등 부작용을 주의하세요.")
    else:
        st.caption("선택된 항암제가 없습니다.")
    return doses

def antibiotic_section():
    st.subheader("3️⃣ 항생제 (한글 표기)")
    sel = st.multiselect("복용/투여 중인 항생제 계열 선택", options=ANTIBIOTIC_CATEGORIES)
    abx = {}
    if sel:
        for cat in sel:
            amt = st.number_input(f"{cat} — 복용/주입량 (예: 정/앰플/회/일)", min_value=0.0, step=0.5, format="%.2f", key=f"abx_{cat}")
            abx[cat] = to_float(amt, 0.0)
        if any(is_pos(v) for v in abx.values()):
            st.info("항생제 사용 중: 설사, 발진, 간/신장 기능 이상, QT 연장 등의 부작용에 주의하세요.")
    else:
        st.caption("선택된 항생제가 없습니다.")
    return abx

def basic_labs():
    st.subheader("4️⃣ 기본 혈액 수치")
    wbc = to_float(st.number_input("WBC (×10³/µL)", min_value=0.0, step=0.1))
    hb  = to_float(st.number_input("Hb (g/dL)", min_value=0.0, step=0.1))
    plt = to_float(st.number_input("혈소판 PLT (×10³/µL)", min_value=0.0, step=1.0))
    anc = to_float(st.number_input("호중구 ANC (/µL)", min_value=0.0, step=10.0))
    return dict(WBC=wbc, Hb=hb, PLT=plt, ANC=anc)

def special_tests():
    st.subheader("5️⃣ 특수검사 (토글)")
    show_coag = st.checkbox("응고패널 (PT, aPTT, Fibrinogen, D-dimer)")
    show_comp = st.checkbox("보체 (C3, C4)")
    show_ua   = st.checkbox("요검사 (단백뇨, 잠혈, 요당)")

    out = {}
    if show_coag:
        st.markdown("**응고패널**")
        out["PT"] = to_float(st.number_input("PT (sec)", min_value=0.0, step=0.1, format="%.1f"))
        out["aPTT"] = to_float(st.number_input("aPTT (sec)", min_value=0.0, step=0.1, format="%.1f"))
        out["Fibrinogen"] = to_float(st.number_input("Fibrinogen (mg/dL)", min_value=0.0, step=1.0, format="%.0f"))
        out["D-dimer"] = to_float(st.number_input("D-dimer (µg/mL FEU)", min_value=0.0, step=0.1, format="%.2f"))
    if show_comp:
        st.markdown("**보체**")
        out["C3"] = to_float(st.number_input("C3 (mg/dL)", min_value=0.0, step=1.0, format="%.0f"))
        out["C4"] = to_float(st.number_input("C4 (mg/dL)", min_value=0.0, step=1.0, format="%.0f"))
    if show_ua:
        st.markdown("**요검사**")
        out["요단백(Proteinuria)"] = to_float(st.number_input("요단백 (정량 mg/dL)", min_value=0.0, step=1.0, format="%.0f"))
        out["잠혈(Hematuria)"] = to_float(st.number_input("잠혈 (정량/지표)", min_value=0.0, step=1.0, format="%.0f"))
        out["요당(Glycosuria)"] = to_float(st.number_input("요당 (정량 mg/dL)", min_value=0.0, step=1.0, format="%.0f"))
    return out

def advice(labs):
    st.subheader("6️⃣ 요약 안내")
    anc = labs.get("ANC", 0.0)
    if anc < 500:
        st.error("호중구 매우 낮음: 생야채 금지, 익힌 음식만 섭취, 외출 자제, 발열 시 즉시 병원.")
    elif anc < 1000:
        st.warning("호중구 낮음: 위생 철저, 음식 재가열 권장.")
    else:
        st.success("호중구 수치 양호.")

def main():
    apply_css()
    st.title("🩸 피수치 가이드 — 육종(Sarcoma) 전용 통합")
    st.caption("※ 참고용 도구입니다. 최종 의학적 판단은 의료진에게 문의하세요.")

    nick, pin = id_row()
    subtype = sarcoma_selector()
    doses = anticancer_section()
    abx = antibiotic_section()
    labs = basic_labs()
    extras = special_tests()
    advice(labs)

    st.divider()
    key = f"{(nick or '무명').strip()}#{(pin or '0000')}"
    st.caption(f"제작: Hoya/GPT · 저장키: {key}")
    st.caption("모바일 줄꼬임 방지·숫자 입력 방어·항암제/항생제 한글 표기·특수검사 토글")

if __name__ == "__main__":
    main()
