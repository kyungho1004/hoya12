\
# special_tests.py — SAFE (no re-patch, unique keys, minimal summary)
import streamlit as st
from uuid import uuid4

def _uniq(base: str) -> str:
    sid = st.session_state.get("_sp_uid", None)
    if not sid:
        sid = st.session_state["_sp_uid"] = uuid4().hex[:6]
    return f"{base}.{sid}"

def special_tests_ui():
    st.info("특수검사 모듈 (safe) — 토글을 열어 값을 입력하세요.")
    lines = []
    with st.expander("🔴 소변 검사 보기", expanded=True):
        alb = st.selectbox("Albumin (알부민뇨)", ["없음","+","++","+++"], key=_uniq("alb"))
        rbc = st.text_input("RBC/HPF", key=_uniq("rbc"))
        wbc = st.text_input("WBC/HPF", key=_uniq("wbc"))
        if alb != "없음" or rbc or wbc:
            lines.append(f"소변 요약: Alb {alb}, RBC/HPF {rbc or '-'}, WBC/HPF {wbc or '-'}")
    with st.expander("🟡 대변 검사 보기", expanded=False):
        occ = st.selectbox("잠혈(FOBT)", ["음성","양성"], key=_uniq("fobt"))
        if occ == "양성":
            lines.append("대변 요약: FOBT 양성")
    if not lines:
        lines = ["특수검사 항목을 펼치지 않아 요약이 없습니다. 필요 시 토글을 열어 값을 입력하세요."]
    st.session_state["special_interpretations"] = lines
    return lines
