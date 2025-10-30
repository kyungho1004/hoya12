# special_tests_safe.py — minimal, safe Special Tests fallback UI
def special_tests_ui():
    import streamlit as st
    st.subheader("🔍 특수검사 해석 (Safe Fallback)")
    on = st.toggle("예시 토글 — 소변검사 패널 표시", value=True, key="sp_demo_urine")
    if on:
        st.markdown("**소변 검사 요약**")
        st.write("- 잠혈: 음성")
        st.write("- 단백뇨: 음성")
        st.write("- 케톤뇨: 음성")
    st.divider()
    st.markdown("✅ 이 화면은 안전 폴백입니다. 실제 모듈이 로드되면 자동으로 교체됩니다.")
    return ["safe-fallback-rendered"]
