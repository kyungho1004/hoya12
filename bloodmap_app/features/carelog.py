"""
Carelog: append-only CSV log with a compact Streamlit UI.
File: /mnt/data/carelog.csv
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
from datetime import datetime

CARELOG_PATH = Path("/mnt/data/carelog.csv")

@dataclass
class CareEvent:
    ts_iso: str
    tag: str
    note: str = ""
    temp_c: Optional[float] = None
    hr: Optional[int] = None
    sbp: Optional[int] = None
    dbp: Optional[int] = None
    drug: str = ""
    dose_mg: Optional[float] = None

def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")

def ensure_file() -> None:
    if not CARELOG_PATH.exists():
        CARELOG_PATH.write_text("ts_iso,tag,note,temp_c,hr,sbp,dbp,drug,dose_mg\n", encoding="utf-8")

def log_event(ev: CareEvent) -> None:
    try:
        ensure_file()
        import csv
        with CARELOG_PATH.open("a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow([
                ev.ts_iso, ev.tag, ev.note.replace("\n"," ").strip(),
                ev.temp_c if ev.temp_c is not None else "",
                ev.hr if ev.hr is not None else "",
                ev.sbp if ev.sbp is not None else "",
                ev.dbp if ev.dbp is not None else "",
                ev.drug, ev.dose_mg if ev.dose_mg is not None else "",
            ])
    except Exception:
        pass

def load_events() -> List[Dict[str, Any]]:
    ensure_file()
    import csv
    rows: List[Dict[str, Any]] = []
    with CARELOG_PATH.open("r", newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            rows.append(row)
    return rows

def export_csv(path: str) -> str:
    p = Path(path)
    try:
        if CARELOG_PATH.exists():
            p.write_bytes(CARELOG_PATH.read_bytes())
            return p.as_posix()
    except Exception:
        return ""
    return ""

def export_pdf(path: str) -> str:
    try:
        from utils.pdf_utils import save_pdf
        rows = load_events()[-50:]  # last 50
        elements = [("h1", "Care Log (최근 50개)")]
        for r in rows:
            line = f"{r.get('ts_iso','')} • {r.get('tag','')} • T:{r.get('temp_c','')}°C HR:{r.get('hr','')} BP:{r.get('sbp','')}/{r.get('dbp','')} {r.get('drug','')} {r.get('dose_mg','')}mg — {r.get('note','')}"
            elements.append(("p", line))
        return save_pdf(elements, path, title="Care Log")
    except Exception:
        return ""

# ---- Minimal Streamlit UI ----
def render_carelog_ui(st) -> None:
    try:
        with st.expander("케어로그 (β)", expanded=False):
            st.caption("증상/수치/약 복용을 간단히 기록하고, CSV/PDF로 내보낼 수 있어요.")
            with st.form("carelog_form", clear_on_submit=True):
                c1, c2, c3, c4 = st.columns([1,1,1,1])
                with c1:
                    tag = st.selectbox("태그", ["증상", "해열제", "연락", "기타"], index=0)
                with c2:
                    temp_c = st.number_input("체온(°C)", min_value=0.0, max_value=45.0, value=0.0, step=0.1, format="%.1f")
                with c3:
                    hr = st.number_input("심박수", min_value=0, max_value=240, value=0, step=1)
                with c4:
                    sbp = st.number_input("수축기", min_value=0, max_value=260, value=0, step=1)
                c5, c6, c7 = st.columns([1,1,2])
                with c5:
                    dbp = st.number_input("이완기", min_value=0, max_value=200, value=0, step=1)
                with c6:
                    drug = st.text_input("약물", value="")
                with c7:
                    dose_mg = st.number_input("용량(mg)", min_value=0.0, max_value=20000.0, value=0.0, step=10.0, format="%.1f")
                note = st.text_area("메모", height=60)
                submitted = st.form_submit_button("기록 추가")
                if submitted:
                    ev = CareEvent(
                        ts_iso=_now_iso(),
                        tag=tag,
                        note=note or "",
                        temp_c=(temp_c if temp_c>0 else None),
                        hr=(hr if hr>0 else None),
                        sbp=(sbp if sbp>0 else None),
                        dbp=(dbp if dbp>0 else None),
                        drug=drug.strip(),
                        dose_mg=(dose_mg if dose_mg>0 else None),
                    )
                    log_event(ev)
                    st.success("기록 저장 완료")
            # viewer
            rows = load_events()
            if rows:
                st.write(f"총 {len(rows)}개 기록")
                # simple table
                import pandas as pd
                df = pd.DataFrame(rows)
                st.dataframe(df.tail(50), use_container_width=True)
                cexp1, cexp2 = st.columns([1,1])
                with cexp1:
                    if st.button("CSV 내보내기"):
                        out = export_csv("/mnt/data/carelog_export.csv")
                        if out:
                            st.success(f"저장됨: {out}")
                            st.write(f"[다운로드]({out})")
                with cexp2:
                    if st.button("PDF 내보내기"):
                        outp = export_pdf("/mnt/data/carelog_export.pdf")
                        if outp:
                            st.success(f"저장됨: {outp}")
                            st.write(f"[다운로드]({outp})")
            else:
                st.info("아직 기록이 없습니다.")
    except Exception:
        pass
