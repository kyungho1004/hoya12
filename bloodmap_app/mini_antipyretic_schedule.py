
# -*- coding: utf-8 -*-
"""
mini_antipyretic_schedule.py — 해열제 스케줄표 (소아·일상·질환 전용)
- APAP/IBU 스케줄 자동 생성 (mL 계산 포함)
- 대상(성인/소아), 나이/체중, 농도, mg/kg, 간격(시간), 기간(일수) 지정
- CSV/ICS 내보내기, 표 직접 편집 가능
- drop-in: render_antipyretic_schedule_ui(storage_key="...")
"""
from __future__ import annotations
from typing import Dict, Any, Tuple, List
import streamlit as st
import pandas as pd
from datetime import datetime, date, time, timedelta, timezone

# Pediatric dosing (override when available)
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

def _adult_ml(weight_kg: float|None, mg_per_kg: float, syrup_mg_per_5ml: float, cap_low: float, cap_high: float) -> Tuple[float, int]:
    w = float(weight_kg or 60.0)
    mg = max(cap_low, min(cap_high, w*mg_per_kg))
    ml = round(mg * 5.0 / max(1e-6, syrup_mg_per_5ml), 1)
    return ml, int(round(mg))

def _kst(dt: datetime) -> datetime:
    return dt.astimezone(timezone(timedelta(hours=9)))

def _make_rows(start_dt: datetime, days: int, step_h: float, agent: str, dose_ml: float) -> List[Dict[str, Any]]:
    out = []
    total_slots = int((24*days) / step_h) + 1
    cur = start_dt
    for i in range(total_slots):
        out.append({
            "No": i+1,
            "KST_time": _kst(cur).strftime("%Y-%m-%d %H:%M"),
            "Agent": agent,
            "Dose_mL": dose_ml,
            "Taken": False,
            "Note": ""
        })
        cur = cur + timedelta(hours=step_h)
    return out

def _ics(df: pd.DataFrame, title_prefix: str = "해열제"):
    lines = ["BEGIN:VCALENDAR","VERSION:2.0","PRODID:-//BloodMap//AntipyreticSchedule//KR"]
    for _, r in df.iterrows():
        try:
            dt = datetime.strptime(str(r["KST_time"]), "%Y-%m-%d %H:%M")
        except Exception:
            continue
        stamp = dt.strftime("%Y%m%dT%H%M%S")
        title = f"{title_prefix} {r.get('Agent','')} {r.get('Dose_mL','')} mL"
        uid = f"{stamp}-{title}@bloodmap"
        lines += ["BEGIN:VEVENT", f"UID:{uid}", f"DTSTART;TZID=Asia/Seoul:{stamp}", f"SUMMARY:{title}", "END:VEVENT"]
    lines.append("END:VCALENDAR")
    return "\n".join(lines)

