
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

# === [PATCH 2025-10-22 KST] Add missing onco_map drugs with AE ===
def _extend_onco_missing_from_map(db: Dict[str, Dict[str, Any]]) -> None:
    _u = _upsert
    # Immunotherapy / mAbs
    _u(db, "Atezolizumab", "아테졸리주맙", "면역항암제(PD-L1)", "면역관련 이상반응(피부/대장염/간염/폐렴/내분비)",)
    _u(db, "Durvalumab", "더발루맙", "면역항암제(PD-L1)", "면역관련 이상반응(피부/대장염/간염/폐렴/내분비)",)
    _u(db, "Cetuximab", "세툭시맙", "표적치료(anti-EGFR)", "여드름양 발진 · 설사/저Mg · 주입반응 · 손발톱변화")
    _u(db, "Panitumumab", "파니투무맙", "표적치료(anti-EGFR)", "여드름양 발진 · 설사/저Mg · 주입반응")
    # PARP inhibitors
    _u(db, "Olaparib", "올라파립", "표적치료(PARP)", "빈혈/혈소판감소 · 피로 · 오심 · 구내염")
    _u(db, "Niraparib", "니라파립", "표적치료(PARP)", "혈소판감소/빈혈 · 고혈압 · 피로 · 오심")
    # Multi-TKI
    _u(db, "Lenvatinib", "렌바티닙", "표적치료(MTKI)", "고혈압 · 단백뇨 · 설사 · 피로 · 손발증후군")
    _u(db, "Sorafenib", "소라페닙", "표적치료(MTKI)", "손발증후군 · 설사 · 고혈압 · 피로")
    # Cytotoxics
    _u(db, "Topotecan", "토포테칸", "항암제(Topo I inhibitor)", "골수억제 · 오심/구토 · 탈모 · 피로")
    _u(db, "Nab-Paclitaxel", "나노입자 파클리탁셀", "항암제(Taxane)", "말초신경병증 · 골수억제 · 과민반응(용제↓) · 피로")
    _u(db, "Daunorubicin", "다우노루비신", "항암제(Anthracycline)", "심독성(누적) · 골수억제 · 점막염 · 오심/구토")
    _u(db, "Idarubicin", "이다루비신", "항암제(Anthracycline)", "심독성(누적) · 골수억제 · 점막염 · 오심/구토")

    # lowercase mirrors
    for k in ["Atezolizumab","Durvalumab","Cetuximab","Panitumumab","Olaparib","Niraparib","Lenvatinib","Sorafenib","Topotecan","Nab-Paclitaxel","Daunorubicin","Idarubicin"]:
        rec = db.get(k, {})
        _u(db, k.lower(), rec.get("alias", k), rec.get("moa",""), rec.get("ae",""))

_prev_oncomiss = globals().get("ensure_onco_drug_db")
def ensure_onco_drug_db(db):
    if callable(_prev_oncomiss):
        try:
            _prev_oncomiss(db)
        except Exception:
            pass
    _extend_onco_missing_from_map(db)
# === [/PATCH] ===

# === [PATCH 2025-10-22 KST] Add ATRA/ATO ===
def _extend_apl_core_agents(db: Dict[str, Dict[str, Any]]) -> None:
    _u = _upsert
    _u(db, "ATRA", "ATRA(베사노이드)", "분화유도제", "RA-증후군(발열/호흡곤란/부종) · 두통/피부건조 · 간효소↑ · 고지혈증")
    _u(db, "Arsenic Trioxide", "비소 트리옥사이드(ATO)", "분화유도제", "QT 연장 · 전해질 이상(K/Mg) · 피로 · 간효소↑ · RA-유사 증후군")
    _u(db, "ATO", "비소 트리옥사이드(ATO)", "분화유도제", "QT 연장 · 전해질 이상(K/Mg) · 피로 · 간효소↑ · RA-유사 증후군")
    for k in ["ATRA","Arsenic Trioxide","ATO"]:
        rec = db.get(k, {})
        _u(db, k.lower(), rec.get("alias", k), rec.get("moa",""), rec.get("ae",""))

_prev_apl = globals().get("ensure_onco_drug_db")
def ensure_onco_drug_db(db):
    if callable(_prev_apl):
        try:
            _prev_apl(db)
        except Exception:
            pass
    _extend_apl_core_agents(db)
# === [/PATCH] ===

# === [PATCH 2025-10-22 KST] Add MTX and 6-MP for maintenance ===
def _extend_maintenance_core(db: Dict[str, Dict[str, Any]]) -> None:
    _u = _upsert
    _u(db, "MTX", "메토트렉세이트(MTX)", "항암제/면역조절(Antimetabolite)", "간효소↑ · 구내염 · 골수억제 · 신독성(고용량) · 광과민/피부발진")
    _u(db, "Methotrexate", "메토트렉세이트(MTX)", "항암제/면역조절(Antimetabolite)", "간효소↑ · 구내염 · 골수억제 · 신독성(고용량) · 광과민/피부발진")
    _u(db, "6-MP", "6-머캅토퓨린(6-MP)", "항대사제", "골수억제 · 간독성 · 오심/구토 · 발진")
    _u(db, "Mercaptopurine", "6-머캅토퓨린(6-MP)", "항대사제", "골수억제 · 간독성 · 오심/구토 · 발진")
    for k in ["MTX","Methotrexate","6-MP","Mercaptopurine"]:
        rec = db.get(k, {})
        _u(db, k.lower(), rec.get("alias", k), rec.get("moa",""), rec.get("ae",""))

_prev_maint = globals().get("ensure_onco_drug_db")
def ensure_onco_drug_db(db):
    if callable(_prev_maint):
        try:
            _prev_maint(db)
        except Exception:
            pass
    _extend_maintenance_core(db)
# === [/PATCH] ===

# === [PATCH 2025-10-22 KST] Monitoring checklist metadata ===
def _attach_monitoring_metadata(db: Dict[str, Dict[str, Any]]) -> None:
    """각 약물/군별 모니터링 체크리스트를 'monitor' 필드로 추가(추가만, 기존 필드 보존)."""
    def add_mon(keys, items):
        for k in keys:
            if k in db:
                rec = db[k]
                mons = list(rec.get("monitor", [])) if isinstance(rec.get("monitor"), (list, tuple)) else []
                for it in items:
                    if it not in mons:
                        mons.append(it)
                rec["monitor"] = mons
            if k.lower() in db:
                rec = db[k.lower()]
                mons = list(rec.get("monitor", [])) if isinstance(rec.get("monitor"), (list, tuple)) else []
                for it in items:
                    if it not in mons:
                        mons.append(it)
                rec["monitor"] = mons

    # 공통 세포독성
    add_mon([
        "Cyclophosphamide","Ifosfamide","Cytarabine","Ara-C","Ara-C IV","Ara-C SC","Ara-C HDAC",
        "Gemcitabine","Dacarbazine","Dactinomycin","Topotecan","Vincristine","Vinblastine",
        "Paclitaxel","Docetaxel","Chlorambucil","Bendamustine","Trabectedin","Daunorubicin","Idarubicin","Doxorubicin"
    ], ["CBC","LFT","Renal(eGFR)","Electrolytes","Fever/Sepsis","Mucositis","N/V","Diarrhea"])

    # Ara-C 고용량 특이
    add_mon(["Ara-C HDAC","Cytarabine HDAC"], ["Cerebellar exam","Conjunctivitis(스테로이드 점안)"])

    # Platinum
    add_mon(["Cisplatin"], ["Renal(eGFR)","Mg/K","Ototoxicity","Neuropathy"])
    add_mon(["Carboplatin"], ["CBC(Platelet)","Allergy"])
    add_mon(["Oxaliplatin"], ["Cold-induced neuropathy","Neuropathy"])

    # Taxane
    add_mon(["Paclitaxel","Docetaxel","Nab-Paclitaxel"], ["Neuropathy","Hypersensitivity","Edema(Doce)"])

    # Anthracycline
    add_mon(["Doxorubicin","Daunorubicin","Idarubicin"], ["Echo/LVEF","BNP/NT-proBNP"])

    # Anti-VEGF/VEGFR
    add_mon(["Bevacizumab","Ramucirumab","Lenvatinib","Sorafenib","Regorafenib","Sunitinib","Pazopanib","Ripretinib"],
            ["BP","Proteinuria(UPCR)","Wound healing/bleeding"])

    # HER2 축
    add_mon(["Trastuzumab","Pertuzumab","T-DM1","Trastuzumab deruxtecan"], ["Echo/LVEF","Platelet(T-DM1)","ILD(deruxte칸)"])

    # EGFR/ALK/RET/TRK TKI
    add_mon(["Osimertinib"], ["Rash/Diarrhea","ILD","LFT"])
    add_mon(["Alectinib","Crizotinib","Capmatinib","Lorlatinib"], ["Edema","LFT","Lipids(Lorlatinib)"])
    add_mon(["Selpercatinib","Pralsetinib","Entrectinib","Larotrectinib","Tucatinib"], ["BP","LFT","QT(ECG)"])

    # mTOR
    add_mon(["Everolimus"], ["Glucose","Lipids","LFT","ILD"])

    # PARP
    add_mon(["Olaparib","Niraparib"], ["CBC(Anemia/Platelet)","BP(Nira)","Fatigue/Nausea"])

    # 면역항암제
    add_mon(["Nivolumab","Pembrolizumab","Atezolizumab","Durvalumab"], ["TFT","LFT","Renal(eGFR)","Cortisol±ACTH","iRAE screening","SpO2(if respiratory)"])

    # 호르몬/지지요법
    add_mon(["Octreotide"], ["Stool/Fatty stool","Gallstone"])

    # 스테로이드
    add_mon(["Prednisone"], ["Glucose","BP","Sleep/Mood","Weight"])

    # 유지요법
    add_mon(["MTX","Methotrexate"], ["LFT","Renal(eGFR)","Mucositis","Photosensitivity"])
    add_mon(["6-MP","Mercaptopurine"], ["CBC","LFT","Rash/Nausea"])

_prev_monitor = globals().get("ensure_onco_drug_db")
def ensure_onco_drug_db(db):
    if callable(_prev_monitor):
        try:
            _prev_monitor(db)
        except Exception:
            pass
    _attach_monitoring_metadata(db)
