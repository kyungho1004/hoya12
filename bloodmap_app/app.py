
# -*- coding: utf-8 -*-
import streamlit as st
from dataclasses import dataclass
from typing import Dict, List, Tuple
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

# -----------------------------
# Helpers: diet rules
# -----------------------------

DIET_GUIDES = {
    "Albumin_low": ["달걀", "연두부", "흰살 생선", "닭가슴살", "귀리죽"],
    "K_low": ["바나나", "감자", "호박죽", "고구마", "오렌지"],
    "Hb_low": ["소고기", "시금치", "두부", "달걀 노른자", "렌틸콩"],
    "Na_low": ["전해질 음료", "미역국", "바나나", "오트밀죽", "삶은 감자"],
    "Ca_low": ["연어통조림", "두부", "케일", "브로콜리", "(참깨 제외)"],
}

NEUTROPENIA_FOOD_SAFETY = [
    "생채소 금지, 충분히 익혀서 섭취",
    "남은 음식은 2시간 이후 섭취하지 않기",
    "멸균/살균 제품 권장",
    "껍질 있는 과일은 주치의와 상담 후 결정",
]

# -----------------------------
# Rendering / Export
# -----------------------------

def build_sections_md(sections: List[Tuple[str, List[str]]]) -> str:
    md = []
    for title, lines in sections:
        md.append(f"## {title}")
        for ln in lines:
            if ln.strip():
                if ln.startswith("- "):
                    md.append(ln)
                else:
                    md.append(f"- {ln}")
        md.append("")
    return "\n".join(md).strip() + "\n"

def build_txt(md_text: str) -> str:
    # Very simple markdown→plain text: strip '## ' headers
    out = []
    for line in md_text.splitlines():
        if line.startswith("## "):
            out.append(line[3:])
            out.append("-" * len(line[3:]))
        elif line.startswith("- "):
            out.append("• " + line[2:])
        else:
            out.append(line)
    return "\n".join(out) + "\n"

def build_pdf(md_text: str) -> bytes:
    # Simple text PDF using ReportLab
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    left = 15 * mm
    top = height - 15 * mm
    max_width = width - 30 * mm

    # Basic font (built-in) for portability
    c.setFont("Helvetica", 11)

    def draw_wrapped(text: str, y: float) -> float:
        # naive wrap
        words = text.split(" ")
        line = ""
        for w in words:
            test = (line + " " + w).strip()
            if c.stringWidth(test, "Helvetica", 11) <= max_width:
                line = test
            else:
                c.drawString(left, y, line)
                y -= 14
                line = w
                if y < 20 * mm:
                    c.showPage()
                    c.setFont("Helvetica", 11)
                    y = height - 20 * mm
        if line:
            c.drawString(left, y, line)
            y -= 14
        return y

    y = top
    for raw in md_text.splitlines():
        line = raw
        if line.startswith("## "):
            # Section header
            title = line[3:]
            c.setFont("Helvetica-Bold", 12)
            c.drawString(left, y, title)
            y -= 18
            c.setFont("Helvetica", 11)
        elif line.startswith("- "):
            y = draw_wrapped("• " + line[2:], y)
        else:
            y = draw_wrapped(line, y)

        if y < 20 * mm:
            c.showPage()
            c.setFont("Helvetica", 11)
            y = height - 20 * mm

    c.save()
    buffer.seek(0)
    return buffer.getvalue()

# -----------------------------
# Interpretation Logic (minimal demo)
# -----------------------------

@dataclass
class Labs:
    wbc: float | None = None
    hb: float | None = None
    plt: float | None = None
    anc: float | None = None
    na: float | None = None
    k: float | None = None
    ca: float | None = None
    albumin: float | None = None
    crp: float | None = None

def interpret_labs(labs: Labs) -> List[Tuple[str, List[str]]]:
    sections: List[Tuple[str, List[str]]] = []

    summary = []
    if labs.wbc is not None:
        summary.append(f"WBC: {labs.wbc}")
    if labs.hb is not None:
        summary.append(f"Hb: {labs.hb}")
    if labs.plt is not None:
        summary.append(f"혈소판: {labs.plt}")
    if labs.anc is not None:
        summary.append(f"호중구(ANC): {labs.anc}")
    if labs.crp is not None:
        summary.append(f"CRP: {labs.crp}")
    if summary:
        sections.append(("검사 요약", summary))

    # Simple flags to demo diet guide
    diet_lines = []
    if labs.albumin is not None and labs.albumin < 3.5:
        diet_lines.append("알부민 낮음 → 권장 식품: " + ", ".join(DIET_GUIDES["Albumin_low"]))
    if labs.k is not None and labs.k < 3.5:
        diet_lines.append("칼륨 낮음 → 권장 식품: " + ", ".join(DIET_GUIDES["K_low"]))
    if labs.hb is not None and labs.hb < 10:
        diet_lines.append("헤모글로빈 낮음 → 권장 식품: " + ", ".join(DIET_GUIDES["Hb_low"]))
    if labs.na is not None and labs.na < 135:
        diet_lines.append("나트륨 낮음 → 권장 식품: " + ", ".join(DIET_GUIDES["Na_low"]))
    if labs.ca is not None and labs.ca < 8.6:
        diet_lines.append("칼슘 낮음 → 권장 식품: " + ", ".join(DIET_GUIDES["Ca_low"]))

    # ANC safety overlay
    if labs.anc is not None and labs.anc < 500:
        diet_lines = ["[호중구 낮음 — 위생/조리 안전 수칙]"] + [f"- {rule}" for rule in NEUTROPENIA_FOOD_SAFETY] + [""] + diet_lines

    if diet_lines:
        # Normalize to bullet lines
        diet_bullets = []
        for ln in diet_lines:
            if ln.startswith("- ") or ln.startswith("["):
                diet_bullets.append(ln)
            else:
                diet_bullets.append(ln)
        sections.append(("식이가이드", diet_bullets))

    return sections

