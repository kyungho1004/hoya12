
# -*- coding: utf-8 -*-
"""
mini_antipyretic_schedule.py — 해열제 스케줄표 (mL) — Smart v3.1
- 버튼 프리셋이 Streamlit 세션 상태를 안전하게 다루도록 수정
  (위젯 키에 직접 할당하지 않고 별도 *_state 키를 사용)
"""
from __future__ import annotations
from typing import Dict, Any, Tuple, List
import streamlit as st
import pandas as pd
from datetime import datetime, date, time, timedelta, timezone

# --- 기존 로직: (생략 없이 포함) ---
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

def _round_half_ml(x: float) -> float:
    return round(x * 2) / 2.0

def _make_rows(start_dt: datetime, hours: float, days: int, agent: str, dose_ml: float, diarrhea: str, add_temp: bool) -> List[Dict[str, Any]]:
    out = []
    total_slots = int((24*days) / hours) + 1
    cur = start_dt
    for i in range(total_slots):
        row = {
            "No": i+1,
            "KST_time": _kst(cur).strftime("%Y-%m-%d %H:%M"),
            "Agent": agent,
            "Dose_mL": dose_ml,
            "Diarrhea": diarrhea,
            "Taken": False,
            "Note": ""
        }
        if add_temp:
            row["Temp_C"] = ""
        out.append(row)
        cur = cur + timedelta(hours=hours)
    return out

