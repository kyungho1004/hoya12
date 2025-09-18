
# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Dict, Any, Tuple
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone

# Pediatric override
try:
    from peds_dose_override import acetaminophen_ml, ibuprofen_ml  # type: ignore
except Exception:
    def _w_from_age(age_m: float) -> float:
        if age_m <= 0: return 3.3
        if age_m < 12: return 3.3 + 0.5*age_m
        return (age_m/12.0)*2.0 + 8.0
    def acetaminophen_ml(age_m: float, weight_kg: float|None):
        w = weight_kg if (weight_kg and weight_kg>0) else _w_from_age(age_m or 0)
        mgkg, c = 12.5, 160.0
        ml = round(w*mgkg*5.0/c, 1)
        return ml, {"weight_used": round(w,1)}
    def ibuprofen_ml(age_m: float, weight_kg: float|None):
        w = weight_kg if (weight_kg and weight_kg>0) else _w_from_age(age_m or 0)
        mgkg, c = 7.5, 100.0
        ml = round(w*mgkg*5.0/c, 1)
        return ml, {"weight_used": round(w,1)}

def _to_float(x, default=None):
    try: return float(x)
    except Exception: return default

def _adult_apap_ml(weight_kg: float|None, mg_per_kg: float, syrup_mg_per_5ml: float):
    w = _to_float(weight_kg, None) or 60.0
    mg = min(1000.0, max(325.0, w*mg_per_kg))
    ml = round(mg * 5.0 / max(1e-6, syrup_mg_per_5ml), 1)
    return ml, {"mg": int(round(mg)), "weight_used": w}

def _adult_ibu_ml(weight_kg: float|None, mg_per_kg: float, syrup_mg_per_5ml: float):
    w = _to_float(weight_kg, None) or 60.0
    mg = min(400.0, max(200.0, w*mg_per_kg))
    ml = round(mg * 5.0 / max(1e-6, syrup_mg_per_5ml), 1)
    return ml, {"mg": int(round(mg)), "weight_used": w}

def _kst_now():
    return datetime.now(timezone(timedelta(hours=9)))

def _ensure_df(key: str) -> pd.DataFrame:
    df = st.session_state.get(key)
    if isinstance(df, pd.DataFrame):
        return df.copy()
    cols = ["KST_time","Who","Age_m","Weight_kg","Diarrhea","Agent","Dose_mL","Dose_meta","Note"]
    return pd.DataFrame(columns=cols)

def _save_df(key: str, df: pd.DataFrame):
    st.session_state[key] = df

