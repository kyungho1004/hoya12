# -*- coding: utf-8 -*-
from typing import Tuple, Any
import re
import streamlit as st

def _normalize_label(label: Any):
    if isinstance(label, (list, tuple)):
        for x in label:
            if isinstance(x, str) and x.strip():
                text = x; break
        else:
            text = "항목"
        safe_src = "_".join(str(x) for x in label)
    elif isinstance(label, dict):
        text = label.get("label") or label.get("name") or label.get("title") or "항목"
        safe_src = label.get("key") or text
    else:
        text = str(label); safe_src = text
    safe_key = re.sub(r"[^0-9A-Za-z가-힣_]+", "_", str(safe_src)).strip("_") or "field"
    return text, safe_key[:50]

def _fmt(decimals: int, as_int: bool) -> str:
    if as_int: return "%d"
    decimals = max(0, min(6, int(decimals or 0)))
    return "%." + str(decimals) + "f"

def num_input_generic(label, key=None, decimals: int = 1, as_int: bool = False, placeholder: str = ""):
    text, safe_key = _normalize_label(label)
    fmt = _fmt(decimals, as_int)
    # step/value 타입을 format과 맞춤
    if as_int:
        step = 1
        default = 0
    else:
        dec = max(0, int(decimals or 0))
        step = 1.0 if dec == 0 else (10 ** (-dec))
        default = 0.0
    if not key:
        key = f"num_{safe_key}"
    try:
        v = st.number_input(text, key=key, step=step, format=fmt, value=default)
    except TypeError:
        v = st.number_input(str(text), key=key, step=step, format=fmt, value=default)
    if as_int:
        try: return int(v)
        except Exception: return None
    return v

def _parse_numeric(raw, decimals: int = 1):
    if raw in ("", None): return None
    try: return round(float(raw), max(0, int(decimals or 0)))
    except Exception: return None

def entered(x) -> bool:
    try:
        return x not in (None, "") and (float(x) == float(x))
    except Exception:
        # 문자열(예: 요검사 '+')도 입력으로 인정
        return bool(x)