def render_antipyretic_schedule_ui(storage_key: str = "antipyretic_sched", show_title: bool = True):
    if show_title:
        st.markdown("### ⏱️ 해열제 스케줄표 (mL)")

    # 누적 테이블
    def _get_df(): 
        df = st.session_state.get(storage_key)
        if isinstance(df, pd.DataFrame): return df.copy()
        return pd.DataFrame(columns=["No","KST_time","Agent","Dose_mL","Taken","Note"])
    def _save_df(df): st.session_state[storage_key] = df

    # 1) 대상/용량 계산
    c1,c2,c3 = st.columns([0.22,0.22,0.56])
    with c1: who = st.radio("대상", ["성인","소아"], horizontal=True, key=f"{storage_key}_who")
    with c2: agent = st.selectbox("약", ["APAP(아세트아미노펜)","IBU(이부프로펜)"], key=f"{storage_key}_agent")
    with c3: st.caption(f"한국시간 기준: **{_kst(datetime.now(timezone(timedelta(hours=9)))).strftime('%Y-%m-%d %H:%M')}**")

    adv = st.expander("⚙️ 농도/계산 설정", expanded=False)
    with adv:
        s1, s2, s3, s4 = st.columns(4)
        with s1: apap_c = st.number_input("APAP 농도 (mg/5mL)", min_value=80.0, max_value=500.0, step=10.0, value=160.0, key=f"{storage_key}_apap_c")
        with s2: ibu_c  = st.number_input("IBU 농도 (mg/5mL)",  min_value=50.0, max_value=400.0, step=10.0, value=100.0, key=f"{storage_key}_ibu_c")
        with s3: apap_mgkg = st.number_input("APAP mg/kg", min_value=8.0, max_value=15.0, step=0.5, value=12.5, key=f"{storage_key}_apap_mgkg")
        with s4: ibu_mgkg  = st.number_input("IBU mg/kg",  min_value=5.0, max_value=10.0, step=0.5, value=7.5,  key=f"{storage_key}_ibu_mgkg")

    # 대상별 기본 입력
    if who == "소아":
        a1,a2 = st.columns([0.3,0.7])
        with a1: age_m = st.number_input("나이(개월)", min_value=0, step=1, key=f"{storage_key}_age")
        with a2: weight = st.number_input("체중(kg)", min_value=0.0, step=0.1, key=f"{storage_key}_wt")
        apap_ml, _ = acetaminophen_ml(age_m, weight or None)
        ibu_ml,  _ = ibuprofen_ml(age_m, weight or None)
    else:
        age_m = None
        a1 = st.columns(1)[0]
        with a1: weight = st.number_input("체중(kg)", min_value=0.0, step=0.5, value=60.0, key=f"{storage_key}_wt_adult")
        apap_ml, apap_mg = _adult_ml(weight or None, apap_mgkg, apap_c, 325.0, 1000.0)
        ibu_ml,  ibu_mg  = _adult_ml(weight or None, ibu_mgkg,  ibu_c, 200.0,  400.0)

    if agent.startswith("APAP"):
        dose_ml = apap_ml
        step_default = 6.0  # 4–6h → 기본 6h
        title = f"APAP {dose_ml} mL"
    else:
        dose_ml = ibu_ml
        step_default = 8.0  # 6–8h → 기본 8h
        title = f"IBU {dose_ml} mL"

    # 2) 스케줄 파라미터
    st.markdown("#### 📅 스케줄 설정")
    p1,p2,p3,p4 = st.columns([0.27,0.23,0.25,0.25])
    with p1: start_date = st.date_input("시작 날짜", value=date.today(), key=f"{storage_key}_start_d")
    with p2: start_time = st.time_input("시작 시각", value=time(9,0), key=f"{storage_key}_start_t")
    with p3: step_h     = st.number_input("간격(시간)", min_value=3.0, max_value=12.0, step=0.5, value=step_default, key=f"{storage_key}_step")
    with p4: days       = st.number_input("기간(일)", min_value=1, max_value=7, step=1, value=2, key=f"{storage_key}_days")

    btn1, btn2, btn3, btn4 = st.columns([0.23,0.23,0.23,0.31])
    def _compose_df():
        start_dt = datetime.combine(start_date, start_time, tzinfo=timezone(timedelta(hours=9)))
        base = _get_df()
        new_rows = _make_rows(start_dt, int(days), float(step_h), "APAP" if agent.startswith("APAP") else "IBU", float(dose_ml))
        df = pd.concat([base, pd.DataFrame(new_rows)], ignore_index=True)
        df["No"] = range(1, len(df)+1)
        return df
    with btn1:
        if st.button("➕ 생성/추가", key=f"{storage_key}_gen"):
            _save_df(_compose_df())
            st.success("스케줄이 저장되었습니다.")
    with btn2:
        if st.button("🧹 전체 삭제", key=f"{storage_key}_clear"):
            _save_df(_get_df().iloc[0:0])
            st.warning("스케줄을 모두 삭제했습니다.")
    with btn3:
        df = _get_df()
        if not df.empty:
            st.download_button("⬇️ CSV", data=df.to_csv(index=False).encode("utf-8"),
                               file_name="antipyretic_schedule.csv", use_container_width=True)
    with btn4:
        df = _get_df()
        if not df.empty:
            ics = _ics(df, title_prefix="해열제")
            st.download_button("📆 캘린더(ICS)", data=ics.encode("utf-8"),
                               file_name="antipyretic_schedule.ics", use_container_width=True)

    # 3) 표 표시/편집
    df = _get_df()
    if df.empty:
        st.info(f"예: {title} 기준으로 24~48시간 스케줄을 만들어 보세요.")
    else:
        st.data_editor(
            df,
            use_container_width=True,
            num_rows="dynamic",
            hide_index=True,
            column_config={
                "No": st.column_config.NumberColumn("No", disabled=True),
                "KST_time": st.column_config.TextColumn("KST 시간"),
                "Agent": st.column_config.TextColumn("약"),
                "Dose_mL": st.column_config.NumberColumn("mL"),
                "Taken": st.column_config.CheckboxColumn("복용"),
                "Note": st.column_config.TextColumn("메모"),
            },
            key=f"{storage_key}_editor",
        )
        # 변경 사항 저장
        edited = st.session_state.get(f"{storage_key}_editor")
        if isinstance(edited, pd.DataFrame):
            _save_df(edited)
