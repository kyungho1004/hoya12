
# -*- coding: utf-8 -*-
"""
app.py — 메인(암/혈액) 섹션 명시 렌더 + 소아 안내 분리 최종본
"""

import streamlit as st
import os as _os, sys as _sys, importlib.util as _ilu

st.set_page_config(page_title="Bloodmap", layout="wide")

# ====== 사이드바 라우팅 ======
if "nav_page" not in st.session_state:
    st.session_state["nav_page"] = "메인"
with st.sidebar:
    nav_page = st.radio("페이지", ["메인", "소아 안내"], index=0, key="nav_page")

# ====== 안전 로더 ======
def _load_local(_modname: str, _filename: str):
    try:
        _here = _os.path.dirname(__file__) if "__file__" in globals() else _os.getcwd()
        _path = _os.path.join(_here, _filename)
        if _os.path.exists(_path):
            _spec = _ilu.spec_from_file_location(_modname, _path)
            _mod = _ilu.module_from_spec(_spec)
            assert _spec and _spec.loader
            _spec.loader.exec_module(_mod)  # type: ignore
            _sys.modules[_modname] = _mod
            return _mod
    except Exception as _e:
        st.warning(f"모듈 로드 실패({_modname}): {_e}")
    return None


def _call_maybe_with_st(fn):
    """Call fn(); if it needs one positional arg, pass streamlit as st."""
    try:
        return fn()
    except TypeError as e:
        import inspect, streamlit as st
        try:
            sig = inspect.signature(fn)
            params = [p for p in sig.parameters.values() if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD) and p.default is p.empty]
            if len(params) == 1:
                return fn(st)
        except Exception:
            pass
        raise


def _safe_import(name, filename):
    try:
        return __import__(name)
    except Exception:
        return _load_local(name, filename)

# ====== 메인(암/혈액) 섹션 ======
def _render_main_home():
    # 배너
    branding = _safe_import("branding", "branding.py")
    if branding and hasattr(branding, "render_deploy_banner"):
        try:
            branding.render_deploy_banner(app_url="", made_by="")  # 안전 기본값
        except TypeError:
            # 다른 시그니처 대응
            try:
                branding.render_deploy_banner()
            except Exception as _e:
                st.caption(f"배너 표시 생략: {_e}")

    # 헤더/퀵툴
    core_utils = _safe_import("core_utils", "core_utils.py")
    if core_utils:
        if hasattr(core_utils, "render_page_header"):
            try:
                core_utils.render_page_header("🩺 메인 — 암/혈액 도구")
            except Exception:
                st.header("🩺 메인 — 암/혈액 도구")
        else:
            st.header("🩺 메인 — 암/혈액 도구")
        if hasattr(core_utils, "render_quick_tools"):
            try:
                with st.expander("⚡ 빠른 도구", expanded=False):
                    core_utils.render_quick_tools()
            except Exception as _e:
                st.warning(f"빠른 도구 로딩 실패: {_e}")
    else:
        st.header("🩺 메인 — 암/혈액 도구")

    # 섹션 1: 검사결과 해석
    ui_results = _safe_import("ui_results", "ui_results.py")
    if ui_results and hasattr(ui_results, "results_only_after_analyze"):
        with st.expander("🔬 검사결과 해석", expanded=True):
            try:
                _call_maybe_with_st(ui_results.results_only_after_analyze)
            except Exception as _e:
                st.warning(f"검사결과 섹션 오류: {_e}")

    # 섹션 2: 암 경로 맵
    onco_map = _safe_import("onco_map", "onco_map.py")
    if onco_map and hasattr(onco_map, "render_onco_map"):
        with st.expander("🎗️ 암 경로 맵", expanded=False):
            try:
                onco_map.render_onco_map()
            except Exception as _e:
                st.warning(f"암 경로 맵 오류: {_e}")

    # 섹션 3: 응급도 가중치(UI)
    triage_ui = _safe_import("triage_weights_ui", "triage_weights_ui.py")
    if triage_ui and hasattr(triage_ui, "render_triage_weights_ui"):
        with st.expander("⚖️ 응급도 가중치 (간단/자세히)", expanded=False):
            try:
                triage_ui.render_triage_weights_ui()
            except Exception as _e:
                st.warning(f"응급도 가중치 UI 오류: {_e}")

    # 섹션 4: 식이 안내
    lab_diet = _safe_import("lab_diet", "lab_diet.py")
    if lab_diet and hasattr(lab_diet, "render_lab_diet"):
        with st.expander("🥗 검사 전후 식이 안내", expanded=False):
            try:
                lab_diet.render_lab_diet()
            except Exception as _e:
                st.warning(f"식이 안내 오류: {_e}")

    # 섹션 5: 특수검사
    special_tests = _safe_import("special_tests", "special_tests.py")
    if special_tests and hasattr(special_tests, "render_special_tests"):
        with st.expander("🧪 특수검사", expanded=False):
            try:
                special_tests.render_special_tests()
            except Exception as _e:
                st.warning(f"특수검사 오류: {_e}")

    # 섹션 6: 항암제 DB
    drug_db = _safe_import("drug_db", "drug_db.py")
    if drug_db and hasattr(drug_db, "render_drug_db"):
        with st.expander("💊 항암제 DB/상호작용", expanded=False):
            try:
                drug_db.render_drug_db()
            except Exception as _e:
                st.warning(f"항암제 DB 오류: {_e}")

