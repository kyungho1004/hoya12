
# -*- coding: utf-8 -*-
"""
antipyretic_schedule.py — 해열제 스케줄러 (아세트아미노펜/이부프로펜)
- 성인/소아: 나이(개월)·체중(kg) 기반 용량 자동 계산 (mL 표준, mg 캡션)
- 설사 모듈: 빈도 기록 + 간단 안내
- 기본은 "개별 추가"만 제공 → 사용자가 선택한 시간대만 목록에 표시
- (선택) 연속 스케줄 자동 생성은 expander 안에 보조 기능으로 제공
- 중복 방지: 같은 시각/같은 약물은 추가 안 함
"""
from __future__ import annotations
from typing import Dict, Any, Tuple
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone, date, time

# Pediatric calc 먼저 시도
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

def _adult_mg_to_ml(weight: float|None, mgkg: float, cap_low: float, cap_high: float, syrup_mg_per_5ml: float) -> Tuple[float, int, float]:
    w = _to_float(weight, None) or 60.0
    mg = min(cap_high, max(cap_low, w * mgkg))
    ml = round(mg * 5.0 / max(1e-6, syrup_mg_per_5ml), 1)
    return ml, int(round(mg)), w

def _kst_now():
    return datetime.now(timezone(timedelta(hours=9)))

def _ensure_df(key: str) -> pd.DataFrame:
    df = st.session_state.get(key)
    if isinstance(df, pd.DataFrame):
        return df.copy()
    return pd.DataFrame(columns=["No","KST Datetime","대상","나이(개월)","체중(kg)","설사","약물","용량(mL)","용량(정보)","메모"])

def _save_df(key: str, df: pd.DataFrame):
    st.session_state[key] = df

