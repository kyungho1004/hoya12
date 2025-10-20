
# -*- coding: utf-8 -*-
"""
drug_db.py (patched overlay v3.1)
- Non-breaking: keep _upsert/display_label/key_from_label/ensure_onco_drug_db API
- Stronger aliasing (Ara-C/AraC -> Cytarabine), no nested parentheses
- PROFILES overlay ensures AE shows for Cytarabine and others
"""

from __future__ import annotations
from typing import Dict, Any, List

ALIAS_FALLBACK: Dict[str,str] = {
    "5-FU": "5-플루오로우라실",
    "Capecitabine": "카페시타빈",
    "Ara-C": "시타라빈·Ara-C",
    "AraC": "시타라빈·Ara-C",
    "Cytarabine": "시타라빈·Ara-C",
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
    "Topotecan": "토포테칸",
    "Daunorubicin": "다우노루비신",
    "Idarubicin": "이다루비신",
    "MTX": "메토트렉세이트",
    "6-MP": "6-머캅토퓨린",
    "Nab-Paclitaxel": "나브-파클리탁셀",
    "Ado-trastuzumab emtansine": "트라스투주맙 엠탄신(T-DM1)",
    "ATRA": "트레티노인(ATRA)",
    "Arsenic Trioxide": "비소트리옥사이드(ATO)",
}

def _clean_alias_text(s: str) -> str:
    s = str(s or "").strip()
    # avoid nested parentheses in labels
    return s.replace("(", " ").replace(")", " ")

def display_label(key: str, db: Dict[str, Dict[str, Any]]|None=None) -> str:
    ref = db if isinstance(db, dict) else {}
    alias = ref.get(key, {}).get("alias") if ref else None
    if not alias:
        alias = ALIAS_FALLBACK.get(key)
    if not alias:
        return str(key)
    alias = _clean_alias_text(alias)
    return f"{key} ({alias})" if alias and alias != key else str(key)

def picklist(keys, db=None):
    ref = db if isinstance(db, dict) else {}
    return [display_label(k, ref) for k in (keys or [])]

def key_from_label(label: str, db=None) -> str:
    """Robustly extract key from 'Drug (alias ...)' labels."""
    if not label:
        return ""
    # cut at first ' ('
    pos = label.find(" (")
    base = label[:pos] if pos > 0 else label
    ref = db if isinstance(db, dict) else {}
    if base in ref:
        return base
    # try by alias head (before '·')
    for k, rec in ref.items():
        if not isinstance(rec, dict): 
            continue
        alias = str(rec.get("alias",""))
        head = alias.split("·")[0].strip()
        if head and head == base:
            return k
    return base

def _upsert(db: Dict[str, Dict[str, Any]], key: str, alias: str, moa: str, ae: str, *, tags: List[str]|None=None):
    db.setdefault(key, {})
    rec = db[key]
    rec.update({"alias": alias, "moa": moa, "ae": ae})
    if tags:
        rec.setdefault("tags", [])
        for t in tags:
            if t not in rec["tags"]:
                rec["tags"].append(t)
    # mirror lowercase access
    db.setdefault(key.lower(), rec)

