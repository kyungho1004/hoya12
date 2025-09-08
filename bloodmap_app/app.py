
# -*- coding: utf-8 -*-
from datetime import datetime, date
import os
import streamlit as st

# --- Import compatibility: package or direct-run ---
try:
    from .config import (APP_TITLE, PAGE_TITLE, MADE_BY, CAFE_LINK_MD, FOOTER_CAFE,
                        DISCLAIMER, ORDER, FEVER_GUIDE,
                        LBL_WBC, LBL_Hb, LBL_PLT, LBL_ANC, LBL_Ca, LBL_P, LBL_Na, LBL_K,
                        LBL_Alb, LBL_Glu, LBL_TP, LBL_AST, LBL_ALT, LBL_LDH, LBL_CRP, LBL_Cr, LBL_UA, LBL_TB, LBL_BUN, LBL_BNP,
                        FONT_PATH_REG)
    from .data.drugs import ANTICANCER, ABX_GUIDE
    from .data.ped import PED_TOPICS, PED_INPUTS_INFO, PED_INFECT
    from .utils.inputs import num_input_generic, entered
    from .utils.interpret import interpret_labs, compare_with_previous, food_suggestions, summarize_meds, abx_summary
    from .utils.reports import build_report, md_to_pdf_bytes_fontlocked
    from .utils.graphs import render_graphs
    from .utils.schedule import render_schedule
except Exception:
    from config import (APP_TITLE, PAGE_TITLE, MADE_BY, CAFE_LINK_MD, FOOTER_CAFE,
                        DISCLAIMER, ORDER, FEVER_GUIDE,
                        LBL_WBC, LBL_Hb, LBL_PLT, LBL_ANC, LBL_Ca, LBL_P, LBL_Na, LBL_K,
                        LBL_Alb, LBL_Glu, LBL_TP, LBL_AST, LBL_ALT, LBL_LDH, LBL_CRP, LBL_Cr, LBL_UA, LBL_TB, LBL_BUN, LBL_BNP,
                        FONT_PATH_REG)
    from data.drugs import ANTICANCER, ABX_GUIDE
    from data.ped import PED_TOPICS, PED_INPUTS_INFO, PED_INFECT
    from utils.inputs import num_input_generic, entered
    from utils.interpret import interpret_labs, compare_with_previous, food_suggestions, summarize_meds, abx_summary
    from utils.reports import build_report, md_to_pdf_bytes_fontlocked
    from utils.graphs import render_graphs
    from utils.schedule import render_schedule

try:
    HAS_PD = True
except Exception:
    HAS_PD = False

