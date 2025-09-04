# -*- coding: utf-8 -*-
import streamlit as st
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime

APP_VERSION = "v3.14.7-lipid-quickfix"

# ---------- Helpers ----------
def page_header():
    st.set_page_config(page_title="피수치 가이드 / BloodMap", layout="centered")
    st.markdown(
        "<style> .small-muted{{font-size:12px; color:#777}} .warn{{color:#b30000; font-weight:600}} .ok{{color:#136f63}} </style>",
        unsafe_allow_html=True,
    )
    st.title("🩸 피수치 가이드 — BloodMap")
    st.caption(f"모바일 최적화 / {{APP_VERSION}}  | 제작/자문: Hoya/GPT")
    st.write("---")

def num_input(label, key, step=1.0, min_value=0.0, max_value=None, placeholder="예: 0.0", decimals=1):
    return st.number_input(label, key=key, min_value=min_value, max_value=max_value, step=step, format=f"%.{decimals}f", help=placeholder)

def line():
    st.markdown("<hr/>", unsafe_allow_html=True)

def build_summary_text(basic_vals, order_vals, urine_vals, lipid_vals, guide_msgs, meta):
    lines = []
    lines.append("# 피수치 가이드 요약")
    lines.append("")
    lines.append(f"- 생성시각: {{datetime.now().strftime('%Y-%m-%d %H:%M')}} (한국시간)")
    lines.append(f"- 사용자: {{meta.get('nick','-')}}#{{meta.get('pin','----')}}")
    lines.append("")
    lines.append("## 기본 수치")
    for k, v in basic_vals.items():
        if v is not None and v != "":
            lines.append(f"- {{k}}: {{v}}")
    lines.append("")
    if order_vals:
        lines.append("## ORDER 20 항목 (요약 입력)")
        for k, v in order_vals.items():
            if v is not None and v != "":
                lines.append(f"- {{k}}: {{v}}")
        lines.append("")
    if urine_vals:
        lines.append("## 특수검사 — 요검사")
        for k, v in urine_vals.items():
            if v is not None and v != "":
                lines.append(f"- {{k}}: {{v}}")
        lines.append("")
    if lipid_vals:
        lines.append("## 특수검사 — 지질패널")
        for k, v in lipid_vals.items():
            if v is not None and v != "":
                lines.append(f"- {{k}}: {{v}}")
        lines.append("")
    if guide_msgs:
        lines.append("## 생활/식이 가이드 (자동 합산)")
        for g in guide_msgs:
            lines.append(f"- {{g}}")
    lines.append("")
    lines.append("> 본 자료는 보호자의 이해를 돕기 위한 참고용 정보이며, 의학적 판단은 의료진의 권한입니다.")
    return "\n".join(lines)

def bytes_for_txt(md_text):
    return md_text.encode("utf-8")

def bytes_for_md(md_text):
    return md_text.encode("utf-8")

def bytes_for_pdf(md_text):
    # 간단 PDF (영문/숫자 위주 렌더링). 한글 폰트 미설치 환경에선 일부 글자가 깨질 수 있음.
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    x, y = 40, height - 40
    for line in md_text.split("\n"):
        if y < 60:
            c.showPage()
            y = height - 40
        c.drawString(x, y, line[:110])  # 줄 길이 제한
        y -= 16
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()

def add_guide(msgs, text):
    if text not in msgs:
        msgs.append(text)

