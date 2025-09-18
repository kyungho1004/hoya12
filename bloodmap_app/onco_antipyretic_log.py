
# -*- coding: utf-8 -*-
"""
onco_antipyretic_log.py — 해열제 복용 기록 (mL 통일) — Lite UX
- 누구나 쉽게: 1) 대상 선택 → 2) 체중/나이 입력 → 3) 시간 선택 → 4) '기록' 버튼
- 기본값/고급설정 분리: 농도·mg/kg는 숨기고 필요할 때만 펼침
- 표시는 mL, 캡션으로 mg 환산 보조
- 기존 API 유지: render_onco_antipyretic_log(storage_key=...)
"""
from __future__ import annotations
from typing import Dict, Any, Tuple
import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta

# Pediatric dosing (override first)
try:
    from peds_dose_override import acetaminophen_ml, ibuprofen_ml  # type: ignore
except Exception:
    def _w_from_age(age_m: float) -> float:
        if age_m <= 0: return 3.3
        if age_m < 12: return 3.3 + 0.5*age_m
        return (age_m/12.0)*2.0 + 8.0
    def acetaminophen_ml(age_m: float, weight_kg: float|None) -> Tuple[float, Dict[str, Any]]:
        w = weight_kg if (weight_kg and weight_kg>0) else _w_from_age(age_m or 0)
        mgkg, c = 12.5, 160.0
        ml = round(w*mgkg*5.0/c, 1)
        return ml, {"weight_used": round(w,1)}
    def ibuprofen_ml(age_m: float, weight_kg: float|None) -> Tuple[float, Dict[str, Any]]:
        w = weight_kg if (weight_kg and weight_kg>0) else _w_from_age(age_m or 0)
        mgkg, c = 7.5, 100.0
        ml = round(w*mgkg*5.0/c, 1)
        return ml, {"weight_used": round(w,1)}

# Helpers
def _kst_now(): return datetime.now(timezone(timedelta(hours=9)))
def _ensure_df(key: str) -> pd.DataFrame:
    df = st.session_state.get(key)
    if isinstance(df, pd.DataFrame): return df.copy()
    return pd.DataFrame(columns=["KST_time","Who","Age_m","Weight_kg","Diarrhea","Agent","Dose_mL","Dose_meta","Note"])
def _save_df(key: str, df: pd.DataFrame): st.session_state[key] = df

