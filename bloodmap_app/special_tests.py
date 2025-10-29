# -*- coding: utf-8 -*-
# bloodmap_app/special_tests.py — safe replacement (collision-proof keys, no hard gate)
import streamlit as st
import uuid

_MODULE_SALT = "03c0d81c"

def _ns_uid():
    ss = st.session_state
    if "_sp_ns_uid" not in ss:
        ss["_sp_ns_uid"] = "sp" + uuid.uuid4().hex[:10]
    return ss["_sp_ns_uid"]

def _next_seq():
    ss = st.session_state
    k = "_sp_ns_seq"
    ss[k] = int(ss.get(k, 0)) + 1
    return ss[k]

def special_tests_ui():
    ss = st.session_state
    # Relaxed gate: render unless explicitly blocked
    # Do NOT require ss['_ctx_tab'] == 'special' to prevent blank screen
    st.markdown("### 🧪 특수검사 패널")
    st.caption("패키지 경로: bloodmap_app/special_tests.py (safe replacement)")
    uid = _ns_uid(); seq = _next_seq()
    key = f"__sp__/toggle/{_MODULE_SALT}/{uid}/{seq}"
    on = st.toggle("전문가용: 응급도 가중치 편집", key=key, value=False)
    if on:
        st.info("가중치 편집 모드가 켜졌습니다.")
    # Return True to signal render happened
    return True
