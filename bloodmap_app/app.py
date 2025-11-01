# app.py — Classic App (Deep-compat wiring, Patch-only, Safe Guards)
import sys, pathlib, importlib, inspect
import streamlit as st
st.set_page_config(page_title="🩸 피수치 해석기 — 클래식", layout="wide")

APP_URL = "https://bloodmap.streamlit.app/"
MADE_BY = "Hoya/GPT"

# === Ensure project dir on sys.path ===
APP_DIR = pathlib.Path(__file__).parent.resolve()
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

# === Generic compat-caller ===
def call_compat(fn, **kwargs):
    try:
        sig = inspect.signature(fn)
        accepted = {k: v for k, v in kwargs.items() if k in sig.parameters}
        return fn(**accepted)
    except Exception:
        # fall back to positional-less call
        return fn()

def safe_import(name):
    try:
        return importlib.import_module(name)
    except Exception as e:
        st.caption(f"[임포트 생략] {name}: {e}")
        return None

def try_funcs(mod, cand_names, **kwargs):
    if not mod:
        return False, None
    for n in cand_names:
        fn = getattr(mod, n, None)
        if callable(fn):
            try:
                call_compat(fn, **kwargs)
                return True, n
            except Exception as e:
                st.error(f"{mod.__name__}.{n} 실행 오류: {e}")
                return True, n
    return False, None

connected = {}

# === Branding banner (compat) ===
try:
    import branding
    if hasattr(branding, "render_deploy_banner"):
        call_compat(branding.render_deploy_banner, app_url=APP_URL, made_by=MADE_BY, st=st)
        connected["branding"] = "render_deploy_banner"
except Exception as _e:
    st.caption(f"branding skipped: {str(_e)}")

# === Special Tests force loader (prefer external injector) ===
try:
    import app_special_lock_inject as _sp_lock
    special_tests_ui = _sp_lock.special_tests_ui
    connected["special_tests"] = "injector"
except Exception:
    import importlib.util
    def _force_load_safe_special_tests():
        candidate = APP_DIR / "special_tests.py"
        if not candidate.exists():
            st.warning("special_tests.py 안전판이 없습니다.")
            return None
        spec = importlib.util.spec_from_file_location("special_tests", str(candidate))
        if not spec or not spec.loader:
            st.error("special_tests 안전판 로딩 실패(spec)")
            return None
        mod = importlib.util.module_from_spec(spec)
        sys.modules["special_tests"] = mod
        spec.loader.exec_module(mod)
        return mod
    try:
        _stmod = _force_load_safe_special_tests()
        st.caption(f"special_tests loaded from (FORCED): {getattr(_stmod,'__file__',None)}")
        def special_tests_ui():
            if not _stmod or not hasattr(_stmod, "special_tests_ui"):
                st.session_state["special_interpretations"] = ["특수검사 모듈을 찾지 못했습니다."]
                return st.session_state["special_interpretations"]
            try:
                lines = _stmod.special_tests_ui()
                if isinstance(lines, list) and lines:
                    st.session_state["special_interpretations"] = [str(x) for x in lines if x is not None]
                elif isinstance(lines, str) and lines.strip():
                    st.session_state["special_interpretations"] = [lines.strip()]
                else:
                    st.session_state["special_interpretations"] = ["특수검사 항목을 펼치지 않아 요약이 없습니다. 필요 시 토글을 열어 값을 입력하세요."]
                return st.session_state["special_interpretations"]
            except Exception as e:
                st.error(f"특수검사 UI 실행 오류(안전모드): {e}")
                st.session_state["special_interpretations"] = ["특수검사 UI 실행 중 오류가 발생하여 안전모드로 전환되었습니다."]
                return st.session_state["special_interpretations"]
        connected["special_tests"] = "inline_safe"
    except Exception as _e2:
        st.caption(f"special_tests force-load failed: {_e2}")

# === Tabs (original order) ===
tabs = st.tabs(["홈", "소아", "암 선택", "항암제", "특수검사", "보고서", "케어로그"])

# 홈
with tabs[0]:
    st.title("🩸 BloodMap — Classic")
    st.subheader("홈")
    st.write("이곳은 클래식 홈 화면입니다.")
    _alerts = safe_import("alerts")
    ok, used = try_funcs(_alerts, ["render_recent_risk_banner", "render_risk_banner"], st=st)
    if ok: connected["alerts"] = used

# 소아
with tabs[1]:
    st.subheader("소아")
    _peds = (
        safe_import("pages_peds") or
        safe_import("peds_symptoms_ui") or
        safe_import("peds_guide") or
        safe_import("peds_conditions_ui")
    )
    ok, used = try_funcs(_peds, [
        "render","render_page","render_tabs",
        "peds_main","main","show"
    ], st=st)
    if ok:
        connected["peds"] = f"{_peds.__name__}.{used}"
    else:
        st.info("소아 전용 모듈이 준비되지 않았습니다.")

# 암 선택
with tabs[2]:
    st.subheader("암 선택")
    _router = safe_import("router") or safe_import("route_patch_safest") or safe_import("app_router")
    ok, used = try_funcs(_router, ["render_dx_selector","render_dx_panel","render","main","show"], st=st)
    if ok: connected["router"] = f"{_router.__name__}.{used}"
    else: st.info("암/진단 선택 모듈이 준비되지 않았습니다.")

# 항암제
with tabs[3]:
    st.subheader("항암제")
    _onco = safe_import("onco_map") or safe_import("drug_db")
    ok, used = try_funcs(_onco, ["render_chemo_panel","render_onco_drugs","render","main","show"], st=st)
    if ok: connected["onco"] = f"{_onco.__name__}.{used}"
    else: st.info("항암제 패널이 준비되지 않았습니다.")

# 특수검사
with tabs[4]:
    st.subheader("특수검사")
    st.info("입력 후 '보고서' 탭에서 결과를 확인하세요.")
    try:
        special_tests_ui()
        connected["special_tests_ui"] = "ok"
    except Exception as e:
        st.error(f"특수검사 실행 오류: {e}")

# 보고서
with tabs[5]:
    st.subheader("보고서")
    try:
        from app_report_special_patch import render_special_report_section
        render_special_report_section()
        connected["report"] = "special_section"
    except Exception as e:
        st.error(f"특수검사 보고서 섹션 오류: {e}")
    _pdf = safe_import("pdf_export")
    ok, used = try_funcs(_pdf, ["render_export_panel","render","show"], st=st, app_url=APP_URL, made_by=MADE_BY)
    if ok: connected["pdf_export"] = f"{_pdf.__name__}.{used}"

# 케어로그
with tabs[6]:
    st.subheader("케어로그")
    _cl = safe_import("care_log_ui")
    ok, used = try_funcs(_cl, ["render","main","show"], st=st)
    if ok: connected["care_log"] = f"{_cl.__name__}.{used}"
    else: st.info("케어로그 모듈이 준비되지 않았습니다.")

# 작은 디버그
with st.expander("🔎 연결 상태(디버그)"):
    st.json(connected)
