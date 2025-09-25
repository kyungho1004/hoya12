import streamlit as st
from modules.branding import render_deploy_banner
from modules.lab_interpreter import render_interpreter_ui
from modules.report_generator import render_report_ui
from modules.care_log_ui import render_care_log_ui
from modules.profile_ui import render_profile_ui
from modules.graph_ui import render_graph_ui

st.set_page_config(page_title="BloodMap", layout="wide")
st.title("🩸 BloodMap 피수치 해석기")
render_deploy_banner()

# 사이드바 정보 표시
with st.sidebar:
    st.header("📁 메뉴")
    selected = st.radio("이동할 기능을 선택하세요:", [
        "피수치 해석기", "보고서 생성", "그래프 보기", "케어 로그", "사용자 프로필"
    ])

# 선택된 기능 렌더링
if selected == "피수치 해석기":
    render_interpreter_ui()
elif selected == "보고서 생성":
    render_report_ui()
elif selected == "그래프 보기":
    render_graph_ui()
elif selected == "케어 로그":
    render_care_log_ui()
elif selected == "사용자 프로필":
    render_profile_ui()
