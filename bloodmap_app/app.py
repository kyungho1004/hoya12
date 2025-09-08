
# -*- coding: utf-8 -*-
import streamlit as st
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple, Optional
from io import BytesIO

# -------- PDF backend (optional) --------
PDF_AVAILABLE = True
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
except Exception:
    PDF_AVAILABLE = False

# ===================
# Config & Data
# ===================

APP_TITLE = "🩸 피수치 가이드 / BloodMap"
APP_SIGNATURE = "제작: Hoya/GPT · 자문: Hoya/GPT"

SARCOMA_LIST = [
    "Ewing", "Osteosarcoma", "Synovial", "Leiomyosarcoma",
    "Liposarcoma", "Rhabdomyosarcoma"
]

SOLID_LIST = ["Lung", "Breast", "Colon", "Stomach", "Liver", "Pancreas", "Cholangiocarcinoma"]

HEMATO_LIST = ["AML", "APL", "ALL", "CML", "CLL"]

# 항암제/항생제 — 한글 병기
CHEMO_BY_DX: Dict[str, List[str]] = {
    "AML": ["아라씨(ARA-C)", "도우노루비신(Daunorubicin)", "에토포사이드(Etoposide)"],
    "APL": ["아트라(ATRA, 트레티노인)", "아산화비소(ATO)", "MTX(메토트렉세이트)", "6-MP(6-머캅토퓨린)"],
    "ALL": ["빈크리스틴(Vincristine)", "사이클로포스파마이드(Cyclophosphamide)", "MTX(메토트렉세이트)"],
    "CML": ["이마티닙(Imatinib)"],
    "CLL": ["플루다라빈(Fludarabine)"],
}
CHEMO_COMMON = ["그라신(G-CSF)"]

ANTIBIOTICS_COMMON = [
    "세프트리악손(ceftriaxone)", "피페라실린/타조박탐(piperacillin/tazobactam)",
    "메로페넴(meropenem)", "레보플록사신(levofloxacin)"
]

# 식이가이드 (각 5개)
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

# ===================
# Helpers
# ===================

def _parse_conc_to_mg_per_ml(conc_label: str) -> Optional[float]:
    try:
        c = conc_label.replace("mL", "ml").replace("ML", "ml")
        mg_part, ml_part = c.split("mg/")
        mg = float(mg_part.strip().split()[-1])
        ml = float(ml_part.strip().split()[0])
        if ml == 0:
            return None
        return mg / ml
    except Exception:
        return None

def _round_ml(x: float, step: float = 0.5) -> Optional[float]:
    try:
        return round(round(x / step) * step, 2)
    except Exception:
        return None

def dose_ml_acetaminophen(weight_kg, conc_label: str, mg_per_kg: float = 12.5, step: float = 0.5):
    try:
        w = float(weight_kg)
        mg_per_ml = _parse_conc_to_mg_per_ml(conc_label)
        if mg_per_ml is None or w <= 0:
            return None
        ml = (w * mg_per_kg) / mg_per_ml
        return _round_ml(ml, step)
    except Exception:
        return None

def dose_ml_ibuprofen(weight_kg, conc_label: str, mg_per_kg: float = 7.5, step: float = 0.5):
    try:
        w = float(weight_kg)
        mg_per_ml = _parse_conc_to_mg_per_ml(conc_label)
        if mg_per_ml is None or w <= 0:
            return None
        ml = (w * mg_per_kg) / mg_per_ml
        return _round_ml(ml, step)
    except Exception:
        return None

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

def build_pdf(md_text: str) -> Optional[bytes]:
    if not PDF_AVAILABLE:
        return None
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    left = 15 * mm
    top = height - 15 * mm
    max_width = width - 30 * mm

    def draw_wrapped(text: str, y: float, font="Helvetica", size=11):
        c.setFont(font, size)
        words = text.split(" ")
        line = ""
        while words:
            w = words.pop(0)
            test = (line + " " + w).strip()
            if c.stringWidth(test, font, size) <= max_width:
                line = test
            else:
                c.drawString(left, y, line)
                y -= 14
                line = w
                if y < 20 * mm:
                    c.showPage(); y = height - 20 * mm
        if line:
            c.drawString(left, y, line); y -= 14
        return y

    y = top
    for raw in md_text.splitlines():
        if raw.startswith("## "):
            y = draw_wrapped(raw[3:], y, font="Helvetica-Bold", size=12)
        elif raw.startswith("- "):
            y = draw_wrapped("• " + raw[2:], y)
        else:
            y = draw_wrapped(raw, y)
        if y < 20 * mm:
            c.showPage(); y = height - 20 * mm

    c.save()
    buffer.seek(0)
    return buffer.getvalue()

