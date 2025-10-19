
# ---------- Fallback Korean aliases (display only; DB alias 우선) ----------
ALIAS_FALLBACK = {
    # Chemo
    "Cytarabine": "시타라빈(Ara-C)",
    "Daunorubicin": "다우노루비신",
    "Idarubicin": "이다루비신",
    "ATRA": "트레티노인",
    "Arsenic Trioxide": "산화비소",
    "MTX": "메토트렉세이트",
    "6-MP": "6-머캅토퓨린",
    "Cyclophosphamide": "사이클로포스파마이드",
    "Prednisone": "프레드니손",
    "Vincristine": "빈크리스틴",
    "Vinblastine": "빈블라스틴",
    "Etoposide": "에토포사이드",
    "Doxorubicin": "독소루비신",
    "Bleomycin": "블레오마이신",
    "Dacarbazine": "다카바진",
    "Chlorambucil": "클로람부실",
    "Bendamustine": "벤다무스틴",
    "Ibrutinib": "이브루티닙",
    "Ifosfamide": "이포스파미드",
    "Gemcitabine": "젬시타빈",
    "Docetaxel": "도세탁셀",
    "Paclitaxel": "파클리탁셀",
    "Topotecan": "토포테칸",
    "Trabectedin": "트라벡테딘",
    "Dactinomycin": "닥티노마이신",
    "Carboplatin": "카보플라틴",
    "Cisplatin": "시스플라틴",
    "Pemetrexed": "페메트렉시드",
    "Oxaliplatin": "옥살리플라틴",
    "Irinotecan": "이리노테칸",
    "Capecitabine": "카페시타빈",
    "5-FU": "5-플루오로우라실",
    "Nab-Paclitaxel": "나노입자 파클리탁셀",
    # Targeted / IO
    "Rituximab": "리툭시맙",
    "Obinutuzumab": "오비누투주맙",
    "Polatuzumab Vedotin": "폴라투주맙 베도틴",
    "Brentuximab Vedotin": "브렌툭시맙 베도틴",
    "Nivolumab": "니볼루맙",
    "Pembrolizumab": "펨브롤리주맙",
    "Atezolizumab": "아테졸리주맙",
    "Durvalumab": "더발루맙",
    "Imatinib": "이마티닙",
    "Sunitinib": "수니티닙",
    "Regorafenib": "레고라페닙",
    "Ripretinib": "리프레티닙",
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
    "Lapatinib": "라파티닙",
    "Tucatinib": "투카티닙",
    "Everolimus": "에베로리무스",
    "Octreotide": "옥트레오타이드",
    "Vandetanib": "반데타닙",
    "Cabozantinib": "카보잔티닙",
    "Selpercatinib": "셀퍼카티닙",
    "Pralsetinib": "프랄세티닙",
    # Antibiotics
    "Piperacillin/Tazobactam": "피페라실린/타조박탐",
    "Cefepime": "세페핌",
    "Meropenem": "메로페넴",
    "Imipenem/Cilastatin": "이미페넴/실라스타틴",
    "Aztreonam": "아즈트레오남",
    "Amikacin": "아미카신",
    "Vancomycin": "반코마이신",
    "Linezolid": "리네졸리드",
    "Daptomycin": "답토마이신",
    "Ceftazidime": "세프타지딤",
    "Levofloxacin": "레보플록사신",
    "TMP-SMX": "트리메토프림/설파메톡사졸",
    "Metronidazole": "메트로니다졸",
    "Amoxicillin/Clavulanate": "아목시실린/클라불란산",
}

def display_label(key: str, db=None) -> str:
    ref = None
    try:
        ref = db if isinstance(db, dict) else DRUG_DB
    except Exception:
        ref = None
    alias = None
    if ref and key in ref and isinstance(ref[key], dict):
        alias = ref[key].get("alias")
    if not alias:
        alias = ALIAS_FALLBACK.get(key)
    if alias and alias != key:
        return f"{key} ({alias})"
    return str(key)

def picklist(keys, db=None):
    ref = db if isinstance(db, dict) else DRUG_DB if 'DRUG_DB' in globals() else {}
    return [display_label(k, ref) for k in (keys or [])]

def key_from_label(label: str, db=None) -> str:
    if not label:
        return ""
    pos = label.find(" (")
    if pos > 0:
        return label[:pos]
    ref = db if isinstance(db, dict) else DRUG_DB if 'DRUG_DB' in globals() else {}
    if label in ref:
        return label
    for k, v in (ref or {}).items():
        if isinstance(v, dict) and v.get("alias") == label:
            return k
    return label

# -*- coding: utf-8 -*-
from typing import Dict, Any
# --- DRUG_KO: English -> Korean drug names (non-destructive patch) ---
DRUG_KO = {
    "Imatinib":"이미티닙","Sunitinib":"수니티닙","Regorafenib":"레고라페닙","Ripretinib":"리프레티닙",
    "Osimertinib":"오시머티닙","Erlotinib":"얼로티닙","Gefitinib":"게피티닙",
    "Alectinib":"알렉티닙","Lorlatinib":"롤라티닙","Bevacizumab":"베바시주맙",
    "Trastuzumab":"트라스투주맙","Rituximab":"리툭시맙",
    "Pembrolizumab":"펨브롤리주맙","Nivolumab":"니볼루맙","Atezolizumab":"아테졸리주맙",
    "Cyclophosphamide":"사이클로포스파마이드","Doxorubicin":"독소루비신","Vincristine":"빈크리스틴","Prednisone":"프레드니손",
    "Paclitaxel":"파클리탁셀","Docetaxel":"도세탁셀","Capecitabine":"카페시타빈",
    "Oxaliplatin":"옥살리플라틴","Cisplatin":"시스플라틴","Carboplatin":"카보플라틴","Irinotecan":"이리노테칸",
    "Fluorouracil":"플루오로우라실","5-Fluorouracil":"플루오로우라실","5FU":"플루오로우라실","5-FU":"플루오로우라실",
}
# --- /DRUG_KO ---

