
# -*- coding: utf-8 -*-
from datetime import datetime
from ..config import DISCLAIMER, APP_TITLE, MADE_BY, FONT_PATH_REG

def build_report(mode, meta, vals, cmp_lines, extra_vals, meds_lines, food_lines, abx_lines):
    lines = []
    lines.append(f"# {APP_TITLE}")
    lines.append(MADE_BY)
    lines.append("")
    lines.append(f"- 생성시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- 모드: {mode}")
    if meta.get("group"): lines.append(f"- 암 그룹: {meta.get('group')}")
    if meta.get("cancer"): lines.append(f"- 진단명: {meta.get('cancer')}")
    if meta.get("anc_place"): lines.append(f"- 현재 장소: {meta.get('anc_place')}")
    if meta.get("infect_sel"): lines.append(f"- 소아 감염질환: {meta.get('infect_sel')}")
    if meta.get("ped_topic"): lines.append(f"- 소아 주제: {meta.get('ped_topic')}")
    if meta.get("ped_inputs"):
        lines.append("## 소아 공통 입력")
        for k,v in meta["ped_inputs"].items():
            lines.append(f"- {k}: {v}")
    if meta.get("infect_info"):
        lines.append("## 감염질환 요약")
        for k,v in meta["infect_info"].items():
            lines.append(f"- {k}: {v}")
    if meta.get("infect_symptoms"):
        lines.append("## 체크한 증상")
        for s in meta["infect_symptoms"]:
            lines.append(f"- {s}")
    lines.append("")
    if vals:
        lines.append("## 입력 혈액 수치(입력한 값만)")
        for k,v in vals.items():
            if v is not None and v != "":
                lines.append(f"- {k}: {v}")
    if extra_vals:
        lines.append("## 암별 디테일 수치")
        for k,v in extra_vals.items():
            if v is not None and v != "":
                lines.append(f"- {k}: {v}")
    if cmp_lines:
        lines.append("## 수치 변화 비교")
        lines.extend(cmp_lines)
    if meds_lines:
        lines.append("## 항암제 요약")
        lines.extend(meds_lines)
    if abx_lines:
        lines.append("## 항생제 주의 요약")
        lines.extend(abx_lines)
    if food_lines:
        lines.append("## 음식 가이드")
        lines.extend(food_lines)
    lines.append("")
    lines.append("> " + DISCLAIMER)
    return "\n".join(lines)

def md_to_pdf_bytes_fontlocked(md_text):
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        import io, textwrap
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        pdfmetrics.registerFont(TTFont("KR", FONT_PATH_REG))
        width, height = A4
        x, y = 40, height-40
        for line in md_text.splitlines():
            line = line.replace("# ", "").replace("## ", "")
            for sub in textwrap.wrap(line, 80):
                c.setFont("KR", 10)
                c.drawString(x, y, sub)
                y -= 14
                if y < 40:
                    c.showPage(); y = height-40
        c.save()
        return buf.getvalue()
    except Exception as e:
        raise e
