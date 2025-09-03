# -*- coding: utf-8 -*-
import streamlit as st

def render_graphs():
    st.header("📈 추이 그래프 (WBC/Hb/PLT/CRP/ANC)")
    recs = st.session_state.get("records", {})
    # records는 별명#PIN 별로 저장됨
    if not recs:
        st.info("저장된 기록이 없습니다. 별명과 PIN을 입력하고 해석을 눌러 저장해보세요.")
        return
    # 가장 최근 프로필 키 추정
    last_key = getattr(st.session_state, "last_profile_key", None)
    sel = st.selectbox("프로필 선택(별명#PIN)", options=list(recs.keys()), index=(list(recs.keys()).index(last_key) if last_key in recs else 0))
    rows = recs.get(sel, [])
    if not rows:
        st.info("해당 프로필의 저장 기록이 없습니다.")
        return

    # 간단 테이블 및 선그래프
    try:
        import pandas as pd
    except Exception:
        st.info("pandas 설치 시 그래프가 활성화됩니다.")
        return

    ts = []
    WBC=[]; Hb=[]; PLT=[]; CRP=[]; ANC=[]
    for r in rows:
        ts.append(r.get("ts"))
        labs = r.get("labs", {})
        WBC.append(labs.get("WBC(백혈구)"))
        Hb.append(labs.get("Hb(혈색소)"))
        PLT.append(labs.get("혈소판(PLT)"))
        CRP.append(labs.get("CRP"))
        ANC.append(labs.get("ANC(호중구)"))

    df = pd.DataFrame({
        "ts": ts, "WBC": WBC, "Hb": Hb, "PLT": PLT, "CRP": CRP, "ANC": ANC
    }).set_index("ts")

    st.line_chart(df[["WBC","Hb","PLT","CRP","ANC"]])
