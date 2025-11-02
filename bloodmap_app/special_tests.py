
# -*- coding: utf-8 -*-
"""
special_tests.py — 안전 템플릿
- 최상단에서 Streamlit 위젯 생성 없음 (임포트 안전)
- 엔트리: special_tests_ui()
- 위젯 key 충돌 방지용 prefix 사용
"""

from __future__ import annotations
from typing import List

def special_tests_ui() -> List[str]:
    try:
        import streamlit as st
    except Exception:
        # Streamlit 아닌 환경에서 임포트되는 경우
        return ["streamlit 환경이 아님"]
    logs: List[str] = []
    st.info("✅ 특수검사 템플릿 UI가 정상 로드되었습니다.")
    with st.form("stx_special_tests_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            crp = st.number_input("CRP", min_value=0.0, step=0.1, format="%.1f", key="stx_crp")
        with c2:
            esr = st.number_input("ESR", min_value=0.0, step=1.0, format="%.0f", key="stx_esr")
        with c3:
            procalcitonin = st.number_input("PCT", min_value=0.0, step=0.01, format="%.2f", key="stx_pct")
        submitted = st.form_submit_button("해석하기", use_container_width=True)
        if submitted:
            st.success("임시 해석 예시: 감염 지표 단순 확인(참고용)")
            logs.append(f"CRP={crp}, ESR={esr}, PCT={procalcitonin}")
            if crp >= 10 or procalcitonin >= 0.5:
                st.warning("🚨 감염 가능성 ↑ — 열/증상 함께 확인하고 의료진과 상의하세요.")
            else:
                st.info("🟢 급성 염증 반응 수치는 높지 않습니다. (참고용)")
    st.caption("이 해석은 참고용이며, 정확한 판단은 의료진의 진료에 따릅니다.")
    return logs
