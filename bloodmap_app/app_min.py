"""
Minimal entry app — uses modular router & shell only (Phase 26).
Safe alternative to heavy app.py. Original app.py remains untouched.
"""
import streamlit as st

def main():
    # Sidebar + lean toggle
    try:
        from features.app_shell import render_sidebar as _shell
        _shell(st)
    except Exception:
        pass

    # Lean-deprecator flags
    try:
        from features.app_deprecator import apply_lean_mode as _lean
        _lean(st)
    except Exception:
        pass

    # Router render (always on in this minimal entry)
    try:
        from features.app_router import render_modular_sections as _mod
        picked_keys = st.session_state.get("picked_keys", [])
        DRUG_DB = st.session_state.get("DRUG_DB", {})
        _mod(st, picked_keys, DRUG_DB)
    except Exception:
        st.warning("모듈 라우터를 불러오지 못했습니다. Phase 23~25 모듈이 설치되었는지 확인하세요.")

if __name__ == "__main__":
    main()
