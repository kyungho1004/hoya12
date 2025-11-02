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

top_guard = """# --- BloodMap Top Guard: restore Streamlit widget originals & block recursion ---
try:
    import streamlit as st
    # 1) Keep originals (first-run only)
    if not hasattr(st, "_bm_text_input_orig"):
        st._bm_text_input_orig = st.text_input
    if not hasattr(st, "_bm_selectbox_orig"):
        st._bm_selectbox_orig = st.selectbox
    if not hasattr(st, "_bm_text_area_orig"):
        st._bm_text_area_orig = st.text_area

    # 2) Always reset to originals
    st.text_input  = st._bm_text_input_orig
    st.selectbox   = st._bm_selectbox_orig
    st.text_area   = st._bm_text_area_orig

    # 3) Safe callers (bypass any wrappers)
    def _BM_TI(*a, **kw):
        fn = getattr(st, "_bm_text_input_orig", st.text_input)
        if fn is _BM_TI:
            fn = st.__dict__.get("_bm_text_input_orig", st.text_input)
        return fn(*a, **kw)

    def _BM_SB(*a, **kw):
        fn = getattr(st, "_bm_selectbox_orig", st.selectbox)
        if fn is _BM_SB:
            fn = st.__dict__.get("_bm_selectbox_orig", st.selectbox)
        return fn(*a, **kw)

    def _BM_TA(*a, **kw):
        fn = getattr(st, "_bm_text_area_orig", st.text_area)
        if fn is _BM_TA:
            fn = st.__dict__.get("_bm_text_area_orig", st.text_area)
        return fn(*a, **kw)
except Exception:
    pass
# --- /Top Guard ---
"""

def patch_app_py(path: pathlib.Path):
    src = path.read_text(encoding="utf-8")
    # Prepend Top Guard once
    if "BloodMap Top Guard" not in src[:4000]:
        src = top_guard + "\n" + src
    # Replace only the login raw_key line (first occurrence)
    src = re.sub(r'raw_key\s*=\s*st\.\s*text_input\s*\(',
                 'raw_key = _BM_TI(',
                 src, count=1)
    ast.parse(src)  # syntax check
    path.write_text(src, encoding="utf-8")

def patch_special_tests(path: pathlib.Path):
    src = path.read_text(encoding="utf-8")
    # Comment-out any global monkeypatch lines (delete nothing)
    src = re.sub(r'(^\s*st\.?\s*(?:_orig_)?text_input\s*=\s*.*$)', r'# [PATCHED-OUT] \1', src, flags=re.MULTILINE)
    src = re.sub(r'(^\s*st\.?\s*(?:_orig_)?selectbox\s*=\s*.*$)', r'# [PATCHED-OUT] \1', src, flags=re.MULTILINE)
    src = re.sub(r'(^\s*st\.?\s*(?:_orig_)?text_area\s*=\s*.*$)',   r'# [PATCHED-OUT] \1', src, flags=re.MULTILINE)
    ast.parse(src)  # syntax check
    path.write_text(src, encoding="utf-8")

def main():
    patch_app_py(app_p)
    patch_special_tests(sp_p)
    print("Hotfix applied OK.")

if __name__ == "__main__":
    main()
