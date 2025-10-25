"""
app_tiny.py — 초경량 진입점 (app.py 대체용)
- 기존 app.py는 보존하고, 이 파일로 실행하거나 이름을 app.py로 바꿔서 사용하세요.
- 패치 방식 유지: 모든 기능은 분리된 features/* 모듈이 처리합니다.
"""
import streamlit as st

def main():
    # 사이드바 + 경량 모드
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

    # 모듈 라우터 (핵심)
    try:
        from features.app_router import render_modular_sections as _mod
        picked_keys = st.session_state.get("picked_keys", [])
        DRUG_DB = st.session_state.get("DRUG_DB", {})
        _mod(st, picked_keys, DRUG_DB)
    except Exception as e:
        st.error("모듈 라우터를 불러오지 못했습니다. Phases 23~27 구성 확인이 필요합니다.")
        st.exception(e)

    # 진단 패널(있으면 사용)
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
