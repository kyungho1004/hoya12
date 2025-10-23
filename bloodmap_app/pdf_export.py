
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



# === [PATCH:P1_PDF_ONCO_AE_SECTION] BEGIN ===
def append_onco_ae_section(md_text: str, drug_list, formulation_map=None):
    """
    Appends an '항암제 요약' section to existing markdown text.
    This function is additive and safe; if ui_results isn't present, it degrades gracefully.
    """
    try:
        from ui_results import build_ae_summary_md
    except Exception:
        def build_ae_summary_md(drug_list, formulation_map=None):
            return "## 항암제 요약\n- (세부 정보를 불러오지 못했습니다)"
    section = build_ae_summary_md(drug_list, formulation_map=formulation_map)
    if not md_text: md_text = ""
    joiner = "\n\n" if not md_text.endswith("\n") else "\n"
    return md_text + joiner + section + "\n"
# === [PATCH:P1_PDF_ONCO_AE_SECTION] END ===

