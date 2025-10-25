Phase 26 — Minimal App Entry
----------------------------
- Provides a lightweight entry `app_min.py` that renders the modular pages only.
- Original `app.py` remains untouched (패치 방식).
- Run with:
    streamlit run app_min.py
- Requires: features/app_shell.py, features/app_deprecator.py, features/app_router.py (Phases 23–25)
  + split modules under features/pages/*
- Notes:
    - `picked_keys` and `DRUG_DB` are read from `st.session_state`.
      If your pipeline sets them in `app.py`, mirror that setup here or seed them in session.
    - You can switch back to the legacy-heavy `app.py` anytime.
