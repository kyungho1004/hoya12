
# -*- coding: utf-8 -*-
"""
onco_map.py (patched v2, 5-group split)
- build_onco_map() → {"혈액암","림프종","육종","고형암","희귀암"} groups
- dx_display(group, dx): "group - EN (KO)" unless already Korean
- auto_recs_by_dx: stable stub
- Non-breaking: same API names; safe import (no side effects at import)
"""

from __future__ import annotations

# ---- Diagnosis Korean map (codes & common English) ----
_DX_KO = {
    # Hematologic (non-lymphoma)
    "ALL": "급성 림프구성 백혈병",
    "AML": "급성 골수성 백혈병",
    "CML": "만성 골수성 백혈병",
    "CLL": "만성 림프구성 백혈병",
    # Lymphomas
    "LYMPHOMA": "림프종",
    "DLBCL": "미만성 거대 B세포 림프종",
    "PMBCL": "원발성 종격동 B세포 림프종",
    "HGBL": "고등급 B세포 림프종",
    "BL": "버킷 림프종",
    "FL": "여포성 림프종",
    "MZL": "변연부 림프종",
    "MCL": "외투세포 림프종",
    "CHL": "고전적 호지킨 림프종",
    "NLPHL": "결절성 림프구우세 호지킨 림프종",
    "PTCL-NOS": "말초 T세포 림프종 (NOS)",
    "AITL": "혈관면역모세포성 T세포 림프종",
    "ALCL (ALK+)": "역형성 대세포 림프종 (ALK 양성)",
    "ALCL (ALK-)": "역형성 대세포 림프종 (ALK 음성)",
    # Solid tumors
    "BREAST": "유방암", "Breast": "유방암",
    "COLON": "결장·직장 선암", "Colon": "결장·직장 선암", "CRC": "결장·직장암",
    "LUNG": "폐암", "Lung": "폐암",
    "NSCLC": "비소세포폐암", "SCLC": "소세포폐암",
    "GIST": "위장관기저종양",
    "NET": "신경내분비종양",
    "MTC": "수질성 갑상선암",
    # Sarcomas
    "OSTEOSARCOMA": "골육종", "Osteosarcoma": "골육종",
    "EWING SARCOMA": "유잉육종", "Ewing sarcoma": "유잉육종",
    "RHABDOMYOSARCOMA": "횡문근육종", "Rhabdomyosarcoma": "횡문근육종",
    "UPS": "미분화 다형성 육종",
    "ANGIOSARCOMA": "혈관육종",
    "Synovial Sarcoma": "윤활막 육종",
    "LEIOMYOSARCOMA": "평활근육종",
    "LIPOSARCOMA": "지방육종",
    # Rare placeholders
    "Chordoma": "척삭종",
    "ACC": "부신피질암",
    "Thymic carcinoma": "흉선암",
    "Histiocytosis": "조직구증(히스티오사이토시스)",
}

def _is_korean(s: str) -> bool:
    return any('\uac00' <= ch <= '\ud7a3' for ch in (s or ""))

def _norm_key(s: str) -> str:
    if not s: return ""
    u = " ".join(s.strip().replace("_"," ").replace("-"," ").split())
    return u

def build_onco_map() -> dict:
    """
    Five-way grouped structure expected by the app.
    Keys (Korean): 혈액암 / 림프종 / 육종 / 고형암 / 희귀암
    Values: dict of diseases (keys used for UI; values can be extended later).
    """
    heme = {
        "ALL": {}, "AML": {}, "CML": {}, "CLL": {},
    }
    lymphoma = {
        "DLBCL": {}, "PMBCL": {}, "HGBL": {}, "BL": {},
        "FL": {}, "MZL": {}, "MCL": {}, "CHL": {}, "NLPHL": {},
        "PTCL-NOS": {}, "AITL": {}, "ALCL (ALK+)": {}, "ALCL (ALK-)": {},
        "Lymphoma": {},  # generic bucket for caregivers
    }
    sarcoma = {
        "Osteosarcoma": {}, "Ewing sarcoma": {}, "Rhabdomyosarcoma": {},
        "UPS": {}, "Angiosarcoma": {}, "Synovial Sarcoma": {},
        "Leiomyosarcoma": {}, "Liposarcoma": {},
    }
    solid = {
        "Breast": {}, "Colon": {}, "Lung": {},
        "GIST": {}, "NET": {}, "MTC": {},
    }
    rare = {
        "Chordoma": {}, "ACC": {}, "Thymic carcinoma": {}, "Histiocytosis": {},
    }
    return {"혈액암": heme, "림프종": lymphoma, "육종": sarcoma, "고형암": solid, "희귀암": rare}

