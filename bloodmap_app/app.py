# -*- coding: utf-8 -*-
def main():
    
    from datetime import datetime, date
    import os
    import streamlit as st
    
    # local modules
    from .config import (APP_TITLE, PAGE_TITLE, MADE_BY, CAFE_LINK_MD, FOOTER_CAFE,
                        DISCLAIMER, ORDER, FEVER_GUIDE,
                        LBL_WBC, LBL_Hb, LBL_PLT, LBL_ANC, LBL_Ca, LBL_P, LBL_Na, LBL_K,
                        LBL_Alb, LBL_Glu, LBL_TP, LBL_AST, LBL_ALT, LBL_LDH, LBL_CRP, LBL_Cr, LBL_UA, LBL_TB, LBL_BUN, LBL_BNP,
                        FONT_PATH_REG)
    from .data.drugs import ANTICANCER, ABX_GUIDE
    from .data.foods import FOODS
    from .data.ped import PED_TOPICS, PED_INPUTS_INFO, PED_INFECT
    from .utils.inputs import num_input_generic, entered, _parse_numeric
    from .utils.interpret import interpret_labs, compare_with_previous, food_suggestions, summarize_meds, abx_summary
    from .utils.reports import build_report, md_to_pdf_bytes_fontlocked
    from .utils.graphs import render_graphs
    from .utils.schedule import render_schedule
    
    # ===== Optional deps =====
    try:
        import pandas as pd
        HAS_PD = True
    except Exception:
        HAS_PD = False
    
    st.set_page_config(page_title=PAGE_TITLE, layout="centered")
    st.title(APP_TITLE)
    st.markdown(MADE_BY)
    st.markdown(CAFE_LINK_MD)

    # ===== SECTION: 공유하기 (moved inside main) =====
    st.markdown("### 🔗 공유하기")
    c1, c2, c3 = st.columns([1,1,2])
    with c1:
        st.link_button("📱 카카오톡/메신저", "https://hdzwo5ginueir7hknzzfg4.streamlit.app/")
    with c2:
        st.link_button("📝 카페/블로그", "https://cafe.naver.com/bloodmap")
    with c3:
        st.code("https://hdzwo5ginueir7hknzzfg4.streamlit.app/", language="text")

    st.caption("✅ 모바일 줄꼬임 방지 · 별명 저장/그래프 · 암별/소아/희귀암 패널 · PDF 한글 폰트 고정 · 수치 변화 비교 · 항암 스케줄표 · 계절 식재료/레시피 · ANC 병원/가정 구분")
    
    os.makedirs("fonts", exist_ok=True)
    # 방문 카운터
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
    
    # ===== UI 1) Patient / Mode =====
    st.divider()
    st.header("1️⃣ 환자/암·소아 정보")
    
    c1, c2 = st.columns(2)
    with c1:
        nickname = st.text_input("별명(저장/그래프/스케줄용)", placeholder="예: 홍길동")
    with c2:
        test_date = st.date_input("검사 날짜", value=date.today())
    
    anc_place = st.radio("현재 식사 장소(ANC 가이드용)", ["가정", "병원"], horizontal=True)
    
    mode = st.selectbox("모드 선택", ["일반/암", "소아(일상/호흡기)", "소아(감염질환)"])
    
    group = None
    cancer = None
    infect_sel = None
    ped_topic = None
    
    if mode == "일반/암":
        group = st.selectbox("암 그룹 선택", ["미선택/일반", "혈액암", "고형암", "소아암", "희귀암"])
        if group == "혈액암":
            cancer = st.selectbox("혈액암 종류", ["AML","APL","ALL","CML","CLL"])
        elif group == "고형암":
            cancer = st.selectbox("고형암 종류", [
                "폐암(Lung cancer)","유방암(Breast cancer)","위암(Gastric cancer)",
                "대장암(Cololoractal cancer)","간암(HCC)","췌장암(Pancreatic cancer)",
                "담도암(Cholangiocarcinoma)","자궁내막암(Endometrial cancer)",
                "구강암/후두암","피부암(흑색종)","육종(Sarcoma)","신장암(RCC)",
                "갑상선암","난소암","자궁경부암","전립선암","뇌종양(Glioma)","식도암","방광암"
            ])
        elif group == "소아암":
            cancer = st.selectbox("소아암 종류", ["Neuroblastoma","Wilms tumor"])
        elif group == "희귀암":
            cancer = st.selectbox("희귀암 종류", [
                "담낭암(Gallbladder cancer)","부신암(Adrenal cancer)","망막모세포종(Retinoblastoma)",
                "흉선종/흉선암(Thymoma/Thymic carcinoma)","신경내분비종양(NET)",
                "간모세포종(Hepatoblastoma)","비인두암(NPC)","GIST"
            ])
        else:
            st.info("암 그룹을 선택하면 해당 암종에 맞는 **항암제 목록과 추가 수치 패널**이 자동 노출됩니다.")
    elif mode == "소아(일상/호흡기)":
        st.markdown("### 🧒 소아 일상 주제 선택")
        st.caption(PED_INPUTS_INFO)
        ped_topic = st.selectbox("소아 주제", PED_TOPICS)
    else:
        st.markdown("### 🧫 소아·영유아 감염질환")
        infect_sel = st.selectbox("질환 선택", list(PED_INFECT.keys()))
        if HAS_PD:
            _df = pd.DataFrame([{
                "핵심": PED_INFECT[infect_sel].get("핵심",""),
                "진단": PED_INFECT[infect_sel].get("진단",""),
                "특징": PED_INFECT[infect_sel].get("특징",""),
            }], index=[infect_sel])
            st.table(_df)
        else:
            st.markdown(f"**{infect_sel}**")
            st.write(f"- 핵심: {PED_INFECT[infect_sel].get('핵심','')}")
            st.write(f"- 진단: {PED_INFECT[infect_sel].get('진단','')}")
            st.write(f"- 특징: {PED_INFECT[infect_sel].get('특징','')}")
    
    table_mode = st.checkbox("⚙️ PC용 표 모드(가로형)", help="모바일은 세로형 고정 → 줄꼬임 없음.")
    
    # ===== Drugs & extras =====
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
            "CLL": ["Fludarabine","Cyclophosphamide","Rituximab"],
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
            "육종(Sarcoma)": ["Doxorubicin","Ifosfamide","Pazopanib"],
            "신장암(RCC)": ["Sunitinib","Pazopanib","Bevacizumab","Nivolumab","Pembrolizumab"],
            "갑상선암": ["Lenvatinib","Sorafenib"],
            "난소암": ["Carboplatin","Paclitaxel","Bevacizumab"],
            "자궁경부암": ["Cisplatin","Paclitaxel","Bevacizumab"],
            "전립선암": ["Docetaxel","Cabazitaxel"],
            "뇌종양(Glioma)": ["Temozolomide","Bevacizumab"],
            "식도암": ["Cisplatin","5-FU","Paclitaxel","Nivolumab","Pembrolizumab"],
            "방광암": ["Cisplatin","Gemcitabine","Bevacizumab","Pembrolizumab","Nivolumab"],
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
            "혈액암": heme_by_cancer.get(cancer, []),
            "고형암": solid_by_cancer.get(cancer, []),
            "소아암": ["Cyclophosphamide","Ifosfamide","Doxorubicin","Vincristine","Etoposide","Carboplatin","Cisplatin","Topotecan","Irinotecan"],
            "희귀암": rare_by_cancer.get(cancer, []),
        }
        drug_list = list(dict.fromkeys(default_drugs_by_group.get(group, [])))
    else:
        drug_list = []
    
    drug_search = st.text_input("🔍 항암제 검색", key="drug_search")
    drug_choices = [d for d in drug_list if not drug_search or (isinstance(drug_search, str) and (drug_search.lower() in d.lower() or drug_search.lower() in ANTICANCER.get(d,{}).get("alias","").lower()))]
    selected_drugs = st.multiselect("항암제 선택", drug_choices, default=[])
    
    meds = {} if 'meds' not in locals() else meds
    for d in selected_drugs:
        alias = ANTICANCER.get(d,{}).get("alias","")
        if d == "ATRA":
            amt = num_input_generic(f"{d} ({alias}) - 캡슐 개수", key=f"med_{d}", as_int=True, placeholder="예: 2")
        elif d == "ARA-C":
            ara_form = st.selectbox(f"{d} ({alias}) - 제형", ["정맥(IV)","피하(SC)","고용량(HDAC)"], key=f"ara_form_{d}")
            amt = num_input_generic(f"{d} ({alias}) - 용량/일", key=f"med_{d}", decimals=1, placeholder="예: 100")
            if amt and float(amt) > 0:
                meds[d] = {"form": ara_form, "dose": amt}
            continue
        else:
            amt = num_input_generic(f"{d} ({alias}) - 용량/알약", key=f"med_{d}", decimals=1, placeholder="예: 1.5")
        if amt and float(amt) > 0:
            meds[d] = {"dose_or_tabs": amt}
    
    st.markdown("### 🧪 항생제 선택 및 입력")
    extras["abx"] = {}
    abx_search = st.text_input("🔍 항생제 검색", key="abx_search")
    abx_choices = [a for a in ABX_GUIDE.keys() if not abx_search or (isinstance(abx_search, str) and (abx_search.lower() in a.lower() or any(abx_search.lower() in tip.lower() for tip in ABX_GUIDE[a])))]
    selected_abx = st.multiselect("항생제 계열 선택", abx_choices, default=[])
    for abx in selected_abx:
        extras["abx"][abx] = num_input_generic(f"{abx} - 복용/주입량", key=f"abx_{abx}", decimals=1, placeholder="예: 1")
    
    st.markdown("### 💧 동반 약물/상태")
    extras["diuretic_amt"] = num_input_generic("이뇨제(복용량/회/일)", key="diuretic_amt", decimals=1, placeholder="예: 1")
    
    # ===== UI 2) Inputs =====
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
        if table_mode:
            render_inputs_table()
        else:
            render_inputs_vertical()
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
    
    # ===== UI 3) Extras =====
    extra_vals = {}
    def ped_risk_banner(age_m, temp_c, rr, spo2, urine_24h, retraction, nasal_flaring, apnea):
        danger=False; urgent=False; notes=[]
        if spo2 and spo2<92: danger=True; notes.append("SpO₂<92%")
        if apnea and apnea>=1: danger=True; notes.append("무호흡")
        if rr and ((age_m and age_m<=12 and rr>60) or (age_m and age_m>12 and rr>50)): urgent=True; notes.append("호흡수 상승")
        if temp_c and temp_c>=39.0: urgent=True; notes.append("고열")
        if retraction and retraction>=1: urgent=True; notes.append("흉곽 함몰")
        if nasal_flaring and nasal_flaring>=1: urgent=True; notes.append("콧벌렁임")
        if urine_24h and urine_24h < max(3, int(24*0.25)): urgent=True; notes.append("소변 감소")
        if danger: st.error("🚑 위급 신호: 즉시 병원/응급실 평가 권고 — " + ", ".join(notes))
        elif urgent: st.warning("⚠️ 주의: 빠른 진료 필요 — " + ", ".join(notes))
        else: st.success("🙂 가정관리 가능 신호(경과관찰). 상태 변화 시 즉시 의료진과 상의")
    
    if mode == "일반/암" and group and group != "미선택/일반" and cancer:
        items = {
            "AML": [("PT","PT","sec",1),("aPTT","aPTT","sec",1),("Fibrinogen","Fibrinogen","mg/dL",1),("D-dimer","D-dimer","µg/mL FEU",2)],
            "APL": [("PT","PT","sec",1),("aPTT","aPTT","sec",1),("Fibrinogen","Fibrinogen","mg/dL",1),("D-dimer","D-dimer","µg/mL FEU",2),("DIC Score","DIC Score","pt",0)],
            "ALL": [("PT","PT","sec",1),("aPTT","aPTT","sec",1),("CNS Sx","CNS 증상 여부(0/1)","",0)],
            "CML": [("BCR-ABL PCR","BCR-ABL PCR","%IS",2),("Basophil%","기저호염기구(Baso) 비율","%",1)],
            "CLL": [("IgG","면역글로불린 IgG","mg/dL",0),("IgA","면역글로불린 IgA","mg/dL",0),("IgM","면역글로불린 IgM","mg/dL",0)],
            "폐암(Lung cancer)": [("CEA","CEA","ng/mL",1),("CYFRA 21-1","CYFRA 21-1","ng/mL",1),("NSE","Neuron-specific enolase","ng/mL",1)],
            "유방암(Breast cancer)": [("CA15-3","CA15-3","U/mL",1),("CEA","CEA","ng/mL",1),("HER2","HER2","IHC/FISH",0),("ER/PR","ER/PR","%",0)],
            "위암(Gastric cancer)": [("CEA","CEA","ng/mL",1),("CA72-4","CA72-4","U/mL",1),("CA19-9","CA19-9","U/mL",1)],
            "대장암(Cololoractal cancer)": [("CEA","CEA","ng/mL",1),("CA19-9","CA19-9","U/mL",1)],
            "간암(HCC)": [("AFP","AFP","ng/mL",1),("PIVKA-II","PIVKA-II(DCP)","mAU/mL",0)],
            "피부암(흑색종)": [("S100","S100","µg/L",1),("LDH","LDH","U/L",0)],
            "육종(Sarcoma)": [("ALP","ALP","U/L",0),("CK","CK","U/L",0)],
            "신장암(RCC)": [("CEA","CEA","ng/mL",1),("LDH","LDH","U/L",0)],
            "식도암": [("SCC Ag","SCC antigen","ng/mL",1),("CEA","CEA","ng/mL",1)],
            "방광암": [("NMP22","NMP22","U/mL",1),("UBC","UBC","µg/L",1)],
        }.get(cancer, [])
        if items:
            st.divider()
            st.header("3️⃣ 암별 디테일 수치")
            st.caption("해석은 주치의 판단을 따르며, 값 기록/공유를 돕기 위한 입력 영역입니다.")
            for key, label, unit, decs in items:
                ph = f"예: {('0' if decs==0 else '0.'+('0'*decs))}" if decs is not None else ""
                val = num_input_generic(f"{label}" + (f" ({unit})" if unit else ""), key=f"extra_{key}", decimals=decs, placeholder=ph)
                extra_vals[key] = val
    elif mode == "소아(일상/호흡기)":
        st.divider()
        st.header("3️⃣ 소아 생활 가이드")
        # 방어: 값이 정의되지 않았을 때 기본값
        age_m = locals().get("age_m", 0) or 0
        temp_c = locals().get("temp_c", 0) or 0
        rr = locals().get("rr", 0) or 0
        spo2 = locals().get("spo2", 0) or 0
        urine_24h = locals().get("urine_24h", 0) or 0
        retraction = locals().get("retraction", 0) or 0
        nasal_flaring = locals().get("nasal_flaring", 0) or 0
        apnea = locals().get("apnea", 0) or 0
        ped_risk_banner(age_m, temp_c, rr, spo2, urine_24h, retraction, nasal_flaring, apnea)
    else:
        st.divider()
        st.header("3️⃣ 감염질환 요약")
        st.info("표는 위 선택창에서 자동 생성됩니다.")
    
    # ===== Schedule =====
    render_schedule(nickname)
    
    # ===== Run =====
    st.divider()
    run = st.button("🔎 해석하기", use_container_width=True)
    
    if run:
        st.subheader("📋 해석 결과")
    
        if mode == "일반/암":
            lines = interpret_labs(vals, extras)
            for line in lines: st.write(line)
    
            if nickname and "records" in st.session_state and st.session_state.records.get(nickname):
                st.markdown("### 🔍 수치 변화 비교 (이전 기록 대비)")
                cmp_lines = compare_with_previous(nickname, {k: vals.get(k) for k in ORDER if entered(vals.get(k))})
                if cmp_lines:
                    for l in cmp_lines: st.write(l)
                else:
                    st.info("비교할 이전 기록이 없거나 값이 부족합니다.")
    
            shown = [ (k, v) for k, v in (extra_vals or {}).items() if entered(v) ]
            if shown:
                st.markdown("### 🧬 암별 디테일 수치")
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
    
        # --- Build report text ---
        meta = {
            "group": group, "cancer": cancer, "infect_sel": infect_sel, "anc_place": anc_place,
            "ped_topic": ped_topic,
        }
        if mode == "소아(일상/호흡기)":
            def _ent(x):
                try: return x is not None and float(x)!=0
                except: return False
            meta["ped_inputs"] = {}
            if _ent(age_m): meta["ped_inputs"]["나이(개월)"] = int(age_m)
            if _ent(temp_c): meta["ped_inputs"]["체온(℃)"] = f"{float(temp_c):.1f}"
            if _ent(rr): meta["ped_inputs"]["호흡수(/분)"] = int(rr)
            if _ent(spo2): meta["ped_inputs"]["SpO₂(%)"] = int(spo2)
            if _ent(urine_24h): meta["ped_inputs"]["24시간 소변 횟수"] = int(urine_24h)
            if _ent(retraction): meta["ped_inputs"]["흉곽 함몰"] = int(retraction)
            if _ent(nasal_flaring): meta["ped_inputs"]["콧벌렁임"] = int(nasal_flaring)
            if _ent(apnea): meta["ped_inputs"]["무호흡"] = int(apnea)
        elif mode == "소아(감염질환)":
            info = PED_INFECT.get(infect_sel, {})
            meta["infect_info"] = {"핵심": info.get("핵심",""), "진단": info.get("진단",""), "특징": info.get("특징","")}
    
        meds_lines = summarize_meds(meds) if meds else []
        abx_lines = abx_summary(extras.get("abx", {})) if extras.get("abx") else []
        cmp_lines = compare_with_previous(nickname, {k: vals.get(k) for k in ORDER if entered(vals.get(k))}) if (mode=="일반/암") else []
        food_lines = food_suggestions(vals, anc_place) if (mode=="일반/암") else []
    
        report_md = build_report(mode, meta, vals, cmp_lines, extra_vals, meds_lines, food_lines, abx_lines)
    
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
    
        if nickname and nickname.strip():
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
            st.session_state.records.setdefault(nickname, []).append(rec)
            st.success("저장되었습니다. 아래 그래프에서 추이를 확인하세요.")
        else:
            st.info("별명을 입력하면 추이 그래프를 사용할 수 있어요.")
    
    # ===== Graphs =====
    render_graphs()
    
    st.markdown("---")
    st.header("📚 약물 사전 (스크롤 최소화 뷰어)")
    with st.expander("열기 / 닫기", expanded=False):
        st.caption("빠르게 찾아보고 싶은 약을 검색하세요. 결과는 페이지로 나눠서 보여줍니다.")
        view_tab1, view_tab2 = st.tabs(["항암제 사전", "항생제 사전"])
    
        # 항암제 사전
        with view_tab1:
            ac_rows = []
            for k, v in ANTICANCER.items():
                alias = v.get("alias","")
                aes = ", ".join(v.get("aes", []))
                tags = []
                key = k.lower()
                if any(x in key for x in ["mab","nib","pembro","nivo","tuzu","zumab"]):
                    tags.append("표적/면역")
                if k in ["Imatinib","Dasatinib","Nilotinib","Sunitinib","Pazopanib","Regorafenib","Lenvatinib","Sorafenib"]:
                    tags.append("TKI")
                if k in ["Pembrolizumab","Nivolumab","Trastuzumab","Bevacizumab"]:
                    tags.append("면역/항체")
                ac_rows.append({"약물": k, "한글명": alias, "부작용": aes, "태그": ", ".join(tags)})
            if HAS_PD:
                import pandas as pd
                ac_df = pd.DataFrame(ac_rows)
            else:
                ac_df = None
            q = st.text_input("🔎 약물명/한글명/부작용/태그 검색", key="drug_search_ac", placeholder="예: MTX, 간독성, 면역, TKI ...")
            page_size = st.selectbox("페이지 크기", [5, 10, 15, 20], index=1, key="ac_page_size")
            if HAS_PD and ac_df is not None:
                fdf = ac_df.copy()
                if q:
                    ql = q.strip().lower()
                    mask = (
                        fdf["약물"].str.lower().str.contains(ql) |
                        fdf["한글명"].str.lower().str.contains(ql) |
                        fdf["부작용"].str.lower().str.contains(ql) |
                        fdf["태그"].str.lower().str.contains(ql)
                    )
                    fdf = fdf[mask]
                total = len(fdf)
                st.caption(f"검색 결과: {total}건")
                if total == 0:
                    st.info("검색 결과가 없습니다.")
                else:
                    max_page = (total - 1) // page_size + 1
                    cur_page = st.number_input("페이지", min_value=1, max_value=max_page, value=1, step=1, key="ac_page")
                    start = (cur_page - 1) * page_size
                    end = start + page_size
                    show_df = fdf.iloc[start:end]
                    for _, row in show_df.iterrows():
                        with st.container(border=True):
                            st.markdown(f"**{row['약물']}** · {row['한글명']}")
                            st.caption(f"태그: {row['태그'] if row['태그'] else '—'}")
                            st.write("부작용: " + (row["부작용"] if row["부작용"] else "—"))
            else:
                st.info("pandas 설치 시 검색/페이지 기능이 활성화됩니다.")
    
        # 항생제 사전
        with view_tab2:
            abx_rows = [{"계열": cat, "주의사항": ", ".join(tips)} for cat, tips in ABX_GUIDE.items()]
            if HAS_PD:
                import pandas as pd
                abx_df = pd.DataFrame(abx_rows)
            else:
                abx_df = None
            q2 = st.text_input("🔎 계열/주의사항 검색", key="drug_search_abx", placeholder="예: QT, 광과민, 와파린 ...")
            page_size2 = st.selectbox("페이지 크기", [5, 10, 15, 20], index=1, key="abx_page_size")
            if HAS_PD and abx_df is not None:
                fdf2 = abx_df.copy()
                if q2:
                    ql2 = q2.strip().lower()
                    mask2 = (
                        fdf2["계열"].str.lower().str.contains(ql2) |
                        fdf2["주의사항"].str.lower().str.contains(ql2)
                    )
                    fdf2 = fdf2[mask2]
                total2 = len(fdf2)
                st.caption(f"검색 결과: {total2}건")
                if total2 == 0:
                    st.info("검색 결과가 없습니다.")
                else:
                    max_page2 = (total2 - 1) // page_size2 + 1
                    cur_page2 = st.number_input("페이지", min_value=1, max_value=max_page2, value=1, step=1, key="abx_page")
                    start2 = (cur_page2 - 1) * page_size2
                    end2 = start2 + page_size2
                    show_df2 = fdf2.iloc[start2:end2]
                    for _, row in show_df2.iterrows():
                        with st.container(border=True):
                            st.markdown(f"**{row['계열']}**")
                            st.write("주의사항: " + (row["주의사항"] if row["주의사항"] else "—"))
            else:
                st.info("pandas 설치 시 검색/페이지 기능이 활성화됩니다.")
    
    st.caption(FOOTER_CAFE)
    st.markdown("> " + DISCLAIMER)
