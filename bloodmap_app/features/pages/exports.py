"""
Modular Exporters page: general exporters + pipeline + carelog export.
"""
from __future__ import annotations

def render(st, picked_keys):
    try:
        payload = {"title": "내보내기 요약", "drugs": list(picked_keys or []), "summary": "", "note": ""}
        try:
            from features.exporters import render_exporters_panel as _exp
            _exp(st, payload)
        except Exception:
            pass
        try:
            from features.exporters_pipeline import render_report_pipeline as _pipe
            _pipe(st, {"title": "보고서", "drugs": list(picked_keys or []), "summary": ""})
        except Exception:
            pass
        try:
            from features.carelog_export import render_carelog_export as _care
            _care(st)
        except Exception:
            pass
    except Exception:
        pass