DRUG_DB: Dict[str, Dict[str, Any]] = {}

def _upsert(db, key, alias, moa, ae):
    db.setdefault(key, {})
    db[key].update({"alias": alias, "moa": moa, "ae": ae})
    for alt in {key, key.lower(), alias, alias.lower()}:
        db.setdefault(alt, {"alias": alias, "moa": moa, "ae": ae})

def ensure_onco_drug_db(db: Dict[str, Dict[str, Any]]):
    pass


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

    # --- Targeted / Immunotherapy additions ---
    _upsert(db, "Polatuzumab Vedotin", "폴라투주맙 베도틴(CD79b ADC)", "CD79b 표적 항체‑약물 접합체", "말초신경병증, 골수억제, 주입반응")
    _upsert(db, "Obinutuzumab", "오비누투주맙(CD20)", "Type II CD20 단일클론항체", "주입반응, 감염, HBV 재활성화")
    _upsert(db, "Pembrolizumab", "펨브롤리주맙(PD‑1)", "면역관문억제제(PD‑1)", "면역관련 이상반응(피부, 갑상선, 폐, 간, 대장)")
    _upsert(db, "Nivolumab", "니볼루맙(PD‑1)", "면역관문억제제(PD‑1)", "면역관련 이상반응(피부, 갑상선, 폐, 간, 대장)")
    _upsert(db, "Atezolizumab", "아테졸리주맙(PD‑L1)", "면역관문억제제(PD‑L1)", "면역관련 이상반응")
    _upsert(db, "Durvalumab", "더발루맙(PD‑L1)", "면역관문억제제(PD‑L1)", "면역관련 이상반응")
    _upsert(db, "Pertuzumab", "퍼투주맙(HER2)", "HER2 dimerization 억제", "설사, 발진, 심기능저하(드묾)")
    _upsert(db, "T-DM1", "트라스투주맙‑엠탄신(T‑DM1)", "HER2 ADC", "혈소판감소, 간효소 상승, 피로")
    _upsert(db, "Regorafenib", "레고라페닙", "멀티 TKI(GIST/대장암 등)", "수족증후군, 고혈압, 간독성")
    _upsert(db, "Ripretinib", "리프레티닙", "KIT/PDGFRA 스위치포켓 억제(GIST)", "탈모, 피로, 고혈압")

    _upsert(db, "Cabozantinib", "카보잔티닙", "멀티 TKI(RET/MET/VEGFR)", "고혈압, 설사, 손발증후군")
    _upsert(db, "Vandetanib", "반데타닙", "RET/EGFR/VEGFR TKI(MTC)", "QT 연장, 설사, 발진")
    _upsert(db, "Capmatinib", "캡마티닙(MET)", "MET 억제(NSCLC)", "말초부종, 오심, 광과민")
    _upsert(db, "Sotorasib", "소토라십(KRAS G12C)", "KRAS G12C 억제", "설사, ALT/AST 상승")

    # --- More antibiotics (FN/pathogen coverage common) ---
    _upsert(db, "Imipenem/Cilastatin", "이미페넴/실라스타틴(카바페넴)", "광범위 카바페넴", "경련 위험(특히 신부전/중추질환), 위장관 증상")
    _upsert(db, "Aztreonam", "아즈트레오남", "그람음성 선택 β‑lactam(녹농균 포함)", "발진, 위장관 증상; β‑lactam 알레르기 시 대안(세페엠 교차반응 낮음)")
    _upsert(db, "Amikacin", "아미카신(아미노글리코시드)", "단백 합성 억제", "신독성/이독성 모니터 필요")
    _upsert(db, "Linezolid", "리네졸리드", "G(+) MRSA/VRE 옥사졸리디논", "혈소판감소, 말초/시신경병증(장기), 세로토닌증후군 주의")
    _upsert(db, "Daptomycin", "다프토마이신", "G(+) 리포펩타이드", "CPK 상승/근병증, 폐렴 치료에는 부적합(서팩턴트에 비활성)")
    _upsert(db, "Metronidazole", "메트로니다졸", "혐기성 커버리지", "금속맛, 알코올 금기(디설피람 유사반응), 말초신경병증(장기)")
    _upsert(db, "Amoxicillin/Clavulanate", "아목시실린/클라불란산(오구멘틴)", "경구 광범위 β‑lactam + 억제제", "설사/발진, 간효소 상승 드묾")



    _upsert(db, "Chlorambucil", "클로람부실", "알킬화제(경구)", "골수억제, 발진, 간효소 상승 드묾")
    _upsert(db, "Lenalidomide", "레날리도마이드", "면역조절제(IMiD)", "혈전증 위험, 골수억제, 발진; 임신 금기")

    # --- Solid tumor targeted / immuno expansions ---
    _upsert(db, "Cetuximab", "세툭시맙(EGFR)", "EGFR 단일클론항체(대장암/두경부암)", "주입반응, 저마그네슘혈증, 여드름양 발진, 설사")
    _upsert(db, "Panitumumab", "파니투무맙(EGFR)", "EGFR 단일클론항체(대장암)", "저마그네슘혈증, 피부발진, 설사")
    _upsert(db, "Ramucirumab", "라무시루맙(VEGFR2)", "VEGFR2 항체(위암/간암 등)", "고혈압, 단백뇨, 출혈/혈전, 상처치유 지연")
    _upsert(db, "Lapatinib", "라파티닙(HER2/EGFR)", "HER2/EGFR TKI(유방암)", "설사, 발진, 간효소 상승, 드물게 심독성")
    _upsert(db, "Tucatinib", "투카티닙(HER2)", "HER2 선택적 TKI(유방암)", "설사, 간효소 상승, 피로")
    _upsert(db, "Trastuzumab deruxtecan", "트라스투주맙 데룩스테칸(T-DXd)", "HER2 ADC", "간질성 폐질환/폐렴 위험, 오심/구토, 골수억제")
    _upsert(db, "Olaparib", "올라파립(PARP)", "PARP 억제제(난소/유방 등)", "빈혈/혈소판감소, 피로, 구역")
    _upsert(db, "Niraparib", "니라파립(PARP)", "PARP 억제제(난소)", "혈소판감소, 빈혈, 고혈압, 피로")
    _upsert(db, "Palbociclib", "팔보시클립(CDK4/6)", "CDK4/6 억제제(유방암)", "호중구감소증, 피로, 구내염")
    _upsert(db, "Ribociclib", "리보시클립(CDK4/6)", "CDK4/6 억제제(유방암)", "호중구감소증, QT 연장, 간효소 상승")
    _upsert(db, "Abemaciclib", "아베마시클립(CDK4/6)", "CDK4/6 억제제(유방암)", "설사, 호중구감소증, 피로")
    _upsert(db, "Lorlatinib", "로를라티닙(ALK)", "ALK TKI(NSCLC)", "지질 상승, 인지/기분 변화, 체중증가")
    _upsert(db, "Selpercatinib", "셀퍼카티닙(RET)", "RET TKI(NSCLC/MTC)", "고혈압, 간효소 상승, 드물게 QT 연장")
    _upsert(db, "Pralsetinib", "프랄세티닙(RET)", "RET TKI(NSCLC)", "고혈압, 간효소 상승, 변비/설사")
    _upsert(db, "Dabrafenib", "다브라페닙(BRAF)", "BRAF V600 억제(흑색종/폐암)", "발열, 피부발진, 관절통")
    _upsert(db, "Trametinib", "트라메티닙(MEK)", "MEK 억제", "심기능저하/좌심실 기능 감소, 피부/설사")
    _upsert(db, "Encorafenib", "엔코라페닙(BRAF)", "BRAF 억제", "피로, 관절통, 발진")
    _upsert(db, "Binimetinib", "비니메티닙(MEK)", "MEK 억제", "망막/시야 이상 드묾, 설사/발진")
    _upsert(db, "Ipilimumab", "이필리무맙(CTLA-4)", "면역관문억제제(CTLA-4)", "면역관련 이상반응(대장염/간염/피부/내분비)")

    # --- Additional chemo used in solid tumors ---
    _upsert(db, "Nab-Paclitaxel", "나브-파클리탁셀", "알부민 결합 파클리탁셀", "말초신경병증, 골수억제, 탈모")
    _upsert(db, "Topotecan", "토포테칸", "Topo I 억제(난소/소세포폐암)", "골수억제, 피로, 오심")



