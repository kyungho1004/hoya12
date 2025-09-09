
# -*- coding: utf-8 -*-
import streamlit as st

def _parse_numeric(raw, decimals=1):
    if raw in (None, ""):
        return None
    try:
        v = float(str(raw).replace(",", "").strip())
        if decimals is None:
            return v
        return round(v, decimals)
    except Exception:
        return None

def num_input_generic(label, key=None, decimals=1, placeholder="", as_int=False):
    raw = st.text_input(label, key=key, placeholder=placeholder)
    if as_int:
        try:
            return int(str(raw).strip())
        except Exception:
            return None
    return _parse_numeric(raw, decimals=decimals)

def entered(v):
    try:
        return v is not None and str(v) != "" and float(v) == float(v)
    except Exception:
        return False