PROFILES: Dict[str, Dict[str, Any]] = {
    "Cytarabine": {"moa": "항대사제", "ae": "🩸 골수억제 · 발열 · 발진 · 결막염(고용량)"},
    "Imatinib": {"moa": "TKI (BCR-ABL, KIT)", "ae": "💧 부종 · 🥵 피로 · 🩸 골수억제 · 속쓰림/구역"},
    "5-FU": {"moa": "피리미딘 유사체(항대사제)", "ae": "🩸 골수억제 · 🤢 오심/구토 · 💩 설사 · 💊 구내염 · 🖐️ 손발증후군"},
    "Capecitabine": {"moa": "5-FU 전구약물(항대사제)", "ae": "🖐️ 손발증후군 · 💩 설사 · 💊 구내염 · 🩸 골수억제"},
    "Doxorubicin": {"moa": "안트라사이클린", "ae": "❤️ 심근독성(누적) · 🩸 골수억제 · 💊 점막염"},
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
    "Nivolumab": {"moa": "PD-1 억제제", "ae": "면역관련 이상반응(대장염/간염/피부/내분비)"},
    "Pembrolizumab": {"moa": "PD-1 억제제", "ae": "면역관련 이상반응(대장염/간염/피부/내분비)"},
    "Bevacizumab": {"moa": "VEGF 억제", "ae": "🩸 출혈 · 고혈압 · 단백뇨 · 상처치유 지연"},
    "Ramucirumab": {"moa": "VEGFR-2 억제", "ae": "🩸 출혈 · 고혈압 · 단백뇨"},
    "Regorafenib": {"moa": "멀티 TKI", "ae": "🖐️ 손발증후군 · 피로 · 고혈압"},
    "Ripretinib": {"moa": "KIT/PDGFRA 억제", "ae": "🧑‍🦲 탈모 · 피로 · 손발증후군"},
    "Everolimus": {"moa": "mTOR 억제", "ae": "🫁 ILD/폐렴 · 🩸 대사이상(혈당/지질) · 💊 구내염"},
    "Rituximab": {"moa": "CD20 항체", "ae": "💉 주입반응 · 감염위험 · HBV 재활성 경고"},
    "Octreotide": {"moa": "Somatostatin 유사체", "ae": "💩 지방변/설사 · 복부불편감 · 담석"},
    "Prednisone": {"moa": "코르티코스테로이드", "ae": "😠 기분변화 · 🍽️ 식욕↑/체중↑ · 혈당↑ · 불면"},
}

PLACEHOLDER_AE = "부작용 정보 필요"

def ensure_onco_drug_db(db: Dict[str, Dict[str, Any]]):
    if not isinstance(db, dict):
        return

    base_keys = [
        "5-FU","Alectinib","Ara-C","Bendamustine","Bevacizumab","Bleomycin","Brentuximab Vedotin",
        "Cabozantinib","Capecitabine","Capmatinib","Carboplatin","Chlorambucil","Cisplatin","Crizotinib",
        "Cyclophosphamide","Dacarbazine","Dactinomycin","Docetaxel","Doxorubicin","Entrectinib","Etoposide",
        "Everolimus","Gemcitabine","Ibrutinib","Ifosfamide","Imatinib","Irinotecan","Lapatinib","Larotrectinib",
        "Lorlatinib","Nivolumab","Obinutuzumab","Octreotide","Osimertinib","Oxaliplatin","Paclitaxel","Pazopanib",
        "Pembrolizumab","Pemetrexed","Pertuzumab","Polatuzumab Vedotin","Pralsetinib","Prednisone","Ramucirumab",
        "Regorafenib","Ripretinib","Rituximab","Selpercatinib","Sotorasib","Sunitinib","T-DM1","Trabectedin",
        "Topotecan","Daunorubicin","Idarubicin","Cytarabine","MTX","6-MP","Nab-Paclitaxel","Ado-trastuzumab emtansine", "ATRA","Arsenic Trioxide"]
    for k in base_keys:
        alias = db.get(k, {}).get("alias") or ALIAS_FALLBACK.get(k, k)
        db.setdefault(k, {"alias": alias, "moa": "", "ae": PLACEHOLDER_AE})

    # overlay profiles
    for k, prof in PROFILES.items():
        rec = db.setdefault(k, {})
        rec.update(prof)

    # alias mirroring (Canon <- alias)
    alias_map = {
        "bendamustine": "Bendamustine",
        "bleomycin": "Bleomycin",
        "베바시주맙": "Bevacizumab",
        "시타라빈": "Cytarabine",
        "AraC": "Cytarabine",
        "Ara-C": "Cytarabine",
        "Nab-Paclitaxel": "Paclitaxel",
        "Ado-trastuzumab emtansine": "T-DM1",
        "T-DXd": "Trastuzumab deruxtecan",
    }
    for alt, canon in alias_map.items():
        # Point aliases to the canonical dict (true mirror)
        db[alt] = db[canon]
        db[alt.lower()] = db[canon]

    # make quick access by Korean head of alias (before '·')
    for k, rec in list(db.items()):
        if not isinstance(rec, dict): continue
        alias = str(rec.get("alias","")).strip()
        if not alias: continue
        head = alias.split("·")[0].strip()
        if head:
            db.setdefault(head, rec)
            db.setdefault(head.lower(), rec)
