
# -*- coding: utf-8 -*-
import streamlit as st
from ..config import LBL_WBC, LBL_Hb, LBL_PLT, LBL_CRP, LBL_ANC

def render_graphs():
    recs = st.session_state.get("records", {})
    if not recs:
        return
    st.header("📈 추이 그래프")
    target = st.selectbox("별명#PIN 선택", list(recs.keys()))
    rows = recs.get(target, [])
    if not rows:
        st.info("기록이 없습니다.")
        return
    st.caption("아래 표에서 날짜별 변화를 확인하세요.")
    table = []
    for r in rows:
        labs = r.get("labs", {})
        row = {"시각": r.get("ts","")}
        for k in [LBL_WBC, LBL_Hb, LBL_PLT, LBL_CRP, LBL_ANC]:
            row[k] = labs.get(k, "")
        table.append(row)
    try:
        import pandas as pd
        st.dataframe(pd.DataFrame(table))
    except Exception:
        for row in table:
            st.write(row)
