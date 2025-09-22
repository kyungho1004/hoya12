# -*- coding: utf-8 -*-
import streamlit as st
from datetime import datetime, timedelta, timezone
from onco_antipyretic_log import render_onco_antipyretic_log
from peds_dx_log import render_peds_dx_section
from special_tests_addon import render_special_tests
from selftest import run_self_checks
import shim_peds_alias  # ensure alias applied

KST = timezone(timedelta(hours=9))

st.set_page_config(page_title="BloodMap — 탭(국문)", page_icon="🩸", layout="wide")
st.title("BloodMap — 탭 (소아 / 일상 / 질병)")
st.caption("v2025-09-22 p8")

# Self-check banner
checks = run_self_checks()
if all(checks.values()):
    st.success("사전 점검: OK")
else:
    st.warning(f"사전 점검 실패 항목: {checks}")

# 사용자 식별 (기본값 보장)
nick = st.text_input("별명", value="게스트", key="nick_input").strip() or "게스트"
pin  = st.text_input("PIN(4자리)", value="0000", key="pin_input").strip() or "0000"
uid = f"{nick}_{pin}"

# 상태 컨텍스트
if "labs_ctx" not in st.session_state: st.session_state["labs_ctx"] = {}

# 탭: 소아 / 일상 / 질병(=암)
tab_peds, tab_daily, tab_disease = st.tabs(["소아", "일상", "질병"])

with tab_peds:
    st.subheader("소아")
    render_peds_dx_section(nick, uid)
    render_onco_antipyretic_log(nick, uid, apap_next=None, ibu_next=None)
    st.markdown("#### 특수검사")
    st.session_state["labs_ctx"] = render_special_tests(st.session_state.get("labs_ctx", {}))

with tab_daily:
    st.subheader("일상")
    render_onco_antipyretic_log(nick, uid, apap_next=None, ibu_next=None)
    st.markdown("#### 특수검사")
    st.session_state["labs_ctx"] = render_special_tests(st.session_state.get("labs_ctx", {}))

with tab_disease:
    st.subheader("질병(암)")
    render_onco_antipyretic_log(nick, uid, apap_next=None, ibu_next=None)
    st.markdown("#### 특수검사")
    st.session_state["labs_ctx"] = render_special_tests(st.session_state.get("labs_ctx", {}))
