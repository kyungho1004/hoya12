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

    # ---------- UI header ----------
    st.set_page_config(page_title=PAGE_TITLE, layout="centered")
    st.title(APP_TITLE); st.markdown(MADE_BY); st.markdown(CAFE_LINK_MD)
    try:
        _bm_counter.bump(); st.caption(f"👀 조회수(방문): {_bm_counter.count()}")
    except Exception: pass

    if "records" not in st.session_state: st.session_state.records = {}

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

        # ====== Anticancer meds section (ALWAYS visible once a cancer group is chosen) ======
        st.markdown("### 💊 항암제 선택 및 입력")
        # default maps
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

        # Build union lists for graceful fallback (so the UI never "disappears")
        def _union(list_of_lists):
            s = []
            seen = set()
            for L in list_of_lists:
                for x in L:
                    if x not in seen:
                        seen.add(x); s.append(x)
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
            # Fallback: show union for the chosen group (still editable)
            drug_seed = group_defaults.get(group or "", [])

        # Searchable list
        all_drugs = sorted(set(group_defaults.get(group or "", []) + drug_seed))
        drug_search = st.text_input("🔍 항암제 검색(영문/한글 허용)", key="drug_search")
        if drug_search:
            show_drugs = [d for d in all_drugs if drug_search.lower() in d.lower()]
        else:
            show_drugs = all_drugs
        selected_drugs = st.multiselect("항암제 선택", show_drugs, default=drug_seed[:3])

        meds = {}
        for d in selected_drugs:
            amt = num_input_generic(f"{d} - 용량/알약", key=f"med_{d}", decimals=1, placeholder="예: 1.5")
            if amt not in (None, ""):
                meds[d] = {"dose_or_tabs": amt}

        # Safety notes
        if any(x in selected_drugs for x in ["MTX","6-MP"]):
            st.info("ℹ️ **유의사항(일반 정보)** — 개인별 처방은 반드시 담당 의료진 지시를 따르세요.")
        if "MTX" in selected_drugs:
            st.warning("MTX: 보통 **주 1회** 복용 스케줄(일일 복용 아님). NSAIDs/술 과다/탈수는 독성 ↑ 가능.")
        if "6-MP" in selected_drugs:
            st.warning("6-MP: **TPMT/NUDT15** 낮으면 골수억제 ↑ 가능. **Allopurinol/Febuxostat** 병용 시 용량조절 필요.")

    elif mode == "소아(일상/호흡기)":
        # Fallback content so the panel "works" even if ped data is empty
        default_topics = PED_TOPICS or ["일상 관리", "해열·수분", "기침/콧물", "호흡기 관찰 포인트"]
        st.caption(PED_INPUTS_INFO or "아이 컨디션과 생활관리 입력 후 해석 버튼을 눌러주세요.")
        ped_topic = st.selectbox("소아 주제", default_topics)
        colA,colB,colC = st.columns(3)
        with colA:
            temp = num_input_generic("체온(°C)", key="ped_temp", decimals=1)
            cough = st.selectbox("기침 정도", ["없음","약간","보통","심함"], key="ped_cough")
        with colB:
            rr = num_input_generic("호흡수(회/분)", key="ped_rr", as_int=True)
            runny = st.selectbox("콧물 색", ["맑음","노란","초록","피섞임"], key="ped_runny")
        with colC:
            intake = num_input_generic("수분 섭취(컵/일)", key="ped_intake", decimals=1)
            urine = num_input_generic("소변 횟수(회/일)", key="ped_urine", as_int=True)
        st.info("참고: 38℃ 이상 지속되거나 호흡 곤란/탈수 의심 시 즉시 진료 권고.")

    else:  # "소아(감염질환)"
        default_infect = PED_INFECT or {
            "AOM(급성 중이염)": ["귀 아파함","체온","구토/설사"],
            "Pharyngitis(인후염)": ["인후통","체온","기침"],
            "URTI(상기도감염)": ["콧물","기침","체온"],
            "Gastroenteritis(장염)": ["설사 횟수","구토 횟수","섭취량"],
            "UTI(요로감염)": ["배뇨통","빈뇨","체온"],
        }
        infect_sel = st.selectbox("질환 선택", list(default_infect.keys()))
        cols = st.columns(3)
        meta_inputs = {}
        for i, name in enumerate(default_infect[infect_sel]):
            with cols[i % 3]:
                meta_inputs[name] = num_input_generic(name, key=f"ped_inf_{i}", decimals=1)

    # ---------- 2) 기본 혈액 검사 ----------
    st.divider(); st.header("2️⃣ 기본 혈액 검사 수치 (입력한 값만 해석)")
    vals = {}
    for name in ORDER:
        decimals = 2 if name==LBL_CRP else 1
        vals[name] = num_input_generic(name, key=f"v_{name}", decimals=decimals, placeholder="")

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
            with col1: vals['TG'] = num_input_generic("TG (중성지방, mg/dL)", key="lip_TG", as_int=True)
            with col2: vals['총콜레스테롤'] = num_input_generic("총콜레스테롤 (mg/dL)", key="lip_TCHOL", as_int=True)
            with col3: vals['HDL'] = num_input_generic("HDL (선택, mg/dL)", key="lip_HDL", as_int=True)
            with col4: vals['LDL'] = num_input_generic("LDL (선택, mg/dL)", key="lip_LDL", as_int=True)

        if on_comp:
            d1,d2,d3 = st.columns(3)
            with d1: vals['C3'] = num_input_generic("C3 (mg/dL)", key="comp_C3", as_int=True)
            with d2: vals['C4'] = num_input_generic("C4 (mg/dL)", key="comp_C4", as_int=True)
            with d3: vals['CH50'] = num_input_generic("CH50 (U/mL)", key="comp_CH50", as_int=True)

        if on_urine:
            u1,u2,u3 = st.columns(3)
            with u1: vals['요단백'] = st.selectbox("요단백", ["-", "trace", "+", "++", "+++"], index=0, key="ur_prot")
            with u2: vals['잠혈'] = st.selectbox("잠혈(혈뇨)", ["-", "trace", "+", "++", "+++"], index=0, key="ur_blood")
            with u3: vals['요당'] = st.selectbox("요당", ["-", "trace", "+", "++", "+++"], index=0, key="ur_glu")

    # ---------- Run ----------
    st.divider()
    run = st.button("🧠 해석하기 / 결과 생성", use_container_width=True)
    if run:
        st.subheader("📋 해석 결과")

        # 기본 해석
        try:
            for line in interpret_labs(vals, {}): st.write(line)
        except Exception:
            st.info("기본 해석 모듈이 없어 최소 가이드만 표시합니다.")

        # 지질 가이드
        def _f(v):
            try: return float(v)
            except: return None
        lipid_guides = []
        tg = _f(vals.get("TG")); tc=_f(vals.get("총콜레스테롤")); hdl=_f(vals.get("HDL")); ldl=_f(vals.get("LDL"))
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

        # 간단 보고서 + 다운로드
        try:
            report_md = build_report(
                mode=mode,
                meta={"group":group,"cancer":cancer_key,"cancer_label":cancer_label,"nickname":nickname,"pin":pin or ""},
                vals=vals, cmp_lines=[], extra_vals={}, meds_lines=[], food_lines=lipid_guides, abx_lines=[]
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
