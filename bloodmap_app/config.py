# -*- coding: utf-8 -*-
# 전역 설정 및 ORDER 기반 20항목 패널
APP_TITLE = "🩸 피수치 가이드 / BloodMap v3.14.7"
APP_TAGLINE = "제작: Hoya/GPT  ·  자문: Hoya/GPT  ·  (학술 참고용, 의학적 판단은 의료진에게)"

# ORDER: (key, label, unit, decimals)
ORDER = [
    ("wbc", "WBC (백혈구)", "×10³/µL", 1),
    ("hb", "Hb (혈색소)", "g/dL", 1),
    ("plt", "혈소판 (PLT)", "×10³/µL", 0),
    ("anc", "ANC (호중구)", "/µL", 0),
    ("ca", "Ca (칼슘)", "mg/dL", 1),
    ("p", "P (인)", "mg/dL", 1),
    ("na", "Na (소디움)", "mmol/L", 0),
    ("k", "K (포타슘)", "mmol/L", 1),
    ("albumin", "Albumin (알부민)", "g/dL", 1),
    ("glucose", "Glucose (혈당)", "mg/dL", 0),
    ("tp", "Total Protein (총단백)", "g/dL", 1),
    ("ast", "AST", "U/L", 0),
    ("alt", "ALT", "U/L", 0),
    ("ldh", "LDH", "U/L", 0),
    ("crp", "CRP", "mg/dL", 2),
    ("cr", "Creatinine (Cr)", "mg/dL", 2),
    ("ua", "Uric Acid (요산)", "mg/dL", 1),
    ("tb", "Total Bilirubin (TB)", "mg/dL", 2),
    ("bun", "BUN", "mg/dL", 0),
    ("bnp", "BNP", "pg/mL", 0),
]

# 기본 임상 범례 (간단 기준)
CUTS = {
    "albumin_low": 3.5,
    "k_low": 3.5,
    "hb_low": 10.0,
    "na_low": 135.0,
    "ca_low": 8.5,
    "anc_neutropenia": 500,
}

NUTRITION_GUIDE = {
    "albumin_low": "알부민 낮음: 달걀, 연두부, 흰살 생선, 닭가슴살, 귀리죽",
    "k_low": "칼륨 낮음: 바나나, 감자, 호박죽, 고구마, 오렌지",
    "hb_low": "헤모글로빈 낮음: 소고기, 시금치, 두부, 달걀 노른자, 렌틸콩 (철분제는 권장 X)",
    "na_low": "나트륨 낮음: 전해질 음료, 미역국, 바나나, 오트밀죽, 삶은 감자",
    "ca_low": "칼슘 낮음: 연어 통조림, 두부, 케일, 브로콜리",
    "anc_low": "ANC<500: 생채소 금지, 익힌 음식 30초+, 멸균식품 권장, 남은 음식 2시간 이후 비권장, 껍질 과일은 주치의와 상담",
}

CANCER_GROUPS = ["혈액암", "고형암", "육종", "희귀암"]

# 육종(진단명) 분리
SARCOMA_TYPES = [
    "연부조직육종", "골육종", "유잉육종", "활막육종", "지방육종", "섬유육종", "평활근육종", "혈관육종"
]

# 항암제(한글 표기) — 예시
ANTICANCER_BY_GROUP = {
    "혈액암": ["아라시티딘(ARA-C)", "메토트렉세이트(MTX)", "6-머캅토퓨린(6-MP)", "아트라(ATRA)", "도우노루비신", "에토포사이드"],
    "고형암": ["시스플라틴", "카보플라틴", "파클리탁셀", "독소루비신", "이포스파마이드"],
    "육종": ["독소루비신", "이포스파마이드", "파조파닙"],
    "희귀암": ["이미티닙", "수니티닙"]
}

# ARA-C 제형 옵션
ARAC_FORMS = ["정맥(IV)", "피하(SC)", "고용량(HDAC)"]

# 항생제(한글 표기, 세대 구분 없이 이해 쉬운 이름 위주)
ANTIBIOTICS = [
    "아목시실린/클라불란산", "세프트리악손", "세포탁심", "피페라실린/타조박탐", "메로페넴",
    "반코마이신", "라인졸리드", "레보플록사신", "아지트로마이신"
]

# 특수검사 토글 묶음
SPECIAL_PANELS = {
    "응고패널": [
        ("pt", "PT (sec)", "sec", 1),
        ("aptt", "aPTT (sec)", "sec", 1),
        ("fib", "Fibrinogen (mg/dL)", "mg/dL", 0),
        ("ddimer", "D-dimer (µg/mL FEU)", "µg/mL FEU", 2),
        ("dic", "DIC Score (pt)", "pt", 0),
    ],
    "보체": [
        ("c3", "C3 (Complement)", "mg/dL", 0),
        ("c4", "C4 (Complement)", "mg/dL", 0),
    ],
    "요검사": [
        ("ua_protein", "요단백 (Protein, urine)", None, None),
        ("ua_blood", "잠혈 (Occult blood, urine)", None, None),
        ("ua_glucose", "요당 (Glucose, urine)", None, None),
    ]
}
