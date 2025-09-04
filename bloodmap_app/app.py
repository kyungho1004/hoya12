# -*- coding: utf-8 -*-
def main():
    from datetime import datetime, date
    import os, sys
    import streamlit as st

    # ==== Robust imports: relative -> absolute -> local, with fallbacks for drug_data/utils_core ====
    try:
        from .config import (APP_TITLE, PAGE_TITLE, MADE_BY, CAFE_LINK_MD, FOOTER_CAFE,
                            DISCLAIMER, ORDER, FEVER_GUIDE,
                            LBL_WBC, LBL_Hb, LBL_PLT, LBL_ANC, LBL_Ca, LBL_P, LBL_Na, LBL_K,
                            LBL_Alb, LBL_Glu, LBL_TP, LBL_AST, LBL_ALT, LBL_LDH, LBL_CRP, LBL_Cr, LBL_UA, LBL_TB, LBL_BUN, LBL_BNP,
                            FONT_PATH_REG)
        try:
            from .data.drugs import ANTICANCER, ABX_GUIDE
        except Exception:
            from .drug_data import ANTICANCER, ABX_GUIDE  # fallback
        try:
            from .data.foods import FOODS
        except Exception:
            from .config import FOODS  # fallback if defined
        try:
            from .data.ped import PED_TOPICS, PED_INPUTS_INFO, PED_INFECT
        except Exception:
            PED_TOPICS, PED_INPUTS_INFO, PED_INFECT = [], "", {}

        # prefer package-based utils (after you rename utils.py -> util_core.py)
        from .utils.inputs import num_input_generic, entered, _parse_numeric
        from .utils.interpret import interpret_labs, compare_with_previous, food_suggestions, summarize_meds, abx_summary
        from .utils.reports import build_report, md_to_pdf_bytes_fontlocked
        from .utils.graphs import render_graphs
        from .utils.schedule import render_schedule
        from .utils.counter import bump as counter_bump, count as counter_count
    except Exception:
        try:
            from bloodmap_app.config import (APP_TITLE, PAGE_TITLE, MADE_BY, CAFE_LINK_MD, FOOTER_CAFE,
                                DISCLAIMER, ORDER, FEVER_GUIDE,
                                LBL_WBC, LBL_Hb, LBL_PLT, LBL_ANC, LBL_Ca, LBL_P, LBL_Na, LBL_K,
                                LBL_Alb, LBL_Glu, LBL_TP, LBL_AST, LBL_ALT, LBL_LDH, LBL_CRP, LBL_Cr, LBL_UA, LBL_TB, LBL_BUN, LBL_BNP,
                                FONT_PATH_REG)
            try:
                from bloodmap_app.data.drugs import ANTICANCER, ABX_GUIDE
            except Exception:
                from bloodmap_app.drug_data import ANTICANCER, ABX_GUIDE
            try:
                from bloodmap_app.data.foods import FOODS
            except Exception:
                from bloodmap_app.config import FOODS
            try:
                from bloodmap_app.data.ped import PED_TOPICS, PED_INPUTS_INFO, PED_INFECT
            except Exception:
                PED_TOPICS, PED_INPUTS_INFO, PED_INFECT = [], "", {}

            from bloodmap_app.utils.inputs import num_input_generic, entered, _parse_numeric
            from bloodmap_app.utils.interpret import interpret_labs, compare_with_previous, food_suggestions, summarize_meds, abx_summary
            from bloodmap_app.utils.reports import build_report, md_to_pdf_bytes_fontlocked
            from bloodmap_app.utils.graphs import render_graphs
            from bloodmap_app.utils.schedule import render_schedule
            from bloodmap_app.utils.counter import bump as counter_bump, count as counter_count
        except Exception:
            sys.path.append(os.path.dirname(__file__))
            from config import (APP_TITLE, PAGE_TITLE, MADE_BY, CAFE_LINK_MD, FOOTER_CAFE,
                                DISCLAIMER, ORDER, FEVER_GUIDE,
                                LBL_WBC, LBL_Hb, LBL_PLT, LBL_ANC, LBL_Ca, LBL_P, LBL_Na, LBL_K,
                                LBL_Alb, LBL_Glu, LBL_TP, LBL_AST, LBL_ALT, LBL_LDH, LBL_CRP, LBL_Cr, LBL_UA, LBL_TB, LBL_BUN, LBL_BNP,
                                FONT_PATH_REG)
            try:
                from data.drugs import ANTICANCER, ABX_GUIDE
            except Exception:
                from drug_data import ANTICANCER, ABX_GUIDE
            try:
                from data.foods import FOODS
            except Exception:
                from config import FOODS
            try:
                from data.ped import PED_TOPICS, PED_INPUTS_INFO, PED_INFECT
            except Exception:
                PED_TOPICS, PED_INPUTS_INFO, PED_INFECT = [], "", {}

            # last-resort: local util_core or utils
            try:
                from utils.inputs import num_input_generic, entered, _parse_numeric
                from utils.interpret import interpret_labs, compare_with_previous, food_suggestions, summarize_meds, abx_summary
                from utils.reports import build_report, md_to_pdf_bytes_fontlocked
                from utils.graphs import render_graphs
                from utils.schedule import render_schedule
                from utils.counter import bump as counter_bump, count as counter_count
            except Exception:
                from util_core import (num_input_generic, entered, _parse_numeric,
                                       interpret_labs, compare_with_previous, food_suggestions, summarize_meds, abx_summary,
                                       build_report, md_to_pdf_bytes_fontlocked, render_graphs, render_schedule)
                def counter_bump(): pass
                def counter_count(): return 0

    # Optional deps
    try:
        import pandas as pd
        HAS_PD = True
    except Exception:
        HAS_PD = False

    st.set_page_config(page_title=PAGE_TITLE, layout="centered")
    st.title(APP_TITLE); st.markdown(MADE_BY); st.markdown(CAFE_LINK_MD)

    # 방문 카운터 (있을 때만)
    try:
        counter_bump()
        st.caption(f"👀 조회수(방문): {counter_count()}")
    except Exception:
        pass

    # ===== Header UI =====
    st.divider()
    st.header("1️⃣ 환자/암·소아 정보")
    c1, c2, c3 = st.columns([2,1,1])
    with c1:
        nickname = st.text_input("별명(저장/그래프/스케줄용)", placeholder="예: 홍길동")
    with c2:
        pin = st.text_input("PIN(4자리)", max_chars=4, placeholder="1234")
        if pin and (not pin.isdigit() or len(pin) != 4):
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

    if mode == "일반/암":
        group = st.selectbox("암 그룹 선택", ["미선택/일반", "혈액암", "고형암", "소아암", "희귀암"])
        if group == "혈액암":
            cancer_label = st.selectbox("혈액암 (진단명 선택)", list(heme_labels.keys()))
            cancer_key = heme_labels.get(cancer_label)
            if cancer_label: st.caption(f"🧬 **혈액암 — 진단명:** {cancer_label}")
        elif group == "고형암":
            cancer_label = st.selectbox("고형암 (진단명 선택)", [
                "폐암(Lung cancer)","유방암(Breast cancer)","위암(Gastric cancer)",
                "대장암(Cololoractal cancer)","간암(HCC)","췌장암(Pancreatic cancer)",
                "담도암(Cholangiocarcinoma)","자궁내막암(Endometrial cancer)",
                "구강암/후두암","피부암(흑색종)","육종(Sarcoma)","신장암(RCC)",
                "갑상선암","난소암","자궁경부암","전립선암","뇌종양(Glioma)","식도암","방광암"
            ])
            cancer_key = cancer_label
        elif group == "소아암":
            cancer_label = st.selectbox("소아암 (진단명 선택)", ["Neuroblastoma","Wilms tumor"])
            cancer_key = cancer_label
        elif group == "희귀암":
            cancer_label = st.selectbox("희귀암 (진단명 선택)", [
                "담낭암(Gallbladder cancer)","부신암(Adrenal cancer)","망막모세포종(Retinoblastoma)",
                "흉선종/흉선암(Thymoma/Thymic carcinoma)","신경내분비종양(NET)",
                "간모세포종(Hepatoblastoma)","비인두암(NPC)","GIST"
            ])
            cancer_key = cancer_label
    elif mode == "소아(일상/호흡기)":
        st.caption(PED_INPUTS_INFO if PED_INPUTS_INFO else "—")
        ped_topic = st.selectbox("소아 주제", PED_TOPICS or [])
    else:
        infect_sel = st.selectbox("질환 선택", list(PED_INFECT.keys()) if PED_INFECT else [])

    table_mode = st.checkbox("⚙️ PC용 표 모드(가로형)", help="모바일은 세로형 고정 → 줄꼬임 없음.")

    # ===== Drugs & extras =====
    meds, extras = {}, {}

    if mode == "일반/암" and group and group != "미선택/일반" and cancer_key:
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
            "혈액암": heme_by_cancer.get(cancer_key, []),
            "고형암": solid_by_cancer.get(cancer_key, []),
            "소아암": ["Cyclophosphamide","Ifosfamide","Doxorubicin","Vincristine","Etoposide","Carboplatin","Cisplatin","Topotecan","Irinotecan"],
            "희귀암": rare_by_cancer.get(cancer_key, []),
        }
        drug_list = list(dict.fromkeys(default_drugs_by_group.get(group, [])))
    else:
        drug_list = []

    drug_search = st.text_input("🔍 항암제 검색", key="drug_search")
    drug_choices = [d for d in drug_list if not drug_search or drug_search.lower() in d.lower()]
    selected_drugs = st.multiselect("항암제 선택", drug_choices, default=[])

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

    # ===== Inputs =====
    st.divider()
    st.header("2️⃣ 기본 혈액 검사 수치")
    vals = {}
    for name in ORDER:
        vals[name] = num_input_generic(name, key=f"v_{name}", decimals=1, placeholder="")

    # 지질패널
    st.markdown("#### 🧴 특수검사 — 지질패널")
    colL1, colL2, colL3, colL4 = st.columns(4)
    with colL1: vals['TG'] = num_input_generic("TG (중성지방, mg/dL)", key="lip_TG", decimals=0)
    with colL2: vals['총콜레스테롤'] = num_input_generic("총콜레스테롤 (mg/dL)", key="lip_TCHOL", decimals=0)
    with colL3: vals['HDL'] = num_input_generic("HDL (선택, mg/dL)", key="lip_HDL", decimals=0)
    with colL4: vals['LDL'] = num_input_generic("LDL (선택, mg/dL)", key="lip_LDL", decimals=0)

    # ===== Run =====
    st.divider()
    run = st.button("🧠 해석하기 / 결과 생성", use_container_width=True)
    if run:
        lipid_guides = []
        def _f(v): 
            try: return float(v)
            except: return None
        tg = _f(vals.get("TG"))
        tc = _f(vals.get("총콜레스테롤"))
        hdl = _f(vals.get("HDL"))
        ldl = _f(vals.get("LDL"))
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

        try:
            for line in interpret_labs(vals, {}): st.write(line)
        except Exception:
            st.info("기본 해석 모듈이 없어 최소 가이드만 표시합니다.")

        if lipid_guides:
            st.markdown("### 🥗 음식/생활 가이드")
            for g in lipid_guides: st.markdown(f"- {g}")

        # 간단 보고서
        try:
            report_md = build_report(mode, {"group":group,"cancer":cancer_key,"cancer_label":cancer_label,
                                            "nickname":nickname,"pin":pin or ""}, vals, [], {}, [], lipid_guides, [])
        except Exception:
            report_md = f"# BloodMap 보고서\n- 그룹/진단: {group}/{cancer_label or cancer_key or '—'}\n"

        st.download_button("📥 보고서(.md) 다운로드", data=report_md.encode("utf-8"),
                           file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                           mime="text/markdown")
