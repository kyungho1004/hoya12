# -*- coding: utf-8 -*-
from io import BytesIO

def build_report(mode, meta, vals, cmp_lines, extra_vals, meds_lines, food_lines, abx_lines):
    lines = []
    lines.append("# BloodMap 보고서")
    lines.append(f"- 모드: {mode}")
    for k in ["group","cancer","ped_topic","infect_sel","anc_place"]:
        if meta.get(k): lines.append(f"- {k}: {meta.get(k)}")

    if meta.get("ped_inputs"):
        lines.append("\n## 소아 입력 요약")
        for k, v in meta["ped_inputs"].items(): lines.append(f"- {k}: {v}")

    ent = {k: v for k, v in (vals or {}).items() if v not in (None, "")}
    if ent:
        lines.append("\n## 입력한 혈액 수치")
        for k, v in ent.items(): lines.append(f"- {k}: {v}")

    if cmp_lines:
        lines.append("\n## 수치 변화 비교")
        lines.extend([f"- {x}" for x in cmp_lines])

    ex = {k: v for k, v in (extra_vals or {}).items() if v not in (None, "")}
    if ex:
        lines.append("\n## 암별 디테일 수치")
        for k, v in ex.items(): lines.append(f"- {k}: {v}")

    if meds_lines:
        lines.append("\n## 항암제 요약"); lines.extend(meds_lines)
    if food_lines:
        lines.append("\n## 음식 가이드"); lines.extend([f"- {x}" for x in food_lines])
    if abx_lines:
        lines.append("\n## 항생제 주의 요약"); lines.extend(abx_lines)

    lines.append("\n---\n본 자료는 보호자의 이해를 돕기 위한 참고용 정보이며, 모든 의학적 판단은 주치의의 권한입니다.")
    return "\n".join(lines)

def md_to_pdf_bytes_fontlocked(md_text: str):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        try:
        from ..config import FONT_PATH_REG
    except Exception:
        from config import FONT_PATH_REG
        pdfmetrics.registerFont(TTFont("NanumGothic", FONT_PATH_REG))
        buf = BytesIO(); c = canvas.Canvas(buf, pagesize=A4)
        width, height = A4; x, y = 40, height-40
        c.setFont("NanumGothic", 11)
        for line in md_text.splitlines():
            if y < 60: c.showPage(); c.setFont("NanumGothic", 11); y = height-40
            c.drawString(x, y, line[:1100]); y -= 16
        c.save(); buf.seek(0); return buf.read()
    except FileNotFoundError:
        raise
    except Exception:
        return md_text.encode("utf-8")
