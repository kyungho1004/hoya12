# -*- coding: utf-8 -*-
from typing import Dict, Any, List

DRUG_DB: Dict[str, Dict[str, Any]] = {}

def _upsert(db, key, alias, moa, ae):
    db.setdefault(key, {})
    db[key].update({"alias": alias, "moa": moa, "ae": ae})

# 안전한 최소 목록 (항암제/항생제 예시 + APL 코어)
def ensure_onco_drug_db(db: Dict[str, Dict[str, Any]]):
    items = [
        # APL/혈액암 코어
        ("Tretinoin", "트레티노인(ATRA)", "RARα 작용 — 분화 유도", 
         "분화증후군(DS) 위험: 발열·호흡곤란/저산소증·흉막/심막삼출·체중증가; 의심 즉시 **덱사메타손 10 mg IV q12h**"),
        ("Arsenic Trioxide", "산화비소(ATO)", "분화 유도/아포토시스", 
         "분화증후군(관리 동일), **QT 연장**(저K/저Mg 교정/ECG 모니터), 전해질 이상, 간효소 상승/피부발진"),
        ("Cytarabine", "시타라빈(Ara‑C)", "피리미딘 유사체(항대사제)", "골수억제, 발열, 점막염, 드물게 신경독성"),
        ("Daunorubicin", "다우노루비신", "Topo II 억제(안트라사이클린)", "심근독성(누적), 골수억제, 점막염"),
        ("Idarubicin", "이다루비신", "Topo II 억제(안트라사이클린)", "심근독성, 골수억제, 오심/구토"),
        ("MTX", "메토트렉세이트(MTX)", "DHFR 억제(항대사제)", "골수억제, 점막염, 간독성, 신장독성(고용량)"),
        ("6-MP", "6-머캅토퓨린(6-MP)", "퓨린 유사체(항대사제)", "골수억제, 간독성(상호작용 주의)"),
        # 항생제(발열성 호중구감소 공통)
        ("Piperacillin/Tazobactam", "피페라실린/타조박탐", "광범위 β‑lactam + 억제제", "알레르기/위장관, 나트륨 부하, 신기능에 따른 용량 조절"),
        ("Cefepime", "세페핌(4세대)", "4세대 세팔로스포린(녹농균)", "알레르기, **신경독성**(신부전)"),
        ("Meropenem", "메로페넴", "광범위 카바페넴", "알레르기, 드묾게 경련(신부전/중추질환)"),
        ("Vancomycin", "반코마이신", "G(+) 글리코펩타이드", "신독성, **Red man**(급속 주입), 청력독성 드묾; TDM 필요"),
        ("Levofloxacin", "레보플록사신", "퀴놀론", "힘줄염/파열, QT 연장, 광과민, 혈당 변동; 18세 미만 주의"),
        ("Ceftazidime", "세프타지딤(3세대)", "3세대 세팔로스포린(녹농균)", "알레르기, 드묾게 신경독성"),
        ("TMP-SMX", "트리메토프림/설파메톡사졸", "엽산 대사 억제", "골수억제, 고칼륨혈증, 발진(SJS/TEN 드묾)"),
    ]
    for k, alias, moa, ae in items:
        _upsert(db, k, alias, moa, ae)

def display_label(key: str, db: Dict[str, Dict[str, Any]] = None) -> str:
    ref = db if isinstance(db, dict) else DRUG_DB
    entry = ref.get(key) or ref.get(str(key).strip().strip("'\""))
    if isinstance(entry, dict):
        alias = entry.get("alias")
        if alias and alias != key:
            return f"{key} ({alias})"
    return str(key)

def picklist(keys: List[str], db: Dict[str, Dict[str, Any]] = None) -> List[str]:
    ref = db if isinstance(db, dict) else DRUG_DB
    out = []
    for k in (keys or []):
        out.append(display_label(k, ref))
    return out

def key_from_label(label: str) -> str:
    if not label: return ""
    pos = label.find(" (")
    return label[:pos] if pos > 0 else label
