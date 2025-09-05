# -*- coding: utf-8 -*-
import streamlit as st

# Robust import with clear diagnostics on failure
try:
    from bloodmap_app.app import main
except Exception as e:
    st.set_page_config(page_title="피수치 가이드 / BloodMap", layout="centered", initial_sidebar_state="collapsed")
    st.error("❌ 앱 모듈 임포트 중 오류가 발생했습니다. 아래 로그를 확인해주세요.")
    import traceback
    st.code(traceback.format_exc())
    st.stop()

def run():
    st.set_page_config(page_title="피수치 가이드 / BloodMap", layout="centered", initial_sidebar_state="collapsed")
    main()

if __name__ == "__main__":
    run()
