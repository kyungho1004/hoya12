# -*- coding: utf-8 -*-
import os
import datetime
import streamlit as st

def _chemo_list_for_diagnosis(diag_map, diagnosis, fallback_groups=("혈액암","고형암","육종","희귀암")):
    if not isinstance(diag_map, dict):
        return []
    # Try direct hits in any group
    for g in fallback_groups:
        items = diag_map.get(g, {})
        if isinstance(items, dict) and diagnosis in items:
            return items.get(diagnosis, [])
    # Fuzzy match (contains)
    for g, items in diag_map.items():
        if isinstance(items, dict):
            for name, lst in items.items():
                try:
                    if diagnosis and str(diagnosis) in str(name):
                        return lst or []
                except Exception:
                    continue
    return []


def _pref_value(st, *keys, fallback_name=None):
    """Return first non-empty numeric from session_state keys or None.
    keys: ordered preference (20종 -> 인라인 -> 소아 등)"""
    for k in keys:
        v = st.session_state.get(k, None)
        if v not in (None, ""):
            try:
                return float(v)
            except Exception:
                try:
                    return float(str(v).strip())
                except Exception:
                    pass
    # legacy locals fallback by name (string)
    if fallback_name and fallback_name in globals():
        try:
            return float(globals()[fallback_name])
        except Exception:
            return None
    return None

def _safe_interpret_summary(st, group=None, diagnosis=None):
    msgs = []
    # core
    WBC = _pref_value(st, "WBC_20","WBC_inline","WBC_ped", fallback_name="WBC")
    Hb  = _pref_value(st, "Hb_20","Hb_inline","Hb_ped", fallback_name="Hb")
    PLT = _pref_value(st, "PLT_20","PLT_inline","PLT_ped", fallback_name="PLT")
    ANC = _pref_value(st, "ANC_20","ANC_inline","ANC_ped", fallback_name="ANC")
    CRP = _pref_value(st, "CRP_20","CRP_inline","CRP_ped", fallback_name="CRP")
    Na  = _pref_value(st, "Na_20","Na_inline", fallback_name="Na")
    K   = _pref_value(st, "K_20","K_inline", fallback_name="K")
    Cr  = _pref_value(st, "Cr_20","Cr_inline", fallback_name="Creatinine")
    Tb  = _pref_value(st, "Tb_20", fallback_name="TBILI")
    BNP = _pref_value(st, "BNP_toggle", fallback_name="BNP")
    Alb = _pref_value(st, "Alb_20","Alb_inline", fallback_name="Alb")
    LD  = _pref_value(st, "LD_20","LD_inline", fallback_name="LDH")
    Glu = _pref_value(st, "Glu_20","Glu_inline", fallback_name="Glucose")

    # urine for ACR/UPCR (toggle section priority)
    alb_unit = st.session_state.get("alb_unit_toggle") or st.session_state.get("alb_unit_inline") or "mg/L"
    alb_val  = st.session_state.get("alb_val_toggle") or st.session_state.get("alb_q_inline")
    prot_val = st.session_state.get("prot_val_toggle") or st.session_state.get("prot_q_inline")
    ucr_val  = st.session_state.get("ucr_val_toggle") or st.session_state.get("ucr_q_inline")

    # compute ACR/UPCR with safe fallbacks
    try:
        from .helpers import compute_acr, compute_upcr
    except Exception:
        def compute_acr(alb_mg_L, u_cr_mg_dL):
            if not alb_mg_L or not u_cr_mg_dL:
                return None
            # mg/L to mg/g (divide by (Cr mg/dL)*0.01 to get g/L), simplified common approx
            return (alb_mg_L / (u_cr_mg_dL * 10.0)) * 1000.0  # rough mg/g
        def compute_upcr(u_prot_mg_dL, u_cr_mg_dL):
            if not u_prot_mg_dL or not u_cr_mg_dL:
                return None
            return (u_prot_mg_dL / u_cr_mg_dL) * 1000.0  # mg/g

    acr = None
    upcr = None
    try:
        if alb_val is not None and ucr_val not in (None, ""):
            alb_mg_L = float(alb_val) * (10.0 if alb_unit == "mg/dL" else 1.0)
            acr = compute_acr(alb_mg_L if alb_mg_L else None, float(ucr_val) if ucr_val else None)
        if prot_val not in (None, "") and ucr_val not in (None, ""):
            upcr = compute_upcr(float(prot_val) if prot_val else None, float(ucr_val) if ucr_val else None)
    except Exception:
        pass

    # rules
    if ANC is not None:
        if ANC < 500: msgs.append("⚠️ 중증 호중구감소(ANC<500): 발열 시 패혈증 위험 — 즉시 내원 권고")
        elif ANC < 1000: msgs.append("주의: 중등도 호중구감소(ANC<1000)")
        elif ANC < 1500: msgs.append("경도 호중구감소(ANC<1500)")
    if Hb is not None and Hb < 10: msgs.append("빈혈(Hb<10) — 증상/산소포화도 고려하여 평가")
    if PLT is not None:
        if PLT < 50: msgs.append("⚠️ 혈소판 감소(PLT<50k): 출혈주의, 처치 전 확인")
        elif PLT < 100: msgs.append("혈소판 경감(PLT<100k)")
    if CRP is not None and CRP >= 5: msgs.append("염증수치 상승(CRP≥5)")
    if Na is not None and Na < 130: msgs.append("저나트륨(Na<130)")
    if K is not None:
        if K >= 5.5: msgs.append("⚠️ 고칼륨(K≥5.5) — 심전도/약물검토 필요")
        elif K < 3.0: msgs.append("저칼륨(K<3.0)")
    if Cr is not None and Cr >= 2.0: msgs.append("신장기능 저하(Cr≥2.0) 의심")
    if Tb is not None and Tb >= 2.0: msgs.append("담즙정체/간기능 이상(Tb≥2.0) 의심")
    if BNP is not None and BNP > 100: msgs.append("BNP 상승(>100) — 심부전/과수분 상태 고려")

    if acr is not None:
        if acr >= 300: msgs.append("단백뇨(ACR≥300 mg/g)")
        elif acr >= 30: msgs.append("미세알부민뇨(ACR 30–299 mg/g)")
    if upcr is not None:
        if upcr >= 300: msgs.append("UPCR≥300 mg/g (중등도 이상 단백뇨)")
        elif upcr >= 150: msgs.append("UPCR≥150 mg/g (경증 이상 단백뇨)")

    # pediatric hints
    if group and ("소아" in str(group)):
        Tmax = _pref_value(st, "sx_fever_max")
        days = _pref_value(st, "sx_fever_days")
        if Tmax and Tmax >= 39: msgs.append("소아 고열(≥39℃) — 탈수/해열제 용량 확인")
        if days and days >= 5: msgs.append("소아 발열 5일 이상 — 합병증/원인 재평가 권고")

    # Final
    if not msgs:
        msgs = ["특이 위험 신호 없음(입력값 기준). 증상/진찰/영상·검사와 함께 종합 판단 필요."]
    return msgs

