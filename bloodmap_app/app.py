
# -*- coding: utf-8 -*-
import streamlit as st
from dataclasses import dataclass
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

APP_TITLE = "🩸 피수치 가이드 / BloodMap"
APP_SIGNATURE = "제작: Hoya/GPT · 자문: Hoya/GPT"

# ---- Cancer dictionaries (code -> Korean) ----
HEMATO_KO = {
    "AML": "급성골수성백혈병",
    "APL": "급성전골수구백혈병",
    "ALL": "급성림프모구백혈병",
    "CML": "만성골수성백혈병",
    "CLL": "만성림프구성백혈병",
}
SARCOMA_KO = {
    "Ewing": "유잉육종",
    "Osteosarcoma": "골육종",
    "Synovial": "활막육종",
    "Leiomyosarcoma": "평활근육종",
    "Liposarcoma": "지방육종",
    "Rhabdomyosarcoma": "횡문근육종",
}
SOLID_KO = {
    "Lung": "폐암",
    "Breast": "유방암",
    "Colon": "대장암",
    "Stomach": "위암",
    "Liver": "간암",
    "Pancreas": "췌장암",
    "Cholangiocarcinoma": "담관암",
}

# Options list (code, label)
HEMATO_OPTS = [(k, f"{k} ({v})") for k, v in HEMATO_KO.items()]
SARCOMA_OPTS = [(k, f"{k} ({v})") for k, v in SARCOMA_KO.items()]
SOLID_OPTS = [(k, f"{k} ({v})") for k, v in SOLID_KO.items()]

# 항암제(한글 병기) 기본 제안
CHEMO_BY_DX: Dict[str, List[str]] = {
    "AML": ["아라씨(ARA-C, Cytarabine)","도우노루비신(Daunorubicin)","에토포사이드(Etoposide)"],
    "APL": ["아트라(ATRA, 트레티노인)","아산화비소(ATO)","MTX(메토트렉세이트)","6-MP(6-머캅토퓨린)"],
    "ALL": ["빈크리스틴(Vincristine)","사이클로포스파마이드(Cyclophosphamide)","MTX(메토트렉세이트)"],
    "CML": ["이마티닙(Imatinib)"],
    "CLL": ["플루다라빈(Fludarabine)"],
}
CHEMO_COMMON = ["그라신(G-CSF)","하이드록시우레아(Hydroxyurea)","미토잔트론(Mitoxantrone)","토포테칸(Topotecan)"]

ANTIBIOTICS_COMMON = ["세프트리악손(ceftriaxone)","피페/타조(piperacillin/tazobactam)","메로페넴(meropenem)","레보플록사신(levofloxacin)"]

# 식이가이드 5개 고정 + 확장
DIET_GUIDES = {
    "Albumin_low": ["달걀","연두부","흰살 생선","닭가슴살","귀리죽"],
    "K_low":       ["바나나","감자","호박죽","고구마","오렌지"],
    "Hb_low":      ["소고기","시금치","두부","달걀 노른자","렌틸콩"],
    "Na_low":      ["전해질 음료","미역국","바나나","오트밀죽","삶은 감자"],
    "Ca_low":      ["연어통조림","두부","케일","브로콜리","(참깨 제외)"],
    # 확장
    "Glucose_high": ["현미밥(소량)","삶은 달걀","두부샐러드(익힌 채소)","사과 반 조각(껍질 제거)","오트밀죽"],
    "Liver_high":   ["흰살생선","두부","채소볶음(기름 적게)","쌀죽/미음","무가당 요거트(소량)"],
}
NEUTROPENIA_FOOD_SAFETY = [
    "생채소 금지, 충분히 익혀서 섭취",
    "남은 음식은 2시간 이후 섭취하지 않기",
    "멸균/살균 제품 권장",
    "껍질 있는 과일은 주치의와 상담 후 결정",
]

# ========= Dose helpers (ml 단일 표기) =========
def _parse_conc_to_mg_per_ml(conc_label: str) -> Optional[float]:
    try:
        c = conc_label.replace("mL","ml").replace("ML","ml")
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

# ========= Export helpers =========
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
                c.drawString(left, y, line); y -= 14
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

    c.save(); buffer.seek(0)
    return buffer.getvalue()

