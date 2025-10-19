
# -*- coding: utf-8 -*-
"""
p1_ui_peds.py — P1: 소아 탭 UI 모듈 (Sticky Quick-Nav, ORS PDF 버튼)
패치 방식 준수: import하여 함수 호출로 UI를 렌더링합니다.
"""
from __future__ import annotations
import streamlit as st

def render_sticky_nav() -> None:
    """소아 탭 상단 고정 네비게이터 렌더."""
    st.markdown(
        """
        <style>
        .peds-sticky{position:sticky; top:64px; z-index:9; background:rgba(250,250,250,0.9);
                     padding:8px 8px; border:1px solid #eee; border-radius:10px;}
        .peds-sticky a{margin-right:10px; font-weight:600; text-decoration:none;}
        </style>
        <div class="peds-sticky">
        <a href="#peds_constipation">변비</a>
        <a href="#peds_diarrhea">설사</a>
        <a href="#peds_vomit">구토</a>
        <a href="#peds_antipyretic">해열제</a>
        <a href="#peds_ors">ORS</a>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_ors_pdf_button() -> None:
    """ORS 가이드 원클릭 PDF 저장 버튼 렌더."""
    try:
        import pdf_export as _pdf
    except Exception:
        _pdf = None
    if st.button('ORS 가이드 PDF 저장', key='ors_pdf_btn'):
        try:
            path = _pdf.export_ors_onepager() if (_pdf and hasattr(_pdf, 'export_ors_onepager')) else None
            if path:
                with open(path, 'rb') as f:
                    st.download_button('PDF 다운로드', f, file_name='ORS_guide.pdf',
                                       mime='application/pdf', key='ors_pdf_dl')
            else:
                st.info('pdf_export.export_ors_onepager를 찾지 못했습니다.')
        except Exception as e:
            st.warning('PDF 생성 오류: ' + str(e))
