# -*- coding: utf-8 -*-
# Streamlit robust launcher (bloodmap_app 전용, 레거시 'bloodmap' 경로 차단)
import sys, os, importlib
import streamlit as st

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# 레거시 모듈명 차단(안전장치)
sys.modules.pop("bloodmap", None)

try:
    mod = importlib.import_module("bloodmap_app.app")
    mod.main()
except Exception as e:
    st.set_page_config(page_title="피수치 가이드 / BloodMap", layout="centered")
    st.title("🩸 피수치 가이드 — 실행 오류")
    st.error("`bloodmap_app.app.main()` 실행에 실패했습니다.")
    st.code(str(e))
    st.info(
        "확인 사항\n"
        "1) 루트에 streamlit_app.py 가 있고,\n"
        "2) bloodmap_app/ 폴더가 존재하며,\n"
        "3) bloodmap_app/__init__.py 가 있으며,\n"
        "4) bloodmap_app/app.py 안에 main() 함수가 있어야 합니다."
    )
