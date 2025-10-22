# ae_bridge.py
# Safe helper that exposes adverse-event and user-check maps for the app.
try:
    from drug_db import build_ae_map, build_user_check_map
    ae_map = build_ae_map()
    user_check_map = build_user_check_map()
except Exception:
    ae_map = {}
    user_check_map = {}
__all__ = ["ae_map", "user_check_map"]