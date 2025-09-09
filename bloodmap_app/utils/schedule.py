
# -*- coding: utf-8 -*-
import streamlit as st

def render_schedule(nickname_key: str):
    if not nickname_key:
        return
    st.markdown("### 🗓️ 스케줄(간단)")
    st.caption("추후 항암 주기/검사 일정 입력 UI로 확장 예정")
