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
    _upsert(db, "Ara-C", "시타라빈(Ara‑C)", "시티딘 유사체", "골수억제, 결막염(점안 예방), 소뇌증상(고용량)")
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
    # ▼▼ ensure_onco_drug_db(...) 맨 끝부분(리턴 전)에 아래 블록을 그대로 붙여넣으세요 ▼▼

    # --- 추가 보강: ONCO 맵과 일치하도록 누락 항목 등록 ---
    _upsert(db, "Doxorubicin", "독소루비신(Adriamycin)", "Topo II 억제(안트라사이클린)", "심근독성(누적), 골수억제, 점막염, 탈모")
    _upsert(db, "Chlorambucil", "클로람부실", "알킬화제", "골수억제, 오심/구토")

    # Lymphoma / HL 확장
    _upsert(db, "Obinutuzumab", "오비누투주맙(CD20)", "CD20 단일클론항체", "주입반응, 감염위험, HBV 재활성화")
    _upsert(db, "Polatuzumab Vedotin", "폴라투주맙 베도틴(CD79b ADC)", "CD79b 표적 항체‑약물 접합체", "말초신경병증, 골수억제, 주입반응")
    _upsert(db, "Pembrolizumab", "펨브롤리주맙(PD-1)", "PD-1 면역관문억제제", "면역관련 이상반응(피부/대장염/간염/내분비)")
    _upsert(db, "Nivolumab", "니볼루맙(PD-1)", "PD-1 면역관문억제제", "면역관련 이상반응")

    # NSCLC (EGFR/ALK/ROS1/MET/KRAS/NTRK)
    _upsert(db, "Osimertinib", "오시머티닙(EGFR)", "EGFR TKI(Ex19del/L858R/T790M)", "설사, 발진, 드물게 ILD")
    _upsert(db, "Alectinib", "알렉티닙(ALK)", "ALK TKI", "근육통, 변비, 간효소 상승")
    _upsert(db, "Crizotinib", "크리조티닙(ALK/ROS1)", "ALK/ROS1 TKI", "시야 흐림, 위장관 증상")
    _upsert(db, "Lorlatinib", "로를라티닙(ALK)", "ALK TKI", "지질 상승, 인지/기분 변화")
    _upsert(db, "Entrectinib", "엔트렉티닙(ROS1/NTRK)", "ROS1/NTRK TKI", "체중 증가, 어지러움")
    _upsert(db, "Larotrectinib", "라로트렉티닙(NTRK)", "NTRK TKI", "피로, 어지러움")
    _upsert(db, "Capmatinib", "캡마티닙(MET)", "MET TKI", "말초부종, 간효소 상승")
    _upsert(db, "Sotorasib", "소토라십(KRAS G12C)", "KRAS G12C 억제제", "설사, 간효소 상승")

    # HCC / Urothelial
    _upsert(db, "Atezolizumab", "아테졸리주맙(PD-L1)", "PD-L1 면역관문억제제", "면역관련 이상반응")
    _upsert(db, "Durvalumab", "더발루맙(PD-L1)", "PD-L1 면역관문억제제", "면역관련 이상반응")
    _upsert(db, "Lenvatinib", "렌바티닙", "VEGFR/FGFR TKI", "고혈압, 단백뇨")
    _upsert(db, "Sorafenib", "소라페닙", "VEGFR/RAF TKI", "손발증후군, 고혈압")

    # CRC / Gastric
    _upsert(db, "Cetuximab", "세툭시맙(EGFR)", "EGFR 단일클론항체", "여드름양 발진, 저마그네슘혈증")
    _upsert(db, "Panitumumab", "파니투무맙(EGFR)", "EGFR 단일클론항체", "피부발진, 저마그네슘혈증")
    _upsert(db, "Ramucirumab", "라무시루맙(VEGFR2)", "VEGFR2 단일클론항체", "고혈압, 출혈위험")
    _upsert(db, "Regorafenib", "레고라페닙", "멀티키나아제 억제제", "손발증후군, 피로, 고혈압")

    # GIST / Thyroid (RET)
    _upsert(db, "Ripretinib", "리프레티닙", "KIT/PDGFRA 억제(GIST)", "탈모, 피로, 손발증후군")
    _upsert(db, "Vandetanib", "반데타닙(RET)", "RET/VEGFR/EGFR TKI", "QT 연장, 설사, 발진")
    _upsert(db, "Cabozantinib", "카보잔티닙", "MET/VEGFR/RET TKI", "설사, 피로, 손발증후군")
    _upsert(db, "Selpercatinib", "셀퍼카티닙(RET)", "RET TKI(NSCLC/MTC)", "고혈압, 간효소 상승, QT 연장 드묾")
    _upsert(db, "Pralsetinib", "프랄세티닙(RET)", "RET TKI(NSCLC/MTC)", "고혈압, 간효소 상승, 변비/설사")

    # Ovarian / Breast (HER2 & PARP)
    _upsert(db, "Olaparib", "올라파립(PARP)", "PARP 억제제", "빈혈, 피로, 오심")
    _upsert(db, "Niraparib", "니라파립(PARP)", "PARP 억제제", "혈소판 감소, 피로")
    _upsert(db, "Pertuzumab", "퍼투주맙(HER2)", "HER2 dimer 억제", "설사, LVEF 감소")
    _upsert(db, "T-DM1", "아도-트라스투주맙 엠탄신(T-DM1)", "HER2 ADC", "혈소판 감소, 간독성")
    _upsert(db, "Trastuzumab deruxtecan", "트라스투주맙 데룩스테칸(T-DXd)", "HER2 ADC", "간질성 폐질환(ILD) 위험, 오심")
    _upsert(db, "Tucatinib", "투카티닙(HER2)", "HER2 TKI", "설사, 간효소 상승")
    _upsert(db, "Lapatinib", "라파티닙(HER2)", "HER2 TKI", "설사, 발진")

    # Solid chemo 보강
    _upsert(db, "Nab-Paclitaxel", "나브-파클리탁셀", "알부민 결합 파클리탁셀", "말초신경병증, 골수억제, 탈모")
    _upsert(db, "Topotecan", "토포테칸", "Topo I 억제(난소/소세포폐암)", "골수억제, 피로, 오심")

    # ▲▲ 여기까지 붙여넣고 저장 후, 앱을 재시작하세요 ▲▲


