
# -*- coding: utf-8 -*-
"""
special_tests_finder.py — robust loader + safe renderer for special_tests

Use inside the '특수검사' tab:
    from special_tests_finder import render_special_tests_safe
    render_special_tests_safe()

What it does:
- Searches special_tests.py in common locations (same dir, project root, /mnt/data, etc.)
- If found, loads it WITHOUT global Streamlit monkeypatching (uses originals)
- Tries typical entrypoints: special_tests_ui / render_special_tests / render / main / injector
- If not found, shows a gentle warning and a small demo panel
"""
from __future__ import annotations
import os, sys, importlib, importlib.util, types
from pathlib import Path

COMMON_PATHS = [
    Path(__file__).parent / "special_tests.py",
    Path(__file__).parent.parent / "special_tests.py",
    Path("/mount/src/hoya12/bloodmap_app/special_tests.py"),
    Path("/mnt/data/special_tests.py"),
]

def _restore_streamlit_originals():
    try:
        import streamlit as st
    except Exception:
        return
    if not hasattr(st, "_bm_text_input_orig"):
        st._bm_text_input_orig = st.text_input
    if not hasattr(st, "_bm_selectbox_orig"):
        st._bm_selectbox_orig = st.selectbox
    if not hasattr(st, "_bm_text_area_orig"):
        st._bm_text_area_orig = st.text_area
    st.text_input  = st._bm_text_input_orig
    st.selectbox   = st._bm_selectbox_orig
    st.text_area   = st._bm_text_area_orig

def _load_by_path(p: Path) -> types.ModuleType | None:
    try:
        spec = importlib.util.spec_from_file_location("special_tests", str(p))
        mod = importlib.util.module_from_spec(spec)  # type: ignore
        sys.modules["special_tests"] = mod
        assert spec and spec.loader
        spec.loader.exec_module(mod)  # type: ignore
        return mod
    except Exception as e:
        import streamlit as st
        st.error(f"special_tests 로드 실패: {e}")
        return None

def _find_module() -> types.ModuleType | None:
    # 1) already importable?
    try:
        return importlib.import_module("special_tests")
    except Exception:
        pass
    # 2) search typical paths
    for p in COMMON_PATHS:
        if p.exists():
            return _load_by_path(p)
    return None

def _call_entry(mod: types.ModuleType):
    for name in ("special_tests_ui", "render_special_tests", "injector", "render", "main"):
        fn = getattr(mod, name, None)
        if callable(fn):
            return fn()
    # fallback: any render-like function
    for name in dir(mod):
        if name.startswith(("render_", "ui_", "build_")):
            fn = getattr(mod, name, None)
            if callable(fn):
                return fn()
    import streamlit as st
    st.info("special_tests.py에서 UI 진입 함수를 찾지 못했습니다. special_tests_ui()를 만들어 주세요.")

def render_special_tests_safe():
    import streamlit as st
    os.environ["BM_DISABLE_ST_PATCH"] = "1"  # block any global monkeypatch attempts
    _restore_streamlit_originals()

    mod = _find_module()
    if mod is None:
        st.warning("special_tests.py를 찾지 못해, 특수검사 UI는 데모로 표시됩니다.")
        _restore_streamlit_originals()
        # small demo
        with st.expander("🔧 임시 데모(파일 배치 전) 열기"):
            ti = st._bm_text_input_orig if hasattr(st, "_bm_text_input_orig") else st.text_input
            sb = st._bm_selectbox_orig  if hasattr(st, "_bm_selectbox_orig")  else st.selectbox
            ta = st._bm_text_area_orig  if hasattr(st, "_bm_text_area_orig")  else st.text_area
            _ = ti("예시 입력(임시)", key="demo_st_ti")
            _ = sb("예시 선택(임시)", ["A","B","C"], key="demo_st_sb")
            _ = ta("예시 메모(임시)", key="demo_st_ta")
        st.caption("※ special_tests.py를 app.py와 같은 폴더 또는 /mount/src/hoya12/bloodmap_app/ 에 배치해주세요.")
        return

    # ensure originals after import
    _restore_streamlit_originals()

    return _call_entry(mod)