# ====== PATCH: extend ensure_onco_drug_db with APL + missing therapies ======
try:
    _original_ensure_onco_drug_db = ensure_onco_drug_db
except NameError:
    _original_ensure_onco_drug_db = None

def ensure_onco_drug_db(db):
    # Call original to keep upstream list
    if _original_ensure_onco_drug_db is not None:
        _original_ensure_onco_drug_db(db)
    # APL core

    _upsert(db, "Cytarabine", "시타라빈(Ara‑C)", "피리미딘 유사체(항대사제)", "골수억제, 발열, 점막염, 드물게 신경독성")
    _upsert(db, "Daunorubicin", "다우노루비신", "Topo II 억제(안트라사이클린)", "심근독성(누적), 골수억제, 점막염")
    _upsert(db, "Idarubicin", "이다루비신", "Topo II 억제(안트라사이클린)", "심근독성, 골수억제, 오심/구토")
    _upsert(db, "Tretinoin", "트레티노인(ATRA)", "RARα 작용 — 분화 유도", "분화증후군(DS): 발열·호흡곤란/폐침윤·저산소증, 흉막/심막삼출, 급격한 체중증가(부종)·저혈압·신장기능저하; 대개 투여 2–21일 이내 발생, 백혈구 급증 동반 가능. 의심 즉시 **덱사메타손 10 mg IV q12h** 시작, 산소/수액/전해질 보정, 중증 시 ATRA/ATO 일시중단 고려. 고위험(초진단 시 고백혈구 등)은 예방적 스테로이드 고려), 간효소 상승, 두통/피부건조, 점막염")
    _upsert(db, "Arsenic Trioxide", "산화비소(ATO)", "분화 유도/아포토시스", "분화증후군(ATRA와 동일 관리), **QT 연장**(저K/저Mg 교정·ECG 모니터링, 위험약물 병용 주의), 전해질 이상, 간효소 상승/피부발진")

    # Missing/expanded

    _upsert(db, "Doxorubicin", "독소루비신(Adriamycin)", "Topo II 억제(안트라사이클린)", "심근독성(누적), 골수억제, 점막염, 탈모")
    _upsert(db, "Chlorambucil", "클로람부실", "알킬화제", "골수억제, 오심/구토")
    _upsert(db, "Obinutuzumab", "오비누투주맙(CD20)", "CD20 단일클론항체", "주입반응, 감염위험, HBV 재활성화")
    _upsert(db, "Polatuzumab Vedotin", "폴라투주맙 베도틴(CD79b ADC)", "CD79b 표적 항체‑약물 접합체", "말초신경병증, 골수억제, 주입반응")
    _upsert(db, "Pembrolizumab", "펨브롤리주맙(PD-1)", "PD-1 면역관문억제제", "면역관련 이상반응(피부/대장염/간염/내분비)")
    _upsert(db, "Nivolumab", "니볼루맙(PD-1)", "PD-1 면역관문억제제", "면역관련 이상반응")
    _upsert(db, "Osimertinib", "오시머티닙(EGFR)", "EGFR TKI(Ex19del/L858R/T790M)", "설사, 발진, 드물게 ILD")
    _upsert(db, "Alectinib", "알렉티닙(ALK)", "ALK TKI", "근육통, 변비, 간효소 상승")
    _upsert(db, "Crizotinib", "크리조티닙(ALK/ROS1)", "ALK/ROS1 TKI", "시야 흐림, 위장관 증상")
    _upsert(db, "Lorlatinib", "로를라티닙(ALK)", "ALK TKI", "지질 상승, 인지/기분 변화")
    _upsert(db, "Entrectinib", "엔트렉티닙(ROS1/NTRK)", "ROS1/NTRK TKI", "체중 증가, 어지러움")
    _upsert(db, "Larotrectinib", "라로트렉티닙(NTRK)", "NTRK TKI", "피로, 어지러움")
    _upsert(db, "Capmatinib", "캡마티닙(MET)", "MET TKI", "말초부종, 간효소 상승")
    _upsert(db, "Sotorasib", "소토라십(KRAS G12C)", "KRAS G12C 억제제", "설사, 간효소 상승")
    _upsert(db, "Ramucirumab", "라무시루맙(VEGFR2)", "VEGFR2 단일클론항체", "고혈압, 출혈위험")
    _upsert(db, "Regorafenib", "레고라페닙", "멀티키나아제 억제제", "손발증후군, 피로, 고혈압")
    _upsert(db, "Ripretinib", "리프레티닙", "KIT/PDGFRA 억제(GIST)", "탈모, 피로, 손발증후군")
    _upsert(db, "Vandetanib", "반데타닙(RET)", "RET/VEGFR/EGFR TKI", "QT 연장, 설사, 발진")
    _upsert(db, "Cabozantinib", "카보잔티닙", "MET/VEGFR/RET TKI", "설사, 피로, 손발증후군")
    _upsert(db, "Selpercatinib", "셀퍼카티닙(RET)", "RET TKI(NSCLC/MTC)", "고혈압, 간효소 상승, QT 연장 드묾")
    _upsert(db, "Pralsetinib", "프랄세티닛(RET)", "RET TKI(NSCLC/MTC)", "고혈압, 간효소 상승, 변비/설사")
    _upsert(db, "Pertuzumab", "퍼투주맙(HER2)", "HER2 dimer 억제", "설사, LVEF 감소")
    _upsert(db, "T-DM1", "아도‑트라스투주맙 엠탄신(T‑DM1)", "HER2 ADC", "혈소판 감소, 간독성")
    _upsert(db, "Trastuzumab deruxtecan", "트라스투주맙 데룩스테칸(T‑DXd)", "HER2 ADC", "간질성 폐질환(ILD) 위험, 오심")
    _upsert(db, "Tucatinib", "투카티닙(HER2)", "HER2 TKI", "설사, 간효소 상승")
    _upsert(db, "Lapatinib", "라파티닙(HER2)", "HER2 TKI", "설사, 발진")


    # Mirror with quoted keys for onco_map entries that accidentally include quotes
    def __mirror_with_quotes(key):
        if key in db:
            entry = db.get(key, {})
            _upsert(db, f"'{key}'", entry.get('alias', key), entry.get('moa', ''), entry.get('ae', ''))
            _upsert(db, f'"{key}"', entry.get('alias', key), entry.get('moa', ''), entry.get('ae', ''))
    for __k in [
        "Atezolizumab","Cetuximab","Durvalumab","Lenvatinib","Nab-Paclitaxel",
        "Niraparib","Olaparib","Panitumumab","Sorafenib","Topotecan",
        "Doxorubicin","Osimertinib","Tretinoin","Cytarabine","Arsenic Trioxide"
    ]:
        __mirror_with_quotes(__k)


    # Common synonyms used in ONCO map
    _upsert(db, "ATRA", "트레티노인(ATRA)", "RARα 작용 — 분화 유도", "분화증후군(DS): 발열·호흡곤란/폐침윤·저산소증, 흉막/심막삼출, 급격한 체중증가(부종)·저혈압·신장기능저하; 대개 투여 2–21일 이내 발생, 백혈구 급증 동반 가능. 의심 즉시 **덱사메타손 10 mg IV q12h** 시작, 산소/수액/전해질 보정, 중증 시 ATRA/ATO 일시중단 고려. 고위험(초진단 시 고백혈구 등)은 예방적 스테로이드 고려), 간효소 상승, 두통/피부건조, 점막염")
    _upsert(db, "MTX", "메토트렉세이트(MTX)", "DHFR 억제(항대사제)", "골수억제, 점막염, 간독성, 신장독성(고용량)")
    _upsert(db, "6-MP", "6-머캅토퓨린(6-MP)", "퓨린 유사체(항대사제)", "골수억제, 간독성(특히 병용약물 상호작용)")