# === [/PATCH] ===

# === [PATCH 2025-10-22 KST] Final placeholder cleanup (last in chain) ===
def _final_placeholder_cleanup(db: Dict[str, Dict[str, Any]]) -> None:
    # For each alias bucket, copy the richest non-placeholder AE to all variants.
    buckets: Dict[str, Dict[str, Any]] = {}
    for k, v in list(db.items()):
        if not isinstance(v, dict):
            continue
        alias = (v.get("alias") or k)
        ae = (v.get("ae") or "").strip()
        if "부작용 정보 필요" in ae:
            ae = ""
        cur = buckets.get(alias)
        if (cur is None) or (len(ae) > len((cur.get("ae") or ""))):
            # store a shallow copy with cleaned ae for comparison
            buckets[alias] = {"ae": ae}

    # propagate
    for k, v in list(db.items()):
        if not isinstance(v, dict):
            continue
        alias = (v.get("alias") or k)
        best = buckets.get(alias, {})
        best_ae = (best.get("ae") or "").strip()
        if best_ae and ((v.get("ae") or "").strip() != best_ae):
            v["ae"] = best_ae

_prev_final = globals().get("ensure_onco_drug_db")
def ensure_onco_drug_db(db):
    if callable(_prev_final):
        try:
            _prev_final(db)
        except Exception:
            pass
    _final_placeholder_cleanup(db)
# === [/PATCH] ===

# === [PATCH 2025-10-22 KST] Robust key-variant expansion (EN/KR/composite/lowercase) ===

def _expand_key_variants(db: Dict[str, Dict[str, Any]]) -> None:
    """
    Robust key variants: eng, eng.lower, alias, alias.lower, "eng (alias)", "alias (eng)", and their lowercase.
    Only propagate from records that already have non-placeholder AE.
    """
    def up(src_key: str, dest_key: str):
        src = db.get(src_key, {})
        if not isinstance(src, dict):
            return
        _upsert(db, dest_key, src.get("alias") or src_key, src.get("moa") or "", src.get("ae") or "")

    base_items = [(k, v) for k, v in list(db.items()) if isinstance(v, dict)]
    for eng, rec in base_items:
        alias = (rec.get("alias") or eng).strip()
        ae = (rec.get("ae") or "").strip()
        if (not ae) or ("부작용 정보 필요" in ae):
            continue

        # base
        up(eng, eng.lower())
        if alias and alias != eng:
            up(eng, alias)
            up(eng, alias.lower())
            comp1 = f"{eng} ({alias})"
            comp2 = f"{alias} ({eng})"
            up(eng, comp1)
            up(eng, comp2)
            up(eng, comp1.lower())
            up(eng, comp2.lower())

_prev_expand = globals().get("ensure_onco_drug_db")
def ensure_onco_drug_db(db):
    if callable(_prev_expand):
        try:
            _prev_expand(db)
        except Exception:
            pass
    _expand_key_variants(db)
# === [/PATCH] ===

# === [PATCH 2025-10-22 KST] ULTIMATE FINAL FILL (runs last) ===
def _ultimate_final_fill(db: Dict[str, Dict[str, Any]]) -> None:
    AE = {
        "Bendamustine": "🩸 골수억제 · 발열/감염 · 피부발진 · 피로",
        "Bleomycin": "🫁 폐독성(섬유화) · 발열 · 피부색소침착 · 손발가려움",
        "Carboplatin": "🩸 골수억제(혈소판↓) · 🤢 오심/구토 · 알레르기반응(누적)",
        "Cisplatin": "🛎️ 이독성 · 🔔 말초신경병증 · 🤢 중증 오심/구토 · 🧂 전해질 이상(Mg/K↓) · 신독성",
        "Chlorambucil": "🩸 골수억제 · 오심 · 발진 · 불임 가능",
        "Docetaxel": "🖐️ 손발부종/무감각 · 🩸 골수억제 · 발열성 호중구감소증 · 손발톱 변화 · 체액저류",
        "Gemcitabine": "🩸 골수억제 · 발열 · 발진 · 간효소↑ · 폐독성 드묾",
        "Ifosfamide": "🩸 골수억제 · 🧠 신경독성(혼동) · 🩸 혈뇨/방광염(아크롤레인) · 전해질 이상",
        "Irinotecan": "💩 설사(급성/지연) · 골수억제 · 복통 · 탈모",
        "Lapatinib": "설사 · 발진 · 간효소↑ · 심기능↓ 드묾",
        "Larotrectinib": "어지럼 · 피로 · 간효소↑ · 체중증가",
        "Lorlatinib": "💭 인지/기분 변화 · 지질↑ · 체중↑ · 말초부종",
        "Obinutuzumab": "💉 주입반응 · 감염 · 중성구감소 · HBV 재활성 경고",
        "Oxaliplatin": "🧊 냉유발 감각이상 · 말초신경병증 · 오심/구토 · 설사 · 골수억제",
        "Pazopanib": "고혈압 · 간독성 · 설사 · 탈모/피부변화",
        "Pemetrexed": "피로 · 골수억제 · 발진 · 구내염 · 비타민B9/B12 보충 필요",
        "Polatuzumab Vedotin": "🩸 골수억제 · 말초신경병증 · 감염",
        "Pralsetinib": "고혈압 · 간효소↑ · 변비/설사 · 피로 · 간질성폐질환 드묾",
        "Selpercatinib": "고혈압 · 간효소↑ · QT 연장 · 변비/설사",
        "Sotorasib": "설사 · 오심 · 간효소↑ · 피로",
        "Sunitinib": "고혈압 · 손발증후군 · 갑상선기능저하 · 피로 · 구내염",
        "Trabectedin": "간효소↑ · 근육통(CPK↑) · 골수억제 · 피로",
        "Tucatinib": "설사 · 손발증후군 드묾 · 간효소↑",
        "Vandetanib": "QT 연장 · 설사 · 발진 · 갑상선기능저하",
        "Vinblastine": "골수억제 · 변비 · 말초신경병증",
        "Crizotinib": "시야장애 · 설사/변비 · 부종 · 간효소↑ · 피로",
        "Entrectinib": "어지럼 · 체중증가 · 설사/변비 · 간효소↑ · QT 연장 드묾",
        "Alectinib": "근육통 · 변비 · 🧪 간효소 상승",
        "Capmatinib": "💧 말초부종 · 🧪 간효소 상승",
        "Gemcitabine": "🩸 골수억제 · 발열 · 발진 · 간효소↑ · 폐독성 드묾",
        "Brentuximab Vedotin": "🧠 말초신경병증 · 피로 · 오심 · 혈구감소",
        "Cabozantinib": "설사 · 손발증후군 · 고혈압 · 피로 · 구내염",
        "Bevacizumab": "🩸 출혈 · 고혈압 · 단백뇨 · 상처치유 지연",
        "Cytarabine": "🩸 골수억제 · 🤢 오심/구토 · 💊 점막염 · 👁️ 결막염(점안 예방) · 🧠 소뇌독성(고용량) · 발열/발진",
        "Ara-C": "🩸 골수억제 · 🤢 오심/구토 · 💊 점막염 · 👁️ 결막염(점안 예방) · 🧠 소뇌독성(고용량) · 발열/발진",
    }
    # Apply to canonical keys and common variants (lower/composite)
    for eng, ae in AE.items():
        alias = db.get(eng, {}).get("alias") or eng
        _upsert(db, eng, alias, db.get(eng, {}).get("moa",""), ae)
        _upsert(db, eng.lower(), alias, db.get(eng, {}).get("moa",""), ae)
        comp1 = f"{eng} ({alias})"
        comp2 = f"{alias} ({eng})"
        _upsert(db, comp1, alias, db.get(eng, {}).get("moa",""), ae)
        _upsert(db, comp2, alias, db.get(eng, {}).get("moa",""), ae)
        _upsert(db, comp1.lower(), alias, db.get(eng, {}).get("moa",""), ae)
        _upsert(db, comp2.lower(), alias, db.get(eng, {}).get("moa",""), ae)

_prev_ultimate = globals().get("ensure_onco_drug_db")
def ensure_onco_drug_db(db):
    if callable(_prev_ultimate):
        try:
            _prev_ultimate(db)
        except Exception:
            pass
    _ultimate_final_fill(db)
# === [/PATCH] ===

# === [PATCH 2025-10-22 KST] Alias-KR mapping + mixed-case composites (very last) ===
def _ultimate_alias_kr_and_composites(db: Dict[str, Dict[str, Any]]) -> None:
    KR = {
        "Bendamustine":"벤다무스틴",
        "Chlorambucil":"클로람부실",
        "Dacarbazine":"다카바진",
        "Dactinomycin":"닥티노마이신",
        "Ifosfamide":"이포스파마이드",
        "Lapatinib":"라파티닙",
        "Obinutuzumab":"오비누투주맙",
        "Pazopanib":"파조파닙",
        "Sunitinib":"수니티닙",
        "Trabectedin":"트라벡테딘",
    }
    for eng, kr in KR.items():
        if eng in db and isinstance(db[eng], dict):
            rec = db[eng]
            ae = (rec.get("ae") or "").strip()
            moa = rec.get("moa","")
            if ae:
                _upsert(db, eng, kr, moa, ae)  # update alias to KR while preserving AE
                # generate composites with mixed-case variants
                L = eng.lower()
                K = kr  # Korean lower same
                combos = [
                    f"{eng} ({kr})", f"{kr} ({eng})",
                    f"{L} ({kr})",   f"{eng} ({kr.lower()})",
                    f"{kr} ({L})",   f"{kr.lower()} ({eng})",
                    f"{L} ({kr.lower()})", f"{kr.lower()} ({L})",
                ]
                for c in combos:
                    _upsert(db, c, kr, moa, ae)

_prev_ultimate2 = globals().get("ensure_onco_drug_db")
def ensure_onco_drug_db(db):
    if callable(_prev_ultimate2):
        try:
            _prev_ultimate2(db)
        except Exception:
            pass
    _ultimate_alias_kr_and_composites(db)
# === [/PATCH] ===

