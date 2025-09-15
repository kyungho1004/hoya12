
# -*- coding: utf-8 -*-
import io, os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT

FONT_CANDIDATES = [
    ("/mnt/data/NanumBarunGothic.otf", "KOR"),
    ("/mnt/data/NanumBarunGothicBold.otf", "KOR-Bold"),
    ("/mnt/data/NanumBarunGothicLight.otf", "KOR-Light"),
    ("/mnt/data/NanumBarunGothicUltraLight.otf", "KOR-UL"),
    ("/mnt/data/d84103a9-b7ea-4030-8304-a4ef04d3e1f7.otf", "KOR-Alt"),
]

def _register_fonts():
    ok = False
    for path, name in FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont(name, path))
                ok = True
            except Exception:
                pass
    # Fallback aliasing
    if not pdfmetrics.getFont("KOR"):
        from reportlab.pdfbase.cidfonts import UnicodeCIDFont
        pdfmetrics.registerFont(UnicodeCIDFont("HeiseiMin-W3"))
        pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
        # create aliases
        pdfmetrics.registerFont(TTFont("Helvetica", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
        return ("Helvetica", "Helvetica-Bold")
    # pick bold
    bold = "KOR-Bold" if "KOR-Bold" in pdfmetrics._fonts else "KOR"
    return ("KOR", bold)

BASE_STYLES = None

def _get_styles():
    global BASE_STYLES
    if BASE_STYLES: return BASE_STYLES
    base, bold = _register_fonts()
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle(name="KOR-Body", fontName=base, fontSize=11, leading=15, alignment=TA_LEFT))
    ss.add(ParagraphStyle(name="KOR-H1", fontName=bold, fontSize=16, leading=20, spaceBefore=6, spaceAfter=6))
    ss.add(ParagraphStyle(name="KOR-H2", fontName=bold, fontSize=13, leading=18, spaceBefore=4, spaceAfter=4))
    ss.add(ParagraphStyle(name="KOR-Bullet", fontName=base, fontSize=11, leading=15, leftIndent=10))
    BASE_STYLES = ss
    return ss

def export_md_to_pdf(md_text: str) -> bytes:
    """Very small markdown-ish to PDF renderer (supports #, ##, -, plain)."""
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
        line = raw.strip()
        if not line:
            flush_bullets()
            story.append(Spacer(1, 4))
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
        # fallback plain
        flush_bullets()
        story.append(Paragraph(line, ss["KOR-Body"]))

    flush_bullets()

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18*mm, rightMargin=18*mm, topMargin=18*mm, bottomMargin=18*mm)
    doc.build(story)
    return buf.getvalue()
