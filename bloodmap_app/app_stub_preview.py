"""
app_stub_preview.py — 레거시 블록 호출 없이, 모듈 라우터만 실행하는 *미리보기* 진입점
- 원본 app.py는 손대지 않습니다. (패치 방식)
- 실행: streamlit run app_stub_preview.py
"""
import streamlit as st

def main():
    st.markdown("### 🔍 Stub Preview Mode")
    st.caption("레거시 대블록은 호출하지 않고, 모듈 라우터만 실행합니다. (원본 app.py 보존)")

    # 1) Sidebar + Lean toggle
    try:
        from features.app_shell import render_sidebar as _shell
        _shell(st)
    except Exception:
        pass

    # 2) Lean-mode flags
    try:
        from features.app_deprecator import apply_lean_mode as _lean
        _lean(st)
    except Exception:
        pass

    # 3) Modular Router (only)
    try:
        from features.app_router import render_modular_sections as _mod
        picked_keys = st.session_state.get("picked_keys", [])
        DRUG_DB = st.session_state.get("DRUG_DB", {})
        _mod(st, picked_keys, DRUG_DB)
    except Exception:
        st.error("모듈 라우터를 불러오지 못했습니다. Phase 23–27 설치 확인이 필요합니다.")

    # 4) Diagnostics panel (dev)
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