# === [PATCH 2025-10-22 KST] Mini fill: Dacarbazine & Dactinomycin ===
def _finalize_fill_daca_dacti(db: Dict[str, Dict[str, Any]]) -> None:
    items = {
        "Dacarbazine": ("다카바진", "🤢 심한 오심/구토 · 광과민 · 골수억제"),
        "Dactinomycin": ("닥티노마이신", "💊 점막염 · 오심/구토 · 골수억제 · 피부괴사(누출 시)"),
    }
    for eng, (kr, ae) in items.items():
        moa = db.get(eng, {}).get("moa","")
        _upsert(db, eng, kr, moa, ae)
        L = eng.lower()
        for c in [f"{eng} ({kr})", f"{kr} ({eng})", f"{L} ({kr})", f"{kr} ({L})"]:
            _upsert(db, c, kr, moa, ae)

_prev_daca = globals().get("ensure_onco_drug_db")
def ensure_onco_drug_db(db):
    if callable(_prev_daca):
        try:
            _prev_daca(db)
        except Exception:
            pass
    _finalize_fill_daca_dacti(db)
# === [/PATCH] ===

# === [PATCH 2025-10-22 KST] Human-friendly AE details ===
def _attach_ae_details(db: Dict[str, Dict[str, Any]]) -> None:
    """
    'ae_detail' 필드(사람이 보기 쉬운 요약)를 추가한다.
    구조: {
      "common": [ ... ],          # 흔한 부작용(간단 설명)
      "serious": [ ... ],         # 중대한 경고(간단 설명)
      "tips": [ ... ],            # 예방/관리 팁
      "call": [ ... ],            # 즉시 연락해야 할 신호
      "notes": [ ... ],           # 기타
    }
    """
    def put(key, data):
        if key in db and isinstance(db[key], dict):
            rec = db[key]
            if not isinstance(rec.get("ae_detail"), dict):
                rec["ae_detail"] = {}
            # 병합(덮어쓰기 없이 추가)
            for k, v in data.items():
                if not v:
                    continue
                arr = list(rec["ae_detail"].get(k, [])) if isinstance(rec["ae_detail"].get(k), (list, tuple)) else []
                for item in v:
                    if item not in arr:
                        arr.append(item)
                rec["ae_detail"][k] = arr

    # 5-FU / Capecitabine (손발증후군/위장관)
    fluoropy = {
      "common": ["피부: 손발증후군(따가움·붉어짐·갈라짐)", "위장관: 설사, 구내염, 오심/구토", "혈액: 백혈구/혈소판 감소로 감염·출혈 위험"],
      "serious": ["심장: 흉통/호흡곤란(드묾, 심근허혈)", "중증 설사로 탈수"],
      "tips": ["손발 보습·마찰/열 피하기", "수분섭취 유지, 설사 지속 시 지침에 따라 약 복용", "구강위생·입안 자극 음식 피하기"],
      "call": ["37.8–38.0℃ 이상 발열 또는 오한", "혈변/검은변, 멈추지 않는 구토/설사", "숨가쁨·흉통"],
    }
    for k in ["5-FU","Capecitabine","capecitabine","5-fu","5-플루오로우라실","Capecitabine (카페시타빈)","카페시타빈 (Capecitabine)"]:
        put(k, fluoropy)

    # Cisplatin / Carboplatin / Oxaliplatin (백금계)
    cis_detail = {
      "common": ["오심/구토(예방약 필수)", "피로", "혈액: 혈구감소"],
      "serious": ["신장: 크레아티닌↑, 전해질(Mg/K)↓", "청력: 이명/난청", "신경: 손저림·저림감(말초신경병증)"],
      "tips": ["수액 충분히(병원 지침)", "이명·청력저하 즉시 알리기", "Mg/K 정기 체크"],
      "call": ["소변 급감/붉은 소변", "심한 어지럼·근육경련(전해질 이상 의심)"],
    }
    for k in ["Cisplatin","cisplatin","Cisplatin (시스플라틴)","시스플라틴 (Cisplatin)"]:
        put(k, cis_detail)

    carbo_detail = {
      "common": ["혈소판감소(멍/코피)","오심/구토","피로"],
      "serious": ["과민반응(누적 주기에서 갑자기 나타날 수 있음)"],
      "tips": ["멍/코피 잘 생기면 곧바로 알리기", "주사 중 입·몸 가려움/답답함 느끼면 즉시 손들기"],
      "call": ["호흡곤란·두드러기·어지럼(알레르기 의심)"],
    }
    for k in ["Carboplatin","carboplatin","Carboplatin (카보플라틴)","카보플라틴 (Carboplatin)"]:
        put(k, carbo_detail)

    oxali_detail = {
      "common": ["손발·입 주위 저림/찌릿(특히 찬 것 접촉 시)", "오심/구토", "설사"],
      "serious": ["지속되는 감각저하·운동장애(누적 신경독성)"],
      "tips": ["치료 후 며칠간 차가운 음식/음료·찬 바람 피하기", "따뜻한 장갑/마스크 사용"],
      "call": ["젓가락 잡기 어려움·버튼 잠그기 힘듦 등 기능장애 진행"],
    }
    for k in ["Oxaliplatin","oxaliplatin","Oxaliplatin (옥살리플라틴)","옥살리플라틴 (Oxaliplatin)"]:
        put(k, oxali_detail)

    # Doxorubicin (안트라사이클린)
    doxo = {
      "common": ["피로, 탈모, 점막염", "혈액: 골수억제"],
      "serious": ["심장: 누적용량에 따른 심기능저하(심부전)"],
      "tips": ["누적용량/심장초음파 일정 확인", "구강 케어 철저·자극 음식 피하기"],
      "call": ["숨가쁨·부종·갑작스런 체중증가(심부전 의심)"],
    }
    for k in ["Doxorubicin","독소루비신"]:
        put(k, doxo)

    # Docetaxel / Paclitaxel (탁산계)
    doce = {
      "common": ["손발 저림/무감각(말초신경병증)","손발톱 변화","부종/체액저류","발열성 호중구감소증 위험"],
      "serious": ["과민반응(초반 주기)"],
      "tips": ["부종 발생 시 양말/다리 올리기 등 생활관리 + 의료진 상의", "과민증상 즉시 알리기"],
      "call": ["38℃ 전후 발열·오한", "호흡곤란·가슴답답·몸 가려움(주입 중)"],
    }
    for k in ["Docetaxel","docetaxel","Docetaxel (도세탁셀)","도세탁셀 (Docetaxel)"]:
        put(k, doce)

    pacli = {
      "common": ["말초신경병증(저림/통증)","골수억제","주입 과민반응 가능"],
      "serious": ["중증 과민반응(혈압저하·호흡곤란)"],
      "tips": ["초반 주기 모니터 강화(과민)","손발 시림·통증 지속 시 용량조절 상담"],
      "call": ["호흡곤란·어지럼·전신 두드러기(즉시)"],
    }
    for k in ["Paclitaxel","paclitaxel","Paclitaxel (파클리탁셀)","파클리탁셀 (Paclitaxel)"]:
        put(k, pacli)

    # Irinotecan
    iri = {
      "common": ["설사(급성: 투여 중/직후, 지연: 수일 후)","복통","골수억제"],
      "serious": ["중증 탈수/전해질 이상"],
      "tips": ["급성 설사: 의료진 처방 약 즉시 복용(예: 아트로핀)", "지연 설사: 지침대로 지사제 복용·수분 보충"],
      "call": ["24시간 이상 지속되는 설사/혈변·열 동반"],
    }
    for k in ["Irinotecan","irinotecan","Irinotecan (이리노테칸)","이리노테칸 (Irinotecan)"]:
        put(k, iri)

    # Pemetrexed
    pem = {
      "common": ["피로, 구내염, 발진", "골수억제"],
      "serious": ["중증 점막염/감염"],
      "tips": ["엽산(B9)·비타민B12 보충 필수", "햇빛 노출 과다 피하기"],
      "call": ["입안 통증/궤양으로 음식·수분 섭취 곤란", "38℃ 전후 발열"],
    }
    for k in ["Pemetrexed","pemetrexed","Pemetrexed (페메트렉시드)","페메트렉시드 (Pemetrexed)"]:
        put(k, pem)

    # Bevacizumab / Ramucirumab (anti-VEGF/VEGFR)
    beva = {
      "common": ["혈압상승(고혈압)","소변 단백뇨"],
      "serious": ["출혈·혈전","상처치유 지연·천공(드묾)"],
      "tips": ["집에서도 혈압 기록하기","소변 단백뇨 추적(외래 검사)"],
      "call": ["심한 두통·시야이상·가슴통증·호흡곤란", "혈변/복통(천공 의심)"],
    }
    for k in ["Bevacizumab","bevacizumab","Bevacizumab (베바시주맙)","베바시주맙 (Bevacizumab)"]:
        put(k, beva)
    ramu = {
      "common": ["혈압상승(고혈압)","단백뇨"],
      "serious": ["출혈·혈전"],
      "tips": ["혈압 매일 측정·기록","소변 단백뇨 주기적 확인"],
      "call": ["갑작스런 신경증상/흉통/호흡곤란"],
    }
    for k in ["Ramucirumab","ramucirumab"]:
        put(k, ramu)

    # HER2 축
    trastu = {
      "common": ["주입반응(오한/발열)"],
      "serious": ["심기능저하(LVEF 감소)"],
      "tips": ["심초음파 일정 준수"],
      "call": ["숨가쁨·부종·갑작스런 체중증가"],
    }
    for k in ["Trastuzumab","trastuzumab","Trastuzumab (트라스투주맙)","트라스투주맙 (Trastuzumab)"]:
        put(k, trastu)
    tdm1 = {
      "common": ["피로, 오심","혈소판감소","간효소 상승"],
      "serious": ["중증 간독성"],
      "tips": ["혈소판/간기능 정기 체크"],
      "call": ["코피 멈추지 않음·멍 많아짐", "황달"],
    }
    for k in ["T-DM1","t-dm1"]:
        put(k, tdm1)
    deru = {
      "common": ["오심","피로"],
      "serious": ["ILD/약물성 폐렴(중요)"],
      "tips": ["기침/호흡곤란 새로 생기면 지체없이 보고"],
      "call": ["숨가쁨·가슴통증·발열 동반 호흡기 증상"],
    }
    for k in ["Trastuzumab deruxtecan","trastuzumab deruxtecan"]:
        put(k, deru)

    # EGFR/ALK/RET/TRK
    osi = {
      "common": ["설사·발진", "피로"],
      "serious": ["ILD 드묾"],
      "tips": ["피부건조 관리·자극 피하기","설사 시 수분 보충"],
      "call": ["기침·호흡곤란·발열 동반시"],
    }
    for k in ["Osimertinib","osimertinib","Osimertinib (오시머티닙)","오시머티닙 (Osimertinib)"]:
        put(k, osi)

    alect = {
      "common": ["근육통/통증","변비","간효소 상승","부종"],
      "serious": ["근육효소(CPK) 상승 드묾"],
      "tips": ["근육통 심하면 진통제 조절 상담","부종 시 소금섭취 조절"],
      "call": ["소변 갈색·근육통 극심(횡문근융해 의심 드묾)"],
    }
    for k in ["Alectinib","alectinib","Alectinib (알렉티닙)","알렉티닙 (Alectinib)"]:
        put(k, alect)

    selp = {
      "common": ["고혈압","간효소 상승","변비/설사"],
      "serious": ["QT 연장(심장리듬)"],
      "tips": ["혈압 자가측정·기록","맥박 불규칙·어지럼 시 즉시 보고"],
      "call": ["실신·심계항진·흉통"],
    }
    for k in ["Selpercatinib","selpercatinib"]:
        put(k, selp)

    prale = {
      "common": ["고혈압","간효소 상승","변비/설사","피로"],
      "serious": ["간질성 폐질환 드묾"],
      "tips": ["혈압관리·간기능 추적","기침/호흡곤란 새로 생기면 즉시 보고"],
      "call": ["숨가쁨·가슴통증·산소포화도 저하"],
    }
    for k in ["Pralsetinib","pralsetinib"]:
        put(k, prale)

    lorl = {
      "common": ["인지/기분 변화","지질상승","체중증가","말초부종"],
      "serious": ["중대한 신경정신 증상 드묾"],
      "tips": ["집중력·기분 변화 기록·상담","지질 수치 추적"],
      "call": ["혼동/극심한 불안·우울·환시 등"],
    }
    for k in ["Lorlatinib","lorlatinib"]:
        put(k, lorl)

    larotrk = {
      "common": ["어지럼","피로","간효소 상승","체중증가"],
      "serious": [],
      "tips": ["어지럼 시 운전·위험 작업 주의","간기능 정기 체크"],
      "call": ["지속되는 심한 어지럼·구토"],
    }
    for k in ["Larotrectinib","larotrectinib"]:
        put(k, larotrk)

    entre = {
      "common": ["어지럼","체중증가","설사/변비","간효소 상승"],
      "serious": ["QT 연장 드묾"],
      "tips": ["어지럼 시 안전 주의","심전도 필요 시 병원 지침"],
      "call": ["실신·어지럼 악화"],
    }
    for k in ["Entrectinib","entrectinib"]:
        put(k, entre)

    # Multi-TKI / mTOR
    rego = {
      "common": ["손발증후군","피로","고혈압"],
      "serious": ["간독성"],
      "tips": ["손발 보습/마찰 회피","혈압 기록·간기능 추적"],
      "call": ["피부 벗겨짐·궤양, 심한 피로·황달"],
    }
    for k in ["Regorafenib","regorafenib"]:
        put(k, rego)

    suni = {
      "common": ["고혈압","손발증후군","갑상선기능저하","피로","구내염"],
      "serious": ["심혈관 사건 드묾"],
      "tips": ["혈압·갑상선 기능 추적","손발 관리"],
      "call": ["흉통·호흡곤란"],
    }
    for k in ["Sunitinib","sunitinib"]:
        put(k, suni)

    pazo = {
      "common": ["고혈압","간독성","설사","탈모/피부변화"],
      "serious": ["간부전 드묾"],
      "tips": ["혈압·간기능 정기 체크"],
      "call": ["황달·심한 피로·복부통증"],
    }
    for k in ["Pazopanib","pazopanib"]:
        put(k, pazo)

    evero = {
      "common": ["구내염","고혈당/지질 이상","피부 발진"],
      "serious": ["ILD/폐렴"],
      "tips": ["구강 케어·매운 음식 피하기","혈당/지질 추적"],
      "call": ["기침·호흡곤란·발열"],
    }
    for k in ["Everolimus","everolimus"]:
        put(k, evero)

    # 면역항암제
    pembro_nivo = {
      "common": ["피부 발진/가려움","피로","경미한 설사"],
      "serious": ["면역관련 이상반응: 대장염/간염/폐렴/내분비(갑상선/부신)"],
      "tips": ["새로운 증상은 작게라도 기록 후 보고","TFT/LFT/Cr/eGFR 정기 체크"],
      "call": ["혈성 설사/지속 설사","지속 발열·기침/호흡곤란","심한 피로·현기증(내분비)"],
    }
    for k in ["Nivolumab","nivolumab","Pembrolizumab","pembrolizumab"]:
        put(k, pembro_nivo)

    # Ara-C 제형
    arac_common = {
      "common": ["골수억제(감염/출혈 위험)","오심/구토","점막염","결막염(점안 예방)"],
      "serious": ["고용량에서 소뇌독성(걷기 휘청·말 더듬)"],
      "tips": ["HDAC 시 스테로이드 점안·소뇌 증상 매일 체크"],
      "call": ["시야흐림/눈 통증·분비물 증가","손떨림·말더듬·걸음 불안정"],
    }
    for k in ["Ara-C","Cytarabine","Ara-C IV","Ara-C SC","Ara-C HDAC","Cytarabine HDAC"]:
        put(k, arac_common)

