
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
    "Ara-C": {"moa": "시타라빈(항대사제)", "ae": "🩸 골수억제 · 🤢 오심/구토 · 💊 점막염 · 👁️ 결막염(점안 예방) · 🧠 소뇌독성(고용량) · 발열/발진"},
    "Cytarabine": {"moa": "시타라빈(항대사제)", "ae": "🩸 골수억제 · 🤢 오심/구토 · 💊 점막염 · 👁️ 결막염(점안 예방) · 🧠 소뇌독성(고용량) · 발열/발진"},
    "Bendamustine": {"moa": "알킬화제", "ae": "🩸 골수억제 · 발열/감염 · 피부발진 · 피로"},
    "Bleomycin": {"moa": "항종양 항생제", "ae": "🫁 폐독성(섬유화) · 발열 · 피부색소침착 · 손발가려움"},
    "Brentuximab Vedotin": {"moa": "CD30 표적 ADC", "ae": "🧠 말초신경병증 · 피로 · 오심 · 혈구감소"},
    "Cabozantinib": {"moa": "멀티 TKI (MET/VEGFR 등)", "ae": "설사 · 손발증후군 · 고혈압 · 피로 · 구내염"},
    "Carboplatin": {"moa": "백금제(Platinum)", "ae": "🩸 골수억제(혈소판↓) · 🤢 오심/구토 · 알레르기반응(누적)"},
    "Chlorambucil": {"moa": "알킬화제", "ae": "🩸 골수억제 · 오심 · 발진 · 불임 가능"},
    "Cisplatin": {"moa": "백금제(Platinum)", "ae": "🛎️ 이독성 · 🔔 말초신경병증 · 🤢 중증 오심/구토 · 🧂 전해질 이상(Mg/K↓) · 신독성"},
    "Crizotinib": {"moa": "ALK/ROS1 TKI", "ae": "시야장애 · 설사/변비 · 부종 · 간효소↑ · 피로"},
    "Dacarbazine": {"moa": "알킬화제(트리아진)", "ae": "🤢 심한 오심/구토 · 광과민 · 골수억제"},
    "Dactinomycin": {"moa": "항종양 항생제", "ae": "💊 점막염 · 오심/구토 · 골수억제 · 피부괴사(누출 시)"},
    "Docetaxel": {"moa": "탁산", "ae": "🖐️ 손발부종/무감각 · 🩸 골수억제 · 발열성 호중구감소증 · 손발톱 변화 · 체액저류"},
    "Entrectinib": {"moa": "TRK/ROS1/ALK TKI", "ae": "어지럼 · 체중증가 · 설사/변비 · 간효소↑ · QT 연장 드묾"},
    "Gemcitabine": {"moa": "핵산유사체", "ae": "🩸 골수억제 · 발열 · 발진 · 간효소↑ · 폐독성 드묾"},
    "Ibrutinib": {"moa": "BTK 억제제", "ae": "출혈위험 · 심방세동 · 설사 · 감염"},
    "Ifosfamide": {"moa": "알킬화제", "ae": "🩸 골수억제 · 🧠 신경독성(혼동) · 🩸 혈뇨/방광염(아크롤레인) · 전해질 이상"},
    "Irinotecan": {"moa": "Topo I 억제", "ae": "💩 설사(급성/지연) · 골수억제 · 복통 · 탈모"},
    "Lapatinib": {"moa": "HER2/EGFR TKI", "ae": "설사 · 발진 · 간효소↑ · 심기능↓ 드묾"},
    "Larotrectinib": {"moa": "TRK TKI", "ae": "어지럼 · 피로 · 간효소↑ · 체중증가"},
    "Lorlatinib": {"moa": "ALK/ROS1 TKI", "ae": "💭 인지/기분 변화 · 지질↑ · 체중↑ · 말초부종"},
    "Obinutuzumab": {"moa": "anti‑CD20 mAb", "ae": "💉 주입반응 · 감염 · 중성구감소 · HBV 재활성 경고"},
    "Oxaliplatin": {"moa": "백금제(Platinum)", "ae": "🧊 냉유발 감각이상 · 말초신경병증 · 오심/구토 · 설사 · 골수억제"},
    "Pazopanib": {"moa": "멀티 TKI", "ae": "고혈압 · 간독성 · 설사 · 탈모/피부변화"},
    "Pemetrexed": {"moa": "항대사제(엽산길항)", "ae": "피로 · 골수억제 · 발진 · 구내염 · 비타민B9/B12 보충 필요"},
    "Polatuzumab Vedotin": {"moa": "anti‑CD79b ADC", "ae": "🩸 골수억제 · 말초신경병증 · 감염"},
    "Pralsetinib": {"moa": "RET TKI", "ae": "고혈압 · 간효소↑ · 변비/설사 · 피로 · 간질성폐질환 드묾"},
    "Selpercatinib": {"moa": "RET TKI", "ae": "고혈압 · 간효소↑ · QT 연장 · 변비/설사"},
    "Sotorasib": {"moa": "KRAS G12C 억제제", "ae": "설사 · 오심 · 간효소↑ · 피로"},
    "Sunitinib": {"moa": "멀티 TKI", "ae": "고혈압 · 손발증후군 · 갑상선기능저하 · 피로 · 구내염"},
    "Trabectedin": {"moa": "DNA 결합제(육종)", "ae": "간효소↑ · 근육통(CPK↑) · 골수억제 · 피로"},
    "Tucatinib": {"moa": "HER2 TKI", "ae": "설사 · 손발증후군 드묾 · 간효소↑"},
    "Vandetanib": {"moa": "RET/VEGFR/EGFR TKI", "ae": "QT 연장 · 설사 · 발진 · 갑상선기능저하"},
    "Vinblastine": {"moa": "Vinca 알칼로이드", "ae": "골수억제 · 변비 · 말초신경병증"},
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


