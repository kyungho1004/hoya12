# -*- coding: utf-8 -*-
"""Common utilities for BloodMap app (UI + helpers)."""

import re
import streamlit as st

# ---------- UI: 별명 + PIN 입력 ----------
def nickname_pin(key_prefix="np_"):
    """Render nickname + 4-digit PIN inputs with unique widget keys.
    Returns (nick, pin, key) where key is "nick#pin" when valid, else "".
    """
    c1, c2 = st.columns([2, 1])
    with c1:
        nick = st.text_input("별명", placeholder="예: 홍길동", key=key_prefix + "nick")
    with c2:
        pin = st.text_input("PIN (4자리 숫자)", placeholder="0000", key=key_prefix + "pin", max_chars=4)
    # sanitize
    pin = "".join(ch for ch in pin if ch.isdigit())[:4]
    key = f"{nick}#{pin}" if nick and len(pin) == 4 else ""
    return nick, pin, key

# ---------- Numeric helpers ----------
_num_pat = re.compile(r"-?\d+(?:\.\d+)?")

def clean_num(x, default=None):
    """Extract float from free text/None; return default if not found."""
    if x is None:
        return default
    try:
        return float(x)
    except Exception:
        pass
    m = _num_pat.search(str(x))
    return float(m.group()) if m else default

def round_half(x, digits=1):
    """Round half away from zero with given digits (default 1)."""
    from decimal import Decimal, ROUND_HALF_UP, getcontext
    getcontext().prec = 28
    q = Decimal(10) ** -digits
    return float(Decimal(str(x)).quantize(q, rounding=ROUND_HALF_UP))

# ---------- Clinical helpers ----------
def temp_band(t):
    """Return temperature band label based on project spec."""
    v = clean_num(t, None)
    if v is None:
        return "없음"
    if v < 37.0:
        return "없음"
    if 37.0 <= v < 37.5:
        return "37~37.5 (미열)"
    if 37.5 <= v < 38.5:
        return "37.5~38 (병원 내원 권장)"
    return "38.5~39 (병원/응급실)"

def rr_thr_by_age_m(age_m):
    """Return tachypnea threshold (breaths/min) by age in months (approx WHO)."""
    try:
        a = int(age_m or 0)
    except Exception:
        a = 0
    if a < 2:
        return 60  # <2 months
    if a < 12:
        return 50  # 2–12 months
    if a < 60:
        return 40  # 1–5 years
    return 30      # >5 years

# ---------- Simple layout helper ----------
def schedule_block(title, items):
    """Render a simple bullet list under a section title."""
    st.markdown(f"#### {title}")
    for it in items:
        st.write(f"- {it}")
