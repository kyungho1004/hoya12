# -*- coding: utf-8 -*-
"""
BloodMap Recursion Hotfix (patch-only, non-destructive)

Usage (in /mount/src/hoya12/bloodmap_app):
    python hotfix_recursion_guard.py

What it does:
 1) Prepend a Top Guard to app.py (restore Streamlit widget originals + safe callers)
 2) Replace only the login line: st.text_input(...) -> _BM_TI(...)
 3) Comment-out any global monkeypatch lines in special_tests.py (delete nothing)
"""
import re, io, ast, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent
app_p = ROOT / "app.py"
sp_p  = ROOT / "special_tests.py"

top_guard = r