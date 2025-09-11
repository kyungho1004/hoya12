# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta

# ---------- 숫자/포맷 유틸 ----------
def clean_num(s):
    if s is None: return None
    try:
        x = str(s).strip().replace("±","").replace("+","").replace(",","")
        if x in {"","-"}: return None
        return float(x)
    except: return None

def round_half(x):
    try: return round(float(x)*2)/2
    except: return x

def temp_band(t):
    try:
        t = float(t)
        if t >= 39.0: return "고열(39°+)"
        if t >= 38.5: return "고열(38.5–39°)"
        if t >= 38.0: return "미열(38.0–38.5°)"
        return "정상/미열"
    except:
        return "-"

def rr_thr_by_age_m(age_m):
    try:
        a = int(age_m or 0)
        if a < 2: return 60
        if a < 12: return 50
        if a < 60: return 40
        return 30
    except:
        return 40

def nickname_pin(nick: str, pin: str):
    nick = (nick or "").strip()
    pin  = (pin or "").strip()
    if len(pin) != 4 or not pin.isdigit():
        return ("guest", False)
    return (f"{nick}#{pin}", True)

# ---------- 스케줄 ----------
def schedule_block():
    st.markdown("#### 📅 항암 스케줄(간단)")
    from datetime import date, timedelta
    c1,c2,c3 = st.columns(3)
    with c1: start = st.date_input("시작일", value=date.today())
    with c2: cycle = st.number_input("주기(일)", min_value=1, step=1, value=21)
    with c3: ncyc = st.number_input("사이클 수", min_value=1, step=1, value=6)
    if st.button("스케줄 생성/추가", key="btn_make_schedule"):
        rows = [{"Cycle": i+1, "Date": (start + timedelta(days=i*int(cycle))).strftime("%Y-%m-%d")} for i in range(int(ncyc))]
        df = pd.DataFrame(rows)
        st.session_state.setdefault("schedules", {})
        st.session_state["schedules"][st.session_state["key"]] = df
        st.success("스케줄이 저장되었습니다.")
    df = st.session_state.get("schedules", {}).get(st.session_state.get("key","guest"))
    if isinstance(df, pd.DataFrame) and not df.empty:
        st.dataframe(df, use_container_width=True, height=180)
