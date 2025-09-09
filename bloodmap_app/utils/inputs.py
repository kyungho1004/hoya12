# -*- coding: utf-8 -*-
"""Input helpers (skeleton)."""
import streamlit as st

BASIC_FIELDS = [
    ("WBC (백혈구)", "WBC", (4.0, 10.0), "x10^3/µL"),
    ("Hb (혈색소)", "Hb", (12.0, 16.0), "g/dL"),
    ("혈소판 (PLT)", "PLT", (150, 400), "x10^3/µL"),
    ("ANC (호중구)", "ANC", (1500, 8000), "/µL"),
    ("AST (간 효소 수치)", "AST", (0, 40), "U/L"),
    ("ALT (간세포 수치)", "ALT", (0, 45), "U/L"),
    ("CRP", "CRP", (0.0, 0.5), "mg/dL"),
    ("Creatinine (Cr)", "Cr", (0.6, 1.3), "mg/dL"),
]

def collect_basic_inputs():
    """Render minimal lab inputs and return dict of entered values (only non-empty)."""
    cols = st.columns(2)
    results = {}
    for i, (label, key, _, unit) in enumerate(BASIC_FIELDS):
        c = cols[i % 2]
        with c:
            val = st.text_input(f"{label} ({unit})", key=f"lab_{key}")
            if val.strip():
                try:
                    results[key] = float(val)
                except:
                    st.warning(f"{label}: 숫자만 입력하세요")
    return results
