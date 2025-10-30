# route_patch_safest.py — safe shims for routing; prevents NameError and home-bounce
# Import this as early as possible in app.py, ideally right after ui_patch_safest.

def _install_route_shims():
    try:
        import builtins, streamlit as st
    except Exception:
        return

    ss = st.session_state

    # Ensure allowed routes (non-invasive: only if missing)
    if not hasattr(builtins, "ALLOWED_ROUTES"):
        builtins.ALLOWED_ROUTES = {"home", "dx", "ae", "special", "exports", "peds"}

    # Safe _pin_route if missing
    if not hasattr(builtins, "_pin_route"):
        def _pin_route(name: str):
            # Stick route to desired tab and remember last non-home route
            try:
                ss.setdefault("_route", "home")
                ss.setdefault("_route_last", "home")
                # keep last before change
                if ss.get("_route") != name:
                    ss["_route_last"] = ss.get("_route", "home")
                ss["_route"] = name
            except Exception:
                pass
        builtins._pin_route = _pin_route

    # Optional: helper to keep from bouncing to home on selectbox changes
    if not hasattr(builtins, "_route_lock_to"):
        def _route_lock_to(name: str):
            try:
                ss.setdefault("_route", name)
                ss.setdefault("_route_last", name)
                ss["_route"] = name
                ss["_route_last"] = name
            except Exception:
                pass
        builtins._route_lock_to = _route_lock_to

_install_route_shims()