# ========= Models =========
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

@dataclass
class Peds:
    appetite: Optional[str] = None
    fever_now: Optional[bool] = None
    temp_c: Optional[float] = None
    cough: Optional[str] = None
    dyspnea: Optional[str] = None
    cyanosis: Optional[bool] = None
    spo2: Optional[float] = None
    rsv: Optional[bool] = None
    adeno: Optional[bool] = None
    rota: Optional[bool] = None
    influenza: Optional[bool] = None
    parainfluenza: Optional[bool] = None
    hfm: Optional[bool] = None
    noro: Optional[bool] = None
    mycoplasma: Optional[bool] = None

# ========= Interpretation =========
def interpret_labs(labs: Labs) -> List[Tuple[str, List[str]]]:
    sections: List[Tuple[str, List[str]]] = []

    # Summary
    summary = []
    for key, label in [
        ("wbc","WBC(백혈구)"),("hb","Hb(헤모글로빈)"),("plt","PLT(혈소판)"),("anc","ANC(호중구)"),
        ("ca","Ca(칼슘)"),("na","Na(나트륨)"),("k","K(칼륨)"),("albumin","Albumin(알부민)"),
        ("glucose","Glucose(혈당)"),("ast","AST"),("alt","ALT"),("crp","CRP"),
        ("cr","Cr(크레아티닌)"),("bun","BUN(요소질소)"),("tb","TB(총빌리루빈)"),("ua","UA(요산)"),
    ]:
        v = getattr(labs, key)
        if v is not None and v != 0:
            summary.append(f"{label}: {v}")
    if summary:
        sections.append(("검사 요약", summary))

    # Diet guides
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
    if labs.glucose is not None and labs.glucose >= 180:
        diet_lines.append("혈당 높음 → 권장 식품: " + ", ".join(DIET_GUIDES["Glucose_high"]))
    if ((labs.ast is not None and labs.ast > 40) or (labs.alt is not None and labs.alt > 40)):
        diet_lines.append("간수치 상승(AST/ALT) → 권장 식품: " + ", ".join(DIET_GUIDES["Liver_high"]))

    if labs.anc is not None and labs.anc < 500:
        diet_lines = ["[호중구 낮음 — 위생/조리 안전 수칙]"] + [f"- {rule}" for rule in NEUTROPENIA_FOOD_SAFETY] + [""] + diet_lines

    if diet_lines:
        sections.append(("식이가이드", diet_lines))

    return sections

def interpret_peds(p: Peds) -> List[Tuple[str, List[str]]]:
    lines: List[str] = []
    alerts: List[str] = []
    tips: List[str] = []

    # Vital-based rules
    if p.temp_c is not None and p.temp_c >= 39.0:
        alerts.append("체온 39.0℃ 이상 → 즉시 병원 연락/내원 권고")
    elif p.temp_c is not None and p.temp_c >= 38.5:
        lines.append("체온 38.5℃ 이상 → 해열제 고려, 경과관찰 + 수분")
    elif p.temp_c is not None and p.temp_c >= 38.0:
        lines.append("체온 38.0℃대 → 해열제 고려, 경과관찰")

    if p.spo2 is not None and p.spo2 < 94:
        alerts.append(f"SpO₂ {p.spo2}% (<94%) → 응급 평가 권고")
    if p.cyanosis:
        alerts.append("청색증(입술/손발) → 응급 평가 권고")
    if p.dyspnea in ["많이","심함"]:
        alerts.append(f"호흡곤란 {p.dyspnea} → 응급 평가 고려")

    # Symptoms
    if p.cough in ["보통","많이","심함"]:
        tips.append("기침 심하면 실내 가습/수분, 휴식 · 악화 시 진료")
    if p.appetite == "없음":
        tips.append("식욕 없음 → 소량·자주 수분/죽 위주, 탈수 주의")

    # Infections
    infomap = [
        ("RSV", p.rsv, "영아/소아에서 천명·호흡곤란 주의"),
        ("아데노", p.adeno, "결막염/고열 가능, 수분/해열"),
        ("로타", p.rota, "구토·설사 → 탈수 모니터"),
        ("인플루엔자", p.influenza, "고열·근육통, 48h 이내 항바이러스 고려"),
        ("파라인플루엔자", p.parainfluenza, "크룹(개짖는기침) 가능"),
        ("수족구", p.hfm, "구내염 통증 관리·수분"),
        ("노로", p.noro, "급성 구토·설사 → 위생/격리"),
        ("마이코플라즈마", p.mycoplasma, "기침 지속·비전형 폐렴 가능"),
    ]
    sel = [name for name, flag, _ in infomap if flag]
    if sel:
        lines.append("추정 감염: " + ", ".join(sel))
        for name, flag, note in infomap:
            if flag:
                tips.append(f"{name}: {note}")

    sections: List[Tuple[str, List[str]]] = []
    if alerts:
        sections.append(("소아 — 응급 신호", [f"- {a}" for a in alerts]))
    info_lines = []
    if lines:
        info_lines += [f"- {x}" for x in lines]
    if tips:
        info_lines += [f"- {x}" for x in tips]
    if info_lines:
        sections.append(("소아 — 일상/호흡기/감염 가이드", info_lines))
    return sections

