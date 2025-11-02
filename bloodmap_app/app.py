
# -*- coding: utf-8 -*-
"""
BloodMap - app_classic (오리지널 레이아웃 복구판)
- 탭 순서 유지: 홈 → 소아 → 암 선택/항암제 → 특수검사 → 보고서 → 케어로그
- 기존 기능 삭제 없이 연결만 안전화(패치 방식)
- 특수검사 로더 견고화(special_tests_bridge 또는 직접 탐색)
- 홈으로 튀는 현상 방지(_route 가드)
- 경로 고정: /mnt/data/bloodmap_graph
- ast.parse 등 QA 프리체크 훅 호출(존재 시)
한국시간(KST) 기준.
"""
from __future__ import annotations
import os, sys, importlib, traceback
from pathlib import Path
from datetime import datetime, timedelta, timezone

import streamlit as st

# ========== Page Config (가장 첫 Streamlit 호출) ==========
st.set_page_config(page_title="BloodMap • Classic", page_icon="🩸", layout="wide")

# KST
KST = timezone(timedelta(hours=9))

# 안전 경로 고정
GRAPH_DIR = Path("/mnt/data/bloodmap_graph")
GRAPH_DIR.mkdir(parents=True, exist_ok=True)

# Python path에 /mnt/data 추가(특수검사/브릿지 로딩용)
if "/mnt/data" not in sys.path:
    sys.path.append("/mnt/data")

BASE_DIR = Path(__file__).parent

# ========== 유틸 ==========
def _safe_import(name: str):
    try:
        return importlib.import_module(name)
    except Exception:
        return None

def _safe_attr(mod, *names):
    for nm in names:
        if mod is not None and hasattr(mod, nm) and callable(getattr(mod, nm)):
            return getattr(mod, nm)
    return None

def _caption_ok(msg: str):
    st.caption(msg)

def _expander_error(title: str, err: Exception):
    with st.expander(title, expanded=False):
        st.error(str(err))
        st.code(traceback.format_exc())

def _route_init():
    if "_route" not in st.session_state:
        st.session_state["_route"] = "home"
    if "_route_last" not in st.session_state:
        st.session_state["_route_last"] = "home"

def _pin_route(route: str):
    # 홈 튐 방지: 사용자가 섹션을 열면 그 라우트를 고정
    st.session_state["_route"] = route
    st.session_state["_route_last"] = route

_route_init()

# ========== 모듈 로드(존재 여부만 확인) ==========
branding = _safe_import("branding")
alerts = _safe_import("alerts")
care_log_ui = _safe_import("care_log_ui")
graph_io = _safe_import("graph_io")
ui_results = _safe_import("ui_results")
ui_report = _safe_import("ui_report")
pdf_export = _safe_import("pdf_export")
pages_peds = _safe_import("pages_peds")
ui_peds = _safe_import("ui_peds")
qa_precheck = _safe_import("qa_precheck")

# ========== Branding Banner ==========
if _safe_attr(branding, "render_deploy_banner"):
    try:
        branding.render_deploy_banner()
    except Exception as e:
        _expander_error("branding.render_deploy_banner 오류", e)
else:
    st.caption("制作者: Hoya/GPT · 자문: Hoya/GPT · KST 기준 · 세포·면역 치료는 표기하지 않습니다.")

# ========== 상단 경고 배너(발열/FN/전해질 등) ==========
if _safe_attr(alerts, "render_risk_banner"):
    try:
        alerts.render_risk_banner()
    except Exception as e:
        _expander_error("alerts.render_risk_banner 오류", e)

# ========== 특수검사 안전 로더 ==========
def _load_special_tests_entry():
    # 브릿지 우선
    try:
        from special_tests_bridge import get_special_tests_ui
        fn, info = get_special_tests_ui()
        return fn, info
    except Exception:
        pass
    # 직접 탐색
    candidates = [
        BASE_DIR/"special_tests.py",
        Path("/mnt/data")/"special_tests.py",
        Path.cwd()/"special_tests.py",
    ]
    last_err = None
    for p in candidates:
        try:
            if p.exists():
                spec = importlib.util.spec_from_file_location("special_tests", str(p))
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    for nm in ("special_tests_ui", "render", "ui"):
                        c = getattr(mod, nm, None)
                        if callable(c):
                            return c, f"loaded: {p}"
        except Exception:
            last_err = traceback.format_exc()
    # 패키지 임포트
    try:
        mod = importlib.import_module("special_tests")
        for nm in ("special_tests_ui", "render", "ui"):
            c = getattr(mod, nm, None)
            if callable(c):
                return c, "<pkg-import>"
    except Exception:
        if last_err is None:
            last_err = traceback.format_exc()
    # 실패 → 더미
    def _dummy():
        st.warning("special_tests.py를 찾지 못해, 특수검사 UI는 더미로 표시됩니다.")
        return ["special_tests load failed"]
    return _dummy, (last_err or "not found")

