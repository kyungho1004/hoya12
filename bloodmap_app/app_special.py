
# -*- coding: utf-8 -*-
import streamlit as st
from datetime import datetime, timedelta, timezone
from onco_antipyretic_log import render_onco_antipyretic_log
from peds_dx_log import render_peds_dx_section
from special_tests_addon import render_special_tests

KST = timezone(timedelta(hours=9))
def now_kst(): return datetime.now(KST)

st.set_page_config(page_title="BloodMap — Special", page_icon="🩸", layout="wide")
st.title("BloodMap — 통합 탭 + 특수검사")
st.caption("v2025-09-22 p7-special")

# 사용자 식별 (기본값 보장)
nick = st.text_input("별명", value="게스트").strip() or "게스트"
pin  = st.text_input("PIN(4자리)", value="0000").strip() or "0000"
uid = f"{nick}_{pin}"

# 임시 labs 컨텍스트(기존 앱의 labs 딕셔너리와 호환되도록 설계)
if "labs_ctx" not in st.session_state:
    st.session_state["labs_ctx"] = {}

tab_daily, tab_peds, tab_onco = st.tabs(["일상", "소아", "암"])

with tab_daily:
    st.subheader("일상 모드")
    render_onco_antipyretic_log(nick, uid, apap_next=None, ibu_next=None)
    st.divider()
    st.subheader("특수검사")
    st.session_state["labs_ctx"] = render_special_tests(st.session_state.get("labs_ctx", {}))

with tab_peds:
    st.subheader("소아 모드")
    render_peds_dx_section(nick, uid)
    render_onco_antipyretic_log(nick, uid, apap_next=None, ibu_next=None)
    st.divider()
    st.subheader("특수검사")
    st.session_state["labs_ctx"] = render_special_tests(st.session_state.get("labs_ctx", {}))

with tab_onco:
    st.subheader("암 모드")
    render_onco_antipyretic_log(nick, uid, apap_next=None, ibu_next=None)
    st.divider()
    st.subheader("특수검사")
    st.session_state["labs_ctx"] = render_special_tests(st.session_state.get("labs_ctx", {}))