_prev_aedetail = globals().get("ensure_onco_drug_db")
def ensure_onco_drug_db(db):
    if callable(_prev_aedetail):
        try:
            _prev_aedetail(db)
        except Exception:
            pass
    _attach_ae_details(db)
# === [/PATCH] ===

# === [PATCH 2025-10-22 KST] AE detail: extend coverage ===
def _extend_ae_details_more(db: Dict[str, Dict[str, Any]]) -> None:
    def put(key, data):
        if key in db and isinstance(db[key], dict):
            rec = db[key]
            if not isinstance(rec.get("ae_detail"), dict):
                rec["ae_detail"] = {}
            for k, v in data.items():
                if not v: continue
                arr = list(rec["ae_detail"].get(k, [])) if isinstance(rec["ae_detail"].get(k), (list, tuple)) else []
                for item in v:
                    if item not in arr:
                        arr.append(item)
                rec["ae_detail"][k] = arr

    simple = lambda common=None, serious=None, tips=None, call=None: {
        "common": common or [], "serious": serious or [], "tips": tips or [], "call": call or []
    }

    # mAbs/IO: Atezolizumab, Durvalumab, Cetuximab, Panitumumab
    be_io = simple(
        common=["피부 발진/가려움", "경미한 설사/피로"],
        serious=["면역관련 이상반응(대장염/간염/폐렴/내분비)"],
        tips=["새 증상은 기록 후 보고", "TFT/LFT/Cr 주기 체크"],
        call=["혈성 설사·지속 설사", "지속 발열/기침·호흡곤란"]
    )
    for k in ["Atezolizumab","atezolizumab","Durvalumab","durvalumab"]:
        put(k, be_io)

    anti_egfr = simple(
        common=["여드름양 발진", "설사", "저마그네슘혈증", "손발톱 변화"],
        serious=["중증 피부독성 드묾"],
        tips=["보습·자극 피하기", "Mg 주기 확인"],
        call=["광범위 피부통증/고열"]
    )
    for k in ["Cetuximab","cetuximab","Panitumumab","panitumumab"]:
        put(k, anti_egfr)

    # PARP: Olaparib, Niraparib
    parp = simple(
        common=["빈혈/혈소판감소", "피로", "오심"],
        serious=["골수형성이상 드묾"],
        tips=["혈구수치 주기 체크", "Niraparib은 혈압 기록"],
        call=["어지럼·실신(빈혈), 지속 출혈"]
    )
    for k in ["Olaparib","olaparib","Niraparib","niraparib"]:
        put(k, parp)

    # Multi-TKI: Lenvatinib, Sorafenib, Cabozantinib
    mtk = simple(
        common=["고혈압", "손발증후군", "설사", "피로", "구내염"],
        serious=["간독성"],
        tips=["혈압기록/간기능 추적", "손발 보습"],
        call=["황달·심한 피로·피부 벗겨짐"]
    )
    for k in ["Lenvatinib","lenvatinib","Sorafenib","sorafenib","Cabozantinib","cabozantinib"]:
        put(k, mtk)

    # ALK/ROS/MET: Crizotinib, Capmatinib
    alkmet = simple(
        common=["부종", "설사/변비", "간효소 상승"],
        serious=["시야장애(Crizotinib)"],
        tips=["부종 시 염분 조절", "시야 이상/황달 즉시 보고"],
        call=["시야 흐림·복시, 황달"]
    )
    for k in ["Crizotinib","crizotinib","Capmatinib","capmatinib"]:
        put(k, alkmet)

    # TRK: Larotrectinib, Entrectinib (이미 일부 있음 → 보강)
    trk_more = simple(
        common=["어지럼", "피로", "간효소 상승", "체중증가"],
        serious=["QT 연장(Entrectinib 드묾)"],
        tips=["어지럼 시 운전 주의", "간기능 체크"],
        call=["실신·어지럼 악화"]
    )
    for k in ["Larotrectinib","larotrectinib","Entrectinib","entrectinib"]:
        put(k, trk_more)

    # Anthracycline 확장: Daunorubicin, Idarubicin
    anth = simple(
        common=["피로", "점막염", "탈모", "골수억제"],
        serious=["심장기능저하(누적)"],
        tips=["심초음파 일정 준수", "구강 케어"],
        call=["숨가쁨·부종·갑작스런 체중증가"]
    )
    for k in ["Daunorubicin","daunorubicin","Idarubicin","idarubicin"]:
        put(k, anth)

    # Topoisomerase: Topotecan
    topo = simple(
        common=["골수억제", "오심/구토", "탈모", "피로"],
        serious=["중증 골수억제"],
        tips=["CBC 주기 체크", "감염 예방 교육"],
        call=["38℃ 전후 발열, 출혈"]
    )
    for k in ["Topotecan","topotecan"]:
        put(k, topo)

    # nab-Paclitaxel
    nabp = simple(
        common=["말초신경병증", "골수억제", "피로"],
        serious=["과민반응 드묾(용제↓)"],
        tips=["손발 저림 지속 시 상담", "초기 주기 주입 모니터"],
        call=["호흡곤란·전신 두드러기"]
    )
    for k in ["Nab-Paclitaxel","nab-paclitaxel"]:
        put(k, nabp)

    # Hormone/GI support: Octreotide
    octr = simple(
        common=["지방변/설사", "복부 불편", "담석"],
        tips=["지방 많은 음식 조절", "복통·황달 시 보고"],
        call=["발열 동반 우상복부 통증(담낭염 의심)"]
    )
    for k in ["Octreotide","octreotide"]:
        put(k, octr)

    # Steroid: Prednisone
    pred = simple(
        common=["식욕/체중 증가", "불면", "기분 변화", "혈당 상승"],
        tips=["식사/운동 관리", "수면 위생", "혈당 기록"],
        call=["기분 심각 악화·정신증상, 조절 안되는 고혈당"]
    )
    for k in ["Prednisone","prednisone"]:
        put(k, pred)

