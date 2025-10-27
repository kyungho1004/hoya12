
# router.py — 라우터/쿼리파람 가드 헬퍼 (패치 방식)
from __future__ import annotations

def lock_route(route: str):
    try:
        import streamlit as st
        ss = st.session_state
        if ss.get("_route") != route:
            ss["_route"] = route
        if not ss.get("_route_last") or ss.get("_route_last") == "home":
            ss["_route_last"] = route
    except Exception:
        pass

def sync_query(route: str):
    try:
        import streamlit as st
        qp = (st.experimental_get_query_params().get("route") or [""])[0]
        if qp != route:
            st.experimental_set_query_params(route=route)
    except Exception:
        pass
