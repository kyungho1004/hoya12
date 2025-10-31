# app.py — Classic Ordered App (패치 방식, 안전가드 포함)
import streamlit as st
st.set_page_config(page_title="🩸 피수치 해석기 — 클래식", layout="wide")

# ===== 배너 (선택) =====
try:
    import branding
    if hasattr(branding, "render_deploy_banner"):
        branding.render_deploy_banner()
except Exception as _e:
    st.caption(f"branding skipped: {_e}")

# ===== 특수검사 강제 로더 (모듈 있으면 우선 사용) =====
try:
    import app_special_lock_inject as _sp_lock
    # alias가 이미 제공됨: special_tests_ui = _sp_lock.special_tests_ui
    special_tests_ui = _sp_lock.special_tests_ui
except Exception as _e:
    # 인젝터가 없을 때를 대비한 인라인 안전판
    import importlib.util, sys, pathlib
    def _force_load_safe_special_tests():
        app_dir = pathlib.Path(__file__).parent
        candidate = app_dir / "special_tests.py"
        if not candidate.exists():
            st.warning("special_tests.py 안전판이 없습니다. (app_dir/special_tests.py)")
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
    except Exception as _e2:
        st.caption(f"special_tests force-load failed: {_e2}")
        _stmod = None
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

# ===== 공용 안전 임포트/호출 헬퍼 =====
import importlib

def _load(name):
    try:
        return importlib.import_module(name)
    except Exception as e:
        st.caption(f"{name} 모듈 생략: {e}")
        return None

def _call_first(mod, names, *args, **kwargs):
    if not mod: return False
    for n in names:
        fn = getattr(mod, n, None)
        if callable(fn):
            try:
                fn(*args, **kwargs)
                return True
            except Exception as e:
                st.error(f"{mod.__name__}.{n} 실행 오류: {e}")
                return True  # 시도는 했음
    return False

# ===== 탭 구성 (원래 순서) =====
tabs = st.tabs(["홈", "소아", "암 선택", "항암제", "특수검사", "보고서", "케어로그"])

# ----- 홈 -----
with tabs[0]:
    st.title("🩸 BloodMap — Classic")
    st.subheader("홈")
    st.write("이곳은 클래식 홈 화면입니다.")
    # 위험 배너(있으면)
    _alerts = _load("alerts")
    _call_first(_alerts, ["render_recent_risk_banner", "render_risk_banner"])

# ----- 소아 -----
with tabs[1]:
    st.subheader("소아")
    _peds = _load("pages_peds") or _load("peds_symptoms_ui") or _load("peds_guide")
    rendered = _call_first(_peds, ["render", "main", "render_page", "peds_main", "show"])
    if not rendered:
        st.info("소아 전용 모듈이 준비되지 않았습니다.")

# ----- 암 선택 -----
with tabs[2]:
    st.subheader("암 선택")
    _router = _load("router") or _load("route_patch_safest")
    ok = _call_first(_router, ["render_dx_selector", "render_dx_panel", "render"])
    if not ok:
        st.info("암/진단 선택 모듈이 준비되지 않았습니다.")

# ----- 항암제 -----
with tabs[3]:
    st.subheader("항암제")
    _onco = _load("onco_map") or _load("drug_db")
    ok = _call_first(_onco, ["render_chemo_panel", "render_onco_drugs", "render", "show"])
    if not ok:
        st.info("항암제 패널이 준비되지 않았습니다.")

# ----- 특수검사 -----
with tabs[4]:
    st.subheader("특수검사")
    st.info("입력 후 '보고서' 탭에서 결과를 확인하세요.")
    special_tests_ui()

# ----- 보고서 -----
with tabs[5]:
    st.subheader("보고서")
    try:
        from app_report_special_patch import render_special_report_section
        render_special_report_section()
    except Exception as e:
        st.error(f"특수검사 보고서 섹션 오류: {e}")
    # (선택) ER PDF/CSV/QR 등
    _pdf = _load("pdf_export")
    _call_first(_pdf, ["render_export_panel", "render"])

# ----- 케어로그 -----
with tabs[6]:
    st.subheader("케어로그")
    _cl = _load("care_log_ui")
    if not _call_first(_cl, ["render", "main", "show"]):
        st.info("케어로그 모듈이 준비되지 않았습니다.")
