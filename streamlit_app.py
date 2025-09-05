# -*- coding: utf-8 -*-
import streamlit as st

try:
    from bloodmap_app.app import main
except Exception:
    st.error("❌ 앱 모듈 임포트 중 오류가 발생했습니다. 아래 로그를 확인해주세요.")
    import traceback
    st.code(traceback.format_exc())
    st.stop()

if __name__ == "__main__":
    # page_config는 app.py에서만 설정 (중복 방지)
    main()
