# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta

def clean_num(s):
    if s is None: return None
    try:
        x = str(s).strip().replace("±","").replace("+","").replace(",","")
        if x in {"","-"}: return None
        return float(x)
    except Exception:
        return None

def nickname_pin():
    st.session_state.setdefault("uid","guest")
    st.session_state.setdefault("key","guest")
    c1,c2 = st.columns(2)
    with c1: nick = st.text_input("별명", value=st.session_state.get("nick",""))
    with c2: pin  = st.text_input("PIN(4자리)", type="password", max_chars=4, value=st.session_state.get("pin",""))
    if nick and pin and len(pin)==4:
        uid = f"{nick}_{pin}"
        st.session_state["uid"] = uid
        st.session_state["nick"] = nick
        st.session_state["pin"]  = pin
        st.session_state["key"]  = uid
    return st.session_state.get("nick"), st.session_state.get("pin"), st.session_state.get("key")

def schedule_block():
    from datetime import date, timedelta
    st.markdown("#### 📅 스케줄(선택)")
    c1,c2,c3 = st.columns(3)
    with c1: start = st.date_input("시작일", value=date.today())
    with c2: cycle = st.number_input("주기(일)", min_value=1, step=1, value=21)
    with c3: ncyc = st.number_input("사이클 수", min_value=1, step=1, value=6)
    if st.button("스케줄 생성/추가"):
        rows = [{"Cycle": i+1, "Date": (start + timedelta(days=i*int(cycle))).strftime("%Y-%m-%d")} for i in range(int(ncyc))]
        df = pd.DataFrame(rows)
        st.session_state.setdefault("schedules", {})
        st.session_state["schedules"][st.session_state["key"]] = df
        st.success("스케줄이 저장되었습니다.")
    df = st.session_state.get("schedules", {}).get(st.session_state.get("key","guest"))
    if isinstance(df, pd.DataFrame) and not df.empty:
        st.dataframe(df, use_container_width=True, height=180)
