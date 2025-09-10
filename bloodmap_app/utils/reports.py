
# -*- coding: utf-8 -*-
from datetime import datetime
from typing import Dict, Any, List

def build_report(mode: str, meta: Dict[str, Any], labs: Dict[str, Any], cmp_lines: List[str],
                 extra_vals: Dict[str, Any], meds_lines: List[str], food_lines: List[str], abx_lines: List[str]) -> str:
    md = []
    md.append(f"# BloodMap 결과 ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
    md.append(f"- 모드: {mode}")
    if meta:
        for k, v in meta.items():
            if v:
                md.append(f"- {k}: {v}")
    md.append("\n## 기본 수치")
    if labs:
        for k, v in labs.items():
            md.append(f"- {k}: {v}")
    if cmp_lines:
        md.append("\n## 수치 변화 비교")
        for l in cmp_lines:
            md.append(f"- {l}")
    if extra_vals:
        md.append("\n## 특수/확장 입력")
        for k, v in extra_vals.items():
            md.append(f"- {k}: {v}")
    if meds_lines:
        md.append("\n## 항암제 요약")
        for l in meds_lines:
            md.append(f"- {l}")
    if abx_lines:
        md.append("\n## 항생제 주의")
        for l in abx_lines:
            md.append(f"- {l}")
    if food_lines:
        md.append("\n## 음식 가이드")
        for l in food_lines:
            md.append(f"- {l}")
    return "\n".join(md)

def md_to_pdf_bytes_fontlocked(md_text: str) -> bytes:
    # Best-effort: try reportlab if available; else raise to let app show fallback message
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import mm
        import io, textwrap
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        width, height = A4
        x, y = 20*mm, height - 20*mm
        for line in md_text.splitlines():
            for wrapped in textwrap.wrap(line.replace("#","").strip(), width=90):
                c.drawString(x, y, wrapped)
                y -= 6*mm
                if y < 20*mm:
                    c.showPage(); y = height - 20*mm
        c.save()
        buf.seek(0)
        return buf.read()
    except Exception as e:
        raise e
