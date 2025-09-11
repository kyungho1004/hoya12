# -*- coding: utf-8 -*-
from typing import Dict, Any

DRUG_DB: Dict[str, Dict[str, Any]] = {}

def _upsert(db, key, alias, moa, ae):
    db.setdefault(key, {})
    db[key].update({"alias": alias, "moa": moa, "ae": ae})
    # tolerant lookups
    for alt in {key, key.lower(), alias, alias.lower()}:
        db.setdefault(alt, {"alias": alias, "moa": moa, "ae": ae})

def ensure_onco_drug_db(db: Dict[str, Dict[str, Any]]):
    if db is None: return
    # Hematology core
    _upsert(db, "ATRA", "트레티노인(베사노이드, ATRA)",
            "RARα 수용체 작용 → APL 분화 유도",
            "분화증후군, 두통, 피부/점막 건조·발진, 구내염, 간효소 상승, 고중성지방혈증·췌장염, 두개내압 상승, 임신 금기")
    _upsert(db, "Arsenic Trioxide", "삼산화비소(ATO)",
            "PML-RARα 분해", "QT 연장, 분화증후군")
    _upsert(db, "Idarubicin", "이다루비신", "Topo II 억제", "심독성, 골수억제")
    _upsert(db, "Daunorubicin", "다우노루비신", "Topo II 억제/유리기", "심독성, 골수억제")
    _upsert(db, "Ara-C", "시타라빈(Ara‑C)", "시티딘 유사체", "골수억제, 결막염, 소뇌증상(고용량)")
    _upsert(db, "MTX", "메토트렉세이트(MTX)", "DHF 환원효소 억제", "골수억제, 간독성, 점막염/구내염, 신독성(고용량)")
    _upsert(db, "6-MP", "6‑머캅토퓨린(6‑MP)", "푸린 대사 교란", "골수억제, 간독성; TPMT/NUDT15 관련 독성")
    _upsert(db, "Vincristine", "빈크리스틴", "미세소관 억제", "말초신경병증, 변비/장폐색")
    _upsert(db, "Cyclophosphamide", "사이클로포스파마이드", "알킬화제", "골수억제, 출혈성 방광염(수분/메스나)")
    _upsert(db, "Prednisone", "프레드니손", "글루코코르티코이드", "혈당상승, 불면, 감염 위험")

    # Solid tumor + targeted
    _upsert(db, "Cisplatin", "시스플라틴", "백금계 교차결합", "신독성, 이독성/청력저하, 오심/구토, 말초신경병증")
    _upsert(db, "Carboplatin", "카보플라틴", "백금계", "골수억제, 오심/구토")
    _upsert(db, "Oxaliplatin", "옥살리플라틴", "백금계", "말초신경병증(냉자극성)")
    _upsert(db, "5-FU", "플루오로우라실(5‑FU)", "DNA/RNA 합성 억제", "구내염/설사, 수족증후군, 골수억제")
    _upsert(db, "Capecitabine", "카페시타빈", "경구 5‑FU 전구약물", "수족증후군, 설사/구내염, 피로")
    _upsert(db, "Irinotecan", "이리노테칸", "Topo I 억제", "설사(급성/지연), 골수억제")
    _upsert(db, "Docetaxel", "도세탁셀", "미세소관 안정화", "무과립구증, 부종/체액저류, 손발톱 변화")
    _upsert(db, "Paclitaxel", "파클리탁셀", "미세소관 안정화", "말초신경병증, 과민반응(전처치), 골수억제")
    _upsert(db, "Gemcitabine", "젬시타빈", "핵산합성 억제", "골수억제, 피로, 발열")
    _upsert(db, "Pemetrexed", "페메트렉시드", "엽산경로 억제", "골수억제, 발진; 엽산/B12 보충")
    _upsert(db, "Temozolomide", "테모졸로마이드", "알킬화제", "골수억제")
    _upsert(db, "Imatinib", "이매티닙", "BCR‑ABL/c‑KIT/PDGFR TKI", "부종, 발진, 간효소 상승, 골수억제")
    _upsert(db, "Osimertinib", "오시머티닙(EGFR)", "EGFR TKI", "설사/발진, ILD 드묾, QT 연장")
    _upsert(db, "Alectinib", "알렉티닙", "ALK 억제", "근병증, 변비")
    _upsert(db, "Crizotinib", "크리조티닙", "ALK/ROS1 억제", "시야장애, 오심")
    _upsert(db, "Larotrectinib", "라로트렉티닙", "TRK 억제", "어지러움, 간효소 상승")
    _upsert(db, "Entrectinib", "엔트렉티닙", "TRK/ROS1/ALK 억제", "체중증가, 어지러움")
    _upsert(db, "Trastuzumab", "트라스투주맙(HER2)", "HER2 단일클론항체", "심기능저하(LVEF 감소), 주입반응")
    _upsert(db, "Bevacizumab", "베바시주맙(VEGF)", "VEGF 억제", "고혈압, 단백뇨, 상처치유 지연/출혈")
    _upsert(db, "Sorafenib", "소라페닙", "멀티 TKI(HCC/RCC)", "수족증후군, 고혈압")
    _upsert(db, "Lenvatinib", "렌바티닙", "멀티 TKI(HCC/갑상선)", "고혈압, 피로")
