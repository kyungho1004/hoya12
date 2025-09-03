# -*- coding: utf-8 -*-
import streamlit as st
from ..utils.inputs import num_input_generic

def render_schedule(nickname_key: str):
    st.markdown("### 🗓️ 스케줄(항암/검사/외래)")
    if not nickname_key:
        st.info("별명과 PIN을 먼저 입력하면 스케줄을 저장할 수 있어요.")
        return
    ss = st.session_state
    ss.setdefault("schedules", {})
    ss["schedules"].setdefault(nickname_key, [])

    with st.expander("스케줄 추가", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            date = st.date_input("날짜", key=f"sch_date_{nickname_key}")
        with col2:
            kind = st.selectbox("종류", ["항암", "수혈", "검사", "외래", "기타"], key=f"sch_kind_{nickname_key}")
        desc = st.text_input("메모(예: ARA-C 100mg, 외래 10시)", key=f"sch_desc_{nickname_key}")
        if st.button("추가", key=f"sch_add_{nickname_key}"):
            ss["schedules"][nickname_key].append({"date": str(date), "kind": kind, "desc": desc})
            st.success("추가되었습니다.")

    rows = ss["schedules"][nickname_key]
    if rows:
        st.table(rows)
