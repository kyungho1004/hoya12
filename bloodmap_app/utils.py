# -*- coding: utf-8 -*-
"""
Minimal utils used by app.py
Provides: css_load, num_input, safe_float, pediatric_guard, pin_4_guard
"""
import streamlit as st
from typing import Optional

def css_load():
    """Load local style.css if present (no hard fail)."""
    try:
        with open("bloodmap_app/style.css", "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception:
        pass

def safe_float(x) -> Optional[float]:
    """Safe numeric cast: returns None on failure/empty string."""
    try:
        if x is None:
            return None
        if isinstance(x, str) and x.strip() == "":
            return None
        return float(x)
    except Exception:
        return None

def num_input(label: str, key: str, unit: str = None, step: float = 0.1, format_decimals: int = 2):
    """Text-based numeric input (robust on Streamlit Cloud decimal parsing)."""
    ph = "예: " + ("0" if format_decimals == 0 else "0." + ("0" * format_decimals))
    val = st.text_input(label + (f" ({unit})" if unit else ""), key=key, placeholder=ph)
    return safe_float(val)

def pediatric_guard(years_input, months_input) -> int:
    """Return total months from (years, months) with strong guards to avoid AttributeError."""
    def _to_int(v):
        try:
            if v is None:
                return 0
            if isinstance(v, str) and v.strip() == "":
                return 0
            return int(float(v))
        except Exception:
            return 0
    y = _to_int(years_input)
    m = _to_int(months_input)
    total = y * 12 + m
    return max(total, 0)

def pin_4_guard(pin_str: str) -> str:
    """Keep digits only and enforce 4 chars with zero-left-padding."""
    only_digits = "".join(ch for ch in (pin_str or "") if str(ch).isdigit())
    return (only_digits[-4:]).zfill(4) if only_digits else "0000"
