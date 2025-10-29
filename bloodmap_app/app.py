# Minimal route hard-lock helper (optional drop-in for app.py top)
import streamlit as st
def _route_defaults():
    ss = st.session_state
    ss.setdefault("_route", "dx")
    ss.setdefault("_route_last", "dx")
    ss.setdefault("_home_intent", False)

def _route_hardlock():
    ss = st.session_state
    if ss.get("_route") == "home" and not ss.get("_home_intent", False):
        ss["_route"] = ss.get("_route_last", "dx") or "dx"
        st.rerun()

_route_defaults()
_route_hardlock()
