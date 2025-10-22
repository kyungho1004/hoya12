
from typing import Dict, Any

# ---------- Fallback Korean aliases (display only; DB alias 우선) ----------
ALIAS_FALLBACK: Dict[str,str] = {
    "5-FU": "5-플루오로우라실",
    "Capecitabine": "카페시타빈",
    "Ara-C": "시타라빈(Ara-C)",
    "Cytarabine": "시타라빈(Ara-C)",
    "Cyclophosphamide": "사이클로포스파마이드",
    "Doxorubicin": "독소루비신",
    "Etoposide": "에토포사이드",
    "Vincristine": "빈크리스틴",
    "Vinblastine": "빈블라스틴",
    "Docetaxel": "도세탁셀",
    "Paclitaxel": "파클리탁셀",
    "Carboplatin": "카보플라틴",
    "Cisplatin": "시스플라틴",
    "Oxaliplatin": "옥살리플라틴",
    "Pemetrexed": "페메트렉시드",
    "Irinotecan": "이리노테칸",
    "Gemcitabine": "젬시타빈",
    "Imatinib": "이마티닙",
    "Osimertinib": "오시머티닙",
    "Alectinib": "알렉티닙",
    "Crizotinib": "크리조티닙",
    "Lorlatinib": "로를라티닙",
    "Larotrectinib": "라로트렉티닙",
    "Entrectinib": "엔트렉티닙",
    "Capmatinib": "캡마티닙",
    "Sotorasib": "소토라십",
    "Trastuzumab": "트라스투주맙",
    "Pertuzumab": "퍼투주맙",
    "T-DM1": "트라스투주맙 엠탄신",
    "Trastuzumab deruxtecan": "트라스투주맙 데룩스테칸",
    "Tucatinib": "투카티닙",
    "Nivolumab": "니볼루맙",
    "Pembrolizumab": "펨브롤리주맙",
    "Bevacizumab": "베바시주맙",
    "Ramucirumab": "라무시루맙",
    "Regorafenib": "레고라페닙",
    "Ripretinib": "리프레티닙",
    "Vandetanib": "반데타닙",
    "Cabozantinib": "카보잔티닙",
    "Selpercatinib": "셀퍼카티닙",
    "Pralsetinib": "프랄세티닙",
    "Octreotide": "옥트레오타이드",
    "Everolimus": "에베로리무스",
    "Rituximab": "리툭시맙",
    "Brentuximab Vedotin": "브렌툭시맙 베도틴",
    "Polatuzumab Vedotin": "폴라투주맙 베도틴",
    "Prednisone": "프레드니손",
}

def display_label(key: str, db: Dict[str, Dict[str, Any]]|None=None) -> str:
    ref = db if isinstance(db, dict) else {}
    alias = ref.get(key, {}).get("alias") if ref else None
    if not alias:
        alias = ALIAS_FALLBACK.get(key)
    return f"{key} ({alias})" if alias and alias != key else str(key)

def picklist(keys, db=None):
    ref = db if isinstance(db, dict) else {}
    return [display_label(k, ref) for k in (keys or [])]

def key_from_label(label: str, db=None) -> str:
    if not label:
        return ""
    pos = label.find(" (")
    return label[:pos] if pos > 0 else label

def _upsert(db: Dict[str, Dict[str, Any]], key: str, alias: str, moa: str, ae: str):
    db.setdefault(key, {})
    db[key].update({"alias": alias, "moa": moa, "ae": ae})
    # 편의상 대소문자/한글표기도 키로 진입 가능하도록 미러
    for alt in {key, key.lower(), alias, alias.lower()}:
        db.setdefault(alt, {"alias": alias, "moa": moa, "ae": ae})

