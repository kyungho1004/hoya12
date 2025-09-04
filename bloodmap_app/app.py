
# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from typing import Dict, Any
from .utils import get_user_key, save_session, load_session
from .drug_data import ANTINEOPLASTICS, ANTIBIOTICS, SARCOMA_DIAGNOSES

APP_TITLE = "🩸 피수치 가이드 / BloodMap — v3.14 (특수검사 정리·연구자 모드)"
APP_CAPTION = "본 도구는 보호자의 이해를 돕기 위한 참고 자료이며 의료적 판단은 담당 의료진의 권한입니다."
MOBILE_HINT = "📱 모바일 최적화 완료 — 글자깨짐 시 새로고침 또는 브라우저 글꼴 변경을 시도하세요."

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
                "special_tests": st.session_state.get("special_tests_data", {}),
                "special_tests_adv": st.session_state.get("special_tests_adv_data", {}),
            }
            path = save_session(user_key, payload)
            st.success(f"세션 저장 완료: {path}")
        if st.button("마지막 저장 불러오기"):
            loaded = load_session(user_key)
            if loaded:
                st.json(loaded, expanded=False)
                # 세션 복원
                st.session_state["special_tests_data"] = loaded.get("special_tests", {})
                st.session_state["special_tests_adv_data"] = loaded.get("special_tests_adv", {})
            else:
                st.warning("저장된 기록이 없습니다.")

    st.markdown("### 🧾 특수검사 (한/영 병기)")
    st.caption("일반 사용자 화면에서 5~9 카테고리는 숨김. 연구자 모드에서만 표시.")
    st.divider()

    # 1) 소변/요 검사 — 기본 공개
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
        _ = 0

    # 2) 면역/자가면역 — 공개 유지
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

    # 3) 응고/혈전 — 공개 유지
    with st.expander("3) 응고 / 혈전", expanded=False):
        dd = bool_01("D-다이머 (D-dimer)", key="coag_ddimer")
        fdp = bool_01("피브린분해산물 (FDP)", key="coag_fdp")
        ptt = bool_01("PT/aPTT (프로트롬빈시간/활성부분트롬보플라스틴시간)", key="coag_pt_aptt")
        pcs = bool_01("단백 C/S (Protein C/S)", key="coag_protein_cs")
        at3 = bool_01("안티트롬빈 III (AT-III)", key="coag_at3")
        la = bool_01("루푸스 항응고인자 (Lupus anticoagulant)", key="coag_lupus_ac")

    # 4) 신장 기능 — 공개 유지
    with st.expander("4) 신장 기능", expanded=False):
        prot_q = bool_01("단백뇨 정량 (Proteinuria, quantitative)", key="renal_prot_quant")
        urine_elec = bool_01("요 전해질 Na/K/Cl/Ca/Ph (Urine Na/K/Cl/Ca/Ph)", key="renal_urine_electrolytes")
        b2mg = bool_01("β2-마이크로글로불린 (B2-MG)", key="renal_b2mg")
        cystatin = bool_01("시스타틴 C (Cystatin-C)", key="renal_cystatin_c")

    # 5~9) 고급 패널 — 연구자 모드에서만 표시
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

    # 결과 요약(일반: 고급 비노출)
    basic = {
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
    st.session_state["special_tests_data"] = basic
    st.session_state["special_tests_adv_data"] = adv

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("#### ✅ 특수검사 입력 요약 (일반용: 1~4만 표시)")
    df = pd.DataFrame([basic])
    st.dataframe(df, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.caption("제작: Hoya/GPT · 자문: Hoya/GPT — 무단 배포 금지 · 교육용 참고자료")

if __name__ == "__main__":
    main()
