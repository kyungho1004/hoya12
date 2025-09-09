# -*- coding: utf-8 -*-
import io, re, json, datetime, os
from typing import Dict, Any, List, Tuple
PIN_RE = re.compile(r"^\d{4}$")
def is_valid_pin(pin: str) -> bool:
    return bool(PIN_RE.match(str(pin or "").strip()))
def key_from(alias: str, pin: str) -> str:
    alias = (alias or "").strip()
    pin = (pin or "").strip()
    return f"{alias}#{pin}" if alias and pin else ""
def compute_acr(albumin_mg_L: float, urine_cr_mg_dL: float) -> float:
    if albumin_mg_L is None or urine_cr_mg_dL is None or urine_cr_mg_dL == 0:
        return 0.0
    return (albumin_mg_L / urine_cr_mg_dL) * 100.0
def compute_upcr(protein_mg_dL: float, urine_cr_mg_dL: float) -> float:
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
def interpret_ast(val: float) -> str:
    if not val: return ""
    return "AST 상승(간/근육 손상 가능성)" if val > 80 else "AST: 뚜렷한 상승 없음."
def interpret_alt(val: float) -> str:
    if not val: return ""
    return "ALT 상승(간세포 손상 가능성)" if val > 80 else "ALT: 뚜렷한 상승 없음."
def interpret_na(val: float) -> str:
    if not val: return ""
    if val < 135: return "저나트륨혈증(135 미만) — 탈수/SIADH 등 평가."
    if val > 145: return "고나트륨혈증(145 초과) — 수분관리 필요."
    return "Na: 135~145 범위."
def interpret_k(val: float) -> str:
    if not val: return ""
    if val < 3.5: return "저칼륨혈증(3.5 미만)"
    if val > 5.5: return "고칼륨혈증(5.5 초과) — 심전도 확인 고려."
    return "K: 3.5~5.5 범위."
def interpret_ca(val: float) -> str:
    if not val: return ""
    if val < 8.5: return "저칼슘혈증(8.5 미만)"
    if val > 10.5: return "고칼슘혈증(10.5 초과)"
    return "Ca: 8.5~10.5 범위."
def pediatric_guides(values: Dict[str, Any], group: str, diagnosis: str = "") -> List[str]:
    msgs: List[str] = []
    anc = float(values.get("ANC") or 0)
    if anc:
        ab = anc_banner(anc)
        if ab: msgs.append(ab)
    if group.startswith("소아"):
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
    text = md.replace("#", "").replace("**", "")
    return text
def _register_kr_font(c):
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fonts"))
        candidates = ["NotoSansKR-Regular.ttf", "NanumGothic.ttf", "AppleSDGothicNeo.ttf"]
        for name in candidates:
            path = os.path.join(base_dir, name)
            if os.path.exists(path):
                pdfmetrics.registerFont(TTFont("KR", path))
                c.setFont("KR", 10)
                return True
    except Exception:
        pass
    return False
def build_report_pdf_bytes(md: str) -> bytes:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import mm
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        has_kr = _register_kr_font(c)
        if not has_kr:
            c.setFont("Helvetica", 10)
        width, height = A4
        y = height - 15*mm
        for raw in md.splitlines():
            if y < 20*mm:
                c.showPage()
                c.setFont("KR" if has_kr else "Helvetica", 10)
                y = height - 15*mm
            c.drawString(15*mm, y, raw)
            y -= 6*mm
        c.showPage()
        c.save()
        pdf = buffer.getvalue()
        buffer.close()
        return pdf
    except Exception as e:
        return f"PDF 생성 실패: {e}".encode("utf-8")
