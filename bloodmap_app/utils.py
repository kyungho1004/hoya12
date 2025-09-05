# -*- coding: utf-8 -*-
import io, re, json, datetime
from typing import Dict, Any, List, Tuple

PIN_RE = re.compile(r"^\d{4}$")

def is_valid_pin(pin: str) -> bool:
    return bool(PIN_RE.match(str(pin or "").strip()))

def key_from(alias: str, pin: str) -> str:
    alias = (alias or "").strip()
    pin = (pin or "").strip()
    return f"{alias}#{pin}" if alias and pin else ""

def compute_acr(albumin_mg_L: float, urine_cr_mg_dL: float) -> float:
    """
    ACR (mg/g) = (urine albumin mg/L) / (urine creatinine g/L)
               = (Alb mg/L) / (Cr mg/dL * 0.01)
               = (Alb / Cr) * 100
    """
    if albumin_mg_L is None or urine_cr_mg_dL is None or urine_cr_mg_dL == 0:
        return 0.0
    return (albumin_mg_L / urine_cr_mg_dL) * 100.0

def compute_upcr(protein_mg_dL: float, urine_cr_mg_dL: float) -> float:
    """
    UPCR (mg/g) = (urine protein mg/dL -> mg/L *10) / (urine creatinine g/L)
                = (Prot mg/dL * 10) / (Cr mg/dL * 0.01)
                = (Prot/Cr) * 1000
    """
    if protein_mg_dL is None or urine_cr_mg_dL is None or urine_cr_mg_dL == 0:
        return 0.0
    return (protein_mg_dL / urine_cr_mg_dL) * 1000.0

def interpret_acr(acr: float) -> str:
    if acr <= 0:
        return "ACR: 입력값이 부족합니다."
    if acr < 30:
        return "ACR < 30 mg/g: 정상 범위"
    if acr <= 300:
        return "ACR 30~300 mg/g: 미세알부민뇨(주의)"
    return "ACR > 300 mg/g: 알부민뇨(의료진 상담 권장)"

def interpret_upcr(upcr: float) -> str:
    if upcr <= 0:
        return "UPCR: 입력값이 부족합니다."
    if upcr < 150:
        return "UPCR < 150 mg/g: 정상~경미"
    if upcr <= 500:
        return "UPCR 150~500 mg/g: 단백뇨(주의)"
    return "UPCR > 500 mg/g: 고단백뇨(의료진 상담 권장)"

def anc_banner(anc: float) -> str:
    if anc is None or anc == 0:
        return ""
    if anc < 500:
        return "⚠️ 호중구(ANC) 500 미만: 외출 자제·익힌 음식·멸균 식품 권장. 조리 후 2시간 지난 음식 섭취 금지."
    if anc < 1000:
        return "⚠️ 호중구(ANC) 500~999: 감염 주의, 신선 채소는 세척·가열 후 섭취 권장."
    return "✅ 호중구(ANC) 1000 이상: 비교적 안정. 위생 관리 유지."

def pediatric_guides(values: Dict[str, Any], group: str) -> List[str]:
    msgs: List[str] = []
    anc = float(values.get("ANC") or 0)
    if anc:
        msgs.append(anc_banner(anc))
    # Add group-specific tips
    if group in ("소아-일상", "소아-감염", "소아-혈액암", "소아-고형암", "소아-육종", "소아-희귀암"):
        msgs += [
            "🍼 소아 공통: 해열제는 정해진 용량/간격 준수. 증상 지속/악화 시 의료진과 상의.",
            "🍽️ 음식: 생채소 금지, 모든 음식은 충분히 가열(전자레인지 30초 이상). 껍질 과일은 담당의와 상담.",
            "🥡 보관: 조리 후 2시간 경과 음식 재섭취 금지.",
        ]
    return msgs

def build_report_md(meta: Dict[str, Any], values: Dict[str, Any], derived: Dict[str, Any], guides: List[str]) -> str:
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = []
    lines.append(f"# 피수치 가이드 결과 ({now})")
    lines.append("")
    lines.append(f"- 사용자: **{meta.get('user_key','-')}**")
    lines.append(f"- 진단: {meta.get('diagnosis','-')}")
    lines.append(f"- 카테고리: {meta.get('category','-')}")
    lines.append("")
    lines.append("## 입력 수치")
    for k, v in values.items():
        if v is None or v == "":
            continue
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## 자동 계산")
    for k, v in derived.items():
        lines.append(f"- {k}: {v}")
    if guides:
        lines.append("")
        lines.append("## 소아/케어 가이드")
        for g in guides:
            lines.append(f"- {g}")
    lines.append("")
    lines.append(f"---\n제작: Hoya/GPT · 자문: Hoya/GPT · 한국시간 기준")
    return "\n".join(lines)

def build_report_txt(md: str) -> str:
    # Simple txt fallback: strip markdown hashes
    text = md.replace("#", "").replace("**", "")
    return text

def build_report_pdf_bytes(md: str) -> bytes:
    # Very lightweight PDF using reportlab (no Korean font registration here)
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import mm
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        y = height - 15*mm
        for line in md.splitlines():
            if y < 20*mm:
                c.showPage()
                y = height - 15*mm
            c.drawString(15*mm, y, line.encode('utf-8','ignore').decode('utf-8','ignore'))
            y -= 6*mm
        c.showPage()
        c.save()
        pdf = buffer.getvalue()
        buffer.close()
        return pdf
    except Exception as e:
        # On failure, return a placeholder PDF that explains missing fonts
        return f"PDF 생성 실패: {e}".encode("utf-8")
