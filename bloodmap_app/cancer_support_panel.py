
# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Dict, Any, Tuple
import streamlit as st

try:
    from peds_dose_override import acetaminophen_ml, ibuprofen_ml  # type: ignore
except Exception:
    try:
        from peds_dose import acetaminophen_ml, ibuprofen_ml  # type: ignore
    except Exception:
        acetaminophen_ml = ibuprofen_ml = None  # type: ignore

def _to_float(x, default=None):
    try: return float(x)
    except Exception: return default

def _adult_apap_mg(w: float|None, mg_per_kg: float = 12.5) -> Tuple[int, float]:
    ww = _to_float(w, None) or 60.0
    mg = min(1000.0, max(325.0, ww*mg_per_kg))
    return int(round(mg)), ww

def _adult_ibu_mg(w: float|None, mg_per_kg: float = 7.5) -> Tuple[int, float]:
    ww = _to_float(w, None) or 60.0
    mg = min(400.0, max(200.0, ww*mg_per_kg))
    return int(round(mg)), ww

def _lab_warns(labs: Dict[str, Any]|None) -> list[str]:
    warns = []
    if not isinstance(labs, dict): return warns
    def num(k):
        v = labs.get(k)
        try: return float(v)
        except Exception: return None
    plt_v, cr_v, ast_v, alt_v = num("PLT"), num("Cr"), num("AST"), num("ALT")
    if plt_v is not None and plt_v < 50_000:
        warns.append("혈소판 < 50k → **이부프로펜(IBU) 지양**(출혈 위험). 아세트아미노펜(APAP) 우선 논의.")
    if cr_v is not None and cr_v >= 1.5:
        warns.append("크레아티닌 상승 → **이부프로펜(IBU)** 신장 부담 주의.")
    if (ast_v and ast_v >= 120) or (alt_v and alt_v >= 120):
        warns.append("간효소 3배↑ 추정 → **아세트아미노펜(APAP) 총량 제한**(하루 2–3g) 상담.")
    return warns

def render_onco_support(labs: Dict[str, Any]|None = None, storage_key: str = "onco_support") -> Dict[str, Any]:
    st.markdown("### 🧯 암환자 — 증상/해열제 보조 패널 (mL 표준)")

    # 기본값 (일반 사용자용)
    apap_c, ibu_c = 160.0, 100.0
    apap_mgkg, ibu_mgkg = 12.5, 7.5

    # 전문가만 설정 노출
    with st.expander("⚙️ 전문가 설정(약사/의료진)", expanded=False):
        expert = st.checkbox("mg/kg·농도 직접 조정", value=False, key=f"{storage_key}_expert")
        if expert:
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                apap_c = st.number_input("아세트아미노펜(APAP) 농도 (mg/5mL)", 80.0, 500.0, value=160.0, step=10.0, key=f"{storage_key}_apap_c")
            with c2:
                ibu_c  = st.number_input("이부프로펜(IBU) 농도 (mg/5mL)",  50.0, 400.0, value=100.0, step=10.0, key=f"{storage_key}_ibu_c")
            with c3:
                apap_mgkg = st.number_input("아세트아미노펜(APAP) mg/kg", 8.0, 15.0, value=12.5, step=0.5, key=f"{storage_key}_apap_mgkg")
            with c4:
                ibu_mgkg  = st.number_input("이부프로펜(IBU) mg/kg",  5.0, 10.0, value=7.5, step=0.5, key=f"{storage_key}_ibu_mgkg")

    left, right = st.columns([0.35, 0.65])
    with left:
        who = st.radio("대상", ["성인","소아"], horizontal=True, key=f"{storage_key}_who")
    with right:
        diarrhea = st.selectbox("설사(횟수/일)", ["없음","1~3회","4~6회","7회 이상"], key=f"{storage_key}_diarrhea")

    out: Dict[str, Any] = {"who": who, "diarrhea": diarrhea}

    for w in _lab_warns(labs or {}):
        st.error("⚠️ " + w)
    st.divider()

    if who == "소아":
        c1, c2 = st.columns(2)
        with c1: age_m = st.number_input("나이(개월)", min_value=0, step=1, key=f"{storage_key}_age")
        with c2: weight = st.number_input("체중(kg)", min_value=0.0, step=0.1, key=f"{storage_key}_wt")
        if callable(acetaminophen_ml) and callable(ibuprofen_ml):
            apap_ml, meta1 = acetaminophen_ml(age_m, weight or None)
            ibu_ml,  meta2 = ibuprofen_ml(age_m, weight or None)
            used_w = float(weight or meta1.get("weight_used", meta2.get("weight_used", 0.0)))
            d1, d2, d3 = st.columns(3)
            with d1:
                st.metric("아세트아미노펜(APAP) (1회분)", f"{apap_ml} mL")
                st.caption(f"≒ {round(apap_ml*apap_c/5):d} mg · 간격 4–6h")
            with d2:
                st.metric("이부프로펜(IBU) (1회분)", f"{ibu_ml} mL")
                st.caption(f"≒ {round(ibu_ml*ibu_c/5):d} mg · 간격 6–8h")
            with d3:
                st.metric("계산 체중", f"{used_w:.1f} kg")
            out.update({"apap": f"{apap_ml} mL", "ibu": f"{ibu_ml} mL", "age_m": int(age_m), "weight": used_w})
        else:
            st.warning("소아 용량 모듈이 없습니다.")

    else:
        weight = st.number_input("체중(kg)", min_value=0.0, step=0.5, value=60.0, key=f"{storage_key}_wt_adult")
        apap_mg, wA = _adult_apap_mg(weight or None, apap_mgkg)
        ibu_mg,  wI = _adult_ibu_mg(weight or None,  ibu_mgkg)
        apap_ml = round(apap_mg * 5.0 / apap_c, 1)
        ibu_ml  = round(ibu_mg  * 5.0 / ibu_c, 1)

        c1, c2 = st.columns(2)
        with c1:
            st.metric("아세트아미노펜(APAP) (1회분)", f"{apap_ml} mL")
            st.caption(f"≒ {apap_mg} mg · 간격 4–6h · 1일 최대 3000 mg")
        with c2:
            st.metric("이부프로펜(IBU) (1회분)", f"{ibu_ml} mL")
            st.caption(f"≒ {ibu_mg} mg · 간격 6–8h · 1일 최대 1200 mg(일반)")
        out.update({"apap": f"{apap_ml} mL", "ibu": f"{ibu_ml} mL", "weight": float(wA)})

    st.caption("※ 실제 복용은 반드시 **주치의**와 상의하세요.")
    return out
