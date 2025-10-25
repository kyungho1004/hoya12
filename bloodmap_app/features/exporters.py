"""
Unified exporters (TXT/ICS/PDF/QR) — non-intrusive panel
- Keeps existing exporters intact; just adds a compact panel to call them.
- Saves under /mnt/data/exports
"""
from __future__ import annotations
import os
from typing import List, Dict, Any

EXPORT_DIR = "/mnt/data/exports"

def _ensure_dir():
    try:
        os.makedirs(EXPORT_DIR, exist_ok=True)
    except Exception:
        pass

def _export_txt(text: str, name: str = "export.txt") -> str:
    try:
        _ensure_dir()
        p = os.path.join(EXPORT_DIR, name)
        with open(p, "w", encoding="utf-8") as f:
            f.write(text or "")
        return p
    except Exception:
        return ""

def _export_pdf(elements: List[tuple], name: str = "export.pdf") -> str:
    try:
        _ensure_dir()
        from utils.pdf_utils import save_pdf
        p = os.path.join(EXPORT_DIR, name)
        return save_pdf(elements, p, title="Export")
    except Exception:
        return ""

def _export_ics(summary: str, description: str = "", name: str = "reminder.ics") -> str:
    """
    Write a minimal single VEVENT ics file.
    """
    try:
        from datetime import datetime, timedelta
        _ensure_dir()
        dt = datetime.now() + timedelta(minutes=1)
        dtend = dt + timedelta(minutes=30)
        ts = dt.strftime("%Y%m%dT%H%M%S")
        te = dtend.strftime("%Y%m%dT%H%M%S")
        body = (
            "BEGIN:VCALENDAR\n"
            "VERSION:2.0\n"
            "PRODID:-//BloodMap//Export//KR\n"
            "BEGIN:VEVENT\n"
            f"DTSTART:{ts}\n"
            f"DTEND:{te}\n"
            f"SUMMARY:{summary}\n"
            f"DESCRIPTION:{description}\n"
            "END:VEVENT\n"
            "END:VCALENDAR\n"
        )
        p = os.path.join(EXPORT_DIR, name)
        with open(p, "w", encoding="utf-8") as f:
            f.write(body)
        return p
    except Exception:
        return ""

def _export_qr(text: str, name: str = "export.txt") -> str:
    """
    Best-effort: save the payload to a TXT for now (QR generation may not be available here).
    Upstream QR tool can replace this later; keeping the name consistent helps migration.
    """
    return _export_txt(text, name)

def render_exporters_panel(st, payload: Dict[str, Any] | None = None):
    """
    Small button cluster to export current context.
    payload example: {"title": "...", "drugs": [...], "summary": "...", "note": "..."}
    """
    try:
        payload = payload or {}
        title = str(payload.get("title") or "내보내기 요약")
        drugs = payload.get("drugs") or []
        summary = str(payload.get("summary") or "")
        note = str(payload.get("note") or "")

        with st.expander("내보내기 (TXT/ICS/PDF/QR)", expanded=False):
            cols = st.columns([1,1,1,1,3])
            with cols[0]:
                if st.button("TXT"):
                    path = _export_txt(f"{title}\n약물: {', '.join(map(str, drugs))}\n{summary}\n{note}", "export.txt")
                    if path: st.success(f"저장됨: {path}"); st.write(f"[다운로드]({path})")
            with cols[1]:
                if st.button("ICS"):
                    path = _export_ics(title, description=summary[:120], name="reminder.ics")
                    if path: st.success(f"저장됨: {path}"); st.write(f"[다운로드]({path})")
            with cols[2]:
                if st.button("PDF"):
                    try:
                        from utils.pdf_utils import build_summary_elements
                        els = build_summary_elements(title, list(map(str, drugs)), summary, {"비고": note} if note else None)
                    except Exception:
                        els = [("h1", title), ("p", summary)]
                    path = _export_pdf(els, "export.pdf")
                    if path: st.success(f"저장됨: {path}"); st.write(f"[다운로드]({path})")
            with cols[3]:
                if st.button("QR"):
                    path = _export_qr(summary or title, "payload.txt")
                    if path: st.success(f"저장됨: {path}"); st.write(f"[다운로드]({path})")
    except Exception:
        pass