# 상세 부작용 프로파일(핵심 이모지 포함)
PROFILES: Dict[str, Dict[str, Any]] = {
    "Imatinib": {"moa": "TKI (BCR‑ABL, KIT)", "ae": "💧 부종 · 🥵 피로 · 🩸 골수억제 · 속쓰림/구역"},
    "5-FU": {"moa": "피리미딘 유사체(항대사제)", "ae": "🩸 골수억제 · 🤢 오심/구토 · 💩 설사 · 💊 구내염 · 🖐️ 손발증후군"},
    "Capecitabine": {"moa": "5‑FU 전구약물(항대사제)", "ae": "🖐️ 손발증후군 · 💩 설사 · 💊 구내염 · 🩸 골수억제"},
    "Doxorubicin": {"moa": "안트라사이클린(Topo II 억제)", "ae": "❤️ 심근독성(누적) · 🩸 골수억제 · 💊 점막염"},
    "Cyclophosphamide": {"moa": "알킬화제", "ae": "🩸 골수억제 · 🩸 혈뇨/방광염(고용량) · 🤢 오심/구토"},
    "Etoposide": {"moa": "Topo II 억제", "ae": "🩸 골수억제 · 🤢 오심/구토"},
    "Vincristine": {"moa": "Vinca 알칼로이드", "ae": "🧠 말초신경병증 · 변비 · 턱통증"},
    "Paclitaxel": {"moa": "탁산", "ae": "🧠 말초신경병증 · 🩸 골수억제 · 🤧 과민반응"},
    "Osimertinib": {"moa": "EGFR TKI", "ae": "💩 설사 · 발진 · 🫁 ILD 드묾"},
    "Alectinib": {"moa": "ALK TKI", "ae": "근육통 · 변비 · 🧪 간효소 상승"},
    "Capmatinib": {"moa": "MET TKI", "ae": "💧 말초부종 · 🧪 간효소 상승"},
    "Trastuzumab": {"moa": "HER2 mAb", "ae": "❤️ 심기능저하(LVEF) · 주입반응"},
    "Pertuzumab": {"moa": "HER2 mAb", "ae": "설사 · ❤️ LVEF 감소"},
    "T-DM1": {"moa": "HER2 ADC", "ae": "혈소판감소 · 간독성"},
    "Trastuzumab deruxtecan": {"moa": "HER2 ADC", "ae": "🫁 ILD/폐렴 · 🤢 오심"},
    "Nivolumab": {"moa": "PD‑1 억제제", "ae": "면역관련 이상반응(대장염/간염/피부/내분비)"},
    "Pembrolizumab": {"moa": "PD‑1 억제제", "ae": "면역관련 이상반응(대장염/간염/피부/내분비)"},
    "Bevacizumab": {"moa": "VEGF 억제", "ae": "🩸 출혈 · 고혈압 · 단백뇨 · 상처치유 지연"},
    "Ramucirumab": {"moa": "VEGFR‑2 억제", "ae": "🩸 출혈 · 고혈압 · 단백뇨"},
    "Regorafenib": {"moa": "멀티 TKI", "ae": "🖐️ 손발증후군 · 피로 · 고혈압"},
    "Ripretinib": {"moa": "KIT/PDGFRA 억제", "ae": "🧑‍🦲 탈모 · 피로 · 손발증후군"},
    "Everolimus": {"moa": "mTOR 억제", "ae": "🫁 ILD/폐렴 · 🩸 대사이상(혈당/지질) · 💊 구내염"},
    "Rituximab": {"moa": "CD20 항체", "ae": "💉 주입반응 · 감염위험 · HBV 재활성 경고"},
    "Octreotide": {"moa": "Somatostatin 유사체", "ae": "💩 지방변/설사 · 복부불편감 · 담석"},
    "Prednisone": {"moa": "코르티코스테로이드", "ae": "😠 기분변화 · 🍽️ 식욕↑/체중↑ · 혈당↑ · 불면"},
    "Cytarabine": {"moa": "시티딘 유사체(항대사제)", "ae": "🩸 골수억제 · 🤢 오심/구토 · 💊 구내염"},
    "Cytarabine IV": {"moa": "시티딘 유사체(정맥)", "ae": "🩸 골수억제 · 🤢 오심/구토 · 💊 구내염"},
    "Cytarabine SC": {"moa": "시티딘 유사체(피하)", "ae": "🩸 골수억제 · 주사부위 반응"},
    "Cytarabine (HDAC)": {"moa": "고용량 Ara-C", "ae": "🧠 소뇌독성/실조 · 👁️ 각결막염 · 🩸 골수억제"},
    "Cytarabine": {"moa": "", "ae": "🩸 골수억제(호중구↓/혈소판↓) · 🤢 오심/구토 · 💊 점막염/구내염 · 🌡️ 발열 · 🧠 드묾: 신경독성(특히 누적·신기능저하) · 👁️ 고용량 시 각결막염(점안 스테로이드로 예방)"},
    "Cytarabine IV": {"moa": "", "ae": "🩸 골수억제(호중구↓/혈소판↓) · 🤢 오심/구토 · 💊 점막염/구내염 · 🌡️ 발열 · 주사 관련 반응"},
    "Cytarabine SC": {"moa": "", "ae": "🩸 골수억제(경도~중등도) · 💉 주사부위 통증/홍반/경결 · 🤢 경미한 오심"},
    "Cytarabine (HDAC)": {"moa": "", "ae": "🧠 소뇌독성(운동실조/구음장애; 고령·신기능저하 위험↑) · 👁️ 각결막염/각막염(예방: 점안 스테로이드) · 🩸 심한 골수억제 · 🌡️ 발열 · 💊 점막염"},
    "Daunorubicin": {"moa": "", "ae": "❤️ 누적용량 의존 심근독성(LVEF↓/심부전) · 🩸 골수억제 · 💊 점막염/구내염 · 👄 탈모 · 🔥 정맥외 유출 시 조직괴사(중앙정맥 권장)"},
    "Idarubicin": {"moa": "", "ae": "❤️ 누적용량 의존 심근독성 · 🩸 골수억제 · 💊 점막염 · 👄 탈모 · 🔥 정맥외 유출 위험"},
    "ATRA": {"moa": "", "ae": "🫀 분화증후군(호흡곤란·발열·부종; 조기 스테로이드) · 🧴 피부/점막 건조 · 🧠 두통 · 🧪 지질↑ · 간효소↑ · 드묾: 가성뇌종양"},
    "Arsenic Trioxide": {"moa": "", "ae": "🫀 QT 연장(저K/저Mg 교정) · 🫁 분화증후군 · 🧪 간효소↑ · 🤢 오심/구토 · 드묾: 변비/말초신경병증"},
    "Osimertinib": {"moa": "", "ae": "💩 설사 · 🌋 발진/건성피부 · 🫁 간질성폐질환(드묾·호흡곤란 시 중단) · ❤️ QT 연장/심장기능 저하 가능"},
    "Alectinib": {"moa": "", "ae": "💪 근육통/CPK↑ · 🧪 간효소↑ · 변비/피로 · 드묾: 서맥"},
    "Imatinib": {"moa": "", "ae": "💧 말초부종 · 🩸 골수억제 · 소화불량/구역 · 근경련 · 피부발진"},
    "Trastuzumab": {"moa": "", "ae": "❤️ 심기능저하(LVEF↓; 안트라사이클린 병력 시 위험↑) · 주입반응 · 드묾: 폐독성"},
    "Pertuzumab": {"moa": "", "ae": "💩 설사 · ❤️ LVEF 감소(트라스투주맙 병용 시 모니터링) · 주입반응"},
    "T-DM1": {"moa": "", "ae": "🩸 혈소판↓ · 🧪 간효소↑/간독성 · 피로/오심 · 드묾: 간질성폐질환"},
    "Docetaxel": {"moa": "", "ae": "🩸 골수억제(호중구감소증) · 💧 체액저류/말초부종(스테로이드 전처치) · 🖐️ 손발증후군/손발톱 변화 · 🤢 오심 · 주입반응"},
    "Carboplatin": {"moa": "", "ae": "🩸 골수억제(혈소판↓) · 🤢 오심/구토 · 🧪 전해질 이상 · 드묾: 과민반응(누적 후)"},
    "Cetuximab": {"moa": "", "ae": "🧴 여드름양 발진(치료반응과 연관) · 🧪 저Mg혈증 · 주입반응 · 구강점막염"},
    "Leucovorin": {"moa": "", "ae": "🤢 오심/구토(경미) · 드묾: 과민반응 · (단독 독성 낮음; 5-FU 강화/MTX 구제)"},
    "L-asparaginase": {"moa": "", "ae": "🤧 과민반응/아나필락시스 · 🫛 췌장염 · 🫀 혈전/출혈 위험 · 🧪 간독성/효소↑ · 혈당↑/중성지방↑ · 드묾: 신경독성"},
    "Pegaspargase": {"moa": "", "ae": "🤧 과민반응(지연가능) · 🫛 췌장염 · 🫀 혈전/출혈 위험 · 🧪 간독성/효소↑ · 혈당↑/중성지방↑"},
    "MTX": {"moa": "", "ae": "💊 구내염/점막염 · 🧪 간효소↑ · 🩸 골수억제 · 💧 체액저류 · 신독성(고용량·산성뇨; 알칼리화/류코보린 구제)"},
    "6-MP": {"moa": "", "ae": "🩸 골수억제 · 🧪 간효소↑/간손상 · 발진/광과민 · TPMT/NUDT15 결핍 시 독성↑(용량감소)"},
}

