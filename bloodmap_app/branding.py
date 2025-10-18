
# -*- coding: utf-8 -*-
"""
branding.py — BloodMap 배포/고정 멘트 배너 (안전 동작)
- render_deploy_banner(app_url, made_by)
- render_pledge(text)
"""
from __future__ import annotations

import streamlit as st

_CSS_INJECT_KEY = "_bm_branding_css_v3"


def _inject_css_once() -> None:
    """배너 전용 CSS를 중복 없이 1회만 삽입합니다."""
    if st.session_state.get(_CSS_INJECT_KEY):
        return
    st.session_state[_CSS_INJECT_KEY] = True
    st.markdown(
        '''
<style>
/* ===== BloodMap Branding CSS (scoped) ===== */
:root {
  --bm-accent: #2f6feb;
  --bm-muted: #6b7280;
}
#bm-banner, #bm-pledge {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 14px 16px;
  margin: 8px 0 12px 0;
  background: #fafafa;
}
#bm-banner .bm-link {
  font-weight: 700;
  text-decoration: none;
}
#bm-banner .bm-caption {
  font-size: 0.9rem;
  color: var(--bm-muted);
  line-height: 1.4;
  margin-top: 4px;
}
#bm-pledge .bm-title {
  font-size: 1.6rem;
  font-weight: 800;
  line-height: 1.25;
  letter-spacing: -0.02em;
}
@media (max-width: 640px) {
  #bm-pledge .bm-title { font-size: 1.25rem; }
}
</style>
        ''',
        unsafe_allow_html=True,
    )


def render_deploy_banner(app_url: str, made_by: str) -> None:
    """
    앱 상단에 공식 배포 링크 및 고정 안내를 출력합니다.
    - 링크/캡션 폰트를 기본보다 약간 크게 렌더링
    - HTML 마크다운 기반으로 Streamlit 버전 변화에도 안전
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


def render_pledge(text: str) -> None:
    """대문 헤드라인처럼 보이는 고정 멘트를 페이지 어디에서나 렌더링합니다."""
    _inject_css_once()
    text = (text or "").strip()
    if not text:
        return
    # Streamlit 내부 escape 사용
    try:
        esc = st._escape_html  # type: ignore[attr-defined]
    except Exception:
        import html as _html
        esc = _html.escape
    html = f"""
<div id="bm-pledge">
  <div class="bm-title">{esc(text)}</div>
</div>
"""
    st.markdown(html, unsafe_allow_html=True)
