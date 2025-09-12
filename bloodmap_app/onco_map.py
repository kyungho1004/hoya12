# -*- coding: utf-8 -*-
# 보완된 항암제 맵 (누락 약물 포함)
from typing import Dict, List, Any

# 원래 build_onco_map 결과를 가져온 후 수정하는 구조
def build_onco_map() -> Dict[str, Dict[str, Dict[str, List[str]]]]:
    return {
        "혈액암": {
            "APL": {
                "chemo": ["ATRA", "Arsenic Trioxide", "Idarubicin", "MTX", "6-MP", "Cytarabine"],
                "targeted": [],
                "abx": []
            },
            "AML": {
                "chemo": ["Ara-C", "Daunorubicin", "Idarubicin", "6-MP", "MTX", "Azacitidine", "Decitabine"],
                "targeted": ["Venetoclax", "Ivosidenib", "Enasidenib"],
                "maintenance": ["6-MP", "MTX", "Azacitidine", "Decitabine"],
                "abx": []
            },
            "ALL": {
                "chemo": ["Vincristine", "Ara-C", "MTX", "6-MP", "Cyclophosphamide", "Prednisone", "L-Asparaginase", "Pegaspargase", "Dexamethasone"],
                "targeted": [],
                "abx": []
            },
            "CML": {"chemo": [], "targeted": ["Imatinib"], "abx": []},
            "CLL": {"chemo": ["Cyclophosphamide", "Prednisone", "Chlorambucil"], "targeted": ["Rituximab"], "abx": []},
            "PCNSL": {
                "chemo": ["MTX", "Ara-C", "Temozolomide", "Thiotepa"],
                "targeted": ["Rituximab"],
                "abx": []
            },
        },
        "고형암": {
            "유방암": {
                "chemo": ["Doxorubicin", "Cyclophosphamide", "Paclitaxel", "Docetaxel"],
                "targeted": ["Trastuzumab", "Pertuzumab", "T-DM1", "Trastuzumab deruxtecan", "Lapatinib", "Tucatinib"],
                "abx": []
            },
            "췌장암": {
                "chemo": ["Oxaliplatin", "Irinotecan", "5-FU", "Gemcitabine", "Nab-Paclitaxel", "Leucovorin"],
                "targeted": [],
                "abx": []
            },
            "간세포암": {
                "chemo": [],
                "targeted": ["Sorafenib", "Lenvatinib", "Atezolizumab", "Bevacizumab", "Durvalumab", "Cabozantinib", "Regorafenib"],
                "abx": []
            },
            "전립선암": {
                "chemo": ["Docetaxel"],
                "targeted": ["Abiraterone", "Enzalutamide"],
                "abx": []
            },
            "GIST": {
                "chemo": [],
                "targeted": ["Imatinib", "Sunitinib", "Regorafenib", "Ripretinib", "Avapritinib", "Nilotinib"],
                "abx": []
            }
        }
    }