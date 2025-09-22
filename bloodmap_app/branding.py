# -*- coding: utf-8 -*-
"""
branding.py — 배포 배너 렌더링 (폰트 확대 & 안전 동작)
"""
import streamlit as st

def _inject_css_once() -> None:
    key = "_bm_css_injected"
    if st.session_state.get(key):
        return
    st.session_state[key] = True
    st.markdown(
        """
<style>
#bm-banner { margin: 0 0 0.35rem 0; }
#bm-banner .bm-link {
  font-size: 1.18rem;
  font-weight: 800;
  text-decoration: none;
}
#bm-banner .bm-link:hover { text-decoration: underline; }
#bm-banner .bm-caption {
  font-size: 1.05rem;
  color: rgba(55,65,81,.95);
  line-height: 1.45;
  margin: .15rem 0 0 0;
}
</style>
        """,
        unsafe_allow_html=True,
    )

def render_deploy_banner(app_url: str, made_by: str) -> None:
    _inject_css_once()
    try:
        host = app_url.split("//", 1)[-1]
    except Exception:
        host = str(app_url)
    html = f"""
<div id="bm-banner">
  <a class="bm-link" href="{app_url}" target="_blank" rel="noopener noreferrer">🔗 공식 배포: {host}</a>
  <div class="bm-caption">※ 모든 날짜/시간은 한국시간(Asia/Seoul) 기준입니다.</div>
  <div class="bm-caption">혼돈 방지: 본 앱은 세포·면역 치료(CAR‑T, TCR‑T, NK, HSCT 등)는 표기하지 않습니다.</div>
  <div class="bm-caption">{made_by}</div>
</div>
"""
    st.markdown(html, unsafe_allow_html=True)
