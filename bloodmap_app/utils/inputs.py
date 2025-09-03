# -*- coding: utf-8 -*-
import streamlit as st

def _parse_numeric(raw, decimals=1):
    try:
        if raw is None or str(raw).strip() == "":
            return None
        v = float(str(raw).replace(",", "").strip())
        return round(v, decimals)
    except Exception:
        return None

def num_input_generic(label, key=None, decimals=1, as_int=False, placeholder=""):
    if as_int:
        raw = st.text_input(label, key=key, placeholder=placeholder)
        v = _parse_numeric(raw, decimals=0)
        return int(v) if v is not None else None
    else:
        raw = st.text_input(label, key=key, placeholder=placeholder)
        return _parse_numeric(raw, decimals=decimals)

def entered(v):
    try:
        return v is not None and str(v).strip() != ""
    except:
        return False
