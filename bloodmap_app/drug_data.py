# -*- coding: utf-8 -*-
# 약물 및 진단/카테고리 데이터 (간단 버전)
CANCER_GROUPS = {
    "혈액암": [
        "AML(급성골수성백혈병)",
        "APL(급성전골수구백혈병)",
        "ALL(급성림프구백혈병)",
        "CML(만성골수성백혈병)",
        "CLL(만성림프구백혈병)"
    ],
    "고형암": [
        "폐암",
        "유방암",
        "위암",
        "대장암",
        "간암",
        "췌장암",
        "담도암"
    ],
    "육종(Sarcoma)": [
        "골육종(Osteosarcoma)",
        "유잉육종(Ewing sarcoma)",
        "횡문근육종(Rhabdomyosarcoma)",
        "평활근육종(Leiomyosarcoma)",
        "지방육종(Liposarcoma)"
    ],
    "희귀암": [
        "신경내분비종양",
        "지속성흉선종",
        "복강육종(기타)"
    ],
}

CHEMO_BY_GROUP_OR_DX = {
    # 혈액암 예시
    "AML(급성골수성백혈병)": ["시타라빈(ARA-C)", "도우노루비신(Daunorubicin)", "미토잔트론(Mitoxantrone)"],
    "APL(급성전골수구백혈병)": ["트레티노인(ATRA, 베사노이드)", "아토산(Arsenic trioxide)"],
    "ALL(급성림프구백혈병)": ["빈크리스틴(Vincristine)", "메토트렉세이트(MTX)", "6-머캅토퓨린(6-MP)"],
    "CML(만성골수성백혈병)": ["이미티닙(Imatinib)", "다사티닙(Dasatinib)"],
    "CLL(만성림프구백혈병)": ["플루다라빈(Fludarabine)", "사이클로포스파마이드(Cyclophosphamide)"],

    # 고형암(일부)
    "폐암": ["시스플라틴(Cisplatin)", "카보플라틴(Carboplatin)", "파클리탁셀(Paclitaxel)", "도세탁셀(Docetaxel)"],
    "유방암": ["독소루비신(Doxorubicin)", "도세탁셀(Docetaxel)", "사이클로포스파마이드(Cyclophosphamide)"],

    # 육종
    "골육종(Osteosarcoma)": ["메토트렉세이트(MTX)", "독소루비신(Doxorubicin)", "시스플라틴(Cisplatin)"],
    "유잉육종(Ewing sarcoma)": ["빈크리스틴(Vincristine)", "이포스파마이드(Ifosfamide)", "독소루비신(Doxorubicin)", "에토포사이드(Etoposide)"],
    "횡문근육종(Rhabdomyosarcoma)": ["빈크리스틴(Vincristine)", "독소루비신(Doxorubicin)", "사이클로포스파마이드(Cyclophosphamide)"],
    "평활근육종(Leiomyosarcoma)": ["독소루비신(Doxorubicin)", "이포스파마이드(Ifosfamide)", "파조파닙(Pazopanib)"],
    "지방육종(Liposarcoma)": ["독소루비신(Doxorubicin)", "이포스파마이드(Ifosfamide)"],

    # 그룹 fallback
    "육종(Sarcoma)": ["독소루비신(Doxorubicin)", "이포스파마이드(Ifosfamide)", "파조파닙(Pazopanib)"]
}

ANTIBIOTICS_KR = [
    "세프트리악손", "피페라실린/타조박탐", "메로페넴",
    "반코마이신", "레보플록사신", "시프로플록사신",
    "아목시실린/클라불란산", "클린다마이신", "아지스로마이신"
]
