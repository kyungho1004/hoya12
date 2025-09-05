# -*- coding: utf-8 -*-
from typing import Dict, List, Tuple

# Helper to render "English (Korean)"
def ko(en: str, ko: str) -> str:
    return f"{en} ({ko})"

CHEMO_BY_DIAGNOSIS: Dict[str, Dict[str, List[str]]] = {
    "혈액암": {
        "AML(급성 골수성 백혈병)": [
            ko("Cytarabine", "시타라빈/아라씨"),
            ko("Daunorubicin", "다우노루비신"),
            ko("Idarubicin", "이달루비신"),
            ko("Mitoxantrone", "미토잔트론"),
            ko("Etoposide", "에토포사이드"),
            ko("Fludarabine", "플루다라빈"),
        ],
        "APL(급성 전골수성 백혈병)": [
            ko("ATRA", "베사노이드(비스트레티노인)"),
            ko("Arsenic trioxide", "비소 트리옥사이드"),
            ko("Idarubicin", "이달루비신"),
            ko("Cytarabine", "아라씨"),
        ],
        "ALL(급성 림프구성 백혈병)": [
            ko("Methotrexate", "메토트렉세이트(MTX)"),
            ko("6-Mercaptopurine", "6-MP(머캅토퓨린)"),
            ko("Cyclophosphamide", "사이클로포스파마이드"),
            ko("Doxorubicin", "독소루비신"),
            ko("Cytarabine", "아라씨"),
            ko("Vincristine", "빈크리스틴"),
        ],
        "CML(만성 골수성 백혈병)": [
            ko("Hydroxyurea", "하이드록시우레아"),
            ko("Imatinib", "이미티닙"),
        ],
        "CLL(만성 림프구성 백혈병)": [
            ko("Cyclophosphamide", "사이클로포스파마이드"),
            ko("Fludarabine", "플루다라빈"),
            ko("Bendamustine", "벤다무스틴"),
        ],
    },
    "고형암": {
        "폐암": [
            ko("Cisplatin", "시스플라틴"),
            ko("Carboplatin", "카보플라틴"),
            ko("Paclitaxel", "파클리탁셀"),
            ko("Docetaxel", "도세탁셀"),
            ko("Gemcitabine", "젬시타빈"),
            ko("Pemetrexed", "페메트렉시드"),
        ],
        "유방암": [
            ko("Doxorubicin", "독소루비신"),
            ko("Cyclophosphamide", "사이클로포스파마이드"),
            ko("Paclitaxel", "파클리탁셀"),
            ko("Docetaxel", "도세탁셀"),
        ],
        "위암": [
            ko("Cisplatin", "시스플라틴"),
            ko("5-FU", "플루오로우라실"),
            ko("Capecitabine", "카페시타빈"),
        ],
        "대장암": [
            ko("Oxaliplatin", "옥살리플라틴"),
            ko("Irinotecan", "이리노테칸"),
            ko("5-FU", "플루오로우라실"),
            ko("Capecitabine", "카페시타빈"),
        ],
    },
    "육종": {
        "골육종(Osteosarcoma)": [
            ko("Doxorubicin", "독소루비신"),
            ko("Cisplatin", "시스플라틴"),
            ko("High-dose Methotrexate", "고용량 메토트렉세이트"),
            ko("Ifosfamide", "이포스파미드"),
        ],
        "유잉육종(Ewing Sarcoma)": [
            ko("Vincristine", "빈크리스틴"),
            ko("Doxorubicin", "독소루비신"),
            ko("Cyclophosphamide", "사이클로포스파마이드"),
            ko("Ifosfamide", "이포스파미드"),
            ko("Etoposide", "에토포사이드"),
        ],
        "평활근육종(Leiomyosarcoma)": [
            ko("Doxorubicin", "독소루비신"),
            ko("Ifosfamide", "이포스파미드"),
            ko("Pazopanib", "파조파닙"),
        ],
        "횡문근육종(Rhabdomyosarcoma)": [
            ko("Vincristine", "빈크리스틴"),
            ko("Actinomycin D", "아크티노마이신 D"),
            ko("Cyclophosphamide", "사이클로포스파마이드"),
        ],
        "GIST(위장관기질종양)": [
            ko("Imatinib", "이미티닙"),
            ko("Sunitinib", "수니티닙"),
        ],
    },
    "희귀암": {
        "HLH(혈구탐식성 림프조직구증)": [
            ko("Etoposide", "에토포사이드"),
            ko("Dexamethasone", "덱사메타손"),
            ko("Cyclosporine", "사이클로스포린"),
        ],
    },
}

ANTIBIOTICS_BY_CLASS = {
    "Penicillins(페니실린계)": [ "Amoxicillin(아목시실린)", "Piperacillin-tazobactam(피페라실린/타조박탐)" ],
    "Cephalosporins(세팔로스포린계)": [ "Cefazolin(세파졸린)", "Ceftriaxone(세프트리악손)", "Ceftazidime(세프타지딤)", "Cefepime(세페핌)" ],
    "Carbapenems(카바페넴계)": [ "Meropenem(메로페넴)", "Imipenem/cilastatin(이미페넴/실라스타틴)" ],
    "Glycopeptides(글리코펩타이드)": [ "Vancomycin(반코마이신)" ],
    "Macrolides(마크로라이드)": [ "Azithromycin(아지스로마이신)", "Clarithromycin(클라리스로마이신)" ],
    "Fluoroquinolones(플루오로퀴놀론)": [ "Levofloxacin(레보플록사신)", "Ciprofloxacin(시프로플록사신)" ],
    "Aminoglycosides(아미노글리코사이드)": [ "Gentamicin(겐타마이신)", "Amikacin(아미카신)" ],
    "Others(기타)": [ "Metronidazole(메트로니다졸)", "TMP-SMX(트리메토프림/설파)" ]
}
