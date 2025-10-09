# -*- coding: utf-8 -*-
"""
branding.py (v2) — 배포 배너 렌더링 (폰트 확대 & 안전 동작)
"""
import streamlit as st

def _inject_css_once() -> None:
    """배너 전용 CSS를 중복 없이 1회만 삽입합니다."""
    key = "_bm_css_injected"
    if st.session_state.get(key):
        return
    st.session_state[key] = True
    st.markdown(
        """
<style>
/* BloodMap 배너 전용 스코프 */
#bm-banner { margin: 0 0 0.35rem 0; }
#bm-banner .bm-link {
  font-size: 1.18rem; /* 약간 크게 (기본 대비 +~18%) */
  font-weight: 800;
  text-decoration: none;
}
#bm-banner .bm-link:hover { text-decoration: underline; }
#bm-banner .bm-caption {
  font-size: 1.05rem; /* 캡션도 약간 크게 */
  color: rgba(55,65,81,.95); /* slate-700 근사값 */
  line-height: 1.45;
  margin: .15rem 0 0 0;
}
</style>
        """,
        unsafe_allow_html=True,
    )

def render_deploy_banner(app_url: str="https://bloodmap.streamlit.app", made_by: str="Hoya/GPT") -> None:
    """
    앱 상단에 공식 배포 링크 및 고정 안내를 출력합니다.
    - 링크/캡션 폰트를 기본보다 '약간' 크게 렌더링
    - Streamlit 버전에 무관하게 안정적으로 동작(HTML 링크 사용)
    """
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
