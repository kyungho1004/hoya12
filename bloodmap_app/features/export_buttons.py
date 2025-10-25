"""
Discrete export buttons (TXT/ICS/PDF/QR) — small composable helpers.
Layered on top of features.exporters; non-intrusive.
"""
from __future__ import annotations
from typing import Dict, Any

def render_export_button_row(st, payload: Dict[str, Any] | None = None):
    try:
        from features.exporters import _export_txt, _export_pdf, _export_ics, _export_qr
    except Exception:
        _export_txt = _export_pdf = _export_ics = _export_qr = None

    try:
        payload = payload or {}
        title = str(payload.get("title") or "내보내기 요약")
        drugs = list(map(str, (payload.get("drugs") or [])))
        summary = str(payload.get("summary") or "")
        note = str(payload.get("note") or "")

        with st.expander("내보내기 (단일 버튼)", expanded=False):
            c1, c2, c3, c4 = st.columns(4)
            if _export_txt:
                with c1:
                    if st.button("TXT로"):
                        path = _export_txt(f"{title}\n약물: {', '.join(drugs)}\n{summary}\n{note}", "export.txt")
                        if path: st.success(f"저장됨: {path}"); st.write(f"[다운로드]({path})")
            if _export_ics:
                with c2:
                    if st.button("ICS로"):
                        path = _export_ics(title, description=summary[:120], name="reminder.ics")
                        if path: st.success(f"저장됨: {path}"); st.write(f"[다운로드]({path})")
            if _export_pdf:
                with c3:
                    if st.button("PDF로"):
                        try:
                            from utils.pdf_utils import build_summary_elements
                            els = build_summary_elements(title, drugs, summary, {"비고": note} if note else None)
                        except Exception:
                            els = [("h1", title), ("p", summary)]
                        path = _export_pdf(els, "export.pdf")
                        if path: st.success(f"저장됨: {path}"); st.write(f"[다운로드]({path})")
            if _export_qr:
                with c4:
                    if st.button("QR로"):
                        path = _export_qr(summary or title, "payload.txt")
                        if path: st.success(f"저장됨: {path}"); st.write(f"[다운로드]({path})")
    except Exception:
        pass
