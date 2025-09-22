
# -*- coding: utf-8 -*-
import os, streamlit as st
from datetime import datetime, timedelta, timezone
from onco_antipyretic_log import render_onco_antipyretic_log
from peds_dx_log import render_peds_dx_section
from selftest import run_self_checks

KST = timezone(timedelta(hours=9))
def now_kst(): return datetime.now(KST)

st.set_page_config(page_title="BloodMap — Stable", page_icon="🩸", layout="wide")
st.title("BloodMap — 통합 탭 (Stable)")
st.caption("v2025-09-22 p7-stable")

# ---- Self checks (no crash, only banner) ----
checks = run_self_checks()
ok_all = all(checks.values())
if ok_all:
    st.success("사전 점검: OK — 한국어 라벨/유형·개인별 헤더/파일명·키 네임스페이스 기본 검증 통과")
else:
    st.warning(f"사전 점검 일부 실패: {checks}")

# ---- 사용자 식별 (기본값 보장) ----
nick = st.text_input("별명", value="게스트", key="nick_input").strip() or "게스트"
pin  = st.text_input("PIN(4자리)", value="0000", key="pin_input").strip() or "0000"
uid = f"{nick}_{pin}"

# ---- 탭: 일상 / 소아 / 암 ----
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
    render_onco_antipyretic_log(nick, uid, apap_next=None, ibu_next=None)
