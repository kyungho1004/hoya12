# -*- coding: utf-8 -*-
from __future__ import annotations
import streamlit as st
from typing import List, Dict
from drug_db import display_label

def results_only_after_analyze(st_mod) -> bool:
    return bool(st_mod.session_state.get("analyzed"))

def render_adverse_effects(st_mod, keys: List[str], db: Dict[str, Dict] = None):
    if not keys:
        return
    from drug_db import DRUG_DB
    ref = db if isinstance(db, dict) else DRUG_DB
    for k in keys:
        entry = ref.get(k) or {}
        lab = display_label(k, ref)
        moa = entry.get("moa","")
        ae  = entry.get("ae","")
        st_mod.markdown(f"- **{lab}** — {moa}")
        if ae:
            st_mod.caption(f"  ↳ 부작용/주의: {ae}")

def collect_top_ae_alerts(keys: List[str], db=None) -> List[str]:
    alerts = []
    from drug_db import DRUG_DB
    ref = db if isinstance(db, dict) else DRUG_DB
    for k in keys:
        e = ref.get(k) or {}
        ae = e.get("ae","")
        if "분화증후군" in ae:
            alerts.append("🚨 APL 분화증후군(ATRA/ATO) 주의")
        if "신경독성" in ae or "QT" in ae:
            alerts.append("⚠️ 신경/QT 등 특이 부작용 포함")
    # dedupe
    dedup = []
    for a in alerts:
        if a not in dedup:
            dedup.append(a)
    return dedup[:5]