_prev_more = globals().get("ensure_onco_drug_db")
def ensure_onco_drug_db(db):
    if callable(_prev_more):
        try:
            _prev_more(db)
        except Exception:
            pass
    _extend_ae_details_more(db)
# === [/PATCH] ===

# === [PATCH 2025-10-22 KST] Auto-generate ae_detail for remaining drugs ===
def _autogen_ae_detail_for_all(db: Dict[str, Dict[str, Any]]) -> None:
    import re

    def has_detail(rec):
        return isinstance(rec.get("ae_detail"), dict) and any(rec["ae_detail"].get(k) for k in ("common","serious","tips","call","notes"))

    # Keyword maps
    serious_kw = {
        "ILD": ["ILD","폐렴","간질성","호흡곤란"],
        "Cardio": ["심근","LVEF","심부전","QT","부정맥","흉통"],
        "Renal": ["신독성","크레아티닌","혈뇨","방광염"],
        "Bleed": ["출혈","혈전","천공"],
        "Allergy": ["과민반응","아나필락시스"],
        "Neuro": ["소뇌","혼동","신경독성","말초신경병증","이독성","난청"],
        "Hepatic": ["간독성","간효소","황달"],
        "Myelo": ["발열성","호중구감소","골수억제"]
    }

    tip_by_class = {
        "VEGF": ["혈압 집에서도 기록", "소변 단백뇨 정기 체크"],
        "HER2": ["심초음파 일정 준수"],
        "mTOR": ["혈당/지질 주기 체크", "구내염 예방·관리가이드 준수"],
        "PARP": ["혈구수치 주기 체크", "어지럼/실신 시 즉시 보고"],
        "TKI": ["피부/설사 관리", "심전도·혈압 등 병원 지침 준수"],
        "Anthracycline": ["누적용량·심초음파 확인", "숨가쁨/부종 발생 시 즉시 연락"],
        "Taxane": ["과민반응 초기 모니터", "손발 저림 지속 시 상담"],
        "Platinum": ["수액·전해질 관리", "이명/청력저하 즉시 보고"],
        "Vinca": ["변비 예방(수분·식이섬유)", "장폐색 증상 시 즉시 연락"],
        "Antimetabolite": ["구강 위생·자극 음식 피하기"],
        "Topo": ["설사/골수억제 교육", "발열 시 즉시 연락"],
    }

    def cls_from_moa(moa: str) -> str:
        s = (moa or "").lower()
        if "vegf" in s or "vegfr" in s: return "VEGF"
        if "her2" in s: return "HER2"
        if "mtor" in s: return "mTOR"
        if "parp" in s: return "PARP"
        if "tki" in s or "inhibitor" in s and any(k in s for k in ["egfr","alk","ret","trk","met","ros"]): return "TKI"
        if "anthracycline" in s: return "Anthracycline"
        if "taxane" in s: return "Taxane"
        if "platin" in s: return "Platinum"
        if "vinca" in s: return "Vinca"
        if "antimetabolite" in s: return "Antimetabolite"
        if "topo" in s: return "Topo"
        return ""

    def split_ae(ae: str):
        if not ae: return []
        # split by · or , or · bullets
        parts = re.split(r"[·•,;/]\s*|\s{2,}", ae)
        parts = [p.strip() for p in parts if p.strip()]
        return parts

    for key, rec in list(db.items()):
        if not isinstance(rec, dict): 
            continue
        if has_detail(rec):
            continue
        ae = (rec.get("ae") or "").strip()
        if not ae or "부작용 정보 필요" in ae:
            continue

        moa = rec.get("moa", "")
        cls = cls_from_moa(moa)
        parts = split_ae(ae)
        common = []
        serious = []
        call = []
        tips = []

        # classify parts
        for p in parts:
            # serious flags
            low = p.lower()
            is_serious = False
            for tag, kws in serious_kw.items():
                if any(k.lower() in low for k in kws):
                    is_serious = True
                    break
            if is_serious:
                serious.append(p)
            else:
                common.append(p)

        # generic "call now" rules
        if any("골수억제" in x or "호중구" in x for x in parts):
            call.append("38℃ 전후 발열/오한(발열성 호중구감소 의심)")
        if any(any(k in x for k in ["출혈","혈변","코피","혈소판"]) for x in parts):
            call.append("멈추지 않는 출혈·혈변/흑변")
        if any(any(k in x for k in ["설사","오심","구토"]) for x in parts):
            call.append("하루 이상 지속되는 심한 구토/설사·탈수")
        if any(any(k in x for k in ["호흡","폐렴","ILD"]) for x in parts):
            call.append("기침/호흡곤란·흉통·발열 동반 시")
        if any(any(k in x for k in ["심", "LVEF", "QT", "부정맥", "흉통"]) for x in parts):
            call.append("흉통·실신·심계항진")

        # class tips
        tips.extend(tip_by_class.get(cls, []))

        # remove dups
        def uniq(xs): 
            u=[]
            for x in xs:
                if x not in u: u.append(x)
            return u

        rec["ae_detail"] = {
            "common": uniq(common)[:8],
            "serious": uniq(serious)[:6],
            "tips": uniq(tips)[:6],
            "call": uniq(call)[:6],
        }

_prev_autogen = globals().get("ensure_onco_drug_db")
def ensure_onco_drug_db(db):
    if callable(_prev_autogen):
        try:
            _prev_autogen(db)
        except Exception:
            pass
    _autogen_ae_detail_for_all(db)
# === [/PATCH] ===

# === [PATCH 2025-10-22 KST] Cardiotoxicity detail reinforcement ===
def _reinforce_cardiotox_details(db: Dict[str, Dict[str, Any]]) -> None:
    def add(k, data):
        if k not in db or not isinstance(db[k], dict): 
            return
        rec = db[k]
        det = rec.get("ae_detail") if isinstance(rec.get("ae_detail"), dict) else {}
        for sec, items in data.items():
            if not items: 
                continue
            arr = list(det.get(sec, [])) if isinstance(det.get(sec), (list,tuple)) else []
            for it in items:
                if it not in arr:
                    arr.append(it)
            det[sec] = arr
        rec["ae_detail"] = det

    anthracycline_targets = ["Doxorubicin","Daunorubicin","Idarubicin"]
    anthracycline_add = {
        "serious": [
            "심기능저하(LVEF 감소/심부전) — 누적용량 관련",
            "심낭삼출/심낭염 드묾"
        ],
        "tips": [
            "누적용량 추적(도옥소루비신 환산)",
            "기저/주기적 심초음파(LVEF)",
            "고위험군: 덱스라조산(Dexrazoxane) 고려(센터 프로토콜)"
        ],
        "call": [
            "숨가쁨·밤에 숨차서 깸·발목부종·갑작스런 체중↑",
            "가슴 통증/압박감"
        ]
    }
    for k in anthracycline_targets + [x.lower() for x in anthracycline_targets]:
        add(k, anthracycline_add)

    her2_targets = ["Trastuzumab","Pertuzumab","T-DM1","Trastuzumab deruxtecan"]
    her2_add = {
        "serious": ["심기능저하(LVEF)"],
        "tips": ["기저/주기 심초음파(LVEF) — 보통 3개월 간격"],
        "call": ["숨가쁨·부종·갑작스런 체중↑"]
    }
    for k in her2_targets + [x.lower() for x in her2_targets]:
        add(k, her2_add)

    qtrisk_targets = ["Vandetanib","Selpercatinib","Pralsetinib","Osimertinib","Lapatinib","Entrectinib"]
    qt_add = {
        "serious": ["QT 연장/부정맥(드묾)"],
        "tips": ["기저/필요 시 ECG, 전해질(K≥4.0, Mg≥2.0) 보정"],
        "call": ["실신·심계항진·어지럼"]
    }
    for k in qtrisk_targets + [x.lower() for x in qtrisk_targets]:
        add(k, qt_add)

_prev_cardio = globals().get("ensure_onco_drug_db")
def ensure_onco_drug_db(db):
    if callable(_prev_cardio):
        try:
            _prev_cardio(db)
        except Exception:
            pass
    _reinforce_cardiotox_details(db)
# === [/PATCH] ===

