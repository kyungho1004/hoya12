# app.py — hardened build: force-use built-in SAFE special_tests UI (no external monkeypatch risk)
import streamlit as st
# ==== FORCE-LOAD SAFE special_tests (hard lock) ====
import importlib.util, sys, pathlib, types
import streamlit as st

def _force_load_safe_special_tests():
    app_dir = pathlib.Path(__file__).parent
    candidate = app_dir / "special_tests.py"   # 우리가 배치한 안전판 파일 위치
    if not candidate.exists():
        st.warning("special_tests.py 안전판이 없습니다. (app_dir/special_tests.py)")
        return None
    spec = importlib.util.spec_from_file_location("special_tests", str(candidate))
    if not spec or not spec.loader:
        st.error("special_tests 안전판 로딩 실패(spec).")
        return None
    mod = importlib.util.module_from_spec(spec)          # 새 모듈 객체 생성
    sys.modules["special_tests"] = mod                   # 이름 고정 (다른 import들이 이걸 보게)
    spec.loader.exec_module(mod)                         # 실제 로드
    return mod

try:
    _stmod = _force_load_safe_special_tests()
    st.caption(f"special_tests loaded from (FORCED): {getattr(_stmod,'__file__',None)}")
except Exception as _e:
    st.caption(f"special_tests force-load failed: {_e}")
    _stmod = None

# 안전 호출 래퍼: 문제가 나도 빈 리스트/안내문으로 회복
def special_tests_ui_safe():
    if not _stmod or not hasattr(_stmod, "special_tests_ui"):
        st.warning("특수검사 안전판 모듈이 없어 더미 UI로 대체합니다.")
        st.session_state["special_interpretations"] = ["특수검사 모듈을 찾지 못했습니다."]
        return ["특수검사 모듈을 찾지 못했습니다."]
    try:
        lines = _stmod.special_tests_ui()
        # 방어적: 항상 리스트 보장
        if isinstance(lines, list):
            st.session_state["special_interpretations"] = [str(x) for x in lines if x is not None]
        elif isinstance(lines, str) and lines.strip():
            st.session_state["special_interpretations"] = [lines.strip()]
        else:
            st.session_state["special_interpretations"] = ["특수검사 항목을 펼치지 않아 요약이 없습니다. 필요 시 토글을 열어 값을 입력하세요."]
        return st.session_state["special_interpretations"]
    except Exception as e:
        st.error(f"특수검사 UI 실행 오류(안전모드로 전환): {e}")
        st.session_state["special_interpretations"] = ["특수검사 UI 실행 중 오류가 발생하여 안전모드로 전환되었습니다."]
        return st.session_state["special_interpretations"]

# 기존 코드가 special_tests_ui()를 호출하더라도 안전판으로 흡수되게 alias
special_tests_ui = special_tests_ui_safe
# ==== /FORCE-LOAD SAFE special_tests ====
