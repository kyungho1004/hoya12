# -*- coding: utf-8 -*-
def main():
    from datetime import datetime, date
    import os, sys, importlib
    import streamlit as st

    # ---------- Safe config import ----------
    try:
        from . import config as cfg
    except Exception:
        try:
            cfg = importlib.import_module("bloodmap_app.config")
        except Exception:
            sys.path.append(os.path.dirname(__file__))
            import config as cfg  # type: ignore

    def _g(name, default):
        try: return getattr(cfg, name)
        except Exception: return default

    APP_TITLE   = _g("APP_TITLE", "BloodMap")
    PAGE_TITLE  = _g("PAGE_TITLE", "BloodMap")
    MADE_BY     = _g("MADE_BY", "")
    CAFE_LINK_MD= _g("CAFE_LINK_MD", "")
    FOOTER_CAFE = _g("FOOTER_CAFE", "")
    DISCLAIMER  = _g("DISCLAIMER", "")
    FONT_PATH_REG = _g("FONT_PATH_REG", "fonts/NanumGothic.ttf")

    # Labels
    LBL_WBC=_g("LBL_WBC","WBC"); LBL_Hb=_g("LBL_Hb","Hb"); LBL_PLT=_g("LBL_PLT","PLT"); LBL_ANC=_g("LBL_ANC","ANC")
    LBL_Ca=_g("LBL_Ca","Ca"); LBL_P=_g("LBL_P","P"); LBL_Na=_g("LBL_Na","Na"); LBL_K=_g("LBL_K","K")
    LBL_Alb=_g("LBL_Alb","Albumin (알부민)"); LBL_Glu=_g("LBL_Glu","Glucose"); LBL_TP=_g("LBL_TP","TP")
    LBL_AST=_g("LBL_AST","AST"); LBL_ALT=_g("LBL_ALT","ALT"); LBL_LDH=_g("LBL_LDH","LDH"); LBL_CRP=_g("LBL_CRP","CRP")
    LBL_Cr=_g("LBL_Cr","Cr"); LBL_UA=_g("LBL_UA","UA"); LBL_TB=_g("LBL_TB","TB"); LBL_BUN=_g("LBL_BUN","BUN"); LBL_BNP=_g("LBL_BNP","BNP")

    ORDER = _g("ORDER", [LBL_WBC, LBL_Hb, LBL_PLT, LBL_ANC, LBL_Na, LBL_K, LBL_Ca, LBL_P, LBL_Cr,
                         LBL_BUN, LBL_AST, LBL_ALT, LBL_LDH, LBL_CRP, LBL_Alb, LBL_Glu, LBL_TP, LBL_UA, LBL_TB, LBL_BNP])
    FEVER_GUIDE = _g("FEVER_GUIDE", "- 38℃ 이상 또는 오한/오한전구증상 시 병원 문의")

    # ---------- Lab label annotations (Korean hints) ----------
    ANNO = {
        "WBC": "WBC (백혈구)",
        "Hb": "Hb (혈색소)",
        "PLT": "PLT (혈소판)",
        "ANC": "ANC (절대중성구수)",
        "Na": "Na (나트륨)",
        "K": "K (칼륨)",
        "Ca": "Ca (칼슘)",
        "P": "P (인)",
        "Cr": "Cr (크레아티닌)",
        "BUN": "BUN (혈중요소질소)",
        "AST": "AST (간수치)",
        "ALT": "ALT (간세포 수치)",
        "LDH": "LDH (젖산탈수소효소)",
        "CRP": "CRP (염증수치)",
        "Albumin (알부민)": "Albumin (알부민/단백)",
        "Glucose": "Glucose (혈당)",
        "TP": "TP (총단백)",
        "UA": "UA (요산)",
        "TB": "TB (총빌리루빈)",
        "BNP": "BNP (심부전 표지)",
        # Special tests
        "TG": "TG (중성지방, mg/dL)",
        "총콜레스테롤": "총콜레스테롤 (mg/dL)",
        "HDL": "HDL (고밀도지단백, mg/dL)",
        "LDL": "LDL (저밀도지단백, mg/dL)",
        "C3": "C3 (보체, mg/dL)",
        "C4": "C4 (보체, mg/dL)",
        "CH50": "CH50 (총 보체활성, U/mL)",
        "요단백": "요단백 (정성)",
        "잠혈": "잠혈/혈뇨 (정성)",
        "요당": "요당 (정성)",
    }
    def label_ko(s: str) -> str:
        return ANNO.get(s, s)

    # ---------- Data modules (bridged) ----------
    try:
        from .data.drugs import ANTICANCER, ABX_GUIDE
    except Exception:
        try:
            from bloodmap_app.data.drugs import ANTICANCER, ABX_GUIDE
        except Exception:
            from .drug_data import ANTICANCER, ABX_GUIDE  # last fallback

    # Pediatric data (may be missing)
    try:
        from .data.ped import PED_TOPICS, PED_INPUTS_INFO, PED_INFECT
    except Exception:
        PED_TOPICS, PED_INPUTS_INFO, PED_INFECT = [], "", {}

    # ---------- Utils (bridged) ----------
    try:
        from .utils.inputs import num_input_generic, entered, _parse_numeric
        from .utils.interpret import interpret_labs, compare_with_previous, food_suggestions, summarize_meds, abx_summary
        from .utils.reports import build_report, md_to_pdf_bytes_fontlocked
        from .utils.graphs import render_graphs
        from .utils.schedule import render_schedule
        from .utils import counter as _bm_counter
    except Exception:
        sys.path.append(os.path.dirname(__file__))
        from utils import num_input_generic, entered, _parse_numeric, interpret_labs, compare_with_previous, food_suggestions, summarize_meds, abx_summary, build_report, md_to_pdf_bytes_fontlocked, render_graphs, render_schedule  # type: ignore
        class _DummyCounter:
            @staticmethod
            def bump():
                st.session_state.setdefault("_bm_counter", 0); st.session_state["_bm_counter"] += 1
            @staticmethod
            def count(): return st.session_state.get("_bm_counter", 0)
        _bm_counter = _DummyCounter

    # ---------- Pediatric helpers ----------
    SEV = ["없음", "약간", "보통", "심함"]  # 4단계
    SYM_SEVERITY = {"기침","인후통","귀 아파함","복통","배뇨통","근육통","피로감","탈수 의심","결막 충혈"}
    RUNNY_OPTIONS = ["맑음","노란","초록","피섞임"]
    def sev_idx(s):
        try: return SEV.index(s)
        except: return 0
    def nonempty(x): return x is not None and x != ""

    # ---------- Fallback interpreter (for 암/일반) ----------
    # 간단 범위 기반; 입력한 값만 판단
    REF = {
        "WBC": (4.0, 10.0, "x10^3/μL"),
        "Hb": (12.0, 17.0, "g/dL"),
        "PLT": (150, 400, "x10^3/μL"),
        "ANC": (1500, None, "/μL"),
        "Na": (135, 145, "mmol/L"),
        "K": (3.5, 5.1, "mmol/L"),
        "Ca": (8.6, 10.2, "mg/dL"),
        "P": (2.5, 4.5, "mg/dL"),
        "Cr": (0.6, 1.3, "mg/dL"),
        "BUN": (8, 23, "mg/dL"),
        "AST": (0, 40, "U/L"),
        "ALT": (0, 40, "U/L"),
        "LDH": (0, 250, "U/L"),
        "CRP": (0, 0.5, "mg/dL"),
        "Albumin (알부민)": (3.5, 5.0, "g/dL"),
        "Glucose": (70, 140, "mg/dL"),
        "TP": (6.0, 8.3, "g/dL"),
        "UA": (3.5, 7.2, "mg/dL"),
        "TB": (0.2, 1.2, "mg/dL"),
        "BNP": (0, 100, "pg/mL"),
    }
    def _f(x):
        try: return float(x)
        except: return None

    def interpret_fallback(vals: dict):
        lines = []
        for k, v in vals.items():
            if v in ("", None): continue
            val = _f(v)
            if val is None: continue
            if k == "ANC":
                if val < 500: lines.append("ANC < 500: **중증 호중구감소증** — 발열 시 즉시 진료.")
                elif val < 1000: lines.append("ANC 500~999: **중등도 호중구감소증** — 감염 주의/외출·식품 위생.")
                elif val < 1500: lines.append("ANC 1000~1499: **경증 호중구감소증** — 위생/감염 주의.")
                else: lines.append("ANC 정상 범위.")
                continue
            ref = REF.get(k)
            if not ref: continue
            lo, hi, unit = ref
            disp = f"{label_ko(k)} = {val}"
            if lo is not None and val < lo:
                if k == "Hb": lines.append(f"{disp} ↓ — **빈혈 가능**(피로/어지럼).")
                elif k == "PLT": 
                    if val < 50: lines.append(f"{disp} ↓ — **출혈 위험 高**(멍·코피 주의).")
                    else: lines.append(f"{disp} ↓ — **혈소판 감소**.")
                elif k == "Na": lines.append(f"{disp} ↓ — **저나트륨혈증** 가능.")
                elif k == "K": lines.append(f"{disp} ↓ — **저칼륨혈증** 가능(근력저하/부정맥).")
                elif k == "Ca": lines.append(f"{disp} ↓ — **저칼슘혈증** 가능(쥐남/저림).")
                elif k == "Albumin (알부민)": lines.append(f"{disp} ↓ — **영양상태/간·신장** 점검.")
                else: lines.append(f"{disp} ↓")
            elif hi is not None and val > hi:
                if k in ("AST","ALT"): lines.append(f"{disp} ↑ — **간수치 상승**(약물/간염 등) 추적 필요.")
                elif k == "CRP": lines.append(f"{disp} ↑ — **염증/감염 의심**.")
                elif k == "BUN" or k == "Cr": lines.append(f"{disp} ↑ — **신장 기능 점검**.")
                elif k == "K": lines.append(f"{disp} ↑ — **고칼륨혈증**(부정맥 위험) 주의.")
                elif k == "Na": lines.append(f"{disp} ↑ — **고나트륨혈증** 가능.")
                elif k == "Ca": lines.append(f"{disp} ↑ — **고칼슘혈증**(갈증/피로) 가능.")
                elif k == "LDH": lines.append(f"{disp} ↑ — **조직 손상/용혈** 시 상승.")
                else: lines.append(f"{disp} ↑")
            else:
                lines.append(f"{disp} : 정상 범위.")
        return lines

    # ---------- UI header ----------
    st.set_page_config(page_title=PAGE_TITLE, layout="centered")
    st.title(APP_TITLE); st.markdown(MADE_BY); st.markdown(CAFE_LINK_MD)
    try:
        _bm_counter.bump(); st.caption(f"👀 조회수(방문): {_bm_counter.count()}")
    except Exception: pass

    st.divider()
    st.header("1️⃣ 환자/암·소아 정보")
    c1,c2,c3 = st.columns([2,1,1])
    with c1:
        nickname = st.text_input("별명(저장/그래프/스케줄용)", placeholder="예: 홍길동")
    with c2:
        pin = st.text_input("PIN(4자리)", max_chars=4, placeholder="1234")
        if pin and (not pin.isdigit() or len(pin)!=4):
            st.warning("PIN은 숫자 4자리로 입력해주세요.")
    with c3:
        test_date = st.date_input("검사 날짜", value=date.today())

    anc_place = st.radio("현재 식사 장소(ANC 가이드용)", ["가정", "병원"], horizontal=True)

    nickname_key = (nickname or "").strip()
    if pin and pin.isdigit() and len(pin)==4: nickname_key = f"{nickname_key}#{pin}"
    elif nickname_key: nickname_key = f"{nickname_key}#----"

    mode = st.selectbox("모드 선택", ["일반/암", "소아(일상/호흡기)", "소아(감염질환)"])

    group = cancer_key = cancer_label = infect_sel = ped_topic = None

    # 혈액암: 한글 포함 진단명
    heme_labels = {
        "AML (급성 골수성 백혈병)": "AML",
        "APL (급성 전골수구성 백혈병)": "APL",
        "ALL (급성 림프모구성 백혈병)": "ALL",
        "CML (만성 골수성 백혈병)": "CML",
        "CLL (만성 림프구성 백혈병)": "CLL",
    }
    # 육종 독립 그룹
    sarcoma_dx_list = [
        "연부조직육종 (STS)","골육종 (Osteosarcoma)","유잉육종 (Ewing sarcoma)",
        "평활근육종 (Leiomyosarcoma)","지방육종 (Liposarcoma)","횡문근육종 (Rhabdomyosarcoma)","활막육종 (Synovial sarcoma)"
    ]

    # ====== Group & Diagnosis ======
    if mode == "일반/암":
        group = st.selectbox("암 그룹 선택", ["미선택/일반","혈액암","고형암","육종","소아암","희귀암"])
        if group == "혈액암":
            cancer_label = st.selectbox("혈액암 (진단명 선택)", list(heme_labels.keys()))
            cancer_key = heme_labels.get(cancer_label)
            st.caption(f"🧬 **혈액암 — 진단명:** {cancer_label}")
        elif group == "고형암":
            cancer_label = st.selectbox("고형암 (진단명 선택)", [
                "폐암(Lung cancer)","유방암(Breast cancer)","위암(Gastric cancer)",
                "대장암(Cololoractal cancer)","간암(HCC)","췌장암(Pancreatic cancer)",
                "담도암(Cholangiocarcinoma)","자궁내막암(Endometrial cancer)",
                "구강암/후두암","피부암(흑색종)","신장암(RCC)",
                "갑상선암","난소암","자궁경부암","전립선암","뇌종양(Glioma)","식도암","방광암"
            ]); cancer_key = cancer_label
        elif group == "육종":
            cancer_label = st.selectbox("육종 (진단명 선택)", sarcoma_dx_list); cancer_key = cancer_label
            st.caption(f"🧬 **육종 — 진단명:** {cancer_label}")
        elif group == "소아암":
            cancer_label = st.selectbox("소아암 (진단명 선택)", ["Neuroblastoma","Wilms tumor"]); cancer_key = cancer_label
        elif group == "희귀암":
            cancer_label = st.selectbox("희귀암 (진단명 선택)", [
                "담낭암(Gallbladder cancer)","부신암(Adrenal cancer)","망막모세포종(Retinoblastoma)",
                "흉선종/흉선암(Thymoma/Thymic carcinoma)","신경내분비종양(NET)",
                "간모세포종(Hepatoblastoma)","비인두암(NPC)","GIST"
            ]); cancer_key = cancer_label

        # ====== Anticancer meds section (always visible) ======
        st.markdown("### 💊 항암제 선택 및 입력")
        heme_by_cancer = {
            "AML": ["ARA-C","Daunorubicin","Idarubicin","Cyclophosphamide",
                    "Etoposide","Fludarabine","Hydroxyurea","MTX","ATRA","G-CSF"],
            "APL": ["ATRA","Idarubicin","Daunorubicin","ARA-C","G-CSF","MTX","6-MP"],
            "ALL": ["Vincristine","Asparaginase","Daunorubicin","Cyclophosphamide","MTX","ARA-C","Topotecan","Etoposide","6-MP"],
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
            "연부조직육종 (STS)": ["Doxorubicin","Ifosfamide","Pazopanib","Gemcitabine","Docetaxel"],
            "골육종 (Osteosarcoma)": ["Cisplatin","Doxorubicin","MTX","Ifosfamide","Etoposide"],
            "유잉육종 (Ewing sarcoma)": ["Vincristine","Doxorubicin","Cyclophosphamide","Ifosfamide","Etoposide"],
            "평활근육종 (Leiomyosarcoma)": ["Doxorubicin","Gemcitabine","Docetaxel","Pazopanib"],
            "지방육종 (Liposarcoma)": ["Doxorubicin","Ifosfamide","Pazopanib"],
            "횡문근육종 (Rhabdomyosarcoma)": ["Vincristine","Cyclophosphamide","Doxorubicin","Ifosfamide","Etoposide"],
            "활막육종 (Synovial sarcoma)": ["Ifosfamide","Doxorubicin","Pazopanib"],
        }
        def _union(list_of_lists):
            s = []; seen=set()
            for L in list_of_lists:
                for x in L:
                    if x not in seen: seen.add(x); s.append(x)
            return s
        group_defaults = {
            "혈액암": _union(list(heme_by_cancer.values())),
            "고형암": _union(list(solid_by_cancer.values())),
            "육종"  : _union(list(sarcoma_by_dx.values())),
            "소아암": ["Cyclophosphamide","Ifosfamide","Doxorubicin","Vincristine","Etoposide","Carboplatin","Cisplatin","Topotecan","Irinotecan"],
            "희귀암": ["Imatinib","Sunitinib","Regorafenib","Gemcitabine","Cisplatin","Mitotane","Etoposide","Doxorubicin"],
        }
        if group == "혈액암" and cancer_key in heme_by_cancer:
            drug_seed = heme_by_cancer[cancer_key]
        elif group == "고형암" and cancer_key in solid_by_cancer:
            drug_seed = solid_by_cancer[cancer_key]
        elif group == "육종" and cancer_key in sarcoma_by_dx:
            drug_seed = sarcoma_by_dx[cancer_key]
        else:
            drug_seed = group_defaults.get(group or "", [])
        all_drugs = sorted(set(group_defaults.get(group or "", []) + drug_seed))
        drug_search = st.text_input("🔍 항암제 검색(영문/한글 허용)", key="drug_search")
        show_drugs = [d for d in all_drugs if (not drug_search) or (drug_search.lower() in d.lower())]
        selected_drugs = st.multiselect("항암제 선택", show_drugs, default=drug_seed[:3])

        meds = {}
        for d in selected_drugs:
            amt = num_input_generic(f"{d} - 용량/알약", key=f"med_{d}", decimals=1, placeholder="예: 1.5")
            if amt not in (None, ""): meds[d] = {"dose_or_tabs": amt}

        if any(x in selected_drugs for x in ["MTX","6-MP"]):
            st.info("ℹ️ **유의사항(일반 정보)** — 개인별 처방은 반드시 담당 의료진 지시를 따르세요.")
        if "MTX" in selected_drugs:
            st.warning("MTX: 보통 **주 1회** 복용 스케줄(일일 복용 아님). NSAIDs/술 과다/탈수는 독성 ↑ 가능.")
        if "6-MP" in selected_drugs:
            st.warning("6-MP: **TPMT/NUDT15** 낮으면 골수억제 ↑ 가능. **Allopurinol/Febuxostat** 병용 시 용량조절 필요.")

    elif mode == "소아(일상/호흡기)":
        st.caption(PED_INPUTS_INFO or "아이 컨디션과 생활관리 입력 후 해석 버튼을 눌러주세요.")
        ped_topic = st.selectbox("소아 주제", (PED_TOPICS or ["일상 관리","해열·수분","기침/콧물","호흡기 관찰 포인트"]))
        colA,colB,colC = st.columns(3)
        with colA:
            temp = num_input_generic("체온(°C)", key="ped_temp", decimals=1)
            cough = st.selectbox("기침 정도", SEV, key="ped_cough")
        with colB:
            rr = num_input_generic("호흡수(회/분)", key="ped_rr", as_int=True)
            throat = st.selectbox("인후통", SEV, key="ped_throat")
        with colC:
            intake = num_input_generic("수분 섭취(컵/일)", key="ped_intake", decimals=1)
            ear_pain = st.selectbox("귀 아파함", SEV, key="ped_ear")
        st.session_state["_ped_daily"] = {"temp":temp,"cough":cough,"rr":rr,"throat":throat,"intake":intake,"ear_pain":ear_pain}

    else:  # "소아(감염질환)"
        default_infect = PED_INFECT or {
            "AOM(급성 중이염)": ["귀 아파함", "체온", "구토/설사"],
            "Pharyngitis(인후염)": ["인후통", "체온", "기침"],
            "URTI(상기도감염)": ["콧물", "기침", "체온"],
            "Gastroenteritis(장염)": ["설사 횟수", "구토 횟수", "섭취량(컵/일)", "복통"],
            "UTI(요로감염)": ["배뇨통", "빈뇨(회/일)", "체온"],
            "Rotavirus(로타)": ["설사 횟수", "구토 횟수", "탈수 의심", "체온"],
            "Adenovirus(아데노)": ["인후통", "결막 충혈", "체온"],
            "COVID-19(코로나19)": ["체온", "기침", "인후통", "근육통"],
            "Influenza(독감)": ["체온", "근육통", "기침", "피로감"],
        }
        infect_sel = st.selectbox("질환 선택", list(default_infect.keys()))

        # Build dynamic inputs with smart type inference
        meta_inputs = {}
        cols = st.columns(3)
        for i, raw in enumerate(default_infect[infect_sel]):
            with cols[i % 3]:
                base = raw.split("(")[0].strip()
                if base == "콧물":
                    meta_inputs["콧물"] = st.selectbox("콧물", RUNNY_OPTIONS, key=f"ped_runny_{i}")
                elif base in SYM_SEVERITY:
                    meta_inputs[base] = st.selectbox(base, SEV, key=f"ped_sev_{i}")
                else:
                    decimals = 0 if any(k in base for k in ["횟수","회/일"]) else 1
                    meta_inputs[base] = num_input_generic(base, key=f"ped_num_{i}", decimals=decimals, as_int=(decimals==0))
        st.session_state["_ped_infect"] = {"name": infect_sel, "inputs": meta_inputs}

    # ---------- 2) 기본 혈액 검사 ----------
    st.divider()
    # Pediatric infectious mode: hide labs behind a toggle (default off)
    hide_default = (mode == "소아(감염질환)")
    if hide_default:
        open_labs = st.checkbox("🧪 피수치 입력 열기", value=False)
    else:
        open_labs = True

    vals = {}
    if open_labs:
        st.header("2️⃣ 기본 혈액 검사 수치 (입력한 값만 해석)")
        for name in ORDER:
            decimals = 2 if name==LBL_CRP else 1
            display = label_ko(name)
            vals[name] = num_input_generic(display, key=f"v_{name}", decimals=decimals, placeholder="")

    # ---------- 특수검사 (토글) ----------
    st.markdown("### 🧪 특수검사")
    open_special = st.checkbox("특수검사 입력 열기", value=True)
    if open_special:
        cA, cB, cC = st.columns(3)
        with cA:
            on_lipid = st.checkbox("지질패널 (TG/총콜/HDL/LDL)", value=True)
        with cB:
            on_comp = st.checkbox("보체/면역 (C3·C4·CH50)", value=False)
        with cC:
            on_urine = st.checkbox("요검사 (요단백/잠혈/요당)", value=False)

        if on_lipid:
            col1, col2, col3, col4 = st.columns(4)
            with col1: vals['TG'] = num_input_generic(label_ko("TG"), key="lip_TG", as_int=True)
            with col2: vals['총콜레스테롤'] = num_input_generic(label_ko("총콜레스테롤"), key="lip_TCHOL", as_int=True)
            with col3: vals['HDL'] = num_input_generic(label_ko("HDL"), key="lip_HDL", as_int=True)
            with col4: vals['LDL'] = num_input_generic(label_ko("LDL"), key="lip_LDL", as_int=True)

        if on_comp:
            d1,d2,d3 = st.columns(3)
            with d1: vals['C3'] = num_input_generic(label_ko("C3"), key="comp_C3", as_int=True)
            with d2: vals['C4'] = num_input_generic(label_ko("C4"), key="comp_C4", as_int=True)
            with d3: vals['CH50'] = num_input_generic(label_ko("CH50"), key="comp_CH50", as_int=True)

        if on_urine:
            u1,u2,u3 = st.columns(3)
            with u1: vals['요단백'] = st.selectbox(label_ko("요단백"), ["-", "trace", "+", "++", "+++"], index=0, key="ur_prot")
            with u2: vals['잠혈'] = st.selectbox(label_ko("잠혈"), ["-", "trace", "+", "++", "+++"], index=0, key="ur_blood")
            with u3: vals['요당'] = st.selectbox(label_ko("요당"), ["-", "trace", "+", "++", "+++"], index=0, key="ur_glu")

    # ---------- Run ----------
    st.divider()
    run = st.button("🧠 해석하기 / 결과 생성", use_container_width=True)
    if run:
        st.subheader("📋 해석 결과")

        # 기본 해석 (utils 우선, 없거나 비어있으면 fallback)
        lines = []
        try:
            res = interpret_labs(vals, {})
            if isinstance(res, (list, tuple)):
                lines = [str(x) for x in res if str(x).strip()]
        except Exception:
            lines = []
        if not lines:
            lines = interpret_fallback(vals)

        for line in lines:
            st.write("- " + line)

        # ===== Pediatric interpretations =====
        ped_lines = []
        if mode == "소아(일상/호흡기)":
            pd = st.session_state.get("_ped_daily", {})
            temp=pd.get("temp"); cough=pd.get("cough"); rr=pd.get("rr")
            throat=pd.get("throat"); intake=pd.get("intake"); ear_pain=pd.get("ear_pain")
            if nonempty(temp) and float(temp) >= 38.0:
                ped_lines.append("체온 ≥ 38℃: 해열·수분 보충, **지속/악화 시 진료 권고**")
            if sev_idx(cough) >= 2 or sev_idx(throat) >= 2:
                ped_lines.append("기침/인후통 '보통 이상': 수분·가습, **호흡곤란/열 지속 시 진료**")
            if nonempty(rr) and float(rr) >= 40:
                ped_lines.append("호흡수 ↑(≥40): **호흡곤란 관찰 및 진료 고려**")
            if nonempty(intake) and float(intake) < 3:
                ped_lines.append("수분 섭취 적음(<3컵/일): **소량씩 자주 수분 보충**")
            if sev_idx(ear_pain) >= 2:
                ped_lines.append("귀 통증: 진통제(의사 지시에 따름)·온찜질, **고열/분비물/48시간 지속 시 진료**")

        elif mode == "소아(감염질환)":
            pack = st.session_state.get("_ped_infect", {})
            name = pack.get("name"); data = pack.get("inputs", {})
            def _sev(k): return sev_idx(data.get(k, "없음"))
            def _num(k):
                v = data.get(k); 
                try: return float(v) if v not in ("", None) else None
                except: return None
            t = _num("체온")
            if t is not None and t >= 38.0:
                ped_lines.append("체온 ≥ 38℃: 해열·수분 보충, **지속/악화 시 진료 권고**")
            if name and data:
                if name.startswith("AOM"):
                    if _sev("귀 아파함") >= 2:
                        ped_lines.append("중이염 의심: 귀 통증 '보통 이상' → 진통제/온찜질, **48시간 지속/고열 시 진료**")
                elif name.startswith("Pharyngitis"):
                    if _sev("인후통") >= 2:
                        ped_lines.append("인후염 의심: 수분·가습, 연하곤란/호흡곤란 시 **진료**")
                elif name.startswith("URTI"):
                    if _sev("기침") >= 2 or data.get("콧물") in ["노란","초록","피섞임"]:
                        ped_lines.append("감기 증상: 휴식·수분·가습, 호흡곤란/열 3일↑ 시 **진료 고려**")
                elif name.startswith("Gastroenteritis"):
                    d=_num("설사 횟수"); v=_num("구토 횟수"); ab=_sev("복통")
                    if (d and d>=5) or (v and v>=3) or ab>=2:
                        ped_lines.append("장염 의심: 탈수 위험 → **소량씩 ORS/수분 보충, 핏변·무반응 시 진료**")
                elif name.startswith("UTI"):
                    if _sev("배뇨통") >= 2 or (_num("빈뇨") and _num("빈뇨") >= 8):
                        ped_lines.append("요로감염 의심: **소변 통증/빈뇨** → 진료 및 소변검사 고려")
                elif name.startswith("Rotavirus"):
                    d=_num("설사 횟수"); v=_num("구토 횟수")
                    if (d and d>=5) or (v and v>=3) or _sev("탈수 의심")>=2:
                        ped_lines.append("로타 의심: **탈수 주의** → ORS/수분 보충, 소변 감소·무기력 시 진료")
                elif name.startswith("Adenovirus"):
                    if _sev("인후통")>=2 or _sev("결막 충혈")>=2:
                        ped_lines.append("아데노바이러스 의심: 결막염/인후염 동반 가능 → 위생·증상 완화, 악화 시 진료")
                elif name.startswith("COVID-19"):
                    if _sev("기침")>=2 or _sev("인후통")>=2 or _sev("근육통")>=2:
                        ped_lines.append("코로나19 의심: **휴식·마스크·수분**, 호흡곤란/탈수·고위험군은 진료")
                elif name.startswith("Influenza"):
                    if _sev("근육통")>=2 or _sev("기침")>=2 or (t and t>=38.0):
                        ped_lines.append("독감 의심: **초기 48시간 내 고위험군 항바이러스제 고려(의사 지시)**, 휴식·수분")

        if ped_lines:
            st.markdown("### 🧒 소아 가이드")
            for ln in ped_lines: st.write("- " + ln)

        # ===== Lipid guide =====
        def _fv(v):
            try: return float(v)
            except: return None
        lipid_guides = []
        tg = _fv(vals.get("TG")); tc=_fv(vals.get("총콜레스테롤")); hdl=_fv(vals.get("HDL")); ldl=_fv(vals.get("LDL"))
        if tg is not None and tg >= 200:
            lipid_guides.append("중성지방(TG) 높음: 단 음료/과자 제한 · 튀김/버터/마요네즈 등 기름진 음식 줄이기 · 라면/가공식품(짠맛) 줄이기 · 채소/등푸른생선/현미·잡곡/소량 견과류 권장")
        if tc is not None and tc >= 240:
            lipid_guides.append("총콜레스테롤 높음(≥240): 포화·트랜스지방 줄이기(가공육·튀김·제과) · 가공치즈/크림 줄이기 · 식이섬유(귀리·콩류·과일) 늘리기 · 식물성 스테롤 도움")
        if tc is not None and 200 <= tc <= 239:
            lipid_guides.append("총콜레스테롤 경계역(200~239): 위 생활수칙을 참고하여 식습관 개선 권고")
        if hdl is not None and hdl < 40:
            lipid_guides.append("HDL 낮음(<40): 규칙적 유산소·체중조절·채소/통곡물·견과류·생선 섭취 권장")
        if ldl is not None and ldl >= 160:
            lipid_guides.append("LDL 높음(≥160): 포화지방 제한·식이섬유/식물성 스테롤·등푸른생선 권장")

        if lipid_guides:
            st.markdown("### 🥗 음식/생활 가이드")
            for g in lipid_guides: st.markdown(f"- {g}")

        # Report & downloads
        try:
            report_md = build_report(
                mode=mode,
                meta={"group":group,"cancer":cancer_key,"cancer_label":cancer_label,"nickname":nickname,"pin":pin or ""},
                vals=vals, cmp_lines=[], extra_vals={}, meds_lines=[], food_lines=lipid_guides, abx_lines=ped_lines
            )
        except Exception:
            report_md = f"# BloodMap 보고서\n- 모드/그룹/진단: {mode}/{group}/{cancer_label or cancer_key or '—'}\n"

        st.download_button("📥 보고서(.md) 다운로드", data=report_md.encode("utf-8"),
                           file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                           mime="text/markdown")
        st.download_button("📄 보고서(.txt) 다운로드", data=report_md.encode("utf-8"),
                           file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                           mime="text/plain")
        try:
            pdf_bytes = md_to_pdf_bytes_fontlocked(report_md)
            st.download_button("🖨️ 보고서(.pdf) 다운로드", data=pdf_bytes,
                               file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                               mime="application/pdf")
        except Exception as e:
            st.info(f"PDF 생성 모듈 사용 불가: {e}")

    st.caption(FOOTER_CAFE); st.markdown("> " + DISCLAIMER)
