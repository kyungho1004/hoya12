
# -*- coding: utf-8 -*-
"""
app.py — FINAL special_tests hard‑fix
- 외부 special_tests.py 로드 실패해도 항상 '내장 특수검사 UI' 표시(더미 금지)
- 실패 사유를 화면에 모두 표시(경로 존재 여부, ast.parse 결과, 스택트레이스)
- 기존 기능은 손대지 않되, 특수검사 섹션만 안전 덮어쓰기(패치 방식 아이디어)
"""
from __future__ import annotations
import os, sys, importlib, importlib.util, traceback, ast
from pathlib import Path
from datetime import datetime, timedelta, timezone

import streamlit as st

try:
    st.set_page_config(page_title="BloodMap • SpecialTests FINAL", page_icon="🧪", layout="wide")
except Exception:
    pass

KST = timezone(timedelta(hours=9))
BASE_DIR = Path(__file__).parent
if "/mnt/data" not in sys.path:
    sys.path.append("/mnt/data")

def _builtin_special_tests_ui():
    st.info("✅ (내장) 특수검사 UI가 표시됩니다. 외부 special_tests.py가 실패한 경우 자동 대체됩니다.")
    with st.form("stx_special_builtin"):
        c1, c2, c3 = st.columns(3)
        with c1: crp = st.number_input("CRP", min_value=0.0, step=0.1, format="%.1f", key="stx_crp_b")
        with c2: esr = st.number_input("ESR", min_value=0.0, step=1.0, format="%.0f", key="stx_esr_b")
        with c3: pct = st.number_input("Procalcitonin (PCT)", min_value=0.0, step=0.01, format="%.2f", key="stx_pct_b")
        ok = st.form_submit_button("해석하기", use_container_width=True)
    if ok:
        if crp >= 10 or pct >= 0.5:
            st.warning("🚨 감염 가능성 ↑ — 열/증상 함께 확인하고 의료진과 상의하세요.")
        else:
            st.info("🟢 급성 염증 반응 수치는 높지 않습니다. (참고용)")
    st.caption("※ 참고용 해석 — 최종 판단은 의료진의 진료에 따릅니다.")

def _exists(p: Path):
    try: return p.exists()
    except Exception: return False

def _try_load_from_path(p: Path):
    spec = importlib.util.spec_from_file_location("special_tests", str(p))
    if spec and spec.loader:
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    raise ImportError("spec/loader 생성 실패")

def _try_pkg():
    return importlib.import_module("special_tests")

def _find_ui(mod):
    for nm in ("special_tests_ui","render","ui"):
        c = getattr(mod, nm, None)
        if callable(c):
            return c, nm
    raise AttributeError("엔트리 함수(special_tests_ui/render/ui) 없음")

def _ast_result(p: Path):
    try:
        src = p.read_text(encoding="utf-8")
    except Exception as e:
        return f"READ_FAIL: {e}"
    try:
        ast.parse(src)
        return "OK (syntax)"
    except SyntaxError as e:
        return f"SyntaxError: {e}"

def render_special_final():
    st.title("🧪 특수검사 — 최종 하드 픽스")
    st.caption(f"한국시간: {datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')}")
    errors = []
    candidates = [BASE_DIR/"special_tests.py", Path("/mnt/data")/"special_tests.py"]

    # 1) 파일 경로 시도 (ast 검사 포함)
    for p in candidates:
        try:
            if _exists(p):
                ast_info = _ast_result(p)
                mod = _try_load_from_path(p)
                ui, attr = _find_ui(mod)
                st.success(f"✅ 외부 special_tests 로드 성공 — {p} (entry: {attr}, ast={ast_info})")
                ui()
                with st.expander("🔧 로더 진단", expanded=False):
                    st.code(f"CWD={os.getcwd()}\n__file__={__file__}\nBASE_DIR={BASE_DIR}\nLOADED_FROM={p}")
                return
            else:
                errors.append(f"MISS: {p}")
        except Exception:
            errors.append(f"FAIL_LOAD_PATH: {p}\n{traceback.format_exc()}")

    # 2) 패키지 임포트
    try:
        mod = _try_pkg()
        ui, attr = _find_ui(mod)
        st.success(f"✅ 패키지 special_tests 로드 성공 — <pkg-import> (entry: {attr})")
        ui()
        with st.expander("🔧 로더 진단", expanded=False):
            st.code(f"CWD={os.getcwd()}\n__file__={__file__}\nBASE_DIR={BASE_DIR}\nLOADED_FROM=<pkg-import>")
        return
    except Exception:
        errors.append(f"FAIL_PKG_IMPORT:\n{traceback.format_exc()}")

    # 3) 모두 실패 — 내장 UI 표시 + 전체 진단
    st.error("외부 special_tests.py를 불러오지 못했습니다. 아래 진단정보를 확인하세요. (내장 UI로 대체 표시)")
    _builtin_special_tests_ui()
    with st.expander("🔎 전체 진단 출력", expanded=True):
        info = {
            "CWD": os.getcwd(),
            "__file__": __file__,
            "BASE_DIR": str(BASE_DIR),
            "CANDIDATES": [str(x) for x in candidates],
            "CANDIDATE_EXISTS": {str(x): _exists(x) for x in candidates},
            "sys.path": sys.path,
        }
        st.json(info)
        for e in errors:
            st.code(e)

render_special_final()
