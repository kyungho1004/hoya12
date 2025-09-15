# -*- coding: utf-8 -*-
"""
branding.py
- 앱 상단에 공식 배포/고정 안내를 렌더링하는 유틸 모듈
- 사용법:
    from branding import render_deploy_banner
    from config import MADE_BY, APP_URL
    render_deploy_banner(APP_URL, MADE_BY)
"""
import streamlit as st

def render_deploy_banner(app_url: str, made_by: str) -> None:
    """앱 상단에 공식 배포 링크 및 고정 안내를 출력합니다."""
    try:
        host = app_url.split("//", 1)[-1]
    except Exception:
        host = app_url
    st.markdown(f"[🔗 공식 배포: **{host}**]({app_url})")
    st.caption("※ 모든 날짜/시간은 한국시간(Asia/Seoul) 기준입니다.")
    st.caption("혼돈 방지: 본 앱은 세포·면역 치료(CAR‑T, TCR‑T, NK, HSCT 등)는 표기하지 않습니다.")
    st.caption(made_by)