# === [PATCH 2025-10-22 KST] Fill missing ONCO_MAP refs (maintenance + targeted) ===
def _safe_extend_missing_onco_refs(db):
    _u = _upsert
    # Antimetabolites / maintenance
    _u(db, "6-MP", "6-머캅토퓨린", "항암제(Thiopurine)", "🩸 골수억제 · 간수치 상승 · 구역")
    _u(db, "MTX", "메토트렉세이트", "항암제(Antimetabolite)", "🩸 골수억제 · 💊 구내염 · 간수치↑ · 신독성(고용량) · 광과민")
    _u(db, "ATRA", "베사노이드(ATRA)", "분화유도제", "두통 · 피부건조 · 지질↑ · 📛 RA‑증후군(호흡곤란/발열/체액저류) 경고")
    _u(db, "Arsenic Trioxide", "삼산화비소(ATO)", "분화유도제", "QT 연장 · 전해질 이상 · 📛 RA‑증후군")

    # Classic anthracyclines
    _u(db, "Daunorubicin", "다우노루비신", "항암제(Anthracycline)", "❤️ 심근독성(누적) · 🩸 골수억제 · 탈모")
    _u(db, "Idarubicin", "이다루비신", "항암제(Anthracycline)", "❤️ 심근독성(누적) · 🩸 골수억제 · 구역")

    # Solid tumor/targeted add-ons
    _u(db, "Atezolizumab", "아테졸리주맙", "면역항암제(PD‑L1)", "면역관련 이상반응(폐렴/대장염/간염/내분비)")
    _u(db, "Durvalumab", "더발루맙", "면역항암제(PD‑L1)", "면역관련 이상반응(폐렴/대장염/간염/내분비)")
    _u(db, "Cetuximab", "세툭시맙", "표적치료(EGFR)", "여드름양 발진 · 저마그네슘혈증 · 과민반응")
    _u(db, "Panitumumab", "파니투무맙", "표적치료(EGFR)", "여드름양 발진 · 저마그네슘혈증")
    _u(db, "Sorafenib", "소라페닙", "표적치료(MTKI)", "손발증후군 · 고혈압 · 피로")
    _u(db, "Lenvatinib", "렌바티닙", "표적치료(MTKI)", "고혈압 · 단백뇨 · 피로 · 설사")
    _u(db, "Olaparib", "올라파립", "표적치료(PARP)", "오심 · 피로 · 빈혈")
    _u(db, "Niraparib", "니라파립", "표적치료(PARP)", "혈소판감소 · 오심 · 피로")

    # Chemo add-ons
    _u(db, "Topotecan", "토포테칸", "항암제(Topoisomerase I)", "🩸 골수억제 · 오심/구토 · 탈모")
    _u(db, "Nab-Paclitaxel", "나노입자 파클리탁셀", "항암제(Taxane)", "🧠 말초신경병증 · 🩸 골수억제")

    # Lowercase mirrors for robustness
    for key in ["6-MP","MTX","ATRA","Arsenic Trioxide","Daunorubicin","Idarubicin",
                "Atezolizumab","Durvalumab","Cetuximab","Panitumumab","Sorafenib","Lenvatinib",
                "Olaparib","Niraparib","Topotecan","Nab-Paclitaxel"]:
        rec = db.get(key, {})
        _u(db, key.lower(), rec.get("alias", key), rec.get("class",""), rec.get("ae",""))

try:
    __prev_ensure  # type: ignore
except NameError:
    __prev_ensure = None

# chain patch into ensure_onco_drug_db
_prev = globals().get("ensure_onco_drug_db")
def ensure_onco_drug_db(db):
    if callable(_prev):
        try:
            _prev(db)
        except Exception:
            pass
    _safe_extend_missing_onco_refs(db)
# === [END PATCH] ===
