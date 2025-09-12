# -*- coding: utf-8 -*-
from typing import Dict, Any

DRUG_DB: Dict[str, Dict[str, Any]] = {}

def _upsert(db, key, alias, moa, ae):
    db.setdefault(key, {})
    db[key].update({"alias": alias, "moa": moa, "ae": ae})
    for alt in {key, key.lower(), alias, alias.lower()}:
        db.setdefault(alt, {"alias": alias, "moa": moa, "ae": ae})

def ensure_onco_drug_db(db: Dict[str, Dict[str, Any]]):
    # ===== 핵심 항암제 (부작용 보강) =====
    _upsert(db, "ATRA", "트레티노인(ATRA)", "RARα 작용 — 분화 유도",
            "분화증후군(호흡곤란·부종·저혈압 가능), 간효소 상승, 두통/피부건조")
    _upsert(db, "Arsenic Trioxide", "산화비소(ATO)", "분화 유도/아포토시스",
            "분화증후군, QT 연장, 전해질 이상(저K/저Mg)")
    _upsert(db, "Cytarabine", "시타라빈(Ara-C)", "피리미딘 유사체(항대사제)",
            "골수억제, 발열, 점막염, (고용량) 소뇌독성/혼미")
    _upsert(db, "MTX", "메토트렉세이트(MTX)", "DHFR 억제(항대사제)",
            "골수억제, 점막염, 간독성, (고용량) 신장독성 — 수액/요알칼리화 필요")
    _upsert(db, "6-MP", "6-머캅토퓨린(6-MP)", "퓨린 유사체(항대사제)",
            "골수억제, 간독성(알로푸리놀/메토트렉세이트 등 상호작용 주의)")
    _upsert(db, "Doxorubicin", "독소루비신(Adriamycin)", "Topo II 억제(안트라사이클린)",
            "심근독성(누적 용량 의존), 골수억제, 점막염, 탈모")
    _upsert(db, "Cyclophosphamide", "사이클로포스파미드", "알킬화제",
            "골수억제, 오심/구토, 출혈성 방광염(수분섭취/메스나)")
    _upsert(db, "Ifosfamide", "이포스파미드", "알킬화제",
            "뇌병증, 신장독성, 출혈성 방광염(메스나 병용)")
    _upsert(db, "Cisplatin", "시스플라틴", "백금계(교차결합)",
            "신독성, 오심/구토, 신경병증, 이독성(난청)")
    _upsert(db, "Oxaliplatin", "옥살리플라틴", "백금계(교차결합)",
            "말초신경병증(한랭유발), 구역/구토")
    _upsert(db, "Paclitaxel", "파클리탁셀", "미세소관 안정화",
            "말초신경병증, 골수억제, 탈모, 과민반응")
    _upsert(db, "Irinotecan", "이리노테칸", "Topo I 억제",
            "설사(조기 콜린성/지연성), 골수억제")
    _upsert(db, "Bleomycin", "블레오마이신", "DNA 절단 유도",
            "폐섬유화(누적), 발열/피부반응")
    _upsert(db, "Rituximab", "리툭시맙(CD20)", "CD20 단일클론항체",
            "주입반응, 감염위험, HBV 재활성화")

    # ===== 항생제 (부작용 강조 보강) =====
    _upsert(db, "Vancomycin", "반코마이신", "G(+) 당원질 억제",
            "적색인자(주입속도 관련), 신부전(AKI), 드물게 청력저하")
    _upsert(db, "Linezolid", "리네졸리드", "G(+) 단백합성 억제(50S)",
            "골수억제(특히 혈소판↓), 시신경염/시력저하(장기복용), 세로토닌증후군 위험")
    _upsert(db, "Daptomycin", "다프토마이신", "G(+) 세포막 탈분극",
            "CPK 상승/근육통(스타틴 병용 주의), 호산구성 폐렴 드묾")
    _upsert(db, "Cefepime", "세페핌", "4세대 세팔로스포린",
            "신부전 시 축적→신경독성(혼동/경련), 설사")
    _upsert(db, "Piperacillin/Tazobactam", "피페라실린/타조박탐", "BL/BLI",
            "저칼륨혈증, 신장기능 악화 가능, 발진/설사")
    _upsert(db, "Meropenem", "메로페넴", "카바페넴",
            "경련 드묾(고용량/신부전), 설사, C. difficile 위험")
    _upsert(db, "Imipenem/Cilastatin", "이미페넴/실라스타틴", "카바페넴",
            "경련 위험 상대적 증가, 오심/구토")
    _upsert(db, "Aztreonam", "아즈트레오남", "항-그람음성 단백합성 억제",
            "발진, 간효소 상승, 드물게 호흡기 증상")
    _upsert(db, "Amikacin", "아미카신", "아미노글리코사이드",
            "이독성/신독성(혈중농도 모니터링 필요)")
    _upsert(db, "Levofloxacin", "레보플록사신", "플루오로퀴놀론",
            "힘줄병증/파열, QT 연장, 말초/중추신경계 증상, 저혈당/고혈당 변동")
    _upsert(db, "TMP-SMX", "트리메토프림/설파메톡사졸", "엽산 길항",
            "고칼륨혈증, 범혈구감소, 과민반응(SJS/TEN) 드묾")
    _upsert(db, "Metronidazole", "메트로니다졸", "DNA 절단",
            "금주 필요(알코올과 병용 시 반응), 말초신경병증 드묾, 입금속맛/오심")
    _upsert(db, "Amoxicillin/Clavulanate", "아모키실린/클라불란산", "BL/BLI",
            "담즙정체성 간염 드묾, 설사/발진")

    # 표적치료/면역은 필요 시 앱에서 계속 확장
    # (필요 약물은 app에서 display_label()만으로도 보일 수 있도록 alias 구성)

def picklist(keys):
    return [display_label(k) for k in keys]

def key_from_label(label: str) -> str:
    if not label: return ""
    pos = label.find(" (")
    return label[:pos] if pos > 0 else label

def display_label(key: str, db: dict = None) -> str:
    ref = db if isinstance(db, dict) else DRUG_DB
    k = key if isinstance(key, str) else str(key)
    norm = k.strip().strip("'\"")
    entry = ref.get(norm) or ref.get(k)
    if isinstance(entry, dict):
        return entry.get("alias") or norm
    return norm
