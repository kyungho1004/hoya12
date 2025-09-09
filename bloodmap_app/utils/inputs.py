import streamlit as st

def _parse_numeric(raw, decimals=1):
    if raw is None:
        return None
    s = str(raw).strip().replace(",", "")
    if s == "":
        return None
    try:
        return int(float(s)) if decimals == 0 else round(float(s), decimals)
    except Exception:
        return None

def num_input_generic(label, key=None, decimals=1, placeholder="", as_int=False):
    raw = st.text_input(label, key=key, placeholder=placeholder)
    return _parse_numeric(raw, 0 if as_int else decimals)

def entered(v):
    try:
        if v is None:
            return False
        if isinstance(v, str):
            return v.strip() != ""
        return True
    except Exception:
        return False
