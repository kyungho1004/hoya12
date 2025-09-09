# -*- coding: utf-8 -*-
"""Interpretation engine (very small skeleton consistent with caregiver UX)."""
from typing import Dict, Tuple

NORMALS = {
    "AST": (0, 40),
    "ALT": (0, 55),
    "TG": (0, 200),
    "CRP": (0, 0.5),
}

def status_color(level: str) -> str:
    return {"정상":"ok", "주의":"warn", "위험":"danger"}.get(level, "ok")

def classify(value: float, normal: Tuple[float, float]) -> str:
    lo, hi = normal
    if value < lo*0.9 or value > hi*1.5:
        return "위험"
    if value < lo or value > hi:
        return "주의"
    return "정상"

def interpret_labs(labs: Dict[str, float]):
    """Return list of (label, value, level, hint). Only for available keys."""
    out = []
    for k, v in labs.items():
        if k in NORMALS:
            level = classify(v, NORMALS[k])
            if k == "AST" and v >= 50:
                hint = "50 이상: 간기능 저하 가능성"
            elif k == "ALT" and v >= 55:
                hint = "55 이상: 간세포 손상 의심"
            elif k == "CRP" and v > 1.0:
                hint = "염증 반응 상승"
            else:
                hint = "범위 확인"
            out.append((k, v, level, hint))
    return out
