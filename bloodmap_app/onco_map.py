# -*- coding: utf-8 -*-
"""
onco_map.py
-----------
Cancer→diagnosis→regimen mapping and recommender.
"""

from typing import Dict, List, Any


def build_onco_map() -> Dict[str, Dict[str, Dict[str, List[str]]]]:
    """
    Minimal example map: {group: {dx: {"chemo":[...], "targeted":[...], "abx":[...]}}}
    Keys should match DRUG_DB primary keys.
    """
    return {
        "혈액암": {
            "APL": {"chemo": ["ATRA", "6-MP", "MTX"], "targeted": [], "abx": []},
            "AML": {"chemo": ["Ara-C", "Doxorubicin"], "targeted": [], "abx": []},
            "ALL": {"chemo": ["Vincristine", "6-MP", "MTX"], "targeted": [], "abx": []},
            "CML": {"chemo": [], "targeted": ["Imatinib"], "abx": []},
        },
        "림프종": {
            "B거대세포(DLBCL)": {
                "chemo": ["Cyclophosphamide", "Doxorubicin", "Vincristine", "Prednisone"],
                "targeted": [],
                "abx": [],
            },
        },
        "고형암": {
            "폐선암": {"chemo": ["Cisplatin", "Pemetrexed"], "targeted": [], "abx": []},
        },
        "육종": {},
        "희귀암": {},
    }


def auto_recs_by_dx(group: str, dx: str, DRUG_DB: Dict[str, Dict[str, Any]], ONCO_MAP: Dict[str, Dict[str, Dict[str, List[str]]]]) -> Dict[str, List[str]]:
    """
    Safe recommender that respects the map and returns only known keys present in DRUG_DB.
    """
    out = {"chemo": [], "targeted": [], "abx": []}
    gmap = ONCO_MAP.get(group or "", {})
    dmap = gmap.get(dx or "", {})
    for k in out.keys():
        picks = dmap.get(k, [])
        out[k] = [p for p in picks if p in (DRUG_DB or {})]
    # Default ABX placeholders for neutropenic fever (display only)
    if not out["abx"]:
        out["abx"] = ["Tazocin(설명)", "Cefepime(설명)", "Meropenem(설명)"]
    return out
