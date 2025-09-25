# diagnostic_app.py — environment & log helper
import os, sys, platform, json
import streamlit as st

st.set_page_config(page_title="Diagnostics", layout="wide")
st.title("🔧 Diagnostics")

st.subheader("Python / Platform")
st.code("\n".join([
    f"python: {sys.version}",
    f"executable: {sys.executable}",
    f"platform: {platform.platform()}",
    f"cwd: {os.getcwd()}",
]))

st.subheader("Env (filtered)")
env = {k:v for k,v in os.environ.items() if k.upper() in {"PYTHONPATH","HOME","PATH","VIRTUAL_ENV","STREAMLIT_SERVER_PORT","PORT"}}
st.json(env)

st.subheader("Files in CWD")
st.code("\n".join(sorted(os.listdir("."))))

st.subheader("Imported packages quick check")
try:
    import streamlit as _st; ok = True
    st.success("streamlit import OK")
except Exception as e:
    st.error(f"streamlit import FAILED: {e!r}")

st.subheader("Session state")
st.json(dict(st.session_state))
