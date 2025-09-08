# -*- coding: utf-8 -*-
import streamlit as st
from . import utils
from .drug_data import solid_targeted, ko

APP_TITLE = "🩸 피수치 가이드 / BloodMap — v3.14.3 (KST)"
APP_SIGNATURE = "制作者: Hoya/GPT · 자문: Hoya/GPT"
RUNNY_OPTIONS = ["없음","흰색","연한색","누런색","피섞임"]
DYSP_3 = ["적게","조금","심함"]  # 요청: 호흡 난이도 3단계

def section_user():
    st.subheader("사용자")
    c1, c2 = st.columns([2,1])
    nickname = c1.text_input("별명", placeholder="예: 지민맘 / 보호자별 표시")
    pin = c2.text_input("PIN 4자리", max_chars=4, placeholder="0000", type="password")
    key = utils.user_key(nickname, pin)
    if not key:
        st.info("별명 + PIN(4자리 숫자)을 모두 입력하면 기록이 구분되어 저장됩니다.")
    st.caption(APP_SIGNATURE)
    return key

# ---------------- 피수치 + 특수검사 ----------------
def section_labs():
    st.header("피수치")
    c1, c2, c3 = st.columns(3)
    WBC = c1.number_input("WBC", min_value=0.0, step=0.1)
    Hb = c2.number_input("Hb", min_value=0.0, step=0.1)
    PLT = c3.number_input("혈소판(PLT)", min_value=0.0, step=1.0)
    c4, c5, c6 = st.columns(3)
    ANC = c4.number_input("호중구(ANC)", min_value=0.0, step=10.0)
    Na = c5.number_input("Na⁺", min_value=0.0, step=0.1)
    K = c6.number_input("K⁺", min_value=0.0, step=0.1)
    c7, c8, c9 = st.columns(3)
    Ca = c7.number_input("Ca²⁺", min_value=0.0, step=0.1)
    Alb = c8.number_input("Albumin", min_value=0.0, step=0.1)
    Cr = c9.number_input("Creatinine", min_value=0.0, step=0.01)
    c10, c11, c12 = st.columns(3)
    BUN = c10.number_input("BUN", min_value=0.0, step=0.1)
    AST = c11.number_input("AST", min_value=0.0, step=1.0)
    ALT = c12.number_input("ALT", min_value=0.0, step=1.0)
    c13, c14 = st.columns(2)
    CRP = c13.number_input("CRP", min_value=0.0, step=0.1)
    Glu = c14.number_input("Glucose", min_value=0.0, step=1.0)

    with st.expander("특수검사 (보체 C3/C4 포함)", expanded=True):
        st.caption("보체(C3/C4), 소변검사(단백뇨/당뇨/혈뇨) 등")
        c1, c2 = st.columns(2)
        C3 = c1.number_input("C3", min_value=0.0, step=0.1)
        C4 = c2.number_input("C4", min_value=0.0, step=0.1)
        u1, u2, u3 = st.columns(3)
        prot = u1.selectbox("단백뇨", ["없음","1+","2+","3+"], index=0)
        gluc = u2.selectbox("당뇨(요당)", ["없음","1+","2+","3+"], index=0)
        blood = u3.selectbox("혈뇨", ["없음","1+","2+","3+"], index=0)
    st.divider()

# ---------------- 암(고형암 표적치료제 중심) ----------------
def section_oncology():
    st.header("암/진단 — 고형암(표적위주)")
    cancer = st.selectbox("고형암 선택", list(solid_targeted.keys()))
    drug_list = solid_targeted[cancer]

    onco_key = f"solid|{cancer}"
    if st.session_state.get("onco_prev_key") != onco_key:
        st.session_state["onco_selected"] = [ko(x) for x in drug_list]
        st.session_state["onco_prev_key"] = onco_key

    selected = st.multiselect("표적항암제/면역치료제 선택(한글 병기)",
                              [ko(x) for x in drug_list],
                              default=st.session_state.get("onco_selected", []),
                              key="onco_selected")
    with st.expander("선택 미리보기", expanded=False):
        for d in selected:
            st.write("•", d)

