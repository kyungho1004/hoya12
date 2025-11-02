
# -*- coding: utf-8 -*-
"""
app.py (hard-load special_tests)
- 기존 기능 삭제 없이, 특수검사 섹션만 '강제 로드 + 전체 진단 출력'으로 교체
- 우선순위: (1) 같은 폴더 special_tests.py → (2) /mnt/data/special_tests.py → (3) 패키지 import
- 실패 시: 검색 경로/존재여부/cwd/__file__까지 화면에 전부 출력
"""
from __future__ import annotations
import os, sys, importlib, importlib.util, traceback
from pathlib import Path
from datetime import timedelta, timezone, datetime

import streamlit as st

# ---- Page config 먼저
try:
    st.set_page_config(page_title="BloodMap • hard-load", page_icon="🧪", layout="wide")
except Exception:
    pass

# ---- 공통 KST/경로
KST = timezone(timedelta(hours=9))
BASE_DIR = Path(__file__).parent
if "/mnt/data" not in sys.path:
    sys.path.append("/mnt/data")

# ---- 상단
st.title("🧪 특수검사 (강제 로더)")
st.caption(f"한국시간: {datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')}")

def _exists(p: Path):
    try:
        return p.exists()
    except Exception:
        return False

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

def render_special_hard():
    errors = []
    candidates = [BASE_DIR/"special_tests.py", Path("/mnt/data")/"special_tests.py"]
    loaded_from = None
    mod = None
    # 1) 파일 경로 시도
    for p in candidates:
        try:
            if _exists(p):
                mod = _try_load_from_path(p)
                loaded_from = str(p)
                break
            else:
                errors.append(f"MISS: {p}")
        except Exception as e:
            errors.append(f"FAIL_LOAD_PATH: {p}\n{traceback.format_exc()}")
    # 2) 패키지
    if mod is None:
        try:
            mod = _try_pkg()
            loaded_from = "<pkg-import>"
        except Exception as e:
            errors.append(f"FAIL_PKG_IMPORT:\n{traceback.format_exc()}")
    # 3) UI 호출
    if mod is not None:
        try:
            ui, attr = _find_ui(mod)
            st.success(f"✅ special_tests 로드 성공 — {loaded_from} (entry: {attr})")
            lines = ui()
            if lines:
                with st.expander("📄 특수검사 · 디버그 로그", expanded=False):
                    for ln in lines:
                        st.write(ln)
            with st.expander("🔧 로더 진단 정보", expanded=False):
                st.code(f"CWD={os.getcwd()}\n__file__={__file__}\nBASE_DIR={BASE_DIR}\nLOADED_FROM={loaded_from}")
            return
        except Exception:
            errors.append(f"FAIL_UI_RUN:\n{traceback.format_exc()}")
    # 4) 실패 보고서
    st.warning("special_tests.py를 찾거나 실행하지 못했습니다. (하단 진단 정보 확인)")
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

# ---- 실제 호출
render_special_hard()
