# -*- coding: utf-8 -*-
import streamlit as st

def render_graphs():
    if "records" not in st.session_state or not st.session_state.records:
        return
    st.markdown("### 📈 추이 그래프")
    keys = list(st.session_state.records.keys())
    sel = st.selectbox("기록 확인(별명#PIN)", keys)
    data = st.session_state.records.get(sel, [])
    if not data:
        st.info("기록이 없습니다."); return
    try:
        import pandas as pd
        rows = []
        for rec in data:
            labs = rec.get("labs", {})
            rows.append({
                "ts": rec.get("ts"),
                "WBC": labs.get("WBC(백혈구)"),
                "Hb": labs.get("Hb(혈색소)"),
                "PLT": labs.get("혈소판(PLT)"),
                "CRP": labs.get("CRP"),
                "ANC": labs.get("ANC(호중구)"),
            })
        df = pd.DataFrame(rows).dropna(how="all", subset=["WBC","Hb","PLT","CRP","ANC"])
        if df.empty: st.info("그래프화할 수치가 없습니다."); return
        df = df.set_index("ts")
        st.line_chart(df)
    except Exception:
        st.info("pandas 미설치 또는 데이터 부족으로 그래프 미표시.")
