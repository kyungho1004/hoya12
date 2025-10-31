
# === PATCH: Stable key helpers for Special Tests (v2, patch-only) ===
# Drop this block at the TOP of your existing `special_tests.py` (without deleting anything),
# or replace your existing helper key functions with these. It keeps keys STABLE across reruns.
# - No deletion of features or paths
# - Keys incorporate a stable session UID + fixed section id
# - Avoids per-render counters which break persistence

import streamlit as st
import re
from typing import Optional

def _stable_uid() -> str:
    # Prefer existing session _uid; fall back to hashed "key" (nickname#PIN) to keep stable within session
    uid = st.session_state.get("_uid")
    if uid:
        return str(uid)
    base = st.session_state.get("key", "guest#unknown")
    return "guest_" + re.sub(r'[^a-zA-Z0-9_.-]', '_', base)

def _slug(x: str) -> str:
    return re.sub(r'[^a-zA-Z0-9_.-]+', '_', str(x)).strip('_') or "x"

def _sec_ns(sec_id: Optional[str]) -> str:
    sid = _slug(sec_id or "root")
    return f"{_stable_uid()}.special.v2.{sid}"

# ---- Stable key generators (PATCH) ----
def _tog_key(sec_id: str) -> str:
    # Used for st.toggle per section
    return f"{_sec_ns(sec_id)}.tog"

def _fav_key(sec_id: str) -> str:
    # If you had a "favorite" star/heart toggle
    return f"{_sec_ns(sec_id)}.fav"

def _w_key(sec_id: str, label: str) -> str:
    # For text_input/number_input keys
    return f"{_sec_ns(sec_id)}.w.{_slug(label)}"

def _sel_key(sec_id: str, label: str) -> str:
    # For selectbox/radio keys
    return f"{_sec_ns(sec_id)}.sel.{_slug(label)}"

# ---- OPTIONAL: safe wrappers (won't override if already patched) ----
# If your code calls st.toggle/ st.selectbox without key=, these wrappers inject stable keys.
try:
    _orig_toggle = st.toggle
    def _patched_toggle(label, key=None, **kwargs):
        if key is None:
            sec_id = st.session_state.get("_special_current_section", "root")
            key = _tog_key(sec_id)
        return _orig_toggle(label, key=key, **kwargs)
    st.toggle = _patched_toggle  # monkeypatch
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

# Helper context to mark current section (optional, use if convenient)
class special_section:
    def __init__(self, sec_id: str):
        self.sec_id = sec_id
        self._prev = None
    def __enter__(self):
        self._prev = st.session_state.get("_special_current_section")
        st.session_state["_special_current_section"] = self.sec_id
    def __exit__(self, exc_type, exc, tb):
        if self._prev is None:
            st.session_state.pop("_special_current_section", None)
        else:
            st.session_state["_special_current_section"] = self._prev
# === /PATCH ===
