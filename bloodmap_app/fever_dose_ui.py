
# -*- coding: utf-8 -*-
"""
fever_dose_ui.py — 소아/성인 해열제 용량 패널 (나이·체중 기반 자동 계산 + 수동 덮어쓰기)
- 외부 의존성 없음 (Streamlit만 필요)
- 기본 공식: APAP 10~15 mg/kg(기본 12.5), IBU 7~10 mg/kg(기본 7.5)
- 시럽 농도 기본값: APAP 160 mg/5mL, IBU 100 mg/5mL (국내 흔한 제형 기준)
"""
from __future__ import annotations
from typing import Optional, Tuple
import streamlit as st

# ---- 기본 파라미터 ----
ACETAMINOPHEN_MG_PER_5ML = 160.0
IBUPROFEN_MG_PER_5ML     = 100.0
ACETAMINOPHEN_MG_PER_KG  = 12.5
IBUPROFEN_MG_PER_KG      = 7.5

def estimate_weight_from_age_months(age_months: float) -> float:
    """간단 추정: <12개월: 3.3 + 0.5*개월, >=12개월: 2*세 + 8"""
    try:
        a = float(age_months)
    except Exception:
        return 3.3
    if a <= 0: return 3.3
    if a < 12: return 3.3 + 0.5*a
    years = a / 12.0
    return 2.0*years + 8.0

def _ml_from_mg(weight_kg: float, mg_per_kg: float, syrup_mg_per_5ml: float) -> float:
    dose_mg = max(0.0, float(weight_kg)) * max(0.0, float(mg_per_kg))
    ml = dose_mg * 5.0 / max(1e-6, float(syrup_mg_per_5ml))
    return round(ml, 1)

def calc_apap_ml(age_months: float, weight_kg: Optional[float], mg_per_kg: float, syrup_mg_per_5ml: float) -> Tuple[float, float]:
    w = weight_kg if (weight_kg and weight_kg > 0) else estimate_weight_from_age_months(age_months or 0)
    return _ml_from_mg(w, mg_per_kg, syrup_mg_per_5ml), round(w, 1)

def calc_ibu_ml(age_months: float, weight_kg: Optional[float], mg_per_kg: float, syrup_mg_per_5ml: float) -> Tuple[float, float]:
    w = weight_kg if (weight_kg and weight_kg > 0) else estimate_weight_from_age_months(age_months or 0)
    return _ml_from_mg(w, mg_per_kg, syrup_mg_per_5ml), round(w, 1)

def render_fever_panel(storage_key: str = "fever_panel", default_age_m: int = 36, default_weight: float = 15.0) -> dict:
    """
    반환: {'apap_ml': float, 'ibu_ml': float, 'weight_kg': float, 'age_m': int}
    - st.session_state[storage_key] 에도 같은 dict 저장
    """
    st.markdown("### ⏱️ 해열제 24시간 시간표 — **나이/체중 기반 자동 계산**")
    c0,c1,c2,c3 = st.columns([0.9,0.8,1,1])
    with c0: age_m = st.number_input("나이(개월)", min_value=0, step=1, value=int(default_age_m), key=f"{storage_key}_age")
    with c1: weight = st.number_input("체중(kg)", min_value=0.0, step=0.1, value=float(default_weight), key=f"{storage_key}_wt")
    with c2: apap_mgkg = st.number_input("APAP mg/kg", min_value=8.0, max_value=15.0, step=0.5, value=ACETAMINOPHEN_MG_PER_KG, key=f"{storage_key}_apap_mgkg")
    with c3: ibu_mgkg  = st.number_input("IBU mg/kg",  min_value=5.0, max_value=10.0, step=0.5, value=IBUPROFEN_MG_PER_KG,     key=f"{storage_key}_ibu_mgkg")

    d0,d1 = st.columns(2)
    with d0: apap_syr = st.number_input("APAP 농도 (mg/5mL)", min_value=80.0, max_value=500.0, step=10.0, value=ACETAMINOPHEN_MG_PER_5ML, key=f"{storage_key}_apap_c")
    with d1: ibu_syr  = st.number_input("IBU 농도 (mg/5mL)",  min_value=50.0, max_value=400.0, step=10.0, value=IBUPROFEN_MG_PER_5ML,     key=f"{storage_key}_ibu_c")

    apap_ml, w1 = calc_apap_ml(age_m, weight or None, apap_mgkg, apap_syr)
    ibu_ml,  w2 = calc_ibu_ml(age_m, weight or None, ibu_mgkg,  ibu_syr)

    # 수동 덮어쓰기 옵션
    st.toggle("수동으로 ml 값을 직접 입력", value=False, key=f"{storage_key}_manual")
    if st.session_state.get(f"{storage_key}_manual"):
        apap_ml = st.number_input("아세트아미노펜 수동(ml)", min_value=0.0, step=0.1, value=apap_ml, key=f"{storage_key}_apap_manual")
        ibu_ml  = st.number_input("이부프로펜 수동(ml)",    min_value=0.0, step=0.1, value=ibu_ml,  key=f"{storage_key}_ibu_manual")

    cA, cB, cC = st.columns(3)
    with cA:
        st.metric("1회분 — 아세트아미노펜", f"{apap_ml} ml")
        st.caption("간격 4–6h, 최대 4회/일 (성분 중복 금지)")
    with cB:
        st.metric("1회분 — 이부프로펜", f"{ibu_ml} ml")
        st.caption("간격 6–8h, 위장 자극 시 식후")
    with cC:
        st.metric("추정/입력 체중", f"{w1 if (weight or 0)<=0 else weight} kg")
        st.caption("※ 체중 입력 시 추정값 대신 입력값 사용")

    out = {"apap_ml": float(apap_ml), "ibu_ml": float(ibu_ml), "weight_kg": float(weight or w1), "age_m": int(age_m)}
    st.session_state[storage_key] = out
    return out
