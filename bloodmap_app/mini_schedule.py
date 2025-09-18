
# -*- coding: utf-8 -*-
"""
mini_schedule.py — 공용 미니 스케줄표(소아·성인·질환 공용)
v1.1 업데이트:
- 마지막 스케줄 이름/대상 자동 기억
- 표 편집(st.data_editor), 행 삭제/전체 삭제
- CSV 및 ICS(캘린더) 내보내기
"""
from __future__ import annotations
import pandas as pd
import streamlit as st
from datetime import date, timedelta, datetime

def _get_df(storage_key: str):
    df = st.session_state.get(storage_key)
    if isinstance(df, pd.DataFrame):
        return df.copy()
    return pd.DataFrame(columns=["No","Date","Name","Who"])

def _save_df(storage_key: str, df: pd.DataFrame):
    st.session_state[storage_key] = df

def _ics_from_df(df: pd.DataFrame, title_prefix: str = "미니"):
    lines = ["BEGIN:VCALENDAR","VERSION:2.0","PRODID:-//BloodMap//MiniSchedule//KR"]
    for _, r in df.iterrows():
        d = str(r.get("Date","")).replace("-","")
        name = str(r.get("Name") or title_prefix)
        sub = str(r.get("Who") or "공용")
        uid = f"{d}-{name}-{sub}@bloodmap"
        dt = f"{d}T090000"  # 09:00 KST
        lines += [
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTART:{dt}",
            f"SUMMARY:{name} ({sub})",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    return "\n".join(lines)

def mini_schedule_ui(storage_key: str = "mini_sched") -> None:
    st.markdown("### 🗓️ 미니 스케줄표")
    df_prev = _get_df(storage_key)
    last_tag = st.session_state.get(f"{storage_key}_last_tag","")
    last_who = st.session_state.get(f"{storage_key}_last_who","공용")

    c1, c2, c3 = st.columns(3)
    with c1: start = st.date_input("시작일", value=date.today(), key=f"{storage_key}_start")
    with c2: step  = st.number_input("주기(일)", min_value=1, step=1, value=7, key=f"{storage_key}_step")
    with c3: n     = st.number_input("횟수", min_value=1, step=1, value=6, key=f"{storage_key}_n")

    c4, c5 = st.columns([0.6, 0.4])
    with c4: tag = st.text_input("스케줄 이름(예: 성인-감기, 소아-RSV, 항암캘린더 등)", value=last_tag, key=f"{storage_key}_tag")
    with c5: who = st.selectbox("대상", ["공용","소아","성인","질환"], index=["공용","소아","성인","질환"].index(last_who if last_who in ["공용","소아","성인","질환"] else "공용"), key=f"{storage_key}_who")

    c_btn = st.columns([0.28,0.22,0.22,0.28])
    with c_btn[0]:
        if st.button("➕ 생성/추가", key=f"{storage_key}_gen"):
            rows = []
            for i in range(int(n)):
                d = (start + timedelta(days=i*int(step))).strftime("%Y-%m-%d")
                rows.append({"No": i+1, "Date": d, "Name": (tag or "미니"), "Who": who})
            df_new = pd.DataFrame(rows)
            df = pd.concat([df_prev, df_new], ignore_index=True)
            df = df.drop_duplicates(subset=["Date","Name"], keep="last").sort_values(["Date","Name"]).reset_index(drop=True)
            _save_df(storage_key, df)
            st.session_state[f"{storage_key}_last_tag"] = tag
            st.session_state[f"{storage_key}_last_who"] = who
            st.success("스케줄 저장됨.")
    with c_btn[1]:
        if st.button("🗑️ 선택 삭제", key=f"{storage_key}_del"):
            sel = st.session_state.get(f"{storage_key}_sel") or []
            if sel:
                df = df_prev.drop(index=sel).reset_index(drop=True)
                _save_df(storage_key, df)
                st.success(f"{len(sel)}개 행 삭제.")
            else:
                st.info("삭제할 행을 먼저 선택하세요.")
    with c_btn[2]:
        if st.button("🧹 전체 삭제", key=f"{storage_key}_clear"):
            _save_df(storage_key, _get_df(storage_key).iloc[0:0])
            st.warning("모든 스케줄을 삭제했습니다.")
    with c_btn[3]:
        if isinstance(df_prev, pd.DataFrame) and not df_prev.empty:
            csv = df_prev.to_csv(index=False).encode("utf-8")
            ics = _ics_from_df(df_prev, title_prefix=(tag or "미니")).encode("utf-8")
            st.download_button("⬇️ CSV", data=csv, file_name="mini_schedule.csv")
            st.download_button("⬇️ ICS", data=ics, file_name="mini_schedule.ics")

    df = _get_df(storage_key)
    if isinstance(df, pd.DataFrame) and not df.empty:
        # 선택용 체크박스 컬럼 추가
        if "_sel" not in df.columns:
            df["_sel"] = False
        edited = st.data_editor(
            df,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "_sel": st.column_config.CheckboxColumn("선택"),
                "No": st.column_config.NumberColumn("No", disabled=True),
                "Date": st.column_config.TextColumn("Date"),
                "Name": st.column_config.TextColumn("Name"),
                "Who": st.column_config.TextColumn("Who"),
            },
            hide_index=True,
            key=f"{storage_key}_editor",
        )
        # 선택된 행 인덱스 저장 (삭제 버튼용)
        sel_idx = [i for i, v in enumerate(edited.get("_sel", [])) if v] if isinstance(edited, pd.DataFrame) else []
        st.session_state[f"{storage_key}_sel"] = sel_idx
        # 저장
        if isinstance(edited, pd.DataFrame):
            # 편집 후 저장(선택 컬럼은 유지)
            _save_df(storage_key, edited)
    else:
        st.info("아직 저장된 스케줄이 없습니다.")