# ---------- UI ----------
def main():
    page_header()

    # 별명 + PIN 4자리 (중복 방지)
    st.subheader("👤 사용자 식별")
    col1, col2 = st.columns([2,1])
    with col1:
        nick = st.text_input("별명", key="nick", placeholder="예: 보호자A")
    with col2:
        pin = st.text_input("PIN (4자리 숫자)", key="pin", max_chars=4, placeholder="1234")
    if pin and (not pin.isdigit() or len(pin) != 4):
        st.warning("PIN은 숫자 4자리로 입력해주세요.")
    user_key = f"{{(nick or '').strip()}}#{{(pin or '----').strip()}}"

    line()

    # 기본 수치 (요약 입력 — 실제 앱에서는 ORDER 20 전체 포함)
    st.subheader("1️⃣ 기본 수치 (요약)")
    colA, colB = st.columns(2)
    with colA:
        wbc = num_input("WBC (x10³/µL)", "wbc", step=0.1, decimals=1)
        hb = num_input("Hb (g/dL)", "hb", step=0.1, decimals=1)
        plt = num_input("혈소판 (x10³/µL)", "plt", step=1.0, decimals=0)
        anc = num_input("ANC (호중구, /µL)", "anc", step=10.0, decimals=0)
        albumin = num_input("Albumin (g/dL)", "albumin", step=0.1, decimals=1)
    with colB:
        na = num_input("Na (mmol/L)", "na", step=1.0, decimals=0)
        k = num_input("K (mmol/L)", "k", step=0.1, decimals=1)
        ca = num_input("Ca (mg/dL)", "ca", step=0.1, decimals=1)
        crp = num_input("CRP (mg/dL)", "crp", step=0.1, decimals=2)
        glu = num_input("Glucose (mg/dL)", "glu", step=1.0, decimals=0)

    basic_vals = {{
        "WBC": wbc, "Hb": hb, "혈소판": plt, "ANC": anc, "Albumin": albumin,
        "Na": na, "K": k, "Ca": ca, "CRP": crp, "Glucose": glu
    }}

    # 특수검사 — 요검사 패널
    line()
    st.subheader("2️⃣ 특수검사 — 요검사 패널")
    colU1, colU2, colU3 = st.columns(3)
    with colU1:
        urine_prot = st.selectbox("요단백 (Protein, urine)", ["-", "Negative", "Trace", "1+", "2+", "3+"], index=0, key="ur_prot")
    with colU2:
        urine_blood = st.selectbox("잠혈 (Occult blood, urine)", ["-", "Negative", "Trace", "1+", "2+", "3+"], index=0, key="ur_bld")
    with colU3:
        urine_glu = st.selectbox("요당 (Glucose, urine)", ["-", "Negative", "Trace", "1+", "2+", "3+"], index=0, key="ur_glu")
    urine_vals = {{
        "요단백": urine_prot, "잠혈": urine_blood, "요당": urine_glu
    }}

    # 특수검사 — 지질 패널 (신설)
    line()
    st.subheader("3️⃣ 특수검사 — 지질패널 (신설)")
    colL1, colL2, colL3, colL4 = st.columns(4)
    with colL1:
        tg = num_input("TG (중성지방, mg/dL)", "tg", step=10.0, decimals=0)
    with colL2:
        tchol = num_input("총콜레스테롤 (mg/dL)", "tchol", step=5.0, decimals=0)
    with colL3:
        hdl = st.text_input("HDL (선택, mg/dL)", key="hdl", placeholder="선택")
    with colL4:
        ldl = st.text_input("LDL (선택, mg/dL)", key="ldl", placeholder="선택")
    lipid_vals = {{"TG": tg, "총콜레스테롤": tchol, "HDL": hdl, "LDL": ldl}}

    # 가이드 로직 (합산)
    line()
    st.subheader("4️⃣ 생활/식이 가이드")
    guides = []

    # 기본 가이드 샘플 (핵심들만 — 실제 앱에선 모든 항목 확장)
    if anc and anc < 500:
        add_guide(guides, "ANC 500 미만: 생야채 금지, 익힌 음식 섭취, 남은 음식 2시간 이후 섭취 금지, 멸균식품 권장")
    if albumin and albumin < 3.0:
        add_guide(guides, "알부민 낮음: 달걀·연두부·흰살생선·닭가슴살·귀리죽 권장")
    if k and k < 3.5:
        add_guide(guides, "칼륨 낮음: 바나나·감자·호박죽·고구마·오렌지 권장")
    if hb and hb < 8.0:
        add_guide(guides, "Hb 낮음: 소고기·시금치·두부·달걀노른자·렌틸콩 권장 (철분제는 의사와 상의)")
    if na and na < 135:
        add_guide(guides, "나트륨 낮음: 전해질 음료·미역국·오트밀죽·삶은 감자 권장")
    if ca and ca < 8.5:
        add_guide(guides, "칼슘 낮음: 연어통조림·두부·케일·브로콜리 권장")

    # 지질패널 로직 (요청사항 반영)
    if tg and tg >= 200:
        add_guide(guides, "중성지방(TG) 높음: 단 음료/과자 제한 · 튀김/버터/마요네즈 등 기름진 음식 줄이기 · 라면/가공식품(짠맛) 줄이기 · 채소/등푸른생선/현미·잡곡/소량 견과류 권장")
    if tchol and tchol >= 240:
        add_guide(guides, "총콜레스테롤 높음(≥240): 포화·트랜스지방 줄이기(가공육·튀김·제과) · 가공치즈/크림 줄이기 · 식이섬유(귀리·콩류·과일) 늘리기 · 식물성 스테롤 도움")
    if tchol and 200 <= tchol <= 239:
        add_guide(guides, "총콜레스테롤 경계역(200~239): 위 생활수칙을 참고하여 식습관 개선 권고")

    # (선택) HDL/LDL 세분화 기준은 입력 시 확장 가능
    try:
        hdl_val = float(hdl) if hdl else None
    except:
        hdl_val = None
    try:
        ldl_val = float(ldl) if ldl else None
    except:
        ldl_val = None

    if hdl_val is not None and hdl_val < 40:
        add_guide(guides, "HDL 낮음(<40): 규칙적 유산소·체중조절·채소/통곡물·견과류·생선 섭취 권장")
    if ldl_val is not None and ldl_val >= 160:
        add_guide(guides, "LDL 높음(≥160): 포화지방 제한·식이섬유/식물성 스테롤·등푸른생선 권장")

    # 해석 생성 버튼 (복구)
    line()
    make_interp = st.button("🧠 해석하기 / 결과 생성", use_container_width=True)

    if make_interp:
        # 화면 표시
        if guides:
            st.success("가이드가 생성되었습니다. 아래 요약과 다운로드를 확인하세요.")
            for g in guides:
                st.markdown(f"- {{g}}")
        else:
            st.info("특이 소견에 따른 가이드가 없습니다. 그래도 균형 잡힌 식사와 위생 수칙을 지켜주세요.")

        # 요약 텍스트 생성
        order_vals = {{}}  # 자리표시자(ORDER 20 전체는 기존 앱에서 채움)
        meta = {{"nick": nick or "", "pin": pin or ""}}
        md_text = build_summary_text(basic_vals, order_vals, urine_vals, lipid_vals, guides, meta)

        # 다운로드 버튼 (복구)
        st.write("---")
        st.subheader("📥 결과 다운로드")
        colD1, colD2, colD3 = st.columns(3)
        with colD1:
            st.download_button("MD 받기", data=bytes_for_md(md_text), file_name="bloodmap_result.md", mime="text/markdown", use_container_width=True)
        with colD2:
            st.download_button("TXT 받기", data=bytes_for_txt(md_text), file_name="bloodmap_result.txt", mime="text/plain", use_container_width=True)
        with colD3:
            try:
                pdf_bytes = bytes_for_pdf(md_text)
                st.download_button("PDF 받기", data=pdf_bytes, file_name="bloodmap_result.pdf", mime="application/pdf", use_container_width=True)
            except Exception as e:
                st.warning("PDF 생성 중 문제가 발생했습니다. MD/TXT 파일을 사용해주세요.")

    st.markdown('<p class="small-muted">© 피수치 가이드 · 참고용. 모든 의학적 판단은 의료진에게.</p>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
