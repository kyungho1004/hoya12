
# -*- coding: utf-8 -*-
from datetime import datetime, date
import os
import streamlit as st

from .config import (APP_TITLE, PAGE_TITLE, MADE_BY, CAFE_LINK_MD, FOOTER_CAFE,
                    DISCLAIMER, ORDER, FEVER_GUIDE,
                    LBL_WBC, LBL_Hb, LBL_PLT, LBL_ANC, LBL_Ca, LBL_P, LBL_Na, LBL_K,
                    LBL_Alb, LBL_Glu, LBL_TP, LBL_AST, LBL_ALT, LBL_LDH, LBL_CRP, LBL_Cr, LBL_UA, LBL_TB, LBL_BUN, LBL_BNP,
                    FONT_PATH_REG)
from .data.drugs import ANTICANCER, ABX_GUIDE
from .data.foods import FOODS
try:
    from .data.ped import PED_TOPICS, PED_INPUTS_INFO, PED_INFECT, PED_SYMPTOMS, PED_RED_FLAGS
except Exception:
    from .data.ped import PED_TOPICS, PED_INPUTS_INFO, PED_INFECT
    PED_SYMPTOMS, PED_RED_FLAGS = {}, {}
from .utils.inputs import num_input_generic, entered, _parse_numeric
from .utils.interpret import interpret_labs, compare_with_previous, food_suggestions, summarize_meds, abx_summary
from .utils.reports import build_report, md_to_pdf_bytes_fontlocked
from .utils.graphs import render_graphs
from .utils.schedule import render_schedule

try:
    import pandas as pd
    HAS_PD = True
except Exception:
    HAS_PD = False

def _nickname_with_pin():
    col1, col2 = st.columns([2,1])
    with col1:
        nickname = st.text_input("별명", placeholder="예: 홍길동")
    with col2:
        pin = st.text_input("PIN(4자리 숫자)", max_chars=4, help="중복 방지용 4자리 숫자", key="pin", placeholder="0000")
    pin_clean = "".join([c for c in (pin or "") if c.isdigit()])[:4]
    if pin and pin != pin_clean:
        st.warning("PIN은 숫자 4자리만 허용됩니다.")
    if pin_clean and len(pin_clean)!=4:
        st.info("PIN 4자리를 입력해주세요.")
    k = (nickname.strip() + "#" + pin_clean) if nickname and pin_clean else nickname.strip()
    return nickname, pin_clean, k

def _load_css():
    try:
        st.markdown('<style>'+open(os.path.join(os.path.dirname(__file__), "style.css"), "r", encoding="utf-8").read()+'</style>', unsafe_allow_html=True)
    except Exception:
        pass

def main():
    st.set_page_config(page_title=PAGE_TITLE, layout="centered")
    _load_css()
    st.title(APP_TITLE)
    st.markdown(MADE_BY)
    st.markdown(CAFE_LINK_MD)

    st.markdown("### 🔗 공유하기")
    c1, c2, c3 = st.columns([1,1,2])
    with c1:
        st.link_button("📱 카카오톡/메신저", "https://hdzwo5ginueir7hknzzfg4.streamlit.app/")
    with c2:
        st.link_button("📝 카페/블로그", "https://cafe.naver.com/bloodmap")
    with c3:
        st.code("https://hdzwo5ginueir7hknzzfg4.streamlit.app/", language="text")
    st.caption("✅ 모바일 줄꼬임 방지 · 별명+PIN 저장/그래프 · 암별/소아/희귀암/육종 패널 · PDF 한글 폰트 고정 · 수치 변화 비교 · 항암 스케줄표 · ANC 가이드")

    os.makedirs("fonts", exist_ok=True)
    from .utils import counter as _bm_counter
    try:
        _bm_counter.bump()
        st.caption(f"👀 조회수(방문): {_bm_counter.count()}")
    except Exception:
        pass

    if "records" not in st.session_state:
        st.session_state.records = {}
    if "schedules" not in st.session_state:
        st.session_state.schedules = {}

    st.divider()
    st.header("1️⃣ 환자/암·소아 정보")

    nickname, pin, nickname_key = _nickname_with_pin()
    test_date = st.date_input("검사 날짜", value=date.today())
    anc_place = st.radio("현재 식사 장소(ANC 가이드용)", ["가정", "병원"], horizontal=True)

    mode = st.selectbox("모드 선택", ["일반/암", "소아(일상/호흡기)", "소아(감염질환)"])

    group = None
    cancer = None
    infect_sel = None
    ped_topic = None

    # 내부키(혈액암) 정규화: 화면표기는 'AML(…)' 등이나 로직키는 'AML'
    heme_key_map = {
    # EN-first
    'AML(급성 골수성 백혈병)': 'AML',
    'APL(급성 전골수구성백혈병)': 'APL',
    'ALL(급성 림프모구성 백혈병)': 'ALL',
    'CML(만성 골수성백혈병)': 'CML',
    'CLL(만성 림프구성백혈병)': 'CLL',
    # KR-first
    '급성 골수성 백혈병(AML)': 'AML',
    '급성 전골수구성 백혈병(APL)': 'APL',
    '급성 림프모구성 백혈병(ALL)': 'ALL',
    '만성 골수성 백혈병(CML)': 'CML',
    '만성 림프구성 백혈병(CLL)': 'CLL',
}

    if mode == "일반/암":
        group = st.selectbox("암 그룹 선택", ["미선택/일반", "혈액암", "고형암", "육종", "희귀암"])
        if group == "혈액암":

