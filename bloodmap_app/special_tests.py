# -*- coding: utf-8 -*-
# Special Tests shim (patched v2) — avoids duplicate element keys
import streamlit as st
import uuid

def _ns_uid():
    ss = st.session_state
    if "_sp_ns_uid" not in ss:
        ss["_sp_ns_uid"] = "sp" + uuid.uuid4().hex[:10]
    return ss["_sp_ns_uid"]

def special_tests_ui():
    ss = st.session_state
    # relax gate: render unless _ctx_tab is explicitly set to a non-special value
    if ss.get('_ctx_tab') not in (None, 'special', 't_special'):
        return False
    st.markdown("### 🧪 특수검사 패널(패치 v2)")
    st.caption("special_tests 로드: /mnt/data/special_tests.py (shim v2)")
    uid = _ns_uid()
    # unique key per session to avoid collisions across reruns or other modules
    key = f"sp_ns_toggle_{uid}"
    on = st.toggle("전문가용: 응급도 가중치 편집", key=key, value=bool(ss.get(key, False)))
    if on:
        st.info("가중치 편집 모드가 켜졌습니다.")
    return True
