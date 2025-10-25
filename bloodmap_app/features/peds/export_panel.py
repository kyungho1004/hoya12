"""
Pediatric exporters panel — summarizes current peds inputs and exports via features.exporters.
"""
from __future__ import annotations

def render_peds_export(st):
    try:
        try:
            from features.exporters import render_exporters_panel as _exporters
        except Exception:
            _exporters = None
        if not _exporters:
            return
        ss = st.session_state
        title = "소아 요약"
        drugs = list(ss.get("picked_keys") or [])
        # Collect common peds inputs if present
        summary_bits = []
        for k, label in [
            ("peds_age_m","나이(개월)"),
            ("peds_wt_kg","체중(kg)"),
            ("peds_sputum","가래"),
            ("peds_wheeze","쌕쌕"),
            ("peds_stool_color","변 색상"),
            ("peds_stool_tex","변 질감"),
            ("peds_stool_freq","설사 횟수/일"),
        ]:
            v = ss.get(k)
            if v not in (None, "", 0):
                summary_bits.append(f"{label}: {v}")
        summary = " | ".join(summary_bits)
        with st.expander("내보내기(소아 요약)", expanded=False):
            _exporters(st, {"title": title, "drugs": drugs, "summary": summary, "note": ""})
    except Exception:
        pass