import pandas as pd

from .config import VERSION, APP_TITLE, BRAND, KST_NOTE
from .helpers import (
    is_valid_pin, key_from,
    compute_acr, compute_upcr, interpret_acr, interpret_upcr,
    pediatric_guides, build_report_md, build_report_txt, build_report_pdf_bytes
)
from .graphs import render_graphs
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
os.makedirs(DATA_DIR, exist_ok=True)
HISTORY_CSV = os.path.join(DATA_DIR, "history.csv")

def load_css():
    try:
        css_path = os.path.join(os.path.dirname(__file__), "style.css")
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception:
        pass

def save_row(row: dict):
    cols = [
        "timestamp","user_key","category","diagnosis",
        "WBC","Hb","PLT","ANC","CRP",
        "Urine Alb (mg/L)","Urine Prot (mg/dL)","Urine Cr (mg/dL)",
        "Ferritin","LDH","Uric acid","ESR","Retic(%)","β2-microglobulin","BNP","Coombs",
        "AST","ALT","ALP","GGT","Total bilirubin","Tb",
        "Na","K","Ca","Mg","Phos","P","INR","aPTT","Fibrinogen","D-dimer","Triglycerides","Lactate","Albumin","Alb","Glucose","Glu","Total protein","TP","Creatinine","Cr",
        "ACR (mg/g)","UPCR (mg/g)","Chemo","Antibiotics"
    ]
    df_new = pd.DataFrame([row], columns=cols)
    if os.path.exists(HISTORY_CSV):
        try:
            df_old = pd.read_csv(HISTORY_CSV)
            df = pd.concat([df_old, df_new], ignore_index=True)
        except Exception:
            df = df_new
    else:
        df = df_new
    df.to_csv(HISTORY_CSV, index=False)