# === [PATCH 2025-10-22 KST] KR key backfill for user-listed items ===
def _backfill_kr_keys_user_list(db: Dict[str, Dict[str, Any]]) -> None:
    MAP = {
        "카보잔티닙": ("Cabozantinib", "설사 · 손발증후군 · 고혈압 · 피로 · 구내염"),
        "크리조티닙": ("Crizotinib", "시야장애 · 설사/변비 · 부종 · 간효소↑ · 피로"),
        "투카티닙": ("Tucatinib", "설사 · 손발증후군 드묾 · 간효소↑"),
        "페메트렉시드": ("Pemetrexed", "피로 · 골수억제 · 발진 · 구내염 · 비타민B9/B12 보충 필요"),
        "폴라투주맙 베도틴": ("Polatuzumab Vedotin", "🩸 골수억제 · 말초신경병증 · 감염"),
        "프랄세티닙": ("Pralsetinib", "고혈압 · 간효소↑ · 변비/설사 · 피로 · 간질성폐질환 드묾"),
        "카보플라틴": ("Carboplatin", "🩸 골수억제(혈소판↓) · 🤢 오심/구토 · 알레르기반응(누적)"),
        "젬시타빈": ("Gemcitabine", "🩸 골수억제 · 발열 · 발진 · 간효소↑ · 폐독성 드묾"),
        "이리노테칸": ("Irinotecan", "💩 설사(급성/지연) · 골수억제 · 복통 · 탈모"),
        "옥살리플라틴": ("Oxaliplatin", "🧊 냉유발 감각이상 · 말초신경병증 · 오심/구토 · 설사 · 골수억제"),
        "엔트렉티닙": ("Entrectinib", "어지럼 · 체중증가 · 설사/변비 · 간효소↑ · QT 연장 드묾"),
        "시스플라틴": ("Cisplatin", "🛎️ 이독성 · 🔔 말초신경병증 · 🤢 중증 오심/구토 · 🧂 전해질 이상(Mg/K↓) · 신독성"),
        "소토라십": ("Sotorasib", "설사 · 오심 · 간효소↑ · 피로"),
        "셀퍼카티닙": ("Selpercatinib", "고혈압 · 간효소↑ · QT 연장 · 변비/설사"),
        "빈블라스틴": ("Vinblastine", "골수억제 · 변비 · 말초신경병증"),
        "브렌툭시맙 베도틴": ("Brentuximab Vedotin", "🧠 말초신경병증 · 피로 · 오심 · 혈구감소"),
        "반데타닙": ("Vandetanib", "QT 연장 · 설사 · 발진 · 갑상선기능저하"),
        "로를라티닙": ("Lorlatinib", "💭 인지/기분 변화 · 지질↑ · 체중↑ · 말초부종"),
        "라로트렉티닙": ("Larotrectinib", "어지럼 · 피로 · 간효소↑ · 체중증가"),
        "도세탁셀": ("Docetaxel", "🖐️ 손발부종/무감각 · 🩸 골수억제 · 발열성 호중구감소증 · 손발톱 변화 · 체액저류"),
        "닥티노마이신": ("Dactinomycin", "💊 점막염 · 오심/구토 · 골수억제 · 피부괴사(누출 시)"),
        "다카바진": ("Dacarbazine", "🤢 심한 오심/구토 · 광과민 · 골수억제"),
        "Ibrutinib": ("Ibrutinib", "출혈위험 · 심방세동 · 설사 · 감염"),
        "ibrutinib (Ibrutinib)": ("Ibrutinib", "출혈위험 · 심방세동 · 설사 · 감염"),
        "dactinomycin (Dactinomycin)": ("Dactinomycin", "💊 점막염 · 오심/구토 · 골수억제 · 피부괴사(누출 시)"),
        "dacarbazine (Dacarbazine)": ("Dacarbazine", "🤢 심한 오심/구토 · 광과민 · 골수억제"),
    }
    for kr, (eng, ae) in MAP.items():
        base = db.get(eng, {})
        alias = kr
        moa = base.get("moa","") if isinstance(base, dict) else ""
        _upsert(db, kr, alias, moa, ae)
        # also create composite both ways
        comp1 = f"{eng} ({kr})"
        comp2 = f"{kr} ({eng})"
        _upsert(db, comp1, alias, moa, ae)
        _upsert(db, comp2, alias, moa, ae)

_prev_krfill = globals().get("ensure_onco_drug_db")
def ensure_onco_drug_db(db):
    if callable(_prev_krfill):
        try:
            _prev_krfill(db)
        except Exception:
            pass
    _backfill_kr_keys_user_list(db)
# === [/PATCH] ===

# === [PATCH 2025-10-22 KST] Ara-C HDAC cardiopericardial note ===
def _arac_hdac_cardiopericard_detail(db: Dict[str, Dict[str, Any]]) -> None:
    targets = ["Ara-C HDAC","Cytarabine HDAC"]
    add_serious = ["심장: 심낭염/심낭삼출 드묾(흉통·호흡곤란)"]
    add_tips    = ["HDAC에서 흉통·호흡곤란 발생 시 즉시 보고", "증상 시 ECG/효소(Troponin) 평가 고려(센터 프로토콜)"]
    add_call    = ["가슴 통증·압박감, 숨가쁨·누우면 더 힘듦(심낭삼출 의심)"]
    for key in targets:
        if key in db and isinstance(db[key], dict):
            rec = db[key]
            det = rec.get("ae_detail") if isinstance(rec.get("ae_detail"), dict) else {}
            for sec, arr in [("serious", add_serious), ("tips", add_tips), ("call", add_call)]:
                cur = list(det.get(sec, [])) if isinstance(det.get(sec), (list,tuple)) else []
                for it in arr:
                    if it not in cur:
                        cur.append(it)
                det[sec] = cur
            rec["ae_detail"] = det

_prev_arac_cardio = globals().get("ensure_onco_drug_db")
def ensure_onco_drug_db(db):
    if callable(_prev_arac_cardio):
        try:
            _prev_arac_cardio(db)
        except Exception:
            pass
    _arac_hdac_cardiopericard_detail(db)
# === [/PATCH] ===

# === [PATCH 2025-10-22 KST] Ensure Ara-C formulation keys exist ===
def _ensure_arac_formulations(db: Dict[str, Dict[str, Any]]) -> None:
    base = db.get("Cytarabine") or db.get("Ara-C") or {}
    moa  = base.get("moa","") if isinstance(base, dict) else "Antimetabolite (pyrimidine analog)"
    alias = base.get("alias","시타라빈(Ara-C)") if isinstance(base, dict) else "시타라빈(Ara-C)"
    # Common AE
    common = "🩸 골수억제 · 🤢 오심/구토 · 💊 점막염 · 👁️ 결막염(점안 예방)"
    # Form-specific notes
    hdac_note = " · 🧠 소뇌독성(고용량) · 발열/발진"
    iv_note   = " · 주입 관련 오심/구토 관리 필요"
    sc_note   = " · 주사부위 통증/발적 가능"
    entries = {
        "Ara-C IV": (alias, moa, common + iv_note),
        "Ara-C SC": (alias, moa, common + sc_note),
        "Ara-C HDAC": (alias, moa, common + hdac_note),
        "Cytarabine IV": (alias, moa, common + iv_note),
        "Cytarabine SC": (alias, moa, common + sc_note),
        "Cytarabine HDAC": (alias, moa, common + hdac_note),
    }
    for k, (al, m, ae) in entries.items():
        _upsert(db, k, al, m, ae)

_prev_arac_forms = globals().get("ensure_onco_drug_db")
def ensure_onco_drug_db(db):
    if callable(_prev_arac_forms):
        try:
            _prev_arac_forms(db)
        except Exception:
            pass
    _ensure_arac_formulations(db)
# === [/PATCH] ===



# === [PATCH 2025-10-25 KST] AE plain-language summaries injection ===
def _set_plain(rec, text):
    if not isinstance(rec, dict):
        return
    # use both keys for flexibility
    if not rec.get("ae_plain"):
        rec["ae_plain"] = text
    if not rec.get("plain"):
        rec["plain"] = text

