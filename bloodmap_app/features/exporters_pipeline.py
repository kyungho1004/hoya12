"""
Unified report pipeline — builds summary elements and exports via pdf_export if available,
otherwise falls back to features.exporters.
"""
from __future__ import annotations

def _build_elements(title: str, drugs: list[str], summary: str, notes: dict | None = None):
    els = []
    try:
        els.append(("h1", title))
        if drugs:
            els.append(("h2", "항암제 목록"))
            els.append(("ul", drugs))
        if summary:
            els.append(("h2", "요약"))
            els.append(("p", summary))
        if notes:
            els.append(("h2", "비고"))
            for k, v in notes.items():
                els.append(("p", f"{k}: {v}"))
    except Exception:
        pass
    return els or [("h1", title or "요약")]

def render_report_pipeline(st, payload: dict | None = None):
    try:
        payload = payload or {}
        title = str(payload.get("title") or "보고서")
        drugs = list(map(str, payload.get("drugs") or []))
        summary = str(payload.get("summary") or "")
        notes = payload.get("notes") or {}

        with st.expander("보고서 생성 파이프라인 (β)", expanded=False):
            c1, c2, c3 = st.columns(3)
            if c1.button("PDF 만들기"):
                path = ""
                try:
                    import pdf_export as _pe
                    els = _build_elements(title, drugs, summary, notes)
                    path = _pe.save_pdf(els, "/mnt/data/exports/report.pdf", title=title)
                except Exception:
                    # fallback
                    try:
                        from features.exporters import _export_pdf
                        els = _build_elements(title, drugs, summary, notes)
                        path = _export_pdf(els, "report.pdf")
                    except Exception:
                        path = ""
                if path:
                    st.success(f"저장됨: {path}")
                    st.write(f"[다운로드]({path})")
            if c2.button("TXT 만들기"):
                try:
                    from features.exporters import _export_txt
                    text = f"{title}\n약물: {', '.join(drugs)}\n{summary}"
                    p = _export_txt(text, "report.txt")
                    if p: st.success(f"저장됨: {p}"); st.write(f"[다운로드]({p})")
                except Exception:
                    pass
            if c3.button("ICS 만들기"):
                try:
                    from features.exporters import _export_ics
                    p = _export_ics(title, description=summary[:120], name="report.ics")
                    if p: st.success(f"저장됨: {p}"); st.write(f"[다운로드]({p})")
                except Exception:
                    pass
    except Exception:
        pass
