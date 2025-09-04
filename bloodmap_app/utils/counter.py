
try:
    from ..util_core import bump, count
except Exception:
    import streamlit as st
    def bump():
        st.session_state.setdefault("_bm_counter", 0)
        st.session_state["_bm_counter"] += 1
    def count():
        return st.session_state.get("_bm_counter", 0)