def render_antipyretic_schedule(storage_key: str = "antipy_sched") -> pd.DataFrame:
    st.markdown("### 🗓️ 해열제 스케줄러 (mL 표준)")

    with st.expander("대상/용량 설정", expanded=True):
        c0, c1, c2 = st.columns([0.2,0.4,0.4])
        with c0:
            who = st.radio("대상", ["성인","소아"], horizontal=True, key=f"{storage_key}_who")
        with c1:
            apap_c = st.number_input("아세트아미노펜 농도 (mg/5mL)", 80.0, 500.0, value=160.0, step=10.0, key=f"{storage_key}_apap_c")
        with c2:
            ibu_c  = st.number_input("이부프로펜 농도 (mg/5mL)",  50.0, 400.0, value=100.0, step=10.0, key=f"{storage_key}_ibu_c")

        # 설사 모듈
        diarrhea = st.selectbox("설사(횟수/일)", ["없음","1~3회","4~6회","7회 이상"], key=f"{storage_key}_diarrhea")
        if diarrhea == "4~6회":
            st.warning("수분/전해질 보충을 충분히 해주세요. 증상이 지속되면 의료진과 상의.")
        elif diarrhea == "7회 이상":
            st.error("탈수 위험 ↑ — 수분/전해질 보충 및 **의료진 상담 권장**.")

        if who == "소아":
            a1, a2 = st.columns([0.3,0.3])
            with a1:
                age_m = st.number_input("나이(개월)", min_value=0, step=1, key=f"{storage_key}_age")
            with a2:
                weight = st.number_input("체중(kg)", min_value=0.0, step=0.1, key=f"{storage_key}_wt")
            if callable(acetaminophen_ml) and callable(ibuprofen_ml):
                apap_ml, meta1 = acetaminophen_ml(age_m, weight or None)
                ibu_ml,  meta2 = ibuprofen_ml(age_m, weight or None)
                used_w = float(weight or meta1.get("weight_used") or meta2.get("weight_used") or 0.0)
            else:
                st.warning("소아 용량 모듈이 없습니다.")
                apap_ml = ibu_ml = 0.0
                used_w = float(weight or 0.0)
            st.caption(f"계산 체중: **{used_w:.1f} kg**")
        else:
            a1 = st.columns(1)[0]
            with a1:
                weight = st.number_input("체중(kg)", min_value=0.0, step=0.5, value=60.0, key=f"{storage_key}_wt_adult")
            # 성인: mg/kg → mg cap → mL
            apap_ml, apap_mg, _ = _adult_mg_to_ml(weight, 12.5, 325.0, 1000.0, apap_c)
            ibu_ml,  ibu_mg,  _ = _adult_mg_to_ml(weight, 7.5, 200.0,  400.0,  ibu_c)
            st.caption(f"아세트아미노펜 ≒ **{apap_mg} mg**, 이부프로펜 ≒ **{ibu_mg} mg**")

    st.divider()

    # 약물 선택 / 메모
    m1, m2 = st.columns([0.5,0.5])
    with m1:
        agent = st.selectbox("약물", ["아세트아미노펜","이부프로펜","교차(아세트→이부)"], key=f"{storage_key}_agent")
    with m2:
        note = st.text_input("메모(선택)", key=f"{storage_key}_note")

    df_prev = _ensure_df(storage_key)

    # --- 개별 추가 (기본) ---
    st.markdown("#### ⏱️ 개별 추가")
    ic1, ic2 = st.columns([0.5,0.5])
    with ic1:
        pick_date = st.date_input("날짜 (KST)", value=_kst_now().date(), key=f"{storage_key}_one_date")
    with ic2:
        pick_time = st.time_input("시각 (KST)", value=_kst_now().time().replace(second=0, microsecond=0), key=f"{storage_key}_one_time")

    def _append_row(dt_obj, drug, dose_ml, meta_txt):
        dt_str = dt_obj.strftime("%Y-%m-%d %H:%M")
        if not df_prev.empty:
            dup = df_prev[(df_prev["KST Datetime"] == dt_str) & (df_prev["약물"] == drug)]
            if not dup.empty:
                return False
        new = {
            "No": len(df_prev) + 1,
            "KST Datetime": dt_str,
            "대상": who,
            "나이(개월)": (0 if who=="성인" else int(age_m)),
            "체중(kg)": (float(weight) if who=="성인" else float(weight or 0.0)),
            "설사": diarrhea,
            "약물": drug,
            "용량(mL)": float(dose_ml),
            "용량(정보)": meta_txt,
            "메모": note or "",
        }
        df_prev.loc[len(df_prev)] = new
        return True

    b1, b2 = st.columns([0.4,0.6])
    with b1:
        if st.button("➕ 이 시간으로 추가", key=f"{storage_key}_add_one"):
            dt_obj = datetime.combine(pick_date, pick_time).replace(tzinfo=timezone(timedelta(hours=9)))
            if agent == "아세트아미노펜":
                ok = _append_row(dt_obj, "아세트아미노펜", apap_ml, f"{apap_c} mg/5mL")
            elif agent == "이부프로펜":
                ok = _append_row(dt_obj, "이부프로펜", ibu_ml, f"{ibu_c} mg/5mL")
            else:
                # 교차는 현재 선택된 시간 1건만: 짝수/홀수 개념 없이 두 줄을 한 번에 넣지 않고 약물 선택 기준으로 입력하도록 유지
                ok = _append_row(dt_obj, "아세트아미노펜", apap_ml, f"{apap_c} mg/5mL")
                ok = ok or _append_row(dt_obj, "이부프로펜", ibu_ml, f"{ibu_c} mg/5mL")
            if ok:
                df_sorted = df_prev.sort_values("KST Datetime").reset_index(drop=True)
                df_sorted["No"] = range(1, len(df_sorted)+1)
                _save_df(storage_key, df_sorted)
                st.success("1건 추가됨.")
            else:
                st.info("이미 같은 시간/같은 약물이 있습니다.")

    # --- (선택) 연속 스케줄 자동 생성 ---
    with st.expander("🔁 연속 스케줄 자동 생성 (선택 기능)", expanded=False):
        s1, s2, s3 = st.columns([0.33,0.33,0.34])
        with s1:
            start_date = st.date_input("시작일 (KST)", value=_kst_now().date(), key=f"{storage_key}_date")
            start_time = st.time_input("시작 시각 (KST)", value=_kst_now().time().replace(second=0, microsecond=0), key=f"{storage_key}_time")
        with s2:
            interval_h = st.number_input("간격(시간)", min_value=1, max_value=24, value=6, step=1, key=f"{storage_key}_interval")
        with s3:
            count = st.number_input("횟수", min_value=1, max_value=24, value=6, step=1, key=f"{storage_key}_count")

        if st.button("➕ 연속 스케줄 생성·추가", key=f"{storage_key}_add_series"):
            dt0 = datetime.combine(start_date, start_time).replace(tzinfo=timezone(timedelta(hours=9)))
            added = 0
            for i in range(int(count)):
                dt_i = dt0 + timedelta(hours=int(interval_h)*i)
                if agent == "아세트아미노펜":
                    ok = _append_row(dt_i, "아세트아미노펜", apap_ml, f"{apap_c} mg/5mL")
                elif agent == "이부프로펜":
                    ok = _append_row(dt_i, "이부프로펜", ibu_ml, f"{ibu_c} mg/5mL")
                else:
                    if i % 2 == 0:
                        ok = _append_row(dt_i, "아세트아미노펜", apap_ml, f"{apap_c} mg/5mL")
                    else:
                        ok = _append_row(dt_i, "이부프로펜", ibu_ml, f"{ibu_c} mg/5mL")
                if ok: added += 1
            if added > 0:
                df_sorted = df_prev.sort_values("KST Datetime").reset_index(drop=True)
                df_sorted["No"] = range(1, len(df_sorted)+1)
                _save_df(storage_key, df_sorted)
                st.success(f"{added}건 추가됨.")
            else:
                st.info("추가된 항목이 없습니다(중복 방지).")

    # 표시/선택 삭제
    df = _ensure_df(storage_key)
    if df.empty:
        st.info("아직 저장된 스케줄이 없습니다.")
        return df

    st.markdown("#### 📋 스케줄")
    st.dataframe(df, use_container_width=True, height=260)

    # 선택 삭제
    idx = st.number_input("삭제할 No (한 개씩)", min_value=0, step=1, value=0, key=f"{storage_key}_delno")
    if st.button("🗑️ 선택 삭제", key=f"{storage_key}_delbtn"):
        if idx > 0 and idx <= len(df):
            df2 = df[df["No"] != int(idx)].copy().reset_index(drop=True)
            df2["No"] = range(1, len(df2)+1)
            _save_df(storage_key, df2)
            st.success(f"No {idx} 삭제됨.")
        else:
            st.info("유효한 No를 입력하세요.")

    st.download_button("⬇️ CSV 내보내기", data=df.to_csv(index=False).encode("utf-8"), file_name="antipyretic_schedule_kst.csv")
    return df
