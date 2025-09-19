# -*- coding: utf-8 -*-
"""
핵심 중증 부작용(요약) 오버레이
- DRUG_DB 키와 매칭되도록 가능한 한 일반명 기준
- 키 매칭: 대소문자 무시, 공백/슬래시/하이픈 제거 후 비교 + 별칭 대응
"""

CRITICAL_AE = {
    # 세포독성 항암제
    "CYTARABINE": [
        "고용량(HiDAC): **소뇌실조/언어장애**, **각결막염**(스테로이드 점안 예방)",
        "드물게 **심장막삼출/심막염** 보고 — 흉통/호흡곤란 시 즉시 평가",
        "일반용량: 골수억제, 발열성 호중구감소증, 발진",
    ],
    "DOXORUBICIN": [
        "**누적용량 의존성 심근병증/심부전** — 누적 용량·심초음파 모니터",
        "심근허혈/부정맥, 점막염, 탈모, 심한 오심구토",
    ],
    "DAUNORUBICIN": [
        "**심장독성(누적용량)**, 골수억제, 점막염",
    ],
    "EPIRUBICIN": [
        "**심근병증/심부전(누적용량)**, 점막염",
    ],
    "CYCLOPHOSPHAMIDE": [
        "**출혈성 방광염**(아크롤레인) — **MESNA/수분요법**",
        "SIADH, 고용량 시 심장독성",
    ],
    "IFOSFAMIDE": [
        "**신경독성/섬망**(뇌병증), **신독성/팬코니증후군**, 출혈성 방광염 — MESNA 필요",
    ],
    "CISPLATIN": [
        "**신독성**(수액·Mg 보충), **오토톡시시티(난청/이명)**, 말초신경병증, 심한 오심구토",
        "전해질 이상: Mg/K/Ca 감소",
    ],
    "CARBOPLATIN": [
        "골수억제(혈소판↓), 과민반응(누적 주기 후)",
    ],
    "OXALIPLATIN": [
        "**한랭 유발 감각이상/후두경련** — 차가운 것 회피, 만성 말초신경병증",
    ],
    "METHOTREXATE": [
        "**고용량(HD-MTX): 신독성/요산염 결석** — **류코보린 구제**, 알칼리뇨, 농도 모니터",
        "간독성/섬유화, 점막염, 골수억제",
    ],
    "5-FLUOROURACIL": [
        "**DPD 결핍 시 중증 독성**(골수억제/점막염/설사) — 필요시 DPD 검사",
        "**관상동맥 연축/흉통** 가능, 손발증후군, 설사",
    ],
    "CAPECITABINE": [
        "손발증후군, 설사; **DPD 결핍** 위험 유사",
    ],
    "VINCRISTINE": [
        "**말초신경병증**, **장마비/변비** — 완하제 고려, **용량 단위 오류(FATAL) 주의: mg**",
    ],
    "VINBLASTINE": [
        "말초신경병증(상대적으로 덜함), 골수억제",
    ],
    "ETOPOSIDE": [
        "저혈압(급속투여), 골수억제; 장기적으로 **이차성 AML** 위험",
    ],
    "BLEOMYCIN": [
        "**폐섬유화/간질성폐질환** — 누적용량/고령/산소노출 시 위험↑, 폐기능 모니터",
    ],
    "IRINOTECAN": [
        "**급성 콜린성 증상**(투여 중) — 아트로핀, **지연성 심한 설사** — 로페라마이드 고용량 요법",
    ],
    "PACLITAXEL": [
        "과민반응(전처치 필요), 말초신경병증, 무월경",
    ],
    "DOCETAXEL": [
        "체액저류/말초부종, 손발톱 변화, 점막염",
    ],
    "ASPARAGINASE": [
        "**췌장염**, **혈전/출혈**(항응고계 이상), 간독성, 고혈당",
    ],
    "GEMCITABINE": [
        "골수억제, 간질성폐렴/폐섬유화 드물게, TMA 보고",
    ],
    "TOPOTECAN": [
        "강한 골수억제(호중구감소증), 설사, 점막염",
    ],
    "TEMOZOLOMIDE": [
        "골수억제, **PJP 폐렴** 위험 — 스테로이드 병용 시 PJP 예방 고려",
    ],
    "DACARBAZINE": [
        "강한 오심구토, 간독성(희귀: 간정맥폐쇄병 VOD)",
    ],
    "PROCARBAZINE": [
        "MAO 억제 특성 — **치즈/티라민 음식·상호작용 주의**, 골수억제",
    ],
    "MERCAPTOPURINE": [
        "TPMT/NUDT15 변이 시 **중증 골수억제** — 유전자 검사 고려",
    ],
    "THIOGUANINE": [
        "간정맥폐쇄병(VOD) 위험, 골수억제",
    ],
    "CLADRIBINE": [
        "심한 림프구감소·감염, **PJP/HSV 예방** 고려",
    ],
    "FLUDARABINE": [
        "강한 면역억제, 누적 시 신경독성 보고, **PJP/HSV 예방**",
    ],
    "BENDAMUSTINE": [
        "골수억제, 피부독성(SJS/TEN 드묾), 감염 위험",
    ],
    # 표적/항체/기타
    "BORTEZOMIB": [
        "말초신경병증, **HSV 재활성화** — 아시클로버 예방 고려, 저혈압",
    ],
    "CARFILZOMIB": [
        "심부전/심근병증, 고혈압 위기, 호흡곤란",
    ],
    "LENALIDOMIDE": [
        "혈전 위험(항응고 고려), 골수억제, 기형유발 — **임신 금기/REMS**",
    ],
    "POMALIDOMIDE": [
        "혈전 위험, 골수억제, 기형유발 — **임신 금기**",
    ],
    "THALIDOMIDE": [
        "말초신경병증, 혈전 위험, 기형유발",
    ],
    "PANOBINOSTAT": [
        "QT 연장/부정맥, 설사, 혈소판감소",
    ],
    "VORINOSTAT": [
        "고혈당, 혈소판감소, 피로",
    ],
    "BRENTUXIMAB VEDOTIN": [
        "말초신경병증, **PML** 드묾, 중성구감소증, 주입반응",
    ],
    "POLATUZUMAB VEDOTIN": [
        "말초신경병증, 골수억제",
    ],
    "OBINUTUZUMAB": [
        "강한 주입반응, **HBV 재활성화**",
    ],
    "OFATUMUMAB": [
        "주입반응, 감염 위험, HBV 재활성화",
    ],
    "MOGAMULIZUMAB": [
        "피부독성(SJS/TEN 드묾), 주입반응",
    ],
    "TRASTUZUMAB": [
        "**좌심실 기능저하/심부전** — 안트라사이클린 병용 시 위험↑, 심초음파 모니터",
    ],
    "RITUXIMAB": [
        "**주입반응** — 첫 주기 특히, **HBV 재활성화** 위험(투여 전 HBV 스크리닝)",
        "PML(희귀) 보고",
    ],
    "BEVACIZUMAB": [
        "**창상치유 지연**, **위장관 천공**, **출혈/혈전**, 고혈압/단백뇨",
    ],
    "IMATINIB": [
        "체액저류/부종, 근육경련, 간효소 상승",
    ],
    "OSIMERTINIB": [
        "QT 연장, 간질성폐질환(폐렴) 보고",
    ],
    "IBRUTINIB": [
        "출혈/피하출혈, 심방세동, 고혈압 — 수술 전 중단 고려",
    ],
    "ACALABRUTINIB": [
        "두통(빈번), 출혈, 심방세동 드묾",
    ],
    "IDELALISIB": [
        "심한 대장염/간염/폐렴 — 조기 스테로이드·항생제",
    ],
    "COPANLISIB": [
        "고혈당/고혈압 주입 직후 상승, 감염 위험",
    ],
    "VENETOCLAX": [
        "**종양용해증후군(TLS)** — 점진적 증량, 수액/요산강하제",
    ],
    "SELINEXOR": [
        "심한 오심구토/식욕부진/저나트륨혈증 — 적극 지지요법",
    ],
    "BLINATUMOMAB": [
        "**CRS**, **신경독성(혼동/경련)** — 스테로이드·토실리주맙 알고리즘",
    ],
    "INOTUZUMAB OZOGAMICIN": [
        "간정맥폐쇄병(VOD) 위험↑ — 이식 전후 주의, 골수억제",
    ],
    "TISAGENLECLEUCEL": [
        "**CAR-T**: CRS/ICANS — 토실리주맙/스테로이드 프로토콜, 감염/저감마글로불린혈증",
    ],
    "AXICABTAGENE CILOLEUCEL": [
        "**CAR-T**: CRS/ICANS 관리 동일, 감염 위험",
    ],
    "CRIZOTINIB": [
        "시야흐림/시각장애, QT 연장, 간효소 상승",
    ],
    "SUNITINIB": [
        "고혈압/단백뇨, 손발증후군, 갑상선기능저하, 심부전 드묾",
    ],
    "SORAFENIB": [
        "손발증후군, 고혈압, 출혈 위험",
    ],
}

