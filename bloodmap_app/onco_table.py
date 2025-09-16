# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Optional
from datetime import date
import pandas as pd

try:
    import streamlit as st
except Exception:
    class _Dummy:
        def __getattr__(self, k): return lambda *a, **k: None
    st = _Dummy()

COLUMNS = ["Date","WBC(10^3/µL)","ANC(/µL)","Hb(g/dL)","PLT(10^3/µL)","CRP(mg/L)","메모"]

def _init_table() -> pd.DataFrame:
    if "onco_table" not in st.session_state:
        df = pd.DataFrame(columns=COLUMNS)
        st.session_state["onco_table"] = df
    return st.session_state["onco_table"]

def ui_onco_table_card(key: str = "onco_table") -> pd.DataFrame:
    st.markdown("### 📋 암환자 피수치 표 (엑셀 스타일)")
    df = _init_table()

    c1, c2 = st.columns(2)
    with c1:
        if st.button("➕ 오늘 행 추가", key=f"{key}_add"):
            row = {c:"" for c in COLUMNS}
            row["Date"] = date.today().strftime("%Y-%m-%d")
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
            st.session_state["onco_table"] = df
    with c2:
        if st.button("🧹 표 비우기", key=f"{key}_clear"):
            st.session_state["onco_table"] = pd.DataFrame(columns=COLUMNS)
            df = st.session_state["onco_table"]

    edited = st.data_editor(
        df,
        use_container_width=True,
        num_rows="dynamic",
        key=f"{key}_editor",
        column_config={
            "Date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
        },
        hide_index=True
    )

    st.session_state["onco_table"] = edited

    # Export / Import
    exp1, exp2 = st.columns(2)
    with exp1:
        csv = edited.to_csv(index=False)
        st.download_button("⬇️ CSV 내보내기", data=csv, file_name="onco_table.csv")
    with exp2:
        up = st.file_uploader("CSV 가져오기", type=["csv"], key=f"{key}_upl")
        if up is not None:
            try:
                imp = pd.read_csv(up)
                # ensure columns
                for c in COLUMNS:
                    if c not in imp.columns:
                        imp[c] = ""
                st.session_state["onco_table"] = imp[COLUMNS]
                st.success("불러오기 완료")
            except Exception as e:
                st.error(f"가져오기 실패: {e}")
    return edited
