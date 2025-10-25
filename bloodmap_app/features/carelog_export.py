"""
Carelog exporters — aggregate and export care logs (CSV→TXT/ICS best-effort).
- Reads /mnt/data/care_log/*.csv (if present)
- Writes exports under /mnt/data/exports
"""
from __future__ import annotations
import os, glob, csv
from datetime import datetime, timedelta

CARE_DIR = "/mnt/data/care_log"
EXPORT_DIR = "/mnt/data/exports"

def _ensure_dir():
    try:
        os.makedirs(EXPORT_DIR, exist_ok=True)
    except Exception:
        pass

def _collect_rows(limit: int = 500):
    rows = []
    try:
        for p in sorted(glob.glob(os.path.join(CARE_DIR, "*.csv"))):
            with open(p, newline="", encoding="utf-8") as f:
                r = csv.DictReader(f)
                for row in r:
                    rows.append(row)
                    if len(rows) >= limit:
                        return rows
    except Exception:
        pass
    return rows

def _export_txt(rows, name: str = "carelog.txt"):
    try:
        _ensure_dir()
        p = os.path.join(EXPORT_DIR, name)
        with open(p, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(", ".join(f"{k}:{v}" for k, v in r.items()) + "\n")
        return p
    except Exception:
        return ""

def _export_ics(rows, name: str = "carelog.ics"):
    try:
        _ensure_dir()
        body = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//BloodMap//CareLog//KR"]
        for r in rows[:200]:
            ts = (r.get("ts") or r.get("timestamp") or "")
            if not ts:
                continue
            try:
                dt = datetime.fromisoformat(ts.replace("Z","").replace(" ","T"))
            except Exception:
                # fallback: now shifting per row
                dt = datetime.now()
            te = dt + timedelta(minutes=30)
            body += [
                "BEGIN:VEVENT",
                f"DTSTART:{dt.strftime('%Y%m%dT%H%M%S')}",
                f"DTEND:{te.strftime('%Y%m%dT%H%M%S')}",
                f"SUMMARY:CareLog - {r.get('type') or r.get('event') or 'record'}",
                f"DESCRIPTION:{r.get('note') or ''}",
                "END:VEVENT",
            ]
        body += ["END:VCALENDAR"]
        p = os.path.join(EXPORT_DIR, name)
        with open(p, "w", encoding="utf-8") as f:
            f.write("\n".join(body) + "\n")
        return p
    except Exception:
        return ""

def render_carelog_export(st):
    try:
        with st.expander("케어로그 내보내기 (β)", expanded=False):
            rows = _collect_rows()
            if not rows:
                st.info("케어로그 데이터가 아직 없습니다.")
                return
            cols = st.columns([1,1,3])
            with cols[0]:
                if st.button("TXT로 저장"):
                    p = _export_txt(rows, "carelog.txt")
                    if p: st.success(f"저장됨: {p}"); st.write(f"[다운로드]({p})")
            with cols[1]:
                if st.button("ICS로 저장"):
                    p = _export_ics(rows, "carelog.ics")
                    if p: st.success(f"저장됨: {p}"); st.write(f"[다운로드]({p})")
    except Exception:
        pass
