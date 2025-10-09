
# -*- coding: utf-8 -*-
"""
app.py — 최종본(메인=암 관련 복구, 소아=분리)
- 메인: 기존 암/혈액 관련 섹션을 가능한 한 자동 탐지·렌더
- 소아 보호자 가이드는 사이드바 '소아 안내'에서만 렌더
- 세션 시드 기반 네임스페이스로 탭 간/페이지 간 충돌 방지
"""

import streamlit as st
import os as _os, sys as _sys, importlib.util as _ilu
from typing import List, Tuple

st.set_page_config(page_title="Bloodmap", layout="wide")

# ====== 사이드바 라우팅 ======
if "nav_page" not in st.session_state:
    st.session_state["nav_page"] = "메인"

with st.sidebar:
    nav_page = st.radio("페이지", ["메인", "소아 안내"], index=0, key="nav_page")

# ====== 공통: 안전 로더 ======
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

# ====== 메인(암/혈액) 섹션 자동 렌더 ======
def _render_main_home():
    st.header("🩺 메인")
    st.caption("암/혈액 관련 도구를 자동으로 불러옵니다. 모듈이 없으면 해당 섹션은 건너뜁니다.")

    # (모듈, 후보 함수들, 섹션 제목)
    sections: List[Tuple[str, List[str], str]] = [
        ("ui_results", ["render_main", "render_page", "render_results"], "🔬 검사결과 해석"),
        ("onco_map", ["render_main", "render_onco_map", "render_page"], "🎗️ 암 경로 맵"),
        ("lab_diet", ["render_main", "render_section", "render_page"], "🥗 검사 전후 식이"),
        ("special_tests", ["render_main", "render_section", "render_page"], "🧪 특수검사"),
        ("drug_db", ["render_main", "render_drug_db", "render_page"], "💊 항암제 DB/상호작용"),
        ("core_utils", ["render_main", "render_page"], "🧰 유틸리티"),
    ]

    any_rendered = False
    for mod_name, fn_candidates, title in sections:
        mod = None
        try:
            mod = __import__(mod_name)
        except Exception:
            mod = _load_local(mod_name, f"{mod_name}.py")
        if not mod:
            continue

        fn = None
        for cand in fn_candidates:
            if hasattr(mod, cand):
                fn = getattr(mod, cand)
                break
        if not callable(fn):
            continue

        any_rendered = True
        with st.expander(title, expanded=True if title.startswith("🔬") else False):
            try:
                fn()  # type: ignore
            except TypeError:
                # 일부 함수는 st/session을 args로 받을 수 있음 → 인자 없이 재시도 실패 시 경고
                try:
                    fn(st)  # type: ignore
                except Exception as _e:
                    st.warning(f"{title} 로딩 실패: {_e}")

    if not any_rendered:
        st.info("불러올 메인 섹션을 찾지 못했습니다. 기존 메인 코드를 이 함수(_render_main_home) 안에서 호출하도록 연결해 주세요.")

# ====== 소아 보호자 안내(전용 페이지) ======
# pediatric modules
try:
    from peds_conditions_ui import render_peds_conditions_page  # type: ignore
except Exception:
    _m = _load_local("peds_conditions_ui", "peds_conditions_ui.py")
    render_peds_conditions_page = getattr(_m, "render_peds_conditions_page", None)

try:
    from peds_caregiver_page import render_caregiver_mode  # type: ignore
except Exception:
    _m = _load_local("peds_caregiver_page", "peds_caregiver_page.py")
    render_caregiver_mode = getattr(_m, "render_caregiver_mode", None)

try:
    from peds_symptoms_ui import render_peds_symptoms_page  # type: ignore
except Exception:
    _m = _load_local("peds_symptoms_ui", "peds_symptoms_ui.py")
    render_peds_symptoms_page = getattr(_m, "render_peds_symptoms_page", None)

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

    # 탭 구성
    tab_names = ["병명별 한눈에", "보호자 모드(묶음)"]
    if callable(render_peds_symptoms_page):
        tab_names.insert(1, "소아 증상")
    tabs = st.tabs(tab_names)

    idx = 0
    with tabs[idx]:
        if callable(render_peds_conditions_page):
            try:
                render_peds_conditions_page(key_prefix=_guide_prefix)
            except Exception as _e:
                st.warning(f"병명별 가이드 로딩 실패: {_e}")
        else:
            st.error("peds_conditions_ui 모듈을 찾을 수 없습니다.")
    idx += 1

    if "소아 증상" in tab_names:
        with tabs[idx]:
            try:
                render_peds_symptoms_page(key_prefix=_sym_prefix)  # type: ignore
            except Exception as _e:
                st.warning(f"소아 증상 로딩 실패: {_e}")
        idx += 1

    with tabs[idx]:
        if callable(render_caregiver_mode):
            try:
                render_caregiver_mode(key_prefix=_cg_prefix)
            except Exception as _e:
                st.warning(f"보호자 모드 로딩 실패: {_e}")
        else:
            st.error("peds_caregiver_page 모듈을 찾을 수 없습니다.")

# ====== 라우팅 ======
if nav_page == "메인":
    _render_main_home()
elif nav_page == "소아 안내":
    _render_pediatric_guides_section()
else:
    _render_main_home()