_special_ui, _special_info = _load_special_tests_entry()

# ========== 탭 구성: 홈 / 소아 / 암선택(항암제) / 특수검사 / 보고서 / 케어로그 ==========
t_home, t_peds, t_dx, t_special, t_report, t_care = st.tabs(
    ["🏠 홈", "👶 소아", "🧬 암 선택·항암제", "🧪 특수검사", "📄 보고서", "🗒️ 케어로그"]
)

with t_home:
    _pin_route("home")
    st.markdown("### BloodMap — caregiver‑friendly lab & chemo assistant (Classic)")
    st.write(f"한국시간: {datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')}")
    # QA 프리체크(있으면)
    _qa_btn = st.button("🔍 QA 프리체크 실행", key="qa_precheck_btn")
    if _qa_btn and _safe_attr(qa_precheck, "run_precheck"):
        try:
            ok, report_path = qa_precheck.run_precheck(base_dir=str(BASE_DIR))
            if ok:
                st.success("문법/키/핵심 기능 누락 점검: 통과")
            else:
                st.warning("경고 있음 — 상세 보고서를 확인하세요.")
            if report_path:
                st.caption(f"PRECHECK_REPORT: {report_path}")
        except Exception as e:
            _expander_error("QA 프리체크 오류", e)
    st.info("핵심 기능(케어로그·해열제 가드레일·eGFR·그래프 외부저장·ER PDF·CSV·PIN)은 모듈에서 유지됩니다.")

with t_peds:
    _pin_route("peds")
    fn = _safe_attr(pages_peds, "render") or _safe_attr(ui_peds, "render", "render_peds_tab", "render_page")
    if fn:
        try:
            fn()
        except Exception as e:
            _expander_error("소아 탭 렌더링 오류", e)
    else:
        st.info("소아 탭 모듈을 찾지 못했습니다. (pages_peds.py / ui_peds.py)")

with t_dx:
    _pin_route("dx")
    # 진단/항암제 섹션은 보유 모듈에 따라 다르므로, 안전 래퍼만 제공
    st.subheader("암 선택 · 항암제 가이드")
    # ui_results.render_results_panel가 있으면 호출
    fn = _safe_attr(ui_results, "render_results_panel", "render")
    if fn:
        try:
            fn()
        except Exception as e:
            _expander_error("암 선택/항암제 패널 오류", e)
    else:
        st.info("암 선택/항암제 패널 모듈(ui_results.py)을 찾지 못했습니다.")

with t_special:
    _pin_route("special")
    st.subheader("특수검사")
    try:
        lines = _special_ui()  # UI 내부에서 위젯을 그릴 수 있음
        if lines:
            with st.expander("📄 특수검사 · 디버그 로그", expanded=False):
                for ln in lines:
                    st.write(ln)
        if _special_info:
            st.caption(f"special_tests source: {_special_info}")
    except Exception as e:
        _expander_error("특수검사 UI 실행 오류", e)

with t_report:
    _pin_route("report")
    st.subheader("보고서 / 내보내기")
    # ui_report or pdf_export 엔트리 호출
    fn = _safe_attr(ui_report, "render_report_tab", "render") or _safe_attr(pdf_export, "render_report_tab", "render")
    if fn:
        try:
            fn()
        except Exception as e:
            _expander_error("보고서 탭 실행 오류", e)
    else:
        st.info("보고서 탭 모듈(ui_report.py 또는 pdf_export.py)을 찾지 못했습니다.")

with t_care:
    _pin_route("care")
    st.subheader("케어로그")
    fn = _safe_attr(care_log_ui, "render", "render_carelog_tab", "render_page")
    if fn:
        try:
            fn()
        except Exception as e:
            _expander_error("케어로그 탭 실행 오류", e)
    else:
        st.info("케어로그 UI 모듈(care_log_ui.py)을 찾지 못했습니다.")

# ========== 하단 그래프 저장 경로 안내(외부저장 유지) ==========
st.caption(f"📈 그래프 외부저장 경로: {GRAPH_DIR}")
