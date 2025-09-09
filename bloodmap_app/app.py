# -*- coding: utf-8 -*-
# app_utils.py — shim used by app.py to avoid conflicts with `utils` package.
try:
    import streamlit as st
except Exception:
    st = None

def user_key(nickname: str, pin: str) -> str:
    pin = (pin or "").strip()
    # allow only 4 digits
    if len(pin) != 4 or not pin.isdigit():
        return ""
    nickname = (nickname or "").strip()
    return f"{nickname}#{pin}" if nickname else ""

def init_state():
    """Initialize session_state keys used across pages."""
    if st is None:
        return
    defaults = {
        "onco_prev_key": "",
        "onco_selected": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
