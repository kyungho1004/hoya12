
import os, sys, json, importlib, traceback
import datetime as _dt

# Lazy import streamlit only when available to avoid masking import errors
try:
    import streamlit as st
except Exception as e:
    print("STREAMLIT_IMPORT_ERROR::", e)
    raise

st.set_page_config(page_title="BloodMap Safe Boot", page_icon="🩸", layout="centered")

st.title("🩸 BloodMap Safe Boot")
st.caption("KST: " + _dt.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z"))
st.write("이 페이지는 환경/임포트 문제를 **즉시** 드러내기 위한 최소 앱입니다.")

MODULES = ["branding", "special_tests", "lab_diet", "onco_map", "drug_db", "ui_results", "pdf_export"]
results = {}

for name in MODULES:
    try:
        mod = importlib.import_module(name)
        attrs = [a for a in dir(mod) if not a.startswith("_")]
        results[name] = {"status": "ok", "attrs_sample": attrs[:8]}
    except Exception as e:
        results[name] = {"status": "error", "error": f"{type(e).__name__}: {e}", "trace": traceback.format_exc()}

st.subheader("임포트 상태")
st.json(results)

st.subheader("파이썬/패키지 정보")
st.write({
    "python": sys.version,
    "executable": sys.executable,
    "cwd": os.getcwd(),
    "env_STREAMLIT_SERVER_PORT": os.environ.get("PORT") or os.environ.get("STREAMLIT_SERVER_PORT"),
})

st.success("✅ Safe Boot 완료: 이 화면이 보이면 프레임워크 자체는 기동 중입니다.")
