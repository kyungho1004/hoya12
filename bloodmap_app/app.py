# app.py — Original-style Hardened App (patch-only, safe imports)
# - Keeps classic single-file feel while delegating to modules if present
# - Force-loads safe special_tests
# - Always renders Special Tests report section
# - Wraps optional modules with try/except so missing files won't crash

import streamlit as st
st.set_page_config(page_title="BloodMap Classic", layout="wide")

# ====== Deploy banner (optional) ======
try:
    import branding
    if hasattr(branding, "render_deploy_banner"):
        branding.render_deploy_banner()
except Exception as _e:
    st.caption(f"branding skipped: {_e}")

# ====== Force-load safe special_tests and alias ======
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
except Exception as _e:
    st.caption(f"special_tests force-load failed: {_e}")
    _stmod = None

def special_tests_ui_safe():
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

special_tests_ui = special_tests_ui_safe

# ====== Optional modules (safe import wrappers) ======
def _load_module(name):
    try:
        return importlib.import_module(name)
    except Exception as e:
        st.caption(f"{name} 불러오기 생략: {e}")
        return None

ui_results = _load_module("ui_results")
care_log_ui = _load_module("care_log_ui")
pdf_export = _load_module("pdf_export")
graph_io = _load_module("graph_io")
alerts = _load_module("alerts")

# ====== UI Structure ======
st.title("🩸 BloodMap — Classic")

tabs = st.tabs(["홈", "피수치 해석", "특수검사", "보고서", "케어로그"])

with tabs[0]:
    st.subheader("홈")
    st.write("이곳은 클래식 홈 화면입니다.")

with tabs[1]:
    st.subheader("피수치 해석")
    if ui_results and hasattr(ui_results, "render_lab_results"):
        try:
            ui_results.render_lab_results()
        except Exception as e:
            st.error(f"피수치 해석 오류: {e}")
    else:
        st.info("피수치 해석 모듈이 준비되지 않았습니다.")

with tabs[2]:
    st.subheader("특수검사")
    st.info("입력 후 '보고서' 탭에서 결과를 확인하세요.")
    special_tests_ui()

with tabs[3]:
    st.subheader("보고서")
    # 특수검사 섹션
    try:
        from app_report_special_patch import render_special_report_section
        render_special_report_section()
    except Exception as e:
        st.error(f"특수검사 보고서 섹션 오류: {e}")
    # (선택) ER PDF 등 추가 섹션
    if pdf_export and hasattr(pdf_export, "render_export_panel"):
        try:
            pdf_export.render_export_panel()
        except Exception as e:
            st.error(f"내보내기 오류: {e}")

with tabs[4]:
    st.subheader("케어로그")
    if care_log_ui and hasattr(care_log_ui, "render"):
        try:
            care_log_ui.render()
        except Exception as e:
            st.error(f"케어로그 오류: {e}")
    else:
        st.info("케어로그 모듈이 준비되지 않았습니다.")

# ====== Safety banners (optional) ======
if alerts and hasattr(alerts, "render_recent_risk_banner"):
    try:
        alerts.render_recent_risk_banner()
    except Exception as e:
        st.caption(f"경고 배너 생략: {e}")
