# -*- coding: utf-8 -*-
import os, sys, traceback
import streamlit as st

# Ensure package root on path
PKG_DIR = os.path.dirname(__file__)
if PKG_DIR not in sys.path:
    sys.path.insert(0, PKG_DIR)

# Imports from skeleton
try:
    from utils import user_key, init_state
    from utils.inputs import collect_basic_inputs
    from utils.interpret import interpret_labs, status_color
    from utils.reports import build_markdown_report
    from utils.counter import bump_count, get_count
    from data.drugs import get_drugs
    from data.foods import foods_for, ANC_LOW_GUIDE
except Exception as e:
    st.error("모듈 임포트 실패: 패키지 구조/파일명을 확인하세요.")
    st.exception(e)
    raise

APP_NAME = "BloodMap 피수치 가이드 (SafeBoot)"
DISCLAIMER = "본 도구는 보호자의 이해를 돕기 위한 참고용 정보이며, 모든 의학적 판단은 의료진의 판단을 따르세요."

def page_header():
    st.set_page_config(page_title=APP_NAME, layout="wide")
    st.title(APP_NAME)
    try:
        n = bump_count()
        st.caption(f"조회수 카운트: {n:,}")
    except Exception:
        pass

def sidebar_user():
    st.sidebar.header("사용자")
    nickname = st.sidebar.text_input("별명")
    pin = st.sidebar.text_input("PIN(4자리)", max_chars=4)
    key = user_key(nickname, pin)
    st.sidebar.caption(f"식별키: {key}")
    return key

def render_labs_and_interpret():
    st.subheader("피수치 입력")
    labs = collect_basic_inputs()
    if not labs:
        st.info("왼쪽/위 입력창에 수치를 입력하면 자동으로 해석됩니다.")
        return
    st.subheader("해석 결과")
    items = interpret_labs(labs)
    for k, v, level, hint in items:
        color = status_color(level)
        st.markdown(f"- **{k}**: {v} → <span class='badge {color}'>{level}</span> · {hint}", unsafe_allow_html=True)
    # 음식 추천 (예시: 알부민 낮음)
    if "Albumin" in labs and labs["Albumin"] < 3.5:
        st.write("### 음식 추천 (알부민 낮음)")
        for f in foods_for("알부민 낮음"):
            st.write("• ", f)
    # 보고서
    nickname_pin = "사용자"
    md = build_markdown_report(nickname_pin, items)
    st.download_button("보고서(.md) 다운로드", md, file_name="bloodmap_report.md")

def main():
    try:
        page_header()
        sidebar_user()
        render_labs_and_interpret()
        st.markdown("> " + DISCLAIMER)
    except Exception as e:
        st.error("런타임 오류가 발생했습니다. 아래 상세를 확인하세요.")
        st.exception(e)
        st.code("\n".join(traceback.format_exc().splitlines()[-20:]))

if __name__ == "__main__":
    main()
