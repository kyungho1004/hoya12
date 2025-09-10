
# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd

def render_graphs():
    recs_all = []
    for k, arr in st.session_state.get("records", {}).items():
        for it in arr:
            row = {"별명PIN": k, "ts": it.get("ts","")}
            for lab, v in (it.get("labs") or {}).items():
                row[lab] = v
            recs_all.append(row)
    if not recs_all:
        st.info("그래프: 별명과 PIN으로 저장된 기록이 있으면 추이를 볼 수 있어요.")
        return
    df = pd.DataFrame(recs_all)
    st.markdown("### 📈 추이 그래프")
    pick = st.multiselect("표시할 수치", [c for c in df.columns if c not in ("별명PIN","ts")], default=None)
    if pick:
        show = df[["ts"] + pick].set_index("ts")
        st.line_chart(show)
