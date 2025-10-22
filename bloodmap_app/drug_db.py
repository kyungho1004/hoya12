
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
