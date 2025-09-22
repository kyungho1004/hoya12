
# -*- coding: utf-8 -*-
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Tuple, Optional
import streamlit as st

KST = timezone(timedelta(hours=9))

def _within_24h(ts:str)->bool:
    try:
        t = datetime.fromisoformat(ts)
        return (datetime.now(KST) - t).total_seconds() <= 24*3600
    except Exception:
        return False

def compute_guard(entries: List[Dict[str,Any]], weight_kg: float|None, is_adult: bool)->Dict[str,Any]:
    apap_total = 0.0; ibu_total = 0.0; last_apap=None; last_ibu=None
    for e in entries or []:
        if not _within_24h(e.get("ts","")): continue
        if e.get("type") == "apap":
            apap_total += float(e.get("mg") or 0); last_apap = e.get("ts")
        if e.get("type") == "ibu":
            ibu_total += float(e.get("mg") or 0); last_ibu = e.get("ts")
    lim_apap = min(4000.0 if is_adult else 75.0*(weight_kg or 0), 4000.0)
    lim_ibu  = min(1200.0 if is_adult else 30.0*(weight_kg or 0), 1200.0)
    def _next(last_ts, h):
        if not last_ts: return None
        try:
            return (datetime.fromisoformat(last_ts) + timedelta(hours=h)).strftime("%H:%M")
        except Exception:
            return None
    return {
        "apap_total": int(apap_total), "ibu_total": int(ibu_total),
        "apap_limit": int(lim_apap), "ibu_limit": int(lim_ibu),
        "apap_next": _next(last_apap, 4), "ibu_next": _next(last_ibu, 6)
    }

def render_guard(profile: Dict[str,Any], labs: Dict[str,Any], care_entries: List[Dict[str,Any]]):
    age = int(profile.get("age", 18) if isinstance(profile, dict) else 18)
    is_adult = age >= 18
    weight = float(profile.get("weight", 0) if isinstance(profile, dict) else 0)
    info = compute_guard(care_entries, weight, is_adult)
    st.caption(f"APAP 24h: {info['apap_total']}/{info['apap_limit']} mg · 다음가능: {info['apap_next'] or '—'}")
    st.caption(f"IBU 24h: {info['ibu_total']}/{info['ibu_limit']} mg · 다음가능: {info['ibu_next'] or '—'}")
    # safety
    plt = labs.get("PLT"); egfr = labs.get("eGFR")
    ast_v = labs.get("AST"); alt_v = labs.get("ALT")
    if isinstance(plt,(int,float)) and plt < 50000:
        st.error("IBU 금지: PLT < 50k")
    if egfr is not None and isinstance(egfr,(int,float)) and egfr < 60:
        st.warning("eGFR < 60: IBU 주의")
    if (isinstance(ast_v,(int,float)) and ast_v > 120) or (isinstance(alt_v,(int,float)) and alt_v > 120):
        st.warning("AST/ALT > 120: APAP 간기능 주의")
