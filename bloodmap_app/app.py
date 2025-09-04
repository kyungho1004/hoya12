
# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import math
from typing import Dict, Any

from bloodmap_app.storage import get_user_key, save_session, load_session
from bloodmap_app.drug_data import ANTINEOPLASTICS, ANTIBIOTICS, SARCOMA_DIAGNOSES

APP_TITLE = "🩸 피수치 가이드 / BloodMap — v3.15 (소아 패널 복구)"
APP_CAPTION = "본 도구는 정보 제공용입니다. 최종 의료 판단은 담당 의료진의 권한입니다."
MOBILE_HINT = "📱 모바일 최적화 — 입력/요약 가독성 향상."

def _inject_css():
    try:
        from pathlib import Path
        css_path = Path(__file__).with_name("style.css")
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
    except Exception:
        pass

def bool_01(label: str, key: str, default: int = 0) -> int:
    val = st.selectbox(label, options=[0,1], index=default, key=key, help="0=음성/정상, 1=양성/이상 또는 시행")
    return int(val)

def num(label: str, key: str, step: float = 0.1, format_str: str = None, placeholder: str = ""):
    return st.number_input(label, key=key, step=step, format=format_str if format_str else None, placeholder=placeholder)

def mosteller_bsa(cm: float, kg: float) -> float:
    try:
        if cm and kg and cm>0 and kg>0:
            return math.sqrt((cm * kg) / 3600.0)
        return 0.0
    except Exception:
        return 0.0

