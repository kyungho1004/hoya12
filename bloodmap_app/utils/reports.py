# -*- coding: utf-8 -*-
from typing import Dict, List
from datetime import datetime
from ..config import DISCLAIMER, APP_TITLE, FONT_PATH_REG

def build_report(mode: str, meta: Dict, vals: Dict, cmp_lines: List[str], extra_vals: Dict, meds_lines: List[str], food_lines: List[str], abx_lines: List[str]) -> str:
    lines = []
    lines.append(f"# {APP_TITLE}")
    lines.append("")
    lines.append(f"생성시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"모드: {mode}")
    if meta:
        for k, v in meta.items():
            if v:
                lines.append(f"- {k}: {v}")
    lines.append("")
    if vals:
        lines.append("## 기본 수치(입력 항목만)")
        for k, v in vals.items():
            if v is not None:
                lines.append(f"- {k}: {v}")
    if extra_vals:
        lines.append("")
        lines.append("## 암별 디테일/특수 검사")
        for k, v in extra_vals.items():
            if v is not None:
                lines.append(f"- {k}: {v}")
    if cmp_lines:
        lines.append("")
        lines.append("## 이전 기록과 비교")
        lines.extend(cmp_lines)
    if meds_lines:
        lines.append("")
        lines.append("## 항암제 요약")
        lines.extend(meds_lines)
    if abx_lines:
        lines.append("")
        lines.append("## 항생제 요약")
        lines.extend(abx_lines)
    if food_lines:
        lines.append("")
        lines.append("## 음식 가이드")
        lines.extend(food_lines)
    lines.append("")
    lines.append("> " + DISCLAIMER)
    return "\n".join(lines)

def md_to_pdf_bytes_fontlocked(md_text: str) -> bytes:
    # 간단 텍스트 PDF (reportlab) — 마크다운 렌더링 대신 줄바꿈 텍스트
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
    except Exception as e:
        raise RuntimeError("reportlab 모듈이 필요합니다. (pip install reportlab)") from e

    # 폰트 등록(없으면 기본 폰트로)
    font_name = "NanumGothic"
    try:
        pdfmetrics.registerFont(TTFont(font_name, FONT_PATH_REG))
    except Exception:
        font_name = "Helvetica"  # fallback

    from io import BytesIO
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    x, y = 40, height - 40
    c.setFont(font_name, 10)

    for line in md_text.splitlines():
        if y < 60:
            c.showPage()
            c.setFont(font_name, 10)
            y = height - 40
        c.drawString(x, y, line[:110])  # 한 줄 제한
        y -= 14

    c.save()
    return buf.getvalue()
