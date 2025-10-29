# -*- coding: utf-8 -*-
# Special Tests shim (patched) — renders even if _ctx_tab is unset
import streamlit as st

def special_tests_ui():
    ss = st.session_state
    # relax gate: render unless _ctx_tab is explicitly set to a non-special value
    if ss.get('_ctx_tab') not in (None, 'special', 't_special'):
        return False
    st.markdown("### 🧪 특수검사 패널(패치)")
    # simple guard to show something to avoid blank page illusion
    st.caption("special_tests 로드: /mnt/data/special_tests.py (shim)")
    # example toggle safe key namespace
    on = st.toggle("전문가용: 응급도 가중치 편집", key="sp_ns_toggle_0", value=bool(ss.get("sp_ns_toggle_0", False)))
    if on:
        st.info("가중치 편집 모드가 켜졌습니다.")
    return True
