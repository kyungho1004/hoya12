try:
    ONCO_MAP
except NameError:
    try:
        from onco_map import build_onco_map
        ONCO_MAP = build_onco_map()
    except Exception:
        ONCO_MAP = {}

try:
    local_dx_display
except NameError:
    def local_dx_display(group: str, dx: str) -> str:
        group = (group or "").strip()
        dx = (dx or "").strip()
        return f"{group} - {dx}" if group else dx

# 암 카테고리/진단 셀렉트 (format_func 핫픽스 포함)
import streamlit as st
group = st.selectbox("암 카테고리", ["혈액암","림프종","고형암","육종","희귀암"])
dx_options = list((ONCO_MAP.get(group, {}) or {}).keys())

def _dx_fmt(opt: str) -> str:
    try:
        return local_dx_display(group, opt)
    except Exception:
        return str(opt)

dx = st.selectbox("진단(영문+한글)", dx_options or ["직접 입력"], format_func=_dx_fmt)
