
# -*- coding: utf-8 -*-
"""
p1_ui_report.py — P1: 보고서 탭 UI 모듈 (Special Notes 편집기)
"""
from __future__ import annotations
import os
import streamlit as st

NOTES_PATH = "/mnt/data/profile/special_notes.txt"

def render_special_notes_panel() -> None:
    """특수 메모 입력/저장 패널 렌더."""
    with st.expander('📝 Special Notes (환자별 메모)', expanded=False):
        try:
            os.makedirs('/mnt/data/profile', exist_ok=True)
            if 'special_notes' not in st.session_state:
                if os.path.exists(NOTES_PATH):
                    st.session_state['special_notes'] = open(NOTES_PATH,'r',encoding='utf-8').read()
                else:
                    st.session_state['special_notes'] = ''
        except Exception:
            st.session_state['special_notes'] = st.session_state.get('special_notes','')

        val = st.text_area('메모(보고서/PDF에 첨부 용)',
                           st.session_state.get('special_notes',''),
                           height=140, key='special_notes_ta')
        colA, colB = st.columns([1,1])
        with colA:
            if st.button('저장', key='special_notes_save'):
                try:
                    open(NOTES_PATH,'w',encoding='utf-8').write(val or '')
                    st.session_state['special_notes'] = val or ''
                    st.success('저장 완료')
                except Exception as e:
                    st.warning('저장 오류: ' + str(e))
        with colB:
            if st.button('초기화', key='special_notes_reset'):
                st.session_state['special_notes'] = ''
                try:
                    open(NOTES_PATH,'w',encoding='utf-8').write('')
                except Exception:
                    pass
