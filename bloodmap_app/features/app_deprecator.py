"""
Lean-mode deprecator flags.
- Marks modular render used; hints legacy blocks to skip if they check these flags.
- Does NOT delete or rewrite legacy blocks.
"""
from __future__ import annotations

def apply_lean_mode(st):
    try:
        ss = st.session_state
        if not ss.get("_lean_mode"):
            return
        # Mark that modular sections will/已 렌더
        ss["_modular_render"] = True
        ss["_ae_main_rendered"] = True
        ss["_stests_rendered"] = True
        # Generic skip flags some legacy code may honor
        ss["_skip_legacy_ae"] = True
        ss["_skip_legacy_special"] = True
        ss["_skip_legacy_exports"] = True
        ss["_skip_legacy_peds"] = True
    except Exception:
        pass
