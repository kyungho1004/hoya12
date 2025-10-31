# app_report_special_patch.py — Report bridge for special tests
# 사용: 보고서 탭/섹션에서 render_special_report_section() 한 줄 호출
from __future__ import annotations
import streamlit as st

def render_special_report_section():
    st.markdown("## 특수검사 해석(각주 포함)")
    lines = st.session_state.get("special_interpretations", [])
    if not isinstance(lines, list):
        lines = [str(lines)] if lines else []
    if not lines:
        st.info("특수검사 입력은 있었지만 해석 문장이 아직 없습니다.")
    else:
        for s in lines:
            st.write(f"- {s}")
    with st.expander("🔎 디버그 보기"):
        st.write({"special_interpretations": lines})
