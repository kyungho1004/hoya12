# -*- coding: utf-8 -*-
from typing import Dict, List, Any
import re

# --- Korean labels (병기) & tolerant synonyms ---
DX_KO = {
    # Hematology
    "APL": "급성 전골수구성 백혈병",
    "AML": "급성 골수성 백혈병",
    "ALL": "급성 림프구성 백혈병",
    "CML": "만성 골수성 백혈병",
    "CLL": "만성 림프구성 백혈병",
    "PCNSL": "원발성 중추신경계 림프종",

    # Lymphoma (B/T/NK, with common synonyms)
    "DLBCL": "미만성 거대 B세포 림프종",
    "B거대세포종": "미만성 거대 B세포 림프종",
    "B거대세포 림프종": "미만성 거대 B세포 림프종",
    "B 거대세포종": "미만성 거대 B세포 림프종",
    "b거대세포종": "미만성 거대 B세포 림프종",
    "PMBCL": "원발성 종격동 B세포 림프종",
    "HGBL": "고등급 B세포 림프종",
    "BL": "버킷 림프종",
    "MZL": "변연부 B세포 림프종",
    "MALT lymphoma": "점막연관 변연부 B세포 림프종",
    "FL": "여포성 림프종",
    "MCL": "외투세포 림프종",
    "cHL": "고전적 호지킨 림프종",
    "NLPHL": "결절성 림프구우세 호지킨 림프종",
    "PTCL-NOS": "말초 T세포 림프종 (NOS)",
    "AITL": "혈관면역모세포성 T세포 림프종",
    "ALCL (ALK+)": "역형성 대세포 림프종 (ALK 양성)",
    "ALCL (ALK−)": "역형성 대세포 림프종 (ALK 음성)",

    # Sarcoma
    "Osteosarcoma": "골육종",
    "Ewing sarcoma": "유잉육종",
    "Rhabdomyosarcoma": "횡문근육종",
    "Synovial sarcoma": "활막육종",
    "Leiomyosarcoma": "평활근육종",
    "Liposarcoma": "지방육종",
    "UPS": "미분화 다형성 육종",
    "Angiosarcoma": "혈관육종",
    "MPNST": "악성 말초신경초종",
    "DFSP": "피부섬유종증성 육종(DFSP)",
    "Clear cell sarcoma": "투명세포 육종",
    "Epithelioid sarcoma": "상피양 육종",

    # Solid (kept from previous)
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
    "NET": "신경내분비종양",
    "MTC": "수질성 갑상선암",
}

def _is_korean(s: str) -> bool:
    return any('\uac00' <= ch <= '\ud7a3' for ch in (s or ""))

def dx_display(group: str, dx: str) -> str:
    ko = DX_KO.get(dx, "")
    # Avoid duplicating when dx already contains Korean name
    if ko and (_is_korean(dx) or ko in (dx or "")):
        return f"{group} - {dx}"
    return f"{group} - {dx} ({ko})" if ko else f"{group} - {dx}"