# 별칭 매핑
ALIASES = {
    "ARAC": "CYTARABINE",
    "ARA-C": "CYTARABINE",
    "ADR": "DOXORUBICIN",
    "5FU": "5-FLUOROURACIL",
    "S1": "TEGAFUR/GIMERACIL/OTERACIL",
    "VCR": "VINCRISTINE",
    "VBL": "VINBLASTINE",
    "BTZ": "BORTEZOMIB",
}

def _normalize(s: str) -> str:
    return "".join(ch for ch in s.upper() if ch.isalnum())

def _canon(key: str) -> str:
    k = _normalize(key)
    # 직접 키
    for base in CRITICAL_AE.keys():
        if _normalize(base) == k:
            return base
    # 별칭
    for alias, base in ALIASES.items():
        if _normalize(alias) == k:
            return base
    # 포함 매칭(유연 매칭)
    for base in CRITICAL_AE.keys():
        if _normalize(base) in k or k in _normalize(base):
            return base
    return ""

def get_critical_ae(keys, display_label_func=lambda x: x):
    """입력 key 리스트에서 매칭되는 핵심 AE를 [(라벨, [문장..]), ...]로 반환"""
    out = []
    seen = set()
    for k in (keys or []):
        base = _canon(str(k))
        if base and base not in seen:
            seen.add(base)
            out.append((display_label_func(base), CRITICAL_AE[base]))
    return out