def dx_display(group: str, dx: str) -> str:
    group = (group or "").strip()
    dx_raw = (dx or "").strip()
    if _is_korean(dx_raw):
        return f"{group} - {dx_raw}" if group else dx_raw
    ko = _DX_KO.get(dx_raw) or _DX_KO.get(_norm_key(dx_raw).upper()) or _DX_KO.get(_norm_key(dx_raw))
    if ko:
        return f"{group} - {dx_raw} ({ko})" if group else f"{dx_raw} ({ko})"
    return f"{group} - {dx_raw}" if group else dx_raw


    return {"chemo": [], "targeted": [], "abx": []}


# --- Minimal DB-aware recommendations by diagnosis (non-exhaustive; safe defaults) ---
# Keys must match DRUG_DB keys when possible.
_REC = {
    # Hematologic (non-lymphoma)
    "ALL": {
        "chemo": ["Vincristine", "Cyclophosphamide", "Doxorubicin", "Ara-C", "Methotrexate", "6-MP", "Prednisone"],
        "targeted": ["Imatinib", "Rituximab"],
    },
    "AML": {
        "chemo": ["Ara-C", "Etoposide", "Idarubicin", "Daunorubicin"],
        "targeted": [],
    },
    "CML": {
        "chemo": [],
        "targeted": ["Imatinib", "Dasatinib", "Nilotinib"],
    },
    "CLL": {
        "chemo": ["Cyclophosphamide"],
        "targeted": ["Ibrutinib", "Obinutuzumab", "Rituximab"],
    },

    # Lymphomas
    "DLBCL": {
        "chemo": ["Cyclophosphamide", "Doxorubicin", "Vincristine", "Prednisone"],
        "targeted": ["Rituximab", "Polatuzumab Vedotin"],
    },
    "PMBCL": {
        "chemo": ["Cyclophosphamide", "Doxorubicin", "Vincristine", "Prednisone", "Etoposide"],
        "targeted": ["Rituximab"],
    },
    "HGBL": {"chemo": ["Cyclophosphamide", "Doxorubicin", "Vincristine", "Prednisone", "Etoposide"], "targeted": ["Rituximab"]},
    "BL": {"chemo": ["Cyclophosphamide", "Doxorubicin", "Vincristine", "Ara-C", "Methotrexate"], "targeted": ["Rituximab"]},
    "FL": {"chemo": ["Cyclophosphamide", "Doxorubicin", "Vincristine", "Prednisone", "Bendamustine"], "targeted": ["Rituximab", "Obinutuzumab"]},
    "MZL": {"chemo": ["Cyclophosphamide", "Bendamustine"], "targeted": ["Rituximab", "Obinutuzumab"]},
    "MCL": {"chemo": ["Cyclophosphamide", "Bendamustine"], "targeted": ["Ibrutinib", "Rituximab"]},
    "CHL": {"chemo": ["Doxorubicin", "Vinblastine", "Dacarbazine", "Bleomycin"], "targeted": ["Brentuximab Vedotin", "Nivolumab", "Pembrolizumab"]},
    "NLPHL": {"chemo": ["Cyclophosphamide", "Doxorubicin", "Vincristine", "Prednisone"], "targeted": ["Rituximab"]},
    "PTCL-NOS": {"chemo": ["Cyclophosphamide", "Doxorubicin", "Etoposide"], "targeted": []},
    "AITL": {"chemo": ["Cyclophosphamide", "Doxorubicin", "Etoposide"], "targeted": []},
    "ALCL (ALK+)": {"chemo": ["Cyclophosphamide", "Doxorubicin", "Etoposide"], "targeted": []},
    "ALCL (ALK-)": {"chemo": ["Cyclophosphamide", "Doxorubicin", "Etoposide"], "targeted": []},
    "Lymphoma": {"chemo": ["Cyclophosphamide", "Doxorubicin", "Vincristine", "Prednisone"], "targeted": ["Rituximab"]},

    # Sarcomas
    "Osteosarcoma": {"chemo": ["Doxorubicin", "Cisplatin", "Methotrexate", "Ifosfamide", "Etoposide"], "targeted": []},
    "Ewing sarcoma": {"chemo": ["Vincristine", "Doxorubicin", "Cyclophosphamide", "Ifosfamide", "Etoposide"], "targeted": []},
    "Rhabdomyosarcoma": {"chemo": ["Vincristine", "Dactinomycin", "Cyclophosphamide", "Ifosfamide", "Etoposide"], "targeted": []},
    "UPS": {"chemo": ["Doxorubicin", "Ifosfamide", "Paclitaxel"], "targeted": ["Pazopanib"]},
    "Angiosarcoma": {"chemo": ["Paclitaxel", "Doxorubicin"], "targeted": ["Bevacizumab", "Pazopanib"]},
    "Synovial Sarcoma": {"chemo": ["Ifosfamide", "Doxorubicin"], "targeted": []},
    "Leiomyosarcoma": {"chemo": ["Doxorubicin", "Ifosfamide"], "targeted": ["Pazopanib"]},
    "Liposarcoma": {"chemo": ["Doxorubicin", "Ifosfamide"], "targeted": []},

    # Solid tumors
    "Breast": {"chemo": ["Paclitaxel", "Docetaxel", "Doxorubicin", "Cyclophosphamide"], "targeted": ["Trastuzumab", "Pertuzumab", "T-DM1", "Trastuzumab deruxtecan", "Tucatinib"]},
    "Colon": {"chemo": ["Oxaliplatin", "Irinotecan", "Capecitabine", "5-FU"], "targeted": ["Bevacizumab", "Ramucirumab", "Regorafenib"]},
    "Lung": {"chemo": ["Carboplatin", "Cisplatin", "Pemetrexed", "Docetaxel", "Paclitaxel"], "targeted": ["Osimertinib", "Nivolumab", "Pembrolizumab", "Alectinib", "Lorlatinib", "Capmatinib", "Entrectinib", "Crizotinib", "Sotorasib"]},
    "GIST": {"chemo": [], "targeted": ["Imatinib", "Sunitinib", "Regorafenib", "Ripretinib"]},
    "NET": {"chemo": [], "targeted": ["Octreotide", "Everolimus"]},
    "MTC": {"chemo": [], "targeted": ["Vandetanib", "Cabozantinib"]},

    # Rare
    "Chordoma": {"chemo": [], "targeted": ["Imatinib"]},
    "ACC": {"chemo": [], "targeted": ["Cabozantinib"]},
    "Thymic carcinoma": {"chemo": ["Carboplatin", "Paclitaxel"], "targeted": []},
    "Histiocytosis": {"chemo": ["Vinblastine", "Prednisone"], "targeted": []},
}

def _dedup(seq):
    out = []
    seen = set()
    for x in seq or []:
        if x not in seen:
            out.append(x); seen.add(x)
    return out

def _in_db_only(keys, db):
    return [k for k in keys if k in (db or {})]

def auto_recs_by_dx(group: str, dx: str, db=None):
    """
    Return {'chemo': [...], 'targeted': [...], 'abx': []} filtered by DRUG_DB membership.
    Non-breaking: if key not found in _REC, returns empty lists.
    """
    g = (group or "").strip()
    d = (dx or "").strip()
    rec = _REC.get(d) or _REC.get(d.upper()) or _REC.get(d.title()) or {}
    chemo = _in_db_only(rec.get("chemo", []), db)
    targeted = _in_db_only(rec.get("targeted", []), db)
    return {"chemo": _dedup(chemo), "targeted": _dedup(targeted), "abx": []}
