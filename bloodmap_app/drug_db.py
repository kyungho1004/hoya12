# -*- coding: utf-8 -*-
"""
drug_db.py
----------
Centralized oncology drug database and normalizer utilities.
- DRUG_DB: canonical store (keyed by short code or common name)
- ensure_onco_drug_db(): upserts core drugs with alias/MOA/AEs
"""

from typing import Dict, Any

DRUG_DB: Dict[str, Dict[str, Any]] = {}


def _upsert(db: Dict[str, Dict[str, Any]], key: str, alias: str, moa: str, ae: str) -> None:
    db.setdefault(key, {})
    db[key].update({"alias": alias, "moa": moa, "ae": ae})
    # convenience aliases for tolerant lookups
    for alt in {key, alias, alias.lower(), key.lower()}:
        db.setdefault(alt, {"alias": alias, "moa": moa, "ae": ae})


def ensure_onco_drug_db(db: Dict[str, Dict[str, Any]]) -> None:
    """
    Upsert side effects for key drugs (caregiver-friendly wording).
    """
    if db is None:
        return

    # ATRA (Vesanoid, Tretinoin) — include skin/mucosal disorders
    _upsert(
        db,
        "ATRA",
        "트레티노인(베사노이드, ATRA)",
        "RARα 수용체 작용 → APL 미성숙 전골수구 분화 유도",
        "분화증후군(발열/호흡곤란/부종/저혈압), 두통, 피부/점막 건조·발진, 구내염, "
        "간효소 상승/간독성, 고중성지방혈증·췌장염, 두개내압 상승(가성 뇌종양; "
        "테트라사이클린계 병용 시 위험↑), 임신 금기(기형 유발)"
    )

    # Methotrexate
    _upsert(
        db,
        "MTX",
        "메토트렉세이트(MTX)",
        "DHF 환원효소 억제 → 엽산 대사 차단(항대사제)",
        "골수억제(백혈구/혈소판 감소), 간독성(AST/ALT 상승), 구내염/점막염, 탈수 시 신독성(특히 고용량), "
        "폐독성(기침/호흡곤란), 광과민, 약물상호작용(NSAIDs, TMP-SMX 등)"
    )

    # 6-Mercaptopurine
    _upsert(
        db,
        "6-MP",
        "6-머캅토퓨린(6‑MP)",
        "푸린 대사 교란 → DNA 합성 억제(항대사제)",
        "골수억제, 간독성/담즙정체, 구역/구토, 구내염, 발진; "
        "TPMT/NUDT15 결핍 시 심한 독성 가능(용량조절 필요)"
    )

    # Cytarabine (Ara-C)
    _upsert(
        db,
        "Ara-C",
        "시타라빈(Ara‑C)",
        "시티딘 유사체(항대사제) → DNA 중합 억제",
        "골수억제(호중구/혈소판 감소), 발열/오한, 구내염/설사, 결막염(점안제 예방), "
        "소뇌실조/진정(고용량 HDAC), 손발 붓기/발진"
    )

    # G-CSF (Filgrastim)
    _upsert(
        db,
        "G-CSF",
        "필그라스팀(G‑CSF)",
        "과립구 콜로니 자극인자 → 호중구 회복 촉진",
        "골통/등·골반 통증, 백혈구증가, 드물게 비장 비대/파열, 과민반응, "
        "급성호흡곤란증후군(드묾), 겸상적혈구병 악화 가능"
    )

    # Imatinib (targeted)
    _upsert(
        db,
        "Imatinib",
        "이매티닙",
        "BCR‑ABL, c‑KIT, PDGFR 티로신키나제 억제제",
        "부종/체액저류, 오심/구토/설사, 발진, 근육경련, 간효소 상승, 골수억제"
    )

    # R-CHOP components (chemo subset)
    _upsert(
        db,
        "Cyclophosphamide",
        "사이클로포스파마이드",
        "알킬화제 → DNA 교차결합",
        "골수억제, 오심/구토, 탈모, 출혈성 방광염(수분섭취/메스나), 감염 위험"
    )
    _upsert(
        db,
        "Doxorubicin",
        "독소루비신(아드리아마이신)",
        "안트라사이클린 → 토포이소머레이스 II 억제/유리기 생성",
        "심근독성(누적용량), 골수억제, 점막염/탈모, 홍색뇨(일시적)"
    )
    _upsert(
        db,
        "Vincristine",
        "빈크리스틴",
        "미세소관 중합 억제(방추사 억제)",
        "말초신경병증(저림/무력), 변비/장폐색, 턱통증; 골수억제 상대적으로 약함"
    )
    _upsert(
        db,
        "Prednisone",
        "프레드니손",
        "글루코코르티코이드 → 림프구성 종양 세포사 촉진",
        "혈당상승, 불면/기분변화, 위장관 자극, 감염 위험 증가, 부종"
    )

    # Solid tumor examples
    _upsert(
        db,
        "Cisplatin",
        "시스플라틴",
        "백금계 → DNA 가닥 교차결합",
        "오심/구토 심함, 신독성(수액), 이독성/청력저하, 말초신경병증, 전해질 이상(저Mg)"
    )
    _upsert(
        db,
        "Pemetrexed",
        "페메트렉시드",
        "다중 엽산경로 억제(항대사제)",
        "골수억제, 피로, 발진, 구역/구토; 엽산/비타민 B12 보충 필요"
    )