def _make_rows_alternating(start_dt: datetime, apap_h: float, ibu_h: float, days: int, apap_ml: float, ibu_ml: float, diarrhea: str, add_temp: bool) -> List[Dict[str, Any]]:
    out = []
    cur = start_dt
    agent = "APAP"
    end_dt = start_dt + timedelta(days=days)
    i = 0
    while cur <= end_dt + timedelta(hours=1e-6):
        dose_ml = apap_ml if agent=="APAP" else ibu_ml
        row = {
            "No": i+1,
            "KST_time": _kst(cur).strftime("%Y-%m-%d %H:%M"),
            "Agent": agent,
            "Dose_mL": dose_ml,
            "Diarrhea": diarrhea,
            "Taken": False,
            "Note": ""
        }
        if add_temp:
            row["Temp_C"] = ""
        out.append(row)
        if agent == "APAP":
            cur = cur + timedelta(hours=apap_h); agent = "IBU"
        else:
            cur = cur + timedelta(hours=ibu_h);  agent = "APAP"
        i += 1
    for idx, r in enumerate(out): r["No"] = idx+1
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

    # state helpers
    def _get_df(): 
        df = st.session_state.get(storage_key)
        if isinstance(df, pd.DataFrame): return df.copy()
        return pd.DataFrame(columns=["No","KST_time","Agent","Dose_mL","Diarrhea","Taken","Note"])
    def _save_df(df): st.session_state[storage_key] = df

    # ── STEP 1. 대상/설사 ────────────────────────────
    c1,c2,c3 = st.columns([0.22,0.38,0.40])
    with c1: who = st.radio("대상", ["성인","소아"], horizontal=True, key=f"{storage_key}_who")
    with c2: diarrhea = st.selectbox("설사(횟수/일)", ["없음","1~3회","4~6회","7회 이상"], key=f"{storage_key}_diarrhea")
    with c3: st.caption(f"한국시간 기준: **{_kst(datetime.now(timezone(timedelta(hours=9)))).strftime('%Y-%m-%d %H:%M')}**")

    # 옵션: 체온 칼럼
    add_temp = st.toggle("체온(°C) 칼럼 추가", value=False, key=f"{storage_key}_add_temp")

    # ── 고급설정(접힘): 농도·mg/kg ───────────────────
    adv = st.expander("⚙️ 농도/계산 설정 (필요할 때만)", expanded=False)
    with adv:
        s1, s2, s3, s4 = st.columns(4)
        with s1: apap_c = st.number_input("APAP 농도 (mg/5mL)", min_value=80.0, max_value=500.0, step=10.0, value=160.0, key=f"{storage_key}_apap_c")
        with s2: ibu_c  = st.number_input("IBU 농도 (mg/5mL)",  min_value=50.0, max_value=400.0, step=10.0, value=100.0, key=f"{storage_key}_ibu_c")
        with s3: apap_mgkg = st.number_input("APAP mg/kg", min_value=8.0, max_value=15.0, step=0.5, value=12.5, key=f"{storage_key}_apap_mgkg")
        with s4: ibu_mgkg  = st.number_input("IBU mg/kg",  min_value=5.0, max_value=10.0, step=0.5, value=7.5,  key=f"{storage_key}_ibu_mgkg")

    # ── STEP 2. 체중/나이 ────────────────────────────
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

    # 반올림 0.5 mL
    apap_ml = _round_half_ml(apap_ml); ibu_ml = _round_half_ml(ibu_ml)

    # ── STEP 3. 약/교대 & 용량 ─────────────────────────
    st.markdown("#### 💊 약 & 1회 용량")
    agent = st.segmented_control("약 선택", options=["APAP","IBU"], default="APAP", key=f"{storage_key}_agent_seg")
    alt = st.toggle("교대 복용(APAP↔IBU) 스케줄 만들기", value=False, key=f"{storage_key}_alt")

    # ── STEP 4. 스케줄 설정 ─────────────────────────
    st.markdown("#### 🗓️ 스케줄 설정")

    # 내부 상태키(*_state) 준비
    sd_key = f"{storage_key}_start_d_state"
    st_key = f"{storage_key}_start_t_state"
    if sd_key not in st.session_state: st.session_state[sd_key] = date.today()
    if st_key not in st.session_state: st.session_state[st_key] = time(9,0)

    if alt:
        p1,p2,p3,p4,p5 = st.columns([0.22,0.18,0.18,0.21,0.21])
        with p1: start_date = st.date_input("시작 날짜", value=st.session_state[sd_key], key=f"{storage_key}_start_d")
        with p2: start_time = st.time_input("시작 시각", value=st.session_state[st_key], key=f"{storage_key}_start_t")
        with p3: apap_h     = st.number_input("APAP 간격(h)", min_value=4.0, max_value=8.0, step=0.5, value=6.0, key=f"{storage_key}_apap_h")
        with p4: ibu_h      = st.number_input("IBU 간격(h)",  min_value=6.0, max_value=12.0, step=0.5, value=8.0, key=f"{storage_key}_ibu_h")
        with p5: days       = st.number_input("기간(일)", min_value=1, max_value=7, step=1, value=2, key=f"{storage_key}_days")
    else:
        p1,p2,p3,p4 = st.columns([0.27,0.23,0.25,0.25])
        with p1: start_date = st.date_input("시작 날짜", value=st.session_state[sd_key], key=f"{storage_key}_start_d")
        with p2: start_time = st.time_input("시작 시각", value=st.session_state[st_key], key=f"{storage_key}_start_t")
        with p3: step_h     = st.number_input("간격(시간)", min_value=3.0, max_value=12.0, step=0.5, value=6.0 if agent=="APAP" else 8.0, key=f"{storage_key}_step")
        with p4: days       = st.number_input("기간(일)", min_value=1, max_value=7, step=1, value=2, key=f"{storage_key}_days")

    # 프리셋 버튼: *_state 키만 업데이트 (위젯 키에 직접 할당 금지)
    pr1, pr2, pr3, pr4 = st.columns(4)
    if pr1.button("지금부터", key=f"{storage_key}_now"):
        now = _kst(datetime.now(timezone(timedelta(hours=9))))
        st.session_state[sd_key] = now.date()
        st.session_state[st_key] = time(now.hour, now.minute)
        st.rerun()
    if pr2.button("+6시간", key=f"{storage_key}_p6"):
        base = datetime.combine(start_date, start_time, tzinfo=timezone(timedelta(hours=9))) + timedelta(hours=6)
        st.session_state[sd_key] = base.date()
        st.session_state[st_key] = time(base.hour, base.minute)
        st.rerun()
    if pr3.button("+8시간", key=f"{storage_key}_p8"):
        base = datetime.combine(start_date, start_time, tzinfo=timezone(timedelta(hours=9))) + timedelta(hours=8)
        st.session_state[sd_key] = base.date()
        st.session_state[st_key] = time(base.hour, base.minute)
        st.rerun()
    if pr4.button("간격 추천", key=f"{storage_key}_rec"):
        if alt:
            st.session_state[f"{storage_key}_apap_h"] = 6.0
            st.session_state[f"{storage_key}_ibu_h"] = 8.0
        else:
            st.session_state[f"{storage_key}_step"] = 6.0 if agent == "APAP" else 8.0
        st.rerun()

    # 생성/삭제/내보내기 (기존 로직 유지)
    def _compose_df():
        start_dt = datetime.combine(start_date, start_time, tzinfo=timezone(timedelta(hours=9)))
        base = _get_df()
        if st.session_state.get(f"{storage_key}_alt"):
            apap_h = float(st.session_state.get(f"{storage_key}_apap_h", 6.0))
            ibu_h  = float(st.session_state.get(f"{storage_key}_ibu_h", 8.0))
            new_rows = _make_rows_alternating(start_dt, apap_h, ibu_h, int(st.session_state.get(f"{storage_key}_days",2)),
                                              float(apap_ml), float(ibu_ml), diarrhea, add_temp)
        else:
            step_h = float(st.session_state.get(f"{storage_key}_step", 6.0 if agent=="APAP" else 8.0))
            new_rows = _make_rows(start_dt, step_h, int(st.session_state.get(f"{storage_key}_days",2)), agent, float(dose_ml), diarrhea, add_temp)
        df = pd.concat([base, pd.DataFrame(new_rows)], ignore_index=True)
        df["No"] = range(1, len(df)+1)
        return df

    btn1, btn2, btn3, btn4 = st.columns([0.23,0.23,0.23,0.31])
    with btn1:
        if st.button("➕ 생성/추가", key=f"{storage_key}_gen"):
            st.session_state[storage_key] = _compose_df()
            st.success("스케줄이 저장되었습니다.")
    with btn2:
        if st.button("🧹 전체 삭제", key=f"{storage_key}_clear"):
            st.session_state[storage_key] = _get_df().iloc[0:0]
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

    # 표/진행률
    df = _get_df()
    if df.empty:
        st.info("예: APAP 6h / IBU 8h 또는 교대로 24~48시간 스케줄을 만들어 보세요.")
    else:
        taken = df["Taken"].sum() if "Taken" in df else 0
        progress = float(taken) / float(len(df)) if len(df) else 0.0
        st.progress(progress, text=f"복용 진행률: {int(progress*100)}%")
        st.data_editor(df, use_container_width=True, num_rows="dynamic", hide_index=True,
                       key=f"{storage_key}_editor")
        edited = st.session_state.get(f"{storage_key}_editor")
        if isinstance(edited, pd.DataFrame):
            st.session_state[storage_key] = edited
