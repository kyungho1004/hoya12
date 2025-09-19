# -*- coding: utf-8 -*-
from typing import Dict, List

def extend_peds_lymphoma(M: Dict[str, Dict[str, Dict[str, List[str]]]]) -> Dict[str, Dict[str, Dict[str, List[str]]]]:
    """림프종에 소아 전용 항암제/진단 옵션을 추가"""
    L = M.get("림프종", {})
    # 소아 B-NHL (LMB 프로토콜 기반)
    L["소아 B-NHL (LMB)"] = {
        "chemo": [
            "Cyclophosphamide","Vincristine","Prednisone","Doxorubicin",
            "High-dose MTX","Cytarabine","Ifosfamide","Etoposide"
        ],
        "targeted": ["Rituximab"],
        "abx": []
    }
    # 소아 Burkitt 변형
    L["소아 Burkitt"] = {
        "chemo": ["Cyclophosphamide","Doxorubicin","Vincristine","High-dose MTX","Cytarabine"],
        "targeted": ["Rituximab"],
        "abx": []
    }
    # 소아 호지킨 (OEPA/AVD 계열)
    L["소아 호지킨"] = {
        "chemo": ["Vincristine","Etoposide","Prednisone","Doxorubicin","Dacarbazine","Vinblastine","Bleomycin"],
        "targeted": [],
        "abx": []
    }
    # 소아 T/NK 림프종(대표)
    L["소아 T/NK 림프종"] = {
        "chemo": ["Cyclophosphamide","Doxorubicin","Vincristine","Prednisone","Ifosfamide","Etoposide","Cytarabine"],
        "targeted": [],
        "abx": []
    }
    M["림프종"] = L
    return M