# ====== END PATCH ======


# === FINAL ensure_onco_drug_db (patched) ===
try:
    _original_ensure_onco_drug_db
except NameError:
    _original_ensure_onco_drug_db = None

def ensure_onco_drug_db(db):
    if _original_ensure_onco_drug_db is not None:
        _original_ensure_onco_drug_db(db)
    # APL core
    _upsert(db, "Cytarabine", "시타라빈(Ara‑C)", "피리미딘 유사체(항대사제)", "골수억제, 발열, 점막염, 드물게 신경독성")
    _upsert(db, "Daunorubicin", "다우노루비신", "Topo II 억제(안트라사이클린)", "심근독성(누적), 골수억제, 점막염")
    _upsert(db, "Idarubicin", "이다루비신", "Topo II 억제(안트라사이클린)", "심근독성, 골수억제, 오심/구토")
    _upsert(db, "Tretinoin", "트레티노인(ATRA)", "RARα 작용 — 분화 유도", "분화증후군(DS): 발열·호흡곤란/폐침윤·저산소증, 흉막/심막삼출, 급격한 체중증가(부종)·저혈압·신장기능저하; 대개 투여 2–21일 이내 발생, 백혈구 급증 동반 가능. 의심 즉시 **덱사메타손 10 mg IV q12h** 시작, 산소/수액/전해질 보정, 중증 시 ATRA/ATO 일시중단 고려. 고위험(초진단 시 고백혈구 등)은 예방적 스테로이드 고려), 간효소 상승, 두통/피부건조, 점막염")
    _upsert(db, "Arsenic Trioxide", "산화비소(ATO)", "분화 유도/아포토시스", "분화증후군(ATRA와 동일 관리), **QT 연장**(저K/저Mg 교정·ECG 모니터링, 위험약물 병용 주의), 전해질 이상, 간효소 상승/피부발진")

    # Solid/GI/HCC & EGFR/HER2 & PARP 확장
    _upsert(db, "Atezolizumab", "아테졸리주맙(PD-L1)", "PD-L1 면역관문억제제", "면역관련 이상반응")
    _upsert(db, "Cetuximab", "세툭시맙(EGFR)", "EGFR 단일클론항체", "여드름양 발진, 저마그네슘혈증")
    _upsert(db, "Durvalumab", "더발루맙(PD-L1)", "PD-L1 면역관문억제제", "면역관련 이상반응")
    _upsert(db, "Lenvatinib", "렌바티닙", "VEGFR/FGFR TKI", "고혈압, 단백뇨")
    _upsert(db, "Niraparib", "니라파립(PARP)", "PARP 억제제", "혈소판 감소, 피로")
    _upsert(db, "Olaparib", "올라파립(PARP)", "PARP 억제제", "빈혈, 피로, 오심")
    _upsert(db, "Panitumumab", "파니투무맙(EGFR)", "EGFR 단일클론항체", "피부발진, 저마그네슘혈증")
    _upsert(db, "Sorafenib", "소라페닙", "VEGFR/RAF TKI", "손발증후군, 고혈압")
    _upsert(db, "Topotecan", "토포테칸", "Topo I 억제(난소/소세포폐암)", "골수억제, 피로, 오심")
    _upsert(db, "Nab-Paclitaxel", "나브-파클리탁셀", "알부민 결합 파클리탁셀", "말초신경병증, 골수억제, 탈모")

    # 약어/동의어
    _upsert(db, "ATRA", "트레티노인(ATRA)", "RARα 작용 — 분화 유도", "분화증후군(DS): 발열·호흡곤란/폐침윤·저산소증, 흉막/심막삼출, 급격한 체중증가(부종)·저혈압·신장기능저하; 대개 투여 2–21일 이내 발생, 백혈구 급증 동반 가능. 의심 즉시 **덱사메타손 10 mg IV q12h** 시작, 산소/수액/전해질 보정, 중증 시 ATRA/ATO 일시중단 고려. 고위험(초진단 시 고백혈구 등)은 예방적 스테로이드 고려), 간효소 상승, 두통/피부건조, 점막염")
    _upsert(db, "MTX", "메토트렉세이트(MTX)", "DHFR 억제(항대사제)", "골수억제, 점막염, 간독성, 신장독성(고용량)")
    _upsert(db, "6-MP", "6-머캅토퓨린(6-MP)", "퓨린 유사체(항대사제)", "골수억제, 간독성(특히 병용약물 상호작용)")