def render_onco_antipyretic_log(storage_key: str = "onco_antipyretic_log") -> pd.DataFrame:
    st.markdown("### 🌡️ 해열제 복용 기록 (mL 통일) — 한국시간")

    # 일반 사용자 기본값
    apap_c, ibu_c = 160.0, 100.0
    apap_mgkg, ibu_mgkg = 12.5, 7.5

    # 전문가만 노출
    with st.expander("⚙️ 전문가 설정(약사/의료진)", expanded=False):
        expert = st.checkbox("mg/kg·농도 직접 조정", value=False, key=f"{storage_key}_expert")
        if expert:
            cC1, cC2, cC3, cC4 = st.columns(4)
            with cC1:
                apap_c = st.number_input("아세트아미노펜(APAP) 농도 (mg/5mL)", 80.0, 500.0, value=160.0, step=10.0, key=f"{storage_key}_apap_c")
            with cC2:
                ibu_c  = st.number_input("이부프로펜(IBU) 농도 (mg/5mL)",  50.0, 400.0, value=100.0, step=10.0, key=f"{storage_key}_ibu_c")
            with cC3:
                apap_mgkg = st.number_input("아세트아미노펜(APAP) mg/kg", 8.0, 15.0, value=12.5, step=0.5, key=f"{storage_key}_apap_mgkg")
            with cC4:
                ibu_mgkg  = st.number_input("이부프로펜(IBU) mg/kg",  5.0, 10.0, value=7.5,  step=0.5, key=f"{storage_key}_ibu_mgkg")

    c0, c1, c2 = st.columns([0.25, 0.25, 0.5])
    with c0:
        who = st.radio("대상", ["성인","소아"], horizontal=True, key=f"{storage_key}_who")
    with c1:
        diarrhea = st.selectbox("설사(횟수/일)", ["없음","1~3회","4~6회","7회 이상"], key=f"{storage_key}_diarrhea")
    with c2:
        st.caption(f"현재 한국시간: **{_kst_now().strftime('%Y-%m-%d %H:%M:%S KST')}**")

    if who == "소아":
        a1, a2, _ = st.columns([0.25,0.25,0.5])
        with a1: age_m = st.number_input("나이(개월)", min_value=0, step=1, key=f"{storage_key}_age")
        with a2: weight = st.number_input("체중(kg)", min_value=0.0, step=0.1, key=f"{storage_key}_wt")
        apap_ml, meta1 = acetaminophen_ml(age_m, weight or None)
        ibu_ml,  meta2 = ibuprofen_ml(age_m, weight or None)
        used_w = float(weight or meta1.get("weight_used") or meta2.get("weight_used") or 0.0)
    else:
        a1, _ = st.columns([0.25,0.75])
        with a1:
            weight = st.number_input("체중(kg)", min_value=0.0, step=0.5, value=60.0, key=f"{storage_key}_wt_adult")
        age_m = None
        apap_ml, mA = _adult_apap_ml(weight or None, apap_mgkg, apap_c)
        ibu_ml,  mI = _adult_ibu_ml(weight or None,  ibu_mgkg, ibu_c)
        used_w = float(mA["weight_used"])

    # 입력 공통
    tcol1, tcol2, tcol3 = st.columns([0.33,0.33,0.34])
    with tcol1:
        date_pick = st.date_input("복용 날짜 (KST)", value=_kst_now().date(), key=f"{storage_key}_date")
    with tcol2:
        time_pick = st.time_input("복용 시각 (KST)", value=_kst_now().time().replace(second=0, microsecond=0), key=f"{storage_key}_time")
    with tcol3:
        note = st.text_input("비고/메모", key=f"{storage_key}_note")



