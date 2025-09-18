
# -*- coding: utf-8 -*-
"""
cancer_support_panel.py — 암환자 보조 패널 (해열제/설사) — v2 UI
- 성인/소아 지원 (동일 함수명 유지: render_onco_support)
- 가독성 개선: 큰 메트릭, 정제 개수 추천(성인), 경고 배지, 도움말
- 기존 앱과 완전 호환 (임포트/호출 방식 그대로)
"""
from __future__ import annotations
from typing import Dict, Any, Optional, Tuple
import math
import streamlit as st

# Pediatric calc (override first)
try:
    from peds_dose_override import acetaminophen_ml, ibuprofen_ml  # type: ignore
except Exception:
    try:
        from peds_dose import acetaminophen_ml, ibuprofen_ml  # type: ignore
    except Exception:
        acetaminophen_ml = ibuprofen_ml = None  # type: ignore

# ---------------- 유틸 ----------------
def _to_float(x, default=None):
    try:
        return float(x)
    except Exception:
        return default

def _pill_recommend(mg: int, options: list[int]) -> str:
    if not options: 
        return ""
    # 가까운 정제용량으로 안내(반정 고려: 1/2만 허용)
    best = min(options, key=lambda o: abs(o - mg))
    # 추천 정제 개수 (반정 포함)
    counts = []
    for o in options:
        # 0.5정까지 표시 (예: 325mg 1정, 500mg 0.5정 등은 혼란 → 기본은 1정 단위 우선)
        n_full = round(mg / o)
        if n_full <= 0:
            continue
        counts.append((o, n_full, abs(mg - n_full*o)))
        # 반정은 일부 제형만 가능하니 캡션으로만 참고 표시
    if counts:
        counts.sort(key=lambda t: (t[2], t[1]))
        o, n, _ = counts[0]
        return f"{o} mg × {n}정 (≈ {o*n} mg)"
    return f"{best} mg 권장"

def _adult_apap_mg(weight_kg: float|None, mg_per_kg: float = 12.5) -> Tuple[int, Dict[str, Any]]:
    """성인 APAP: 10–15 mg/kg, 1회 최대 1000 mg, 1일 최대 3000 mg(보수)"""
    w = _to_float(weight_kg, None)
    base = int(round((w or 60.0) * mg_per_kg))  # weight 없으면 60kg 가정
    mg = max(325, min(1000, base))
    return mg, {"mg_per_kg": mg_per_kg, "cap_mg": 1000, "max_day": 3000, "weight_used": w or 60.0}

def _adult_ibu_mg(weight_kg: float|None, mg_per_kg: float = 7.5) -> Tuple[int, Dict[str, Any]]:
    """성인 IBU: 5–10 mg/kg, 1회 200–400 mg, 1일 최대 1200 mg(일반의약품 기준)"""
    w = _to_float(weight_kg, None)
    base = int(round((w or 60.0) * mg_per_kg))
    mg = min(400, max(200, base))
    return mg, {"mg_per_kg": mg_per_kg, "cap_mg": 400, "max_day": 1200, "weight_used": w or 60.0}

def _lab_warns(labs: Dict[str, Any]|None) -> list[str]:
    warns = []
    if not isinstance(labs, dict):
        return warns
    def get_num(k): 
        v = labs.get(k)
        return _to_float(v, None)
    plt_v = get_num("PLT")
    cr_v  = get_num("Cr")
    ast_v = get_num("AST")
    alt_v = get_num("ALT")
    if plt_v is not None and plt_v < 50_000:
        warns.append("혈소판 **< 50k** → 이부프로펜/NSAID 지양(출혈 위험). APAP 우선 논의.")
    if cr_v is not None and cr_v >= 1.5:
        warns.append("크레아티닌 상승 → 이부프로펜 신장 부하 주의.")
    if (ast_v and ast_v >= 120) or (alt_v and alt_v >= 120):
        warns.append("간효소 3배↑ 추정 → 아세트아미노펜 총량 제한(하루 2–3g 내) 상담.")
    return warns

