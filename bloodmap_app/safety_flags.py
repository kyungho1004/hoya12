
# -*- coding: utf-8 -*-
"""
safety_flags.py
- 실시간 안전 플래그/이상치 감지 (참고용)
- Fever / ANC / PLT / Hb / Na / K / Cr / AST/ALT / CRP 등 기본 규칙
"""
from typing import Dict, List, Tuple

def _num(x):
    try:
        return float(x)
    except Exception:
        return None

def flag_anomalies(labs: Dict[str, float] | None, vitals: Dict[str, float] | None = None) -> List[str]:
    """
    입력: labs = {"ANC":..,"PLT":..,"Hb":..,"Na":..,"K":..,"Cr":..,"AST":..,"ALT":..,"CRP":..}
         vitals = {"temp":..}
    출력: 경고 리스트 (이모지 포함)
    """
    labs = labs or {}
    vitals = vitals or {}
    out: List[str] = []

    T = _num(vitals.get("temp"))
    if T is not None:
        if T >= 39.0: out.append("🚑 39.0℃ 이상 고열 — 즉시 병원 권장")
        elif T >= 38.5: out.append("📞 38.5℃ 이상 발열 — 병원 연락 권장")
        elif T >= 38.0: out.append("💊 38.0–38.4℃ — 해열제 복용/경과관찰")

    anc = _num(labs.get("ANC"))
    if anc is not None:
        if anc < 500: out.append("🧪 ANC < 500 — 격리·생채소 금지 등 중증 호중구감소")
        elif anc < 1000: out.append("⚠️ ANC < 1000 — 감염주의")

    plt = _num(labs.get("PLT"))
    if plt is not None:
        if plt < 10000: out.append("🩸 PLT < 10k — 출혈 위험 매우 높음")
        elif plt < 50000: out.append("🩸 PLT < 50k — 출혈주의")

    hb = _num(labs.get("Hb"))
    if hb is not None and hb < 7.0:
        out.append("🫁 Hb < 7 — 빈혈 심함")

    na = _num(labs.get("Na"))
    if na is not None:
        if na < 125: out.append("🧂 저나트륨(중증) — 125 미만")

    k = _num(labs.get("K"))
    if k is not None:
        if k < 3.0: out.append("⚡ 저칼륨 — 3.0 미만")
        elif k > 6.0: out.append("⚡ 고칼륨 — 6.0 초과")

    cr = _num(labs.get("Cr"))
    if cr is not None and cr >= 2.0:
        out.append("🧪 Cr 상승 — 신장기능 저하 의심")

    ast = _num(labs.get("AST"))
    alt = _num(labs.get("ALT"))
    if ast is not None and ast >= 100: out.append("🫀 AST ≥ 100 — 간/근육 손상 의심")
    if alt is not None and alt >= 100: out.append("🫀 ALT ≥ 100 — 간손상 의심")

    crp = _num(labs.get("CRP"))
    if crp is not None and crp >= 10.0:
        out.append("🔥 CRP ≥ 10 — 염증/감염 의심")

    # 비현실적 수치/단위 의심 (샘플 규칙)
    upcr = _num(labs.get("UPCR"))
    if upcr is not None and upcr > 5000:
        out.append("🚨 위험 UPCR — 단위/입력 오류 가능")

    return out
