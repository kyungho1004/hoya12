
# -*- coding: utf-8 -*-
import streamlit as st

def _parse_numeric(raw, decimals=1):
    if raw is None or raw == "":
        return None
    try:
        v = float(str(raw).replace(",", "").strip())
        if decimals is None:
            return v
        if decimals == 0:
            return int(round(v))
        return round(v, decimals)
    except Exception:
        return None

def entered(v):
    try:
        return v is not None and str(v) != "" and float(v) == float(v)
    except Exception:
        return False

def num_input_generic(label, key=None, decimals=1, placeholder="", as_int=False):
    raw = st.text_input(label, key=key, placeholder=placeholder)
    v = _parse_numeric(raw, decimals=0 if as_int else decimals)
    return v
