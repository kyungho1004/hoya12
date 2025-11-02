# -*- coding: utf-8 -*-
"""
special_tests_safe.py — Drop-in shim to render Special Tests UI safely
Usage (in app.py tab "특수검사"):

    from special_tests_safe import render_special_tests
    render_special_tests()  # inside the tab/container

This shim:
 - Prevents global Streamlit monkeypatch loops
 - Uses Streamlit originals (text_input/selectbox/text_area)
 - Adapts to different function names in special_tests.py
"""

from __future__ import annotations
import os, importlib, types

def _restore_streamlit_originals():
    try:
        import streamlit as st
    except Exception:
        return
    # keep originals once
    if not hasattr(st, "_bm_text_input_orig"):
        st._bm_text_input_orig = st.text_input
    if not hasattr(st, "_bm_selectbox_orig"):
        st._bm_selectbox_orig = st.selectbox
    if not hasattr(st, "_bm_text_area_orig"):
        st._bm_text_area_orig = st.text_area
    # always reset
    st.text_input  = st._bm_text_input_orig
    st.selectbox   = st._bm_selectbox_orig
    st.text_area   = st._bm_text_area_orig

def _call_best_ui_entry(mod: types.ModuleType):
    """
    Try common entrypoints in order.
    """
    for name in ("special_tests_ui", "render_special_tests", "render", "main", "injector"):
        fn = getattr(mod, name, None)
        if callable(fn):
            return fn()
    # fallback: search any function that looks like a UI builder
    for name in dir(mod):
        if name.startswith(("ui_", "render_", "draw_", "build_")):
            fn = getattr(mod, name, None)
            if callable(fn):
                return fn()
    import streamlit as st
    st.warning("특수검사 UI 엔트리 함수를 찾지 못했어요. special_tests.py 안에 special_tests_ui() 또는 render()를 확인해주세요.")

def render_special_tests():
    """
    Safe renderer for Special Tests.
    """
    # 1) Disable any module-level monkeypatch attempt by convention
    os.environ["BM_DISABLE_ST_PATCH"] = "1"
    # 2) Restore originals before importing the module
    _restore_streamlit_originals()

    # 3) Import or reload special_tests
    try:
        if "special_tests" in globals():
            mod = importlib.reload(globals()["special_tests"])
        elif "special_tests" in importlib.sys.modules:
            mod = importlib.reload(importlib.sys.modules["special_tests"])
        else:
            mod = importlib.import_module("special_tests")
    except Exception as e:
        import streamlit as st
        st.error(f"special_tests 모듈을 불러오지 못했어요: {e}")
        return

    # 4) After import, ensure globals are still originals
    _restore_streamlit_originals()

    # 5) Finally, call the best UI entry
    return _call_best_ui_entry(mod)