heme_display = [
    "급성 골수성 백혈병(AML)",
    "급성 전골수구성 백혈병(APL)",
    "급성 림프모구성 백혈병(ALL)",
    "만성 골수성 백혈병(CML)",
    "만성 림프구성 백혈병(CLL)",
]
cancer = st.selectbox("혈액암(진단명)", heme_display)
        elif group == "고형암":
            cancer = st.selectbox("고형암(진단명)", [
                "폐암(Lung cancer)","유방암(Breast cancer)","위암(Gastric cancer)",
                "대장암(Cololoractal cancer)","간암(HCC)","췌장암(Pancreatic cancer)",
                "담도암(Cholangiocarcinoma)","자궁내막암(Endometrial cancer)",
                "구강암/후두암","피부암(흑색종)","신장암(RCC)",
                "갑상선암","난소암","자궁경부암","전립선암","뇌종양(Glioma)","식도암","방광암"
            ])
        elif group == "육종":
            cancer = st.selectbox("육종(진단명)", [
                "연부조직육종(Soft tissue sarcoma)","골육종(Osteosarcoma)","유잉육종(Ewing sarcoma)",
                "평활근육종(Leiomyosarcoma)","지방육종(Liposarcoma)","악성 섬유성 조직구종(UPS/MFH)"
            ])
        elif group == "희귀암":
            cancer = st.selectbox("희귀암(진단명)", [
                "담낭암(Gallbladder cancer)","부신암(Adrenal cancer)","망막모세포종(Retinoblastoma)",
                "흉선종/흉선암(Thymoma/Thymic carcinoma)","신경내분비종양(NET)",
                "간모세포종(Hepatoblastoma)","비인두암(NPC)","GIST"
            ])
        else:
            st.info("암 그룹을 선택하면 해당 암종에 맞는 **항암제 목록과 추가 수치 패널**이 자동 노출됩니다.")
    elif mode == "소아(일상/호흡기)":
        st.markdown("### 🧒 소아 일상 주제 선택")
        st.caption(PED_INPUTS_INFO)
        ped_topic = st.selectbox("소아 주제", ["일상 케어","수분 섭취","해열제 사용","기침/콧물 관리"])
    else:
        st.markdown("### 🧫 소아·영유아 감염질환")
        infect_sel = st.selectbox("질환 선택", list(PED_INFECT.keys()))
        info = PED_INFECT.get(infect_sel, {})
        st.info(f"핵심: {info.get('핵심','')} · 진단: {info.get('진단','')} · 특징: {info.get('특징','')}")
        # 증상 체크리스트
        with st.expander("🧒 증상 체크리스트", expanded=True):
            sel_sym = []
            for i, s in enumerate(PED_SYMPTOMS.get(infect_sel, [])):
                if st.checkbox(s, key=f"sym_{infect_sel}_{i}"):
                    sel_sym.append(s)
            # 공통+질환별 레드 플래그
            reds = list(set(PED_RED_FLAGS.get("공통", []) + PED_RED_FLAGS.get(infect_sel, [])))
            if reds:
                st.markdown("**🚨 레드 플래그(아래 항목이 하나라도 해당되면 진료/응급실 고려)**")
                for i, r in enumerate(reds):
                    st.checkbox(r, key=f"red_{infect_sel}_{i}")
        # 저장
        st.session_state["infect_symptoms"] = sel_sym

    table_mode = st.checkbox("⚙️ PC용 표 모드(가로형)", help="모바일은 세로형 고정 → 줄꼬임 없음.")

    meds = {}
    extras = {}

    if mode == "일반/암" and group and group != "미선택/일반" and cancer:
        st.markdown("### 💊 항암제 선택 및 입력")
        heme_by_cancer = {
            "AML": ["ARA-C","Daunorubicin","Idarubicin","Cyclophosphamide",
                    "Etoposide","Fludarabine","Hydroxyurea","MTX","ATRA","G-CSF"],
            "APL": ["ATRA","Idarubicin","Daunorubicin","ARA-C","G-CSF"],
            "ALL": ["Vincristine","Asparaginase","Daunorubicin","Cyclophosphamide","MTX","ARA-C","Topotecan","Etoposide"],
            "CML": ["Imatinib","Dasatinib","Nilotinib","Hydroxyurea"],
            "CLL": ["Fludarabine","Cyclophosphamide"],
        }
        solid_by_cancer = {
            "폐암(Lung cancer)": ["Cisplatin","Carboplatin","Paclitaxel","Docetaxel","Gemcitabine","Pemetrexed",
                               "Gefitinib","Erlotinib","Osimertinib","Alectinib","Bevacizumab","Pembrolizumab","Nivolumab"],
            "유방암(Breast cancer)": ["Doxorubicin","Cyclophosphamide","Paclitaxel","Docetaxel","Trastuzumab","Bevacizumab"],
            "위암(Gastric cancer)": ["Cisplatin","Oxaliplatin","5-FU","Capecitabine","Paclitaxel","Trastuzumab","Pembrolizumab"],
            "대장암(Cololoractal cancer)": ["5-FU","Capecitabine","Oxaliplatin","Irinotecan","Bevacizumab"],
            "간암(HCC)": ["Sorafenib","Lenvatinib","Bevacizumab","Pembrolizumab","Nivolumab"],
            "췌장암(Pancreatic cancer)": ["Gemcitabine","Oxaliplatin","Irinotecan","5-FU"],
            "담도암(Cholangiocarcinoma)": ["Gemcitabine","Cisplatin","Bevacizumab"],
            "자궁내막암(Endometrial cancer)": ["Carboplatin","Paclitaxel"],
            "구강암/후두암": ["Cisplatin","5-FU","Docetaxel"],
            "피부암(흑색종)": ["Dacarbazine","Paclitaxel","Nivolumab","Pembrolizumab"],
            "신장암(RCC)": ["Sunitinib","Pazopanib","Bevacizumab","Nivolumab","Pembrolizumab"],
            "갑상선암": ["Lenvatinib","Sorafenib"],
            "난소암": ["Carboplatin","Paclitaxel","Bevacizumab"],
            "자궁경부암": ["Cisplatin","Paclitaxel","Bevacizumab"],
            "전립선암": ["Docetaxel","Cabazitaxel"],
            "뇌종양(Glioma)": ["Temozolomide","Bevacizumab"],
            "식도암": ["Cisplatin","5-FU","Paclitaxel","Nivolumab","Pembrolizumab"],
            "방광암": ["Cisplatin","Gemcitabine","Bevacizumab","Pembrolizumab","Nivolumab"],
        }
        sarcoma_by_dx = {
            "연부조직육종(Soft tissue sarcoma)": ["Doxorubicin","Ifosfamide","Pazopanib","Gemcitabine","Docetaxel"],
            "골육종(Osteosarcoma)": ["Doxorubicin","Cisplatin","Ifosfamide","High-dose MTX"],
            "유잉육종(Ewing sarcoma)": ["Vincristine","Doxorubicin","Cyclophosphamide","Ifosfamide","Etoposide"],
            "평활근육종(Leiomyosarcoma)": ["Doxorubicin","Ifosfamide","Gemcitabine","Docetaxel","Pazopanib"],
            "지방육종(Liposarcoma)": ["Doxorubicin","Ifosfamide","Trabectedin"],
            "악성 섬유성 조직구종(UPS/MFH)": ["Doxorubicin","Ifosfamide","Gemcitabine","Docetaxel"],
        }
        rare_by_cancer = {
            "담낭암(Gallbladder cancer)": ["Gemcitabine","Cisplatin"],
            "부신암(Adrenal cancer)": ["Mitotane","Etoposide","Doxorubicin","Cisplatin"],
            "망막모세포종(Retinoblastoma)": ["Vincristine","Etoposide","Carboplatin"],
            "흉선종/흉선암(Thymoma/Thymic carcinoma)": ["Cyclophosphamide","Doxorubicin","Cisplatin"],
            "신경내분비종양(NET)": ["Etoposide","Cisplatin","Sunitinib"],
            "간모세포종(Hepatoblastoma)": ["Cisplatin","Doxorubicin"],
            "비인두암(NPC)": ["Cisplatin","5-FU","Gemcitabine","Bevacizumab","Nivolumab","Pembrolizumab"],
            "GIST": ["Imatinib","Sunitinib","Regorafenib"],
        }
        default_drugs_by_group = {
            "혈액암": heme_by_cancer.get(heme_key_map.get(cancer, cancer), []),
            "고형암": solid_by_cancer.get(cancer, []),
            "육종": sarcoma_by_dx.get(cancer, []),
            "희귀암": rare_by_cancer.get(cancer, []),
        }
        drug_list = list(dict.fromkeys(default_drugs_by_group.get(group, [])))
    else:
        drug_list = []

    if mode == "일반/암":
        st.markdown("### 💊 항암제 선택 및 입력")
        drug_search = st.text_input("🔍 항암제 검색", key="drug_search")
        drug_choices = [d for d in drug_list if not drug_search or drug_search.lower() in d.lower() or drug_search.lower() in ANTICANCER.get(d,{}).get("alias","").lower()]
        selected_drugs = st.multiselect("항암제 선택", drug_choices, default=[])

        for d in selected_drugs:
            alias = ANTICANCER.get(d,{}).get("alias","")
            if d == "ATRA":
                amt = num_input_generic(f"{d} ({alias}) - 캡슐 개수", key=f"med_{d}", as_int=True, placeholder="예: 2")
            elif d == "ARA-C":
                ara_form = st.selectbox(f"{d} ({alias}) - 제형", ["정맥(IV)","피하(SC)","고용량(HDAC)"], key=f"ara_form_{d}")
                amt = num_input_generic(f"{d} ({alias}) - 용량/일", key=f"med_{d}", decimals=1, placeholder="예: 100")
                if amt and float(amt)>0:
                    meds[d] = {"form": ara_form, "dose": amt}
                continue
            else:
                amt = num_input_generic(f"{d} ({alias}) - 용량/알약", key=f"med_{d}", decimals=1, placeholder="예: 1.5")
            if amt and float(amt)>0:
                meds[d] = {"dose_or_tabs": amt}

    st.markdown("### 🧪 항생제 선택 및 입력")
    extras["abx"] = {}
    abx_search = st.text_input("🔍 항생제 검색", key="abx_search")
    abx_choices = [a for a in ABX_GUIDE.keys() if not abx_search or abx_search.lower() in a.lower() or any(abx_search.lower() in tip.lower() for tip in ABX_GUIDE[a])]
    selected_abx = st.multiselect("항생제 계열 선택", abx_choices, default=[])
    for abx in selected_abx:
        extras["abx"][abx] = num_input_generic(f"{abx} - 복용/주입량", key=f"abx_{abx}", decimals=1, placeholder="예: 1")

    st.markdown("### 💧 동반 약물/상태")
    extras["diuretic_amt"] = num_input_generic("이뇨제(복용량/회/일)", key="diuretic_amt", decimals=1, placeholder="예: 1")

    st.divider()
    if mode == "일반/암":
        st.header("2️⃣ 기본 혈액 검사 수치 (입력한 값만 해석)")
    elif mode == "소아(일상/호흡기)":
        st.header("2️⃣ 소아 공통 입력")
    else:
        st.header("2️⃣ (감염질환은 별도 수치 입력 없음)")

    vals = {}

    def render_inputs_vertical():
        st.markdown("**기본 패널**")
        for name in ORDER:
            if name == LBL_CRP:
                vals[name] = num_input_generic(f"{name}", key=f"v_{name}", decimals=2, placeholder="예: 0.12")
            elif name in (LBL_WBC, LBL_ANC, LBL_AST, LBL_ALT, LBL_LDH, LBL_BNP, LBL_Glu):
                vals[name] = num_input_generic(f"{name}", key=f"v_{name}", decimals=1, placeholder="예: 1200")
            else:
                vals[name] = num_input_generic(f"{name}", key=f"v_{name}", decimals=1, placeholder="예: 3.5")

    def render_inputs_table():
        st.markdown("**기본 패널 (표 모드)**")
        left, right = st.columns(2)
        half = (len(ORDER)+1)//2
        with left:
            for name in ORDER[:half]:
                if name == LBL_CRP:
                    vals[name] = num_input_generic(f"{name}", key=f"l_{name}", decimals=2, placeholder="예: 0.12")
                elif name in (LBL_WBC, LBL_ANC, LBL_AST, LBL_ALT, LBL_LDH, LBL_BNP, LBL_Glu):
                    vals[name] = num_input_generic(f"{name}", key=f"l_{name}", decimals=1, placeholder="예: 1200")
                else:
                    vals[name] = num_input_generic(f"{name}", key=f"l_{name}", decimals=1, placeholder="예: 3.5")
        with right:
            for name in ORDER[half:]:
                if name == LBL_CRP:
                    vals[name] = num_input_generic(f"{name}", key=f"r_{name}", decimals=2, placeholder="예: 0.12")
                elif name in (LBL_WBC, LBL_ANC, LBL_AST, LBL_ALT, LBL_LDH, LBL_BNP, LBL_Glu):
                    vals[name] = num_input_generic(f"{name}", key=f"r_{name}", decimals=1, placeholder="예: 1200")
                else:
                    vals[name] = num_input_generic(f"{name}", key=f"r_{name}", decimals=1, placeholder="예: 3.5")

    if mode == "일반/암":
        if table_mode: render_inputs_table()
        else: render_inputs_vertical()
    elif mode == "소아(일상/호흡기)":
        def _parse_num_ped(label, key, decimals=1, placeholder=""):
            raw = st.text_input(label, key=key, placeholder=placeholder)
            return _parse_numeric(raw, decimals=decimals)
        age_m        = _parse_num_ped("나이(개월)", key="ped_age", decimals=0, placeholder="예: 18")
        temp_c       = _parse_num_ped("체온(℃)", key="ped_temp", decimals=1, placeholder="예: 38.2")
        rr           = _parse_num_ped("호흡수(/분)", key="ped_rr", decimals=0, placeholder="예: 42")
        spo2         = _parse_num_ped("산소포화도(%)", key="ped_spo2", decimals=0, placeholder="예: 96")
        urine_24h    = _parse_num_ped("24시간 소변 횟수", key="ped_u", decimals=0, placeholder="예: 6")
        retraction   = _parse_num_ped("흉곽 함몰(0/1)", key="ped_ret", decimals=0, placeholder="0 또는 1")
        nasal_flaring= _parse_num_ped("콧벌렁임(0/1)", key="ped_nf", decimals=0, placeholder="0 또는 1")
        apnea        = _parse_num_ped("무호흡(0/1)", key="ped_ap", decimals=0, placeholder="0 또는 1")

    extra_vals = {}

    if mode == "일반/암":
        st.divider()
        st.header("3️⃣ 특수 검사(토글)")
        t1, t2, t3, t4 = st.columns(4)
        with t1:
            t_coag = st.checkbox("응고패널(PT/aPTT 등)")
        with t2:
            t_comp = st.checkbox("보체(C3/C4/CH50)")
        with t3:
            t_urine = st.checkbox("요검사(단백/잠혈/요당/요Cr)")
        with t4:
            t_lipid = st.checkbox("지질(TG/TC)")

        if t_coag:
            st.markdown("**응고패널**")
            extra_vals["PT"] = num_input_generic("PT (sec)", key="ex_pt", decimals=1, placeholder="예: 12.0")
            extra_vals["aPTT"] = num_input_generic("aPTT (sec)", key="ex_aptt", decimals=1, placeholder="예: 32.0")
            extra_vals["Fibrinogen"] = num_input_generic("Fibrinogen (mg/dL)", key="ex_fbg", decimals=1, placeholder="예: 250")
            extra_vals["D-dimer"] = num_input_generic("D-dimer (µg/mL FEU)", key="ex_dd", decimals=2, placeholder="예: 0.50")

        if t_comp:
            st.markdown("**보체**")
            extra_vals["C3"] = num_input_generic("C3 (mg/dL)", key="ex_c3", decimals=1, placeholder="예: 90")
            extra_vals["C4"] = num_input_generic("C4 (mg/dL)", key="ex_c4", decimals=1, placeholder="예: 20")
            extra_vals["CH50"] = num_input_generic("CH50 (U/mL)", key="ex_ch50", decimals=1, placeholder="예: 50")

        acr = upcr = None
        if t_urine:
            st.markdown("**요검사** — (영문명 병기)")
            u_prot = num_input_generic("요단백(Urine protein, mg/dL)", key="ex_upr", decimals=1, placeholder="예: 30")
            u_bld  = num_input_generic("잠혈(Hematuria, 0/1 또는 RBC/hpf)", key="ex_ubld", decimals=1, placeholder="예: 0")
            u_glu  = num_input_generic("요당(Glycosuria, mg/dL)", key="ex_uglu", decimals=1, placeholder="예: 0")
            u_cr   = num_input_generic("소변 크레아티닌(Urine Cr, mg/dL)", key="ex_ucr", decimals=1, placeholder="예: 100")
            u_alb  = num_input_generic("소변 알부민(Urine albumin, mg/L)", key="ex_ualb", decimals=1, placeholder="예: 30")
            if u_cr and u_prot:
                upcr = round((u_prot * 1000.0) / float(u_cr), 1)
                st.info(f"UPCR(요단백/Cr): **{upcr} mg/g** (≈ 1000×[mg/dL]/[mg/dL])")
            if u_cr and u_alb:
                acr = round((u_alb * 100.0) / float(u_cr), 1)
                st.info(f"ACR(소변 알부민/Cr): **{acr} mg/g** (≈ 100×[mg/L]/[mg/dL])")
            if acr is not None: extra_vals["ACR(mg/g)"] = acr
            if upcr is not None: extra_vals["UPCR(mg/g)"] = upcr
            extra_vals["Urine protein"] = u_prot
            extra_vals["Hematuria"] = u_bld
            extra_vals["Glycosuria"] = u_glu
            extra_vals["Urine Cr"] = u_cr
            extra_vals["Urine albumin"] = u_alb

        if t_lipid:
            st.markdown("**지질**")
            extra_vals["TG"] = num_input_generic("Triglyceride (mg/dL)", key="ex_tg", decimals=0, placeholder="예: 150")
            extra_vals["TC"] = num_input_generic("Total Cholesterol (mg/dL)", key="ex_tc", decimals=0, placeholder="예: 180")

    if mode == "일반/암" and group and group != "미선택/일반" and cancer:
        if group == "혈액암" and heme_key_map.get(cancer, cancer) in ["AML","APL","ALL","CML","CLL"]:
            st.divider()
            st.header("4️⃣ 암별 디테일 수치")
            st.caption("해석은 주치의 판단을 따르며, 값 기록/공유를 돕기 위한 입력 영역입니다.")
            if cancer in ["AML","APL"]:
                extra_vals["DIC Score"] = num_input_generic("DIC Score (pt)", key="ex_dic", decimals=0, placeholder="예: 3")
        elif group == "육종":
            st.divider()
            st.header("4️⃣ 육종 전용 지표")
            extra_vals["ALP"] = num_input_generic("ALP(U/L)", key="ex_alp", decimals=0, placeholder="예: 100")
            extra_vals["CK"] = num_input_generic("CK(U/L)", key="ex_ck", decimals=0, placeholder="예: 150")

    render_schedule(nickname_key)

    st.divider()
    run = st.button("🔎 해석하기", use_container_width=True)

    if run:
        st.subheader(f"📋 해석 결과 — {nickname}#{pin if pin else '----'}")

        if mode == "일반/암":
            lines = interpret_labs(vals, extras)
            for line in lines: st.write(line)

            if nickname_key and "records" in st.session_state and st.session_state.records.get(nickname_key):
                st.markdown("### 🔍 수치 변화 비교 (이전 기록 대비)")
                cmp_lines = compare_with_previous(nickname_key, {k: vals.get(k) for k in ORDER if entered(vals.get(k))})
                if cmp_lines:
                    for l in cmp_lines: st.write(l)
                else:
                    st.info("비교할 이전 기록이 없거나 값이 부족합니다.")

            shown = [ (k, v) for k, v in (extra_vals or {}).items() if entered(v) ]
            if shown:
                st.markdown("### 🧬 특수/암별 디테일 수치")
                for k, v in shown:
                    st.write(f"- {k}: {v}")

            fs = food_suggestions(vals, anc_place)
            if fs:
                st.markdown("### 🥗 음식 가이드 (계절/레시피 포함)")
                for f in fs: st.markdown(f)
        elif mode == "소아(일상/호흡기)":
            st.info("위 위험도 배너를 참고하세요.")
        else:
            st.success("선택한 감염질환 요약을 보고서에 포함했습니다.")

        if meds:
            st.markdown("### 💊 항암제 부작용·상호작용 요약")
            for line in summarize_meds(meds): st.write(line)

        if extras.get("abx"):
            abx_lines = abx_summary(extras["abx"])
            if abx_lines:
                st.markdown("### 🧪 항생제 주의 요약")
                for l in abx_lines: st.write(l)

        st.markdown("### 🌡️ 발열 가이드")
        st.write(FEVER_GUIDE)

        meta = {"group": group, "cancer": cancer, "infect_sel": infect_sel, "anc_place": anc_place, "ped_topic": ped_topic}
        if mode == "소아(일상/호흡기)":
            def _ent(x):
                try: return x is not None and float(x)!=0
                except: return False
            meta["ped_inputs"] = {}
            for k,lab in [("나이(개월)", "ped_age"), ("체온(℃)", "ped_temp"), ("호흡수(/분)", "ped_rr"), ("SpO₂(%)", "ped_spo2"), ("24시간 소변 횟수", "ped_u"),
                          ("흉곽 함몰","ped_ret"),("콧벌렁임","ped_nf"),("무호흡","ped_ap")]:
                v = st.session_state.get(lab)
                if _ent(v): meta["ped_inputs"][k] = v
        elif mode == "소아(감염질환)":
            info = PED_INFECT.get(infect_sel, {})
            meta["infect_info"] = {"핵심": info.get("핵심",""), "진단": info.get("진단",""), "특징": info.get("특징","")}
            # 선택한 증상도 리포트에 포함
            meta["infect_symptoms"] = st.session_state.get("infect_symptoms", [])

        meds_lines = summarize_meds(meds) if meds else []
        abx_lines = abx_summary(extras.get("abx", {})) if extras.get("abx") else []
        cmp_lines = compare_with_previous(nickname_key, {k: vals.get(k) for k in ORDER if entered(vals.get(k))}) if (mode=="일반/암") else []
        food_lines = food_suggestions(vals, anc_place) if (mode=="일반/암") else []

        report_md = build_report(mode, meta, {k: v for k, v in vals.items() if entered(v)}, cmp_lines, extra_vals, meds_lines, food_lines, abx_lines)

        st.download_button("📥 보고서(.md) 다운로드", data=report_md.encode("utf-8"),
                           file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                           mime="text/markdown")
        st.download_button("📄 보고서(.txt) 다운로드", data=report_md.encode("utf-8"),
                           file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                           mime="text/plain")

        try:
            pdf_bytes = md_to_pdf_bytes_fontlocked(report_md)
            st.info("PDF 생성 시 사용 폰트: NanumGothic(제목 Bold/ExtraBold 있으면 자동 적용)")
            st.download_button("🖨️ 보고서(.pdf) 다운로드", data=pdf_bytes,
                               file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                               mime="application/pdf")
        except FileNotFoundError as e:
            st.warning(str(e))
        except Exception as e:
            st.info("PDF 모듈이 없거나 오류가 발생했습니다. (pip install reportlab)")

        if nickname_key and nickname_key.strip():
            rec = {
                "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "mode": mode,
                "group": group,
                "cancer": cancer,
                "infect": infect_sel,
                "labs": {k: vals.get(k) for k in ORDER if entered(vals.get(k))},
                "extra": {k: v for k, v in (locals().get('extra_vals') or {}).items() if entered(v)},
                "meds": meds,
                "extras": extras,
            }
            st.session_state.records.setdefault(nickname_key, []).append(rec)
            st.success("저장되었습니다. 아래 그래프에서 추이를 확인하세요.")
        else:
            st.info("별명과 PIN을 입력하면 추이 그래프를 사용할 수 있어요.")

    render_graphs()

    st.caption(FOOTER_CAFE)
    st.markdown("> " + DISCLAIMER)

if __name__ == "__main__":
    main()