PLACEHOLDER_AE = "부작용 정보 필요"

def ensure_onco_drug_db(db: Dict[str, Dict[str, Any]]):
    """패치 방식: 기존 ensure가 있으면 먼저 호출 → 부족분/자리표시 보강 → PROFILES로 오버레이."""
    # 1) 이전 레이어 보존 호출
    prev = globals().get('__prev_ensure_ref', None)
    if prev is None and 'ensure_onco_drug_db' in globals():
        # 첫 로드 시 기존 심볼 백업(자기 자신 가리키지 않게)
        pass
    # 2) 자리표시 일괄 등록(요청 목록 키)
    for key in [
        "5-FU","Alectinib","Ara-C","Bendamustine","Bevacizumab","Bleomycin","Brentuximab Vedotin",
        "Cabozantinib","Capecitabine","Capmatinib","Carboplatin","Chlorambucil","Cisplatin","Crizotinib",
        "Cyclophosphamide","Dacarbazine","Dactinomycin","Docetaxel","Doxorubicin","Entrectinib","Etoposide",
        "Everolimus","Gemcitabine","Ibrutinib","Ifosfamide","Imatinib","Irinotecan","Lapatinib","Larotrectinib",
        "Lorlatinib","Nivolumab","Obinutuzumab","Octreotide","Osimertinib","Oxaliplatin","Paclitaxel","Pazopanib",
        "Pembrolizumab","Pemetrexed","Pertuzumab","Polatuzumab Vedotin","Pralsetinib","Prednisone","Ramucirumab",
        "Regorafenib","Ripretinib","Rituximab","Selpercatinib","Sotorasib","Sunitinib","T-DM1","Trabectedin",
        "Trastuzumab","Trastuzumab deruxtecan","Tucatinib","Vandetanib","Vinblastine","Vincristine"
    ]:
        alias = ALIAS_FALLBACK.get(key, key)
        _upsert(db, key, alias, "항암/표적치료(자동등록)", PLACEHOLDER_AE)
    # 3) PROFILES로 상세 덮어쓰기
    for key, prof in PROFILES.items():
        alias = ALIAS_FALLBACK.get(key, key)
        _upsert(db, key, alias, prof.get("moa",""), prof.get("ae",""))
    # 4) 동의어 보완
    if "Ara-C" in db and "Cytarabine" not in db:
        entry = db["Ara-C"]
        _upsert(db, "Cytarabine", entry.get("alias","시타라빈(Ara-C)"), entry.get("moa",""), entry.get("ae",""))
    return db
