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

        # 🔸 면역·보체 검사
        st.markdown("### 🔸 면역 · 보체 검사")
        col2 = st.columns(2)
        with col2[0]:
            c3 = st.text_input("C3 (mg/dL)")
        with col2[1]:
            c4 = st.text_input("C4 (mg/dL)")

        # 🧬 지질 검사
        st.markdown("### 🧬 지질 검사")
        col3 = st.columns(2)
        with col3[0]:
            tg = st.text_input("TG (mg/dL)")
            hdl = st.text_input("HDL (mg/dL)")
        with col3[1]:
            ldl = st.text_input("LDL (mg/dL)")
            tc  = st.text_input("총콜레스테롤 (mg/dL)")

        # 🫀 신장/심장 기능
        st.markdown("### 🫀 신장 / 심장 기능")
        col4 = st.columns(2)
        with col4[0]:
            bun = st.text_input("BUN (mg/dL)")
            bnp = st.text_input("BNP (pg/mL)")
        with col4[1]:
            ckmb = st.text_input("CK-MB (ng/mL)")
            trop = st.text_input("Troponin-I (ng/mL)")
            myo  = st.text_input("Myoglobin (ng/mL)")

        # 🔍 해석 버튼 및 로직
        if st.button("🔎 특수검사 해석"):
            if alb!="없음": lines.append("알부민뇨 " + ("+"*QUAL.index(alb)) + " → 🟡~🔴 신장 이상 가능")
            if hem!="없음": lines.append("혈뇨 " + ("+"*QUAL.index(hem)) + " → 🟡 요로 염증/결석 등")
            if sug!="없음": lines.append("요당 " + ("+"*QUAL.index(sug)) + " → 🟡 고혈당/당뇨 의심")
            if ket!="없음": lines.append("케톤뇨 " + ("+"*QUAL.index(ket)) + " → 🟡 탈수/케톤증 가능")

            C3 = clean_num(c3); C4 = clean_num(c4)
            if C3 is not None: lines.append("C3 낮음 → 🟡 면역계 이상 가능" if C3 < 90 else "C3 정상/상승")
            if C4 is not None: lines.append("C4 낮음 → 🟡 면역계 이상 가능" if C4 < 10 else "C4 정상/상승")

            TG = clean_num(tg); HDL = clean_num(hdl); LDL = clean_num(ldl); TC = clean_num(tc)
            if TG is not None:
                lines.append("🔴 TG≥200: 고중성지방혈증 가능" if TG >= 200 else ("🟡 TG 150~199 경계" if TG >= 150 else "🟢 TG 양호"))
            if HDL is not None:
                lines.append("🟠 HDL<40: 심혈관 위험" if HDL < 40 else "🟢 HDL 양호")
            if LDL is not None:
                lines.append("🔴 LDL≥160: 고LDL콜" if LDL >= 160 else ("🟡 LDL 130~159 경계" if LDL >= 130 else "🟢 LDL 양호"))
            if TC is not None:
                lines.append("🔴 총콜≥240: 고지혈증" if TC >= 240 else ("🟡 총콜 200~239 경계" if TC >= 200 else "🟢 총콜 양호"))

            BUN = clean_num(bun)
            if BUN is not None:
                lines.append("🔴 BUN≥25: 탈수/신장기능 저하 의심" if BUN >= 25 else "🟢 BUN 정상")
            BNP = clean_num(bnp)
            if BNP is not None:
                lines.append("🔴 BNP≥100: 심부전 의심" if BNP >= 100 else "🟢 BNP 정상")

            CKMB = clean_num(ckmb)
            TROP = clean_num(trop)
            MYO = clean_num(myo)

            if CKMB is not None:
                lines.append("🔴 CK-MB>5: 심장 손상 가능성" if CKMB > 5 else "🟢 CK-MB 정상")
            if TROP is not None:
                lines.append("🔴 Troponin-I>0.04: 심근경색 의심" if TROP > 0.04 else "🟢 Troponin-I 정상")
            if MYO is not None:
                lines.append("🟡 Myoglobin>85: 근육/심장 손상 가능성" if MYO > 85 else "🟢 Myoglobin 정상")

            if not lines:
                lines.append("입력값이 없어 해석할 내용이 없습니다.")
                
    return lines
