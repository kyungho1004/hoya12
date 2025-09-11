# -*- coding: utf-8 -*-
from typing import Dict, List, Any

DX_KO = {
    "APL": "급성 전골수구성 백혈병",
    "AML": "급성 골수성 백혈병",
    "ALL": "급성 림프구성 백혈병",
    "CML": "만성 골수성 백혈병",
    "CLL": "만성 림프구성 백혈병",
    "DLBCL": "미만성 거대 B세포 림프종",
    # Solid
    "폐선암": "폐선암",
    "유방암": "유방암",
    "대장암": "결장/직장 선암",
    "위암": "위선암",
    "간세포암": "간세포암(HCC)",
    "췌장암": "췌장암",
    "난소암": "난소암",
    "자궁경부암": "자궁경부암",
    "방광암": "방광암",
    "식도암": "식도암",
    "GIST": "위장관기저종양",
}

def dx_display(group: str, dx: str) -> str:
    ko = DX_KO.get(dx, "")
    return f"{group} - {dx}{(' ('+ko+')') if ko else ''}"

def build_onco_map() -> Dict[str, Dict[str, Dict[str, List[str]]]]:
    return {
        "혈액암": {
            "APL": {"chemo": ["ATRA","Arsenic Trioxide","Idarubicin","MTX","6-MP"], "targeted": [], "abx": []},
            "AML": {"chemo": ["Ara-C","Daunorubicin","Idarubicin"], "targeted": [], "abx": []},
            "ALL": {"chemo": ["Vincristine","Ara-C","MTX","6-MP","Cyclophosphamide","Prednisone"], "targeted": [], "abx": []},
            "CML": {"chemo": [], "targeted": ["Imatinib"], "abx": []},
            "CLL": {"chemo": ["Cyclophosphamide","Prednisone"], "targeted": [], "abx": []},
        },
        "림프종": {
            "DLBCL": {"chemo": ["Cyclophosphamide","Doxorubicin","Vincristine","Prednisone"], "targeted": [], "abx": []},
        },
        "고형암": {
            "폐선암": {"chemo": ["Cisplatin","Pemetrexed"], "targeted": ["Osimertinib","Alectinib","Crizotinib","Larotrectinib","Entrectinib"], "abx": []},
            "유방암": {"chemo": ["Doxorubicin","Cyclophosphamide","Paclitaxel"], "targeted": ["Trastuzumab"], "abx": []},
            "대장암": {"chemo": ["Oxaliplatin","5-FU","Irinotecan","Capecitabine"], "targeted": ["Bevacizumab"], "abx": []},
            "위암": {"chemo": ["Cisplatin","5-FU","Capecitabine"], "targeted": ["Trastuzumab"], "abx": []},
            "간세포암": {"chemo": [], "targeted": ["Sorafenib","Lenvatinib"], "abx": []},
            "췌장암": {"chemo": ["Oxaliplatin","Irinotecan","5-FU","Gemcitabine"], "targeted": [], "abx": []},
            "난소암": {"chemo": ["Carboplatin","Paclitaxel"], "targeted": ["Bevacizumab"], "abx": []},
            "자궁경부암": {"chemo": ["Cisplatin"], "targeted": ["Bevacizumab"], "abx": []},
            "방광암": {"chemo": ["Gemcitabine","Cisplatin"], "targeted": [], "abx": []},
            "식도암": {"chemo": ["Cisplatin","5-FU"], "targeted": [], "abx": []},
            "GIST": {"chemo": [], "targeted": ["Imatinib"], "abx": []},
        },
        "육종": {},
        "희귀암": {},
    }

def auto_recs_by_dx(group: str, dx: str, DRUG_DB: Dict[str, Dict[str, Any]], ONCO_MAP: Dict[str, Dict[str, Dict[str, List[str]]]]):
    out = {"chemo": [], "targeted": [], "abx": []}
    gmap = ONCO_MAP.get(group or "", {})
    dmap = gmap.get(dx or "", {})
    for k in out.keys():
        picks = dmap.get(k, [])
        out[k] = [p for p in picks if p in (DRUG_DB or {})]
    if not out["abx"]:
        out["abx"] = ["Tazocin(설명)", "Cefepime(설명)", "Meropenem(설명)"]
    return out
