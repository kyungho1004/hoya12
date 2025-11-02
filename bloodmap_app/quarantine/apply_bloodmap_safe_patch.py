# -*- coding: utf-8 -*-
"""
apply_bloodmap_safe_patch.py  —  Unified safe patch (non-destructive)
- Patches app.py and special_tests.py in-place with .bak backups
- app.py:
    * Insert Top Guard (restore Streamlit originals) + BM_DISABLE_ST_PATCH=1
    * Replace first login line: st.text_input( → _BM_TI(
    * Comment out global rebind lines (st.text_input = _text_input, etc.)
    * Rename wrapper defs to *_disabled
    * Syntax-check with ast.parse()
- special_tests.py:
    * Inject Monkey-Free Header mapping ORIG_TI/SB/TA to originals
    * Comment out global monkeypatch lines
    * Rewire st._orig_* calls to ORIG_*
    * Syntax-check with ast.parse()
Usage:
    python apply_bloodmap_safe_patch.py
"""

from __future__ import annotations
import os, re, ast, shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
APP = HERE / "app.py"
SP  = HERE / "special_tests.py"

TOP_GUARD = """# --- BloodMap Top Guard (inserted by patch) ---
import os
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
    def _BM_TI(*a, **kw): return st._bm_text_input_orig(*a, **kw)
    def _BM_SB(*a, **kw): return st._bm_selectbox_orig(*a, **kw)
    def _BM_TA(*a, **kw): return st._bm_text_area_orig(*a, **kw)
except Exception:
    pass
os.environ["BM_DISABLE_ST_PATCH"] = "1"
# --- /Top Guard ---
"""

SP_HEADER = """# --- [Monkey-Free Header injected by patch] ---
try:
    import streamlit as st
    ORIG_TI = getattr(st, "_bm_text_input_orig", st.text_input)
    ORIG_SB = getattr(st, "_bm_selectbox_orig", st.selectbox)
    ORIG_TA = getattr(st, "_bm_text_area_orig", st.text_area)
except Exception:
    import streamlit as st  # type: ignore
    ORIG_TI = getattr(st, "_bm_text_input_orig", st.text_input)
    ORIG_SB = getattr(st, "_bm_selectbox_orig", st.selectbox)
    ORIG_TA = getattr(st, "_bm_text_area_orig", st.text_area)
# --- [/Monkey-Free Header] ---
"""

RE_LOGIN = (r'raw_key\s*=\s*st\s*\.\s*text_input\s*\(', 'raw_key = _BM_TI(')
RE_BIND_LINES = [
    r'^\s*st\._orig_text_input\s*=\s*st\.text_input\s*$',
    r'^\s*st\.text_input\s*=\s*_text_input\s*$',
    r'^\s*st\._orig_selectbox\s*=\s*st\.selectbox\s*$',
    r'^\s*st\.selectbox\s*=\s*_selectbox\s*$',
    r'^\s*st\._orig_text_area\s*=\s*st\.text_area\s*$',
    r'^\s*st\.text_area\s*=\s*_text_area\s*$',
]
RE_RENAME_FUNCS = [
    (r'^(\s*)def\s+_text_input\s*\(', r'\1# [PATCHED-OUT WRAPPER]\n\1def _text_input_disabled('),
    (r'^(\s*)def\s+_selectbox\s*\(',  r'\1# [PATCHED-OUT WRAPPER]\n\1def _selectbox_disabled('),
    (r'^(\s*)def\s+_text_area\s*\(',  r'\1# [PATCHED-OUT WRAPPER]\n\1def _text_area_disabled('),
]

def backup(path: Path):
    b = path.with_suffix(path.suffix + ".bak")
    if not b.exists():
        shutil.copy2(path, b)

def insert_top_guard_app(src: str) -> str:
    if "BloodMap Top Guard" not in src[:5000]:
        src = TOP_GUARD + "\n" + src
    return src

def replace_login(src: str) -> str:
    return re.sub(RE_LOGIN[0], RE_LOGIN[1], src, count=1)

def comment_rebinds(src: str) -> str:
    for pat in RE_BIND_LINES:
        src = re.sub(pat, lambda m: "# [PATCHED-OUT] " + m.group(0), src, flags=re.MULTILINE)
    return src

def rename_wrappers(src: str) -> str:
    for pat, repl in RE_RENAME_FUNCS:
        src = re.sub(pat, repl, src, flags=re.MULTILINE)
    return src

def patch_app():
    if not APP.exists():
        return "[WARN] app.py not found — skipped"
    backup(APP)
    src = APP.read_text(encoding="utf-8")
    src = insert_top_guard_app(src)
    src = replace_login(src)
    src = comment_rebinds(src)
    src = rename_wrappers(src)
    ast.parse(src)
    APP.write_text(src, encoding="utf-8")
    return "[OK] app.py patched"

def ensure_sp_header(src: str) -> str:
    if "Monkey-Free Header injected by patch" in src:
        return src
    return SP_HEADER + "\n" + src

def comment_sp_monkey(src: str) -> str:
    pats = [
        r'^\s*st\._orig_text_input\s*=\s*st\.text_input\s*$',
        r'^\s*st\.text_input\s*=\s*_text_input\s*$',
        r'^\s*st\._orig_selectbox\s*=\s*st\.selectbox\s*$',
        r'^\s*st\.selectbox\s*=\s*_selectbox\s*$',
        r'^\s*st\._orig_text_area\s*=\s*st\.text_area\s*$',
        r'^\s*st\.text_area\s*=\s*_text_area\s*$',
    ]
    for pat in pats:
        src = re.sub(pat, lambda m: "# [PATCHED-OUT] " + m.group(0), src, flags=re.MULTILINE)
    return src

def rewire_sp_calls(src: str) -> str:
    src = re.sub(r'st\._orig_text_input\s*\(', 'ORIG_TI(', src)
    src = re.sub(r'st\._orig_selectbox\s*\(', 'ORIG_SB(', src)
    src = re.sub(r'st\._orig_text_area\s*\(', 'ORIG_TA(', src)
    return src

def patch_special_tests():
    if not SP.exists():
        return "[WARN] special_tests.py not found — skipped"
    backup(SP)
    src = SP.read_text(encoding="utf-8")
    src = ensure_sp_header(src)
    src = comment_sp_monkey(src)
    src = rewire_sp_calls(src)
    ast.parse(src)
    SP.write_text(src, encoding="utf-8")
    return "[OK] special_tests.py patched"

def main():
    msgs = [patch_app(), patch_special_tests()]
    print("\\n".join([m for m in msgs if m]))

if __name__ == "__main__":
    main()
