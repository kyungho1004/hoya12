
# -*- coding: utf-8 -*-
import streamlit as st

def render_schedule(nickname_key: str):
    with st.expander("🗓️ 항암 스케줄(선택)", expanded=False):
        st.caption("간단 메모용 — 실제 처방/스케줄과 다를 수 있어요.")
        st.text_input("이번 주기 메모", key="sched_note")