# ---------------- 메인 패널 ----------------
def render_onco_support(labs: Dict[str, Any]|None = None, storage_key: str = "onco_support") -> Dict[str, Any]:
    st.markdown("### 🧯 암환자 — 증상/해열제 보조 패널")

    # 상단 옵션
    left, right = st.columns([0.35, 0.65])
    with left:
        who = st.radio("대상", ["성인","소아"], horizontal=True, key=f"{storage_key}_who")
    with right:
        diarrhea = st.selectbox("설사(횟수/일)", ["없음","1~3회","4~6회","7회 이상"], key=f"{storage_key}_diarrhea")

    result: Dict[str, Any] = {"who": who, "diarrhea": diarrhea}

    warns = _lab_warns(labs or {})
    if warns:
        for w in warns:
            st.error("⚠️ " + w)

    st.divider()

    if who == "소아":
        c1, c2 = st.columns([0.5,0.5])
        with c1:
            age_m = st.number_input("나이(개월)", min_value=0, step=1, key=f"{storage_key}_age")
        with c2:
            weight = st.number_input("체중(kg)", min_value=0.0, step=0.1, key=f"{storage_key}_wt")

        if callable(acetaminophen_ml) and callable(ibuprofen_ml):
            apap_ml, meta1 = acetaminophen_ml(age_m, weight or None)
            ibu_ml, meta2  = ibuprofen_ml(age_m, weight or None)

            d1, d2, d3 = st.columns([0.33,0.33,0.34])
            with d1:
                st.metric("아세트아미노펜 (1회분)", f"{apap_ml} mL")
                st.caption("간격 4–6h · 최대 4회/일")
            with d2:
                st.metric("이부프로펜 (1회분)", f"{ibu_ml} mL")
                st.caption("간격 6–8h")
            with d3:
                st.metric("계산 체중", f"{meta1.get('weight_used', meta2.get('weight_used','?'))} kg")
                st.caption("※ 체중 입력 시 추정값 대신 입력값 사용")

            result.update({
                "apap": f"{apap_ml} mL",
                "ibu": f"{ibu_ml} mL",
                "age_m": int(age_m),
                "weight": float(weight or meta1.get("weight_used", 0.0)),
            })
        else:
            st.warning("소아 용량 모듈이 로드되지 않았습니다.")

    else:
        # 성인: 초기 체중 기본 60kg 제안 (이전 값이 너무 낮으면 보정)
        default_w = st.session_state.get(f"{storage_key}_wt_adult", 60.0)
        if default_w < 30.0:
            default_w = 60.0
        weight = st.number_input("체중(kg)", min_value=0.0, step=0.5, value=float(default_w), key=f"{storage_key}_wt_adult")

        apap_mg, metaA = _adult_apap_mg(weight or None)
        ibu_mg,  metaI = _adult_ibu_mg(weight or None)

        # 메트릭 + 정제 권장 병행 표시
        c1, c2 = st.columns(2)
        with c1:
            st.metric("아세트아미노펜 (1회분)", f"{apap_mg} mg")
            st.caption(f"간격 4–6h · 1일 최대 {metaA['max_day']} mg")
            st.caption("💡 권장: " + _pill_recommend(apap_mg, [325, 500]))
        with c2:
            st.metric("이부프로펜 (1회분)", f"{ibu_mg} mg")
            st.caption(f"간격 6–8h · 1일 최대 {metaI['max_day']} mg(일반 기준)")
            st.caption("💡 권장: " + _pill_recommend(ibu_mg, [200, 400]))

        result.update({
            "apap": f"{apap_mg} mg",
            "ibu": f"{ibu_mg} mg",
            "weight": float(metaA['weight_used']),
        })

    st.caption("※ 실제 복용은 반드시 **주치의**와 상의하세요.")
    return result
