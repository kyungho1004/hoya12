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

# --- Additional interpreters (simple, general-purpose) ---
def interpret_ferritin(val: float) -> str:
    if not val:
        return ""
    if val < 15:
        return "Ferritin: 15 ng/mL 미만 — 철결핍 가능성."
    if val > 500:
        return "Ferritin: 500 ng/mL 초과 — 염증/과부하 가능(맥락 고려)."
    return "Ferritin: 참고범위 내(맥락필요)."

def interpret_ldh(val: float) -> str:
    if not val:
        return ""
    if val > 480:
        return "LDH 상승 — 용혈/조직손상/종양활성 가능성."
    return "LDH: 뚜렷한 상승 없음."

def interpret_ua(val: float) -> str:
    if not val:
        return ""
    if val > 7.0:
        return "Uric acid 상승 — 종양용해증후군/통풍 위험 평가 필요."
    return "Uric acid: 특이소견 없음."

def interpret_esr(val: float) -> str:
    if not val:
        return ""
    if val > 40:
        return "ESR 상승 — 염증/감염/자면역 등 의심."
    return "ESR: 경미/정상."

def interpret_b2m(val: float) -> str:
    if not val:
        return ""
    if val > 3.0:
        return "β2-microglobulin 상승 — 예후/신기능 반영 가능."
    return "β2-microglobulin: 참고범위 내."

# --- LFT / Electrolyte / Coagulation simple interpreters ---
def interpret_ast(val: float) -> str:
    if not val: return ""
    return "AST 상승(간/근육 손상 가능성)" if val > 80 else "AST: 뚜렷한 상승 없음."

def interpret_alt(val: float) -> str:
    if not val: return ""
    return "ALT 상승(간세포 손상 가능성)" if val > 80 else "ALT: 뚜렷한 상승 없음."

def interpret_alp(val: float) -> str:
    if not val: return ""
    return "ALP 상승(담즙정체/골성장 등, 소아는 생리적 상승 가능)" if val > 350 else "ALP: 특이소견 없음."

def interpret_ggt(val: float) -> str:
    if not val: return ""
    return "GGT 상승(담즙정체/약물 영향 가능)" if val > 60 else "GGT: 특이소견 없음."

def interpret_tbili(val: float) -> str:
    if not val: return ""
    return "총빌리루빈 상승(황달/담도폐쇄/용혈 등 평가 필요)" if val > 2.0 else "총빌리루빈: 특이소견 없음."

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

def interpret_mg(val: float) -> str:
    if not val: return ""
    if val < 1.6: return "저마그네슘혈증(1.6 미만)"
    if val > 2.6: return "고마그네슘혈증(2.6 초과)"
    return "Mg: 1.6~2.6 범위."

def interpret_phos(val: float) -> str:
    if not val: return ""
    if val < 2.5: return "저인산혈증(2.5 미만)"
    if val > 4.5: return "고인산혈증(4.5 초과)"
    return "P: 2.5~4.5 범위."

def interpret_inr(val: float) -> str:
    if not val: return ""
    return "INR 상승(>1.3) — 출혈 위험 평가" if val > 1.3 else "INR: 1.0~1.3 범위."

def interpret_aptt(val: float) -> str:
    if not val: return ""
    return "aPTT 연장 — 응고인자/헤파린 영향 가능" if val > 40 else "aPTT: 대체로 정상."

def interpret_fibrinogen(val: float) -> str:
    if not val: return ""
    return "피브리노겐 저하(<150 mg/dL) — DIC/HLH 의심" if val < 150 else "피브리노겐: 심한 저하 없음."

def interpret_ddimer(val: float) -> str:
    if not val: return ""
    return "D-dimer 상승 — 혈전/염증/수술 후 등 여러 원인 가능" if val > 0.5 else "D-dimer: 낮음."

def interpret_tg(val: float) -> str:
    if not val: return ""
    return "중성지방 상승(>265 mg/dL) — HLH 기준 중 하나" if val > 265 else "중성지방: 특이소견 없음."

def interpret_lactate(val: float) -> str:
    if not val: return ""
    return "젖산 상승(>2 mmol/L) — 저관류/패혈증 등 평가" if val > 2.0 else "젖산: 정상 범위."

