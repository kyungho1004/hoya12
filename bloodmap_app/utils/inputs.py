# -*- coding: utf-8 -*-
"""
All numeric entries without +/- steppers.
Replaces number_input with text_input + robust parsing.
"""
from typing import Any, Tuple
import re
import streamlit as st

def _normalize_label(label: Any) -> Tuple[str, str]:
    if isinstance(label, (list, tuple)):
        text = next((x for x in label if isinstance(x, str) and x.strip()), "항목")
        safe_src = "_".join(str(x) for x in label)
    elif isinstance(label, dict):
        text = label.get("label") or label.get("name") or label.get("title") or "항목"
        safe_src = label.get("key") or text
    else:
        text = str(label); safe_src = text
    safe_key = re.sub(r"[^0-9A-Za-z가-힣_]+","_", str(safe_src)).strip("_") or "field"
    return text, safe_key[:50]

def _fmt_placeholder(decimals: int, as_int: bool) -> str:
    if as_int: return "예: 1"
    d = max(0, int(decimals or 0))
    return "예: " + ("0" if d==0 else "0." + "0"*d)

def _parse_numeric(raw, decimals: int = 1):
    if raw in (None, ""): return None
    try:
        return round(float(str(raw).strip().replace(",","")), max(0, int(decimals or 0)))
    except Exception:
        return None

def num_input_generic(label, key=None, decimals: int = 1, as_int: bool = False, placeholder: str = ""):
    text, safe_key = _normalize_label(label)
    if not key: key = f"num_{safe_key}"
    ph = placeholder or _fmt_placeholder(decimals, as_int)
    # text_input has no +/- steppers
    raw = st.text_input(text, key=key, placeholder=ph)
    val = _parse_numeric(raw, decimals=0 if as_int else decimals)
    if as_int:
        try: return int(val) if val is not None else None
        except Exception: return None
    return val

def entered(x) -> bool:
    try:
        return x not in (None, "") and (float(x) == float(x))
    except Exception:
        return bool(x)
