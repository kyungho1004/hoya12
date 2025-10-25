"""
app_classic_strict_dxlike.py — '옛날 인터페이스 동일' 버전
순서: 홈/응급도 → 소아 → 암 선택(그룹/진단명 selectbox) → 항암제 → 특수검사 → 내보내기
- '암 선택' UI를 예전과 동일하게: "암 그룹" selectbox → "의심/진단명" selectbox
- 불필요한 새로운 위젯/칩 없음
"""
import streamlit as st
import importlib

def _seed_defaults():
    ss = st.session_state
    ss.setdefault("_lean_mode", True)
    ss.setdefault("_router_tab", "전체")
    ss.setdefault("_show_ae", True)
    ss.setdefault("_show_special", True)
    ss.setdefault("_show_exports", True)
    ss.setdefault("_show_peds", True)
    if "picked_keys" not in ss:
        ss["picked_keys"] = []
    if "DRUG_DB" not in ss:
        try:
            from drug_db import DRUG_DB as _DB
            ss["DRUG_DB"] = _DB
        except Exception:
            ss["DRUG_DB"] = {}

def _render_home_emergency(st):
    for mod, fn in [
        ("features.home", "render_home"),
        ("features.emergency", "render_emergency_panel"),
        ("features.triage", "render_urgency"),
        ("features.overview", "render_dashboard"),
    ]:
        try:
            m = __import__(mod, fromlist=["_"])
            if hasattr(m, fn):
                getattr(m, fn)(st); return
        except Exception:
            pass
    try:
        _app = importlib.import_module("app")
        if hasattr(_app, "render_home"):
            getattr(_app, "render_home")(st); return
    except Exception:
        pass

# === 옛날식 암 선택: "암 그룹" → "의심/진단명" ===
def _dx_selector_legacy(st):
    ss = st.session_state
    st.subheader("암 선택")
    try:
        from onco_map import ONCO, DX_KO, _norm as _dx_norm  # type: ignore
    except Exception:
        ONCO, DX_KO = {}, {}
        def _dx_norm(s): return s

    groups = sorted(ONCO.keys()) if isinstance(ONCO, dict) and ONCO else ["혈액암", "고형암"]
    group = st.selectbox("암 그룹", options=groups, index=0, key="_dx_group_sel")

    diseases = sorted(ONCO.get(group, {}).keys()) if isinstance(ONCO, dict) and ONCO else ["ALL","AML","Lymphoma","Breast","Colon","Lung"]
    disease = st.selectbox("의심/진단명", options=diseases, index=0, key="_dx_name_sel")

    pick = _dx_norm(disease)
    if pick:
        ss["picked_keys"] = [pick]  # 단일 선택 유지(옛날 UX와 동일)
    return pick

def main():
    st.set_page_config(page_title="클래식(완전 동일 UI)", layout="wide")
    _seed_defaults()
    ss = st.session_state
    picked_keys = ss.get("picked_keys", [])
    DRUG_DB = ss.get("DRUG_DB", {})

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

    # 0) 홈/응급도
    _render_home_emergency(st)

    # 1) 소아
    try:
        from features.pages.peds import render as _peds
        _peds(st)
    except Exception:
        pass

    # 2) 암 선택 (예전 UI)
    _dx_selector_legacy(st)
    picked_keys = ss.get("picked_keys", [])

    # 3) 항암제
    try:
        from features.pages.ae import render as _ae
        _ae(st, picked_keys, DRUG_DB)
    except Exception:
        pass

    # 4) 특수검사
    try:
        from features.pages.special import render as _special
        _special(st)
    except Exception:
        pass

    # 5) 내보내기
    try:
        from features.pages.exports import render as _exports
        _exports(st, picked_keys)
    except Exception:
        pass

    # (선택) 진단 패널
    try:
        try:
            from features.dev.diag_panel import render_diag_panel as _diag
        except Exception:
            from features_dev.diag_panel import render_diag_panel as _diag
        _diag(st)
    except Exception:
        pass

if __name__ == "__main__":
    main()