def pediatric_guides(values: Dict[str, Any], group: str, diagnosis: str = "") -> List[str]:
    msgs: List[str] = []
    anc = float(values.get("ANC") or 0)
    if anc:
        msgs.append(anc_banner(anc))
    # Group-level common tips
    if group in ("소아-일상", "소아-감염", "소아-혈액암", "소아-고형암", "소아-육종", "소아-희귀암"):
        msgs += [
            "🍼 소아 공통: 해열제는 정해진 용량/간격 준수. 증상 지속/악화 시 의료진과 상의.",
            "🍽️ 음식: 생채소 금지, 모든 음식은 충분히 가열(전자레인지 30초 이상). 껍질 과일은 담당의와 상담.",
            "🥡 보관: 조리 후 2시간 경과 음식 재섭취 금지.",
        ]
    # Diagnosis-specific enrichments (examples)
    d = (diagnosis or "").lower()
    if "all" in d:
        msgs += ["ALL: 유지요법(6-MP/MTX 등) 복용 누락 주의, 발열 시 즉시 보고."]
    if "aml" in d or "apl" in d:
        msgs += ["AML/APL: 점막출혈·멍 증가 시 항응고제/항혈소판제 임의 중단 금지, 의료진과 상의."]
    if "유잉" in d or "ewing" in d:
        msgs += ["유잉육종: VAC/IE 주기 중 발열중성구감염(FN) 교육 강화 필요.", "IE 주기 전후 수분섭취·신장기능 모니터."]
    if "골육종" in d or "osteosarcoma" in d:
        msgs += ["골육종: 고용량 MTX 시 수분·알칼리뇨, 류코보린 구조요법 스케줄 준수.", "시스플라틴 병용 시 이독성 관찰(청력 변화 시 보고)."]
    if "rhabdomyo" in d or "횡문근육종" in d:
        msgs += ["횡문근육종: 빈크리스틴 말초신경 증상(보행/감각) 체크, 변비 예방 교육."]
    if "hlh" in d:
        msgs += ["HLH: 발열 지속/의식저하 시 즉시 내원, ferritin/TG/피브리노겐 추적."]
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


# --- Pediatric infection quick interpreter ---
def interpret_ped_infection(paths, temp_c: float, fever_days: float, dehydration: str, resp_severity: str,
                            risk_neutro: bool=False, age_months: int=0) -> list:
    """
    paths: list of selected pathogens, e.g., ["Adenovirus","RSV"]
    dehydration: "-", "없음","경미","중등도","중증"
    resp_severity: "-", "경증","중등도","중증"
    """
    msgs = []
    P = set([p.lower() for p in paths])

    if risk_neutro:
        msgs.append("⚠️ 항암치료/호중구감소증 의심: 38.0℃ 이상 발열 시 즉시 내원(FN 규약).")

    if age_months and age_months < 3*12 and temp_c >= 38.0:
        msgs.append("⚠️ 영아(36개월 미만) 발열: 저연령 고위험군 — 의료기관 평가 권고.")

    # Generic by pathogen
    if "adenovirus" in P or "아데노" in P:
        msgs += ["아데노바이러스: 고열·인두염/결막염 가능. 해열·수분, 세균 2차감염 의심 시 진료."]
    if "rsv" in P:
        msgs += ["RSV: 세기관지염 — 수분, 비강흡인, 산소포화도 관찰. 호흡곤란/얼굴창백/무호흡 시 즉시 내원."]
    if "influenza" in P or "인플루엔자" in P or "flu" in P:
        msgs += ["인플루엔자: 증상 48시간 이내라면 항바이러스제 고려(고위험군 우선). 해열·수분, 합병증 주의."]
    if "parainfluenza" in P or "파라인플루엔자" in P or "크룹" in P:
        msgs += ["파라인플루엔자/크룹: 컹컹기침·흡기성 천명 시 응급실에서 스테로이드/네불라이저 고려."]
    if "rhinovirus" in P or "라이노" in P:
        msgs += ["라이노바이러스: 상기도감염 — 대증치료, 수분·비강세척."]
    if "metapneumovirus" in P or "메타뉴모" in P:
        msgs += ["hMPV: RSV 유사 — 저연령/기저질환 시 호흡부전 관찰."]
    if "norovirus" in P or "로타" in P or "rotavirus" in P:
        msgs += ["장관바이러스: 구토·설사 — 소량·자주 ORS, 탈수 징후 시 수액치료."]
    if "covid" in P or "sars-cov-2" in P or "코로나" in P:
        msgs += ["COVID-19: 고열·기침·인후통. 격리/등교 기준은 지역 지침 따르며, 고위험군 항바이러스 고려."]

    # Fever duration
    if fever_days and fever_days >= 5:
        msgs.append("발열 5일 이상 지속: 가와사키/다른 원인 감별 위해 진료 권고.")

    # Dehydration
    d = (dehydration or "").strip()
    if d in ("중등도","중증"):
        msgs.append("탈수 중등도 이상: ORS 실패 시 병원 수액치료 고려.")
    elif d == "경미":
        msgs.append("탈수 경미: 소량·자주 수분공급, 전해질 보충.")

    # Respiratory severity
    r = (resp_severity or "").strip()
    if r == "중증":
        msgs.append("호흡곤란(중증): 청색증·함몰호흡·무호흡 — 응급실 권고.")
    elif r == "중등도":
        msgs.append("호흡곤란(중등도): 호흡수 증가/함몰 — 의료기관 평가 권고.")

    # High temp
    if temp_c and temp_c >= 39.0:
        msgs.append("고열(≥39℃): 해열제(아세트아미노펜/이부프로펜) 교대 복용 가능 — 간·신장 병력 확인.")

    if not msgs:
        msgs.append("입력값이 부족합니다. 증상·체온·병원체를 선택하면 맞춤 안내가 나옵니다.")
    return msgs


def interpret_bnp(val: float) -> str:
    if not val:
        return ""
    # 간단 기준(성인 일반): >100 pg/mL 상승. 소아/연령별 상이할 수 있음.
    if val > 100:
        return "BNP 상승 — 심부전/심장 부담 가능성(연령·신장/수분상태 고려)."
    return "BNP: 뚜렷한 상승 없음."
