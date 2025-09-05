
# -*- coding: utf-8 -*-
import streamlit as st

def render_schedule(nickname_key):
    with st.expander("📅 항암/외래 스케줄 메모(간단)", expanded=False):
        st.caption("이 칸은 개인 메모용입니다. 브라우저 세션 내에서만 보존됩니다.")
        note = st.text_area("스케줄 메모", key=f"sched_{nickname_key}")
        st.session_state.get("schedules", {})[nickname_key] = note
