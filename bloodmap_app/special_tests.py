# -*- coding: utf-8 -*-
# Special Tests shim (patched v3) — collision-proof keys even on double render
import streamlit as st
import uuid

# module-scope random salt so different modules won't collide even if they copy logic
_MODULE_SALT = uuid.uuid4().hex[:8]

def _ns_uid():
    ss = st.session_state
    if "_sp_ns_uid" not in ss:
        ss["_sp_ns_uid"] = "sp" + uuid.uuid4().hex[:10]
    return ss["_sp_ns_uid"]

def _next_seq():
    ss = st.session_state
    key = "_sp_ns_seq"
    ss[key] = int(ss.get(key, 0)) + 1
    return ss[key]

def special_tests_ui():
    ss = st.session_state
    # relax gate: render unless _ctx_tab is explicitly set to a non-special value
    if ss.get('_ctx_tab') not in (None, 'special', 't_special'):
        return False
    st.markdown("### 🧪 특수검사 패널(패치 v3)")
    st.caption("special_tests 로드: /mnt/data/special_tests.py (shim v3)")
    uid = _ns_uid()
    seq = _next_seq()  # ensure uniqueness across multiple invocations in same run
    # compose an extremely unique key namespace
    key = f"__sp__/toggle/{_MODULE_SALT}/{uid}/{seq}"
    on = st.toggle("전문가용: 응급도 가중치 편집", key=key, value=False)
    if on:
        st.info("가중치 편집 모드가 켜졌습니다.")
    return True
