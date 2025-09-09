# -*- coding: utf-8 -*-
from typing import List, Tuple
import datetime as _dt
import os

FOOTER = (
    "\n\n---\n"
    "본 자료는 보호자의 이해를 돕기 위한 참고용 정보이며, "
    "모든 의학적 판단은 주치의 및 의료진의 판단을 따릅니다.\n"
    "제작: Hoya/GPT (자문: Hoya/GPT)\n"
)

def build_markdown_report(nickname_pin: str, items: List[Tuple[str, float, str, str]]):
    t = _dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [f"# 피수치 해석 결과 ({t})", f"- 사용자: `{nickname_pin}`", ""]
    for (k,v,level,hint) in items:
        lines.append(f"- **{k}**: {v} → {level} · {hint}")
    lines.append(FOOTER)
    return "\n".join(lines)

def to_txt(md_text: str) -> str:
    return md_text.replace("# ", "").replace("**", "")

def to_pdf(md_text: str, output_path: str) -> str:
    """Very simple PDF from text. Registers NanumGothic if exists for Korean."""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        W, H = A4
        # try register font
        fonts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fonts")
        ng = os.path.join(fonts_dir, "NanumGothic.ttf")
        if os.path.exists(ng):
            pdfmetrics.registerFont(TTFont("NanumGothic", ng))
            font = "NanumGothic"
        else:
            font = "Helvetica"
        c = canvas.Canvas(output_path, pagesize=A4)
        c.setFont(font, 10)
        x, y = 40, H-40
        for line in md_text.splitlines():
            if y < 40:
                c.showPage()
                c.setFont(font, 10)
                y = H-40
            c.drawString(x, y, line[:1100])
            y -= 14
        c.save()
        return output_path
    except Exception as e:
        raise
