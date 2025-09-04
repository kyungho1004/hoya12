# -*- coding: utf-8 -*-
import streamlit as st
from typing import Optional

def css_load():
    try:
        with open("bloodmap_app/style.css", "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception as e:
        st.caption("스타일 로드 실패: %s" % e)

def safe_float(x) -> Optional[float]:
    """문자/None/빈값 섞여도 안전하게 float로 변환. 변환 실패 시 None."""
    try:
        if x is None or (isinstance(x, str) and x.strip() == ""):
            return None
        return float(x)
    except Exception:
        return None

def num_input(label: str, key: str, unit: str = None, step: float = 0.1, format_decimals: int = 2):
    ph = "예: " + ("0" if format_decimals == 0 else "0." + ("0" * format_decimals))
    val = st.text_input(label + (f" ({unit})" if unit else ""), key=key, placeholder=ph)
    return safe_float(val)

def pediatric_guard(years_input, months_input):
    """소아 계산 도우미용 가드: AttributeError 방지형 캐스팅"""
    y = None if years_input is None else safe_float(years_input)
    m = None if months_input is None else safe_float(months_input)
    y = int(y) if y is not None else 0
    m = int(m) if m is not None else 0
    try:
        total_m = int(y) * 12 + int(m)
        return max(total_m, 0)
    except Exception:
        return 0

def pin_4_guard(pin_str: str) -> str:
    """숫자 외 제거 + 4자리 강제 (왼쪽 0-padding)"""
    only_digits = "".join(ch for ch in (pin_str or "") if ch.isdigit())
    return (only_digits[-4:]).zfill(4) if only_digits else "0000"
