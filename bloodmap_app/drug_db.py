# -*- coding: utf-8 -*-
"""
drug_db.py
- 약물(항암제/항생제) 한-영 매핑과 설명 DB
- UI 표시는 기본 "영문,한글" 형식을 사용 (예: "Cefepime,세페핌")
- 외부에서 DRUG_DB를 보강하려면 ensure_onco_drug_db(DRUG_DB)를 호출
- 미승인(국제 기준 신약 후보 등)은 포함하지 않음
"""

from typing import Dict, Any, List, Optional

# ---------- Fallback Korean aliases (display only; DB alias 우선) ----------
ALIAS_FALLBACK: Dict[str, str] = {
    # Chemo (core & common)
    "Cytarabine": "시타라빈(Ara-C)",
    "Ara-C": "시타라빈(Ara-C)",
    "Daunorubicin": "다우노루비신",
    "Idarubicin": "이다루비신",
    "Doxorubicin": "독소루비신",
    "ATRA": "트레티노인(베사노이드)",
    "Tretinoin": "트레티노인(베사노이드)",
    "Vesanoid": "베사노이드(트레티노인)",
    "Arsenic Trioxide": "산화비소",
    "Methotrexate": "메토트렉세이트",
    "MTX": "메토트렉세이트",
    "6-MP": "6-머캅토퓨린",
    "Mercaptopurine": "6-머캅토퓨린",
    "Cyclophosphamide": "사이클로포스파마이드",
    "Prednisone": "프레드니손",
    "Prednisolone": "프레드니솔론",
    "Vincristine": "빈크리스틴",
    "Vinblastine": "빈블라스틴",
    "Bleomycin": "블레오마이신",
    "Etoposide": "에토포사이드",
    "Ifosfamide": "이포스파미드",
    "Gemcitabine": "젬시타빈",
    "Trabectedin": "트라벡테딘",
    "Dactinomycin": "닥티노마이신",
    "Dacarbazine": "다카르바진",
    "Bendamustine": "벤다무스틴",
    "Cisplatin": "시스플라틴",
    "Carboplatin": "카보플라틴",
    "Oxaliplatin": "옥살리플라틴",
    "Irinotecan": "이리노테칸",
    "Topotecan": "토포테칸",
    "Paclitaxel": "파클리탁셀",
    "Nab-Paclitaxel": "나브-파클리탁셀",
    "Docetaxel": "도세탁셀",
    "Capecitabine": "카페시타빈",
    "5-FU": "5-플루오로우라실",
    "Leucovorin": "류코보린(폴린산)",
    "Pemetrexed": "페메트렉시드",
    "Chlorambucil": "클로람부실",

    # Targeted / IO (selected, 승인 약물만)
    "Rituximab": "리툭시맙",
    "Obinutuzumab": "오비누투주맙",
    "Brentuximab Vedotin": "브렌툭시맙 베도틴",
    "Polatuzumab Vedotin": "폴라투주맙 베도틴",
    "Imatinib": "이매티닙",
    "Dasatinib": "다사티닙",
    "Nilotinib": "닐로티닙",
    "Trastuzumab": "트라스투주맙",
    "Pertuzumab": "퍼투주맙",
    "T-DM1": "트라스투주맙 엠탄신",
    "Trastuzumab deruxtecan": "트라스투주맙 데룩스테칸",
    "Everolimus": "에베로리무스",

    # G-CSF, etc.
    "G-CSF": "그라신(필그라스팀 등)",
    "Filgrastim": "필그라스팀(G-CSF)",
    "Pegfilgrastim": "페그필그라스팀(G-CSF)",

    # AML 신약(승인)
    "Revumenib": "레부메닙(Revuforj)",
    "Revuforj": "레부메닙(Revumenib)",

    # Common antibiotics (FN)
    "Piperacillin/Tazobactam": "피페라실린/타조박탐",
    "Pip/Tazo": "피페라실린/타조박탐",
    "Cefepime": "세페핌",
    "Ceftazidime": "세프타지딤",
    "Meropenem": "메로페넴",
    "Imipenem/Cilastatin": "이미페넴/실라스타틴",
    "Ertapenem": "에르타페넴",
    "Aztreonam": "아즈트레오남",
    "Amikacin": "아미카신",
    "Gentamicin": "겐타마이신",
    "Vancomycin": "반코마이신",
    "Linezolid": "리네졸리드",
    "Daptomycin": "답토마이신",
    "Levofloxacin": "레보플록사신",
    "Ciprofloxacin": "시프로플록사신",
    "TMP-SMX": "트리메토프림/설파메톡사졸",
    "Trimethoprim/Sulfamethoxazole": "트리메토프림/설파메톡사졸",
    "Metronidazole": "메트로니다졸",
    "Amoxicillin/Clavulanate": "아목시실린/클라불란산",
    "Ceftriaxone": "세프트리악손",
    "Cefotaxime": "세포탁심",
}

