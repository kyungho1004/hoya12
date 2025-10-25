"""
Diagnosis route guard (home-bounce protection) — non-invasive.
- Restores _route from _route_last if spurious 'home' occurs without explicit nav.
- Optionally force 'dx' if a dx selection flag is set.
"""
from __future__ import annotations

def enforce_route_guard(st, route_key: str = "_route", last_key: str = "_route_last", nav_flag: str = "_nav_clicked", dx_flag: str = "_dx_active"):
    try:
        ss = st.session_state
        cur = ss.get(route_key)
        last = ss.get(last_key)
        nav = bool(ss.get(nav_flag))
        if cur == "home" and last and last != "home" and not nav:
            ss[route_key] = last  # restore last stable route
        # If dx is active, keep it sticky
        if ss.get(dx_flag) and ss.get(route_key) != "dx":
            ss[route_key] = "dx"
    except Exception:
        pass
