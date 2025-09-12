# app_fix_snippet.py — 참조용 스니펫 (app.py에 직접 반영하세요)
import streamlit as st

# 가정: ONCO_MAP, local_dx_display는 이미 import/정의되어 있음
group = st.selectbox("암 카테고리", ["혈액암","림프종","고형암","육종","희귀암"])
dx_options = list(ONCO_MAP.get(group, {}).keys())

def _dx_fmt(opt: str) -> str:
    try:
        return local_dx_display(group, opt)
    except Exception:
        return str(opt)

dx = st.selectbox("진단(영문+한글)", dx_options or ["직접 입력"], format_func=_dx_fmt)

if dx == "직접 입력":
    dx = st.text_input("진단(영문/축약 직접 입력)", value="")
    if dx:
        st.caption(local_dx_display(group, dx))
else:
    st.caption(local_dx_display(group, dx))