def build_onco_map() -> Dict[str, Dict[str, Dict[str, List[str]]]]:
    """
    Returns: {group: {dx: { 'chemo': [...], 'targeted': [...], 'abx': [...]}}}
    Only keys present in DRUG_DB will be shown in AE table.
    """
    return {
        "혈액암": {
            "APL": {"chemo": ["ATRA","Arsenic Trioxide","Idarubicin","MTX","6-MP"], "targeted": [], "abx": []},
            "AML": {"chemo": ["Ara-C","Daunorubicin","Idarubicin"], "targeted": [], "abx": []},
            "ALL": {"chemo": ["Vincristine","Ara-C","MTX","6-MP","Cyclophosphamide","Prednisone"], "targeted": [], "abx": []},
            "CML": {"chemo": [], "targeted": ["Imatinib"], "abx": []},
            "CLL": {"chemo": ["Cyclophosphamide","Prednisone","Chlorambucil"], "targeted": ["Rituximab"], "abx": []},
            "PCNSL": {"chemo": ["MTX","Ara-C"], "targeted": ["Rituximab"], "abx": []},
        },
        "림프종": {
            # B-cell large cell
            "DLBCL": {
                "chemo": ["Cyclophosphamide","Doxorubicin","Vincristine","Prednisone"],  # CHOP
                "targeted": ["Rituximab","Polatuzumab Vedotin"],  # R-CHOP / pola options
                "abx": []
            },
            "B거대세포종": {
                "chemo": ["Cyclophosphamide","Doxorubicin","Vincristine","Prednisone"],
                "targeted": ["Rituximab"],
                "abx": []
            },
            "PMBCL": {
                "chemo": ["Cyclophosphamide","Doxorubicin","Vincristine","Prednisone"],
                "targeted": ["Rituximab","Pembrolizumab"],
                "abx": []
            },
            "HGBL": {
                "chemo": ["Etoposide","Doxorubicin","Cyclophosphamide","Vincristine","Prednisone"],  # DA-EPOCH-R
                "targeted": ["Rituximab"],
                "abx": []
            },
            "BL": {
                "chemo": ["Cyclophosphamide","Doxorubicin","Vincristine","MTX","Ara-C"],
                "targeted": ["Rituximab"],
                "abx": []
            },
            # Indolent B-cell
            "FL": {
                "chemo": ["Cyclophosphamide","Doxorubicin","Vincristine","Prednisone","Bendamustine"],
                "targeted": ["Rituximab","Obinutuzumab"],
                "abx": []
            },
            "MZL": {
                "chemo": ["Bendamustine","Chlorambucil"],
                "targeted": ["Rituximab"],
                "abx": []
            },
            "MALT lymphoma": {
                "chemo": ["Chlorambucil"],
                "targeted": ["Rituximab"],
                "abx": []
            },
            "MCL": {
                "chemo": ["Cyclophosphamide","Doxorubicin","Vincristine","Prednisone","Bendamustine"],
                "targeted": ["Rituximab","Ibrutinib"],
                "abx": []
            },
            # Hodgkin
            "cHL": {
                "chemo": ["Doxorubicin","Bleomycin","Vinblastine","Dacarbazine"],
                "targeted": ["Brentuximab Vedotin","Nivolumab","Pembrolizumab"],
                "abx": []
            },
            "NLPHL": {
                "chemo": ["Cyclophosphamide","Doxorubicin","Vincristine","Prednisone"],
                "targeted": ["Rituximab"],
                "abx": []
            },
            # T-cell
            "PTCL-NOS": {
                "chemo": ["Cyclophosphamide","Doxorubicin","Vincristine","Prednisone"],  # CHOP
                "targeted": [],
                "abx": []
            },
            "AITL": {
                "chemo": ["Cyclophosphamide","Doxorubicin","Vincristine","Prednisone"],
                "targeted": [],
                "abx": []
            },
            "ALCL (ALK+)": {
                "chemo": ["Cyclophosphamide","Doxorubicin","Vincristine","Prednisone"],
                "targeted": ["Brentuximab Vedotin"],
                "abx": []
            },
            "ALCL (ALK−)": {
                "chemo": ["Cyclophosphamide","Doxorubicin","Vincristine","Prednisone"],
                "targeted": ["Brentuximab Vedotin"],
                "abx": []
            },
        },
        "고형암": {
            "폐선암": {"chemo": ["Cisplatin","Pemetrexed"], "targeted": ["Osimertinib","Alectinib","Crizotinib","Larotrectinib","Entrectinib","Capmatinib","Sotorasib"], "abx": []},
            "유방암": {"chemo": ["Doxorubicin","Cyclophosphamide","Paclitaxel"], "targeted": ["Trastuzumab","Pertuzumab","T-DM1"], "abx": []},
            "대장암": {"chemo": ["Oxaliplatin","5-FU","Irinotecan","Capecitabine"], "targeted": ["Bevacizumab","Regorafenib"], "abx": []},
            "위암": {"chemo": ["Cisplatin","5-FU","Capecitabine"], "targeted": ["Trastuzumab"], "abx": []},
            "간세포암": {"chemo": [], "targeted": ["Sorafenib","Lenvatinib","Atezolizumab","Bevacizumab","Durvalumab"], "abx": []},
            "췌장암": {"chemo": ["Oxaliplatin","Irinotecan","5-FU","Gemcitabine"], "targeted": [], "abx": []},
            "난소암": {"chemo": ["Carboplatin","Paclitaxel"], "targeted": ["Bevacizumab"], "abx": []},
            "자궁경부암": {"chemo": ["Cisplatin"], "targeted": ["Bevacizumab"], "abx": []},
            "방광암": {"chemo": ["Gemcitabine","Cisplatin"], "targeted": ["Pembrolizumab","Nivolumab"], "abx": []},
            "식도암": {"chemo": ["Cisplatin","5-FU"], "targeted": [], "abx": []},
            "GIST": {"chemo": [], "targeted": ["Imatinib","Sunitinib","Regorafenib","Ripretinib"], "abx": []},
            "NET": {"chemo": [], "targeted": ["Everolimus","Octreotide"], "abx": []},
            "MTC": {"chemo": [], "targeted": ["Vandetanib","Cabozantinib"], "abx": []},
        },
        "육종": {
            "Osteosarcoma": {"chemo": ["MTX","Doxorubicin","Cisplatin"], "targeted": [], "abx": []},  # MAP
            "Ewing sarcoma": {"chemo": ["Vincristine","Doxorubicin","Cyclophosphamide","Ifosfamide","Etoposide"], "targeted": [], "abx": []},  # VDC/IE
            "Rhabdomyosarcoma": {"chemo": ["Vincristine","Dactinomycin","Cyclophosphamide"], "targeted": [], "abx": []},  # VAC
            "Synovial sarcoma": {"chemo": ["Ifosfamide","Doxorubicin"], "targeted": ["Pazopanib"], "abx": []},
            "Leiomyosarcoma": {"chemo": ["Doxorubicin","Ifosfamide","Gemcitabine","Docetaxel"], "targeted": ["Pazopanib"], "abx": []},
            "Liposarcoma": {"chemo": ["Doxorubicin","Ifosfamide","Trabectedin"], "targeted": [], "abx": []},
            "UPS": {"chemo": ["Doxorubicin","Ifosfamide","Gemcitabine","Docetaxel"], "targeted": [], "abx": []},
            "Angiosarcoma": {"chemo": ["Paclitaxel","Doxorubicin"], "targeted": ["Pazopanib"], "abx": []},
            "MPNST": {"chemo": ["Doxorubicin","Ifosfamide"], "targeted": [], "abx": []},
            "DFSP": {"chemo": [], "targeted": ["Imatinib"], "abx": []},
            "Clear cell sarcoma": {"chemo": ["Doxorubicin","Ifosfamide"], "targeted": ["Pazopanib"], "abx": []},
            "Epithelioid sarcoma": {"chemo": ["Doxorubicin","Ifosfamide"], "targeted": ["Pazopanib"], "abx": []},
        },
        "희귀암": {
            "GIST": {"chemo": [], "targeted": ["Imatinib","Sunitinib","Regorafenib","Ripretinib"], "abx": []},
            "NET": {"chemo": [], "targeted": ["Everolimus","Octreotide"], "abx": []},
            "MTC": {"chemo": [], "targeted": ["Vandetanib","Cabozantinib"], "abx": []},
        },
    }

def auto_recs_by_dx(group: str, dx: str, DRUG_DB: Dict[str, Dict[str, Any]], ONCO_MAP: Dict[str, Dict[str, Dict[str, List[str]]]]):
    out = {"chemo": [], "targeted": [], "abx": []}
    gmap = ONCO_MAP.get(group or "", {})
    dmap = gmap.get(dx or "", {})
    for k in out.keys():
        picks = dmap.get(k, [])
        out[k] = [p for p in picks if p in (DRUG_DB or {})]
    if not out["abx"]:
        out["abx"] = ["Piperacillin/Tazobactam(설명)", "Cefepime(설명)", "Meropenem(설명)"]
    return out