# ===================
# Interpretation
# ===================

@dataclass
class Labs:
    wbc: Optional[float] = None
    hb: Optional[float] = None
    plt: Optional[float] = None
    anc: Optional[float] = None
    ca: Optional[float] = None
    p: Optional[float] = None
    na: Optional[float] = None
    k: Optional[float] = None
    albumin: Optional[float] = None
    glucose: Optional[float] = None
    tp: Optional[float] = None
    ast: Optional[float] = None
    alt: Optional[float] = None
    ldh: Optional[float] = None
    crp: Optional[float] = None
    cr: Optional[float] = None
    ua: Optional[float] = None
    tb: Optional[float] = None
    bun: Optional[float] = None
    bnp: Optional[float] = None

def interpret_labs(labs: Labs) -> List[Tuple[str, List[str]]]:
    sections: List[Tuple[str, List[str]]] = []

    # Summary
    summary = []
    for key, label in [
        ("wbc","WBC"), ("hb","Hb"), ("plt","혈소판"), ("anc","ANC"),
        ("ca","Ca"), ("na","Na"), ("k","K"), ("albumin","Albumin"),
        ("crp","CRP"), ("cr","Cr"), ("bun","BUN"), ("tb","TB"), ("ua","UA"),
    ]:
        v = getattr(labs, key)
        if v is not None:
            summary.append(f"{label}: {v}")
    if summary:
        sections.append(("검사 요약", summary))

    # Diet guide triggers
    diet_lines: List[str] = []
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

    if labs.anc is not None and labs.anc < 500:
        diet_lines = ["[호중구 낮음 — 위생/조리 안전 수칙]"] + [f"- {rule}" for rule in NEUTROPENIA_FOOD_SAFETY] + [""] + diet_lines

    if diet_lines:
        sections.append(("식이가이드", diet_lines))

    return sections

# ===================
# UI
# ===================

