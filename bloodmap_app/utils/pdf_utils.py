"""
Thin wrapper utilities for pdf_export to keep calling sites clean.
"""
from typing import List, Tuple, Optional
from pathlib import Path
try:
    import pdf_export  # existing module
except Exception:
    pdf_export = None  # allow import even if missing in some environments

DEFAULT_FONT = "NanumGothic"
DEFAULT_FONT_PATHS = [
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/mnt/data/NanumGothic.ttf",
]

def to_pdf_bytes(elements: List[Tuple[str, str]], title: str = "Report") -> Optional[bytes]:
    if pdf_export is None:
        return None
    return pdf_export.build_pdf(elements, title=title, font_candidates=DEFAULT_FONT_PATHS)

def save_pdf(elements: List[Tuple[str, str]], out_path: str, title: str = "Report") -> str:
    if pdf_export is None:
        return ""
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    data = pdf_export.build_pdf(elements, title=title, font_candidates=DEFAULT_FONT_PATHS)
    p.write_bytes(data)
    return p.as_posix()

# ---- Phase 8: Patient summary preset ----
from datetime import datetime

def _now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def build_summary_elements(title: str, drugs: list[str], ae_snippet: str, extra: dict[str, str] | None = None):
    els: list[tuple[str, str]] = []
    if title:
        els.append(("h1", title))
    if drugs:
        els.append(("p", "선택 약물: " + ", ".join(drugs)))
    if ae_snippet:
        els.append(("p", ae_snippet.strip()))
    for k, v in (extra or {}).items():
        if k:
            els.append(("h2", str(k)))
        if v:
            els.append(("p", str(v)))
    return els

def save_patient_summary(drugs: list[str], ae_snippet: str, extra: dict[str, str] | None = None, out_path: str | None = None) -> str:
    fn = out_path or f"/mnt/data/summary_{_now_stamp()}.pdf"
    els = build_summary_elements("환자 안내 요약", drugs, ae_snippet, extra=extra)
    try:
        return save_pdf(els, fn, title="환자 안내 요약")
    except Exception:
        return ""
