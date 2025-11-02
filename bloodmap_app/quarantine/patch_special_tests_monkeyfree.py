# -*- coding: utf-8 -*-
"""
patch_special_tests_monkeyfree.py
- Purpose: Make special_tests.py render again WITHOUT global monkeypatching.
- What it does (idempotent):
  1) Backs up special_tests.py -> special_tests.py.bak
  2) Injects a small header that maps ORIG_TI/SB/TA to Streamlit originals
  3) Comments out global monkeypatch lines like:
        st._orig_text_input = st.text_input
        st.text_input = _text_input
        st._orig_selectbox = st.selectbox
        st.selectbox = _selectbox
        st._orig_text_area = st.text_area
        st.text_area = _text_area
  4) Replaces any call to st._orig_text_input(...) with ORIG_TI(...)
     and similarly for selectbox/text_area.
- Usage (run in the folder that contains special_tests.py):
    python patch_special_tests_monkeyfree.py
"""
import re, ast, pathlib, shutil

HERE = pathlib.Path(__file__).resolve().parent
SP   = HERE / "special_tests.py"

HEADER = """# --- [Monkey-Free Header injected by patch_special_tests_monkeyfree.py] ---
try:
    import streamlit as st
    ORIG_TI = getattr(st, "_bm_text_input_orig", st.text_input)
    ORIG_SB = getattr(st, "_bm_selectbox_orig", st.selectbox)
    ORIG_TA = getattr(st, "_bm_text_area_orig", st.text_area)
except Exception:
    # late import fallback
    import streamlit as st  # type: ignore
    ORIG_TI = getattr(st, "_bm_text_input_orig", st.text_input)
    ORIG_SB = getattr(st, "_bm_selectbox_orig", st.selectbox)
    ORIG_TA = getattr(st, "_bm_text_area_orig", st.text_area)
# --- [/Monkey-Free Header] ---
"""

def backup(p: pathlib.Path):
    b = p.with_suffix(p.suffix + ".bak")
    if not b.exists():
        shutil.copy2(p, b)

def ensure_header(src: str) -> str:
    if "Monkey-Free Header injected" in src:
        return src
    # after first import section is a good place; otherwise prepend.
    return HEADER + "\n" + src

def comment_monkeypatches(src: str) -> str:
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

def rewire_calls_to_originals(src: str) -> str:
    # st._orig_text_input(...) -> ORIG_TI(...)
    src = re.sub(r'st\._orig_text_input\s*\(', 'ORIG_TI(', src)
    src = re.sub(r'st\._orig_selectbox\s*\(', 'ORIG_SB(', src)
    src = re.sub(r'st\._orig_text_area\s*\(', 'ORIG_TA(', src)
    return src

def main():
    if not SP.exists():
        print("[ERR] special_tests.py not found in this folder.")
        return 2
    backup(SP)
    src = SP.read_text(encoding="utf-8")
    src = ensure_header(src)
    src = comment_monkeypatches(src)
    src = rewire_calls_to_originals(src)
    # Syntax check
    ast.parse(src)
    SP.write_text(src, encoding="utf-8")
    print("[OK] Patched special_tests.py (monkeypatch-free, using ORIG_*). Backup: special_tests.py.bak")

if __name__ == "__main__":
    main()