def main():

    # --- safe module binding (avoid NameError/UnboundLocalError) ---
    try:
        from . import drug_data as _drug_data
    except Exception:
        import importlib
        _drug_data = importlib.import_module("bloodmap_app.drug_data")
    drug_data = _drug_data
    st.set_page_config(page_title=APP_TITLE, layout="centered", initial_sidebar_state="collapsed")
    load_css()
    st.markdown(f"### {APP_TITLE} — {VERSION}")
    st.caption(f"{BRAND} · {KST_NOTE}")
    st.divider()

    # ===== User identity (별명 + PIN) =====
    c1, c2 = st.columns([2,1])
    with c1:
        alias = st.text_input("별명", placeholder="예: 민트초코")
    with c2:
        pin = st.text_input("PIN (4자리 숫자)", max_chars=4, placeholder="0000")
    valid_pin = is_valid_pin(pin)
    user_key = key_from(alias, pin) if valid_pin else ""
    if not valid_pin and pin:
        st.error("PIN은 숫자 4자리만 가능해요. 예: 0427")
    st.markdown(f"**저장키:** `{user_key or '별명#PIN 형식'}`")

    st.divider()

    # ===== Tabs =====
    tabs = st.tabs(["기본 수치","특수/소변","약물 선택","소아 가이드","결과/내보내기"])

    # ===== Diagnosis =====
    with st.container():
        group = st.radio("암 그룹", ["혈액암","고형암","육종","희귀암"], horizontal=True)
        st.session_state["group_sel"] = group
        group_cur = (group if "group" in locals() else st.session_state.get("group_sel") or "혈액암")
        diag_map = getattr(drug_data, "CHEMO_BY_DIAGNOSIS", {}) or {}

        # --- 혈액암/고형암/육종/희귀암 프리셋(폴백 확장) ---
        _F_DIAG = {
            "혈액암": {
                "AML(급성 골수성 백혈병)": [
                    "Cytarabine (사이타라빈)","Daunorubicin (다우노루비신)","Idarubicin (이다루비신)",
                    "Gemtuzumab ozogamicin (게무투주맙 오조가마이신)","Midostaurin (미도스타우린)"
                ],
                "APL(급성 전골수성 백혈병)": [
                    "All-trans retinoic acid (ATRA)",
                    "Arsenic trioxide (ATO)",
                    "Methotrexate (메토트렉세이트(MTX))",
                    "6-Mercaptopurine (6-MP(머캅토퓨린))",
                    "Daunorubicin (다우노루비신)","Idarubicin (이다루비신)"
                ],
                "ALL(급성 림프구성 백혈병)": [
                    "Vincristine (빈크리스틴)","Prednisone (프레드니손)","Dexamethasone (덱사메타손)",
                    "Asparaginase (아스파라기나아제)","Daunorubicin (다우노루비신)",
                    "Methotrexate (메토트렉세이트(MTX))","6-Mercaptopurine (6-MP(머캅토퓨린))",
                    "Cytarabine (사이타라빈)"
                ],
                "CLL(만성 림프구성 백혈병)": [
                    "Fludarabine (플루다라빈)","Cyclophosphamide (사이클로포스파마이드)","Rituximab (리툭시맙)",
                    "Bendamustine (벤다무스틴)","Venetoclax (베네토클락스)","Obinutuzumab (오비누투주맙)",
                    "Acalabrutinib (아칼라브루티닙)","Ibrutinib (이브루티닙)"
                ],
                "CML(만성 골수성 백혈병)": ["Imatinib (이매티닙)","Dasatinib (다사티닙)","Nilotinib (닐로티닙)"],
                "DLBCL(미만성 거대B세포림프종)": ["Rituximab","Cyclophosphamide","Doxorubicin","Vincristine","Prednisone","Polatuzumab vedotin"],
                "Hodgkin lymphoma": ["Doxorubicin","Bleomycin","Vinblastine","Dacarbazine","Brentuximab vedotin"],
                "MM(다발골수종)": ["Bortezomib","Lenalidomide","Dexamethasone","Daratumumab","Cyclophosphamide"],
                "MDS(골수이형성증후군)": ["Azacitidine","Decitabine"]
            },
            "고형암": {
                "폐암(NSCLC-비편평)": ["Cisplatin","Pemetrexed","Carboplatin","Paclitaxel","Pembrolizumab"],
                "폐암(NSCLC-편평)": ["Cisplatin","Gemcitabine","Carboplatin","Paclitaxel","Pembrolizumab"],
                "소세포 폐암(SCLC)": ["Etoposide","Cisplatin","Carboplatin","Atezolizumab"],
                "식도암": ["Cisplatin","5-FU","Oxaliplatin","Leucovorin"],
                "위암": ["5-FU","Oxaliplatin","Docetaxel","Capecitabine"],
                "대장암": ["5-FU","Oxaliplatin","Irinotecan","Leucovorin","Capecitabine","Bevacizumab"],
                "간암(HCC)": ["Atezolizumab","Bevacizumab","Sorafenib","Lenvatinib"],
                "담도암": ["Gemcitabine","Cisplatin","Oxaliplatin"],
                "췌장암": ["5-FU","Oxaliplatin","Irinotecan","Leucovorin","Gemcitabine","nab-Paclitaxel"],
                "유방암": ["Doxorubicin","Cyclophosphamide","Paclitaxel","Docetaxel","Trastuzumab","Pertuzumab"],
                "난소암": ["Carboplatin","Paclitaxel","Docetaxel"],
                "자궁내막암": ["Carboplatin","Paclitaxel"],
                "자궁경부암": ["Cisplatin","Carboplatin","Paclitaxel","Bevacizumab"],
                "신장암": ["Pembrolizumab","Axitinib","Nivolumab","Ipilimumab"],
                "방광암": ["Gemcitabine","Cisplatin","Methotrexate","Vinblastine","Doxorubicin"],
                "전립선암": ["Docetaxel","Abiraterone","Prednisone","Enzalutamide","ADT"],
                "갑상선암": ["Lenvatinib","Sorafenib"],
                "두경부암": ["Cetuximab","Cisplatin","Carboplatin","5-FU","Docetaxel"]
            },
            "육종": {
                "골육종(MAP)": ["High-dose Methotrexate (고용량 메토트렉세이트)","Doxorubicin","Cisplatin"],
                "유잉육종(VAC/IE)": ["Vincristine","Actinomycin D","Cyclophosphamide","Ifosfamide","Etoposide"],
                "횡문근육종": ["Vincristine","Actinomycin D","Cyclophosphamide","Ifosfamide","Etoposide"]
            },
            "희귀암": {
                "신경모세포종": ["Cyclophosphamide","Doxorubicin","Vincristine","Carboplatin","Etoposide","Ifosfamide"],
                "윌름스종양": ["Vincristine","Dactinomycin(Actinomycin D)","Doxorubicin"],
                "간모세포종": ["Cisplatin","Doxorubicin","Vincristine","5-FU"],
                "GCT(BEP)": ["Bleomycin","Etoposide","Cisplatin"],
                "수모세포종": ["Cisplatin","Vincristine","Cyclophosphamide","Etoposide"]
            }
        }
        # merge fallback into loaded map (without overwriting existing)
        for _grp, _items in _F_DIAG.items():
            base = diag_map.get(_grp, {})
            for k, v in _items.items():
                base.setdefault(k, v)
            diag_map[_grp] = base
        diag_options = list(diag_map.get(group_cur, {}).keys()) or ["AML(급성 골수성 백혈병)"]
        if not diag_options:
            diag_options = ["-"]
        diagnosis = st.selectbox("진단명", diag_options, index=0)

        # --- 항암제(진단별 선택) ---
        if st.session_state.get("mode_main","암")=="암":
            with st.expander("🧬 항암제(진단별 선택)", expanded=False):

            # --- 기본 피수치(20종) ---
            if st.session_state.get("mode_main","암")=="암":
            with st.expander("🧪 기본 피수치(20종)", expanded=False):
                st.caption("필요 수치만 입력하세요. 입력값은 결과/해석에 반영됩니다.")
                def _numtxt(label, key):
                    val = st.session_state.get(key, "")
                    return st.text_input(label, value=str(val) if val not in (None, "") else "", key=key, placeholder="")
                c1,c2,c3,c4,c5 = st.columns(5)
                _numtxt("WBC(×10³/µL)", "WBC_20"); _numtxt("Hb(g/dL)", "Hb_20"); _numtxt("PLT(×10³/µL)", "PLT_20"); _numtxt("ANC(/µL)", "ANC_20"); _numtxt("CRP(mg/dL)", "CRP_20")
                c6,c7,c8,c9,c10 = st.columns(5)
                _numtxt("Ca(mg/dL)", "Ca_20"); _numtxt("K(mmol/L)", "K_20"); _numtxt("TP(g/dL)", "TP_20"); _numtxt("LD(U/L)", "LD_20"); _numtxt("P(mg/dL)", "P_20")
                c11,c12,c13,c14,c15 = st.columns(5)
                _numtxt("Alb(g/dL)", "Alb_20"); _numtxt("AST(U/L)", "AST_20"); _numtxt("Cr(mg/dL)", "Cr_20"); _numtxt("Na(mmol/L)", "Na_20"); _numtxt("Glu(mg/dL)", "Glu_20")
                c16,c17,c18,c19,c20 = st.columns(5)
                _numtxt("ALT(U/L)", "ALT_20"); _numtxt("UA(mg/dL)", "UA_20"); _numtxt("Tb(mg/dL)", "Tb_20"); _numtxt("Ferritin(ng/mL)", "Ferritin_20"); _numtxt("D-dimer(µg/mL)", "Ddimer_20")
            # 진단별 약물 목록 (drug_data 우선, 없으면 폴백 맵 사용)
            diag_map = getattr(drug_data, "CHEMO_BY_DIAGNOSIS", {})
            chemo_list = _chemo_list_for_diagnosis(diag_map, diagnosis)
            if not chemo_list and "고형암" in str(group):
                chemo_list = ["Cisplatin (시스플라틴)","Carboplatin (카보플라틴)","Paclitaxel (파클리탁셀)","Gemcitabine (젬시타빈)","5-FU (플루오로우라실)","Oxaliplatin (옥살리플라틴)"]
            if not chemo_list and "혈액암" in str(group):
                chemo_list = ["Cytarabine (사이타라빈)","Daunorubicin (다우노루비신)","Idarubicin (이다루비신)","Methotrexate (메토트렉세이트(MTX))","6-Mercaptopurine (6-MP(머캅토퓨린))"]
            sel_chemo = st.multiselect("항암제 선택(진단별)", options=chemo_list, default=chemo_list, key="chemo_by_diagnosis")
            if not chemo_list:
                st.caption("진단별 약물 데이터가 비어 있습니다. drug_data.CHEMO_BY_DIAGNOSIS에 추가하거나 메시지로 알려주세요.")
    

        # Quick preview for core labs on the first tab
        st.markdown("#### 🧪 피수치(핵심) 미리보기")
        q1,q2,q3,q4,q5 = st.columns(5)
        ss = st.session_state
        with q1: st.metric("WBC (×10³/µL)", f"{ss.get('WBC_val',0.0):.1f}" if ss.get('WBC_val') else "-")
        with q2: st.metric("Hb (g/dL)", f"{ss.get('Hb_val',0.0):.1f}" if ss.get('Hb_val') else "-")
        with q3: st.metric("PLT (×10³/µL)", f"{ss.get('PLT_val',0.0):.0f}" if ss.get('PLT_val') else "-")
        with q4: st.metric("ANC (/µL)", f"{ss.get('ANC_val',0.0):.0f}" if ss.get('ANC_val') else "-")
        with q5: st.metric("CRP (mg/dL)", f"{ss.get('CRP_val',0.0):.2f}" if ss.get('CRP_val') else "-")
        st.caption("자세한 입력은 상단의 '기본 수치' 탭에서 가능합니다.")

    # ===== Basic panel =====
    with st.container():
        def _numfield(label, key):
            v = st.session_state.get(key, "")
            return st.text_input(label, value=str(v) if v not in (None, "") else "", key=key, placeholder="")

        st.markdown("#### 기본 수치")
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            WBC = _numfield("WBC(×10³/µL)", "WBC_val")
        with c2:
            Hb  = _numfield("Hb(g/dL)", "Hb_val")
        with c3:
            PLT = _numfield("혈소판(×10³/µL)", "PLT_val")
        with c4:
            ANC = _numfield("호중구 ANC(/µL)", "ANC_val")
        with c5:
            CRP = _numfield("CRP(mg/dL)", "CRP_val")


        st.markdown("#### 기본 수치(확장)")
        # 전해질/간·신장/대사 핵심
        b1,b2,b3,b4 = st.columns(4)
        with b1:
            Ca = _numfield("Ca(칼슘, mg/dL)", "Ca_val")
            P_ = _numfield("P(인, mg/dL)", "P_val")
            Na = _numfield("Na(나트륨, mmol/L)", "Na_val")
        with b2:
            K_ = _numfield("K(칼륨, mmol/L)", "K_val")
            Alb = _numfield("Alb(알부민, g/dL)", "Alb_val")
            Glu = _numfield("Glu(혈당, mg/dL)", "Glu_val")
        with b3:
            TP = _numfield("TP(총단백질, g/dL)", "TP_val")
            AST = _numfield("AST(간수치, U/L)", "AST_val_basic")
            ALT = _numfield("ALT(간세포수치, U/L)", "ALT_val_basic")
        with b4:
            LD = _numfield("LD(유산탈수효소, U/L)", "LD_val")
            sCr = _numfield("Cr(크레아티닌, mg/dL)", "Cr_val")
            UA = _numfield("UA(요산, mg/dL)", "UA_val")
            Tb = _numfield("Tb(총빌리루빈, mg/dL)", "Tb_val")

        # 간단 해석 캡션
        from .helpers import interpret_na, interpret_k, interpret_ca, interpret_phos, interpret_ast, interpret_alt, interpret_ldh as _int_ldh, interpret_tbili, interpret_ua
        hints = []
        hints += [interpret_na(Na), interpret_k(K_), interpret_ca(Ca), interpret_phos(P_)]
        hints += [interpret_ast(AST), interpret_alt(ALT)]
        hints += [(_int_ldh(LD) if LD else "")]
        hints += [interpret_tbili(Tb), interpret_ua(UA)]
        for h in hints:
            if h: st.caption("• " + h)

        # # (removed legacy oncology quick panel; using new toggles)
