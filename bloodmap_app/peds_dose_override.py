
# -*- coding: utf-8 -*-
"""
peds_dose_override.py — Drop-in replacement for peds_dose
- 앱의 app.py가 기대하는 함수 시그니처와 동일:
    acetaminophen_ml(age_m: int|float, weight_kg: float|None) -> (ml, meta_dict)
    ibuprofen_ml(age_m: int|float, weight_kg: float|None)     -> (ml, meta_dict)
- 원인이 되던 "고정값"을 제거하고, 반드시 나이/체중을 반영해 계산.
- 기본 공식(권장 범위 안에서 중앙값):
    * APAP: 10~15 mg/kg → 기본 12.5 mg/kg, 농도 160 mg/5mL
    * IBU : 5~10 mg/kg  → 기본 7.5 mg/kg , 농도 100 mg/5mL
- weight_kg가 None/0인 경우, 간단 추정식을 이용해 나이(개월)에서 체중을 추정합니다.
"""
from __future__ import annotations
from typing import Tuple, Dict

ACETAMINOPHEN_MG_PER_KG = 12.5
IBUPROFEN_MG_PER_KG     = 7.5
ACETAMINOPHEN_MG_PER_5ML = 160.0
IBUPROFEN_MG_PER_5ML     = 100.0

def _estimate_weight_from_age_months(age_months: float) -> float:
    # <12개월: 대략 3.3kg 시작 + 0.5kg/월, ≥12개월: 2*세 + 8
    try:
        a = float(age_months)
    except Exception:
        return 3.3
    if a <= 0: return 3.3
    if a < 12: return 3.3 + 0.5*a
    years = a / 12.0
    return 2.0*years + 8.0

def _ml_from_mg(weight_kg: float, mg_per_kg: float, syrup_mg_per_5ml: float) -> float:
    # ml = (weight*mg/kg) * (5mL / syrup_mg_per_5ml)
    dose_mg = max(0.0, float(weight_kg)) * max(0.0, float(mg_per_kg))
    ml = dose_mg * 5.0 / max(1e-6, float(syrup_mg_per_5ml))
    return round(ml, 1)

def acetaminophen_ml(age_m: float|int, weight_kg: float|None) -> Tuple[float, Dict]:
    w = float(weight_kg) if (weight_kg and weight_kg > 0) else _estimate_weight_from_age_months(age_m or 0)
    ml = _ml_from_mg(w, ACETAMINOPHEN_MG_PER_KG, ACETAMINOPHEN_MG_PER_5ML)
    meta = {
        "weight_used": round(w, 1),
        "mg_per_kg": ACETAMINOPHEN_MG_PER_KG,
        "syrup_mg_per_5ml": ACETAMINOPHEN_MG_PER_5ML,
        "interval": "4–6h",
        "max_per_day": 4
    }
    return ml, meta

def ibuprofen_ml(age_m: float|int, weight_kg: float|None) -> Tuple[float, Dict]:
    w = float(weight_kg) if (weight_kg and weight_kg > 0) else _estimate_weight_from_age_months(age_m or 0)
    ml = _ml_from_mg(w, IBUPROFEN_MG_PER_KG, IBUPROFEN_MG_PER_5ML)
    meta = {
        "weight_used": round(w, 1),
        "mg_per_kg": IBUPROFEN_MG_PER_KG,
        "syrup_mg_per_5ml": IBUPROFEN_MG_PER_5ML,
        "interval": "6–8h",
        "max_per_day": 3  # 기관에 따라 3~4회
    }
    return ml, meta