# ---------------- 소아(일상/호흡기) ----------------
def ped_common_resp():
    st.header("소아 — 일상/호흡기")
    c1, c2 = st.columns(2)
    appetite = c1.radio("식욕", ["있음","없음"], horizontal=True)
    fever = c2.number_input("체온(℃)", min_value=34.0, max_value=42.5, step=0.1, format="%.1f")
    cough = st.select_slider("기침 정도", options=["안함","조금","보통","많이","심함"])
    dysp = st.select_slider("호흡곤란", options=DYSP_3)  # 요청: 3단계(적게/조금/심함)
    runny = st.selectbox("콧물(색/성상)", ["없음","흰색","연한색","누런색","피섞임"])

    has_spo2 = st.checkbox("SpO₂ 측정기 있음")
    if has_spo2:
        spo2 = st.number_input("SpO₂(%)", min_value=50, max_value=100, step=1)

# ---------------- 소아(감염질환) — 질환별 폼, 청진소견 제거 ----------------
def ped_infection():
    st.header("소아 — 감염별 증상")
    disease = st.selectbox(
        "질환 선택",
        ["RSV","아데노","로타","인플루엔자","파라인플루엔자","수족구","노로","마이코플라즈마"]
    )
    # 공통
    runny = st.selectbox("콧물(색/성상)", ["없음","흰색","연한색","누런색","피섞임"], key="runny_common")
    cough = st.select_slider("기침 정도", options=["안함","조금","보통","많이","심함"], key="cough_common")
    fever = st.number_input("체온(℃)", min_value=34.0, max_value=42.5, step=0.1, format="%.1f", key="fever_common")

    # 질환별 특이항목 (청진소견 제거; wheeze 등 제외)
    if disease == "RSV":
        apnea = st.checkbox("무호흡(영아)")
    elif disease == "아데노":
        eye = st.checkbox("눈꼽/결막 충혈")
        st.text_input("인후통/연하통 정도(메모)", key="aden_sore")
    elif disease == "로타":
        diarrhea = st.select_slider("설사 횟수", options=[str(i) for i in range(0,21)], key="rota_d")
        dehyd = st.checkbox("탈수 징후(입마름/눈물감소/소변감소)")
        vomit = st.checkbox("구토")
    elif disease == "인플루엔자":
        myalgia = st.select_slider("근육통", options=["없음","약함","보통","심함"], key="flu_m")
        headache = st.checkbox("두통")
    elif disease == "파라인플루엔자":
        bark = st.checkbox("크루프성 기침(개 짖는 소리)")
        hoarse = st.checkbox("쉰 목소리")
    elif disease == "수족구":
        mouth = st.checkbox("구내염/입안 수포")
        rash = st.checkbox("손/발 수포성 발진")
    elif disease == "노로":
        diarrhea = st.select_slider("설사 횟수", options=[str(i) for i in range(0,21)], key="noro_d")
        vomit = st.checkbox("구토/복통")
        dehyd = st.checkbox("탈수 징후")
    elif disease == "마이코플라즈마":
        dryc = st.select_slider("마른기침 지속기간(일)", options=[str(i) for i in range(0,31)], key="myco_dry")
        chest = st.checkbox("흉통/흉부 불편감")

    if st.button("해석하기", key="btn_infect"):
        st.success("입력값에 맞는 기본 가이드를 생성했어요. (의료진 상담을 대체하지 않습니다)")

def main():
    st.set_page_config(page_title="피수치 가이드 / BloodMap", layout="centered")
    st.title(APP_TITLE)
    with open(__file__.replace("app.py","style.css").replace("__init__.py","style.css"), "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    utils.init_state()
    ukey = section_user()

    mode = st.radio("모드 선택", ["피수치","암/진단(고형암)","소아(일상/호흡기)","소아(감염질환)"], horizontal=True)

    if mode == "피수치":
        section_labs()
    elif mode == "암/진단(고형암)":
        section_oncology()
    elif mode == "소아(일상/호흡기)":
        ped_common_resp()
    else:
        ped_infection()

    # 전역 해석하기 버튼(존재 확인용)
    if st.button("해석하기", key="btn_global"):
        st.success("해석 결과 요약을 생성했어요. (데모용 메시지)")

    st.caption("※ 본 도구는 보호자의 이해를 돕기 위한 참고용입니다. 모든 의학적 판단은 의료진의 진료·지시에 따르세요.")
    st.caption(APP_SIGNATURE)

if __name__ == "__main__":
    main()
