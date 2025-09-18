
# -*- coding: utf-8 -*-
"""
cancer_support_panel.py — 암환자 보조 패널 (해열제/설사)
- 성인/소아 모두 지원
- 소아: peds_dose_override(없으면 peds_dose)로 ml 자동 계산
- 성인: 체중 기반 mg 자동 계산(상한치 적용)
- 안전 가드: PLT, Cr, AST/ALT를 참고해 경고 표기(가능한 경우)
"""
from __future__ import annotations
from typing import Dict, Any, Optional, Tuple
import streamlit as st

# Pediatric calc (override first)
try:
    from peds_dose_override import acetaminophen_ml, ibuprofen_ml  # type: ignore
except Exception:
    try:
        from peds_dose import acetaminophen_ml, ibuprofen_ml  # type: ignore
    except Exception:
        acetaminophen_ml = ibuprofen_ml = None  # type: ignore

def _to_float(x, default=None):
    try:
        return float(x)
    except Exception:
        return default

def _adult_apap_mg(weight_kg: float|None, mg_per_kg: float = 12.5) -> Tuple[int, Dict[str, Any]]:
    """성인 APAP: 10–15 mg/kg, 1회 최대 1000 mg, 1일 최대 3000–4000 mg (보수적으로 3000 권장)"""
    w = _to_float(weight_kg, None)
    base = int(round((w or 50.0) * mg_per_kg))  # weight 없으면 50kg 가정
    mg = max(325, min(1000, base))
    return mg, {"mg_per_kg": mg_per_kg, "cap_mg": 1000, "max_day": 3000, "weight_used": w or 50.0}

def _adult_ibu_mg(weight_kg: float|None, mg_per_kg: float = 7.5) -> Tuple[int, Dict[str, Any]]:
    """성인 IBU: 5–10 mg/kg, 1회 200–400 mg, 1일 최대 1200 mg(일반의약품 기준)"""
    w = _to_float(weight_kg, None)
    base = int(round((w or 50.0) * mg_per_kg))
    mg = min(400, max(200, base))
    return mg, {"mg_per_kg": mg_per_kg, "cap_mg": 400, "max_day": 1200, "weight_used": w or 50.0}

def _lab_warns(labs: Dict[str, Any]|None) -> list[str]:
    warns = []
    if not isinstance(labs, dict):
        return warns
    plt_v = _to_float(labs.get("PLT"), None)
    cr_v  = _to_float(labs.get("Cr"), None)
    ast_v = _to_float(labs.get("AST"), None)
    alt_v = _to_float(labs.get("ALT"), None)
    if plt_v is not None and plt_v < 50_000:
        warns.append("혈소판 **< 50k**: 이부프로펜/NSAID **지양** (출혈 위험). APAP 우선 논의.")
    if cr_v is not None and cr_v >= 1.5:
        warns.append("크레아티닌 상승: **이부프로펜** 신장 부하 주의.")
    if (ast_v and ast_v >= 3*40) or (alt_v and alt_v >= 3*40):
        warns.append("간효소 3배↑ 추정: **아세트아미노펜 총량 제한**(하루 2–3g 이내) 상담.")
    return warns

def render_onco_support(labs: Dict[str, Any]|None = None, storage_key: str = "onco_support") -> Dict[str, Any]:
    st.markdown("#### 🧯 암환자 — 증상/해열제 보조 패널")
    who = st.radio("대상", ["성인","소아"], horizontal=True, key=f"{storage_key}_who")
    diarrhea = st.selectbox("설사(횟수/일)", ["없음","1~3회","4~6회","7회 이상"], key=f"{storage_key}_diarrhea")

    result: Dict[str, Any] = {"who": who, "diarrhea": diarrhea}

    if who == "소아":
        age_m = st.number_input("나이(개월)", min_value=0, step=1, key=f"{storage_key}_age")
        weight = st.number_input("체중(kg)", min_value=0.0, step=0.1, key=f"{storage_key}_wt")
        if callable(acetaminophen_ml) and callable(ibuprofen_ml):
            apap_ml, meta1 = acetaminophen_ml(age_m, weight or None)
            ibu_ml, meta2  = ibuprofen_ml(age_m, weight or None)
            c1,c2 = st.columns(2)
            with c1:
                st.metric("아세트아미노펜 (1회분)", f"{apap_ml} mL")
                st.caption("간격 4–6h, 최대 4회/일")
            with c2:
                st.metric("이부프로펜 (1회분)", f"{ibu_ml} mL")
                st.caption("간격 6–8h")
            result.update({"apap": f"{apap_ml} mL", "ibu": f"{ibu_ml} mL", "age_m": int(age_m), "weight": float(weight or meta1.get("weight_used", 0))})
        else:
            st.warning("소아 용량 모듈이 로드되지 않았습니다.")
    else:
        weight = st.number_input("체중(kg)", min_value=0.0, step=0.5, key=f"{storage_key}_wt_adult")
        apap_mg, metaA = _adult_apap_mg(weight or None)
        ibu_mg,  metaI = _adult_ibu_mg(weight or None)
        c1,c2 = st.columns(2)
        with c1:
            st.metric("아세트아미노펜 (1회분)", f"{apap_mg} mg")
            st.caption(f"간격 4–6h · 1일 최대 {metaA['max_day']} mg")
        with c2:
            st.metric("이부프로펜 (1회분)", f"{ibu_mg} mg")
            st.caption(f"간격 6–8h · 1일 최대 {metaI['max_day']} mg(일반 기준)")
        result.update({"apap": f"{apap_mg} mg", "ibu": f"{ibu_mg} mg", "weight": float(metaA['weight_used'])})

    warns = _lab_warns(labs or {})
    for w in warns:
        st.error(w)
    if not warns:
        st.caption("※ 실제 복용은 반드시 **주치의**와 상의하세요.")

    return result
