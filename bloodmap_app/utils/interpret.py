# -*- coding: utf-8 -*-
from typing import Dict, Tuple, List

NORMALS = {
    "WBC": (4.0, 10.0),
    "Hb": (12.0, 16.0),
    "PLT": (150, 400),
    "ANC": (1500, 8000),
    "Ca": (8.6, 10.2),
    "P": (2.5, 4.5),
    "Na": (135, 145),
    "K": (3.5, 5.1),
    "Albumin": (3.5, 5.2),
    "Glucose": (70, 140),
    "Total Protein": (6.0, 8.3),
    "AST": (0, 40),
    "ALT": (0, 55),
    "LDH": (120, 250),
    "CRP": (0.0, 0.5),
    "Creatinine": (0.6, 1.3),
    "Uric Acid": (3.5, 7.2),
    "Total Bilirubin": (0.3, 1.2),
    "BUN": (8, 23),
    "BNP": (0, 100),
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

def interpret_labs(labs: Dict[str, float]) -> List[Tuple[str, float, str, str]]:
    out = []
    for k, v in labs.items():
        if k in NORMALS:
            level = classify(v, NORMALS[k])
            hint = "범위 확인"
            if k == "AST" and v >= 50:
                hint = "50 이상: 간기능 저하 가능성"
            elif k == "ALT" and v >= 55:
                hint = "55 이상: 간세포 손상 의심"
            elif k == "CRP" and v > 1.0:
                hint = "염증 반응 상승"
            elif k == "ANC" and v < 500:
                hint = "중증 호중구 감소 → 생채소 금지, 익힌 음식 권장"
            out.append((k, v, level, hint))
    return out

# === Special tests ===
QUAL_MAP = {
    "없음": ("정상", "정상 범위"),
    "+": ("주의", "약한 양성"),
    "++": ("주의", "중등도 양성"),
    "+++": ("위험", "강한 양성"),
}

def interpret_qual(name: str, val: str):
    level, msg = QUAL_MAP.get(val or "없음")
    hint = ""
    if name == "단백뇨" and val in ("++", "+++"):
        hint = "🚨 신장 기능 이상 가능성"
    if name == "잠혈" and val in ("++", "+++"):
        hint = "🚨 요로 출혈/염증 의심"
    return (name, val or "없음", level, msg + (f" · {hint}" if hint else ""))

def interpret_quant(name: str, value: float):
    normals = {
        "C3": (90, 180), "C4": (10, 40),
        "TG": (0, 200), "HDL": (40, 999), "LDL": (0, 130),
        "적혈구": (4.0, 5.5), "백혈구": (4.0, 10.0),
    }
    level = "정상"
    hint = "범위 확인"
    if name in normals:
        lo, hi = normals[name]
        if value < lo*0.9 or value > hi*1.5:
            level = "위험"
        elif value < lo or value > hi:
            level = "주의"
        if name == "TG" and value >= 200:
            hint = "200 이상: 고지혈증 가능성"
        if name in ("C3","C4") and value < lo:
            hint = "낮음 → 🟡 면역계 이상 가능성"
    return (name, value, level, hint)

def diuretic_checks(labs: Dict[str, float], on_diuretic: bool) -> List[str]:
    tips = []
    bun = labs.get("BUN")
    cr = labs.get("Creatinine") or labs.get("Cr")
    if bun and cr:
        try:
            ratio = float(bun) / float(cr)
            if ratio > 20:
                tips.append("BUN/Cr > 20 → 탈수 의심")
        except Exception:
            pass
    if on_diuretic:
        for k, lo in [("K", 3.5), ("Na", 135), ("Ca", 8.6)]:
            if k in labs and labs[k] < lo:
                tips.append(f"{k} 낮음 → 이뇨제 관련 전해질 이상 가능")
    return tips
