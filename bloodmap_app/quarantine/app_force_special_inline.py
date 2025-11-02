# ==== PATCH • App bootstrap for Special Tests fallback (non-destructive) ====
from __future__ import annotations
import streamlit as st
try:
    from special_tests_force_inline import force_render_special_tab
    # Render once at end of the app lifecycle
    force_render_special_tab()
except Exception as e:  # pragma: no cover
    try:
        st.warning(f"특수검사 폴백 부트스트랩 오류: {e}")
    except Exception:
        pass
# ==== /PATCH END ====