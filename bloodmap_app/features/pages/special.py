"""
Modular Special Tests: uses migrated wrapper (robust keys) with legacy fallback.
"""
from __future__ import annotations

def render(st):
    try:
        # Initialize bridge for robust keys (safe no-op if missing)
        try:
            from features.special_tests_bridge import initialize_special_tests_keys as _init
            _init()
        except Exception:
            pass
        # Prefer migrated wrapper
        try:
            from features.special_tests_migrated import render_special_tests_migrated as _mig
            _mig(st)
            return
        except Exception:
            pass
        # Fallback to prior wrapper
        try:
            from features.special_tests_ui import render_special_tests_panel as _legacy_wrap
            _legacy_wrap(st)
        except Exception:
            pass
    except Exception:
        pass
