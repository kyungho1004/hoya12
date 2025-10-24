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
    """
    elements: list of (type, content) like [("h1","Title"), ("p","text"), ("img","/mnt/data/fig.png")]
    returns: PDF as bytes (or None if pdf_export unavailable)
    """
    if pdf_export is None:
        return None
    return pdf_export.build_pdf(elements, title=title, font_candidates=DEFAULT_FONT_PATHS)

def save_pdf(elements: List[Tuple[str, str]], out_path: str, title: str = "Report") -> str:
    """
    Save PDF to the given path and return it. If pdf_export is missing, returns "".
    """
    if pdf_export is None:
        return ""
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    data = pdf_export.build_pdf(elements, title=title, font_candidates=DEFAULT_FONT_PATHS)
    p.write_bytes(data)
    return p.as_posix()
