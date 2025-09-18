
# -*- coding: utf-8 -*-
"""
mini_schedule.py — 공용 미니 스케줄표(소아·성인·질환 공용)
- 별명+PIN 세션 키(`core_utils.nickname_pin`)와 함께 쓰면 사용자별 히스토리 저장 가능.
- 테이블을 한 화면에서 가볍게 생성/추가/표시.
"""
from __future__ import annotations
import pandas as pd
import streamlit as st
from datetime import date, timedelta

def mini_schedule_ui(storage_key: str = "mini_sched") -> None:
    st.markdown("### 🗓️ 미니 스케줄표")
    c1, c2, c3 = st.columns(3)
    with c1: start = st.date_input("시작일", value=date.today(), key=f"{storage_key}_start")
    with c2: step  = st.number_input("주기(일)", min_value=1, step=1, value=7, key=f"{storage_key}_step")
    with c3: n     = st.number_input("횟수", min_value=1, step=1, value=6, key=f"{storage_key}_n")

    # 라벨(선택): 소아/성인/질환
    c4, c5 = st.columns([0.6, 0.4])
    with c4: tag = st.text_input("스케줄 이름(예: 성인-감기, 소아-RSV, 항암캘린더 등)", key=f"{storage_key}_tag")
    with c5: who = st.selectbox("대상", ["공용","소아","성인","질환"], index=0, key=f"{storage_key}_who")

    if st.button("➕ 생성/추가", key=f"{storage_key}_gen"):
        rows = []
        for i in range(int(n)):
            d = (start + timedelta(days=i*int(step))).strftime("%Y-%m-%d")
            rows.append({"No": i+1, "Date": d, "Name": (tag or "미니"), "Who": who})
        df_new = pd.DataFrame(rows)

        st.session_state.setdefault(storage_key, pd.DataFrame())
        df_prev = st.session_state[storage_key]
        df = pd.concat([df_prev, df_new], ignore_index=True)
        # 중복 날짜-이름 병합
        df = df.drop_duplicates(subset=["Date","Name"], keep="last").sort_values(["Date","Name"])
        st.session_state[storage_key] = df
        st.success("스케줄 저장됨.")

    df = st.session_state.get(storage_key)
    if isinstance(df, pd.DataFrame) and not df.empty:
        st.dataframe(df, use_container_width=True, height=220)
        # CSV 다운로드
        st.download_button("⬇️ CSV 다운로드", data=df.to_csv(index=False), file_name="mini_schedule.csv")
    else:
        st.info("아직 저장된 스케줄이 없습니다.")