# ====== 소아 보호자 안내(전용 페이지) ======
# pediatric modules
peds_cond = _safe_import("peds_conditions_ui", "peds_conditions_ui.py")
peds_cg   = _safe_import("peds_caregiver_page", "peds_caregiver_page.py")
peds_sym  = _safe_import("peds_symptoms_ui", "peds_symptoms_ui.py")

def _render_pediatric_guides_section():
    st.header("👶 소아 — 보호자 안내")

    # 세션 시드 기반 프리픽스(충돌 방지)
    if "_peds_ns_seed" not in st.session_state:
        import uuid
        st.session_state["_peds_ns_seed"] = uuid.uuid4().hex[:6]
    _seed = st.session_state["_peds_ns_seed"]

    _guide_prefix = f"peds_guide_{_seed}"
    _sym_prefix   = f"peds_sym_{_seed}"
    _cg_prefix    = f"peds_cg_{_seed}"

    # 섹션 초기화
    col_reset, _ = st.columns([1,3])
    with col_reset:
        if st.button("🔄 섹션 초기화", key=f"peds_reset_{_seed}"):
            keys_to_del = [k for k in list(st.session_state.keys()) if k.startswith("peds_")]
            for k in keys_to_del:
                try:
                    del st.session_state[k]
                except Exception:
                    pass
            import uuid
            st.session_state["_peds_ns_seed"] = uuid.uuid4().hex[:6]
            st.experimental_rerun()

    tab_names = ["병명별 한눈에", "보호자 모드(묶음)"]
    has_sym = (peds_sym is not None) and hasattr(peds_sym, "render_peds_symptoms_page")
    if has_sym:
        tab_names.insert(1, "소아 증상")

    tabs = st.tabs(tab_names)

    idx = 0
    with tabs[idx]:
        if peds_cond and hasattr(peds_cond, "render_peds_conditions_page"):
            try:
                peds_cond.render_peds_conditions_page(key_prefix=_guide_prefix)
            except Exception as _e:
                st.warning(f"병명별 가이드 로딩 실패: {_e}")
        else:
            st.error("peds_conditions_ui 모듈이 필요합니다.")
    idx += 1

    if has_sym:
        with tabs[idx]:
            try:
                peds_sym.render_peds_symptoms_page(key_prefix=_sym_prefix)  # type: ignore
            except Exception as _e:
                st.warning(f"소아 증상 로딩 실패: {_e}")
        idx += 1

    with tabs[idx]:
        if peds_cg and hasattr(peds_cg, "render_caregiver_mode"):
            try:
                peds_cg.render_caregiver_mode(key_prefix=_cg_prefix)
            except Exception as _e:
                st.warning(f"보호자 모드 로딩 실패: {_e}")
        else:
            st.error("peds_caregiver_page 모듈이 필요합니다.")

# ====== 라우팅 ======
if nav_page == "메인":
    _render_main_home()
elif nav_page == "소아 안내":
    _render_pediatric_guides_section()
else:
    _render_main_home()
