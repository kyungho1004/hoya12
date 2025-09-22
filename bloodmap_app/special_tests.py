# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import List, Optional
import streamlit as st

def _num(x):
    try:
        if x is None: return None
        if isinstance(x, (int,float)): return float(x)
        s = str(x).replace(",", "").strip()
        s2 = "".join(ch for ch in s if (ch.isdigit() or ch=='.' or ch=='-'))
        return float(s2) if s2 else None
    except Exception:
        return None

def _flag(kind: Optional[str]) -> str:
    return {"ok":"🟢 정상", "warn":"🟡 주의", "risk":"🚨 위험"}.get(kind or "", "")

def _emit(lines: List[str], kind: Optional[str], msg: str):
    tag = _flag(kind)
    lines.append(f"{tag} {msg}" if tag else msg)

def special_tests_ui() -> List[str]:
    lines: List[str] = []
    with st.expander("🧪 특수검사 (선택 입력)", expanded=False):
        # 심장/근육 섹션
        st.markdown("**심장/근육 (CK / CK-MB / Troponin / Myoglobin)**")
        h1,h2,h3,h4 = st.columns(4)
        with h1: ck   = _num(st.text_input("CK (U/L)", placeholder="예: 160"))
        with h2: ckmb = _num(st.text_input("CK-MB (ng/mL)", placeholder="예: 2.5"))
        with h3: troI = _num(st.text_input("Troponin I (ng/mL)", placeholder="예: 0.01"))
        with h4: troT = _num(st.text_input("Troponin T (ng/mL)", placeholder="예: 0.005"))
        ulnI = _num(st.text_input("ULN Troponin I (ng/mL)", placeholder="예: 0.04"))
        ulnT = _num(st.text_input("ULN Troponin T (ng/mL)", placeholder="예: 0.014"))
        myo  = _num(st.text_input("Myoglobin (ng/mL)", placeholder="예: 50"))
        myo_uln = _num(st.text_input("ULN Myoglobin (ng/mL)", placeholder="예: 70"))

        if ck is not None:
            if ck >= 5000: _emit(lines, "risk", f"CK {ck} → 횡문근융해 의심(즉시 상담)")
            elif ck >= 1000: _emit(lines, "warn", f"CK {ck} → 근손상/운동/약물 영향 가능")
        if ckmb is not None and ckmb >= 5: _emit(lines, "warn", f"CK-MB {ckmb} ≥ 5 → 심근 손상 지표 상승 가능")
        if troI is not None and troI >= (ulnI if ulnI is not None else 0.04): _emit(lines, "risk", f"Troponin I {troI} ≥ ULN → 심근 손상 의심")
        if troT is not None and troT >= (ulnT if ulnT is not None else 0.014): _emit(lines, "risk", f"Troponin T {troT} ≥ ULN → 심근 손상 의심")

        if myo is not None and myo_uln is not None and myo >= myo_uln:
            _emit(lines, "warn", f"Myoglobin {myo} ≥ ULN({myo_uln}) → 근손상/초기 심근 손상 가능")
        if myo is not None and myo >= 500:
            _emit(lines, "risk", f"Myoglobin {myo} ≥ 500 ng/mL → 근육 손상 심함/횡문근융해 가능(즉시 평가)")
    return lines
