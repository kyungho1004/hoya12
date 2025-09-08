# -*- coding: utf-8 -*-
import streamlit as st

def user_key(nickname: str, pin: str) -> str:
    pin = (pin or "").strip()
    if len(pin) != 4 or not pin.isdigit():
        return ""
    nickname = (nickname or "").strip()
    return f"{nickname}#{pin}"

def init_state():
    for k, v in {"onco_prev_key": "", "onco_selected": []}.items():
        if k not in st.session_state:
            st.session_state[k] = v
