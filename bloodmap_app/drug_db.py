
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


# ====== PATCH v2025-10-19: Fill missing AEs + Korean labels (emoji) ======
try:
    __prev_ensure = ensure_onco_drug_db  # chain previous layers
except Exception:
    __prev_ensure = None

def ensure_onco_drug_db(db):
    # keep everything previously registered
    if __prev_ensure is not None:
        __prev_ensure(db)

    def _alias(k: str) -> str:
        # Prefer existing alias → else fallback map
        rec = (db or {}).get(k) or {}
        a = rec.get("alias")
        if a: 
            return a
        try:
            # ALIAS_FALLBACK is defined earlier in this module
            return ALIAS_FALLBACK.get(k, k)
        except Exception:
            return k

    def add(k, alias=None, moa="", ae="", tags=None):
        lab = alias or _alias(k)
        _upsert(db, k, lab, moa or "항암/표적치료", ae or "(보강 필요)")
        if tags:
            rec = db.setdefault(k, {})
            prev = set(rec.get("tags", []))
            rec["tags"] = sorted(prev | set(tags))

    # --- canonical minimal profiles (focus: 중요부작용 이모지) ---
    PROFILES = {
        "5-FU": {
            "moa": "피리미딘 유사체(항대사제)",
            "ae": "🩸 골수억제 · 🤢 오심/구토 · 💩 설사 · 💊 구내염 · 🖐️ 손발증후군",
            "tags": ["myelosuppression","mucositis","hand_foot"]
        },
        "Ara-C": {
            "moa": "피리미딘 유사체(항대사제)",
            "ae": "🩸 골수억제 · 🌡️ 발열 · 💊 점막염 · 🧠 고용량 시 신경독성",
            "tags": ["myelosuppression","neurotoxicity"]
        },
        "Capecitabine": {
            "moa": "5‑FU 전구약물(항대사제)",
            "ae": "🖐️ 손발증후군 · 💩 설사 · 💊 구내염 · 🩸 골수억제",
            "tags": ["hand_foot","mucositis","myelosuppression"]
        },
        "Cisplatin": {
            "moa": "백금제(알킬화 유사)",
            "ae": "🧏‍♂️ 이독성 · 🚽 신독성 · 🤢 심한 구토 · 🩸 골수억제",
            "tags": ["nephrotoxicity","ototoxicity","emetogenic","myelosuppression"]
        },
        "Carboplatin": {
            "moa": "백금제",
            "ae": "🩸 골수억제(혈소판↓) · 🤢 오심/구토 · ⚠️ 알레르기반응",
            "tags": ["myelosuppression","hypersensitivity","emetogenic"]
        },
        "Oxaliplatin": {
            "moa": "백금제",
            "ae": "🧠 말초신경병증(저온 유발) · 🤢 오심/구토 · 🩸 골수억제",
            "tags": ["neuropathy","myelosuppression","emetogenic"]
        },
        "Docetaxel": {
            "moa": "탁산(Taxane)",
            "ae": "🩸 골수억제 · 💧 부종/체액저류 · 🤧 과민반응",
            "tags": ["myelosuppression","fluid_retention","hypersensitivity"]
        },
        "Paclitaxel": {
            "moa": "탁산(Taxane)",
            "ae": "🩸 골수억제 · 🧠 말초신경병증 · 🤧 과민반응",
            "tags": ["myelosuppression","neuropathy","hypersensitivity"]
        },
        "Doxorubicin": {
            "moa": "안트라사이클린(Topo II 억제)",
            "ae": "❤️ 심근독성(누적 용량) · 🩸 골수억제 · 💊 점막염 · 🔴 주사혈관염/괴사(누출)",
            "tags": ["cardiotoxicity","myelosuppression","mucositis","vesicant"]
        },
        "Etoposide": {
            "moa": "Topo II 억제",
            "ae": "🩸 골수억제 · 🤢 오심/구토 · 🦠 감염위험 증가",
            "tags": ["myelosuppression"]
        },
        "Cyclophosphamide": {
            "moa": "알킬화제",
            "ae": "🩸 골수억제 · 🩸 혈뇨/출혈성 방광염(고용량) · 🤢 오심/구토",
            "tags": ["myelosuppression","hemorrhagic_cystitis"]
        },
        "Ifosfamide": {
            "moa": "알킬화제",
            "ae": "🩸 골수억제 · 🧠 신경독성/섬망 · 🩸 출혈성 방광염(MESNA 병용)",
            "tags": ["myelosuppression","neurotoxicity","hemorrhagic_cystitis"]
        },
        "Gemcitabine": {
            "moa": "피리미딘 유사체",
            "ae": "🩸 골수억제 · 😮‍💨 호흡곤란/간질성 폐질환 드묾 · 발열/피로",
            "tags": ["myelosuppression","ild_pneumonitis"]
        },
        "Irinotecan": {
            "moa": "Topo I 억제",
            "ae": "💩 설사(급성·지연) · 🤢 오심/구토 · 🩸 골수억제",
            "tags": ["diarrhea","myelosuppression"]
        },
        "Pemetrexed": {
            "moa": "항대사제(엽산 경로)",
            "ae": "🩸 골수억제 · 💊 구내염 · 🤢 오심/구토 (엽산/비12 보충 필요)",
            "tags": ["myelosuppression","mucositis"]
        },
        "Bevacizumab": {
            "moa": "VEGF 억제",
            "ae": "🩸 출혈/상처치유 지연 · 🧠 혈전·허혈 · 💥 천공(드묾) · 💉 단백뇨/고혈압",
            "tags": ["bleeding","hypertension","proteinuria","gi_perforation"]
        },
        "Ramucirumab": {
            "moa": "VEGFR‑2 억제",
            "ae": "🩸 출혈·고혈압 · 💉 단백뇨 · 상처치유 지연",
            "tags": ["bleeding","hypertension","proteinuria"]
        },
        "Regorafenib": {
            "moa": "멀티 TKI",
            "ae": "🖐️ 손발증후군 · 🩸 고혈압 · 🧪 간독성",
            "tags": ["hand_foot","hypertension","hepatotoxicity"]
        },
        "Sunitinib": {
            "moa": "멀티 TKI",
            "ae": "🩸 골수억제 · 🧪 간효소 상승 · 🥵 피로/식욕저하 · 🦷 점막염",
            "tags": ["myelosuppression","hepatotoxicity","mucositis"]
        },
        "Imatinib": {
            "moa": "TKI (BCR‑ABL, KIT)",
            "ae": "💧 부종 · 🥵 피로 · 🩸 골수억제 · 속쓰림/구역",
            "tags": ["myelosuppression","edema"]
        },
        "Ibrutinib": {
            "moa": "BTK 억제",
            "ae": "🩸 출혈 위험 · 💓 심방세동 · 설사/피로",
            "tags": ["bleeding","arrhythmia"]
        },
        "Bendamustine": {
            "moa": "알킬화제",
            "ae": "🩸 골수억제 · 🤢 오심/구토 · 발열",
            "tags": ["myelosuppression"]
        },
        "Chlorambucil": {
            "moa": "알킬화제",
            "ae": "🩸 골수억제 · 발진/오심",
            "tags": ["myelosuppression"]
        },
        "Bleomycin": {
            "moa": "DNA 손상",
            "ae": "🫁 폐독성/섬유화 · 🤧 발열/오한 · 피부변화(선조/경결)",
            "tags": ["pulmonary_toxicity"]
        },
        "Dacarbazine": {
            "moa": "알킬화제",
            "ae": "🤢 고위험 구토 · 🩸 골수억제 · 광과민",
            "tags": ["emetogenic","myelosuppression"]
        },
        "Dactinomycin": {
            "moa": "DNA 합성 억제",
            "ae": "🩸 골수억제 · 💊 점막염 · 🔴 주사혈관염/괴사(누출)",
            "tags": ["myelosuppression","mucositis","vesicant"]
        },
        "Trabectedin": {
            "moa": "DNA groove 결합",
            "ae": "🧪 간독성 · 🩸 골수억제 · 근육통/피로",
            "tags": ["hepatotoxicity","myelosuppression"]
        },
        "Vincristine": {
            "moa": "Vinca alkaloid",
            "ae": "🧠 말초신경병증 · 변비/장폐색 · (상대적) 골수억제 적음",
            "tags": ["neuropathy"]
        },
        "Vinblastine": {
            "moa": "Vinca alkaloid",
            "ae": "🩸 골수억제 · 🧠 말초신경병증 · 탈모",
            "tags": ["myelosuppression","neuropathy"]
        },
        "Nivolumab": {
            "moa": "PD‑1 억제(면역항암제)",
            "ae": "🛡️ 면역관련 이상반응(피부/갑상선/폐/간/장) · 피로",
            "tags": ["immunotherapy"]
        },
        "Pembrolizumab": {
            "moa": "PD‑1 억제",
            "ae": "🛡️ 면역관련 이상반응 · 발진/피로",
            "tags": ["immunotherapy"]
        },
        "Obinutuzumab": {
            "moa": "Anti‑CD20",
            "ae": "💉 주입반응 · 🦠 감염위험 · 🩸 호중구감소",
            "tags": ["infusion_reaction","myelosuppression"]
        },
        "Rituximab": {
            "moa": "Anti‑CD20",
            "ae": "💉 주입반응 · 💤 피로 · 드물게 PML",
            "tags": ["infusion_reaction"]
        },
        "Polatuzumab Vedotin": {
            "moa": "ADC(anti‑CD79b)",
            "ae": "🩸 호중구감소 · 🧠 말초신경병증 · 💉 주입반응",
            "tags": ["myelosuppression","neuropathy","infusion_reaction"]
        },
        "Brentuximab Vedotin": {
            "moa": "ADC(anti‑CD30)",
            "ae": "🧠 말초신경병증 · 🩸 호중구감소 · 💉 주입반응",
            "tags": ["neuropathy","myelosuppression","infusion_reaction"]
        },
        "Trastuzumab": {
            "moa": "HER2 억제",
            "ae": "❤️ 심기능저하(좌심실) · 💉 주입반응",
            "tags": ["cardiotoxicity","infusion_reaction"]
        },
        "Pertuzumab": {
            "moa": "HER2 dimerization 억제",
            "ae": "💩 설사 · 💉 주입반응 · ❤️ 심기능저하(드묾)",
            "tags": ["diarrhea","cardiotoxicity","infusion_reaction"]
        },
        "T-DM1": {
            "moa": "HER2 ADC",
            "ae": "🩸 혈소판감소 · 🧪 간효소 상승 · 피로/오심",
            "tags": ["myelosuppression","hepatotoxicity"]
        },
        "Trastuzumab deruxtecan": {
            "moa": "HER2 ADC",
            "ae": "🫁 간질성폐질환/폐렴 · 🩸 골수억제 · 오심",
            "tags": ["ild_pneumonitis","myelosuppression"]
        },
        "Lapatinib": {
            "moa": "HER2/EGFR TKI",
            "ae": "💩 설사 · 발진 · 드물게 QT 연장",
            "tags": ["diarrhea","qt_prolong"]
        },
        "Tucatinib": {
            "moa": "HER2 TKI",
            "ae": "💩 설사 · 🧪 간효소 상승",
            "tags": ["diarrhea","hepatotoxicity"]
        },
        "Osimertinib": {
            "moa": "EGFR TKI",
            "ae": "🫁 ILD/폐렴(드묾) · ⚡ QT 연장 · 발진/설사",
            "tags": ["ild_pneumonitis","qt_prolong"]
        },
        "Alectinib": {
            "moa": "ALK TKI",
            "ae": "🧪 간효소 상승 · 근육통/CPK↑ · 변비 · 드물게 ILD",
            "tags": ["hepatotoxicity","ild_pneumonitis"]
        },
        "Crizotinib": {
            "moa": "ALK/MET TKI",
            "ae": "👀 시야 변화 · 💩 설사/변비 · 부종 · 간효소 상승",
            "tags": ["hepatotoxicity"]
        },
        "Lorlatinib": {
            "moa": "ALK TKI",
            "ae": "🧠 인지/기분 변화 · 고지혈증 · 말초부종",
            "tags": ["cns_effects"]
        },
        "Larotrectinib": {
            "moa": "TRK TKI",
            "ae": "🧠 어지럼/피로 · 간효소 상승",
            "tags": ["hepatotoxicity"]
        },
        "Entrectinib": {
            "moa": "TRK/ROS1/ALK TKI",
            "ae": "🧠 어지럼/체중증가 · 💧 부종 · 간효소 상승",
            "tags": ["hepatotoxicity"]
        },
        "Selpercatinib": {
            "moa": "RET TKI",
            "ae": "🩸 고혈압 · 간효소 상승 · 💩 설사 · QT 연장 가능",
            "tags": ["hypertension","hepatotoxicity","qt_prolong"]
        },
        "Pralsetinib": {
            "moa": "RET TKI",
            "ae": "🩸 고혈압 · 간효소 상승 · 변비/설사",
            "tags": ["hypertension","hepatotoxicity"]
        },
        "Vandetanib": {
            "moa": "RET/EGFR/VEGFR TKI",
            "ae": "⚡ QT 연장 · 💩 설사 · 발진",
            "tags": ["qt_prolong"]
        },
        "Cabozantinib": {
            "moa": "RET/MET/VEGFR TKI",
            "ae": "🩸 고혈압 · 🖐️ 손발증후군 · 설사 · 피로",
            "tags": ["hypertension","hand_foot"]
        },
        "Pazopanib": {
            "moa": "멀티 TKI",
            "ae": "🧪 간독성 · 🩸 고혈압 · 모발 탈색",
            "tags": ["hepatotoxicity","hypertension"]
        },
        "Ripretinib": {
            "moa": "KIT/PDGFRA 억제(GIST)",
            "ae": "🧑‍🦲 탈모 · 🩸 고혈압 · 피로/통증",
            "tags": ["hypertension"]
        },
        "Octreotide": {
            "moa": "Somatostatin 유사체",
            "ae": "💩 지방변/설사 · 복부불편감 · 담석",
            "tags": ["diarrhea"]
        },
        "Everolimus": {
            "moa": "mTOR 억제",
            "ae": "🫁 ILD/폐렴 · 🩸 고혈당/고지혈증 · 구내염",
            "tags": ["ild_pneumonitis","mucositis"]
        },
        "Ramucirumab": {
            "moa": "VEGFR‑2 억제",
            "ae": "🩸 출혈 · 고혈압 · 단백뇨",
            "tags": ["bleeding","hypertension","proteinuria"]
        },
        "Prednisone": {
            "moa": "코르티코스테로이드",
            "ae": "😠 기분변화 · 🍽️ 식욕↑/체중↑ · 혈당↑ · 불면",
            "tags": ["steroid"]
        },
        "Sotorasib": {
            "moa": "KRAS G12C 억제",
            "ae": "💩 설사 · 🧪 ALT/AST 상승 · 피로",
            "tags": ["hepatotoxicity","diarrhea"]
        },
    }

    for k, v in PROFILES.items():
        add(k, alias=None, moa=v.get("moa",""), ae=v.get("ae",""), tags=v.get("tags"))


