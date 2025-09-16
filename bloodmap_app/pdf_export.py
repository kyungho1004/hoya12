# -*- coding: utf-8 -*-
import io, os, re
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT

try:
    import qrcode
except Exception:
    qrcode = None

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

_QR_PATTERN = re.compile(r'\[\[QR:(?P<url>https?://[^\]]+)\]\]')

def export_md_to_pdf(md_text: str, qr_url: str | None = None) -> bytes:
    """Markdown 유사 포맷을 PDF로 변환.
    지원: 제목(#, ##), 글머리(- ), 인라인 [[QR:<url>]]
    qr_url 제공 시 문서 말미에 항상 QR을 추가합니다.
    """
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

    qr_candidates: list[str] = []
    for raw in (md_text or "").splitlines():
        line = raw.rstrip()
        if not line.strip():
            flush_bullets()
            story.append(Spacer(1, 6))
            continue
        m = _QR_PATTERN.search(line)
        if m:
            flush_bullets()
            url = m.group("url")
            qr_candidates.append(url)
            line = _QR_PATTERN.sub("(QR 코드가 문서 하단에 추가됩니다.)", line)

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

    # QR at the end
    final_qr = qr_url or (qr_candidates[-1] if qr_candidates else None)
    if qrcode is not None and final_qr:
        try:
            img = qrcode.make(final_qr)
            bio = io.BytesIO()
            img.save(bio, format="PNG")
            bio.seek(0)
            story.append(Spacer(1, 8))
            story.append(Paragraph("🔗 QR 코드", ss["KOR-H2"]))
            story.append(Image(bio, width=32*mm, height=32*mm))
            story.append(Paragraph(final_qr, ss["KOR-Body"]))
        except Exception:
            pass

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18*mm, rightMargin=18*mm, topMargin=18*mm, bottomMargin=18*mm)
    doc.build(story)
    return buf.getvalue()