# Main DB
DRUG_DB: Dict[str, Dict[str, Any]] = {}

def _upsert(db: Dict[str, Dict[str, Any]], key: str, alias: str, moa: str, ae: str) -> None:
    """키(영문) 기준으로 alias/moa/ae를 병합 삽입. 대소문자/별칭 접근도 동일하게."""
    entry = db.setdefault(key, {})
    entry.update({"alias": alias, "moa": moa, "ae": ae})
    for alt in {key, key.lower(), alias, alias.lower()}:
        db.setdefault(alt, entry)

def display_label(key: str, db: Optional[Dict[str, Dict[str, Any]]] = None, style: str = "comma") -> str:
    """
    약물 표시 라벨을 생성.
    style="comma"  →  "영문,한글" (기본)  예: "Cefepime,세페핌"
    style="paren"  →  "영문 (한글)"       예: "Cefepime (세페핌)"
    """
    if not key:
        return ""
    k = str(key).strip().strip('"\'')
    ref = db if isinstance(db, dict) else DRUG_DB
    alias = None
    e = ref.get(k)
    if isinstance(e, dict):
        alias = e.get("alias")
    if not alias:
        alias = ALIAS_FALLBACK.get(k)
    if alias and alias != k:
        return f"{k} ({alias})" if style == "paren" else f"{k},{alias}"
    return k

def key_from_label(label: str) -> str:
    """표시 라벨에서 원래 키(영문명)를 복원."""
    if not label:
        return ""
    s = str(label).strip().replace(", ", ",")
    if "," in s:
        return s.split(",", 1)[0]
    if " (" in s and s.endswith(")"):
        return s.split(" (", 1)[0]
    return s

def picklist(keys: List[str], db: Optional[Dict[str, Dict[str, Any]]] = None, style: str = "comma") -> List[str]:
    """주어진 키 리스트를 표시 라벨 리스트로 변환."""
    return [display_label(k, db=db, style=style) for k in keys]

