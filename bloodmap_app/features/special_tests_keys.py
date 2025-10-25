"""
Special Tests: key/namespace helpers (standalone, import-safe).
- Keeps session namespace, per-call sub-namespace, and per-name counters.
- Use: set_call_namespace(); tog_key(name); fav_key(name)
"""
from __future__ import annotations

def _session_ns() -> str:
    try:
        import streamlit as st
        ss = st.session_state
        if "_stests_ns" not in ss:
            import uuid
            ss["_stests_ns"] = f"stests_{uuid.uuid4().hex[:6]}"
        return ss["_stests_ns"]
    except Exception:
        return "stests_default"

def set_call_namespace() -> None:
    try:
        import streamlit as st, uuid
        ss = st.session_state
        ss["_stests_call_ns"] = f"{_session_ns()}_{uuid.uuid4().hex[:4]}"
    except Exception:
        pass

def _prefix() -> str:
    try:
        import streamlit as st
        ss = st.session_state
        return ss.get("_stests_call_ns") or _session_ns()
    except Exception:
        return _session_ns()

def _bump(name: str) -> str:
    try:
        import streamlit as st
        ss = st.session_state
        d = ss.get("_stests_key_counts") or {}
        c = int(d.get(name, 0)) + 1
        d[name] = c
        ss["_stests_key_counts"] = d
        return f"{c:02d}"
    except Exception:
        return "01"

def ns_key(kind: str, name: str) -> str:
    return f"{_prefix()}_{kind}_{name}_{_bump(kind+'_'+name)}"

def tog_key(name: str) -> str:
    return ns_key("tog", name)

def fav_key(name: str) -> str:
    return ns_key("fav", name)