# ========= UI =========
def main():
    st.set_page_config(page_title="피수치 가이드 / BloodMap", layout="centered")

    # --- Hide +/- buttons on number_input (and native spinners) ---
    st.markdown(
        '''<style>
        [data-testid="stNumberInput"] button {display:none !important;}
        /* Hide native spin buttons */
        input[type=number]::-webkit-outer-spin-button,
        input[type=number]::-webkit-inner-spin-button { -webkit-appearance: none; margin: 0; }
        input[type=number] { -moz-appearance: textfield; }
        </style>''',
        unsafe_allow_html=True
    )
    st.title(APP_TITLE)
    st.caption(APP_SIGNATURE)

    # Nickname + PIN
    col1, col2 = st.columns([2,1])
    nickname = col1.text_input("별명", placeholder="예: 보호자A")
    pin = col2.text_input("PIN 4자리", max_chars=4, placeholder="0000")
    if pin and not pin.isdigit():
        st.warning("PIN은 숫자 4자리로 입력해주세요.")
    key_id = f"{nickname}#{pin}" if nickname and pin and pin.isdigit() and len(pin)==4 else None

    # ---- Toggles: 소아일상 / 소아감염 / 암종류 ----
    st.divider()
    st.subheader("토글 선택")
    t_peds_daily = st.checkbox("소아 — 일상/호흡기")
    t_peds_inf   = st.checkbox("소아 — 감염")
    t_cancer     = st.checkbox("암 종류")

    # 1) 소아 — 일상/호흡기 (toggle)
    if t_peds_daily:
        st.markdown("### 소아 — 일상/호흡기")
        g1, g2, g3 = st.columns(3)
        with g1:
            appetite = st.selectbox("식욕", ["모름","있음","없음"], index=0, key="pd_appetite")
            fever_now = st.checkbox("발열 있음", key="pd_fever")
            temp_c = st.number_input("체온(℃)", min_value=0.0, step=0.1, format="%.1f", key="pd_temp")
        with g2:
            cough = st.selectbox("기침", ["안함","조금","보통","많이","심함"], index=0, key="pd_cough")
            dyspnea = st.selectbox("호흡곤란", ["없음","조금","보통","많이","심함"], index=0, key="pd_dyspnea")
            cyanosis = st.checkbox("청색증", key="pd_cyanosis")
        with g3:
            has_pulseox = st.checkbox("산소포화도 측정기 있음", key="pd_haspo")
            spo2 = st.number_input("SpO₂(%)", min_value=0.0, max_value=100.0, step=0.1, format="%.1f", key="pd_spo2") if has_pulseox else None
        with st.expander("소아 해열제 빠른 계산 (중앙값, ml 단일 표기)"):
            pc1, pc2, pc3 = st.columns([1,1,2])
            with pc1:
                wt = st.number_input("체중(kg)", min_value=0.0, step=0.1, format="%.1f", key="wt_calc")
            with pc2:
                acet_conc = st.selectbox("아세트아미노펜 농도", ["160 mg/5 ml","120 mg/5 ml"], key="acet_calc")
                ibu_conc  = st.selectbox("이부프로펜 농도", ["100 mg/5 ml"], key="ibu_calc")
            with pc3:
                if (locals().get("wt", 0) or 0) > 0:
                    ml_acet = dose_ml_acetaminophen(wt, acet_conc)
                    ml_ibu  = dose_ml_ibuprofen(wt, ibu_conc)
                    if ml_acet is not None:
                        st.info(f"아세트아미노펜 권장 1회: **{ml_acet:.1f} ml**  (간격 4–6시간, 하루 최대 5회)")
                    if ml_ibu is not None:
                        st.info(f"이부프로펜 권장 1회: **{ml_ibu:.1f} ml**  (간격 6–8시간)")
    else:
        appetite = fever_now = temp_c = cough = dyspnea = cyanosis = has_pulseox = spo2 = None

    # 2) 소아 — 감염 (toggle)
    if t_peds_inf:
        st.markdown("### 소아 — 감염 의심(체크)")
        rsv = st.checkbox("RSV", key="pi_rsv")
        adeno = st.checkbox("아데노", key="pi_adeno")
        rota = st.checkbox("로타", key="pi_rota")
        influenza = st.checkbox("인플루엔자", key="pi_infl")
        parainfluenza = st.checkbox("파라인플루엔자", key="pi_parainfl")
        hfm = st.checkbox("수족구", key="pi_hfm")
        noro = st.checkbox("노로", key="pi_noro")
        mycoplasma = st.checkbox("마이코플라즈마", key="pi_mycop")
    else:
        rsv = adeno = rota = influenza = parainfluenza = hfm = noro = mycoplasma = None

    # 3) 암 종류 (toggle)
    if t_cancer:
        st.markdown("### 암 종류")
        grp = st.selectbox("암 그룹", ["혈액암", "육종(진단명 분리)", "고형암(기타)"])
        if grp == "혈액암":
            code, label = st.selectbox("진단명", HEMATO_OPTS, format_func=lambda x: x[1])
        elif grp == "육종(진단명 분리)":
            code, label = st.selectbox("육종 세부", SARCOMA_OPTS, format_func=lambda x: x[1])
        else:
            code, label = st.selectbox("고형암", SOLID_OPTS, format_func=lambda x: x[1])
        dx = code
    else:
        dx = None

    
    # ---- 약물 선택 ----
    st.divider()
    if t_peds_daily or t_peds_inf:
        st.subheader("소아 — 항생제")
        sel_abx = st.multiselect("항생제(한글 병기)", ANTIBIOTICS_COMMON, default=[], key="abx_sel")
        sel_chemo = []
    else:
        st.subheader("항암제 / 항생제")
        default_chemo = CHEMO_BY_DX.get(dx or "AML", [])
        st.caption("암종에 맞는 항암제 목록이 보이지만 **자동 선택은 하지 않습니다. 직접 선택하세요.**")
        sel_chemo = st.multiselect("항암제(한글 병기)", default_chemo + CHEMO_COMMON, default=[], key="chemo_sel")
        sel_abx   = st.multiselect("항생제(한글 병기)", ANTIBIOTICS_COMMON, default=[], key="abx_sel")
    
    # 3) 피수치 (toggle; pediatric on → default collapsed)
    st.divider()
    default_labs_open = not (t_peds_daily or t_peds_inf)
    t_labs = st.checkbox("피수치 입력 열기", value=default_labs_open)
 (toggle; pediatric on → default collapsed) ----
    st.divider()
    default_labs_open = not (t_peds_daily or t_peds_inf)
    t_labs = st.checkbox("피수치 입력 열기", value=default_labs_open)
    if t_labs:
        st.markdown("### 피수치")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            wbc = st.number_input("WBC(백혈구)", min_value=0.0, step=0.1, format="%.1f")
            hb = st.number_input("Hb(헤모글로빈)", min_value=0.0, step=0.1, format="%.1f")
            plt = st.number_input("PLT(혈소판)", min_value=0.0, step=1.0, format="%.0f")
            anc = st.number_input("ANC(호중구)", min_value=0.0, step=10.0, format="%.0f")
            ca = st.number_input("Ca(칼슘)", min_value=0.0, step=0.1, format="%.1f")
        with c2:
            p = st.number_input("P(인)", min_value=0.0, step=0.1, format="%.1f")
            na = st.number_input("Na(나트륨)", min_value=0.0, step=0.5, format="%.1f")
            k = st.number_input("K(칼륨)", min_value=0.0, step=0.1, format="%.1f")
            albumin = st.number_input("Albumin(알부민)", min_value=0.0, step=0.1, format="%.1f")
            glucose = st.number_input("Glucose(혈당)", min_value=0.0, step=1.0, format="%.0f")
        with c3:
            tp = st.number_input("Total Protein(총단백)", min_value=0.0, step=0.1, format="%.1f")
            ast = st.number_input("AST", min_value=0.0, step=1.0, format="%.0f")
            alt = st.number_input("ALT", min_value=0.0, step=1.0, format="%.0f")
            ldh = st.number_input("LDH", min_value=0.0, step=1.0, format="%.0f")
            crp = st.number_input("CRP(C-반응단백)", min_value=0.0, step=0.1, format="%.1f")
        with c4:
            cr = st.number_input("Cr(크레아티닌)", min_value=0.0, step=0.01, format="%.2f")
            ua = st.number_input("UA(요산)", min_value=0.0, step=0.1, format="%.1f")
            tb = st.number_input("TB(총빌리루빈)", min_value=0.0, step=0.1, format="%.1f")
            bun = st.number_input("BUN(요소질소)", min_value=0.0, step=0.1, format="%.1f")
            bnp = st.number_input("BNP(선택)", min_value=0.0, step=1.0, format="%.0f")
    else:
        wbc=hb=plt=anc=ca=p=na=k=albumin=glucose=tp=ast=alt=ldh=crp=cr=ua=tb=bun=bnp=None

    # ---- 특수검사 (toggle) ----
    st.divider()
    t_special = st.checkbox("특수검사 입력 열기")
    if t_special:
        st.markdown("### 특수검사 (토글)")
        t1, t2, t3, t4, t5 = st.columns(5)
        with t1: tg_c = st.checkbox("보체")
        with t2: tg_u = st.checkbox("요검사/단백뇨")
        with t3: tg_coag = st.checkbox("응고")
        with t4: tg_lip = st.checkbox("지질")
        with t5: tg_etc = st.checkbox("기타")

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
            c1_, c2_, c3_ = st.columns(3)
            PT  = c1_.number_input("PT(sec)",   min_value=0.0, step=0.1, format="%.1f")
            INR = c2_.number_input("INR",       min_value=0.0, step=0.01, format="%.2f")
            aPTT= c3_.number_input("aPTT(sec)", min_value=0.0, step=0.1, format="%.1f")

        if tg_lip:
            st.markdown("**지질/혈당대사**")
            l1, l2, l3 = st.columns(3)
            chol = l1.number_input("총콜레스테롤", min_value=0.0, step=1.0, format="%.0f")
            hdl  = l2.number_input("HDL", min_value=0.0, step=1.0, format="%.0f")
            tg   = l3.number_input("Triglyceride", min_value=0.0, step=1.0, format="%.0f")

        if tg_etc:
            st.markdown("**기타**")
            e1, e2, e3 = st.columns(3)
            tsh     = e1.number_input("TSH", min_value=0.0, step=0.01, format="%.2f")
            pct     = e2.number_input("Procalcitonin", min_value=0.0, step=0.01, format="%.2f")
            lactate = e3.number_input("Lactate", min_value=0.0, step=0.1, format="%.1f")

    # ---- 해석하기 ----
    st.divider()
    go = st.button("🔎 해석하기", type="primary", use_container_width=True)

    if go:
        # Pediatric collect
        peds = Peds(
            appetite=appetite if (t_peds_daily and appetite!="모름") else None,
            fever_now=bool(fever_now) if t_peds_daily else None,
            temp_c=temp_c if (t_peds_daily and (temp_c or 0)>0) else None,
            cough=cough if t_peds_daily else None,
            dyspnea=dyspnea if t_peds_daily else None,
            cyanosis=bool(cyanosis) if t_peds_daily else None,
            spo2=spo2 if (t_peds_daily and (spo2 is not None) and spo2 > 0) else None,
            rsv=rsv if t_peds_inf else None,
            adeno=adeno if t_peds_inf else None,
            rota=rota if t_peds_inf else None,
            influenza=influenza if t_peds_inf else None,
            parainfluenza=parainfluenza if t_peds_inf else None,
            hfm=hfm if t_peds_inf else None,
            noro=noro if t_peds_inf else None,
            mycoplasma=mycoplasma if t_peds_inf else None,
        )

        # Labs collect
        labs = Labs(
            wbc=wbc or None, hb=hb or None, plt=plt or None, anc=anc or None,
            ca=ca or None, p=p or None, na=na or None, k=k or None, albumin=albumin or None,
            glucose=glucose or None, tp=tp or None, ast=ast or None, alt=alt or None,
            ldh=ldh or None, crp=crp or None, cr=cr or None, ua=ua or None, tb=tb or None,
            bun=bun or None, bnp=bnp or None
        ) if t_labs else Labs()

        sections: List[Tuple[str, List[str]]] = []

        # 확장된 항암제 경고
        warn = []
        for d in (sel_chemo or []):
            if "MTX" in d:
                warn += ["[MTX] 간독성↑, 골수억제, 구내염, 신기능 영향 — 엽산 보충은 반드시 의료진 지시에 따라"]
            if "6-MP" in d:
                warn += ["[6-MP] 간독성/골수억제 — 황달·발열·멍 주의, 상호작용(알로푸리놀)"]
            if "ARA-C" in d or "Cytarabine" in d:
                warn += ["[ARA-C] 고용량 시 소뇌실조/시력·결막염 — 점안 스테로이드 고려, 신경증상 즉시 보고"]
            if "Daunorubicin" in d or "미토잔트론" in d:
                warn += ["[Anthracycline/Mitoxantrone] 심독성(누적용량) — 호흡곤란/부종 시 진료"]
            if "Cyclophosphamide" in d:
                warn += ["[Cyclophosphamide] 출혈성 방광염 — 수분섭취/메스나, 혈뇨 시 즉시 보고"]
            if "Etoposide" in d:
                warn += ["[Etoposide] 저혈압/골수억제 — 어지러움·발열 시 주의"]
            if "Topotecan" in d:
                warn += ["[Topotecan] 심한 호중구감소/설사 — 발열·혈변 시 즉시 연락"]
            if "Fludarabine" in d:
                warn += ["[Fludarabine] 강한 면역억제 — 기회감염 예방/백신 상담"]
            if "G-CSF" in d:
                warn += ["[G-CSF] 골통증 흔함, 드물게 비장비대/파열 — 좌상복부 통증 즉시 진료"]
            if "Hydroxyurea" in d:
                warn += ["[Hydroxyurea] 골수억제/피부변화 — 상처치유 지연 주의"]
        if warn:
            sections.append(("약물 주의 요약(확장)", warn))

        # 소아/일상 해석이 최상단
        sections = interpret_peds(peds) + sections
        # Labs 해석 + 식이가이드
        sections += interpret_labs(labs)

        # 화면 표시
        st.success("해석 완료 — 아래 결과를 확인하세요.")
        for title, lines in sections:
            st.subheader(title)
            for ln in lines:
                st.markdown(f"{ln if ln.startswith('- ') else '- ' + ln}")

        # Export
        md_text = build_sections_md(sections)
        txt_text = build_txt(md_text)
        pdf_bytes = build_pdf(md_text) if PDF_AVAILABLE else None
        st.divider()
        st.write("📄 결과 저장")
        cdl1, cdl2 = st.columns(2)
        cdl1.download_button("TXT로 저장", data=txt_text.encode("utf-8"),
                             file_name="bloodmap_result.txt", mime="text/plain", use_container_width=True)
        if pdf_bytes is not None:
            cdl2.download_button("PDF로 저장", data=pdf_bytes,
                                 file_name="bloodmap_result.pdf", mime="application/pdf", use_container_width=True)
        else:
            cdl2.button("PDF 생성 불가 (reportlab 필요)", disabled=True, use_container_width=True)

if __name__ == "__main__":
    main()
