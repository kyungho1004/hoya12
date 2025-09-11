# -*- coding: utf-8 -*-
import streamlit as st
from core_utils import clean_num

QUAL = ["없음", "+", "++", "+++"]

def special_tests_ui():
    lines = []
    with st.expander("🧪 특수검사 (토글)", expanded=False):

        # 🔹 소변 검사
        st.markdown("### 🔹 소변 검사")
        col1 = st.columns(2)
        with col1[0]:
            alb = st.selectbox("알부민뇨", QUAL)
            hem = st.selectbox("혈뇨", QUAL)
        with col1[1]:
            sug = st.selectbox("요당", QUAL)
            ket = st.selectbox("케톤뇨", QUAL)

        # 🔸 면역 · 보체 검사
        st.markdown("### 🔸 면역 · 보체 검사")
        col2 = st.columns(2)
        with col2[0]:
            c3 = st.text_input("C3 (mg/dL)")
            c4 = st.text_input("C4 (mg/dL)")
        with col2[1]:
            crp_hs = st.text_input("hs-CRP (mg/L)")
            ana = st.text_input("ANA (titer)")

        # 🧠 기타 특수
        st.markdown("### 🧠 기타 특수")
        col3 = st.columns(2)
        with col3[0]:
            tg = st.text_input("TG (mg/dL)")
            hdl = st.text_input("HDL (mg/dL)")
            ldl = st.text_input("LDL (mg/dL)")
        with col3[1]:
            lpa = st.text_input("Lp(a) (mg/dL)")
            homa = st.text_input("HOMA-IR")
            ferr = st.text_input("Ferritin (ng/mL)")

        # ❤️ 심장 표지자
        st.markdown("### ❤️ 심장 표지자")
        col4 = st.columns(2)
        with col4[0]:
            bnp = st.text_input("BNP (pg/mL)")
        with col4[1]:
            ckmb = st.text_input("CK-MB (ng/mL)")
            trop = st.text_input("Troponin-I (ng/mL)")
            myo  = st.text_input("Myoglobin (ng/mL)")

        # 🔍 해석 버튼 및 로직
        if st.button("🔎 특수검사 해석", key="btn_special_tests"):
            if alb!="없음": lines.append("알부민뇨 " + ("+"*QUAL.index(alb)) + " → 🟡~🔴 신장 이상 가능")
            if hem!="없음": lines.append("혈뇨 " + ("+"*QUAL.index(hem)) + " → 🟡 요로 염증/결석 등")
            if sug!="없음": lines.append("요당 " + ("+"*QUAL.index(sug)) + " → 🟡 고혈당/당뇨 의심")
            if ket!="없음": lines.append("케톤뇨 " + ("+"*QUAL.index(ket)) + " → 🟡 탈수/케톤증 가능")

            C3 = clean_num(c3); C4 = clean_num(c4)
            if C3 is not None: lines.append("C3 낮음 → 🟡 면역계 이상 가능" if C3 < 90 else "C3 정상/상승")
            if C4 is not None: lines.append("C4 낮음 → 🟡 면역계 이상 가능" if C4 < 10 else "C4 정상/상승")

            TG = clean_num(tg)
            if TG is not None and TG >= 200: lines.append("TG 200 이상 → 🔴 고지혈증 가능성")
            HDL = clean_num(hdl)
            if HDL is not None and HDL < 40: lines.append("HDL 낮음 → 🟡 심혈관 위험")
            LDL = clean_num(ldl)
            if LDL is not None and LDL >= 160: lines.append("LDL 높음 → 🔴 고지혈증 가능성")

            BNP = clean_num(bnp)
            if BNP is not None and BNP > 100: lines.append("BNP 상승 → 🟡 심부전 가능성")
            CKMB = clean_num(ckmb)
            if CKMB is not None and CKMB > 5: lines.append("CK-MB 상승 → 🟡 심근 손상 의심")
            TRO = clean_num(trop)
            if TRO is not None and TRO > 0.05: lines.append("Troponin-I 상승 → 🔴 급성관상동맥증후군 의심")
            MYO = clean_num(myo)
            if MYO is not None and MYO > 85: lines.append("Myoglobin 상승 → 🟡 근육 손상 가능")

            # 출력
            st.markdown("#### 🧾 특수검사 해석 결과")
            for L in lines: st.write("- " + L)

    return lines
