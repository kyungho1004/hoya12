# -*- coding: utf-8 -*-
import os
import datetime
import streamlit as st
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
    tabs = st.tabs(["진단 선택", "기본 수치", "특수/소변", "약물 선택", "소아 가이드", "결과/내보내기"])

    # ===== Diagnosis =====
    with tabs[0]:
        group = st.radio("암 그룹", ["혈액암","고형암","육종","희귀암"], horizontal=True)
        st.session_state["group_sel"] = group
        group_cur = (group if "group" in locals() else st.session_state.get("group_sel") or "혈액암")
        diag_map = getattr(drug_data, "CHEMO_BY_DIAGNOSIS", {}) or {}

        # --- 혈액암/고형암/육종/희귀암 프리셋(폴백 확장) ---
        _F_DIAG = {
            "혈액암": {
                "AML(급성 골수성 백혈병)": ["7+3 (Cytarabine + Daunorubicin)", "FLAG-IDA (Fludarabine+Cytarabine+G-CSF+Idarubicin)", "CPX-351"],
                "APL(급성 전골수성 백혈병)": ["ATRA + ATO (All-trans retinoic acid + Arsenic trioxide)", "ATRA + Anthracycline"],
                "ALL(급성 림프구성 백혈병)": ["Hyper-CVAD", "CALGB 기반(유지: POMP)"],
                "CLL(만성 림프구성 백혈병)": ["FCR (Fludarabine/Cyclophosphamide/Rituximab)", "Acalabrutinib + Obinutuzumab", "Venetoclax + Obinutuzumab", "Ibrutinib"],
                "CML(만성 골수성 백혈병)": ["Imatinib", "Dasatinib", "Nilotinib"],
                "DLBCL(미만성 거대B세포림프종)": ["R-CHOP", "Polatuzumab + R-CHP"],
                "Hodgkin lymphoma": ["ABVD", "Brentuximab + AVD"],
                "MM(다발골수종)": ["VRd (Bortezomib/Lenalidomide/Dexamethasone)", "DRd (Daratumumab + Lenalidomide + Dexamethasone)"],
                "MDS(골수이형성증후군)": ["Azacitidine", "Decitabine"]
            },
            "고형암": {
                "폐암(NSCLC-비편평)": ["Cisplatin + Pemetrexed (시스플라틴/페메트렉시드)", "Carboplatin + Paclitaxel (카보플라틴/파클리탁셀)"],
                "폐암(NSCLC-편평)": ["Cisplatin + Gemcitabine (시스플라틴/젬시타빈)", "Carboplatin + Paclitaxel (카보플라틴/파클리탁셀)"],
                "소세포 폐암(SCLC)": ["Etoposide + Cisplatin (EP)", "Etoposide + Carboplatin (EC)"],
                "식도암": ["Cisplatin + 5-FU (FP)", "FOLFOX (5-FU/Leucovorin/Oxaliplatin)"],
                "위암": ["FOLFOX", "FLOT (5-FU/Leucovorin/Oxaliplatin/Docetaxel)", "CAPOX (Capecitabine/Oxaliplatin)"],
                "대장암": ["FOLFOX", "FOLFIRI (5-FU/Leucovorin/Irinotecan)", "CAPOX (Capecitabine/Oxaliplatin)"],
                "간암(HCC)": ["Atezolizumab + Bevacizumab (아테졸리주맙/베바시주맙)", "Sorafenib (소라페닙)", "Lenvatinib (렌바티닙)"],
                "담도암": ["Gemcitabine + Cisplatin (GemCis)", "GEMOX (Gemcitabine/Oxaliplatin)"],
                "췌장암": ["FOLFIRINOX", "Gemcitabine + nab-Paclitaxel"],
                "유방암": ["AC → T (Doxorubicin/Cyclophosphamide → Paclitaxel)", "TC (Docetaxel/Cyclophosphamide)", "Trastuzumab + Pertuzumab + Taxane (HER2+)"],
                "난소암": ["Carboplatin + Paclitaxel", "Carboplatin + Docetaxel"],
                "자궁내막암": ["Carboplatin + Paclitaxel"],
                "자궁경부암": ["Cisplatin(동시방사선)", "Carboplatin + Paclitaxel"],
                "신장암": ["Pembrolizumab + Axitinib", "Nivolumab + Ipilimumab"],
                "방광암": ["Gemcitabine + Cisplatin (GC)", "MVAC (Methotrexate/Vinblastine/Doxorubicin/Cisplatin)"],
                "전립선암": ["Docetaxel (도세탁셀)", "Abiraterone + Prednisone (아비라테론+프레드니손)", "ADT(호르몬치료)"],
                "갑상선암": ["Lenvatinib", "Sorafenib"],
                "두경부암": ["EXTREME (Cetuximab + Platinum + 5-FU)", "TPF (Docetaxel/Cisplatin/5-FU)"]
            },
            "육종": {
                "골육종(MAP)": ["High-dose Methotrexate (고용량 메토트렉세이트)", "Doxorubicin", "Cisplatin"],
                "유잉육종(VAC/IE)": ["Vincristine", "Actinomycin D", "Cyclophosphamide", "Ifosfamide", "Etoposide"],
                "횡문근육종": ["Vincristine", "Actinomycin D", "Cyclophosphamide", "Ifosfamide", "Etoposide"]
            },
            "희귀암": {
                "신경모세포종": ["Cyclophosphamide", "Doxorubicin", "Vincristine", "Carboplatin", "Etoposide", "Ifosfamide"],
                "윌름스종양": ["Vincristine", "Dactinomycin(Actinomycin D)", "Doxorubicin"],
                "간모세포종": ["Cisplatin", "Doxorubicin", "Vincristine", "5-FU"],
                "GCT(BEP)": ["Bleomycin", "Etoposide", "Cisplatin"],
                "수모세포종": ["Cisplatin", "Vincristine", "Cyclophosphamide", "Etoposide"]
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
        
        # Regimen quick selector mirrored to '약물 선택' 탭
        _fallback_reg = {
            "MAP": ["High-dose Methotrexate (고용량 메토트렉세이트)","Doxorubicin (독소루비신)","Cisplatin (시스플라틴)"],
            "VAC/IE": ["Vincristine (빈크리스틴)","Actinomycin D (아크티노마이신 D)","Cyclophosphamide (사이클로포스파마이드)","Ifosfamide (이포스파미드)","Etoposide (에토포사이드)"],
            "POMP": ["6-Mercaptopurine (6-MP(머캅토퓨린))","Vincristine (빈크리스틴)","Methotrexate (메토트렉세이트(MTX))","Prednisone (프레드니손)"]
        }
        REG = getattr(drug_data, "REGIMENS", None) or _fallback_reg
        reg_keys_quick = ["(프리셋 없음)"] + list(REG.keys())
        st.selectbox("레짐 프리셋(Quick)", reg_keys_quick, key="chosen_reg_quick", help="약물 선택 탭과 연동됩니다.")
        # sync shared state
        st.session_state["chosen_reg_shared"] = st.session_state.get("chosen_reg_quick", "(프리셋 없음)")

    # ===== Basic panel =====
    with tabs[1]:
        st.markdown("#### 기본 수치")
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            WBC = st.number_input("WBC(×10³/µL)", min_value=0.0, step=0.1, format="%.1f", key="WBC_val")
        with c2:
            Hb  = st.number_input("Hb(g/dL)", min_value=0.0, step=0.1, format="%.1f", key="Hb_val")
        with c3:
            PLT = st.number_input("혈소판(×10³/µL)", min_value=0.0, step=1.0, format="%.0f", key="PLT_val")
        with c4:
            ANC = st.number_input("호중구 ANC(/µL)", min_value=0.0, step=10.0, format="%.0f", key="ANC_val")
        with c5:
            CRP = st.number_input("CRP(mg/dL)", min_value=0.0, step=0.1, format="%.2f", key="CRP_val")


        st.markdown("#### 기본 수치(확장)")
        # 전해질/간·신장/대사 핵심
        b1,b2,b3,b4 = st.columns(4)
        with b1:
            Ca = st.number_input("Ca(칼슘, mg/dL)", min_value=0.0, step=0.1, format="%.2f", key="Ca_val")
            P_ = st.number_input("P(인, mg/dL)", min_value=0.0, step=0.1, format="%.2f", key="P_val")
            Na = st.number_input("Na(나트륨, mmol/L)", min_value=0.0, step=0.1, format="%.1f", key="Na_val")
        with b2:
            K_ = st.number_input("K(칼륨, mmol/L)", min_value=0.0, step=0.1, format="%.1f", key="K_val")
            Alb = st.number_input("Alb(알부민, g/dL)", min_value=0.0, step=0.1, format="%.2f", key="Alb_val")
            Glu = st.number_input("Glu(혈당, mg/dL)", min_value=0.0, step=1.0, format="%.0f", key="Glu_val")
        with b3:
            TP = st.number_input("TP(총단백질, g/dL)", min_value=0.0, step=0.1, format="%.2f", key="TP_val")
            AST = st.number_input("AST(간수치, U/L)", min_value=0.0, step=1.0, format="%.0f", key="AST_val_basic")
            ALT = st.number_input("ALT(간세포수치, U/L)", min_value=0.0, step=1.0, format="%.0f", key="ALT_val_basic")
        with b4:
            LD = st.number_input("LD(유산탈수효소, U/L)", min_value=0.0, step=1.0, format="%.0f", key="LD_val")
            sCr = st.number_input("Cr(크레아티닌, mg/dL)", min_value=0.0, step=0.01, format="%.2f", key="Cr_val")
            UA = st.number_input("UA(요산, mg/dL)", min_value=0.0, step=0.1, format="%.2f", key="UA_val")
            Tb = st.number_input("Tb(총빌리루빈, mg/dL)", min_value=0.0, step=0.1, format="%.2f", key="Tb_val")

        # 간단 해석 캡션
        from .helpers import interpret_na, interpret_k, interpret_ca, interpret_phos, interpret_ast, interpret_alt, interpret_ldh as _int_ldh, interpret_tbili, interpret_ua
        hints = []
        hints += [interpret_na(Na), interpret_k(K_), interpret_ca(Ca), interpret_phos(P_)]
        hints += [interpret_ast(AST), interpret_alt(ALT)]
        hints += [(_int_ldh(LD) if LD else "")]
        hints += [interpret_tbili(Tb), interpret_ua(UA)]
        for h in hints:
            if h: st.caption("• " + h)

        # Oncology quick panel: 항암제 & 특수검사(소변) 바로 밑에 표시
        if group in ("혈액암","고형암","육종"):
            st.markdown("---")
            st.markdown("### 🧬 항암제(빠른 선택)")
            _fallback_reg = {
                "MAP": ["High-dose Methotrexate (고용량 메토트렉세이트)","Doxorubicin (독소루비신)","Cisplatin (시스플라틴)"],
                "VAC/IE": ["Vincristine (빈크리스틴)","Actinomycin D (아크티노마이신 D)","Cyclophosphamide (사이클로포스파마이드)","Ifosfamide (이포스파미드)","Etoposide (에토포사이드)"],
                "POMP": ["6-Mercaptopurine (6-MP(머캅토퓨린))","Vincristine (빈크리스틴)","Methotrexate (메토트렉세이트(MTX))","Prednisone (프레드니손)"]
            }
            REG = getattr(drug_data, "REGIMENS", None) or _fallback_reg
            reg_keys2 = ["(프리셋 없음)"] + list(REG.keys())
            chosen_reg2 = st.selectbox("레짐 프리셋(빠른 선택)", reg_keys2, key="chosen_reg_basic", help="약물 선택 탭과 연동")
            chemo_list2 = drug_data.CHEMO_BY_DIAGNOSIS.get(group, {}).get(diagnosis, [])
            if chosen_reg2 != "(프리셋 없음)":
                preset2 = REG.get(chosen_reg2, [])
                chemo_list2 = list(dict.fromkeys(list(preset2) + list(chemo_list2)))
                st.caption(f"프리셋 적용: {chosen_reg2} → {len(preset2)}개 항목 선반영")
            sel_chemo_basic = st.multiselect("항암제 선택(빠른)", options=chemo_list2, default=(REG.get(chosen_reg2, []) if chosen_reg2 != "(프리셋 없음)" else []), key="chemo_quick")

            st.markdown("### 🧪 특수검사(소변 간편)")
            u1,u2,u3 = st.columns(3)
            with u1:
                alb_unit_q = st.radio("요 알부민 단위", ["mg/L","mg/dL"], horizontal=True, index=0, key="alb_unit_quick")
            with u2:
                alb_q = st.number_input(f"요 알부민 ({st.session_state.get('alb_unit_quick','mg/L')})", min_value=0.0, step=1.0, format="%.1f", key="alb_quick")
            with u3:
                prot_q = st.number_input("요 단백 (mg/dL)", min_value=0.0, step=1.0, format="%.1f", key="prot_quick")
            cr_q = st.number_input("요 크레아티닌 (mg/dL)", min_value=0.0, step=0.1, format="%.1f", key="ucr_quick")
            alb_mg_L_q = (st.session_state.get("alb_quick") or 0.0) * (10.0 if st.session_state.get("alb_unit_quick") == "mg/dL" else 1.0)
            acr_q = compute_acr(alb_mg_L_q if alb_mg_L_q else None, cr_q if cr_q else None)
            upcr_q = compute_upcr(prot_q if prot_q else None, cr_q if cr_q else None)
            c1,c2 = st.columns(2)
            with c1:
                st.metric("ACR (mg/g)", f"{acr_q:.0f}" if acr_q else "-")
                st.caption(interpret_acr(acr_q))
            with c2:
                st.metric("UPCR (mg/g)", f"{upcr_q:.0f}" if upcr_q else "-")
                st.caption(interpret_upcr(upcr_q))
    
        if ANC:
            if ANC < 500:
                st.info("ANC 가이드: ⚠️ 500 미만 주의")
            elif ANC < 1000:
                st.info("ANC 가이드: ⚠️ 500~999 주의")
            else:
                st.info("ANC 가이드: ✅ 1000 이상 안정")

    # ===== Special/Urine panel =====
    with tabs[2]:
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


    # ===== Drugs panel =====
    with tabs[3]:
        st.markdown("#### 항암제/항생제 (한글 병기)")
        chemo_list = drug_data.CHEMO_BY_DIAGNOSIS.get(group, {}).get(diagnosis, [])
        # 레짐 프리셋 (drug_data.REGIMENS 없을 때도 안전하게 동작)
        _fallback_reg = {
            "MAP": [
                "High-dose Methotrexate (고용량 메토트렉세이트)",
                "Doxorubicin (독소루비신)",
                "Cisplatin (시스플라틴)"
            ],
            "VAC/IE": [
                "Vincristine (빈크리스틴)",
                "Actinomycin D (아크티노마이신 D)",
                "Cyclophosphamide (사이클로포스파마이드)",
                "Ifosfamide (이포스파미드)",
                "Etoposide (에토포사이드)"
            ],
            "POMP": [
                "6-Mercaptopurine (6-MP(머캅토퓨린))",
                "Vincristine (빈크리스틴)",
                "Methotrexate (메토트렉세이트(MTX))",
                "Prednisone (프레드니손)"
            ],
        }
        REG = getattr(drug_data, "REGIMENS", None) or _fallback_reg
        reg_keys = list(REG.keys())
        options_full = ["(프리셋 없음)"] + reg_keys
        default_shared = st.session_state.get("chosen_reg_shared", "(프리셋 없음)")
        try:
            idx_default = options_full.index(default_shared)
        except ValueError:
            idx_default = 0
        chosen_reg = st.selectbox(
            "레짐 프리셋", options_full, index=idx_default,
            key="chosen_reg_full", help="예: MAP, VAC/IE, POMP"
        )
        # keep shared in sync if user changes here
        st.session_state["chosen_reg_shared"] = chosen_reg
        if chosen_reg != "(프리셋 없음)":
            preset = REG.get(chosen_reg, [])
            base_set = set(chemo_list)
            chemo_list = list(dict.fromkeys(list(preset) + list(base_set)))
            st.caption(f"프리셋 적용: {chosen_reg} → {len(preset)}개 항목 선반영")
        sel_chemo = st.multiselect(
            "항암제 선택",
            options=chemo_list,
            default=(REG.get(chosen_reg, []) if chosen_reg != "(프리셋 없음)" else []),
            help="복수 선택 가능"
        )


        st.markdown("---")
        ABX = getattr(drug_data, "ANTIBIOTICS_BY_CLASS", {
            "Cephalosporins(세팔로스포린계)": ["Cefazolin(세파졸린)", "Ceftriaxone(세프트리악손)", "Ceftazidime(세프타지딤)", "Cefepime(세페핌)"],
            "Penicillins(페니실린계)": ["Amoxicillin(아목시실린)", "Piperacillin-tazobactam(피페라실린/타조박탐)"],
            "Carbapenems(카바페넴계)": ["Meropenem(메로페넴)", "Imipenem/cilastatin(이미페넴/실라스타틴)"],
            "Glycopeptides(글리코펩타이드)": ["Vancomycin(반코마이신)"],
        })
        ABX_TIPS = getattr(drug_data, "ABX_CLASS_TIPS", {
            "Cephalosporins(세팔로스포린계)": "교차 알레르기 가능성. 일부 약은 담즙정체성 간염 드물게 보고.",
            "Penicillins(페니실린계)": "알레르기/발진 주의. 신장기능 저하 시 용량 조절 고려.",
            "Carbapenems(카바페넴계)": "광범위. 경련 위험(고용량/신기능 저하) 주의.",
            "Glycopeptides(글리코펩타이드)": "반코마이신: 신독성/이독성, 혈중농도 모니터링.",
        })
        abx_classes = list(ABX.keys())
        abx_class = st.selectbox("항생제 계열", abx_classes)
        abx_options = ABX.get(abx_class, [])
        sel_abx = st.multiselect("항생제 선택", options=abx_options)
        tip = ABX_TIPS.get(abx_class, "")
        if tip:
            st.info(f"계열 안내: {tip}")

    # ===== Pediatrics =====
    with tabs[4]:
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
        ped_msgs = pediatric_guides({"ANC": ANC}, group_ped, diagnosis)
        for m in ped_msgs:
            st.markdown(f"- {m}")

    # ===== Result / Export =====
    with tabs[5]:
        st.markdown("### 결과 요약")
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
            "WBC": (st.session_state.get("WBC_inline") or WBC) if (st.session_state.get("WBC_inline") or WBC) else "",
            "Hb": Hb if Hb else "",
            "PLT": PLT if PLT else "",
            "ANC": ANC if ANC else "",
            "CRP": CRP if CRP else "",
            "Urine Alb (mg/L)": urine_albumin_mg_L if urine_albumin_mg_L else "",
            "Ferritin": Ferritin if "Ferritin" in locals() and Ferritin else "",
            "LDH": LDH if "LDH" in locals() and LDH else "",
            "Uric acid": UricAcid if "UricAcid" in locals() and UricAcid else "",
            "ESR": ESR if "ESR" in locals() and ESR else "",
            "Retic(%)": Retic if "Retic" in locals() and Retic else "",
            "β2-microglobulin": B2M if "B2M" in locals() and B2M else "",
            "BNP": BNP if "BNP" in locals() and BNP else "",
            "Coombs": Coombs if "Coombs" in locals() and Coombs and Coombs!="선택 안 함" else "",
            "AST": (st.session_state.get("AST_inline") or (AST if "AST" in locals() else None)) or "",
            "ALT": (st.session_state.get("ALT_inline") or (ALT if "ALT" in locals() else None)) or "",
            "ALP": ALP if "ALP" in locals() and ALP else "",
            "GGT": GGT if "GGT" in locals() and GGT else "",
            "Total bilirubin": TBILI if "TBILI" in locals() and TBILI else "",
            "Na": (st.session_state.get("Na_inline") or (Na if "Na" in locals() else None)) or "",
            "K": (st.session_state.get("K_inline") or (K if "K" in locals() else None)) or "",
            "Ca": (st.session_state.get("Ca_inline") or (Ca if "Ca" in locals() else None)) or "",
            "Mg": Mg if "Mg" in locals() and Mg else "",
            "Phos": Phos if "Phos" in locals() and Phos else "",
            "INR": INR if "INR" in locals() and INR else "",
            "aPTT": aPTT if "aPTT" in locals() and aPTT else "",
            "Fibrinogen": Fibrinogen if "Fibrinogen" in locals() and Fibrinogen else "",
            "D-dimer": Ddimer if "Ddimer" in locals() and Ddimer else "",
            "Triglycerides": TG if "TG" in locals() and TG else "",
            "Lactate": Lactate if "Lactate" in locals() and Lactate else "",
            "Urine Prot (mg/dL)": urine_protein_mg_dL if urine_protein_mg_dL else "",
            "Ca": (st.session_state.get("Ca_inline") or (Ca if "Ca" in locals() else None)) or "",
            "P": P_ if "P_" in locals() and P_ else "",
            "Na": (st.session_state.get("Na_inline") or (Na if "Na" in locals() else None)) or "",
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