# ===== Special/Urine panel =====
    with tabs[0]:
        st.markdown("#### 특수/소변 검사")
        st.caption("요단백·요알부민·혈뇨 등은 필요한 값만 입력하세요.")
        unit_col, _, _ = st.columns(3)
        with unit_col:
            alb_unit = st.radio("요 알부민 단위", ["mg/L","mg/dL"], horizontal=True, index=0)
        u1, u2, u3 = st.columns(3)
        with u1:
            urine_albumin_val = st.number_input(f"요 알부민 ({alb_unit})", min_value=0.0, step=1.0, format="%.1f")
        with u2:
            urine_protein_mg_dL = st.number_input("요 단백 (mg/dL)", min_value=0.0, step=1.0, format="%.1f")
        with u3:
            urine_cr_mg_dL = st.number_input("요 크레아티닌 (mg/dL)", min_value=0.0, step=0.1, format="%.1f")

        urine_albumin_mg_L = urine_albumin_val*10.0 if alb_unit == "mg/dL" else urine_albumin_val
        acr = compute_acr(urine_albumin_mg_L if urine_albumin_mg_L else None, urine_cr_mg_dL if urine_cr_mg_dL else None)
        upcr = compute_upcr(urine_protein_mg_dL if urine_protein_mg_dL else None, urine_cr_mg_dL if urine_cr_mg_dL else None)

        d1, d2 = st.columns(2)
        with d1:
            st.metric("ACR (mg/g)", f"{acr:.0f}" if acr else "-")
            st.caption(interpret_acr(acr))
        with d2:
            st.metric("UPCR (mg/g)", f"{upcr:.0f}" if upcr else "-")
            st.caption(interpret_upcr(upcr))

        st.markdown("#### 특수검사")
        e1,e2,e3 = st.columns(3)
        with e1:
            Ferritin = st.number_input("Ferritin (ng/mL)", min_value=0.0, step=1.0, format="%.1f")
            LDH = st.number_input("LDH (U/L)", min_value=0.0, step=1.0, format="%.0f")
        with e2:
            UricAcid = st.number_input("Uric acid (mg/dL)", min_value=0.0, step=0.1, format="%.2f")
            ESR = st.number_input("ESR (mm/hr)", min_value=0.0, step=1.0, format="%.0f")
        with e3:
            Retic = st.number_input("Retic(%)", min_value=0.0, step=0.1, format="%.1f")
            B2M = st.number_input("β2-microglobulin (mg/L)", min_value=0.0, step=0.1, format="%.2f")
        Coombs = st.selectbox("Coombs 검사", ["직접항글로불린 양성","직접항글로불린 음성","간접항글로불린 양성","간접항글로불린 음성","선택 안 함"], index=4)

        from .helpers import interpret_ferritin, interpret_ldh, interpret_ua, interpret_esr, interpret_b2m
        extra_msgs = []
        if Ferritin: extra_msgs.append(interpret_ferritin(Ferritin))
        if LDH: extra_msgs.append(interpret_ldh(LDH))
        if UricAcid: extra_msgs.append(interpret_ua(UricAcid))
        if ESR: extra_msgs.append(interpret_esr(ESR))
        if B2M: extra_msgs.append(interpret_b2m(B2M))
        if Coombs and Coombs != "-": extra_msgs.append(f"Coombs: {Coombs}")
        for m in extra_msgs:
            st.caption("• " + m)

        st.info("단위: ACR = Alb(mg/L)/Cr(mg/dL)×100, UPCR = Prot(mg/dL)/Cr(mg/dL)×1000")

        st.markdown("#### 간기능/전해질/응고")
        l1,l2,l3 = st.columns(3)
        with l1:
            AST = st.number_input("AST (U/L)", min_value=0.0, step=1.0, format="%.0f")
            ALT = st.number_input("ALT (U/L)", min_value=0.0, step=1.0, format="%.0f")
            ALP = st.number_input("ALP (U/L)", min_value=0.0, step=1.0, format="%.0f")
            GGT = st.number_input("GGT (U/L)", min_value=0.0, step=1.0, format="%.0f")
            TBILI = st.number_input("Total bilirubin (mg/dL)", min_value=0.0, step=0.1, format="%.2f")
        with l2:
            Na = st.number_input("Na (mmol/L)", min_value=0.0, step=0.5, format="%.1f")
            K  = st.number_input("K (mmol/L)", min_value=0.0, step=0.1, format="%.1f")
            Ca = st.number_input("Ca (mg/dL)", min_value=0.0, step=0.1, format="%.2f")
            Mg = st.number_input("Mg (mg/dL)", min_value=0.0, step=0.1, format="%.2f")
            Phos = st.number_input("Phos (mg/dL)", min_value=0.0, step=0.1, format="%.2f")
        with l3:
            INR = st.number_input("INR", min_value=0.0, step=0.1, format="%.2f")
            aPTT = st.number_input("aPTT (sec)", min_value=0.0, step=0.5, format="%.1f")
            Fibrinogen = st.number_input("Fibrinogen (mg/dL)", min_value=0.0, step=1.0, format="%.0f")
            Ddimer = st.number_input("D-dimer (µg/mL FEU)", min_value=0.0, step=0.1, format="%.2f")
            TG = st.number_input("Triglycerides (mg/dL)", min_value=0.0, step=1.0, format="%.0f")
            Lactate = st.number_input("Lactate (mmol/L)", min_value=0.0, step=0.1, format="%.2f")

        from .helpers import (
            interpret_ast, interpret_alt, interpret_alp, interpret_ggt, interpret_tbili,
            interpret_na, interpret_k, interpret_ca, interpret_mg, interpret_phos,
            interpret_inr, interpret_aptt, interpret_fibrinogen, interpret_ddimer,
            interpret_tg, interpret_lactate
        )
        quick = []
        quick += [interpret_ast(AST), interpret_alt(ALT), interpret_alp(ALP), interpret_ggt(GGT), interpret_tbili(TBILI)]
        quick += [interpret_na(Na), interpret_k(K), interpret_ca(Ca), interpret_mg(Mg), interpret_phos(Phos)]
        quick += [interpret_inr(INR), interpret_aptt(aPTT), interpret_fibrinogen(Fibrinogen), interpret_ddimer(Ddimer)]
        quick += [interpret_tg(TG), interpret_lactate(Lactate)]
        for q in quick:
            if q: st.caption("• " + q)


    # ===== Pediatrics =====
    with tabs[0]:
        st.markdown("#### 소아 패널 / 해석 가이드")
        c1,c2,c3 = st.columns(3)
        with c1:
            age_years = st.number_input("나이(년)", min_value=0, step=1)
        with c2:
            age_months = st.number_input("나이(개월)", min_value=0, step=1, help="년 입력 시 자동 계산됨")
        with c3:
            weight = st.number_input("체중(kg)", min_value=0.0, step=0.1)
        if age_years and not age_months:
            st.session_state["auto_age_months"] = age_years*12
            st.experimental_rerun()
        group_ped = st.selectbox("소아 질환군", ["-", "소아-일상", "소아-감염", "소아-혈액암", "소아-고형암", "소아-육종", "소아-희귀암"])
        # 소아 증상 요약 메시지(참고용)
        ped_msgs = []
        try:
            suspect = st.session_state.get("ped_suspect")
            if suspect and suspect != "-":
                ped_msgs.append(f"의심 질환: {suspect}")
            pain = st.session_state.get("sx_pain")
            if pain and pain != "없음":
                ped_msgs.append(f"통증: {pain}")
            rhin = st.session_state.get("sx_rhin")
            if rhin and rhin != "없음":
                ped_msgs.append(f"콧물: {rhin}")
            cough = st.session_state.get("sx_cough")
            if cough and cough != "없음":
                ped_msgs.append(f"기침: {cough}")
            sore = st.session_state.get("sx_sore")
            if sore and sore != "없음":
                ped_msgs.append(f"인후통: {sore}")
            fd = st.session_state.get("sx_fever_days")
            fx = st.session_state.get("sx_fever_max")
            if fd not in (None, "", 0):
                ped_msgs.append(f"발열 {int(fd)}일")
            if fx not in (None, "", 0):
                ped_msgs.append(f"최고체온 {fx}℃")
            vomit = st.session_state.get("sx_vomit")
            if vomit and vomit != "없음":
                ped_msgs.append(f"구토: {vomit}")
            diarrhea = st.session_state.get("sx_diarrhea")
            if diarrhea and diarrhea != "없음":
                ped_msgs.append(f"설사: {diarrhea}")
        except Exception:
            pass
        if not ped_msgs:
            ped_msgs = ["입력된 소아 증상 요약이 없습니다. (참고용)"]

        for m in ped_msgs:
            st.markdown(f"- {m}")

    # ===== Result / Export =====
    with tabs[1]:
        st.info('''이 해석기는 참고용 도구이며, 모든 수치는 개발자와 무관합니다.
결과를 기반으로 반드시 주치의와 상담 후 의학적 판단 및 치료 결정을 하시기 바랍니다.''')
        st.markdown("### 결과 요약")
        if st.button("🧠 해석 보기", key="btn_interpret_results"):
            msgs = _safe_interpret_summary(st, group=group, diagnosis=diagnosis)
            st.markdown("\n".join([f"- {m}" for m in msgs]))
            st.caption("※ 참고용: 해석은 자동 요약이며 최종 의학적 판단은 의료진에게 확인하세요.")
            if st.session_state.get("mode_main","암") == "소아질환":
                fx = st.session_state.get("sx_fever_max"); fd = st.session_state.get("sx_fever_days")
                try:
                    if fx is not None and float(fx) >= 39.5:
                        st.error("🚑 고열(≥39.5℃): 병원 방문 권고")
                    elif fd is not None and int(fd) >= 5:
                        st.warning("⚠️ 발열 5일 이상 지속: 진료 권고")
                except Exception:
                    pass
        # --- 핵심 피수치 요약(상단 고정) ---
        st.markdown("#### 🧪 피수치(핵심)")
        m1, m2, m3, m4, m5 = st.columns(5)
        try:
            with m1: st.metric("WBC (×10³/µL)", f"{WBC:.1f}" if WBC else "-")
            with m2: st.metric("Hb (g/dL)", f"{Hb:.1f}" if Hb else "-")
            with m3: st.metric("PLT (×10³/µL)", f"{PLT:.0f}" if PLT else "-")
            with m4: st.metric("ANC (/µL)", f"{ANC:.0f}" if ANC else "-")
            with m5: st.metric("CRP (mg/dL)", f"{CRP:.2f}" if CRP else "-")
        except Exception:
            pass

        sticky = st.empty()
        header_html = f"""
        <div class='sticky-header'>
          <b>{user_key or "별명#PIN 필요"}</b> · {group} · {diagnosis}
        </div>
        """
        sticky.markdown(header_html, unsafe_allow_html=True)

        if user_key:
            st.success(f"사용자: **{user_key}** · 진단: {diagnosis} · 그룹: {group}")
        else:
            st.warning("별명과 유효한 4자리 PIN을 입력하면 저장/내보내기가 활성화됩니다.")

        derived = {}
        if acr:
            derived["ACR (mg/g)"] = f"{acr:.0f}"
        if upcr:
            derived["UPCR (mg/g)"] = f"{upcr:.0f}"

        values = {
            "WBC": (st.session_state.get("WBC_20") or st.session_state.get("WBC_inline") or st.session_state.get("WBC_ped") or (WBC if "WBC" in locals() else None)) or "",
            "Hb": (st.session_state.get("Hb_20") or st.session_state.get("Hb_inline") or st.session_state.get("Hb_ped") or (Hb if "Hb" in locals() else None)) or "",
            "PLT": (st.session_state.get("PLT_20") or st.session_state.get("PLT_inline") or st.session_state.get("PLT_ped") or (PLT if "PLT" in locals() else None)) or "",
            "ANC": (st.session_state.get("ANC_20") or st.session_state.get("ANC_inline") or st.session_state.get("ANC_ped") or (ANC if "ANC" in locals() else None)) or "",
            "CRP": (st.session_state.get("CRP_20") or st.session_state.get("CRP_inline") or st.session_state.get("CRP_ped") or (CRP if "CRP" in locals() else None)) or "",
            "Urine Alb (mg/L)": urine_albumin_mg_L if urine_albumin_mg_L else "",
            "Ferritin": Ferritin if "Ferritin" in locals() and Ferritin else "",
            "LDH": (st.session_state.get("LD_20") or (LDH if "LDH" in locals() else None)) or "",
            "Uric acid": (st.session_state.get("UA_20") or (UricAcid if "UricAcid" in locals() else None)) or "",
            "ESR": ESR if "ESR" in locals() and ESR else "",
            "Retic(%)": Retic if "Retic" in locals() and Retic else "",
            "β2-microglobulin": B2M if "B2M" in locals() and B2M else "",
            "BNP": BNP if "BNP" in locals() and BNP else "",
            "C3 (보체)": st.session_state.get("C3_toggle",""),
            "C4 (보체)": st.session_state.get("C4_toggle",""),
            "Urine dip Protein": st.session_state.get("UPRO_dip",""),
            "Urine dip WBC-esterase": st.session_state.get("ULEU_dip",""),
            "Urine dip Nitrite": st.session_state.get("UNIT_dip",""),
            "Urine dip pH": st.session_state.get("UpH_dip",""),
            "Pediatric suspect": st.session_state.get("ped_suspect",""),
            "Pain severity": st.session_state.get("sx_pain",""),
            "Rhinorrhea": st.session_state.get("sx_rhin",""),
            "Cough": st.session_state.get("sx_cough",""),
            "Sore throat": st.session_state.get("sx_sore",""),
            "Fever days": st.session_state.get("sx_fever_days",""),
            "Fever Tmax(℃)": st.session_state.get("sx_fever_max",""),
            "Vomiting": st.session_state.get("sx_vomit",""),
            "Diarrhea": st.session_state.get("sx_diarrhea",""),
            "Urine glucose(dip)": st.session_state.get("UGLU_toggle",""),
            "Hematuria(dip)": st.session_state.get("UBLD_toggle",""),
            "Ketone(dip)": st.session_state.get("UKET_toggle",""),
            "Coombs": Coombs if "Coombs" in locals() and Coombs and Coombs!="선택 안 함" else "",
            "AST": (st.session_state.get("AST_inline") or (AST if "AST" in locals() else None)) or "",
            "ALT": (st.session_state.get("ALT_inline") or (ALT if "ALT" in locals() else None)) or "",
            "ALP": ALP if "ALP" in locals() and ALP else "",
            "GGT": GGT if "GGT" in locals() and GGT else "",
            "Total bilirubin": (st.session_state.get("Tb_20") or (TBILI if "TBILI" in locals() else None)) or "",
            "Na": (st.session_state.get("Na_20") or st.session_state.get("Na_inline") or (Na if "Na" in locals() else None)) or "",
            "K": (st.session_state.get("K_20") or st.session_state.get("K_inline") or (K if "K" in locals() else None)) or "",
            "Ca": (st.session_state.get("Ca_20") or st.session_state.get("Ca_inline") or (Ca if "Ca" in locals() else None)) or "",
            "Mg": Mg if "Mg" in locals() and Mg else "",
            "Phos": Phos if "Phos" in locals() and Phos else "",
            "INR": INR if "INR" in locals() and INR else "",
            "aPTT": aPTT if "aPTT" in locals() and aPTT else "",
            "Fibrinogen": Fibrinogen if "Fibrinogen" in locals() and Fibrinogen else "",
            "D-dimer": Ddimer if "Ddimer" in locals() and Ddimer else "",
            "Triglycerides": TG if "TG" in locals() and TG else "",
            "Lactate": Lactate if "Lactate" in locals() and Lactate else "",
            "Urine Prot (mg/dL)": urine_protein_mg_dL if urine_protein_mg_dL else "",
            "Ca": (st.session_state.get("Ca_20") or st.session_state.get("Ca_inline") or (Ca if "Ca" in locals() else None)) or "",
            "P": (st.session_state.get("P_20") or (P_ if "P_" in locals() else None)) or "",
            "Na": (st.session_state.get("Na_20") or st.session_state.get("Na_inline") or (Na if "Na" in locals() else None)) or "",
            "K": K_ if "K_" in locals() and K_ else "",
            "Alb": (st.session_state.get("Alb_inline") or (Alb if "Alb" in locals() else None)) or "",
            "Glu": (st.session_state.get("Glu_inline") or (Glu if "Glu" in locals() else None)) or "",
            "TP": (st.session_state.get("TP_inline") or (TP if "TP" in locals() else None)) or "",
            "AST": (st.session_state.get("AST_inline") or (AST if "AST" in locals() else None)) or "",
            "ALT": (st.session_state.get("ALT_inline") or (ALT if "ALT" in locals() else None)) or "",
            "LD": (st.session_state.get("LD_inline") or (LD if "LD" in locals() else None)) or "",
            "Cr": sCr if "sCr" in locals() and sCr else "",
            "UA": (st.session_state.get("UA_inline") or (UA if "UA" in locals() else None)) or "",
            "Tb": (st.session_state.get("Tb_inline") or (Tb if "Tb" in locals() else None)) or "",
            "Urine Cr (mg/dL)": urine_cr_mg_dL if urine_cr_mg_dL else "",
        }
        meta = {"user_key": user_key or "-", "diagnosis": diagnosis, "category": group}
        md = build_report_md(meta, values, derived, ped_msgs)
        txt = build_report_txt(md)
        pdf_bytes = build_report_pdf_bytes(md)


        # ---- 공유하기 ----
        st.markdown("### 🔗 공유하기")
        try:
            from .config import CAFE_URL, HELP_URL
        except Exception:
            CAFE_URL, HELP_URL = "", ""
        cc1, cc2, cc3 = st.columns([1,1,2])
        with cc1:
            if CAFE_URL:
                st.link_button("카페(가이드/공유)", CAFE_URL, use_container_width=True)
        with cc2:
            if HELP_URL:
                st.link_button("업데이트/문의", HELP_URL, use_container_width=True)
        # 공유 텍스트 구성 (핵심 피수치 요약)
        core_keys = ["WBC","Hb","PLT","ANC","CRP"]
        extra_keys = ["Na","K","Ca","Cr","TBili","AST","ALT","LD","Alb","TP","Glu","BNP"]
        def _fmt(v):
            try:
                if v is None or v == "": return "-"
                if isinstance(v, float) and v.is_integer(): return f"{int(v)}"
                return f"{v}"
            except Exception:
                return f"{v}"
        parts = [f"{k}:{_fmt(values.get(k,''))}" for k in core_keys if values.get(k,"") not in ("",None)]
        parts += [f"{k}:{_fmt(values.get(k,''))}" for k in extra_keys if values.get(k,"") not in ("",None)]
        share_txt = f"[{user_key}] {group} · {diagnosis}\\n" + " | ".join(parts)
        st.code(share_txt, language="text")
        st.download_button("🔗 공유 텍스트(.txt)", data=share_txt, file_name=f"{user_key or 'share'}.txt", disabled=not user_key)
        
        # ---- 내보내기 ----
        st.markdown("### ⬇️ 내보내기")
        cdl1, cdl2, cdl3 = st.columns(3)

        with cdl1:
            st.download_button("📄 결과 .md 다운로드", data=md, file_name=f"{user_key or 'result'}.md", disabled=not user_key)
        with cdl2:
            st.download_button("📝 결과 .txt 다운로드", data=txt, file_name=f"{user_key or 'result'}.txt", disabled=not user_key)
        with cdl3:
            st.download_button("🧾 결과 .pdf 다운로드", data=pdf_bytes, file_name=f"{user_key or 'result'}.pdf", disabled=not user_key)
        st.markdown("#### 한글 폰트 (PDF 인쇄용)")
        from .font_installer import ensure_fonts
        if st.button("📥 한글 폰트 자동 설치(NotoSansKR/NanumGothic)"):
            font_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fonts"))
            res = ensure_fonts(font_dir)
            msg = ", ".join([f"{k}:{v}" for k,v in res.items()])
            st.success(f"폰트 설치 결과: {msg}")
        else:
            font_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fonts"))
            exists = [fn for fn in os.listdir(font_dir) if fn.lower().endswith((".ttf",".otf"))] if os.path.exists(font_dir) else []
            if exists:
                st.caption("감지된 폰트: " + ", ".join(exists))
            else:
                st.caption("설치된 폰트가 없습니다. 위 버튼으로 설치하면 PDF 한글 출력 품질이 좋아집니다.")


        if user_key and st.button("💾 결과 저장 (별명#PIN 별 이력)"):
            ts = datetime.datetime.now().isoformat(timespec="milliseconds")
            row = {
                "timestamp": ts,
                "user_key": user_key,
                "category": group,
                "diagnosis": diagnosis,
                "WBC": WBC, "Hb": Hb, "PLT": PLT, "ANC": ANC, "CRP": CRP,
                "Urine Alb (mg/L)": urine_albumin_mg_L,
                "Urine Prot (mg/dL)": urine_protein_mg_dL,
                "Urine Cr (mg/dL)": urine_cr_mg_dL,
                "Ca": Ca if "Ca" in locals() else 0.0,
                "P": P_ if "P_" in locals() else 0.0,
                "Na": Na if "Na" in locals() else 0.0,
                "K": K_ if "K_" in locals() else 0.0,
                "Alb": Alb if "Alb" in locals() else 0.0,
                "Glu": Glu if "Glu" in locals() else 0.0,
                "TP": TP if "TP" in locals() else 0.0,
                "AST": AST if "AST" in locals() else 0.0,
                "ALT": ALT if "ALT" in locals() else 0.0,
                "LD": LD if "LD" in locals() else 0.0,
                "Cr": sCr if "sCr" in locals() else 0.0,
                "UA": UA if "UA" in locals() else 0.0,
                "Tb": Tb if "Tb" in locals() else 0.0,
                "Ferritin": Ferritin if "Ferritin" in locals() else 0.0,
                "LDH": LDH if "LDH" in locals() else 0.0,
                "Uric acid": UricAcid if "UricAcid" in locals() else 0.0,
                "ESR": ESR if "ESR" in locals() else 0.0,
                "Retic(%)": Retic if "Retic" in locals() else 0.0,
                "β2-microglobulin": B2M if "B2M" in locals() else 0.0,
                "BNP": BNP if "BNP" in locals() else 0.0,
                "Coombs": Coombs if "Coombs" in locals() else "",
                "AST": AST if "AST" in locals() else 0.0,
                "ALT": ALT if "ALT" in locals() else 0.0,
                "ALP": ALP if "ALP" in locals() else 0.0,
                "GGT": GGT if "GGT" in locals() else 0.0,
                "Total bilirubin": TBILI if "TBILI" in locals() else 0.0,
                "Na": Na if "Na" in locals() else 0.0,
                "K": K if "K" in locals() else 0.0,
                "Ca": Ca if "Ca" in locals() else 0.0,
                "Mg": Mg if "Mg" in locals() else 0.0,
                "Phos": Phos if "Phos" in locals() else 0.0,
                "INR": INR if "INR" in locals() else 0.0,
                "aPTT": aPTT if "aPTT" in locals() else 0.0,
                "Fibrinogen": Fibrinogen if "Fibrinogen" in locals() else 0.0,
                "D-dimer": Ddimer if "Ddimer" in locals() else 0.0,
                "Triglycerides": TG if "TG" in locals() else 0.0,
                "Lactate": Lactate if "Lactate" in locals() else 0.0,
                "ACR (mg/g)": float(f"{acr:.2f}") if acr else 0.0,
                "UPCR (mg/g)": float(f"{upcr:.2f}") if upcr else 0.0,
                "Chemo": "; ".join(sel_chemo) if sel_chemo else "",
                "Antibiotics": "; ".join(sel_abx) if sel_abx else "",
            }

            # Duplicate-safe save: if same user_key & timestamp exists, add suffix; skip exact duplicates
            if os.path.exists(HISTORY_CSV):
                try:
                    df_exist = pd.read_csv(HISTORY_CSV)
                    if not df_exist.empty:
                        # exact duplicate row?
                        cols_chk = list(row.keys())
                        dup_mask = (df_exist[["user_key","timestamp"]]
                                    .assign(_join=1))  # dummy to avoid errors if subset missing
                        # Simple check: same user_key & timestamp
                        same_ts = (df_exist["user_key"]==row["user_key"]) & (df_exist["timestamp"]==row["timestamp"])
                        if same_ts.any():
                            row["timestamp"] = row["timestamp"] + "_1"
                except Exception:
                    pass
            save_row(row)
            st.success("저장 완료! 동일한 별명#PIN으로 누적 기록이 저장됩니다.")
            render_graphs(HISTORY_CSV, user_key)

        # 과거 기록이 있으면 바로 그래프 표시
        if user_key:
            try:
                render_graphs(HISTORY_CSV, user_key)
            except Exception:
                pass