
# -*- coding: utf-8 -*-
import io, os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT

FONT_MAP = [
    ("/mnt/data/NanumBarunGothic.otf", "KOR"),
    ("/mnt/data/NanumBarunGothicBold.otf", "KOR-Bold"),
    ("/mnt/data/NanumBarunGothicLight.otf", "KOR-Light"),
    ("/mnt/data/NanumBarunGothicUltraLight.otf", "KOR-UL"),
    ("/mnt/data/d84103a9-b7ea-4030-8304-a4ef04d3e1f7.otf", "KOR-Alt"),
]

def _register_fonts():
    regular = None
    bold = None
    for path, name in FONT_MAP:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont(name, path))
                if name == "KOR" or regular is None:
                    regular = name
                if "Bold" in name and bold is None:
                    bold = name
            except Exception:
                pass
    if not regular:
        try:
            from reportlab.pdfbase.cidfonts import UnicodeCIDFont
            regular = "HeiseiKakuGo-W5"
            pdfmetrics.registerFont(UnicodeCIDFont(regular))
            bold = regular
        except Exception:
            regular = "Helvetica"
            bold = "Helvetica"
    return regular, bold

_styles = None
def _get_styles():
    global _styles
    if _styles: return _styles
    base, bold = _register_fonts()
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle(name="KOR-Body", fontName=base, fontSize=11, leading=15, alignment=TA_LEFT))
    ss.add(ParagraphStyle(name="KOR-H1", fontName=bold, fontSize=16, leading=20, spaceBefore=6, spaceAfter=6))
    ss.add(ParagraphStyle(name="KOR-H2", fontName=bold, fontSize=13, leading=18, spaceBefore=4, spaceAfter=4))
    _styles = ss
    return ss

def export_md_to_pdf(md_text: str) -> bytes:
    ss = _get_styles()
    story = []
    bullets = []

    def flush_bullets():
        nonlocal bullets
        if bullets:
            lf = ListFlowable([ListItem(Paragraph(b, ss["KOR-Body"])) for b in bullets], bulletType="bullet", start="•")
            story.append(lf)
            story.append(Spacer(1, 4))
            bullets = []

    for raw in (md_text or "").splitlines():
        line = raw.rstrip()
        if not line.strip():
            flush_bullets()
            story.append(Spacer(1, 6))
            continue
        if line.startswith("## "):
            flush_bullets()
            story.append(Paragraph(line[3:], ss["KOR-H2"]))
            continue
        if line.startswith("# "):
            flush_bullets()
            story.append(Paragraph(line[2:], ss["KOR-H1"]))
            continue
        if line.startswith("- "):
            bullets.append(line[2:].strip())
            continue
        flush_bullets()
        story.append(Paragraph(line, ss["KOR-Body"]))

    flush_bullets()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18*mm, rightMargin=18*mm, topMargin=18*mm, bottomMargin=18*mm)
    doc.build(story)
    return buf.getvalue()


def export_ors_onepager(save_path: str = "/mnt/data/ors_onepager.pdf") -> str:
    """Build a single-page ORS dehydration guidance PDF and save it.

    Returns the saved file path.

    """
    lines = [
        "# ORS(경구수분보충) / 탈수 가이드",
        "- 5~10분마다 소량씩 자주, 토하면 10~15분 휴식 후 재개",
        "- 2시간 이상 소변 없음 / 입마름 / 눈물 감소 / 축 늘어짐 → 진료",
        "- 가능하면 스포츠음료 대신 ORS 용액 사용",
        "",
        "# ORS 집에서 만드는 법 (WHO 권장 비율, 1 L 기준)",
        "- 끓였다 식힌 물 1 L",
        "- 설탕 작은술 6스푼(평평하게) ≈ 27 g",
        "- 소금 작은술 1/2 스푼(평평하게) ≈ 2.5 g",
        "",
        "- 모두 완전히 녹을 때까지 저어주세요.",
        "- 5~10분마다 소량씩 마시고, 토하면 10~15분 쉬었다 재개하세요.",
        "- 맛은 '살짝 짠 단물(눈물맛)' 정도가 정상입니다. 너무 짜거나 달면 물을 더 넣어 희석하세요.",
        "",
        "# 주의",
        "- 과일주스·탄산·순수한 물만 대량 섭취는 피하세요(전해질 불균형 위험).",
        "- 6개월 미만 영아/만성질환/신생아는 반드시 의료진과 상의 후 사용하세요.",
        "- 설탕 대신 꿀 금지(영아 보툴리누스 위험).",
    ]
    pdf_bytes = export_md_to_pdf(lines)
    Path(save_path).write_bytes(pdf_bytes)
    return save_path