def render_onco_antipyretic_log(storage_key: str = "onco_antipyretic_log"):
    st.markdown("## 🌡️ 해열제 복용 기록 (mL) — 한국시간")

    # ── STEP 1. 대상/증상 ─────────────────────────────────────────────
    c1, c2, c3 = st.columns([0.28, 0.28, 0.44])
    with c1: who = st.radio("대상", ["성인","소아"], horizontal=True, key=f"{storage_key}_who")
    with c2: diarrhea = st.selectbox("설사(횟수/일)", ["없음","1~3회","4~6회","7회 이상"], key=f"{storage_key}_diarrhea")
    with c3: st.caption(f"현재 한국시간: **{_kst_now().strftime('%Y-%m-%d %H:%M')} KST**")

    # ── STEP 2. 기본 입력 ─────────────────────────────────────────────
    if who == "소아":
        a1, a2, a3 = st.columns([0.25,0.25,0.5])
        with a1: age_m = st.number_input("나이(개월)", min_value=0, step=1, key=f"{storage_key}_age")
        with a2: weight = st.number_input("체중(kg)", min_value=0.0, step=0.1, key=f"{storage_key}_wt")
    else:
        age_m = None
        a1, a2 = st.columns([0.25,0.75])
        with a1: weight = st.number_input("체중(kg)", min_value=0.0, step=0.5, value=60.0, key=f"{storage_key}_wt_adult")

    # ── STEP 3. 복용 시각(한국시간) ────────────────────────────────────
    t1, t2, t3 = st.columns([0.33,0.33,0.34])
    with t1: d = st.date_input("복용 날짜", value=_kst_now().date(), key=f"{storage_key}_date")
    with t2: t = st.time_input("복용 시각", value=_kst_now().time().replace(second=0, microsecond=0), key=f"{storage_key}_time")
    with t3: note = st.text_input("비고/메모", key=f"{storage_key}_note")

    # ── 고급 설정 (필요할 때만) ────────────────────────────────────────
    with st.expander("⚙️ 고급 설정 (농도·mg/kg 조절)", expanded=False):
        s1, s2, s3, s4 = st.columns(4)
        with s1: apap_c = st.number_input("APAP 농도 (mg/5mL)", min_value=80.0, max_value=500.0, step=10.0, value=160.0, key=f"{storage_key}_apap_c")
        with s2: ibu_c  = st.number_input("IBU 농도 (mg/5mL)",  min_value=50.0, max_value=400.0, step=10.0, value=100.0, key=f"{storage_key}_ibu_c")
        with s3: apap_mgkg = st.number_input("APAP mg/kg", min_value=8.0, max_value=15.0, step=0.5, value=12.5, key=f"{storage_key}_apap_mgkg")
        with s4: ibu_mgkg  = st.number_input("IBU mg/kg",  min_value=5.0, max_value=10.0, step=0.5, value=7.5,  key=f"{storage_key}_ibu_mgkg")

    # ── 용량 계산 (mL) ────────────────────────────────────────────────
    if who == "소아":
        apap_ml, m1 = acetaminophen_ml(age_m, weight or None)
        ibu_ml,  m2 = ibuprofen_ml(age_m, weight or None)
        used_w = float(weight or m1.get("weight_used") or m2.get("weight_used") or 0.0)
        apap_mg = round(apap_ml*apap_c/5); ibu_mg = round(ibu_ml*ibu_c/5)
    else:
        # 성인: mg/kg → mL 변환
        mg_apap = min(1000.0, max(325.0, (weight or 60.0)*apap_mgkg))
        mg_ibu  = min(400.0, max(200.0,  (weight or 60.0)*ibu_mgkg))
        apap_ml = round(mg_apap * 5.0 / apap_c, 1)
        ibu_ml  = round(mg_ibu  * 5.0 / ibu_c, 1)
        used_w = float(weight or 60.0)
        apap_mg = int(round(mg_apap)); ibu_mg = int(round(mg_ibu))

    # ── STEP 4. 결과 카드 + 원클릭 기록 ───────────────────────────────
    st.markdown("### ✅ 오늘 복용 권장 (mL 기준)")
    cA, cB = st.columns(2)
    with cA:
        st.metric("아세트아미노펜(APAP) 1회분", f"{apap_ml} mL")
        st.caption(f"≈ {apap_mg} mg · 간격 4–6h · 하루 최대 3000 mg")
        if st.button("➕ APAP 기록", use_container_width=True, key=f"{storage_key}_add_apap"):
            dt = datetime.combine(d, t).replace(tzinfo=timezone(timedelta(hours=9)))
            df = _ensure_df(storage_key)
            row = {"KST_time": dt.strftime("%Y-%m-%d %H:%M"), "Who": who, "Age_m": (int(age_m) if age_m is not None else ""),
                   "Weight_kg": round(used_w,1), "Diarrhea": diarrhea, "Agent": "APAP",
                   "Dose_mL": float(apap_ml), "Dose_meta": f"{apap_mg} mg @ {apap_c} mg/5mL", "Note": note or ""}
            _save_df(storage_key, pd.concat([df, pd.DataFrame([row])], ignore_index=True))
            st.success("APAP 기록됨.")
    with cB:
        st.metric("이부프로펜(IBU) 1회분", f"{ibu_ml} mL")
        st.caption(f"≈ {ibu_mg} mg · 간격 6–8h · 하루 최대 1200 mg(일반)")
        if st.button("➕ IBU 기록", use_container_width=True, key=f"{storage_key}_add_ibu"):
            dt = datetime.combine(d, t).replace(tzinfo=timezone(timedelta(hours=9)))
            df = _ensure_df(storage_key)
            row = {"KST_time": dt.strftime("%Y-%m-%d %H:%M"), "Who": who, "Age_m": (int(age_m) if age_m is not None else ""),
                   "Weight_kg": round(used_w,1), "Diarrhea": diarrhea, "Agent": "IBU",
                   "Dose_mL": float(ibu_ml), "Dose_meta": f"{ibu_mg} mg @ {ibu_c} mg/5mL", "Note": note or ""}
            _save_df(storage_key, pd.concat([df, pd.DataFrame([row])], ignore_index=True))
            st.success("IBU 기록됨.")

    # ── 기록 테이블 & 내보내기 ───────────────────────────────────────
    st.divider()
    st.markdown("#### 📒 오늘의 기록")
    df = _ensure_df(storage_key)
    if df.empty:
        st.info("아직 기록이 없습니다. 위의 '기록' 버튼을 눌러 추가하세요.")
    else:
        st.dataframe(df, use_container_width=True, height=240)
        st.download_button("⬇️ CSV 저장", data=df.to_csv(index=False).encode("utf-8"),
                           file_name="antipyretic_log_kst.csv", use_container_width=True)
        if st.button("🧹 전체 삭제", use_container_width=True, key=f"{storage_key}_clear"):
            _save_df(storage_key, _ensure_df(storage_key).iloc[0:0])
            st.warning("모든 기록을 삭제했습니다.")