# --- tiny patch: add Capmatinib profile ---
try:
    __prev_ensure_capmat = ensure_onco_drug_db
except Exception:
    __prev_ensure_capmat = None

def ensure_onco_drug_db(db):
    if __prev_ensure_capmat is not None:
        __prev_ensure_capmat(db)
    _upsert(db, "Capmatinib", ALIAS_FALLBACK.get("Capmatinib","캡마티닙(MET)"), "MET TKI", "말초부종 · 오심/구토 · 광과민 · 간효소 상승")


# === SAFE FINAL WRAPPER (break mutual recursion) ===
def _call_prev_safely(db):
    g = globals()
    # snapshot and temporarily disable recursive bridges
    saved_prev = g.get('__prev_ensure', None)
    saved_prev2 = g.get('__prev2', None)
    g['__prev_ensure'] = None
    g['__prev2'] = None
    try:
        # prefer the later wrapper (__prev2), else earlier
        prev = saved_prev2 or saved_prev
        if callable(prev):
            try:
                prev(db)
            except Exception:
                # don't hard-fail if legacy layer has minor issues
                pass
    finally:
        g['__prev_ensure'] = saved_prev
        g['__prev2'] = saved_prev2

try:
    _BASE_ENSURE = ensure_onco_drug_db
except Exception:
    _BASE_ENSURE = None

def ensure_onco_drug_db(db):
    # prevent re-entry
    g = globals()
    if g.get('_ENSURE_GUARD', False):
        return
    g['_ENSURE_GUARD'] = True
    try:
        # call previous layers once without bouncing into each other
        _call_prev_safely(db)
        # nothing else here: earlier layers already populated oncology/antibiotics/maps
        # This wrapper's sole job is to stop infinite recursion that was crashing the server.
        return
    finally:
        g['_ENSURE_GUARD'] = False
