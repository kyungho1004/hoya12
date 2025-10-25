"""
Lightweight modular router — renders common sections and sets skip flags to reduce duplicate work.
"""
from __future__ import annotations

def render_modular_sections(st, picked_keys=None, DRUG_DB=None):
    try:
        ss = st.session_state
        ss["_modular_render"] = True  # mark modular mode
        # AE
        try:
            from features.pages.ae import render as _ae
            _ae(st, picked_keys, DRUG_DB)
        except Exception:
            pass
        # Special tests
        try:
            from features.pages.special import render as _sp
            _sp(st)
        except Exception:
            pass
        # Exports cluster
        try:
            from features.pages.exports import render as _ex
            _ex(st, picked_keys)
        except Exception:
            pass
        # Pediatrics cluster
        try:
            from features.pages.peds import render as _peds
            _peds(st)
        except Exception:
            pass
        # Hint for legacy blocks (if they check)
        ss["_ae_main_rendered"] = True
        ss["_stests_rendered"] = True
    except Exception:
        pass
