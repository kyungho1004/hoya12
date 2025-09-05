# -*- coding: utf-8 -*-
from __future__ import annotations

def main():
    from datetime import datetime, date
    import os, re
    import streamlit as st

    # ----- local modules -----
    from .config import (APP_TITLE, PAGE_TITLE, MADE_BY, CAFE_LINK_MD, FOOTER_CAFE,
                         DISCLAIMER, ORDER, FEVER_GUIDE,
                         LBL_WBC, LBL_Hb, LBL_PLT, LBL_ANC, LBL_Ca, LBL_P, LBL_Na, LBL_K,
                         LBL_Alb, LBL_Glu, LBL_TP, LBL_AST, LBL_ALT, LBL_LDH, LBL_CRP, LBL_Cr, LBL_UA, LBL_TB, LBL_BUN, LBL_BNP,
                         FONT_PATH_REG)
    from .data.drugs import ANTICANCER, ABX_GUIDE
    from .data.foods import FOODS
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

    st.set_page_config(page_title=PAGE_TITLE, layout="centered")
    st.title(APP_TITLE); st.markdown(MADE_BY); st.markdown(CAFE_LINK_MD)

    st.markdown("### 🔗 공유하기")
    c1, c2, c3 = st.columns([1,1,2])
    with c1: st.link_button("📱 카카오톡/메신저", "https://hdzwo5ginueir7hknzzfg4.streamlit.app/")
    with c2: st.link_button("📝 카페/블로그", "https://cafe.naver.com/bloodmap")
    with c3: st.code("https://hdzwo5ginueir7hknzzfg4.streamlit.app/", language="text")

    st.caption("✅ 별명+PIN(4자리) 저장키 · 육종(진단명) 분리 · 항암제 직접 선택(한글 병기) · 특수검사 토글 · 소아 일상/감염 가이드(질환별 입력)")

    os.makedirs("fonts", exist_ok=True)

    if "records" not in st.session_state: st.session_state.records = {}
    if "schedules" not in st.session_state: st.session_state.schedules = {}

    # ===== Patient / Mode =====
    st.divider(); st.header("1️⃣ 환자 / 모드 선택")
    c1, c2, c3 = st.columns([2,1,1])
    with c1: nickname = st.text_input("별명(저장/그래프/스케줄용)", placeholder="예: 홍길동")
    with c2: pin = st.text_input("PIN 4자리(중복 방지)", max_chars=4, placeholder="예: 1234")
    with c3: test_date = st.date_input("검사 날짜", value=date.today())

    pin_valid = bool(pin) and pin.isdigit() and len(pin) == 4
    if pin and not pin_valid: st.warning("PIN은 숫자 4자리만 가능합니다. (예: 0930)")
    storage_key = f"{(nickname or '').strip()}#{pin}" if (nickname and pin_valid) else (nickname or '').strip()

    anc_place = st.radio("현재 식사 장소(ANC 가이드용)", ["가정", "병원"], horizontal=True)
    mode = st.selectbox("모드 선택", ["일반/암", "소아(일상가이드)", "소아(감염질환)"])

    # ===== 암 그룹 / 진단 =====
    group = cancer = None
    if mode == "일반/암":
        group = st.selectbox("암 그룹 선택", ["미선택/일반", "혈액암", "고형암", "육종", "소아암", "희귀암"])
        if group == "혈액암":
            cancer = st.selectbox("혈액암(진단명) 선택", ["AML","APL","ALL","CML","CLL"])
        elif group == "고형암":
            cancer = st.selectbox("고형암(진단명) 선택", [
                "폐암(Lung cancer)","유방암(Breast cancer)","위암(Gastric cancer)",
                "대장암(Cololoractal cancer)","간암(HCC)","췌장암(Pancreatic cancer)",
                "담도암(Cholangiocarcinoma)","자궁내막암(Endometrial cancer)",
                "구강암/후두암","피부암(흑색종)","신장암(RCC)","갑상선암","난소암",
                "자궁경부암","전립선암","뇌종양(Glioma)","식도암","방광암"
            ])
        elif group == "육종":
            cancer = st.selectbox("육종(진단명) 선택", [
                "연부조직육종(Soft tissue sarcoma)","골육종(Osteosarcoma)","유잉육종(Ewing sarcoma)",
                "평활근육종(Leiomyosarcoma)","지방육종(Liposarcoma)","활막육종(Synovial sarcoma)",
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
            st.info("암별 참고 항암제 목록만 보여주고, 선택은 전부 직접 하도록 되어 있어요.")

    # ===== 항암제/항생제 (암은 수동 선택만) =====
    meds, extras = {}, {"abx": {}}
    if mode == "일반/암":
        st.divider(); st.header("2️⃣ 약물 입력")
        # 한글 병기용 별칭 보강
        AC_ALL = dict(ANTICANCER)
        AC_ALL.setdefault("MTX", {"alias":"메토트렉세이트"})
        AC_ALL.setdefault("6-MP", {"alias":"6-머캅토퓨린"})

        # 참고 목록(자동 선택 아님)
        heme_by_cancer = {
            "AML": ["ARA-C","Daunorubicin","Idarubicin","Cyclophosphamide","Etoposide","Fludarabine","Hydroxyurea","MTX","ATRA","G-CSF"],
            "APL": ["ATRA","Idarubicin","Daunorubicin","ARA-C","G-CSF","MTX","6-MP"],
            "ALL": ["Vincristine","Asparaginase","Daunorubicin","Cyclophosphamide","MTX","6-MP","ARA-C","Topotecan","Etoposide"],
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
            "연부조직육종(Soft tissue sarcoma)": ["Doxorubicin","Ifosfamide","Pazopanib","Gemcitabine","Docetaxel"],
            "골육종(Osteosarcoma)": ["Doxorubicin","Ifosfamide","Cisplatin","High-dose MTX"],
            "유잉육종(Ewing sarcoma)": ["Cyclophosphamide","Ifosfamide","Doxorubicin","Etoposide","Vincristine"],
            "평활근육종(Leiomyosarcoma)": ["Doxorubicin","Ifosfamide","Pazopanib","Gemcitabine","Docetaxel"],
            "지방육종(Liposarcoma)": ["Doxorubicin","Ifosfamide","Gemcitabine","Docetaxel"],
            "활막육종(Synovial sarcoma)": ["Ifosfamide","Doxorubicin","Pazopanib"],
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

        if group and group != "미선택/일반" and cancer:
            ref = (heme_by_cancer if group=="혈액암" else
                   solid_by_cancer if group=="고형암" else
                   sarcoma_by_dx if group=="육종" else
                   rare_by_cancer if group=="희귀암" else {})
            ref_list = ref.get(cancer, [])
            if ref_list:
                st.info("🔎 참고(자동 선택 아님): " + ", ".join([f"{d} ({AC_ALL.get(d,{}).get('alias','')})".strip() for d in ref_list]))

        st.markdown("### 💊 항암제 직접 선택 (이름 옆에 한글)")
        q = st.text_input("🔍 항암제 검색", key="drug_search_all", placeholder="예: MTX, 6-MP, Imatinib ...")
        all_choices = sorted(AC_ALL.keys())
        if q:
            ql = q.lower().strip()
            all_choices = [d for d in all_choices if ql in d.lower() or ql in AC_ALL[d].get("alias","").lower()]
        selected_drugs = st.multiselect("항암제 선택", all_choices, default=[])

        meds = {}
        for d in selected_drugs:
            alias = AC_ALL.get(d,{}).get("alias","")
            label = f"{d} ({alias})" if alias else d
            val = num_input_generic(f"{label} - 용량/횟수", key=f"med_{d}", decimals=2, placeholder="예: 1 또는 1.5")
            if entered(val): meds[d] = {"dose_or_tabs": val}

        st.markdown("### 🧪 항생제 선택 (계열·한글 병기)")
        abx_q = st.text_input("🔍 항생제 검색", key="abx_search", placeholder="예: Macrolide, 퀴놀론 ...")
        abx_choices = [a for a in ABX_GUIDE.keys()
                       if not abx_q or abx_q.lower() in a.lower()
                       or any(abx_q.lower() in tip.lower() for tip in ABX_GUIDE[a])]
        sel_abx = st.multiselect("항생제 계열 선택", abx_choices, default=[])
        for abx in sel_abx:
            extras["abx"][abx] = num_input_generic(f"{abx} - 복용/주입량", key=f"abx_{abx}", decimals=1, placeholder="예: 1")

    # ===== 기본 혈액검사 (암 모드) / 소아 모드에서는 토글 =====
    vals = {}; special_vals = {}; show_labs = False
    if mode == "일반/암":
        st.divider(); st.header("3️⃣ 기본 혈액 검사 (입력한 값만 해석)")
        show_labs = True
    else:
        st.divider(); st.header("2️⃣ 피수치(혈액검사) 입력")
        show_labs = st.checkbox("피수치 입력 보이기", value=False, help="소아가이드/감염질환에서 피수치는 토글로 표시")

    def render_lab_inputs():
        table_mode = st.checkbox("⚙️ PC용 표 모드(가로형)", value=False, key="tbl_mode", help="모바일은 세로형 고정 → 줄꼬임 없음.")
        st.markdown("**기본 패널**")
        for name in ORDER:
            dec = 2 if name==LBL_CRP else 1
            key = f"t_{name}" if table_mode else f"v_{name}"
            vals[name] = num_input_generic(f"{name}", key=key, decimals=dec)

    if show_labs:
        render_lab_inputs()
        # 특수검사 토글
        st.divider(); st.header("3-1️⃣ 특수검사(토글)")
        colA, colB, colC, colD = st.columns(4)
        with colA: on_coag = st.checkbox("응고패널", help="PT/aPTT/Fib/D-dimer")
        with colB: on_comp = st.checkbox("보체", help="C3/C4/CH50")
        with colC: on_lipid = st.checkbox("지질", help="TG/TC")
        with colD: on_urine = st.checkbox("소변", help="ACR/UPCR")
        if on_coag:
            st.markdown("**응고패널**"); special_vals["PT"] = num_input_generic("PT (sec)", key="sp_pt", decimals=1)
            special_vals["aPTT"] = num_input_generic("aPTT (sec)", key="sp_aptt", decimals=1)
            special_vals["Fibrinogen"] = num_input_generic("Fibrinogen (mg/dL)", key="sp_fib", decimals=1)
            special_vals["D-dimer"] = num_input_generic("D-dimer (µg/mL FEU)", key="sp_dd", decimals=2)
        if on_comp:
            st.markdown("**보체**"); special_vals["C3"] = num_input_generic("C3 (mg/dL)", key="sp_c3", decimals=1)
            special_vals["C4"] = num_input_generic("C4 (mg/dL)", key="sp_c4", decimals=1)
            special_vals["CH50"] = num_input_generic("CH50 (U/mL)", key="sp_ch50", decimals=1)
        if on_lipid:
            st.markdown("**지질**"); special_vals["Triglyceride(TG)"] = num_input_generic("중성지방 TG (mg/dL)", key="sp_tg", decimals=0)
            special_vals["Total Cholesterol"] = num_input_generic("총콜레스테롤 (mg/dL)", key="sp_tc", decimals=0)
        if on_urine:
            st.markdown("**소변**"); special_vals["ACR"] = num_input_generic("ACR (mg/g)", key="sp_acr", decimals=1)
            special_vals["UPCR"] = num_input_generic("UPCR (mg/g)", key="sp_upcr", decimals=1)

    # ===== 소아: 일상가이드 =====
    ped_inputs = {}; infection = None; infect_specific = {}
    if mode == "소아(일상가이드)":
        st.divider(); st.header("3️⃣ 소아 — 일상가이드 입력")
        appetite = st.radio("식욕", ["없음","있음"], horizontal=True)
        fever_chk = st.checkbox("발열: 직접 체크")
        c1, c2 = st.columns(2)
        with c1:
            cough = st.radio("기침", ["안함","조금","보통","많이","심함"], horizontal=True)
            dysp = st.radio("호흡곤란", ["없음","조금","보통","많이","심함"], horizontal=True)
        with c2:
            temp_c = num_input_generic("체온(℃)", key="ped_temp", decimals=1)
            cyan = st.checkbox("청색증(체크)")
        ox = st.checkbox("산소포화도 측정기 있음")
        spo2_value = num_input_generic("SpO₂(%) (직접입력)", key="ped_spo2", decimals=0) if ox else None
        ped_inputs = {"식욕": appetite, "발열": bool(fever_chk), "체온": temp_c, "기침": cough, "호흡곤란": dysp, "청색증": bool(cyan), "SpO2": spo2_value, "측정기": bool(ox)}

    # ===== 소아: 감염질환 (질환별로 입력 다르게) =====
    if mode == "소아(감염질환)":
        st.divider(); st.header("3️⃣ 소아 — 감염질환")
        infection = st.selectbox("질환 선택", ["RSV", "아데노", "로타", "인플루엔자", "파라인플루엔자", "수족구", "노로", "마이코플"])

        ox = st.checkbox("산소포화도 측정기 있음")
        spo2_value = num_input_generic("SpO₂(%) (직접입력)", key="inf_spo2", decimals=0) if ox else None

        st.subheader("증상 입력 (질환별 전용)")
        if infection == "RSV":
            r_cough = st.radio("기침", ["안함","조금","보통","많이","심함"], horizontal=True); infect_specific = {"기침": r_cough}
        elif infection == "아데노":
            eye = st.checkbox("눈꼽/결막염 있음"); infect_specific = {"눈꼽": bool(eye)}
        elif infection == "로타":
            dia = num_input_generic("설사(회/일)", key="rota_dia", decimals=0); infect_specific = {"설사(회/일)": dia}
        elif infection == "인플루엔자":
            i_cough = st.radio("기침", ["안함","조금","보통","많이","심함"], horizontal=True); infect_specific = {"기침": i_cough}
        elif infection == "파라인플루엔자":
            p_fever = st.checkbox("발열 있음"); p_cough = st.radio("기침", ["안함","조금","보통","많이","심함"], horizontal=True)
            infect_specific = {"발열": bool(p_fever), "기침": p_cough}
        elif infection == "수족구":
            hf_fever = st.checkbox("발열 있음"); infect_specific = {"발열": bool(hf_fever)}
        elif infection == "노로":
            n_dia = num_input_generic("설사(회/일)", key="noro_dia", decimals=0); infect_specific = {"설사(회/일)": n_dia}
        elif infection == "마이코플":
            m_cough = st.radio("기침", ["안함","조금","보통","많이","심함"], horizontal=True); infect_specific = {"기침": m_cough}

        ped_inputs = {"SpO2": spo2_value, "측정기": bool(ox)}
        ped_inputs.update(infect_specific)

    # ===== 스케줄 =====
    render_schedule(storage_key or nickname)

    # ===== Run =====
    st.divider()
    run = st.button("🔎 해석하기", use_container_width=True)

    # ----- helpers (safe) -----
    def _sev(v:str):
        return {"안함":0,"없음":0,"조금":1,"보통":2,"많이":3,"심함":4}.get(str(v),0)

    def _triage(pdata:dict):
        msgs=[]; danger=False; urgent=False
        s = pdata.get("SpO2", None)
        try:
            if s is not None:
                s = float(s)
                if s < 92: danger=True; msgs.append("SpO₂<92%")
                elif s < 95: urgent=True; msgs.append("SpO₂ 92–94%")
        except: pass
        if pdata.get("청색증", False): danger=True; msgs.append("청색증")
        hs = _sev(pdata.get("호흡곤란", "없음"))
        if hs >= 4: danger=True; msgs.append("호흡곤란 심함")
        elif hs >= 3: urgent=True; msgs.append("호흡곤란 많음")
        try:
            t = pdata.get("체온", None)
            if pdata.get("발열", False) and t is not None and float(t) >= 39.0:
                urgent=True; msgs.append("고열")
        except: pass
        lead = "🚑 위급" if danger else ("⚠️ 주의" if urgent else "🙂 가정 경과관찰")
        if not msgs: msgs.append("특이 위험 신호 없음")
        return f"**{lead}**: " + ", ".join(msgs)

    def _tip(dname:str, fields:dict)->str:
        try:
            if dname=="RSV":
                return "영아에서 천명·무호흡 위험. 기침 심하면 즉시 진료."
            if dname=="아데노":
                return "눈곱/결막염 동반 시 세정·손위생 중요, 고열 지속 시 진료."
            if dname=="로타":
                val = fields.get("설사(회/일)"); 
                try: dia = float(val or 0)
                except: dia = 0
                return "탈수 위험 → 소량·자주 수분 보충." + (" (설사 빈도 높음)" if dia>=6 else "")
            if dname=="인플루엔자":
                return "고열·근육통 가능. 48시간 이내면 항바이러스제 고려(의료진 판단)."
            if dname=="파라인플루엔자":
                return "크룹성 기침 가능. 발열 동반 시 해열·가습, 호흡곤란 악화 시 응급."
            if dname=="수족구":
                return "구내통증으로 수분섭취 저하 흔함 → 탈수 주의."
            if dname=="노로":
                val = fields.get("설사(회/일)")
                try: dia = float(val or 0)
                except: dia = 0
                return "구토/설사로 탈수 주의, 가볍게 자주 수분." + (" (설사 빈도 높음)" if dia>=6 else "")
            if dname=="마이코플":
                return "기침 장기화 가능. 호흡곤란·고열 지속 시 진료."
        except: pass
        return ""

    if run:
        st.subheader("📋 해석 결과")

        # ----- ensure base defaults so NameError never occurs -----
        cleaned, fs_all, meds_lines, abx_lines, cmp_lines = [], [], [], [], []
        extra_all = {k:v for k,v in (special_vals or {}).items() if entered(v)}  # safe even if empty dict

        if mode == "일반/암":
            if show_labs:
                for line in interpret_labs(vals, extras): st.write(line)
                if (storage_key or nickname) and st.session_state.records.get(storage_key or nickname):
                    st.markdown("### 🔍 수치 변화 비교 (이전 기록 대비)")
                    cmp_lines = compare_with_previous(storage_key or nickname, {k: vals.get(k) for k in ORDER if entered(vals.get(k))}) or []
                    for l in cmp_lines: st.write(l)

                fs_all = food_suggestions(vals, anc_place) or []
                cleaned = [s for s in fs_all if not re.search(r\"(철분|비타민|iron|vitamin)\", s, flags=re.I)]
                if cleaned:
                    st.markdown(\"### 🥗 식이가이드\")
                    for s in cleaned: st.markdown(s)

            if meds:
                st.markdown(\"### 💊 항암제 부작용·상호작용 요약\")
                meds_lines = summarize_meds(meds) or []
                for line in meds_lines: st.write(line)

            abx_lines = abx_summary(extras.get(\"abx\", {})) if extras.get(\"abx\") else []
            if abx_lines:
                st.markdown(\"### 🧪 항생제 주의 요약\")
                for l in abx_lines: st.write(l)

            st.markdown(\"### 🌡️ 발열 가이드\"); st.write(FEVER_GUIDE)

        elif mode == "소아(일상가이드)":
            st.write(_triage(ped_inputs))

        else:  # 감염질환
            if infection:
                st.write(_triage(ped_inputs))
                tip = _tip(infection, infect_specific)
                if tip:
                    st.markdown(\"#### 🧾 질환별 안내\"); st.write(tip)

        # ===== Report build & download =====
        meta = {\"group\": group, \"cancer\": cancer, \"anc_place\": anc_place, \"mode\": mode, \"infection\": infection}

        fs_report = []
        if mode==\"일반/암\" and show_labs:
            for s in (fs_all or []):
                if not re.search(r\"(철분|비타민|iron|vitamin)\", s, flags=re.I):
                    fs_report.append(s)

        report_md = build_report(mode, meta, vals if show_labs else {}, cmp_lines, extra_all, meds_lines, fs_report, abx_lines)

        if extra_all and show_labs:
            sp_lines = [f\"- {k}: {v}\" for k,v in extra_all.items()]
            report_md += \"\\n\\n### 🧪 특수검사 요약\\n\" + \"\\n\".join(sp_lines) + \"\\n\"

        if mode != \"일반/암\":
            report_md += \"\\n\\n### 🧒 소아 입력 요약\\n\"
            for k, v in ped_inputs.items():
                if v not in (None, \"\", 0, False):
                    report_md += f\"- {k}: {v}\\n\"
            if infection and infect_specific:
                report_md += f\"\\n### 🧾 {infection} 전용 항목\\n\"
                for k, v in infect_specific.items():
                    if v not in (None, \"\", 0, False):
                        report_md += f\"- {k}: {v}\\n\"

        st.download_button(\"📥 보고서(.md) 다운로드\", data=report_md.encode(\"utf-8\"),
                           file_name=f\"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md\",
                           mime=\"text/markdown\")
        st.download_button(\"📄 보고서(.txt) 다운로드\", data=report_md.encode(\"utf-8\"),
                           file_name=f\"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt\",
                           mime=\"text/plain\")
        try:
            pdf_bytes = md_to_pdf_bytes_fontlocked(report_md)
            st.download_button(\"🖨️ 보고서(.pdf) 다운로드\", data=pdf_bytes,
                               file_name=f\"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf\",
                               mime=\"application/pdf\")
        except Exception:
            st.info(\"PDF 모듈이 없거나 글꼴이 없어 PDF 생성이 비활성화되었습니다. (pip install reportlab)\")

        # 저장
        record = {\"ts\": datetime.now().strftime(\"%Y-%m-%d %H:%M:%S\"),
                  \"mode\": mode, \"group\": group, \"cancer\": cancer, \"infection\": infection,
                  \"labs\": {k: vals.get(k) for k in ORDER if entered(vals.get(k))} if show_labs else {},
                  \"extra\": extra_all, \"meds\": meds, \"extras\": extras, \"ped_inputs\": ped_inputs}
        key = (storage_key or nickname or \"\").strip()
        if key:
            st.session_state.records.setdefault(key, []).append(record)
            st.success(f\"저장되었습니다. 저장키: **{key}**\")
        else:
            st.info(\"별명과 PIN(4자리)을 입력하면 안전하게 저장/그래프 기능을 사용할 수 있어요.\")

    # ===== 그래프 & 사전 =====
    render_graphs()
    st.markdown(\"---\")
    st.header(\"📚 약물 사전 (한글 병기)\")
    with st.expander(\"열기 / 닫기\", expanded=False):
        st.caption(\"검색 + 간단 테이블\")
        try:
            ac_rows = []
            for k, v in ANTICANCER.items():
                alias = v.get(\"alias\",\"\" ); aes = \", \".join(v.get(\"aes\", []))
                ac_rows.append({\"약물\": k, \"한글명\": alias, \"부작용\": aes})
            # 보강 항목도 포함
            ac_rows.append({\"약물\": \"MTX\", \"한글명\":\"메토트렉세이트\", \"부작용\": \"\"})
            ac_rows.append({\"약물\": \"6-MP\", \"한글명\":\"6-머캅토퓨린\", \"부작용\": \"\"})
            if HAS_PD:
                ac_df = pd.DataFrame(ac_rows)
                q = st.text_input(\"🔎 항암제 검색\", key=\"drug_dict_search\")
                if q:
                    ql = q.strip().lower()
                    ac_df = ac_df[ac_df.apply(lambda r: any(ql in str(x).lower() for x in r), axis=1)]
                st.dataframe(ac_df, use_container_width=True, hide_index=True)
        except Exception:
            pass

    st.caption(FOOTER_CAFE); st.markdown(\"> \" + DISCLAIMER)
