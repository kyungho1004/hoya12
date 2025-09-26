# -*- coding: utf-8 -*-
"""eGFR calculation helpers: CKD-EPI 2021 (adult) and Schwartz (peds)."""
from __future__ import annotations

def egfr_ckd_epi_2021(cr_mgdl: float, age: int, sex_female: bool) -> float:
    if cr_mgdl is None or age is None:
        return 0.0
    kappa = 0.7 if sex_female else 0.9
    alpha = -0.241 if sex_female else -0.302
    min_scr = min(cr_mgdl / kappa, 1.0)
    max_scr = max(cr_mgdl / kappa, 1.0)
    coef_sex = 1.012 if sex_female else 1.0
    egfr = 142.0 * (min_scr ** alpha) * (max_scr ** -1.200) * (0.9938 ** age) * coef_sex
    return round(float(egfr), 1)

def egfr_schwartz_peds(cr_mgdl: float, height_cm: float, k: float = 0.413) -> float:
    if cr_mgdl is None or height_cm is None or cr_mgdl <= 0:
        return 0.0
    egfr = k * float(height_cm) / float(cr_mgdl)
    return round(float(egfr), 1)