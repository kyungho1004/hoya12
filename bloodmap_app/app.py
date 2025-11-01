# app.py — Classic App (wired to local modules; dx-selector built-in)
import sys, pathlib, importlib, inspect
import streamlit as st
st.set_page_config(page_title="🩸 피수치 해석기 — 클래식", layout="wide")

APP_URL = "https://bloodmap.streamlit.app/"
MADE_BY = "Hoya/GPT"
APP_DIR = pathlib.Path(__file__).parent.resolve()
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

def call_compat(fn, **kwargs):
    try:
        sig = inspect.signature(fn)
        accepted = {k: v for k, v in kwargs.items() if k in sig.parameters}
        return fn(**accepted)
    except Exception:
        return fn()

def safe_import(name):
    try:
        return importlib.import_module(name)
    except Exception as e:
        st.caption(f"[임포트 생략] {name}: {e}")
        return None

# ---- branding ----
try:
    import branding
    if hasattr(branding, "render_deploy_banner"):
        call_compat(branding.render_deploy_banner, app_url=APP_URL, made_by=MADE_BY, st=st)
except Exception as _e:
    st.caption(f"branding skipped: {str(_e)}")

# ---- special tests injector ----
try:
    import app_special_lock_inject as _sp_lock
    special_tests_ui = _sp_lock.special_tests_ui
except Exception:
    import importlib.util
    def _force_load_safe_special_tests():
        candidate = APP_DIR / "special_tests.py"
        if not candidate.exists():
            st.warning("special_tests.py 안전판이 없습니다.")
            return None
        spec = importlib.util.spec_from_file_location("special_tests", str(candidate))
        mod = importlib.util.module_from_spec(spec)
        sys.modules["special_tests"] = mod
        spec.loader.exec_module(mod)
        return mod
    _stmod = _force_load_safe_special_tests()
    def special_tests_ui():
        if not _stmod or not hasattr(_stmod, "special_tests_ui"):
            st.session_state["special_interpretations"] = ["특수검사 모듈을 찾지 못했습니다."]
            return st.session_state["special_interpretations"]
        lines = _stmod.special_tests_ui()
        st.session_state["special_interpretations"] = lines if lines else []
        return st.session_state["special_interpretations"]

tabs = st.tabs(["홈", "소아", "암 선택", "항암제", "특수검사", "보고서", "케어로그"])

# 홈
with tabs[0]:
    st.title("🩸 BloodMap — Classic")
    st.subheader("홈")
    st.write("이곳은 클래식 홈 화면입니다.")
    _alerts = safe_import("alerts")
    if _alerts:
        try:
            call_compat(getattr(_alerts, "render_recent_risk_banner", _alerts.render_risk_banner), st=st)
        except Exception as e:
            st.caption(f"alerts skipped: {e}")

# 소아
with tabs[1]:
    st.subheader("소아")
    _peds = safe_import("pages_peds") or safe_import("peds_symptoms_ui") or safe_import("peds_guide")
    ok=False
    for cand in ["render_peds_page", "render_peds_tab_phase1", "render", "main", "show"]:
        fn = getattr(_peds, cand, None) if _peds else None
        if callable(fn):
            try:
                call_compat(fn, st=st)
                ok=True
                break
            except Exception as e:
                st.error(f"소아 모듈 오류: {_peds.__name__}.{cand}: {e}")
                ok=True
                break
    if not ok:
        st.info("소아 전용 모듈이 준비되지 않았습니다.")

# 암 선택 — onco_map 기반 내장 셀렉터
with tabs[2]:
    st.subheader("암 선택")
    import json
    _onco = safe_import("onco_map")
    selected_group = st.session_state.get("dx_group", "혈액암")
    selected_dx = st.session_state.get("dx_code", "AML")
    if _onco and hasattr(_onco, "build_onco_map"):
        omap = _onco.build_onco_map()
        groups = list(omap.keys())
        selected_group = st.selectbox("진단 그룹", groups, index=max(groups.index(selected_group) if selected_group in groups else 0,0), key="dx_group")
        dxs = sorted(list(omap.get(selected_group, {}).keys()))
        if dxs:
            try:
                idx = dxs.index(selected_dx) if selected_dx in dxs else 0
            except Exception:
                idx = 0
            selected_dx = st.selectbox("진단명", dxs, index=idx, key="dx_code")
        st.success(f"선택: {selected_group} / {selected_dx}")
        # 추천 약물 프리뷰
        if hasattr(_onco, "auto_recs_by_dx"):
            rec = _onco.auto_recs_by_dx(selected_group, selected_dx)
            st.write("자동 추천(요약):", rec)
    else:
        st.info("onco_map 모듈을 찾지 못했습니다.")

# 항암제 — onco_map / drug_db 연결
with tabs[3]:
    st.subheader("항암제")
    _onco = safe_import("onco_map") or safe_import("drug_db")
    ok=False
    for cand in ["render_chemo_panel","render_onco_drugs","render","main","show"]:
        fn = getattr(_onco, cand, None) if _onco else None
        if callable(fn):
            try:
                call_compat(fn, st=st)
                ok=True
                break
            except Exception as e:
                st.error(f"항암제 모듈 오류: {_onco.__name__}.{cand}: {e}")
                ok=True
                break
    if not ok:
        st.info("항암제 패널이 준비되지 않았습니다.")

# 특수검사
with tabs[4]:
    st.subheader("특수검사")
    special_tests_ui()
    st.info("입력 후 '보고서' 탭에서 결과를 확인하세요.")

# 보고서
with tabs[5]:
    st.subheader("보고서")
    try:
        from app_report_special_patch import render_special_report_section
        render_special_report_section()
    except Exception as e:
        st.error(f"특수검사 보고서 섹션 오류: {e}")
    _pdf = safe_import("pdf_export")
    if _pdf and hasattr(_pdf, "export_md_to_pdf"):
        st.caption("PDF 내보내기 모듈이 로드되었습니다. (버튼 UI는 원래 모듈 UI에 의존)")

# 케어로그
with tabs[6]:
    st.subheader("케어로그")
    _cl = safe_import("care_log_ui")
    ok=False
    for cand in ["render","main","show"]:
        fn = getattr(_cl, cand, None) if _cl else None
        if callable(fn):
            try:
                call_compat(fn, st=st)
                ok=True
                break
            except Exception as e:
                st.error(f"케어로그 모듈 오류: {_cl.__name__}.{cand}: {e}")
                ok=True
                break
    if not ok:
        st.info("케어로그 모듈이 준비되지 않았습니다.")
