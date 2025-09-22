
# -*- coding: utf-8 -*-
"""
special_tests_addon
- Non-destructive Special Tests panel: Myoglobin (ULN, interpretation)
- Drop-in section that does not alter existing lab structures.
"""
from __future__ import annotations
import streamlit as st
from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))

def render_special_tests(labs_ctx: dict) -> dict:
    """
    labs_ctx: dict-like to read/write optional fields (e.g., labs_ctx["Myoglobin"])
    Returns an updated dict with 'Myoglobin' and 'Myoglobin_ULN' if provided.
    """
    st.markdown("### 🧪 특수검사")
    c1, c2 = st.columns([2,1])
    with c1:
        myo = st.text_input("Myoglobin (ng/mL)", value=str(labs_ctx.get("Myoglobin") or ""), key="myoglobin_input")
    with c2:
        uln = st.text_input("ULN (정상 상한, ng/mL)", value=str(labs_ctx.get("Myoglobin_ULN") or 72), key="myoglobin_uln")
    # sanitize
    def num(v):
        try:
            return float(str(v).strip())
        except Exception:
            return None
    myo_v = num(myo)
    uln_v = num(uln)

    # Interpretation
    msg = None
    flag = "ℹ️"
    if myo_v is not None and uln_v is not None:
        if myo_v >= 500:
            flag = "🔴"
            msg = "근육 손상 심함/횡문근융해 가능 — 즉시 평가 권고"
        elif myo_v >= uln_v:
            flag = "🟡"
            msg = "근손상/초기 심근 손상 가능"
        else:
            flag = "🟢"
            msg = "정상 범위"
    if myo_v is not None:
        st.write(f"**Myoglobin:** {myo_v} ng/mL  ·  **ULN:** {uln_v if uln_v is not None else '—'}  → {flag} {msg or ''}")

    # store back into context without mutating required keys of main app
    out = dict(labs_ctx or {})
    if myo_v is not None:
        out["Myoglobin"] = myo_v
    if uln_v is not None:
        out["Myoglobin_ULN"] = uln_v
    return out