# --- 간격/24시간 체크용 헬퍼 ---

    # --- 간격/24시간 체크 (함수 내부) ---
    def _parse_kst(dt_str: str):
        from datetime import datetime, timedelta, timezone
        try:
            return datetime.strptime(dt_str, "%Y-%m-%d %H:%M").replace(tzinfo=timezone(timedelta(hours=9)))
        except Exception:
            return None

    def _last_and_count(df, agent: str, ref_dt):
        if df is None or df.empty:
            return None, 0
        dfa = df[df["Agent"] == agent]
        if dfa.empty:
            return None, 0
        dfa = dfa.copy()
        dfa["__dt"] = dfa["KST_time"].apply(_parse_kst)
        dfa = dfa.dropna(subset=["__dt"])
        if dfa.empty:
            return None, 0
        last_dt = dfa["__dt"].max()
        cutoff = ref_dt - timedelta(hours=24)
        cnt_24h = (dfa["__dt"] >= cutoff).sum()
        return last_dt, int(cnt_24h)

    apap_min_h = 4
    ibu_min_h  = 6
    apap_max_per_24h = 4
    ibu_max_per_24h  = 4

    planned_dt = datetime.combine(date_pick, time_pick).replace(tzinfo=timezone(timedelta(hours=9)))

    df_now_for_check = _ensure_df(storage_key)
    apap_last, apap_24h = _last_and_count(df_now_for_check, "아세트아미노펜(APAP)", planned_dt)
    ibu_last,  ibu_24h  = _last_and_count(df_now_for_check, "이부프로펜(IBU)", planned_dt)

    warn_apap = ""
    warn_ibu = ""
    if apap_last:
        delta_h = (planned_dt - apap_last).total_seconds() / 3600.0
        if delta_h < apap_min_h:
            next_ok = apap_last + timedelta(hours=apap_min_h)
            warn_apap = f"아세트아미노펜(APAP) 마지막 복용으로부터 **{delta_h:.1f}시간** 경과. 최소 {apap_min_h}시간 간격 권장 → **{next_ok.strftime('%Y-%m-%d %H:%M KST')}** 이후 복용 권장."
    if apap_24h >= apap_max_per_24h:
        warn_apap = (warn_apap + " " if warn_apap else "") + f"최근 24시간 내 {apap_24h}회 기록됨(권장 최대 {apap_max_per_24h}회)."

    if ibu_last:
        delta_h = (planned_dt - ibu_last).total_seconds() / 3600.0
        if delta_h < ibu_min_h:
            next_ok = ibu_last + timedelta(hours=ibu_min_h)
            warn_ibu = f"이부프로펜(IBU) 마지막 복용으로부터 **{delta_h:.1f}시간** 경과. 최소 {ibu_min_h}시간 간격 권장 → **{next_ok.strftime('%Y-%m-%d %H:%M KST')}** 이후 복용 권장."
    if ibu_24h >= ibu_max_per_24h:
        warn_ibu = (warn_ibu + " " if warn_ibu else "") + f"최근 24시간 내 {ibu_24h}회 기록됨(권장 최대 {ibu_max_per_24h}회)."
    
    # 버튼
    b1, b2, b3, b4 = st.columns([0.22,0.22,0.22,0.34])
    def _add_row(agent: str, dose_ml: float, meta_label: str):
        kst_dt = datetime.combine(date_pick, time_pick).replace(tzinfo=timezone(timedelta(hours=9)))
        df_prev = _ensure_df(storage_key)
        row = {
            "KST_time": kst_dt.strftime("%Y-%m-%d %H:%M"),
            "Who": who, "Age_m": (int(age_m) if (age_m is not None) else ""),
            "Weight_kg": round(used_w, 1), "Diarrhea": diarrhea,
            "Agent": agent, "Dose_mL": float(dose_ml), "Dose_meta": meta_label,
            "Note": note or "",
        }
        df = pd.concat([df_prev, pd.DataFrame([row])], ignore_index=True)
        _save_df(storage_key, df)
        st.success(f"{agent} {dose_ml} mL 기록됨 ({row['KST_time']} KST).")
    with b1:
        if warn_apap:
            st.warning(warn_apap)
        if st.button("➕ 아세트아미노펜(APAP) 기록", key=f"{storage_key}_add_apap"):
            label = f"{apap_mgkg} mg/kg, {apap_c} mg/5mL"
            _add_row("아세트아미노펜(APAP)", apap_ml, label)
    with b2:
        if warn_ibu:
            st.warning(warn_ibu)
        if st.button("➕ 이부프로펜(IBU) 기록", key=f"{storage_key}_add_ibu"):
            label = f"{ibu_mgkg} mg/kg, {ibu_c} mg/5mL"
            _add_row("이부프로펜(IBU)", ibu_ml, label)
    with b3:
        if st.button("🧹 전체 삭제", key=f"{storage_key}_clear"):
            _save_df(storage_key, _ensure_df(storage_key).iloc[0:0])
            st.warning("모든 기록을 삭제했습니다.")
    with b4:
        df_now = _ensure_df(storage_key)
        if not df_now.empty:
            st.download_button("⬇️ CSV 내보내기", data=df_now.to_csv(index=False).encode("utf-8"),
                               file_name="antipyretic_log_kst.csv")

    df = _ensure_df(storage_key)
    if df.empty:
        st.info("아직 기록이 없습니다. 상단에서 용량을 확인하고 '기록' 버튼을 눌러 추가하세요.")
    else:
        st.dataframe(df, use_container_width=True, height=240)
    return df
