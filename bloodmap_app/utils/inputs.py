
# -*- coding: utf-8 -*-
"""
Robust number/text input helpers.
- Accepts label as str / tuple / list / dict and normalizes to a display string
- Generates safe keys if caller didn't pass one
- Avoids TypeError in streamlit.number_input when label is non-string
"""

from typing import Tuple, Any
import re
import streamlit as st

def _normalize_label(label: Any) -> Tuple[str, str]:
    # 1) decide display string
    text = None
    if isinstance(label, (list, tuple)):
        # prefer the first string element as label
        for x in label:
            if isinstance(x, str) and x.strip():
                text = x
                break
        if text is None:
            text = "항목"
        safe_src = "_".join(str(x) for x in label)
    elif isinstance(label, dict):
        text = (
            label.get("label")
            or label.get("name")
            or label.get("title")
            or next((v for v in label.values() if isinstance(v, str) and v.strip()), "항목")
        )
        safe_src = label.get("key") or text
    else:
        text = str(label)
        safe_src = text

    # 2) sanitize to make a stable key fragment
    safe_key = re.sub(r"[^0-9A-Za-z가-힣_]+", "_", str(safe_src)).strip("_")
    if not safe_key:
        safe_key = "field"
    if len(safe_key) > 50:
        safe_key = safe_key[:50]
    return text, safe_key

def _fmt(decimals: int, as_int: bool) -> str:
    if as_int:
        return "%d"
    if decimals < 0:
        decimals = 0
    if decimals > 6:
        decimals = 6
    return "%." + str(decimals) + "f"

def num_input_generic(label, key=None, decimals: int = 1, as_int: bool = False, placeholder: str = ""):
    text, safe_key = _normalize_label(label)
    fmt = _fmt(decimals, as_int)
    step = 1 if as_int else (10 ** (-max(decimals, 0)))
    # assign a key if missing
    if key is None or key == "":
        key = f"num_{safe_key}"
    try:
        v = st.number_input(text, key=key, step=step, format=fmt)
    except TypeError:
        # final fallback: ensure text is str
        v = st.number_input(str(text), key=key, step=step, format=fmt)
    if as_int and v is not None:
        try:
            return int(v)
        except Exception:
            return None
    return v

def _parse_numeric(raw, decimals: int = 1):
    if raw in ("", None):
        return None
    try:
        return round(float(raw), decimals)
    except Exception:
        return None

def entered(x) -> bool:
    try:
        return x not in (None, "") and (float(x) == float(x))
    except Exception:
        return False