def _inject_plain_20251025(db: Dict[str, Dict[str, Any]]) -> None:
    # Key drug plain-language AE summaries (Korean, caregiver-friendly).
    plain = {
        # Heme
        "Vyxeos": "강한 항암제 조합이라 감염 위험이 크고(열나면 바로 연락), 입안염·피곤함이 흔해요. 심장검사(Echo)가 필요할 수 있어요.",
        "Venetoclax": "암세포가 빨리 녹으면서 혈액수치가 급변할 수 있어요(TLS). 물 많이 마시고, 피검사를 자주 해요.",
        "Gilteritinib": "심전도(QT)·간수치·설사/변비를 체크해요. 어지럼/두근거림이 지속되면 알려주세요.",
        "Midostaurin": "메스꺼움·피부발진이 잦아요. 드물게 심전도 이상이 있어요—어지럼/실신 시 즉시 연락.",
        "Ivosidenib": "드물게 '분화증후군'이 올 수 있어요(갑자기 숨참, 열). 이런 증상이면 바로 병원.",
        "Enasidenib": "황달 느낌(눈·피부 노래짐)이나 숨참·열이 오면 연락(분화증후군 가능).",
        "Acalabrutinib": "멍/코피 등 출혈이 쉬울 수 있어요. 심장이 두근거리면(부정맥) 알려주세요.",
        "Zanubrutinib": "출혈·감염 주의. 가슴두근거림/어지럼이 계속되면 병원에 알려요.",
        "Idelalisib": "설사/복통이 심해지면 중단 후 연락(대장염 가능). 간수치·폐렴 증상도 체크.",
        "Lenalidomide": "피로·피부가려움·혈전 위험. 다리 붓고 아프거나 숨차면 즉시 연락.",
        "Carfilzomib": "숨참/다리붓기·가슴불편감 있으면 심장·혈압 확인 필요.",
        "Daratumumab": "초회 주입 때 열/기침이 있을 수 있어요. 감염 예방이 중요해요.",
        "Belantamab mafodotin": "눈이 뿌옇거나 따가우면 사용을 멈추고 안과 확인(각막 영향).",
        "Elotuzumab": "주입날 열감/기침이 있을 수 있어요. 전반적으로 감염 조심.",
        # Solid
        "Osimertinib": "설사·피부발진이 흔하고, 기침/숨참이 갑자기 심해지면 병원(폐렴증 가능).",
        "Amivantamab": "첫 투여 때 오한·열이 잦아요(주입반응). 피부·손발 관리 병행.",
        "Mobocertinib": "설사·발진 관리가 중요해요. 심전도 이상 드물게 있어요.",
        "Capmatinib": "발·다리 붓기와 간수치 상승이 잦아요.",
        "Tepotinib": "붓기와 메스꺼움. 크레아티닌 수치가 가짜로 오를 수 있어요.",
        "Sotorasib": "설사/피로·간수치 상승. 복통이 심하면 알려주세요.",
        "Adagrasib": "설사·피로. 간수치 확인이 필요해요.",
        "Trastuzumab deruxtecan": "메스꺼움·피로. 마른기침/숨참 등 폐렴증(ILD) 증상이면 즉시 연락.",
        "Trastuzumab emtansine": "피곤·멍이 잘 들 수 있어요(혈소판↓). 간수치도 가끔 올라요.",
        "Pertuzumab": "설사·피부증상. 드물게 심장기능이 떨어질 수 있어요.",
        "Tucatinib": "설사·간수치 상승. 증상 지속되면 상담.",
        "Palbociclib": "백혈구가 줄어 감염이 쉬워요. 열나면 바로 연락.",
        "Ribociclib": "감염 위험 + 드물게 심전도(QT) 이상. 심한 어지럼/실신은 즉시 연락.",
        "Abemaciclib": "설사가 잦아 수분 보충이 중요해요.",
        "Cetuximab": "여드름처럼 나는 피부발진이 흔해요. 보습/자외선차단 필수.",
        "Panitumumab": "피부·설사·저마그네슘. 마그네슘 보충 필요할 수 있어요.",
        "Encorafenib": "피부·관절통·피로. 피부 변화가 심하면 찍어두고 상담.",
        "Regorafenib": "손발바닥 통증/붉어짐(손발증후군)과 혈압 상승—보습·편한 신발·혈압 체크.",
        "Trifluridine/Tipiracil": "피로·백혈구감소. 감염 조심.",
        "Imatinib": "붓기·근육통·메스꺼움. 눈 주변이 붓기도 해요.",
        "Sunitinib": "혈압 상승·손발증후군. 소변 단백이 나오기도 해요.",
        "Ripretinib": "피로·탈모·근육통. 증상이 심하면 용량 조정 상담.",
        "Pemigatinib": "혈중 인이 올라 손발 저림/경련이 생길 수 있어요—혈액검사로 관리.",
        "Futibatinib": "고인산혈증 관리(식이/약). 손발 저림이 있을 수 있어요.",
        "Ivosidenib-Solid": "오심/설사·피로. 갑작스런 숨참/열은 바로 연락.",
        "Selpercatinib": "혈압·간수치 상승이 잦아요. 드물게 심전도 이상.",
        "Pralsetinib": "기침/호흡곤란·간수치 상승. 증상 지속 시 병원.",
        "Larotrectinib": "어지럼·피로·변비/설사. 낙상 주의.",
        "Lenvatinib": "혈압·단백뇨·손발증후군. 두통/코피 나면 알려주세요.",
        "Cabozantinib": "설사·손발증후군·피로. 상처 회복이 늦을 수 있어요.",
        "Axitinib": "혈압·설사·피로. 어지럼 시 앉아 쉬고 측정.",
        "Sorafenib": "손발증후군·설사·피로. 피부 갈라짐엔 보습제.",
        "Olaparib": "피로·빈혈. 어지럽고 창백하면 피검사 상담.",
        "Talazoparib": "빈혈·혈소판 감소. 멍이 잘 들면 알려주세요.",
        "Alpelisib": "혈당이 오르기 쉬워요. 갈증·소변 증가 시 혈당 확인.",
        "Enfortumab vedotin": "피부 발진·저림(신경). 혈당이 오를 수 있어요—목마름/자주 소변보면 확인.",
        "Sacituzumab govitecan": "백혈구감소·설사. 열나면 즉시 연락, 지사제 안내 따르기.",
        "Avapritinib": "붓기·혼동 등 인지 변화 가능—이상하면 바로 연락.",
        "Trilaciclib": "화학요법 전에 맞아 백혈구 감소를 줄여줘요. 주사 부위 통증 정도.",
    }
    for k, msg in plain.items():
        if k in db:
            _set_plain(db[k], msg)
        if k.lower() in db:
            _set_plain(db[k.lower()], msg)

_prev_plain_20251025 = globals().get("ensure_onco_drug_db")
def ensure_onco_drug_db(db):
    if callable(_prev_plain_20251025):
        try:
            _prev_plain_20251025(db)
        except Exception:
            pass
    _inject_plain_20251025(db)
# === [/PATCH] ===



# === [PATCH 2025-10-25 KST] Emergency bullets + care tips (heuristics) ===
def _list_add_unique(lst, items):
    seen = set(lst)
    for x in items:
        if x not in seen:
            lst.append(x); seen.add(x)

def _derive_emergency_from_text(ae_text: str):
    t = (ae_text or "").lower()
    out = []
    if any(k in t for k in ["발열", "열", "감염", "패혈", "호중구"]):
        out.append("🚨 38℃ 이상 열나면 즉시 연락/응급실")
    if any(k in t for k in ["호흡곤란", "숨", "ild", "폐렴", "간질성"]):
        out.append("🚨 기침/숨참이 갑자기 심해지면 즉시 연락")
    if any(k in t for k in ["qt", "부정맥", "심방세동", "심장", "가슴통", "가슴 통"]):
        out.append("🚨 심한 어지럼/실신/가슴통증·심계 시 즉시 연락")
    if any(k in t for k in ["설사", "대장염", "혈변"]):
        out.append("🚨 하루 6회 이상 설사·혈변/탈수 증상 시 즉시 연락")
    if any(k in t for k in ["출혈", "혈소판"]):
        out.append("🚨 멍이 잘 들거나 출혈 지속 시 즉시 연락")
    if any(k in t for k in ["간효소", "간독성", "황달", "alt", "ast", "빌리루빈"]):
        out.append("🚨 눈/피부 노래짐·짙은 소변·심한 피로 시 즉시 상담")
    if "tls" in t or "종양융해" in t:
        out.append("🚨 심한 구역/구토·근육경련·소변 감소 시 즉시 연락(TLS 가능)")
    if any(k in t for k in ["각막", "시력", "눈", "안과"]):
        out.append("🚨 시야 흐림·눈 통증·광선불편 시 즉시 연락(안과)")
    if any(k in t for k in ["주입반응", "crs"]):
        out.append("🚨 오한·고열·숨참·혈압저하 등 주입반응/CRS 의심 시 즉시 연락")
    return out

def _derive_care_tips_from_text(ae_text: str):
    t = (ae_text or "").lower()
    tips = []
    if any(k in t for k in ["발진", "피부"]):
        _list_add_unique(tips, ["🧴 보습", "☀️ 자외선차단"])
    if "손발증후군" in t or "손발" in t:
        _list_add_unique(tips, ["👟 편한신발", "🧴 보습 강화"])
    if "설사" in t:
        _list_add_unique(tips, ["💧 수분보충", "🥣 소량·자주식"])
    if any(k in t for k in ["고혈압", "혈압"]):
        _list_add_unique(tips, ["🩺 혈압체크", "🧂 염분과다 주의"])
    if "단백뇨" in t:
        _list_add_unique(tips, ["🧪 소변단백 체크"])
    if any(k in t for k in ["골수억제", "호중구", "감염"]):
        _list_add_unique(tips, ["🧼 손위생", "😷 군중 회피", "🌡️ 체온기록"])
    if "qt" in t:
        _list_add_unique(tips, ["📈 심전도 일정", "🧪 K/Mg 유지"])
    if "고혈당" in t:
        _list_add_unique(tips, ["🩸 혈당체크", "🥤 물 자주 마시기"])
    if any(k in t for k in ["부종", "붓기"]):
        _list_add_unique(tips, ["🦶 다리 올려 휴식"])
    if any(k in t for k in ["점막염", "구내염"]):
        _list_add_unique(tips, ["🪥 구강관리", "🍽️ 자극적 음식 피함"])
    if any(k in t for k in ["오심", "구토"]):
        _list_add_unique(tips, ["🍚 소량·자주 섭취"])
    if any(k in t for k in ["각막", "시력", "눈"]):
        _list_add_unique(tips, ["👁️ 인공눈물", "🚫 콘택트렌즈"])
    return tips

def _inject_emerg_and_tips_20251025(db: Dict[str, Dict[str, Any]]) -> None:
    for key, rec in db.items():
        if not isinstance(rec, dict): 
            continue
        ae_text = rec.get("ae") or ""
        # emergency bullets
        em = list(rec.get("plain_emergency", [])) if isinstance(rec.get("plain_emergency"), list) else []
        _list_add_unique(em, _derive_emergency_from_text(ae_text))
        if em:
            rec["plain_emergency"] = em
        # care tips
        tips = list(rec.get("care_tips", [])) if isinstance(rec.get("care_tips"), list) else []
        _list_add_unique(tips, _derive_care_tips_from_text(ae_text))
        if tips:
            rec["care_tips"] = tips

_prev_emerg_tips_20251025 = globals().get("ensure_onco_drug_db")
def ensure_onco_drug_db(db):
    if callable(_prev_emerg_tips_20251025):
        try:
            _prev_emerg_tips_20251025(db)
        except Exception:
            pass
    _inject_emerg_and_tips_20251025(db)
# === [/PATCH] ===



# === [PATCH 2025-10-25 KST] Fill MM agent fields (non-empty) ===
def _merge_nonempty(target: dict, src: dict):
    if not isinstance(target, dict) or not isinstance(src, dict):
        return
    for k, v in src.items():
        if k not in target or target.get(k) in (None, "", [], {}):
            target[k] = v

