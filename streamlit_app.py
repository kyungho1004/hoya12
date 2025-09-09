# -*- coding: utf-8 -*-
"""Root launcher for Streamlit Cloud.
Imports and runs bloodmap_app.app:main with strong error surfacing to avoid white-screen.
"""
import sys, os, traceback
import streamlit as st

ROOT = os.path.dirname(__file__)
PKG = os.path.join(ROOT, "bloodmap_app")
if PKG not in sys.path:
    sys.path.insert(0, PKG)

try:
    from bloodmap_app import app as bloodmap_app  # type: ignore
except Exception as e:
    st.error("`bloodmap_app` 임포트 실패 — 폴더명/경로를 확인하세요.")
    st.exception(e)
    st.write("sys.path =", sys.path)
    raise

try:
    bloodmap_app.main()
except Exception as e:
    st.error("앱 실행 중 오류 발생")
    st.exception(e)
    st.code("\n".join(traceback.format_exc().splitlines()[-30:]))
