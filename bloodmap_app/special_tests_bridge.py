# special_tests_bridge.py — safe runner for Special Tests tab
def _import_project_ui():
    try:
        from special_tests import special_tests_ui as project_ui
        return project_ui
    except Exception:
        try:
            from bloodmap_app.special_tests import special_tests_ui as project_ui  # type: ignore
            return project_ui
        except Exception:
            return None

def render_special_tab():
    import streamlit as st
    st.header("🧪 특수검사")
    st.toggle("전문가용: 응급도 가중치 편집", value=False, key="sp_prof_weights")
    st.caption("전문가용 토글을 켜면 응급도 가중치를 편집할 수 있습니다.")

    ui = _import_project_ui()
    lines = []
    try:
        if callable(ui):
            ret = ui()
            if isinstance(ret, (list, tuple)):
                lines.extend(ret)
        else:
            from special_tests_safe import special_tests_ui as safe_ui
            ret = safe_ui()
            if isinstance(ret, (list, tuple)):
                lines.extend(ret)
    except Exception as e:
        st.error("특수검사 UI 실행 중 오류가 발생했지만 앱은 계속 동작합니다.")
        st.caption(f"(safe runner) {type(e).__name__}: {e}")

    if not lines:
        with st.expander("ℹ️ 특수검사 안내가 보이지 않나요? (펼치기)"):
            st.markdown(
                "- 입력값이 없으면 빈 화면일 수 있어요.\n"
                "- 키 충돌은 자동 방지됩니다.\n"
                "- 계속 비면 내부 토글 기본값을 True로 바꿔보세요."
            )
    return lines