def main():
    st.set_page_config(page_title=PAGE_TITLE, layout="centered")
    st.title(APP_TITLE); st.markdown(MADE_BY); st.markdown(CAFE_LINK_MD)

    # 스타일
    try:
        with open(os.path.join(os.path.dirname(__file__), "style.css"), "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception:
        pass

    if "records" not in st.session_state: st.session_state.records = {}
    if "schedules" not in st.session_state: st.session_state.schedules = {}

    st.divider(); st.header("1️⃣ 환자/암·소아 정보")
    c1, c2, c3 = st.columns([1,1,1])
    with c1: nickname = st.text_input("별명", placeholder="예: 홍길동")
    with c2: pin = st.text_input("PIN(4자리)", max_chars=4, placeholder="예: 1234")
    with c3: test_date = st.date_input("검사 날짜", value=date.today())
    _ok_pin = lambda p: p.isdigit() and len(p)==4
    patient_id = f"{nickname.strip()}#{pin}" if (nickname and pin and _ok_pin(pin)) else None
    if nickname and pin and not _ok_pin(pin): st.warning("PIN은 숫자 4자리여야 합니다.")

    anc_place = st.radio("현재 식사 장소(ANC 가이드용)", ["가정", "병원"], horizontal=True)
    mode = st.selectbox("모드 선택", ["일반/암", "소아(일상/호흡기)", "소아(감염질환)"])

    group = None; cancer = None; infect_sel = None; ped_topic = None; sarcoma_sub = None; _heme_code = None
    if mode == "일반/암":
        group = st.selectbox("암 그룹 선택", ["미선택/일반", "혈액암", "고형암", "소아암", "희귀암"])
        if group == "혈액암":
            heme_options = [
                ("AML","급성 골수성 백혈병(AML)"),
                ("APL","급성 전골수구성 백혈병(APL)"),
                ("ALL","급성 림프구성 백혈병(ALL)"),
                ("CML","만성 골수성 백혈병(CML)"),
                ("CLL","만성 림프구성 백혈병(CLL)"),
            ]
            cancer_label = st.selectbox("혈액암 종류", [label for code, label in heme_options])
            _heme_code = next(code for code, label in heme_options if label == cancer_label)
            cancer = cancer_label
        elif group == "고형암":
            cancer = st.selectbox("고형암 종류", [
                "폐암(Lung cancer)","유방암(Breast cancer)","위암(Gastric cancer)",
                "대장암(Cololoractal cancer)","간암(HCC)","췌장암(Pancreatic cancer)",
                "담도암(Cholangiocarcinoma)","자궁내막암(Endometrial cancer)",
                "구강암/후두암","피부암(흑색종)","육종(Sarcoma)","신장암(RCC)",
                "갑상선암","난소암","자궁경부암","전립선암","뇌종양(Glioma)","식도암","방광암"
            ])
            if cancer == "육종(Sarcoma)":
                sarcoma_sub = st.selectbox("육종 진단명", [
                    "골육종(Osteosarcoma)","유잉육종(Ewing sarcoma)","평활근육종(Leiomyosarcoma)",
                    "지방육종(Liposarcoma)","횡문근육종(Rhabdomyosarcoma)"
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
            st.info("암 그룹 선택 시 해당 암종 항암제/특수검사 자동 노출.")
    elif mode == "소아(일상/호흡기)":
        st.markdown("### 🧒 소아 일상 주제"); st.caption(PED_INPUTS_INFO)
        ped_topic = st.selectbox("소아 주제", PED_TOPICS)
    else:
        st.markdown("### 🧫 소아 감염질환")
        infect_sel = st.selectbox("질환 선택", list(PED_INFECT.keys()))
        if HAS_PD:
            _df = _pd.DataFrame([{
                "핵심": PED_INFECT[infect_sel].get("핵심",""),
                "진단": PED_INFECT[infect_sel].get("진단",""),
                "특징": PED_INFECT[infect_sel].get("특징",""),
            }], index=[infect_sel])
            st.table(_df)
        else:
            st.markdown(f"**{infect_sel}**")
            _info = PED_INFECT.get(infect_sel, {})
            st.write("- 핵심:", _info.get("핵심", ""))
            st.write("- 진단:", _info.get("진단", ""))
            st.write("- 특징:", _info.get("특징", ""))

    table_mode = st.checkbox("⚙️ PC용 표 모드(가로형)")

    meds = {}; extras = {}
    if mode == "일반/암" and group and group != "미선택/일반" and (cancer or sarcoma_sub):
        st.markdown("### 💊 항암제 선택 및 입력")
        heme_by_cancer = {
            "AML": ["ARA-C","Daunorubicin","Idarubicin","Cyclophosphamide","Etoposide","Fludarabine","Hydroxyurea","MTX","ATRA","G-CSF"],
            "APL": ["ATRA","Idarubicin","Daunorubicin","ARA-C","G-CSF","MTX","6-MP"],
            "ALL": ["Vincristine","Asparaginase","Daunorubicin","Cyclophosphamide","MTX","ARA-C","Topotecan","Etoposide"],
            "CML": ["Imatinib","Dasatinib","Nilotinib","Hydroxyurea"],
            "CLL": ["Fludarabine","Cyclophosphamide","Rituximab"],
        }
        solid_by_cancer = {
            "폐암(Lung cancer)": ["Cisplatin","Carboplatin","Paclitaxel","Docetaxel","Gemcitabine","Pemetrexed","Gefitinib","Erlotinib","Osimertinib","Alectinib","Bevacizumab","Pembrolizumab","Nivolumab"],
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

        if cancer == "육종(Sarcoma)" and sarcoma_sub:
            base = ["Doxorubicin","Ifosfamide"]
            if "횡문근육종" in sarcoma_sub: base = ["Vincristine","Ifosfamide","Doxorubicin"]
            drug_list = base
        else:
            key_cancer = _heme_code if (group == "혈액암" and _heme_code) else cancer
            default_by_group = {
                "혈액암": heme_by_cancer.get(key_cancer, []),
                "고형암": solid_by_cancer.get(cancer, []),
                "소아암": ["Cyclophosphamide","Ifosfamide","Doxorubicin","Vincristine","Etoposide","Carboplatin","Cisplatin","Topotecan","Irinotecan"],
                "희귀암": rare_by_cancer.get(cancer, []),
            }
            drug_list = list(dict.fromkeys(default_by_group.get(group, [])))
    else:
        drug_list = []

    def _disp(drug):
        alias = ANTICANCER.get(drug, {}).get("alias", "")
        return f"{drug} ({alias})" if alias else drug

    if mode == "일반/암":
        drug_search = st.text_input("🔍 항암제 검색", key="drug_search")
        drug_choices = [d for d in drug_list if not drug_search or drug_search.lower() in d.lower() or drug_search.lower() in ANTICANCER.get(d,{}).get("alias","").lower()]
        display_choices = [_disp(d) for d in drug_choices]
        pick = st.multiselect("항암제 선택", display_choices, default=[])
        rev = {_disp(d): d for d in drug_choices}
        selected_drugs = [rev[x] for x in pick]
        meds = {}
        for d in selected_drugs:
            alias = ANTICANCER.get(d,{}).get("alias","")
            if d == "ATRA":
                amt = num_input_generic(f"{d} ({alias}) - 캡슐 개수", key=f"med_{d}", as_int=True, placeholder="예: 2")
            elif d == "ARA-C":
                ara_form = st.selectbox(f"{d} ({alias}) - 제형", ["정맥(IV)","피하(SC)","고용량(HDAC)"], key=f"ara_form_{d}")
                amt = num_input_generic(f"{d} ({alias}) - 용량/일", key=f"med_{d}", decimals=1, placeholder="예: 100")
                if amt and float(amt)>0: meds[d] = {"form": ara_form, "dose": amt}; continue
            else:
                amt = num_input_generic(f"{d} ({alias}) - 용량/알약", key=f"med_{d}", decimals=1, placeholder="예: 1.5")
            if amt and float(amt) > 0: meds[d] = {"dose_or_tabs": amt}
    else:
        meds = {}

    st.markdown("### 🧪 항생제 선택 및 입력 (한글 병기)")
    extras = {"abx": {}}
    abx_search = st.text_input("🔍 항생제 검색", key="abx_search")
    abx_choices = [a for a in ABX_GUIDE.keys() if not abx_search or abx_search.lower() in a.lower()]
    selected_abx = st.multiselect("항생제 계열 선택", abx_choices, default=[])
    for abx in selected_abx:
        extras["abx"][abx] = num_input_generic(f"{abx} - 복용/주입량", key=f"abx_{abx}", decimals=1, placeholder="예: 1")

    st.markdown("### 💧 동반 약물/상태")
    extras["diuretic_amt"] = num_input_generic("이뇨제(복용량/회/일)", key="diuretic_amt", decimals=1, placeholder="예: 1")

    st.divider()
    if mode == "일반/암": st.header("2️⃣ 기본 혈액 검사 수치 (입력한 값만 해석)")
    elif mode == "소아(일상/호흡기)": st.header("2️⃣ 소아 공통 입력")
    else: st.header("2️⃣ (감염질환은 별도 수치 입력 없음)")

    vals = {}
    def render_inputs_vertical():
        st.markdown("**기본 패널**")
        for name in ORDER:
            dec = 2 if name=="CRP" else 1
            vals[name] = num_input_generic(f"{name}", key=f"v_{name}", decimals=dec, placeholder="예: 0.1")

    def render_inputs_table():
        st.markdown("**기본 패널 (표 모드)**")
        left, right = st.columns(2)
        half = (len(ORDER)+1)//2
        for col, names in zip((left, right), (ORDER[:half], ORDER[half:])):
            with col:
                for name in names:
                    dec = 2 if name=="CRP" else 1
                    vals[name] = num_input_generic(f"{name}", key=f"t_{name}", decimals=dec, placeholder="예: 0.1")

    if mode == "일반/암":
        render_inputs_table() if table_mode else render_inputs_vertical()
    elif mode == "소아(일상/호흡기)":
        def _num(label, key, decimals=1, ph=""):
            raw = st.text_input(label, key=key, placeholder=ph)
            try:
                if raw in (None,""): return None
                v = float(str(raw).strip())
                return round(v, decimals) if decimals is not None else v
            except Exception: return None
        age_m = _num("나이(개월)", "ped_age", 0, "예: 18")
        temp_c = _num("체온(℃)", "ped_temp", 1, "예: 38.2")
        rr = _num("호흡수(/분)", "ped_rr", 0, "예: 42")
        spo2 = _num("산소포화도(%)", "ped_spo2", 0, "예: 96")
        urine_24h = _num("24시간 소변 횟수", "ped_u", 0, "예: 6")
        retraction = _num("흉곽 함몰(0/1)", "ped_ret", 0, "0 또는 1")
        nasal_flaring = _num("콧벌렁임(0/1)", "ped_nf", 0, "0 또는 1")
        apnea = _num("무호흡(0/1)", "ped_ap", 0, "0 또는 1")

    extra_vals = {}
    if mode == "일반/암" and group and group != "미선택/일반" and (cancer or sarcoma_sub):
        items_map = {
            "AML": [("PT","PT","sec",1),("aPTT","aPTT","sec",1),("Fibrinogen","Fibrinogen","mg/dL",1),("D-dimer","D-dimer","µg/mL FEU",2)],
            "APL": [("PT","PT","sec",1),("aPTT","aPTT","sec",1),("Fibrinogen","Fibrinogen","mg/dL",1),("D-dimer","D-dimer","µg/mL FEU",2),("DIC Score","DIC Score","pt",0)],
            "ALL": [("PT","PT","sec",1),("aPTT","aPTT","sec",1),("CNS Sx","CNS 증상 여부(0/1)","",0)],
            "CML": [("BCR-ABL PCR","BCR-ABL PCR","%IS",2),("Basophil%","기저호염기구 비율","%",1)],
            "CLL": [("IgG","IgG","mg/dL",0),("IgA","IgA","mg/dL",0),("IgM","IgM","mg/dL",0)],
            "폐암(Lung cancer)": [("CEA","CEA","ng/mL",1),("CYFRA 21-1","CYFRA 21-1","ng/mL",1),("NSE","NSE","ng/mL",1)],
            "유방암(Breast cancer)": [("CA15-3","CA15-3","U/mL",1),("CEA","CEA","ng/mL",1),("HER2","HER2","IHC/FISH",0),("ER/PR","ER/PR","%",0)],
            "위암(Gastric cancer)": [("CEA","CEA","ng/mL",1),("CA72-4","CA72-4","U/mL",1),("CA19-9","CA19-9","U/mL",1)],
            "대장암(Cololoractal cancer)": [("CEA","CEA","ng/mL",1),("CA19-9","CA19-9","U/mL",1)],
            "간암(HCC)": [("AFP","AFP","ng/mL",1),("PIVKA-II","PIVKA-II(DCP)","mAU/mL",0)],
            "피부암(흑색종)": [("S100","S100","µg/L",1),("LDH","LDH","U/L",0)],
            "육종(Sarcoma)": [("ALP","ALP","U/L",0),("CK","CK","U/L",0)],
            "신장암(RCC)": [("CEA","CEA","ng/mL",1),("LDH","LDH","U/L",0)],
            "식도암": [("SCC Ag","SCC antigen","ng/mL",1),("CEA","CEA","ng/mL",1)],
            "방광암": [("NMP22","NMP22","U/mL",1),("UBC","UBC","µg/L",1)],
        }
        key_cancer = _heme_code if (group == "혈액암" and _heme_code) else cancer
        items = items_map.get(key_cancer, [])
        if cancer == "육종(Sarcoma)" and sarcoma_sub:
            if "골육종" in sarcoma_sub: items = [("ALP","ALP","U/L",0)]
            elif "횡문근육종" in sarcoma_sub: items = [("CK","CK","U/L",0)]
        if items:
            st.divider(); st.header("3️⃣ 암별 디테일 수치")
            for key, label, unit, decs in items:
                ph = f"예: {('0' if decs==0 else '0.'+('0'*decs))}" if decs is not None else ""
                val = num_input_generic(f"{label}" + (f" ({unit})" if unit else ""), key=f"extra_{key}", decimals=decs, placeholder=ph)
                extra_vals[key] = val
    elif mode == "소아(일상/호흡기)":
        st.divider(); st.header("3️⃣ 소아 생활 가이드")
        def ped_banner(age_m, temp_c, rr, spo2, urine_24h, retraction, nasal_flaring, apnea):
            danger=False; urgent=False; notes=[]
            if spo2 and spo2<92: danger=True; notes.append("SpO₂<92%")
            if apnea and apnea>=1: danger=True; notes.append("무호흡")
            if rr and ((age_m and age_m<=12 and rr>60) or (age_m and age_m>12 and rr>50)): urgent=True; notes.append("호흡수↑")
            if temp_c and temp_c>=39.0: urgent=True; notes.append("고열")
            if retraction and retraction>=1: urgent=True; notes.append("흉곽 함몰")
            if nasal_flaring and nasal_flaring>=1: urgent=True; notes.append("콧벌렁임")
            if urine_24h and urine_24h<3: urgent=True; notes.append("소변 감소")
            if danger: st.error("🚑 즉시 병원/응급실 — " + ", ".join(notes))
            elif urgent: st.warning("⚠️ 빠른 진료 필요 — " + ", ".join(notes))
            else: st.success("🙂 가정관리 가능 신호. 변화 시 즉시 상의.")
        # placeholders if not defined
        for n in ["age_m","temp_c","rr","spo2","urine_24h","retraction","nasal_flaring","apnea"]:
            if n not in locals(): locals()[n] = None
        ped_banner(locals()["age_m"], locals()["temp_c"], locals()["rr"], locals()["spo2"],
                   locals()["urine_24h"], locals()["retraction"], locals()["nasal_flaring"], locals()["apnea"])
    else:
        st.divider(); st.header("3️⃣ 감염질환 요약"); st.info("선택한 감염질환 정보는 보고서에 포함됩니다.")

    render_schedule(patient_id)

    st.divider()
    run = st.button("🔎 해석하기", use_container_width=True)
    if run:
        st.subheader("📋 해석 결과")
        if mode == "일반/암":
            lines = interpret_labs(vals, extras)
            for l in lines: st.write(l)
            if patient_id and st.session_state.records.get(patient_id):
                st.markdown("### 🔍 수치 변화 비교 (이전 기록 대비)")
                cmp_lines = compare_with_previous(patient_id, {k: vals.get(k) for k in ORDER if entered(vals.get(k))})
                if cmp_lines: 
                    for l in cmp_lines: st.write(l)
                else: st.info("비교할 이전 기록이 없거나 값이 부족합니다.")
            shown = [(k,v) for k,v in (extra_vals or {}).items() if entered(v)]
            if shown:
                st.markdown("### 🧬 암별 디테일 수치")
                for k,v in shown: st.write(f"- {k}: {v}")
            fs = food_suggestions(vals, anc_place)
            if fs:
                st.markdown("### 🥗 음식 가이드")
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

        st.markdown("### 🌡️ 발열 가이드"); st.write(FEVER_GUIDE)

        meta = {"group": group, "cancer": cancer, "infect_sel": infect_sel, "anc_place": anc_place, "ped_topic": ped_topic}
        if mode == "소아(일상/호흡기)":
            def _ent(x): 
                try: return x is not None and float(x)!=0
                except Exception: return False
            meta["ped_inputs"] = {}
            for k, v in {"나이(개월)":locals().get("age_m"),"체온(℃)":locals().get("temp_c"),"호흡수(/분)":locals().get("rr"),
                         "SpO₂(%)":locals().get("spo2"),"24시간 소변 횟수":locals().get("urine_24h"),
                         "흉곽 함몰":locals().get("retraction"),"콧벌렁임":locals().get("nasal_flaring"),"무호흡":locals().get("apnea")}.items():
                if _ent(v): meta["ped_inputs"][k]=v
        elif mode == "소아(감염질환)":
            info = PED_INFECT.get(infect_sel, {})
            meta["infect_info"] = {"핵심": info.get("핵심",""), "진단": info.get("진단",""), "특징": info.get("특징","")}

        meds_lines = summarize_meds(meds) if meds else []
        abx_lines = abx_summary(extras.get("abx", {})) if extras.get("abx") else []
        cmp_lines = compare_with_previous(patient_id, {k: vals.get(k) for k in ORDER if entered(vals.get(k))}) if (mode=="일반/암" and patient_id) else []
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
            st.info("PDF 생성 시 사용 폰트: NanumGothic(환경에 폰트 파일 필요)")
            st.download_button("🖨️ 보고서(.pdf) 다운로드", data=pdf_bytes,
                               file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                               mime="application/pdf")
        except FileNotFoundError as e:
            st.warning(str(e))
        except Exception:
            st.info("PDF 모듈이 없거나 오류가 발생했습니다. (pip install reportlab)")

        if patient_id:
            rec = {
                "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "mode": mode, "group": group, "cancer": cancer, "infect": infect_sel,
                "labs": {k: vals.get(k) for k in ORDER if entered(vals.get(k))},
                "extra": {k: v for k,v in (locals().get('extra_vals') or {}).items() if entered(v)},
                "meds": meds, "extras": extras,
            }
            st.session_state.records.setdefault(patient_id, []).append(rec)
            st.success("저장되었습니다. 아래 그래프에서 추이를 확인하세요.")
        else:
            st.info("별명과 PIN(4자리)을 입력하면 추이 그래프/스케줄 저장이 활성화됩니다.")

    render_graphs()
    st.markdown("---"); st.header("📚 약물 사전 (스크롤 최소화)")
    with st.expander("열기 / 닫기", expanded=False):
        view_tab1, view_tab2 = st.tabs(["항암제 사전", "항생제 사전"])
        with view_tab1:
            rows=[]
            for k, v in ANTICANCER.items():
                rows.append({"약물":k,"한글명":v.get("alias",""),"부작용":", ".join(v.get("aes",[]))})
            if HAS_PD:
                df = __pd.DataFrame(rows); q = st.text_input("🔎 검색", key="drug_search_ac")
                if q: 
                    ql=q.lower()
                    df = df[df.apply(lambda r: any(ql in str(x).lower() for x in r.values), axis=1)]
                st.dataframe(df, use_container_width=True, height=360)
            else:
                for r in rows[:20]:
                    st.markdown(f"**{r['약물']}** · {r['한글명']} — {r['부작용']}")
        with view_tab2:
            rows=[{"계열":k,"주의사항":", ".join(v)} for k,v in ABX_GUIDE.items()]
            if HAS_PD:
                df = __pd.DataFrame(rows); q = st.text_input("🔎 검색", key="drug_search_abx")
                if q:
                    ql=q.lower()
                    df = df[df.apply(lambda r: any(ql in str(x).lower() for x in r.values), axis=1)]
                st.dataframe(df, use_container_width=True, height=360)
            else:
                for r in rows[:20]:
                    st.markdown(f"**{r['계열']}** — {r['주의사항']}")

    st.caption(FOOTER_CAFE); st.markdown("> " + DISCLAIMER)


if __name__ == "__main__":
    main()
