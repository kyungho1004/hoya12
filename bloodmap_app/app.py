# app.py — Ultra-safe Classic (Lazy import; tabs always clickable)
import sys, pathlib, importlib, inspect
import streamlit as st
st.set_page_config(page_title="🩸 피수치 해석기 — 클래식", layout="wide")

APP_DIR = pathlib.Path(__file__).parent.resolve()
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

APP_URL = "https://bloodmap.streamlit.app/"
MADE_BY = "Hoya/GPT"

def call_compat(fn, **kwargs):
    try:
        sig = inspect.signature(fn)
        return fn(**{k:v for k,v in kwargs.items() if k in sig.parameters})
    except Exception:
        return fn()

def safe_import(name):
    try:
        return importlib.import_module(name)
    except Exception as e:
        st.caption(f"[임포트 생략] {name}: {e}")
        return None

# ---- Top banner (lazy & guarded) ----
with st.container():
    try:
        branding = safe_import("branding")
        if branding and hasattr(branding, "render_deploy_banner"):
            call_compat(branding.render_deploy_banner, st=st, app_url=APP_URL, made_by=MADE_BY)
    except Exception as e:
        st.caption(f"branding skipped: {e}")

# ====== Tabs (no heavy work before this line!) ======
tabs = st.tabs(["홈", "소아", "암 선택", "항암제", "특수검사", "보고서", "케어로그"])

# -------- 홈 --------
with tabs[0]:
    st.title("🩸 BloodMap — Classic")
    st.subheader("홈")
    st.write("이곳은 클래식 홈 화면입니다.")
    try:
        alerts = safe_import("alerts")
        if alerts:
            for fn in ["render_recent_risk_banner","render_risk_banner"]:
                f = getattr(alerts, fn, None)
                if callable(f):
                    call_compat(f, st=st)
                    break
    except Exception as e:
        st.caption(f"alerts skipped: {e}")

# -------- 소아 (lazy) --------
with tabs[1]:
    st.subheader("소아")
    try:
        peds = (safe_import("pages_peds") or safe_import("peds_symptoms_ui") or safe_import("peds_guide"))
        done = False
        for fn in ["render_peds_page","render","render_page","peds_main","main","show"]:
            f = getattr(peds, fn, None) if peds else None
            if callable(f):
                call_compat(f, st=st)
                done = True
                break
        if not done:
            st.info("소아 전용 모듈이 준비되지 않았습니다.")
    except Exception as e:
        st.error(f"소아 탭 오류: {e}")

# -------- 암 선택 (lazy) --------
with tabs[2]:
    st.subheader("암 선택")
    try:
        router = (safe_import("router") or safe_import("route_patch_safest") or safe_import("app_router"))
        done = False
        for fn in ["render_dx_selector","render_dx_panel","render","main","show"]:
            f = getattr(router, fn, None) if router else None
            if callable(f):
                call_compat(f, st=st)
                done = True
                break
        if not done:
            st.info("암/진단 선택 모듈이 준비되지 않았습니다.")
    except Exception as e:
        st.error(f"암 선택 탭 오류: {e}")

# -------- 항암제 (lazy) --------
with tabs[3]:
    st.subheader("항암제")
    try:
        onco = (safe_import("onco_map") or safe_import("drug_db"))
        done = False
        for fn in ["render_chemo_panel","render_onco_drugs","render","main","show"]:
            f = getattr(onco, fn, None) if onco else None
            if callable(f):
                call_compat(f, st=st)
                done = True
                break
        if not done:
            st.info("항암제 패널이 준비되지 않았습니다.")
    except Exception as e:
        st.error(f"항암제 탭 오류: {e}")

# -------- 특수검사 (lazy + injector fallback) --------
with tabs[4]:
    st.subheader("특수검사")
    try:
        # prefer injector
        try:
            _sp = importlib.import_module("app_special_lock_inject")
            ui = getattr(_sp, "special_tests_ui", None)
        except Exception:
            _sp = None
            ui = None
        if not callable(ui):
            # inline safe loader
            import importlib.util
            candidate = APP_DIR / "special_tests.py"
            if candidate.exists():
                spec = importlib.util.spec_from_file_location("special_tests", str(candidate))
                mod = importlib.util.module_from_spec(spec)
                sys.modules["special_tests"] = mod
                spec.loader.exec_module(mod)
                ui = getattr(mod, "special_tests_ui", None)
        if callable(ui):
            lines = ui()
            if isinstance(lines, list):
                st.session_state["special_interpretations"] = lines
        else:
            st.warning("특수검사 모듈을 찾지 못했습니다.")
    except Exception as e:
        st.error(f"특수검사 탭 오류: {e}")

# -------- 보고서 (lazy) --------
with tabs[5]:
    st.subheader("보고서")
    try:
        rpt = safe_import("app_report_special_patch")
        if rpt and hasattr(rpt, "render_special_report_section"):
            rpt.render_special_report_section()
        else:
            st.info("특수검사 보고서 브릿지가 준비되지 않았습니다.")
    except Exception as e:
        st.error(f"보고서 탭 오류: {e}")

# -------- 케어로그 (lazy) --------
with tabs[6]:
    st.subheader("케어로그")
    try:
        cl = safe_import("care_log_ui")
        done = False
        for fn in ["render","main","show"]:
            f = getattr(cl, fn, None) if cl else None
            if callable(f):
                call_compat(f, st=st)
                done = True
                break
        if not done:
            st.info("케어로그 모듈이 준비되지 않았습니다.")
    except Exception as e:
        st.error(f"케어로그 탭 오류: {e}")
