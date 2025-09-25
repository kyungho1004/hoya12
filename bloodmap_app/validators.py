
"""
validators.py — BloodMap input guards (min/max/step) + clamp helpers.
Usage example in Streamlit:
    from validators import num_field
    Na = num_field("Na (mEq/L)", field="Na", key="Na")
"""
from __future__ import annotations
from typing import Optional, Dict, Any
import math

try:
    import streamlit as st
except Exception:
    # Allow import for non-Streamlit validation (tests)
    class _Dummy:
        def number_input(self, *a, **k): return k.get("value")
    st = _Dummy()

# Physiologic bounds (adult default; pediatric still safe). Tune as needed.
BOUNDS: Dict[str, Dict[str, float]] = {
    "ANC":     {"min": 0,    "max": 50000, "step": 100},
    "WBC":     {"min": 0,    "max": 500,   "step": 0.1},
    "Hb":      {"min": 0,    "max": 25,    "step": 0.1},
    "PLT":     {"min": 0,    "max": 2000,  "step": 1},
    "CRP":     {"min": 0,    "max": 50,    "step": 0.1},
    "Na":      {"min": 110,  "max": 170,   "step": 1},
    "K":       {"min": 2.0,  "max": 7.0,   "step": 0.1},
    "Cl":      {"min": 70,   "max": 130,   "step": 1},
    "Ca":      {"min": 6.0,  "max": 14.0,  "step": 0.1},
    "Alb":     {"min": 1.0,  "max": 6.0,   "step": 0.1},
    "AST":     {"min": 0,    "max": 2000,  "step": 1},
    "ALT":     {"min": 0,    "max": 2000,  "step": 1},
    "BUN":     {"min": 1,    "max": 200,   "step": 1},
    "Cr":      {"min": 0.0,  "max": 20.0,  "step": 0.1},
    "UA":      {"min": 0.0,  "max": 20.0,  "step": 0.1},
    "Glucose": {"min": 20,   "max": 1000,  "step": 1},
    "Age":     {"min": 0,    "max": 120,   "step": 1},
    "Weight":  {"min": 1,    "max": 300,   "step": 0.1},
    "Temp":    {"min": 34.0, "max": 43.0,  "step": 0.1},
}

def clamp(field: str, val: Optional[float]) -> Optional[float]:
    if val is None or (isinstance(val, float) and math.isnan(val)): 
        return None
    b = BOUNDS.get(field)
    if not b:
        return val
    return max(b["min"], min(b["max"], float(val)))

def bounds(field: str) -> Dict[str, Any]:
    b = BOUNDS.get(field, {"min": None, "max": None, "step": None})
    return {"min_value": b["min"], "max_value": b["max"], "step": b["step"]}

def num_field(label: str, field: str, key: Optional[str]=None, value: Optional[float]=None, help: Optional[str]=None):
    b = bounds(field)
    return st.number_input(label, key=key or field, value=value, help=help, **{k:v for k,v in b.items() if v is not None})
