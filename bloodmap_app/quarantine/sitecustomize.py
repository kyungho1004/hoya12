# -*- coding: utf-8 -*-
"""
sitecustomize.py — BloodMap self-healing guard (patch-only, idempotent)

Drop this file into: /mount/src/hoya12/bloodmap_app/

Python auto-imports sitecustomize.py before running your app,
so this will patch the files ONCE on startup (no commands needed).

What it does (non-destructive, with .bak backups):
  1) app.py: prepend Top Guard (restore Streamlit widget originals + safe callers)
  2) app.py: replace only the login line st.text_input(...) -> _BM_TI(...)
  3) special_tests.py: comment-out any global monkeypatch lines (delete nothing)

Backups:
  - app.py.bak, special_tests.py.bak
"""
from __future__ import annotations
import re, ast, pathlib, shutil, sys

APP_DIR = pathlib.Path(__file__).resolve().parent
APP_PY  = APP_DIR / "app.py"
SP_PY   = APP_DIR / "special_tests.py"

TOP_GUARD = """# --- BloodMap Top Guard: restore Streamlit widget originals & block recursion ---
try:
    import streamlit as st
    if not hasattr(st, "_bm_text_input_orig"):
        st._bm_text_input_orig = st.text_input
    if not hasattr(st, "_bm_selectbox_orig"):
        st._bm_selectbox_orig = st.selectbox
    if not hasattr(st, "_bm_text_area_orig"):
        st._bm_text_area_orig = st.text_area

    st.text_input  = st._bm_text_input_orig
    st.selectbox   = st._bm_selectbox_orig
    st.text_area   = st._bm_text_area_orig

    def _BM_TI(*a, **kw):
        fn = getattr(st, "_bm_text_input_orig", st.text_input)
        return fn(*a, **kw)

    def _BM_SB(*a, **kw):
        fn = getattr(st, "_bm_selectbox_orig", st.selectbox)
        return fn(*a, **kw)

    def _BM_TA(*a, **kw):
        fn = getattr(st, "_bm_text_area_orig", st.text_area)
        return fn(*a, **kw)
except Exception:
    pass
# --- /Top Guard ---
"""

def _backup(p: pathlib.Path):
    b = p.with_suffix(p.suffix + ".bak")
    try:
        if not b.exists():
            shutil.copy2(p, b)
    except Exception:
        pass

def _patch_app_py(p: pathlib.Path):
    src = p.read_text(encoding="utf-8")
    changed = False
    if "BloodMap Top Guard" not in src[:4000]:
        src = TOP_GUARD + "\n" + src
        changed = True
    # Replace only the first login line occurrence
    new_src = re.sub(r'raw_key\s*=\s*st\.\s*text_input\s*\(',
                     'raw_key = _BM_TI(',
                     src, count=1)
    if new_src != src:
        changed = True
        src = new_src
    if changed:
        ast.parse(src)  # syntax sanity
        p.write_text(src, encoding="utf-8")

def _patch_special_tests(p: pathlib.Path):
    src = p.read_text(encoding="utf-8")
    new_src = re.sub(r'(^\s*st\.?\s*(?:_orig_)?text_input\s*=\s*.*$)', r'# [PATCHED-OUT] \1', src, flags=re.MULTILINE)
    new_src = re.sub(r'(^\s*st\.?\s*(?:_orig_)?selectbox\s*=\s*.*$)', r'# [PATCHED-OUT] \1', new_src, flags=re.MULTILINE)
    new_src = re.sub(r'(^\s*st\.?\s*(?:_orig_)?text_area\s*=\s*.*$)',   r'# [PATCHED-OUT] \1', new_src, flags=re.MULTILINE)
    if new_src != src:
        ast.parse(new_src)
        p.write_text(new_src, encoding="utf-8")

try:
    if APP_PY.exists():
        _backup(APP_PY); _patch_app_py(APP_PY)
    if SP_PY.exists():
        _backup(SP_PY); _patch_special_tests(SP_PY)
except Exception as e:
    # Fail-safe: never block app import
    sys.stderr.write(f"[sitecustomize] patch skipped: {e}\n")
