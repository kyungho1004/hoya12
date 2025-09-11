# -*- coding: utf-8 -*-
from typing import Dict, Any

DRUG_DB: Dict[str, Dict[str, Any]] = {}

def _upsert(db, key, alias, moa, ae):
    db.setdefault(key, {})
    db[key].update({"alias": alias, "moa": moa, "ae": ae})
    for alt in {key, key.lower(), alias, alias.lower()}:
        db.setdefault(alt, {"alias": alias, "moa": moa, "ae": ae})

def ensure_onco_drug_db(db: Dict[str, Dict[str, Any]]):
    if db is None: return

    # --- APL core (분화증후군 상세 설명 포함) ---
    _upsert(db, "ATRA", "트레티노인(베사노이드, ATRA)",
            "RARα 수용체 작용 → APL 미성숙 전골수구 분화 유도",
            "분화증후군: 발열·호흡곤란·저혈압·부종/체중증가·흉막/심낭삼출 가능. 증상 시 즉시 스테로이드(예: 덱사메타손) 고려 및 ATRA/ATO 일시 중단 고려; "
            "두통, 피부/점막 건조·발진, 구내염, 간효소 상승, 고중성지방혈증·췌장염, 두개내압 상승, 임신 금기")
    _upsert(db, "Arsenic Trioxide", "삼산화비소(ATO)",
            "PML‑RARα 분해/아포토시스 유도",
            "분화증후군(상동) 가능, QT 연장/부정맥 위험(전해질 교정·심전도 모니터), 피로/오심")

    # --- Hematology common ---
    _upsert(db, "Idarubicin", "이다루비신", "Topo II 억제(안트라사이클린)", "심독성(누적), 골수억제, 점막염")
    _upsert(db, "Daunorubicin", "다우노루비신", "Topo II 억제/유리기", "심독성, 골수억제")
    _upsert(db, "Ara-C", "시타라빈(Ara‑C)", "시티딘 유사체", "골수억제, 결막염(점안 예방), 소뇌증상(고용량)")
    _upsert(db, "MTX", "메토트렉세이트(MTX)", "DHF 환원효소 억제", "골수억제, 간독성, 점막염/구내염, 신독성(고용량)")
    _upsert(db, "6-MP", "6‑머캅토퓨린(6‑MP)", "푸린 대사 교란", "골수억제, 간독성; TPMT/NUDT15 관련 독성")
    _upsert(db, "Vincristine", "빈크리스틴", "미세소관 억제", "말초신경병증, 변비/장폐색")
    _upsert(db, "Cyclophosphamide", "사이클로포스파마이드", "알킬화제", "골수억제, 출혈성 방광염(수분/메스나)")
    _upsert(db, "Prednisone", "프레드니손", "글루코코르티코이드", "혈당상승, 불면, 감염 위험")

    # --- Lymphoma specific ---
    _upsert(db, "Rituximab", "리툭시맙(CD20)", "CD20 단일클론항체", "주입반응, 감염위험↑, HBV 재활성화, PML 매우 드묾")
    _upsert(db, "Brentuximab Vedotin", "브렌툭시맙 베도틴(CD30 ADC)", "CD30 표적 항체‑약물 접합체", "말초신경병증, 호중구감소/감염, 주입반응")
    _upsert(db, "Bleomycin", "블레오마이신", "DNA 절단 유도", "폐독성(간질성 폐렴/섬유화), 피부색소변화/발진, 발열")
    _upsert(db, "Vinblastine", "빈블라스틴", "미세소관 억제", "골수억제, 변비, 말초신경병증(빈크리스틴보다 약함)")
    _upsert(db, "Dacarbazine", "다카바진", "알킬화제", "골수억제, 오심/구토, 드묾게 간독성")
    _upsert(db, "Bendamustine", "벤다무스틴", "알킬화제 유사", "골수억제, 발진, 감염위험")
    _upsert(db, "Ibrutinib", "이브루티닙(BTK)", "BTK 억제제", "출혈위험, 심방세동, 설사, 감염")

    # --- Sarcoma common ---
    _upsert(db, "Ifosfamide", "이포스파마이드", "알킬화제", "출혈성 방광염(메스나), 신독성, 신경독성(혼미)")
    _upsert(db, "Etoposide", "에토포사이드", "Topo II 억제", "골수억제, 저혈압(급속주입), 탈모")
    _upsert(db, "Dactinomycin", "닥티노마이신(Actinomycin D)", "DNA 간섭/전사 억제", "골수억제, 간독성, 점막염")
    _upsert(db, "Pazopanib", "파조파닙", "VEGFR TKI", "고혈압, 간효소 상승, 수족증후군")
    _upsert(db, "Trabectedin", "트라벡테딘", "DNA minor groove 결합", "간독성, 골수억제, 횡문근융해 드묾")

    # --- Solid / GIST / NET / thyroid etc. ---
    _upsert(db, "Cisplatin", "시스플라틴", "백금계 교차결합", "신독성, 이독성/청력저하, 오심/구토, 말초신경병증")
    _upsert(db, "Carboplatin", "카보플라틴", "백금계", "골수억제, 오심/구토")
    _upsert(db, "Oxaliplatin", "옥살리플라틴", "백금계", "말초신경병증(냉자극성)")
    _upsert(db, "5-FU", "플루오로우라실(5‑FU)", "DNA/RNA 합성 억제", "구내염/설사, 수족증후군, 골수억제")
    _upsert(db, "Capecitabine", "카페시타빈", "경구 5‑FU 전구약물", "수족증후군, 설사/구내염, 피로")
    _upsert(db, "Irinotecan", "이리노테칸", "Topo I 억제", "설사(급성/지연), 골수억제")
    _upsert(db, "Docetaxel", "도세탁셀", "미세소관 안정화", "무과립구증, 체액저류/부종, 손발톱 변화")
    _upsert(db, "Paclitaxel", "파클리탁셀", "미세소관 안정화", "말초신경병증, 과민반응(전처치), 골수억제")
    _upsert(db, "Gemcitabine", "젬시타빈", "핵산합성 억제", "골수억제, 피로, 발열")
    _upsert(db, "Pemetrexed", "페메트렉시드", "엽산경로 억제", "골수억제, 발진; 엽산/B12 보충")
    _upsert(db, "Temozolomide", "테모졸로마이드", "알킬화제", "골수억제")
    _upsert(db, "Imatinib", "이매티닙", "BCR‑ABL/c‑KIT/PDGFR TKI", "부종, 발진, 간효소 상승, 골수억제")
    _upsert(db, "Sunitinib", "수니티닙", "멀티 TKI(c‑KIT/VEGFR 등)", "고혈압, 수족증후군, 갑상선기능저하")
    _upsert(db, "Everolimus", "에버롤리무스(mTOR)", "mTOR 억제제", "구내염, 고혈당/고지혈, 감염")
    _upsert(db, "Octreotide", "옥트레오타이드", "소마토스타틴 유사체", "위장관 증상, 담석, 고혈당/저혈당 변동")
    _upsert(db, "Trastuzumab", "트라스투주맙(HER2)", "HER2 단일클론항체", "심기능저하(LVEF 감소), 주입반응")
    _upsert(db, "Bevacizumab", "베바시주맙(VEGF)", "VEGF 억제", "고혈압, 단백뇨, 상처치유 지연/출혈")



