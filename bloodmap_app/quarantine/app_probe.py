# app_probe.py — minimal always-render probe (no dependencies on project code)
import streamlit as st, importlib, sys, traceback

st.set_page_config(page_title="BloodMap Probe", layout="centered")
st.title("🧪 BloodMap Probe — Render/Import Diagnostics")

st.markdown("### 1) Streamlit session")
st.write({
    "python": sys.version,
    "session_keys": list(getattr(st.session_state, "keys", lambda: [])()),
})

st.markdown("### 2) special_tests import status")
info = {}
try:
    m = importlib.import_module("special_tests")
    info["module_file"] = getattr(m, "__file__", None)
    info["has_special_tests_ui"] = hasattr(m, "special_tests_ui")
    info["_wrap_toggle"] = hasattr(m, "_wrap_toggle")
    info["_patched_toggle"] = hasattr(m, "_patched_toggle")
    st.success("special_tests import OK")
except Exception as e:
    info["error"] = repr(e)
    st.error(f"special_tests import failed: {e}")
st.write(info)

st.markdown("### 3) Try calling special_tests_ui safely")
def call_ui():
    try:
        if "m" not in globals():
            mm = importlib.import_module("special_tests")
        else:
            mm = m
        if hasattr(mm, "special_tests_ui"):
            try:
                lines = mm.special_tests_ui()
            except Exception as e:
                st.error(f"UI raised: {e}")
                lines = []
        else:
            st.warning("No special_tests_ui in module.")
            lines = []
    except Exception as e:
        st.error(f"Import/call error: {e}")
        traceback.print_exc()
        lines = []
    st.session_state["special_interpretations"] = lines
    st.write({"special_interpretations": lines})

if st.button("▶ Run special_tests_ui()"):
    call_ui()

st.markdown("---")
st.info("이 페이지가 뜨면 렌더는 정상입니다. 버튼을 눌러도 앱이 꺼지면 special_tests 내부 예외가 원인입니다.")
