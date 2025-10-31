
# === PATCH: Special Tests Stable Keys + Duplicate-Render Guard (v4) ===
# Place this block at the TOP of special_tests.py (do NOT delete existing features).
# Goal: prevent StreamlitDuplicateElementKey while keeping keys stable across reruns.

import streamlit as st
import re
from typing import Optional

# ---- Per-rerun tick & used-keys registry ----
# Increment on every rerun (module reload happens each rerun)
st.session_state["_special_run_tick"] = st.session_state.get("_special_run_tick", 0) + 1
if st.session_state.get("_special_used_keys_tick") != st.session_state["_special_run_tick"]:
    st.session_state["_special_used_keys_tick"] = st.session_state["_special_run_tick"]
    st.session_state["_special_used_keys"] = set()

def _stable_uid() -> str:
    uid = st.session_state.get("_uid")
    if uid:
        return str(uid)
    base = st.session_state.get("key", "guest#unknown")
    return "guest_" + re.sub(r'[^a-zA-Z0-9_.-]', '_', str(base))

def _slug(x: str) -> str:
    return re.sub(r'[^a-zA-Z0-9_.-]+', '_', str(x)).strip('_') or "x"

def _sec_ns(sec_id: Optional[str]) -> str:
    sid = _slug(sec_id or "root")
    return f"{_stable_uid()}.special.v2.{sid}"

def _mint_key(base: str) -> str:
    # Ensure uniqueness within a single rerun, but keep base stable across reruns
    used = st.session_state["_special_used_keys"]
    if base not in used:
        used.add(base)
        return base
    i = 2
    while True:
        k = f"{base}.dup{i}"
        if k not in used:
            used.add(k)
            return k
        i += 1

# ---- Stable key helpers ----
def _tog_key(sec_id: str) -> str:
    return _mint_key(f"{_sec_ns(sec_id)}.tog")

def _fav_key(sec_id: str) -> str:
    return _mint_key(f"{_sec_ns(sec_id)}.fav")

def _w_key(sec_id: str, label: str) -> str:
    return _mint_key(f"{_sec_ns(sec_id)}.w.{_slug(label)}")

def _sel_key(sec_id: str, label: str) -> str:
    return _mint_key(f"{_sec_ns(sec_id)}.sel.{_slug(label)}")

# ---- Optional: Auto-key wrappers (only when key=None) ----
try:
    _orig_toggle = st.toggle
    def _patched_toggle(label, key=None, **kwargs):
        if key is None:
            sec_id = st.session_state.get("_special_current_section", "root")
            key = _tog_key(sec_id)
        return _orig_toggle(label, key=key, **kwargs)
    st.toggle = _patched_toggle
except Exception:
    pass

try:
    _orig_selectbox = st.selectbox
    def _patched_selectbox(label, options, index=0, key=None, **kwargs):
        if key is None:
            sec_id = st.session_state.get("_special_current_section", "root")
            key = _sel_key(sec_id, label)
        return _orig_selectbox(label, options, index=index, key=key, **kwargs)
    st.selectbox = _patched_selectbox
except Exception:
    pass

try:
    _orig_text_input = st.text_input
    def _patched_text_input(label, value="", max_chars=None, key=None, **kwargs):
        if key is None:
            sec_id = st.session_state.get("_special_current_section", "root")
            key = _w_key(sec_id, label)
        return _orig_text_input(label, value=value, max_chars=max_chars, key=key, **kwargs)
    st.text_input = _patched_text_input
except Exception:
    pass

# ---- Section context to avoid double-render in same rerun ----
class special_section:
    def __init__(self, sec_id: str):
        self.sec_id = sec_id
        self._prev = None
        self._skip = False
    def __enter__(self):
        # skip if this section already rendered in current rerun
        stamp = f"{_sec_ns(self.sec_id)}.__rendered"
        if st.session_state.get(stamp) == st.session_state["_special_run_tick"]:
            self._skip = True
        else:
            st.session_state[stamp] = st.session_state["_special_run_tick"]
        # set current section
        self._prev = st.session_state.get("_special_current_section")
        st.session_state["_special_current_section"] = self.sec_id
        return self
    def __exit__(self, exc_type, exc, tb):
        if self._prev is None:
            st.session_state.pop("_special_current_section", None)
        else:
            st.session_state["_special_current_section"] = self._prev
    @property
    def skip(self) -> bool:
        return self._skip

# Usage example inside your UI code:
# with special_section("urine") as sec:
#     if sec.skip:
#         st.info("이미 표시된 섹션입니다.")  # optional
#     else:
#         on = st.toggle("소변 검사 보기")  # key 자동 주입
#         # ...
# === /PATCH ===
