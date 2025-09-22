# -*- coding: utf-8 -*-
import streamlit as st
def render_special_tests(labs_ctx: dict) -> dict:
    st.markdown("### 🧪 특수검사")
    c1, c2 = st.columns([2,1])
    myo = c1.text_input("Myoglobin (ng/mL)", value=str(labs_ctx.get("Myoglobin") or ""), key="myoglobin_input")
    uln = c2.text_input("ULN (정상 상한, ng/mL)", value=str(labs_ctx.get("Myoglobin_ULN") or 72), key="myoglobin_uln")
    def num(v):
        try: return float(str(v).strip())
        except Exception: return None
    myo_v, uln_v = num(myo), num(uln)
    flag, msg = "ℹ️", None
    if myo_v is not None and uln_v is not None:
        if myo_v >= 500: flag, msg = "🔴", "근육 손상 심함/횡문근융해 가능 — 즉시 평가 권고"
        elif myo_v >= uln_v: flag, msg = "🟡", "근손상/초기 심근 손상 가능"
        else: flag, msg = "🟢", "정상 범위"
    if myo_v is not None:
        st.write(f"**Myoglobin:** {myo_v} ng/mL  ·  **ULN:** {uln_v if uln_v is not None else '—'}  → {flag} {msg or ''}")
    out = dict(labs_ctx or {})
    if myo_v is not None: out["Myoglobin"] = myo_v
    if uln_v is not None: out["Myoglobin_ULN"] = uln_v
    return out