def ensure_onco_drug_db(db: Dict[str, Dict[str, Any]]) -> None:
    """프로젝트 공통으로 쓰이는 핵심 약물들을 DB에 보강한다.
    - onco_map.py 의 chemo 32종 전부 포함
    - APL 필수: ATRA, Arsenic Trioxide, MTX, 6-MP, Cytarabine 포함
    - Lymphoma CHOP: Cyclophosphamide, Doxorubicin, Vincristine, Prednisone 포함
    - AML 승인 신약(Revumenib) 포함, 미승인 후보는 제외
    """
    # --- Chemo full coverage (32 canonical) ---
    _upsert(db, "Bendamustine", "벤다무스틴",
            "알킬화제(머스터드) + 퓨린유사체 성격",
            "골수억제, 발진/가려움, 발열/감염, 드물게 SJS/TEN; 종양용해증후군 주의")
    _upsert(db, "Cytarabine", "시타라빈(Ara-C)",
            "Pyrimidine 아날로그 (DNA 합성 억제)",
            "골수억제(호중구↓), 발열, 발진, 고용량 시 신경독성/결막염; 제형에 따라 다름")
    _upsert(db, "Daunorubicin", "다우노루비신",
            "Anthracycline (Topo II 억제, ROS)",
            "심독성(누적), 골수억제, 구내염, 탈모, 오심/구토")
    _upsert(db, "Idarubicin", "이다루비신",
            "Anthracycline (Topo II 억제, ROS)",
            "심독성, 골수억제, 구내염, 탈모, 오심/구토")
    _upsert(db, "Doxorubicin", "독소루비신",
            "Anthracycline (Topo II 억제, ROS)",
            "누적성 심근병증, 골수억제, 구내염, 탈모, 혈관자극")
    _upsert(db, "ATRA", "트레티노인(베사노이드)",
            "RAR 수용체 작용 (분화 유도)",
            "두통/사지부종, 고지질혈증, 간효소 상승, RA-증후군 주의")
    _upsert(db, "Arsenic Trioxide", "산화비소",
            "세포 분화/아포토시스 유도",
            "QT 연장, 전해질 이상, RA-증후군, 간효소 상승")
    _upsert(db, "MTX", "메토트렉세이트",
            "DHF 환원효소 억제 (항대사제)",
            "골수억제, 구내염, 간독성, 신독성(고용량), 광과민; 류코보린 필요")
    _upsert(db, "6-MP", "6-머캅토퓨린",
            "Purine 합성 억제 (항대사제)",
            "골수억제, 간효소 상승, 발진/오심; TPMT/NUDT15 변이 영향")
    _upsert(db, "Cyclophosphamide", "사이클로포스파마이드",
            "알킬화제",
            "골수억제, 오심/구토, 출혈성 방광염(mesna), 탈모")
    _upsert(db, "Vincristine", "빈크리스틴",
            "Microtubule 억제 (방추사 억제)",
            "말초신경병증, 변비/장폐색, SIADH; 척수강내 금기")
    _upsert(db, "Etoposide", "에토포사이드",
            "Topo II 억제",
            "골수억제, 저혈압(급속주입), 탈모, 오심/구토")
    _upsert(db, "Prednisone", "프레드니손",
            "Glucocorticoid (림프구 사멸 유도)",
            "고혈당/감염 위험↑, 불면/기분변화, 위장관 자극, 장기 사용 시 골다공증/부신억제")
    _upsert(db, "Bleomycin", "블레오마이신",
            "DNA 절단 유도 (유리기)",
            "주요 위험: 폐섬유화, 발열/오한, 피부변화; 골수억제 경미")
    _upsert(db, "Vinblastine", "빈블라스틴",
            "Microtubule 억제",
            "골수억제(빈크리스틴보다 큼), 말초신경병증, 구내염")
    _upsert(db, "Gemcitabine", "젬시타빈",
            "Pyrimidine 아날로그",
            "골수억제, 간효소 상승, 발열/피로, 드물게 폐독성")
    _upsert(db, "Ifosfamide", "이포스파미드",
            "알킬화제",
            "출혈성 방광염(mesna), 신독성/팬코니, 중추신경독성(섬망)")
    _upsert(db, "Chlorambucil", "클로람부실",
            "알킬화제",
            "골수억제, 불임 위험, 2차 악성 종양, 드물게 폐독성")
    _upsert(db, "Dacarbazine", "다카르바진",
            "알킬화제 유사",
            "골수억제, 심한 오심/구토, 간독성, 광과민/독감 유사 증상")
    _upsert(db, "Dactinomycin", "닥티노마이신",
            "DNA intercalation",
            "골수억제, 구내염, 간독성, 강한 점막자극")
    _upsert(db, "Capecitabine", "카페시타빈",
            "경구 5-FU 전구약",
            "수족증후군, 설사, 골수억제; DPD 결핍 시 중증 독성")
    _upsert(db, "5-FU", "5-플루오로우라실",
            "Pyrimidine 유사체 (TS 억제)",
            "구내염/설사, 골수억제, 수족증후군, 드물게 심독성; 류코보린 병용 시 효능↑")
    _upsert(db, "Cisplatin", "시스플라틴",
            "DNA 가교결합 (백금제)",
            "신독성/이독성, 심한 오심/구토, 말초신경병증, 전해질 소실(Mg/K)")
    _upsert(db, "Carboplatin", "카보플라틴",
            "DNA 가교결합 (백금제)",
            "골수억제(혈소판↓), 과민반응, 시스플라틴 대비 신/이독성↓")
    _upsert(db, "Oxaliplatin", "옥살리플라틴",
            "DNA 가교결합 (백금제)",
            "한랭 유발 신경병증, 골수억제, 과민반응")
    _upsert(db, "Irinotecan", "이리노테칸",
            "Topo I 억제",
            "초기 콜린성 설사(아트로핀), 지연성 설사, 골수억제")
    _upsert(db, "Topotecan", "토포테칸",
            "Topo I 억제",
            "골수억제(호중구/빈혈), 설사/오심")
    _upsert(db, "Paclitaxel", "파클리탁셀",
            "Microtubule 안정화(탈중합 억제)",
            "말초신경병증, 골수억제, 탈모, 관절통; 과민반응(전처치 필요)")
    _upsert(db, "Nab-Paclitaxel", "나브-파클리탁셀",
            "Albumin-bound paclitaxel",
            "말초신경병증, 골수억제; 용매 과민반응 감소")
    _upsert(db, "Docetaxel", "도세탁셀",
            "Microtubule 안정화",
            "골수억제, 체액저류/부종, 손발톱 변화, 구내염")
    _upsert(db, "Pemetrexed", "페메트렉시드",
            "다중 효소 항엽산제",
            "골수억제, 피로, 발진(덱사 전처치), 엽산/B12 보충 필요")
    _upsert(db, "Trabectedin", "트라벡테딘",
            "DNA 마이너 그루브 결합",
            "간독성(AST/ALT↑), 골수억제, 드물게 횡문근융해(덱사 권장)")

    # --- Targeted / IO (선별) ---
    _upsert(db, "Rituximab", "리툭시맙",
            "CD20 표적 mAb",
            "주입반응, 감염 위험↑, B형간염 재활성화")
    _upsert(db, "Imatinib", "이매티닙",
            "BCR-ABL TKI",
            "부종, 근육통, 위장증상, 간효소 상승")

    # --- AML 승인 신약 (Menin inhibitor) ---
    _upsert(db, "Revumenib", "레부메닙(Revuforj)",
            "Menin 억제제 (KMT2A/MLL 복합체 결합 억제 → 분화 유도)",
            "분화증후군(DS), QT 연장, 골수억제(호중구↓/빈혈/혈소판↓), 발열/감염, 간효소 상승")

    # --- Antibiotics (FN/oncology common) ---
    _upsert(db, "Piperacillin/Tazobactam", "피페라실린/타조박탐",
            "광범위 β-lactam + 억제제",
            "알레르기/발진, C. difficile 설사, 나트륨 부하, 신기능에 따른 용량 조절")
    _upsert(db, "Cefepime", "세페핌",
            "4세대 세팔로스포린 (녹농균)",
            "과민반응, C. difficile, 신부전 시 신경독성(혼동/경련)")
    _upsert(db, "Ceftazidime", "세프타지딤",
            "3세대 세팔로스포린 (녹농균)",
            "과민반응, 위장관 증상, 드물게 신경독성")
    _upsert(db, "Meropenem", "메로페넴",
            "카바페넴",
            "과민반응, 위장증상, 드물게 경련(신부전/중추질환)")
    _upsert(db, "Imipenem/Cilastatin", "이미페넴/실라스타틴",
            "카바페넴",
            "경련 위험(특히 신부전/중추질환), 위장증상")
    _upsert(db, "Aztreonam", "아즈트레오남",
            "그람음성 선택 β-lactam (녹농균)",
            "발진, 위장증상; β-lactam 알레르기 대안")
    _upsert(db, "Amikacin", "아미카신",
            "Aminoglycoside (단백합성 억제)",
            "신독성/이독성 → 혈중농도/신기능 모니터")
    _upsert(db, "Vancomycin", "반코마이신",
            "G(+) Glycopeptide",
            "신독성, Red man(급속주입), 약동학 모니터; 드물게 이독성")
    _upsert(db, "Linezolid", "리네졸리드",
            "G(+) Oxazolidinone (MRSA/VRE)",
            "혈소판감소, 말초/시신경병증(장기), 세로토닌증후군")
    _upsert(db, "Daptomycin", "답토마이신",
            "G(+) Lipopeptide",
            "CPK 상승/근병증; 폐렴 치료 부적합(서팩턴트)")
    _upsert(db, "Levofloxacin", "레보플록사신",
            "Fluoroquinolone",
            "힘줄염/파열, QT 연장, 광과민, 혈당변동(소아 주의)")
    _upsert(db, "TMP-SMX", "트리메토프림/설파메톡사졸",
            "엽산 대사 억제 조합",
            "골수억제, 고칼륨혈증, 발진(SJS/TEN 드묾), 신기능 영향")
    _upsert(db, "Metronidazole", "메트로니다졸",
            "혐기성 커버",
            "금속맛, 알코올 금기(디설피람 유사), 말초신경병증(장기)")
    _upsert(db, "Amoxicillin/Clavulanate", "아목시실린/클라불란산",
            "경구 β-lactam + 억제제",
            "설사/발진, 드물게 간효소 상승")
    _upsert(db, "Ceftriaxone", "세프트리악손",
            "3세대 세팔로스포린",
            "담즙정체/슬러지, 과민반응, C. difficile 설사")
    _upsert(db, "Cefotaxime", "세포탁심",
            "3세대 세팔로스포린",
            "과민반응, 위장관 증상, 드물게 C. difficile 설사")

# 초기 보강 실행 (모듈 임포트 시)
ensure_onco_drug_db(DRUG_DB)

__all__ = [
    "ALIAS_FALLBACK",
    "DRUG_DB",
    "display_label",
    "key_from_label",
    "picklist",
    "ensure_onco_drug_db",
]
