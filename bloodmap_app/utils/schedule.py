# -*- coding: utf-8 -*-
import streamlit as st

def render_schedule(patient_id):
    st.markdown("### 🗓️ 항암 스케줄 메모")
    if not patient_id:
        st.caption("별명과 PIN을 입력하면 스케줄을 저장/조회할 수 있습니다."); return
    S = st.session_state; S.schedules = S.get("schedules", {})
    cur = S.schedules.get(patient_id, [])
    new_memo = st.text_input("스케줄 메모 추가 (예: 9/10 ARA-C SC, 9/12 MTX)")
    if st.button("➕ 메모 저장", use_container_width=True):
        if new_memo.strip():
            cur.append(new_memo.strip()); S.schedules[patient_id] = cur
            st.success("스케줄 메모를 저장했습니다.")
    if cur:
        st.write("#### 저장된 메모")
        for i, m in enumerate(cur, 1): st.write(f"{i}. {m}")
