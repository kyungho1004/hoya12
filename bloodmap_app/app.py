
# -*- coding: utf-8 -*-
"""
app.py — 최종 수정본
- 소아 보호자 가이드는 사이드바 '소아 안내'에서만 렌더
- 세션 시드 기반 네임스페이스로 탭 간/페이지 간 충돌 방지
- 기존 메인 화면은 보존(간단 안내로 대체); 필요 시 기존 메인 UI를 여기로 옮겨오면 됩니다.
"""

import streamlit as st

# ====== 사이드바 라우팅 ======
if "nav_page" not in st.session_state:
    st.session_state["nav_page"] = "메인"

with st.sidebar:
    nav_page = st.radio("페이지", ["메인", "소아 안내"], index=0, key="nav_page")

# ====== 안전 로더들 ======
import os as _os, sys as _sys, importlib.util as _ilu

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

# pediatric modules
try:
    from peds_conditions_ui import render_peds_conditions_page  # type: ignore
except Exception:
    _m = _load_local("peds_conditions_ui", "peds_conditions_ui.py")
    render_peds_conditions_page = getattr(_m, "render_peds_conditions_page", lambda **_: st.error("peds_conditions_ui 로드 실패"))

try:
    from peds_caregiver_page import render_caregiver_mode  # type: ignore
except Exception:
    _m = _load_local("peds_caregiver_page", "peds_caregiver_page.py")
    render_caregiver_mode = getattr(_m, "render_caregiver_mode", lambda **_: st.error("peds_caregiver_page 로드 실패"))

# optional symptoms page (존재하지 않으면 자동 생략)
try:
    from peds_symptoms_ui import render_peds_symptoms_page  # type: ignore
except Exception:
    _m = _load_local("peds_symptoms_ui", "peds_symptoms_ui.py")
    render_peds_symptoms_page = getattr(_m, "render_peds_symptoms_page", None)

# ====== 섹션: 소아 보호자 안내(전용 페이지) ======
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

    # 섹션 초기화(꼬임 시 클릭)
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
        try:
            render_peds_conditions_page(key_prefix=_guide_prefix)
        except Exception as _e:
            st.warning(f"병명별 가이드 로딩 실패: {_e}")
    idx += 1

    if callable(render_peds_symptoms_page):
        with tabs[idx]:
            try:
                render_peds_symptoms_page(key_prefix=_sym_prefix)
            except Exception as _e:
                st.warning(f"소아 증상 로딩 실패: {_e}")
        idx += 1

    with tabs[idx]:
        try:
            render_caregiver_mode(key_prefix=_cg_prefix)
        except Exception as _e:
            st.warning(f"보호자 모드 로딩 실패: {_e}")

# ====== 메인 / 라우팅 ======
def _render_main_placeholder():
    st.header("🩺 메인")
    st.info("메인 화면은 기존 구성을 유지하세요. 소아 보호자 가이드는 사이드바에서 **소아 안내**를 선택하면 표시됩니다.")

# 전역에서 소아 섹션을 절대 직접 호출하지 않음
if nav_page == "메인":
    _render_main_placeholder()
elif nav_page == "소아 안내":
    _render_pediatric_guides_section()
else:
    _render_main_placeholder()
