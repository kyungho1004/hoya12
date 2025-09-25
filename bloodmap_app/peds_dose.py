# -*- coding: utf-8 -*-
from typing import Optional, Tuple

ACETAMINOPHEN_MG_PER_5ML = 160.0
IBUPROFEN_MG_PER_5ML = 100.0
ACETAMINOPHEN_MG_PER_KG = 12.5
IBUPROFEN_MG_PER_KG     = 7.5

def estimate_weight_from_age_months(age_months: float) -> float:
    if age_months <= 0:
        return 3.3
    if age_months < 12:
        return 3.3 + 0.5 * age_months
    years = age_months / 12.0
    return 2.0 * years + 8.0

def _ml_from_mg(weight_kg: float, mg_per_kg: float, syrup_mg_per_5ml: float) -> float:
    dose_mg = weight_kg * mg_per_kg
    ml = dose_mg * 5.0 / syrup_mg_per_5ml
    return round(ml, 1)

def acetaminophen_ml(age_months: float, weight_kg: Optional[float] = None, syrup_mg_per_5ml: float = ACETAMINOPHEN_MG_PER_5ML) -> Tuple[float, float]:
    w = weight_kg if (weight_kg and weight_kg > 0) else estimate_weight_from_age_months(age_months)
    return _ml_from_mg(w, ACETAMINOPHEN_MG_PER_KG, syrup_mg_per_5ml), round(w, 1)

def ibuprofen_ml(age_months: float, weight_kg: Optional[float] = None, syrup_mg_per_5ml: float = IBUPROFEN_MG_PER_5ML) -> Tuple[float, float]:
    w = weight_kg if (weight_kg and weight_kg > 0) else estimate_weight_from_age_months(age_months)
    return _ml_from_mg(w, IBUPROFEN_MG_PER_KG, syrup_mg_per_5ml), round(w, 1)