def _ensure_mm_nonempty_20251025(db: Dict[str, Dict[str, Any]]) -> None:
    entries = {
        "Carfilzomib": {
            "alias": "카르필조밉",
            "moa": "Proteasome inhibitor (PI)",
            "ae": "호흡곤란 · 가슴불편/심부전 · 고혈압 · 피로 · 오심",
            "monitor": ["BP", "Echo/LVEF(필요시)", "CBC", "Cr/eGFR"],
            "plain": "숨참·다리 붓기·가슴 불편감이 있으면 심장/혈압 확인이 필요해요.",
            "plain_emergency": ["🚨 가슴통증/심한 숨참/실신 시 즉시 연락"],
            "care_tips": ["🩺 혈압체크", "🦶 다리 올려 휴식", "💧 수분보충"],
        },
        "Daratumumab": {
            "alias": "다라투무맙",
            "moa": "anti-CD38 단클론 항체",
            "ae": "주입반응(열·기침·저혈압) · 감염 · 피로 · 빈혈",
            "monitor": ["Infection", "CBC"],
            "plain": "처음 투여 때 열/기침 등 주입반응이 있을 수 있어요. 감염 예방이 중요해요.",
            "plain_emergency": ["🚨 오한·고열·숨참/저혈압 등 주입반응 의심 시 즉시 연락"],
            "care_tips": ["😷 군중 회피", "🧼 손위생", "🌡️ 체온기록"],
        },
        "Ixazomib": {
            "alias": "익사조밉",
            "moa": "Proteasome inhibitor (경구)",
            "ae": "설사/오심 · 발진 · 말초신경병증 · 혈소판 감소",
            "monitor": ["CBC", "LFT", "Neuropathy sx"],
            "plain": "메스꺼움/설사·피부발진이 있을 수 있어요. 멍이 잘 들면 알리세요.",
            "plain_emergency": ["🚨 지속되는 심한 설사·혈변/탈수 시 즉시 연락"],
            "care_tips": ["💧 수분보충", "🧴 보습", "🍚 소량·자주 섭취"],
        },
        "Pomalidomide": {
            "alias": "포말리도마이드",
            "moa": "IMiD (면역조절제)",
            "ae": "혈전증 위험 · 호중구감소 · 피로 · 발진/가려움",
            "monitor": ["CBC", "Thrombosis risk"],
            "plain": "다리 붓고 아프거나 숨차면 혈전 의심—즉시 연락.",
            "plain_emergency": ["🚨 다리 통증·부종/갑작스런 흉통·호흡곤란 시 즉시 연락"],
            "care_tips": ["🚶 가벼운 운동", "🧦 압박스타킹(의사 지시 시)", "💧 수분"],
        },
    }
    for key, rec in entries.items():
        # ensure presence via _upsert if available
        try:
            _upsert(db, key, rec.get("alias",""), rec.get("moa",""), rec.get("ae",""))
            _upsert(db, key.lower(), rec.get("alias",""), rec.get("moa",""), rec.get("ae",""))
            _upsert(db, f"{key} ({rec.get('alias','')})", rec.get("alias",""), rec.get("moa",""), rec.get("ae",""))
            _upsert(db, f"{rec.get('alias','')} ({key})", rec.get("alias",""), rec.get("moa",""), rec.get("ae",""))
        except Exception:
            # fallback: create dict
            db.setdefault(key, {"alias": rec.get("alias",""), "moa": rec.get("moa",""), "ae": rec.get("ae","")})
        # merge non-empty extras
        for cand in (key, key.lower(), f"{key} ({rec.get('alias','')})", f"{rec.get('alias','')} ({key})"):
            if cand in db and isinstance(db[cand], dict):
                _merge_nonempty(db[cand], rec)

_prev_mm_nonempty_20251025 = globals().get("ensure_onco_drug_db")
def ensure_onco_drug_db(db):
    if callable(_prev_mm_nonempty_20251025):
        try:
            _prev_mm_nonempty_20251025(db)
        except Exception:
            pass
    _ensure_mm_nonempty_20251025(db)
# === [/PATCH] ===



# === [PATCH 2025-10-25 KST] GLOBAL AUGMENT: fill emojis/tips/emergency/plain for ALL drugs ===
def _norm_txt(x):
    return (x or "").strip()

def _has_emoji(s: str) -> bool:
    if not s: return False
    # basic check for any common emoji characters used in our cards
    return any(ch in s for ch in "🚨🧴☀️👟💧🩺🧪🧼😷🌡️📈🩸🦶🪥🍚👁️🚫")

# class-based defaults
_CLASS_DEFAULTS = [
    # tuples: (keyword in moa lower, emergency list, care tip emojis, plain suffix)
    ("btk", ["🚨 심한 어지럼/실신·가슴두근거림(부정맥) 시 즉시 연락",
             "🚨 코피/멍 등 출혈 지속 시 연락"],
     ["🩺 혈압체크"], "출혈·부정맥 주의가 필요해요."),
    ("pi3k", ["🚨 심한 설사/복통·혈변 시 즉시 연락", "🚨 발열·기침 등 감염 증상 시 바로 연락"],
     ["💧 수분보충", "🧴 보습"], "간수치/장염/감염에 주의가 필요해요."),
    ("bcl-2", ["🚨 구역·구토/근육경련·소변감소 등 TLS 의심 시 즉시 연락"],
     ["💧 수분보충"], "초기 용량증량 동안 TLS 예방이 중요해요."),
    ("flt3", ["🚨 심한 어지럼/실신(심전도 이상 의심) 시 즉시 연락"],
     ["📈 심전도 일정", "🧪 K/Mg 유지"], "심전도(QT)와 간수치 모니터가 필요해요."),
    ("idh", ["🚨 갑작스런 발열·호흡곤란 등 분화증후군 의심 시 즉시 연락"],
     ["💧 수분보충"], "분화증후군 가능성에 주의가 필요해요."),
    ("vegf", ["🚨 심한 두통·시야이상·고혈압 위기 시 즉시 연락"],
     ["🩺 혈압체크", "🧪 소변단백 체크", "🧴 보습"], "혈압·단백뇨·피부/손발 관리가 중요해요."),
    ("egfr", ["🚨 마른기침/숨참 악화(ILD 의심) 시 즉시 연락"],
     ["🧴 보습", "☀️ 자외선차단"], "피부/설사 관리와 드묾게 폐렴증(ILD)에 주의해요."),
    ("alk", ["🚨 혼동·말 어눌함·시야이상 등 신경학적 증상 시 즉시 연락"],
     ["🧴 보습"], "지질/간수치·신경계 증상 모니터가 필요해요."),
    ("parp", ["🚨 현기증·실신 수준의 빈혈 증상 시 연락"],
     ["💧 수분보충"], "빈혈·피로에 주의가 필요해요."),
    ("adc", ["🚨 첫 투여 시 오한·고열·호흡곤란(주입반응/CRS) 시 즉시 연락"],
     ["😷 군중 회피", "🧼 손위생"], "주입반응·감염 관리가 중요해요."),
    ("proteasome", ["🚨 흉통·심한 숨참/부종 시 즉시 연락"],
     ["🩺 혈압체크", "🦶 다리 올려 휴식"], "심혈관계·피로 증상에 주의가 필요해요."),
    ("immunomod", ["🚨 다리 통증·부종/갑작스런 흉통·호흡곤란(혈전) 시 즉시 연락"],
     ["🚶 가벼운 운동", "🧦 압박스타킹(지시 시)"], "혈전 예방과 감염 관리가 중요해요."),
]

def _class_defaults(moa: str):
    moa_l = (moa or "").lower()
    for key, em, tips, p in _CLASS_DEFAULTS:
        if key in moa_l:
            return em, tips, p
    return [], [], ""

def _squeeze_sentences(ae: str, limit=2):
    # extract 1~2 short sentences as plain if missing
    t = (ae or "").replace("\n"," ").replace("—"," ").replace("..",".").strip()
    parts = [s.strip(" ·-") for s in re.split(r"[.]", t) if s.strip()]
    return " ".join(parts[:limit]) if parts else ""

def _augment_all_drugs_20251025(db: Dict[str, Dict[str, Any]]) -> None:
    for k, rec in list(db.items()):
        if not isinstance(rec, dict): 
            continue
        alias = rec.get("alias") or ""
        moa   = rec.get("moa") or ""
        ae    = rec.get("ae") or ""
        # ensure AE exists minimally
        if not ae:
            # minimal AE by class
            _, _, p = _class_defaults(moa)
            rec["ae"] = p or "피로/오심 등 일반적 증상이 있을 수 있어요. 이상 시 의료진과 상의하세요."
            ae = rec["ae"]
        # plain summary
        if not rec.get("ae_plain") and not rec.get("plain"):
            em, tips, p = _class_defaults(moa)
            base = _squeeze_sentences(ae) or p
            if base:
                rec["ae_plain"] = base
                rec["plain"] = base
        # emergency bullets
        if not rec.get("plain_emergency"):
            # reuse earlier heuristic if defined
            try:
                em_list = _derive_emergency_from_text(ae)  # may exist from previous patch
            except Exception:
                em_list = []
            if not em_list:
                em_list, _, _p = _class_defaults(moa)
            if em_list:
                rec["plain_emergency"] = em_list
        # care tips
        if not rec.get("care_tips"):
            try:
                tips = _derive_care_tips_from_text(ae)
            except Exception:
                tips = []
            if not tips:
                _, tips, _p = _class_defaults(moa)
            if tips:
                rec["care_tips"] = tips
        # add emojis into AE if none present to make it visually scannable
        if not _has_emoji(rec.get("ae")):
            # lightweight emoji prefix by class
            if "설사" in ae or "diarr" in ae.lower():
                rec["ae"] = "💧 " + rec["ae"]
            elif "발진" in ae or "피부" in ae:
                rec["ae"] = "🧴 " + rec["ae"]
            elif "감염" in ae or "호중구" in ae:
                rec["ae"] = "😷 " + rec["ae"]
            elif "고혈압" in ae or "혈압" in ae:
                rec["ae"] = "🩺 " + rec["ae"]
            elif "심장" in ae or "부정맥" in ae or "qt" in ae.lower():
                rec["ae"] = "📈 " + rec["ae"]

_prev_global_augment_20251025 = globals().get("ensure_onco_drug_db")
def ensure_onco_drug_db(db):
    if callable(_prev_global_augment_20251025):
        try:
            _prev_global_augment_20251025(db)
        except Exception:
            pass
    _augment_all_drugs_20251025(db)
# === [/PATCH] ===



# === [HOTFIX 2025-10-25] Safe _squeeze_sentences override ===
def _squeeze_sentences(ae: str, limit=2):
    """Return a short plain-language snippet from AE text.
    Self-contained: attempts to import regex locally and falls back safely.
    """
    t = (ae or "").replace("\n", " ").replace("—", " ").replace("..", ".").strip()
    try:
        import re as _re
        parts = [s.strip(" ·-") for s in _re.split(r"[.?!]", t) if s.strip()]
    except Exception:
        parts = [s.strip(" ·-") for s in t.split(".") if s.strip()]
    return " ".join(parts[:limit]) if parts else ""
# === [/HOTFIX] ===