# === AUTO-FILL: ensure all ONCO_MAP-referenced names exist ===
try:
    __prev_ensure = ensure_onco_drug_db
except NameError:
    __prev_ensure = None

def ensure_onco_drug_db(db):
    if __prev_ensure is not None:
        __prev_ensure(db)
    _upsert(db, "5-FU", "5-FU", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Alectinib", "Alectinib", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Ara-C", "Ara-C", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Bendamustine", "Bendamustine", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Bevacizumab", "Bevacizumab", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Bleomycin", "Bleomycin", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Brentuximab Vedotin", "Brentuximab Vedotin", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Cabozantinib", "Cabozantinib", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Capecitabine", "Capecitabine", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Capmatinib", "Capmatinib", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Carboplatin", "Carboplatin", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Chlorambucil", "Chlorambucil", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Cisplatin", "Cisplatin", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Crizotinib", "Crizotinib", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Cyclophosphamide", "Cyclophosphamide", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Dacarbazine", "Dacarbazine", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Dactinomycin", "Dactinomycin", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Docetaxel", "Docetaxel", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Doxorubicin", "Doxorubicin", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Entrectinib", "Entrectinib", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Etoposide", "Etoposide", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Everolimus", "Everolimus", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Gemcitabine", "Gemcitabine", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Ibrutinib", "Ibrutinib", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Ifosfamide", "Ifosfamide", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Imatinib", "Imatinib", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Irinotecan", "Irinotecan", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Lapatinib", "Lapatinib", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Larotrectinib", "Larotrectinib", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Lorlatinib", "Lorlatinib", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Nivolumab", "Nivolumab", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Obinutuzumab", "Obinutuzumab", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Octreotide", "Octreotide", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Osimertinib", "Osimertinib", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Oxaliplatin", "Oxaliplatin", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Paclitaxel", "Paclitaxel", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Pazopanib", "Pazopanib", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Pembrolizumab", "Pembrolizumab", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Pemetrexed", "Pemetrexed", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Pertuzumab", "Pertuzumab", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Polatuzumab Vedotin", "Polatuzumab Vedotin", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Pralsetinib", "Pralsetinib", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Prednisone", "Prednisone", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Ramucirumab", "Ramucirumab", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Regorafenib", "Regorafenib", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Ripretinib", "Ripretinib", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Rituximab", "Rituximab", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Selpercatinib", "Selpercatinib", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Sotorasib", "Sotorasib", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Sunitinib", "Sunitinib", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "T-DM1", "T-DM1", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Trabectedin", "Trabectedin", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Trastuzumab", "Trastuzumab", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Trastuzumab deruxtecan", "Trastuzumab deruxtecan", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Tucatinib", "Tucatinib", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Vandetanib", "Vandetanib", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Vinblastine", "Vinblastine", "항암/표적치료(자동등록)", "부작용 정보 필요")
    _upsert(db, "Vincristine", "Vincristine", "항암/표적치료(자동등록)", "부작용 정보 필요")

# === SYNONYMS for maintenance/alias ===
try:
    __prev2 = ensure_onco_drug_db
except NameError:
    __prev2 = None

def ensure_onco_drug_db(db):
    if __prev2 is not None:
        __prev2(db)
    _upsert(db, "Ara-C", "시타라빈(Ara-C)", "피리미딘 유사체(항대사제)", "골수억제, 발열, 점막염, 드물게 신경독성")
    _upsert(db, "Methotrexate", "메토트렉세이트(MTX)", "DHFR 억제(항대사제)", "골수억제, 점막염, 간독성, 신장독성(고용량)")
    _upsert(db, "Mercaptopurine", "6-머캅토퓨린(6-MP)", "퓨린 유사체(항대사제)", "골수억제, 간독성(상호작용 주의)")

# --- UI Helper: display_label ---
def display_label(key: str, db: dict = None) -> str:
    """약물 키를 사람이 읽기 쉬운 라벨(한글 병기 alias)로 변환.
    - db가 주어지면 그 dict를, 아니면 모듈 전역 DRUG_DB 사용
    - 키는 따옴표/공백을 제거하여 조회 시도
    """
    try:
        ref = db if isinstance(db, dict) else DRUG_DB
    except NameError:
        ref = db or {}
    k = key if isinstance(key, str) else str(key)
    norm = k.strip().strip("'\"")
    entry = ref.get(norm) or ref.get(k)
    if isinstance(entry, dict):
        return entry.get("alias") or norm
    return norm


# --- Side effects (KO) patch (non-destructive) ---
SIDE_EFFECTS_KO = {
    "Imatinib": ["부종", "발진", "설사", "근육통", "골수억제(빈혈/호중구감소)"],
    "Sunitinib": ["고혈압", "수족증후군", "갑상선기능저하", "피로", "설사"],
    "Regorafenib": ["수족피부반응(HFSR)", "간독성(ALT/AST 상승)", "고혈압", "설사", "피로"],
    "Ripretinib": ["탈모", "근육통", "고혈압", "피로", "설사"],
    "Cyclophosphamide": ["골수억제", "오심/구토", "방광염(출혈성)", "탈모"],
    "Doxorubicin": ["심독성", "골수억제", "오심/구토", "탈모", "점막염"],
    "Vincristine": ["말초신경병증", "변비/장폐색", "복통"],
    "Prednisone": ["고혈당", "체중증가", "불면", "위장관 자극"],
    "Bevacizumab": ["고혈압", "단백뇨", "출혈/혈전", "상처치유 지연"],
    "Trastuzumab": ["심기능저하", "주입반응", "설사"],
    "Rituximab": ["주입반응", "감염 위험 증가", "발열/오한"],
    "Osimertinib": ["설사", "발진", "QT 연장", "간수치 상승"],
    "Erlotinib": ["발진", "설사", "간수치 상승"],
    "Gefitinib": ["발진", "설사", "간수치 상승"],
    "Alectinib": ["변비", "피로", "근육통", "간수치 상승"],
    "Lorlatinib": ["고지혈증", "부종", "정신신경 증상"],
    "Paclitaxel": ["말초신경병증", "골수억제", "탈모", "과민반응"],
    "Docetaxel": ["무과립구열", "부종", "피로", "손발톱 변화"],
    "Capecitabine": ["수족증후군", "설사", "구내염"],
    "Oxaliplatin": ["말초감각이상", "골수억제", "오심/구토"],
    "Cisplatin": ["신독성", "오심/구토", "청각독성", "말초신경병증"],
    "Carboplatin": ["골수억제", "오심/구토", "피로"],
    "Irinotecan": ["설사(급성/지연)", "골수억제", "오심/구토"],
    "Fluorouracil": ["점막염", "설사", "골수억제"],
    "5-Fluorouracil": ["점막염", "설사", "골수억제"],
    "5FU": ["점막염", "설사", "골수억제"],
    "5-FU": ["점막염", "설사", "골수억제"],
}

def drug_side_effects(name: str, lang: str = "ko"):
    base = str(name).strip()
    if lang.lower().startswith("ko"):
        arr = (_SIDE_KO_LC.get(_norm_drug(base)) if '_SIDE_KO_LC' in globals() else [])
        return list(arr or [])
    return []

def format_side_effects_bullets(drugs, lang: str = "ko"):
    lines = []
    for d in drugs or []:
        se = drug_side_effects(d, lang)
        if se:
            lines.append(f"- **{drug_kor(d) if 'drug_kor' in globals() else d}**: " + ", ".join(se))
    return "\n".join(lines)
# --- /Side effects patch ---


# --- Case-insensitive normalization for drug lookups ---
def _norm_drug(s):
    try:
        return str(s).strip().lower()
    except Exception:
        return str(s)





# --- Case-insensitive normalization (rebuilt) ---
def _norm_drug(s):
    try:
        return str(s).strip().lower()
    except Exception:
        return str(s)

_DRUG_KO_LC = {str(k).lower(): v for k, v in (DRUG_KO if 'DRUG_KO' in globals() else {}).items()}
_SIDE_KO_LC = {str(k).lower(): v for k, v in (SIDE_EFFECTS_KO if 'SIDE_EFFECTS_KO' in globals() else {}).items()}
# --- /Case-insensitive normalization ---


# --- drug_kor helpers (re-added) ---
def drug_kor(name: str) -> str:
    base = str(name).strip()
    try:
        kor = (_DRUG_KO_LC.get(base.lower()) if '_DRUG_KO_LC' in globals() else None)
        return f"{base}({kor})" if kor else base
    except Exception:
        return base

def format_drug_list_kor(drugs) -> str:
    seen=set(); out=[]
    for d in drugs or []:
        label = drug_kor(d)
        if label not in seen:
            seen.add(label); out.append(label)
    return ", ".join(out)

def drug_side_effects(name: str, lang: str = "ko"):
    base = str(name).strip()
    if lang.lower().startswith("ko"):
        arr = (_SIDE_KO_LC.get(base.lower()) if '_SIDE_KO_LC' in globals() else [])
        return list(arr or [])
    return []
# --- /drug_kor helpers ---



# --- auto-extend KO/SE maps (patch) ---
try:
    DRUG_KO.update({
        "6-MP":"6-머캅토퓨린","ATRA":"트레티노인(ATRA)","Ara-C":"시타라빈(Ara-C)","Arsenic Trioxide":"산화비소(As2O3)",
        "Bendamustine":"벤다무스틴","Bleomycin":"블레오마이신","Brentuximab Vedotin":"브렌툭시맙 베도틴",
        "Cabozantinib":"카보잔티닙","Capmatinib":"캡마티닙","Cetuximab":"세툭시맙","Chlorambucil":"클로람부실",
        "Crizotinib":"크리조티닙","Cytarabine":"시타라빈","Dacarbazine":"다카바진","Daratumumab":"다라투무맙",
        "Daunorubicin":"다우노루비신","Decitabine":"데시타빈","Dinutuximab":"디누툭시맙",
        "Encorafenib":"엔코라페닙","Entrectinib":"엔트렉티닙","Epirubicin":"에피루비신","Etoposide":"에토포사이드",
        "Everolimus":"에버롤리무스","Gilteritinib":"질테리티닙","Goserelin":"고세렐린",
        "Ifosfamide":"이포스파미드","Idarubicin":"이다루비신","Ibrutinib":"이브루티닙","Ipilimumab":"이필리무맙",
        "Lenvatinib":"렌바티닙","Lenalidomide":"레날리도마이드","Melphalan":"멜팔란","Methotrexate":"메토트렉세이트",
        "Midostaurin":"미도스타우린","Mitomycin":"미토마이신","Necitumumab":"네시투무맙","Nilotinib":"닐로티닙",
        "Obinutuzumab":"오비누투주맙","Ofatumumab":"오파투무맙","Olaparib":"올라파립","Panitumumab":"파니투뮤맙",
        "Pertuzumab":"퍼투주맙","Polatuzumab Vedotin":"폴라투주맙 베도틴",
        "Pralsetinib":"프랄세티닙","Ramucirumab":"라무시루맙","Selpercatinib":"셀퍼카티닙","Sorafenib":"소라페닙",
        "Sotorasib":"소토라십","T-DM1":"트라스투주맙 엠탄신","Topotecan":"토포테칸",
        "Trabectedin":"트라벡티딘","Trastuzumab deruxtecan":"트라스투주맙 데룩스테칸",
        "Tucatinib":"투카티닙","Vandetanib":"반데타닙","Vinblastine":"빈블라스틴"
    })
except Exception:
    pass

try:
    SIDE_EFFECTS_KO.update({
        "6-MP":["골수억제","간수치 상승","구역"],
        "ATRA":["분화증후군","두통","피부건조"],
        "Ara-C":["골수억제","점막염","발열"],
        "Arsenic Trioxide":["QT 연장","전해질 이상","피로"],
        "Bendamustine":["골수억제","발열","피로"],
        "Bleomycin":["폐독성","발열","피부변화"],
        "Brentuximab Vedotin":["말초신경병증","주입반응","피로"],
        "Cabozantinib":["고혈압","설사","손발증후군"],
        "Capmatinib":["간수치 상승","부종","오심"],
        "Cetuximab":["발진","저마그네슘혈증","주입반응"],
        "Chlorambucil":["골수억제","오심/구토","감염"],
        "Crizotinib":["시야장애","부종","간수치 상승"],
        "Cytarabine":["골수억제","발열","점막염"],
        "Dacarbazine":["오심/구토","피로","광과민"],
        "Daratumumab":["주입반응","감염 위험","피로"],
        "Daunorubicin":["심독성","골수억제","탈모"],
        "Decitabine":["골수억제","감염","피로"],
        "Dinutuximab":["통증","발열","저혈압"],
        "Encorafenib":["피부발진","관절통","피로"],
        "Entrectinib":["어지러움","체중증가","변비"],
        "Epirubicin":["심독성","골수억제","탈모"],
        "Etoposide":["골수억제","저혈압","오심/구토"],
        "Everolimus":["구내염","고지혈증","감염"],
        "Gilteritinib":["간수치 상승","QT 연장","피로"],
        "Goserelin":["홍조","발한","골밀도 감소"],
        "Ifosfamide":["신경독성","신독성","출혈성 방광염"],
        "Idarubicin":["심독성","골수억제","탈모"],
        "Ibrutinib":["출혈","감염","설사"],
        "Ipilimumab":["면역관련 이상반응(장염/간염)","발진","피로"],
        "Lenvatinib":["고혈압","단백뇨","수족증후군"],
        "Lenalidomide":["혈전증","골수억제","피부발진"],
        "Melphalan":["골수억제","오심/구토","탈모"],
        "Methotrexate":["구내염","간독성","신독성"],
        "Midostaurin":["오심/구토","QT 연장","피로"],
        "Mitomycin":["골수억제","폐독성","신독성"],
        "Necitumumab":["저마그네슘혈증","발진","주입반응"],
        "Nilotinib":["QT 연장","혈당상승","간수치 상승"],
        "Obinutuzumab":["주입반응","감염","호중구감소"],
        "Ofatumumab":["주입반응","감염","피로"],
        "Olaparib":["빈혈","오심/구토","피로"],
        "Panitumumab":["발진","저마그네슘혈증","설사"],
        "Pertuzumab":["심기능저하","설사","주입반응"],
        "Polatuzumab Vedotin":["말초신경병증","골수억제","주입반응"],
        "Pralsetinib":["간수치 상승","고혈압","피로"],
        "Ramucirumab":["고혈압","단백뇨","출혈"],
        "Selpercatinib":["고혈압","QT 연장","간수치 상승"],
        "Sorafenib":["수족증후군","고혈압","설사"],
        "Sotorasib":["설사","ALT/AST 상승","피로"],
        "T-DM1":["혈소판감소","간수치 상승","피로"],
        "Topotecan":["골수억제","오심/구토","탈모"],
        "Trabectedin":["간독성","골수억제","오심/구토"],
        "Trastuzumab deruxtecan":["간질성폐질환","구토","탈모"],
        "Tucatinib":["설사","간수치 상승","피로"],
        "Vandetanib":["QT 연장","설사","발진"],
        "Vinblastine":["골수억제","신경독성","탈모"]
    })
except Exception:
    pass
# --- /auto-extend ---


# --- rebuild lowercase lookup after updates ---
_DRUG_KO_LC = {str(k).lower(): v for k, v in (DRUG_KO if 'DRUG_KO' in globals() else {}).items()}
_SIDE_KO_LC = {str(k).lower(): v for k, v in (SIDE_EFFECTS_KO if 'SIDE_EFFECTS_KO' in globals() else {}).items()}


# --- auto-extend #2 for remaining gaps ---
try:
    DRUG_KO.update({
        "Gemcitabine":"젬시타빈","Pemetrexed":"페메트렉시드","Pazopanib":"파조파닙","Lapatinib":"라파티닙",
        "Larotrectinib":"라로트렉티닙","Dactinomycin":"닥티노마이신","Octreotide":"옥트레오타이드",
        "Niraparib":"니라파립","Nab-Paclitaxel":"나노입자 파클리탁셀","MTX":"메토트렉세이트",
        "Durvalumab":"더발루맙","Atezolizumab":"아테졸리주맙","Nivolumab":"니볼루맙","Pembrolizumab":"펨브롤리주맙"
    })
except Exception:
    pass

try:
    SIDE_EFFECTS_KO.update({
        "Gemcitabine":["골수억제","발열","피로"],
        "Pemetrexed":["골수억제","피로","구내염"],
        "Pazopanib":["고혈압","간수치 상승","설사"],
        "Lapatinib":["설사","발진","간수치 상승"],
        "Larotrectinib":["간수치 상승","어지러움","피로"],
        "Dactinomycin":["골수억제","오심/구토","점막염"],
        "Octreotide":["위장관 증상","담석증","혈당변동"],
        "Niraparib":["혈소판감소","빈혈","오심/구토"],
        "Nab-Paclitaxel":["말초신경병증","골수억제","탈모"],
        "MTX":["구내염","간독성","신독성"],
        "Durvalumab":["면역관련 이상반응(폐렴/장염/간염)","피로","발진"],
        "Atezolizumab":["면역관련 이상반응","피로","가려움"],
        "Nivolumab":["면역관련 이상반응","피로","발진"],
        "Pembrolizumab":["면역관련 이상반응","피로","발진"]
    })
except Exception:
    pass

# rebuild lowercase lookups
_DRUG_KO_LC = {str(k).lower(): v for k, v in (DRUG_KO if 'DRUG_KO' in globals() else {}).items()}
_SIDE_KO_LC = {str(k).lower(): v for k, v in (SIDE_EFFECTS_KO if 'SIDE_EFFECTS_KO' in globals() else {}).items()}
# --- /auto-extend #2 ---


# --- Regimen expansion patch (non-destructive) ---
# Common regimens → component drugs
REGIMEN_MAP = {
    # Hematology
    "CHOP": ["Cyclophosphamide","Doxorubicin","Vincristine","Prednisone"],
    "R-CHOP": ["Rituximab","Cyclophosphamide","Doxorubicin","Vincristine","Prednisone"],
    "EPOCH": ["Etoposide","Prednisone","Vincristine","Cyclophosphamide","Doxorubicin"],
    "R-EPOCH": ["Rituximab","Etoposide","Prednisone","Vincristine","Cyclophosphamide","Doxorubicin"],
    "ABVD": ["Doxorubicin","Bleomycin","Vinblastine","Dacarbazine"],
    "FLAG-IDA": ["Fludarabine","Cytarabine","G-CSF","Idarubicin"],
    # GI
    "FOLFOX": ["Oxaliplatin","Leucovorin","Fluorouracil"],
    "FOLFIRI": ["Irinotecan","Leucovorin","Fluorouracil"],
    "FOLFOXIRI": ["Oxaliplatin","Irinotecan","Leucovorin","Fluorouracil"],
    # GIST
    "TKI-GIST": ["Imatinib","Sunitinib","Regorafenib","Ripretinib"],
    # APL
    "ATRA+ATO": ["ATRA","Arsenic Trioxide"],
    # Myeloma / lymphoma supportive examples
    "BR": ["Bendamustine","Rituximab"],
}

def expand_regimen(item):
    key = str(item).strip().upper()
    return REGIMEN_MAP.get(key, None)

def expand_items(items):
    out = []
    for x in (items or []):
        comp = expand_regimen(x)
        if comp: out.extend(comp)
        else: out.append(x)
    return out
# --- /Regimen expansion patch ---
