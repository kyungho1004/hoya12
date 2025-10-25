"""
Lean-mode legacy stubs:
- When _lean_mode is True, replace heavy legacy renderers with lightweight no-ops.
- Patch-only, runtime-only. No import changes required in app.py (we call initialize() once).
"""
from __future__ import annotations

def _stub_caption(st, title: str):
    try:
        st.caption(f"※ 경량 모드: '{title}' 레거시 블록은 모듈에서 이미 처리되어 생략되었습니다.")
    except Exception:
        pass

def initialize(st):
    try:
        ss = st.session_state
        if not ss.get("_lean_mode", True):
            return

        # ui_results: render_adverse_effects
        try:
            import ui_results as _ui
            if hasattr(_ui, "render_adverse_effects"):
                _orig = _ui.render_adverse_effects
                def _stub_render_adverse_effects(st, picked_keys, DRUG_DB):
                    _stub_caption(st, "AE(레거시)")
                    return []
                _ui.render_adverse_effects = _stub_render_adverse_effects
                ss["_skip_legacy_ae"] = True
        except Exception:
            pass

        # special_tests: special_tests_ui
        try:
            import special_tests as _st
            if hasattr(_st, "special_tests_ui"):
                def _stub_special_tests_ui():
                    try:
                        import streamlit as st
                        _stub_caption(st, "특수검사(레거시)")
                    except Exception:
                        pass
                    return []
                _st.special_tests_ui = _stub_special_tests_ui
                ss["_skip_legacy_special"] = True
        except Exception:
            pass

        # exporters panel (features.exporters)
        try:
            from features import exporters as _exp
            if hasattr(_exp, "render_exporters_panel"):
                def _stub_exporters_panel(st, payload=None):
                    _stub_caption(st, "내보내기(레거시)")
                    return
                _exp.render_exporters_panel = _stub_exporters_panel
                ss["_skip_legacy_exports"] = True
        except Exception:
            pass

        # peds: try to stub any heavy inline blocks if exposed (rare; kept conservative)
        try:
            # No direct legacy peds entrypoint known; rely on pages/peds.py
            ss["_skip_legacy_peds"] = True
        except Exception:
            pass

    except Exception:
        pass