def main():
    st.set_page_config(page_title="피수치 가이드 / BloodMap", layout="centered")
    _inject_css()
    st.title(APP_TITLE)
    st.caption(APP_CAPTION)
    st.info(MOBILE_HINT)

    with st.sidebar:
        st.subheader("👤 사용자 식별")
        nickname = st.text_input("별명", placeholder="예: 호야", key="nickname")
        pin4 = st.text_input("핀 4자리", placeholder="예: 0000", max_chars=4, key="pin4")
        user_key = get_user_key(nickname, pin4)
        st.write(f"ID: **{user_key}** (중복 방지)")

        st.subheader("🧪 카테고리")
        major = st.selectbox("진료군", ["혈액종양", "고형암", "육종 (Sarcoma)"], index=0, key="major_cat")
        sarcoma_dx = None
        if major == "육종 (Sarcoma)":
            sarcoma_dx = st.selectbox("육종 진단명", SARCOMA_DIAGNOSES, key="sarcoma_dx")

        st.subheader("👶 소아 모드")
        pediatric_mode = st.toggle("소아 패널 사용", value=True, help="체중/신장 기반 계산, 용량 보조 등")

        st.subheader("💊 약물 기록")
        antineo = st.multiselect("항암제 (한글 표기)", ANTINEOPLASTICS, key="antineo")
        abx = st.multiselect("항생제 (한글 표기)", ANTIBIOTICS, key="abx")

        st.subheader("🔒 고급 설정")
        researcher_mode = st.toggle("연구자 모드(고급 패널 표시)", value=False, help="일반 사용자에게는 숨김")

        st.subheader("💾 저장/불러오기")
        if st.button("이 세션 저장"):
            payload = {
                "user_key": user_key,
                "nickname": nickname,
                "pin4": pin4,
                "major": major,
                "sarcoma_dx": sarcoma_dx,
                "antineoplastics": antineo,
                "antibiotics": abx,
                "core_labs": st.session_state.get("core_labs", {}),
                "peds": st.session_state.get("peds", {}),
                "special_tests": st.session_state.get("special_tests_data", {}),
                "special_tests_adv": st.session_state.get("special_tests_adv_data", {}),
            }
            path = save_session(user_key, payload)
            st.success(f"세션 저장 완료: {path}")
        if st.button("마지막 저장 불러오기"):
            loaded = load_session(user_key)
            if loaded:
                st.json(loaded, expanded=False)
                st.session_state["core_labs"] = loaded.get("core_labs", {})
                st.session_state["peds"] = loaded.get("peds", {})
                st.session_state["special_tests_data"] = loaded.get("special_tests", {})
                st.session_state["special_tests_adv_data"] = loaded.get("special_tests_adv", {})
            else:
                st.warning("저장된 기록이 없습니다.")

    # ------------------------
    # 0) 기본 피수치
    # ------------------------
    st.markdown("### 0️⃣ 기본 피수치")
    c1, c2 = st.columns(2)
    with c1:
        WBC = num("WBC (x10³/µL)", "lab_wbc", step=0.1, format_str="%.1f")
        Hb = num("Hb (g/dL)", "lab_hb", step=0.1, format_str="%.1f")
        PLT = num("혈소판 PLT (x10³/µL)", "lab_plt", step=1.0, format_str="%.0f")
        ANC = num("호중구 ANC (/µL)", "lab_anc", step=10.0, format_str="%.0f")
        Ca = num("칼슘 Ca (mg/dL)", "lab_ca", step=0.1, format_str="%.1f")
        P = num("인 P (mg/dL)", "lab_p", step=0.1, format_str="%.1f")
        Na = num("나트륨 Na (mmol/L)", "lab_na", step=1.0, format_str="%.0f")
        K = num("칼륨 K (mmol/L)", "lab_k", step=0.1, format_str="%.1f")
        Albumin = num("알부민 (g/dL)", "lab_alb", step=0.1, format_str="%.1f")
        Glu = num("혈당 Glucose (mg/dL)", "lab_glu", step=1.0, format_str="%.0f")
    with c2:
        TP = num("총단백 Total Protein (g/dL)", "lab_tp", step=0.1, format_str="%.1f")
        AST = num("AST (U/L)", "lab_ast", step=1.0, format_str="%.0f")
        ALT = num("ALT (U/L)", "lab_alt", step=1.0, format_str="%.0f")
        LDH = num("LDH (U/L)", "lab_ldh", step=1.0, format_str="%.0f")
        CRP = num("CRP (mg/dL)", "lab_crp", step=0.1, format_str="%.2f")
        Cr = num("Creatinine Cr (mg/dL)", "lab_cr", step=0.01, format_str="%.2f")
        UA = num("Uric Acid UA (mg/dL)", "lab_ua", step=0.1, format_str="%.1f")
        TB = num("Total Bilirubin TB (mg/dL)", "lab_tb", step=0.1, format_str="%.1f")
        BUN = num("BUN (mg/dL)", "lab_bun", step=0.1, format_str="%.1f")
        BNP = num("BNP (pg/mL) – 선택", "lab_bnp", step=1.0, format_str="%.0f")

    core = {k:v for k,v in [
        ("WBC", WBC), ("Hb", Hb), ("혈소판(PLT)", PLT), ("ANC", ANC),
        ("Ca", Ca), ("P", P), ("Na", Na), ("K", K),
        ("Albumin", Albumin), ("Glucose", Glu), ("Total Protein", TP),
        ("AST", AST), ("ALT", ALT), ("LDH", LDH), ("CRP", CRP),
        ("Creatinine(Cr)", Cr), ("Uric Acid(UA)", UA), ("Total Bilirubin(TB)", TB),
        ("BUN", BUN), ("BNP", BNP),
    ] if v not in (None, "")}
    st.session_state["core_labs"] = core

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("#### ✅ 기본 피수치 요약")
    st.dataframe(pd.DataFrame([core]) if core else pd.DataFrame([{}]), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ------------------------
    # Peds Panel
    # ------------------------
    if pediatric_mode:
        st.divider()
        st.markdown("### 👶 소아 패널")
        colp1, colp2, colp3 = st.columns(3)
        with colp1:
            age_y = num("나이(년)", "p_age_y", step=1.0, format_str="%.0f")
        with colp2:
            age_m = num("나이(개월)", "p_age_m", step=1.0, format_str="%.0f")
        with colp3:
            sex = st.selectbox("성별", ["미상","남","여"], key="p_sex")

        cpa, cpb = st.columns(2)
        with cpa:
            wt = num("체중 (kg)", "p_wt", step=0.1, format_str="%.2f")
            mgkg = num("용량 (mg/kg)", "p_mgkg", step=0.1, format_str="%.2f", placeholder="예: 10")
        with cpb:
            ht = num("신장 (cm)", "p_ht", step=0.1, format_str="%.1f")
            mgm2 = num("용량 (mg/m²)", "p_mgm2", step=0.1, format_str="%.2f", placeholder="예: 500")

        bsa = mosteller_bsa(ht or 0, wt or 0)
        bmi = (wt / ((ht/100)**2)) if wt and ht else 0
        dose_kg = (wt * mgkg) if wt and mgkg else 0
        dose_m2 = (bsa * mgm2) if bsa and mgm2 else 0

        colr1, colr2 = st.columns(2)
        with colr1:
            st.metric("BSA (Mosteller)", f"{bsa:.2f} m²")
            st.metric("BMI", f"{bmi:.1f} kg/m²")
        with colr2:
            st.metric("계산용량 (mg/kg 기준)", f"{dose_kg:.1f} mg")
            st.metric("계산용량 (mg/m² 기준)", f"{dose_m2:.1f} mg")

        # 간단 ANC 위험 레이블 (정보 제공용)
        anc_val = ANC or 0
        risk = "정보없음"
        if anc_val:
            if anc_val < 500: risk = "고위험(ANC<500)"
            elif anc_val < 1000: risk = "중간위험(500≤ANC<1000)"
            else: risk = "일반위험(ANC≥1000)"
        st.info(f"🛡️ 소아 감염 위험(참고): {risk}  · 의료진 판단이 우선입니다.")

        st.session_state["peds"] = {
            "age_years": age_y, "age_months": age_m, "sex": sex,
            "weight_kg": wt, "height_cm": ht, "BSA_m2": round(bsa,2),
            "BMI": round(bmi,1) if bmi else 0,
            "dose_mg_per_kg": mgkg, "dose_mg_per_m2": mgm2,
            "calc_dose_by_kg_mg": round(dose_kg,1) if dose_kg else 0,
            "calc_dose_by_m2_mg": round(dose_m2,1) if dose_m2 else 0,
            "anc_risk_tag": risk,
        }

    st.divider()

    # ------------------------
    # 1)~4) 특수검사 (일반 공개)
    # ------------------------
    st.markdown("### 🧾 특수검사 (일반 공개 + 연구자 모드)")
    st.caption("정성(0/1) 저장 — 기존 보고서/그래프 로직과 충돌 없음")

    # 1) 소변/요 검사
    st.markdown("#### 1) 소변/요 검사")
    col1, col2 = st.columns(2)
    with col1:
        hema = bool_01("혈뇨 (Hematuria) — 정성(0/1)", key="sp_hema")
        prot = bool_01("단백뇨 (Proteinuria) — 정성(0/1)", key="sp_prot")
        gly = bool_01("당뇨 (Glycosuria) — 정성(0/1)", key="sp_gly")
        ket = bool_01("케톤뇨 (Ketonuria) — 정성(0/1)", key="sp_ket")
    with col2:
        microalb = bool_01("미세알부민뇨 (Microalbuminuria) — 정성(0/1)", key="sp_malb")
        nitrite = bool_01("니트라이트 (Nitrite) — 정성(0/1)", key="sp_nit")

    # 2) 면역/자가면역
    with st.expander("2) 면역 / 자가면역", expanded=False):
        c3 = bool_01("보체 C3 (Complement C3)", key="immun_c3")
        c4 = bool_01("보체 C4 (Complement C4)", key="immun_c4")
        ana = bool_01("항핵항체 (ANA)", key="immun_ana")
        rf = bool_01("류마티스인자 (RF)", key="immun_rf")
        anca = bool_01("항호중구세포질항체 (ANCA)", key="immun_anca")
        dsdna = bool_01("이중가닥 DNA 항체 (anti-dsDNA)", key="immun_dsdna")
        ssa_ssb = bool_01("항Ro/La 항체 (SSA/SSB)", key="immun_ssa_ssb")
        sm = bool_01("항 Sm 항체 (anti-Sm)", key="immun_sm")
        rnp = bool_01("항 RNP 항체 (anti-RNP)", key="immun_rnp")

    # 3) 응고/혈전
    with st.expander("3) 응고 / 혈전", expanded=False):
        dd = bool_01("D-다이머 (D-dimer)", key="coag_ddimer")
        fdp = bool_01("피브린분해산물 (FDP)", key="coag_fdp")
        ptt = bool_01("PT/aPTT (프로트롬빈시간/활성부분트롬보플라스틴시간)", key="coag_pt_aptt")
        pcs = bool_01("단백 C/S (Protein C/S)", key="coag_protein_cs")
        at3 = bool_01("안티트롬빈 III (AT-III)", key="coag_at3")
        la = bool_01("루푸스 항응고인자 (Lupus anticoagulant)", key="coag_lupus_ac")

    # 4) 신장 기능
    with st.expander("4) 신장 기능", expanded=False):
        prot_q = bool_01("단백뇨 정량 (Proteinuria, quantitative)", key="renal_prot_quant")
        urine_elec = bool_01("요 전해질 Na/K/Cl/Ca/Ph (Urine Na/K/Cl/Ca/Ph)", key="renal_urine_electrolytes")
        b2mg = bool_01("β2-마이크로글로불린 (B2-MG)", key="renal_b2mg")
        cystatin = bool_01("시스타틴 C (Cystatin-C)", key="renal_cystatin_c")

    # 일반 요약 저장
    basic_tests = {
        "혈뇨(Hematuria)": hema,
        "단백뇨(Proteinuria)": prot,
        "당뇨(Glycosuria)": gly,
        "케톤뇨(Ketonuria)": ket,
        "미세알부민뇨(Microalbuminuria)": microalb,
        "니트라이트(Nitrite)": nitrite,
        "C3": locals().get("c3", 0), "C4": locals().get("c4", 0), "ANA": locals().get("ana", 0),
        "RF": locals().get("rf", 0), "ANCA": locals().get("anca", 0),
        "anti-dsDNA": locals().get("dsdna", 0), "SSA/SSB": locals().get("ssa_ssb", 0),
        "anti-Sm": locals().get("sm", 0), "anti-RNP": locals().get("rnp", 0),
        "단백뇨 정량": locals().get("prot_q", 0), "Urine Na/K/Cl/Ca/Ph": locals().get("urine_elec", 0),
        "B2-MG": locals().get("b2mg", 0), "Cystatin-C": locals().get("cystatin", 0),
    }
    st.session_state["special_tests_data"] = basic_tests

    # 5~9) 연구자 모드
    adv = {}
    if researcher_mode:
        with st.expander("5) 종양표지자 (연구자)", expanded=False):
            adv["AFP"] = bool_01("AFP (알파태아단백)", key="tm_afp")
            adv["β-hCG"] = bool_01("β-hCG (베타 hCG)", key="tm_bhcg")
            adv["CEA"] = bool_01("CEA", key="tm_cea")
            adv["CA 125"] = bool_01("CA 125", key="tm_ca125")
            adv["CA 19-9"] = bool_01("CA 19-9", key="tm_ca199")
            adv["PSA"] = bool_01("PSA", key="tm_psa")
            adv["NSE"] = bool_01("NSE (신경특이 에놀라제)", key="tm_nse")
            adv["Ferritin"] = bool_01("Ferritin (페리틴)", key="tm_ferritin")
        with st.expander("6) 염증/활성도 (연구자)", expanded=False):
            adv["IL-6"] = bool_01("IL-6", key="infl_il6")
            adv["Procalcitonin"] = bool_01("Procalcitonin (프로칼시토닌)", key="infl_pct")
            adv["ESR"] = bool_01("ESR (적혈구침강속도)", key="infl_esr")
            adv["hs-CRP"] = bool_01("hs-CRP (고감도 CRP)", key="infl_hscrp")
            adv["sIL-2R"] = bool_01("sIL-2R (용해성 IL-2 receptor)", key="infl_sil2r")
        with st.expander("7) 유전/세포/조직학 (연구자)", expanded=False):
            adv["Cytogenetics"] = bool_01("골수 세포유전학 (Bone marrow cytogenetics)", key="gen_cytogenetics")
            adv["FISH"] = bool_01("FISH (형광제자리부합법)", key="gen_fish")
            adv["PCR"] = bool_01("PCR", key="gen_pcr")
            adv["HLA typing"] = bool_01("HLA 타이핑 (HLA typing)", key="gen_hla")
            adv["MRD"] = bool_01("MRD (미세잔존질환)", key="gen_mrd")
            adv["NGS"] = bool_01("NGS (차세대염기서열분석)", key="gen_ngs")
        with st.expander("8) 약물농도 / 독성 (연구자)", expanded=False):
            adv["MTX level"] = bool_01("MTX 농도 (MTX level)", key="drug_mtx_level")
            adv["Cyclosporine"] = bool_01("시클로스포린 농도 (Cyclosporine)", key="drug_cyclosporine")
            adv["Tacrolimus"] = bool_01("타크로리무스 농도 (Tacrolimus)", key="drug_tacrolimus")
            adv["Drug screen"] = bool_01("약물 스크리닝 (Drug screen)", key="drug_screen")
        with st.expander("9) 기타 (연구자)", expanded=False):
            adv["Reticulocyte"] = bool_01("망상적혈구 (Reticulocyte)", key="misc_reticulocyte")
            adv["Vitamin D/B12/Folate"] = bool_01("비타민 D/B12/엽산 (Vitamin D/B12/Folate)", key="misc_vitamins")
            adv["Homocysteine"] = bool_01("호모시스테인 (Homocysteine)", key="misc_homocysteine")
            adv["Free light chain"] = bool_01("유리 경쇄 (Free light chain)", key="misc_flc")
            adv["Coombs"] = bool_01("쿰즈 검사 (Coombs)", key="misc_coombs")
    st.session_state["special_tests_adv_data"] = adv

    # 요약 테이블
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("#### ✅ 특수검사 입력 요약 (일반용 1~4)")
    st.dataframe(pd.DataFrame([basic_tests]), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.caption("제작: Hoya/GPT · 자문: Hoya/GPT — 무단 배포 금지 · 교육용 참고자료")

if __name__ == "__main__":
    main()
