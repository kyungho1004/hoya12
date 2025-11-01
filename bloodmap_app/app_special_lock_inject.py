\
# app_special_lock_inject.py — Special Tests Force Loader (Patch-only)
from __future__ import annotations
import importlib.util, sys, pathlib
import streamlit as st

def _force_load_safe_special_tests():
    app_dir = pathlib.Path(__file__).parent
    candidate = app_dir / "special_tests.py"
    if not candidate.exists():
        st.warning("special_tests.py 안전판이 없습니다. (app_dir/special_tests.py)")
        return None
    spec = importlib.util.spec_from_file_location("special_tests", str(candidate))
    if not spec or not spec.loader:
        st.error("special_tests 안전판 로딩 실패(spec).")
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

def special_tests_ui():
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
