
# -*- coding: utf-8 -*-
import streamlit as st

st.set_page_config(page_title="BloodMap – 해열제 스케줄러", layout="wide")
st.title("암 모드 — 해열제 스케줄 + 설사 시간 기록")

# 안전 임포트
try:
    from antipyretic_schedule import render_antipyretic_schedule
except Exception as e:
    def render_antipyretic_schedule(*args, **kwargs):
        st.error(f"해열제 스케줄러 모듈 임포트 실패: {e}")

st.sidebar.success("✅ PROD — 해열제 스케줄러 통합")

# 항암 스케줄 자리(샘플): 실제 본섭에선 기존 schedule_block() 호출 자리에 본 패널이 따라옵니다.
with st.expander("💊 항암 스케줄 (예시 블록)", expanded=True):
    st.caption("※ 본섭에선 여기에 기존 항암 스케줄 UI가 위치합니다.")

# 요청 위치: 항암 스케줄 바로 밑
with st.expander("🌡️ 해열제 스케줄러", expanded=True):
    render_antipyretic_schedule(storage_key="antipy_sched")
