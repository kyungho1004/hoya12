"""
Navigation guards (home-bounce protection & sticky routes).
- Non-intrusive: uses session_state only, never raises.
- Designed to complement existing _block_spurious_home / diagnosis guard.
"""
from __future__ import annotations

def _get(ss, k, default=None):
    try:
        return ss.get(k, default)
    except Exception:
        return default

def _set(ss, k, v):
    try:
        ss[k] = v
    except Exception:
        pass

def remember_route(ss, key: str = "_route", last_key: str = "_route_last"):
    """Store last stable route when it changes."""
    try:
        cur = _get(ss, key)
        last = _get(ss, last_key)
        if cur and cur != last:
            _set(ss, last_key, cur)
    except Exception:
        pass

def prevent_spurious_home(ss, key: str = "_route", last_key: str = "_route_last", nav_flag: str = "_nav_clicked"):
    """If route unexpectedly flips to 'home' without a nav click, restore last route."""
    try:
        cur = _get(ss, key)
        last = _get(ss, last_key)
        nav = bool(_get(ss, nav_flag))
        if cur == "home" and last and last != "home" and not nav:
            _set(ss, key, last)
    except Exception:
        pass

def sticky_route(ss, prefer: str = "dx", flag_key: str = "_dx_active", key: str = "_route"):
    """Keep a preferred route sticky while the flag is true."""
    try:
        if bool(_get(ss, flag_key)) and _get(ss, key) != prefer:
            _set(ss, key, prefer)
    except Exception:
        pass

def apply_all_nav_guards(st):
    """
    Call this early in a page render:
    - remember_route: keep _route_last fresh
    - prevent_spurious_home: bounce back if unintended 'home'
    - sticky_route: keep dx sticky if enabled
    """
    try:
        ss = st.session_state
        remember_route(ss)
        prevent_spurious_home(ss)
        sticky_route(ss, prefer="dx", flag_key="_dx_active")
    except Exception:
        pass
