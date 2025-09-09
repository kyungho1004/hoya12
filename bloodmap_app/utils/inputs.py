# -*- coding: utf-8 -*-
"""Input helpers: full lab list in final order.
- 암 모드: 항상 노출
- 소아 모드: 토글에서 호출하는 쪽에서 감춤/표시
- '입력한 수치만' 결과로 전달
"""
import streamlit as st

# (label, key, unit)
FIELDS = [
    ("WBC (백혈구)", "WBC", "x10^3/µL"),
    ("Hb (혈색소)", "Hb", "g/dL"),
    ("혈소판 (PLT)", "PLT", "x10^3/µL"),
    ("ANC (호중구)", "ANC", "/µL"),
    ("Ca (칼슘)", "Ca", "mg/dL"),
    ("P (인)", "P", "mg/dL"),
    ("Na (소디움)", "Na", "mmol/L"),
    ("K (포타슘)", "K", "mmol/L"),
    ("Albumin (알부민)", "Albumin", "g/dL"),
    ("Glucose (혈당)", "Glucose", "mg/dL"),
    ("Total Protein (총단백)", "Total Protein", "g/dL"),
    ("AST (간 효소 수치)", "AST", "U/L"),
    ("ALT (간세포 수치)", "ALT", "U/L"),
    ("LDH", "LDH", "U/L"),
    ("CRP", "CRP", "mg/dL"),
    ("Creatinine (Cr)", "Creatinine", "mg/dL"),
    ("Uric Acid (UA)", "Uric Acid", "mg/dL"),
    ("Total Bilirubin (TB)", "Total Bilirubin", "mg/dL"),
    ("BUN", "BUN", "mg/dL"),
    ("BNP (선택)", "BNP", "pg/mL"),
]

def collect_basic_inputs():
    """Render inputs and return a dict for non-empty entries only."""
    cols = st.columns(2)
    results = {}
    for i, (label, key, unit) in enumerate(FIELDS):
        c = cols[i % 2]
        with c:
            val = st.number_input(f"{label} ({unit})", key=f"lab_{key}", value=0.0, step=0.1, format="%.2f")
            # 0.0은 미입력 취급
            if val not in (0.0, None):
                results[key] = float(val)
    # clean zeros
    results = {k: v for k, v in results.items() if v != 0.0}
    return results