# --- helpers for UI picklists ---
def display_label(key: str) -> str:
    info = DRUG_DB.get(key) or DRUG_DB.get(key.lower()) or {}
    alias = info.get("alias", "")
    return f"{key} ({alias})" if alias else key

def picklist(keys):
    return [display_label(k) for k in keys]

def key_from_label(label: str) -> str:
    # Expect "Key (Alias...)" → return "Key"
    if not label:
        return ""
    pos = label.find(" (")
    return label[:pos] if pos > 0 else label

    # --- Antibiotics (FN/oncology common) ---
    _upsert(db, "Piperacillin/Tazobactam", "피페라실린/타조박탐(타조신, Tazocin)",
            "광범위 β‑lactam + β‑lactamase 억제제",
            "알레르기/발진, 위장관 증상, C. difficile 연관 설사 가능, 나트륨 부하, 신기능에 따른 용량 조절")
    _upsert(db, "Cefepime", "세페핌(4세대)",
            "4세대 세팔로스포린(녹농균 포함)",
            "알레르기, 위장관 증상, C. difficile, 신부전 시 **신경독성(혼동/경련)** 위험")
    _upsert(db, "Meropenem", "메로페넴(카바페넴)",
            "광범위 카바페넴",
            "알레르기, 위장관 증상, 경련 드묾(특히 신부전/중추질환)")
    _upsert(db, "Vancomycin", "반코마이신",
            "G(+) 대상 글리코펩타이드",
            "신독성, **Red man syndrome**(급속 주입 시), 혈중농도 모니터 필요, 청력독성 드묾")
    _upsert(db, "Ceftazidime", "세프타지딤(3세대)",
            "3세대 세팔로스포린(녹농균)",
            "알레르기, 위장관 증상, 드묾게 신경독성")
    _upsert(db, "Levofloxacin", "레보플록사신(퀴놀론)",
            "DNA gyrase 억제",
            "힘줄염/파열, QT 연장, 광과민, 혈당 변동; 18세 미만 사용 주의")
    _upsert(db, "TMP-SMX", "트리메토프림/설파메톡사졸(코트림)",
            "엽산 대사 억제 조합",
            "골수억제, 고칼륨혈증, 발진(SJS/TEN 드묾), 신기능 영향; 상호작용 주의")
