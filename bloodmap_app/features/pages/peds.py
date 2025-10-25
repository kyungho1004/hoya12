"""
Modular Pediatrics page: fever, ORS, respiratory, symptom guides, ER one-page, jumpbar, export.
"""
from __future__ import annotations

def render(st):
    try:
        # Quick jumpbar at top
        try:
            from features.peds.jumpbar import render_peds_jumpbar as _jb
            _jb(st)
        except Exception:
            pass
        # Core trio
        for mod in (
            ("features.peds.fever", "render_peds_fever"),
            ("features.peds.ors", "render_peds_ors"),
            ("features.peds.resp", "render_peds_resp"),
        ):
            try:
                m = __import__(mod[0], fromlist=["_"])
                getattr(m, mod[1])(st)
            except Exception:
                pass
        # Symptom guides
        try:
            from features.peds.symptom_guides import render_peds_symptom_guides as _sg
            _sg(st)
        except Exception:
            pass
        # ER one-page
        try:
            from features.peds.er_onepage import render_peds_er_onepage as _er
            _er(st)
        except Exception:
            pass
        # Export
        try:
            from features.peds.export_panel import render_peds_export as _pexp
            _pexp(st)
        except Exception:
            pass
    except Exception:
        pass
