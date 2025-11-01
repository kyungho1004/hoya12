# ==== PATCH • Import Guard for special_tests (non-destructive) ====
from __future__ import annotations
import sys, os, importlib, types

# 1) Ensure app directory and its parent are on sys.path
try:
    _here = os.path.dirname(os.path.abspath(__file__))
except Exception:
    _here = os.getcwd()

_candidates = [
    _here,
    os.path.dirname(_here),
]

for _p in _candidates:
    if _p and _p not in sys.path:
        sys.path.insert(0, _p)

def _try_import(module_name: str):
    try:
        return importlib.import_module(module_name)
    except Exception:
        return None

# 2) Try several common locations
_mod = (
    _try_import("special_tests")
    or _try_import("bloodmap_app.special_tests")
)

# 3) If found, alias as `special_tests` for consistent downstream imports
if _mod is not None:
    sys.modules.setdefault("special_tests", _mod)
else:
    # Optional: Drop a hint into Streamlit session for diagnostics
    try:
        import streamlit as st  # type: ignore
        st.session_state["_sp_import_warning"] = True
        st.session_state["_sp_import_paths"] = list(sys.path)[:6]
    except Exception:
        pass
# ==== /PATCH END ====