
# -*- coding: utf-8 -*-
import streamlit as st

def _clean(s): 
    return "" if s is None else str(s).strip()

def _parse_numeric(raw, decimals=1):
    s = _clean(raw)
    if not s:
        return None
    try:
        v = float(s.replace(",", ""))
        if decimals is None:
            return v
        if decimals==0:
            return int(round(v))
        return round(v, decimals)
    except Exception:
        return None

def num_input_generic(label, key, decimals=1, placeholder="", as_int=False):
    raw = st.text_input(label, key=key, placeholder=placeholder)
    v = _parse_numeric(raw, decimals=0 if as_int else decimals)
    return v

def entered(v):
    try:
        return v is not None and str(v) != "" and float(v) != 0
    except Exception:
        return False
