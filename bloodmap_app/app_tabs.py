
# -*- coding: utf-8 -*-
import os, streamlit as st
from datetime import datetime, timedelta, timezone
from onco_antipyretic_log import render_onco_antipyretic_log
from peds_dx_log import render_peds_dx_section

KST = timezone(timedelta(hours=9))
def now_kst(): return datetime.now(KST)

st.set_page_config(page_title="BloodMap Tabs", page_icon="🩸", layout="wide")
st.title("BloodMap — 통합 탭")
st.caption("v2025-09-22 p7 (tabs)")

# ---- 간단한 사용자 식별 ----
nick = st.text_input("별명", value=st.session_state.get("nick","게스트"))
pin  = st.text_input("PIN(4자리)", value=st.session_state.get("pin","0000"))
nick = nick or "게스트"
uid = f"{nick}_{pin}"

# 탭: 일상 / 소아 / 암
tab_daily, tab_peds, tab_onco = st.tabs(["일상", "소아", "암"])

with tab_daily:
    st.subheader("일상 모드")
    render_onco_antipyretic_log(nick, uid, apap_next=None, ibu_next=None)

with tab_peds:
    st.subheader("소아 모드")
    render_peds_dx_section(nick, uid)
    render_onco_antipyretic_log(nick, uid, apap_next=None, ibu_next=None)

with tab_onco:
    st.subheader("암 모드")
    # 암 모드에서도 동일 케어로그/해열제 블록 사용 (필요 시 추가 섹션 배치 가능)
    render_onco_antipyretic_log(nick, uid, apap_next=None, ibu_next=None)
