# -*- coding: utf-8 -*-
from __future__ import annotations

# Minimal unit safety checker for common labs; returns list of warnings.
def unit_guard(labs: dict) -> list[str]:
    warns = []
    # very rough sanity windows
    if labs.get("Na") and labs["Na"] > 200: warns.append("Na 값이 비정상적으로 큼 — 단위 확인(mmol/L?)")
    if labs.get("K") and labs["K"] > 15: warns.append("K 값이 비정상적으로 큼 — 단위 확인(mmol/L?)")
    if labs.get("Cr") and labs["Cr"] > 20: warns.append("Cr 값이 비정상적으로 큼 — 단위 확인(mg/dL?)")
    if labs.get("WBC") and labs["WBC"] > 300: warns.append("WBC 단위(×10^3/μL)인지 확인")
    return warns
