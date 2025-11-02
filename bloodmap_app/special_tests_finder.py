# -*- coding: utf-8 -*-
"""
special_tests_finder.py — robust loader + embedded safe fallback

Use inside the '특수검사' tab:
    from special_tests_finder import render_special_tests_safe
    render_special_tests_safe()

Behavior:
- Try to import an actual special_tests.py from common locations.
- If not found, render an embedded, monkeypatch-free fallback UI (so the tab never looks empty).
"""

from __future__ import annotations
import os, sys, importlib, importlib.util, types
from pathlib import Path

# --- 0) Streamlit originals restore ------------------------------------------
def _restore_streamlit_originals():
    try:
        import streamlit as st
    except Exception:
        return
    if not hasattr(st, "_bm_text_input_orig"):
        st._bm_text_input_orig = st.text_input
    if not hasattr(st, "_bm_selectbox_orig"):
        st._bm_selectbox_orig = st.selectbox
    if not hasattr(st, "_bm_text_area_orig"):
        st._bm_text_area_orig = st.text_area
    st.text_input  = st._bm_text_input_orig
    st.selectbox   = st._bm_selectbox_orig
    st.text_area   = st._bm_text_area_orig

# --- 1) Fallback (embedded) UI (monkeypatch-free) -----------------------------
def _embedded_special_tests_ui():
    import streamlit as st
    # originals
    TI = getattr(st, "_bm_text_input_orig", st.text_input)
    SB = getattr(st, "_bm_selectbox_orig",  st.selectbox)
    TA = getattr(st, "_bm_text_area_orig",  st.text_area)

    def _k(key: str) -> str:
        uid = st.session_state.get("user_key_raw") or st.session_state.get("key") or "guest"
        return f"st_{uid}_{key}"

    st.subheader("특수검사 (임시 안전판)")
    st.caption("※ special_tests.py가 배치되면 이 안전판 대신 실제 모듈 UI가 자동으로 표시됩니다.")

    # U/A
    st.markdown("#### 소변 검사(U/A)")
    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: alb = SB("Albumin (알부민뇨)", ["없음","+","++","+++"], index=0, key=_k("ua_alb"))
    with c2: ket = SB("Ketone (케톤)", ["없음","+","++","+++"], index=0, key=_k("ua_ket"))
    with c3: bld = SB("Blood (혈뇨)", ["없음","+","++","+++"], index=0, key=_k("ua_bld"))
    with c4: nit = SB("Nitrite (아질산염)", ["음성","양성"], index=0, key=_k("ua_nit"))
    with c5: glu = SB("Glucose (당)", ["없음","+","++","+++"], index=0, key=_k("ua_glu"))

    tips = []
    if nit == "양성": tips.append("요로감염 가능성: 발열·복통·배뇨통 동반 시 진료 권고")
    if bld in ("++","+++") and alb in ("++","+++"): tips.append("사구체염 의심: 부종·혈압 확인 및 진료 권고")
    if ket in ("++","+++") and glu in ("++","+++"): tips.append("당뇨성 케톤산증 의심: 탈수/구토/호흡곤란 시 응급실 권고")
    if tips: 
        for t in tips: st.warning("• " + t)
    else:
        st.info("특이소견 없음에 가까움. 증상과 함께 관찰하세요.")

    # 설사
    st.markdown("#### 설사 간단 분류")
    color = SB("변 색상", ["노란색","녹색","피 섞임","검은색","정상/갈색"], key=_k("d_color"))
    freq  = SB("횟수", ["1~3회/일","4회 이상/일"], key=_k("d_freq"))
    mucus = SB("점액", ["없음","조금","많음"], key=_k("d_mucus"))
    if freq == "4회 이상/일" or color in ("피 섞임","검은색"):
        st.warning("🚨 경고: 탈수/혈변 위험. 수분보충과 의료진 상담 권장.")
    st.caption("※ 본 해석은 참고용이며, 정확한 진단은 의료진 판단에 따릅니다.")

    # 구내염
    st.markdown("#### 구내염 자가 관리")
    sev = SB("통증 정도", ["없음","약함","중간","심함"], key=_k("muc_sev"))
    st.info("처방받은 가글을 사용하세요. 약국 생리식염수는 **1주 이상 연속 사용 금지**.")
    if sev in ("중간","심함"):
        st.warning("통증 조절 필요. 음식/수분 섭취가 어려우면 진료 권장.")

    # 메모
    st.markdown("#### 메모")
    TA("특수검사 관련 메모(선택)", key=_k("memo_st"))

    st.success("특수검사 UI(임시 안전판) 로드 완료.")

# --- 2) Find & load external special_tests.py if present ----------------------
COMMON_PATHS = [
    Path(__file__).parent / "special_tests.py",                          # same dir
    Path(__file__).parent.parent / "special_tests.py",                   # parent
    Path("/mount/src/hoya12/bloodmap_app/special_tests.py"),            # common deploy path
    Path("/mnt/data/special_tests.py"),                                  # fallback (this chat)
]

def _load_by_path(p: Path) -> types.ModuleType | None:
    try:
        spec = importlib.util.spec_from_file_location("special_tests", str(p))
        mod = importlib.util.module_from_spec(spec)  # type: ignore
        sys.modules["special_tests"] = mod
        assert spec and spec.loader
        spec.loader.exec_module(mod)  # type: ignore
        return mod
    except Exception as e:
        import streamlit as st
        st.error(f"special_tests 로드 실패: {e}")
        return None

def _find_module() -> types.ModuleType | None:
    # Already importable?
    try:
        return importlib.import_module("special_tests")
    except Exception:
        pass
    # Search common paths
    for p in COMMON_PATHS:
        if p.exists():
            return _load_by_path(p)
    return None

def _call_entry(mod: types.ModuleType):
    for name in ("special_tests_ui", "render_special_tests", "injector", "render", "main"):
        fn = getattr(mod, name, None)
        if callable(fn):
            return fn()
    # fallback: any render-like function
    for name in dir(mod):
        if name.startswith(("render_", "ui_", "build_")):
            fn = getattr(mod, name, None)
            if callable(fn):
                return fn()
    import streamlit as st
    st.info("special_tests.py에서 UI 진입 함수를 찾지 못했습니다. special_tests_ui()를 만들어 주세요.")

# --- 3) Public API ------------------------------------------------------------
def render_special_tests_safe():
    import streamlit as st
    os.environ["BM_DISABLE_ST_PATCH"] = "1"  # block any global monkeypatch attempts
    _restore_streamlit_originals()

    mod = _find_module()
    if mod is None:
        # No external module found: show embedded safe UI (never empty)
        _restore_streamlit_originals()
        _embedded_special_tests_ui()
        st.caption("※ special_tests.py를 app.py와 같은 폴더 또는 /mount/src/hoya12/bloodmap_app/ 에 배치하면, 다음 리런부터 실제 모듈 UI가 표시됩니다.")
        return

    # ensure originals after import
    _restore_streamlit_originals()
    return _call_entry(mod)