# -----------------------------
# UI
# -----------------------------

def main():
    st.set_page_config(page_title="피수치 가이드 / BloodMap", layout="centered")
    st.title("🩸 피수치 가이드 — 해석 & 식이가이드 즉시 표시")
    st.caption("制作者: Hoya/GPT · 자문: Hoya/GPT")

    with st.container():
        col1, col2 = st.columns([2,1])
        nickname = col1.text_input("별명", placeholder="예: 보호자A")
        pin = col2.text_input("PIN 4자리", max_chars=4, placeholder="0000")
        if pin and not pin.isdigit():
            st.warning("PIN은 숫자 4자리로 입력해주세요.")

    # 진단 카테고리
    dx_cat = st.selectbox(
        "암 그룹 / 진단",
        ["혈액암", "육종(진단명 분리)", "고형암(기타)"],
        index=0
    )
    if dx_cat == "혈액암":
        st.selectbox("진단명", ["AML", "APL", "ALL", "CML", "CLL"], index=0)
    elif dx_cat == "육종(진단명 분리)":
        st.selectbox("육종 세부", ["Ewing", "Osteosarcoma", "Synovial", "Leiomyosarcoma", "Liposarcoma", "Rhabdomyosarcoma"], index=0)
    else:
        st.selectbox("고형암", ["Lung", "Breast", "Colon", "Stomach", "Liver", "Pancreas", "Cholangiocarcinoma"], index=0)

    st.divider()
    st.header("피수치 입력")

    c1, c2, c3 = st.columns(3)
    with c1:
        wbc = st.number_input("WBC", min_value=0.0, step=0.1, format="%.1f")
        hb = st.number_input("Hb", min_value=0.0, step=0.1, format="%.1f")
        plt = st.number_input("혈소판(PLT)", min_value=0.0, step=1.0, format="%.0f")
    with c2:
        anc = st.number_input("ANC(호중구)", min_value=0.0, step=10.0, format="%.0f")
        na = st.number_input("Na", min_value=0.0, step=0.5, format="%.1f")
        k = st.number_input("K", min_value=0.0, step=0.1, format="%.1f")
    with c3:
        ca = st.number_input("Ca", min_value=0.0, step=0.1, format="%.1f")
        albumin = st.number_input("Albumin", min_value=0.0, step=0.1, format="%.1f")
        crp = st.number_input("CRP", min_value=0.0, step=0.1, format="%.1f")

    st.divider()
    go = st.button("🔎 해석하기", type="primary", use_container_width=True)

    if go:
        labs = Labs(
            wbc=wbc if wbc > 0 else None,
            hb=hb if hb > 0 else None,
            plt=plt if plt > 0 else None,
            anc=anc if anc > 0 else None,
            na=na if na > 0 else None,
            k=k if k > 0 else None,
            ca=ca if ca > 0 else None,
            albumin=albumin if albumin > 0 else None,
            crp=crp if crp > 0 else None,
        )

        sections = interpret_labs(labs)

        if not sections:
            st.info("입력한 수치가 없습니다. 값을 입력한 항목만 결과에 표시합니다.")
        else:
            st.success("해석 완료! 아래에 결과와 식이가이드를 바로 보여드려요.")
            # 화면 표시 (즉시)
            for title, lines in sections:
                st.subheader(title)
                for ln in lines:
                    if ln.strip():
                        if ln.startswith("- "):
                            st.markdown(ln)
                        else:
                            st.markdown(f"- {ln}")

            # 내보내기 (TXT / PDF)
            md_text = build_sections_md(sections)
            txt_text = build_txt(md_text)
            pdf_bytes = build_pdf(md_text)

            st.divider()
            st.write("📄 결과 저장")
            cdl1, cdl2 = st.columns(2)
            cdl1.download_button(
                "TXT로 저장",
                data=txt_text.encode("utf-8"),
                file_name="bloodmap_result.txt",
                mime="text/plain",
                use_container_width=True
            )
            cdl2.download_button(
                "PDF로 저장",
                data=pdf_bytes,
                file_name="bloodmap_result.pdf",
                mime="application/pdf",
                use_container_width=True
            )

if __name__ == "__main__":
    main()