def main():
    st.set_page_config(page_title="피수치 가이드 / BloodMap", layout="centered")
    st.title(APP_TITLE)
    st.caption(APP_SIGNATURE)

    # Nickname + PIN
    col1, col2 = st.columns([2,1], vertical_alignment="center")
    nickname = col1.text_input("별명", placeholder="예: 보호자A")
    pin = col2.text_input("PIN 4자리", max_chars=4, placeholder="0000")
    if pin and not pin.isdigit():
        st.warning("PIN은 숫자 4자리로 입력해주세요.")
    key_id = f"{nickname}#{pin}" if nickname and pin and pin.isdigit() and len(pin)==4 else None

    # Disease selection
    st.divider()
    st.subheader("암 그룹 / 진단")
    grp = st.selectbox("그룹", ["혈액암", "육종(진단명 분리)", "고형암(기타)"])
    if grp == "혈액암":
        dx = st.selectbox("진단명", HEMATO_LIST)
    elif grp == "육종(진단명 분리)":
        dx = st.selectbox("육종 세부", SARCOMA_LIST)
    else:
        dx = st.selectbox("고형암", SOLID_LIST)

    # Labs
    st.divider()
    st.subheader("피수치 입력")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        wbc = st.number_input("WBC", min_value=0.0, step=0.1, format="%.1f")
        hb = st.number_input("Hb", min_value=0.0, step=0.1, format="%.1f")
        plt = st.number_input("혈소판(PLT)", min_value=0.0, step=1.0, format="%.0f")
        anc = st.number_input("ANC(호중구)", min_value=0.0, step=10.0, format="%.0f")
        ca = st.number_input("Ca", min_value=0.0, step=0.1, format="%.1f")
    with c2:
        p = st.number_input("P(인)", min_value=0.0, step=0.1, format="%.1f")
        na = st.number_input("Na", min_value=0.0, step=0.5, format="%.1f")
        k = st.number_input("K", min_value=0.0, step=0.1, format="%.1f")
        albumin = st.number_input("Albumin", min_value=0.0, step=0.1, format="%.1f")
        glucose = st.number_input("Glucose", min_value=0.0, step=1.0, format="%.0f")
    with c3:
        tp = st.number_input("Total Protein", min_value=0.0, step=0.1, format="%.1f")
        ast = st.number_input("AST", min_value=0.0, step=1.0, format="%.0f")
        alt = st.number_input("ALT", min_value=0.0, step=1.0, format="%.0f")
        ldh = st.number_input("LDH", min_value=0.0, step=1.0, format="%.0f")
        crp = st.number_input("CRP", min_value=0.0, step=0.1, format="%.1f")
    with c4:
        cr = st.number_input("Creatinine(Cr)", min_value=0.0, step=0.01, format="%.2f")
        ua = st.number_input("Uric Acid(UA)", min_value=0.0, step=0.1, format="%.1f")
        tb = st.number_input("Total Bilirubin(TB)", min_value=0.0, step=0.1, format="%.1f")
        bun = st.number_input("BUN", min_value=0.0, step=0.1, format="%.1f")
        bnp = st.number_input("BNP(선택)", min_value=0.0, step=1.0, format="%.0f")

    # 특수검사(피수치 아래)
    st.divider()
    st.subheader("특수검사 (토글)")
    t1, t2, t3, t4, t5 = st.columns(5)
    with t1:
        tg_c = st.checkbox("보체")
    with t2:
        tg_u = st.checkbox("요검사/단백뇨")
    with t3:
        tg_coag = st.checkbox("응고")
    with t4:
        tg_lip = st.checkbox("지질")
    with t5:
        tg_etc = st.checkbox("기타")

    if tg_c:
        st.markdown("**보체**")
        c_c1, c_c2, c_c3 = st.columns(3)
        C3 = c_c1.number_input("C3", min_value=0.0, step=0.1, format="%.1f")
        C4 = c_c2.number_input("C4", min_value=0.0, step=0.1, format="%.1f")
        CH50 = c_c3.number_input("CH50", min_value=0.0, step=0.1, format="%.1f")

    if tg_u:
        st.markdown("**요검사/단백뇨**")
        u1, u2, u3, u4 = st.columns(4)
        hematuria = u1.selectbox("혈뇨", ["모름","음성","미세","육안적"])
        proteinuria = u2.selectbox("단백뇨", ["모름","음성","미세","+","++","+++"])
        glycosuria = u3.selectbox("요당", ["모름","음성","+","++","+++"])
        acr = u4.number_input("ACR (mg/g)", min_value=0.0, step=1.0, format="%.0f")
        upcr = st.number_input("UPCR (mg/g)", min_value=0.0, step=1.0, format="%.0f")

    if tg_coag:
        st.markdown("**응고**")
        c1, c2, c3 = st.columns(3)
        PT = c1.number_input("PT(sec)", min_value=0.0, step=0.1, format="%.1f")
        INR = c2.number_input("INR", min_value=0.0, step=0.01, format="%.2f")
        aPTT = c3.number_input("aPTT(sec)", min_value=0.0, step=0.1, format="%.1f")

    if tg_lip:
        st.markdown("**지질/혈당대사**")
        l1, l2, l3 = st.columns(3)
        chol = l1.number_input("총콜레스테롤", min_value=0.0, step=1.0, format="%.0f")
        hdl = l2.number_input("HDL", min_value=0.0, step=1.0, format="%.0f")
        tg = l3.number_input("Triglyceride", min_value=0.0, step=1.0, format="%.0f")

    if tg_etc:
        st.markdown("**기타**")
        e1, e2, e3 = st.columns(3)
        tsh = e1.number_input("TSH", min_value=0.0, step=0.01, format="%.2f")
        pct = e2.number_input("Procalcitonin", min_value=0.0, step=0.01, format="%.2f")
        lactate = e3.number_input("Lactate", min_value=0.0, step=0.1, format="%.1f")

    # Pediatric antipyretic quick calc
    st.divider()
    st.subheader("소아 해열제 빠른 계산 (중앙값 기준, ml 단일 표기)")
    pc1, pc2, pc3 = st.columns([1,1,2])
    with pc1:
        wt = st.number_input("체중(kg)", min_value=0.0, step=0.1, format="%.1f")
    with pc2:
        acet_conc = st.selectbox("아세트아미노펜 농도", ["160 mg/5 ml", "120 mg/5 ml"])
        ibu_conc = st.selectbox("이부프로펜 농도", ["100 mg/5 ml"])
    with pc3:
        if wt > 0:
            ml_acet = dose_ml_acetaminophen(wt, acet_conc)
            ml_ibu = dose_ml_ibuprofen(wt, ibu_conc)
            if ml_acet is not None:
                st.info(f"아세트아미노펜 권장 1회: **{ml_acet:.1f} ml**  (간격 4–6시간, 하루 최대 5회)")
            if ml_ibu is not None:
                st.info(f"이부프로펜 권장 1회: **{ml_ibu:.1f} ml**  (간격 6–8시간)")

    # 약물 선택 (항암제/항생제)
    st.divider()
    st.subheader("약물 선택")
    default_chemo = CHEMO_BY_DX.get(dx, [])
    st.caption("암종에 맞는 항암제가 먼저 보이며, 필요 시 추가 선택하세요.")
    sel_chemo = st.multiselect("항암제(한글 병기)", default_chemo + CHEMO_COMMON, default=default_chemo)
    sel_abx = st.multiselect("항생제(한글 병기)", ANTIBIOTICS_COMMON, default=[])

    # 해석하기
    st.divider()
    go = st.button("🔎 해석하기", type="primary", use_container_width=True)

    if go:
        labs = Labs(
            wbc=wbc or None, hb=hb or None, plt=plt or None, anc=anc or None,
            ca=ca or None, p=p or None, na=na or None, k=k or None,
            albumin=albumin or None, glucose=glucose or None, tp=tp or None,
            ast=ast or None, alt=alt or None, ldh=ldh or None, crp=crp or None,
            cr=cr or None, ua=ua or None, tb=tb or None, bun=bun or None, bnp=bnp or None
        )
        sections = interpret_labs(labs)

        # 약물 경고 요약(간단)
        warn = []
        if "MTX(메토트렉세이트)" in sel_chemo:
            warn += ["[MTX] 간 수치 상승/구내염/골수억제 주의"]
        if "6-MP(6-머캅토퓨린)" in sel_chemo:
            warn += ["[6-MP] 간독성/골수억제 주의"]
        if "아트라(ATRA, 트레티노인)" in sel_chemo:
            warn += ["[ATRA] 분화증후군, 두통/피부증상 주의"]
        if any(x in sel_abx for x in ["레보플록사신(levofloxacin)"]):
            warn += ["[FQ] 건/중추신경계 이상 드물게 보고 → 복용 중 이상 시 중단/상담"]

        if warn:
            sections.insert(0, ("약물 주의 요약", warn))

        # 화면 표시
        st.success("해석 완료 — 아래 결과와 식이가이드를 확인하세요.")
        for title, lines in sections:
            st.subheader(title)
            for ln in lines:
                st.markdown(f"- {ln}")

        # 파일로 내보내기 (TXT/PDF)
        md_text = build_sections_md(sections)
        txt_text = build_txt(md_text)
        pdf_bytes = build_pdf(md_text) if PDF_AVAILABLE else None

        st.divider()
        st.write("📄 결과 저장")
        cdl1, cdl2 = st.columns(2)
        cdl1.download_button("TXT로 저장", data=txt_text.encode("utf-8"), file_name="bloodmap_result.txt", mime="text/plain", use_container_width=True)
        if pdf_bytes is not None:
            cdl2.download_button("PDF로 저장", data=pdf_bytes, file_name="bloodmap_result.pdf", mime="application/pdf", use_container_width=True)
        else:
            cdl2.button("PDF 생성 불가 (reportlab 필요)", disabled=True, use_container_width=True)

        # 선택적으로 로컬 저장 (닉네임#PIN)
        if key_id:
            try:
                os.makedirs("data", exist_ok=True)
                stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                path = f"data/{key_id}_{stamp}.txt"
                with open(path, "w", encoding="utf-8") as f:
                    f.write(txt_text)
                st.caption(f"로컬 저장됨: {path}")
            except Exception:
                st.caption("로컬 저장 실패(권한/환경 문제).")

if __name__ == "__main__":
    main()
