"""
app_classic.py — 클래식 레이아웃(홈/응급도 유지 + 예전 페이지 순서)
- 상단: 홈/응급도(요약·체크) 섹션을 항상 먼저 렌더(현재 화면 유지)
- 하단: AE → 특수검사 → 내보내기 → 소아 순서로 고정 렌더
- 패치 방식: 모든 실제 로직은 features/* 모듈을 호출. 기존 기능(케어로그, 해열제 가드, eGFR, 응급배너, 그래프 외부저장 등) 유지.
"""
import streamlit as st
import importlib

# ===== 공통 기본값 시딩 (화면 비어보임 방지) =====
def _seed_defaults():
    ss = st.session_state
    # 라우팅/표시 관련
    ss.setdefault("_lean_mode", True)
    ss.setdefault("_router_tab", "전체")
    ss.setdefault("_show_ae", True)
    ss.setdefault("_show_special", True)
    ss.setdefault("_show_exports", True)
    ss.setdefault("_show_peds", True)
    # 데이터 관련
    if "picked_keys" not in ss:
        ss["picked_keys"] = []  # 필요시 기본 선택 약물 ex) ["Sunitinib"]
    if "DRUG_DB" not in ss:
        try:
            from drug_db import DRUG_DB as _DB
            ss["DRUG_DB"] = _DB
        except Exception:
            ss["DRUG_DB"] = {}

# ===== 홈/응급도 최상단 고정 렌더 =====
def _render_home_emergency(st):
    """
    현재 프로젝트별 함수명이 다를 수 있으니 다단계 폴백으로 호출.
    (아무 것도 없으면 조용히 패스하여 기존 위치 렌더에 맡김)
    """
    # 1) 모듈 우선
    for mod, fn in [
        ("features.home", "render_home"),                         # 신규 홈
        ("features.emergency", "render_emergency_panel"),         # 응급도 패널
        ("features.triage", "render_urgency"),                    # triage UI
        ("features.overview", "render_dashboard"),                # 개요/요약
    ]:
        try:
            m = __import__(mod, fromlist=["_"])
            if hasattr(m, fn):
                getattr(m, fn)(st)
                return
        except Exception:
            pass

    # 2) 레거시 진입(있을 때만)
    try:
        _app = importlib.import_module("app")
        if hasattr(_app, "render_home"):
            getattr(_app, "render_home")(st)
            return
    except Exception:
        pass

    # 3) 아무 것도 못 찾으면 조용히 스킵(홈이 다른 데서 이미 렌더될 수 있음)
    return

def main():
    st.set_page_config(page_title="클래식 레이아웃", layout="wide")
    _seed_defaults()
    ss = st.session_state
    picked_keys = ss.get("picked_keys", [])
    DRUG_DB = ss.get("DRUG_DB", {})

    # 사이드바(경량 모드/환경설정 유지)
    try:
        from features.app_shell import render_sidebar as _shell
        _shell(st)
    except Exception:
        pass
    try:
        from features.app_deprecator import apply_lean_mode as _lean
        _lean(st)
    except Exception:
        pass

    # === 0) 홈/응급도 — 캡처된 화면 그대로 유지 ===
    _render_home_emergency(st)

    # === 1) AE(항암 부작용) + 용어칩 ===
    try:
        from features.pages.ae import render as _ae
        _ae(st, picked_keys, DRUG_DB)
    except Exception:
        pass

    # === 2) 특수검사(키 충돌 가드 포함 래퍼) ===
    try:
        from features.pages.special import render as _special
        _special(st)
    except Exception:
        pass

    # === 3) 내보내기(Export/보고서 파이프라인/케어로그 내보내기) ===
    try:
        from features.pages.exports import render as _exports
        _exports(st, picked_keys)
    except Exception:
        pass

    # === 4) 소아(점프바/해열제/ORS/호흡기/증상/ER 원페이지/소아 내보내기) ===
    try:
        from features.pages.peds import render as _peds
        _peds(st)
    except Exception:
        pass

    # (선택) 진단 패널 — 개발 모드에서만 참고
    try:
        try:
            from features.dev.diag_panel import render_diag_panel as _diag
        except Exception:
            from features_dev.diag_panel import render_diag_panel as _diag  # ALT 폴백
        _diag(st)
    except Exception:
        pass

if __name__ == "__main__":
    main()
