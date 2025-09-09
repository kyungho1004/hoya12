
# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd

def render_graphs():
    S = st.session_state
    if "records" not in S or not S["records"]:
        return
    st.markdown("### 📈 추이 그래프")
    # 최근 사용자 키 추정
    last_key = None
    for k, v in S["records"].items():
        if v: last_key = k
    if not last_key: 
        return
    rows = S["records"][last_key]
    if not rows:
        return
    # 간단히 WBC/Hb/PLT/CRP/ANC만
    labs = ["WBC(백혈구)","Hb(혈색소)","혈소판(PLT)","CRP","ANC(호중구)"]
    data = []
    for r in rows:
        ts = r.get("ts","")
        vals = r.get("labs",{})
        row = {"ts": ts}
        for lb in labs:
            row[lb] = vals.get(lb)
        data.append(row)
    df = pd.DataFrame(data)
    df = df.set_index("ts")
    st.line_chart(df)
