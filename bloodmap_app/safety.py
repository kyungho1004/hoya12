# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta, timezone
import json, os

KST = timezone(timedelta(hours=9))

def now_kst() -> datetime:
    return datetime.now(tz=KST)

def _read_json(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _write_json(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ---- eGFR 계산 ----
def egfr_ckd_epi_2021(scr_mgdl: float, age: int, female: bool) -> Optional[float]:
    try:
        kappa = 0.7 if female else 0.9
        alpha = -0.241 if female else -0.302
        min_part = min(scr_mgdl / kappa, 1.0) ** alpha
        max_part = max(scr_mgdl / kappa, 1.0) ** (-1.200)
        sex_mult = 1.012 if female else 1.0
        egfr = 142.0 * min_part * max_part * (0.9938 ** age) * sex_mult
        return round(egfr, 1)
    except Exception:
        return None

def egfr_schwartz_2009(scr_mgdl: float, height_cm: float) -> Optional[float]:
    try:
        if scr_mgdl <= 0 or height_cm <= 0: return None
        return round(0.413 * height_cm / scr_mgdl, 1)
    except Exception:
        return None

# ---- 응급 배너 조건 ----
def urgent_banners(labs: Dict[str, float], care_24h: List[dict]) -> List[str]:
    L: List[str] = []
    na = safe_float(labs.get("Na"))
    k  = safe_float(labs.get("K"))
    anc = safe_float(labs.get("ANC"))
    # 전해질 응급
    if na is not None and (na < 125 or na > 155):
        L.append("🚨 전해질 위험: Na < 125 또는 > 155")
    if k is not None and k >= 6.0:
        L.append("🚨 고칼륨혈증 위험: K ≥ 6.0")
    # FN
    has_fever = any((x.get("type")=="fever" and safe_float(x.get("temp")) and safe_float(x.get("temp"))>=38.0) for x in care_24h)
    if has_fever and (anc is not None and anc < 500):
        L.append("🚨 발열성 호중구감소(FN) 의심: 최근 24h 발열 + ANC < 500 → 즉시 진료 권고")
    return L

def safe_float(x):
    try:
        if x is None: return None
        s = str(x).strip().replace(",","")
        if s=="": return None
        return float(s)
    except Exception:
        return None

# ---- 케어로그 집계/쿨다운/일일한도 ----
APAP_MAX_MG_PER_KG_DAY = 75.0
APAP_ADULT_MAX = 4000.0
IBU_MAX_MG_PER_KG_DAY = 30.0
IBU_ADULT_MAX = 1200.0

APAP_COOLDOWN_H = 4.0
IBU_COOLDOWN_H = 6.0

def _last_time(entries: List[dict], kind: str) -> Optional[datetime]:
    ts = [parse_kst(x.get("ts")) for x in entries if x.get("type")==kind and x.get("ts")]
    ts = [t for t in ts if isinstance(t, datetime)]
    return max(ts) if ts else None

def parse_kst(ts: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(ts.replace("Z","+09:00")).astimezone(KST) if ts else None
    except Exception:
        return None

def next_allowed(entries: List[dict], kind: str) -> Optional[datetime]:
    last = _last_time(entries, kind)
    if not last: return None
    cd = APAP_COOLDOWN_H if kind=="apap" else IBU_COOLDOWN_H
    return last + timedelta(hours=cd)

def total_24h_mg(entries: List[dict], kind: str, now: Optional[datetime]=None) -> float:
    now = now or now_kst()
    cutoff = now - timedelta(hours=24)
    mg = 0.0
    for e in entries:
        if e.get("type")==kind:
            t = parse_kst(e.get("ts"))
            if t and t >= cutoff:
                mg += float(e.get("mg") or 0.0)
    return mg

def limit_for_day(kind: str, weight_kg: Optional[float], adult: bool) -> float:
    if kind=="apap":
        return APAP_ADULT_MAX if adult or not weight_kg else APAP_MAX_MG_PER_KG_DAY * weight_kg
    if kind=="ibu":
        return IBU_ADULT_MAX if adult or not weight_kg else IBU_MAX_MG_PER_KG_DAY * weight_kg
    return 0.0

def block_ibu_reason(labs: Dict[str,float], egfr: Optional[float]) -> Optional[str]:
    pl = safe_float(labs.get("PLT"))
    if pl is not None and pl < 50000:
        return "PLT < 50k → 이부프로펜 금기"
    if egfr is not None and egfr < 60:
        return "eGFR < 60 → 이부프로펜 주의/차단"
    return None

def apap_caution_reason(labs: Dict[str,float]) -> Optional[str]:
    ast = safe_float(labs.get("AST"))
    alt = safe_float(labs.get("ALT"))
    if (ast is not None and ast >= 120) or (alt is not None and alt >= 120):
        return "AST/ALT ≥ 3×ULN(≈120) → 아세트아미노펜 주의"
    return None

# ---- 증상 기반 응급도(피수치 없이) ----
def symptom_emergencies(entries_2h: List[dict], entries_24h: List[dict]) -> List[str]:
    L: List[str] = []
    # green vomit (bile), blood/black stool flags are recorded via 'note' or 'kind'
    v3_2h = sum(1 for e in entries_2h if e.get("type")=="vomit")
    d6_24h = sum(1 for e in entries_24h if e.get("type")=="diarrhea")
    max_temp_24h = max([float(e.get("temp")) for e in entries_24h if e.get("type")=="fever" and e.get("temp")], default=0.0)
    if v3_2h >= 3:
        L.append("⛳ 2시간 내 구토 ≥ 3회")
    if d6_24h >= 6:
        L.append("⛳ 24시간 설사 ≥ 6회")
    if max_temp_24h >= 39.0:
        L.append("⛳ 고열(≥39℃)")
    # Notes based
    if any(("혈변" in (e.get("note") or "")) for e in entries_24h):
        L.append("⛳ 혈변")
    if any(("검은변" in (e.get("note") or "")) for e in entries_24h):
        L.append("⛳ 검은변(멜레나 의심)")
    if any(("초록 구토" in (e.get("note") or "") or "담즙" in (e.get("note") or "")) for e in entries_24h):
        L.append("⛳ 초록 구토(담즙성)")
    return L
