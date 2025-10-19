
# -*- coding: utf-8 -*-
"""
onco_map.py (v3, expanded coverage)
- 5 groups: 혈액암 / 림프종 / 육종 / 고형암 / 희귀암
- build_onco_map(): returns grouped dict of diseases (keys shown in UI)
- dx_display(group, dx): "group - EN (KO)" unless already Korean
- auto_recs_by_dx(group, dx, db): minimal, DB-aware recommendations (safe defaults)
- Non-breaking: same API names; safe import
"""

from __future__ import annotations

# --------------------------- KO Name Map ---------------------------
_DX_KO = {
    # Hematologic (non-lymphoma)
    "ALL": "급성 림프구성 백혈병",
    "AML": "급성 골수성 백혈병",
    "APL": "급성 전골수성 백혈병",
    "CML": "만성 골수성 백혈병",
    "CLL": "만성 림프구성 백혈병",
    "MDS": "골수이형성증후군",
    "MPN": "골수증식성 종양",
    "PV": "진성 다혈구증",
    "ET": "본태성 혈소판증가증",
    "MF": "골수섬유증",
    "MM": "다발골수종",
    "MGUS": "의미불명 단클론감마병증",

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
    "ENKTL": "비인두 NK/T세포 림프종",
    "MF/SS": "피부 T세포 림프종(미코시스 퐁고이데스/쇠자병)",

    # Solid tumors
    "Breast": "유방암",
    "Colon": "결장암",
    "Rectal": "직장암",
    "CRC": "결장·직장암",
    "Gastric": "위암",
    "Esophageal": "식도암",
    "Pancreatic": "췌장암",
    "Hepatocellular carcinoma": "간세포암",
    "Cholangiocarcinoma": "담관암",
    "Gallbladder": "담낭암",
    "Lung": "폐암",
    "NSCLC": "비소세포폐암",
    "SCLC": "소세포폐암",
    "Head & Neck": "두경부 편평상피암",
    "Thyroid (PTC)": "갑상선 유두암",
    "Thyroid (FTC)": "갑상선 여포암",
    "MTC": "수질성 갑상선암",
    "ATC": "역형성 갑상선암",
    "Kidney (RCC)": "신장암(신세포암)",
    "Urothelial": "요로상피암(방광/요관)",
    "Prostate": "전립선암",
    "Ovary": "난소암",
    "Cervical": "자궁경부암",
    "Endometrial": "자궁내막암",
    "Testicular (Seminoma)": "고환종양(세미노마)",
    "Testicular (NSGCT)": "고환종양(비세미노마)",
    "GIST": "위장관기저종양",
    "NET": "신경내분비종양",

    # Sarcomas
    "Osteosarcoma": "골육종",
    "Ewing sarcoma": "유잉육종",
    "Rhabdomyosarcoma": "횡문근육종",
    "Synovial Sarcoma": "윤활막 육종",
    "Leiomyosarcoma": "평활근육종",
    "Liposarcoma": "지방육종",
    "MPNST": "말초신경초종양",
    "DFSP": "피부섬유육종",
    "UPS": "미분화 다형성 육종",
    "Angiosarcoma": "혈관육종",

    # Rare / Pediatric / Others
    "Neuroblastoma": "신경모세포종",
    "Wilms tumor": "윌름스 종양",
    "Hepatoblastoma": "간모세포종",
    "Retinoblastoma": "망막모세포종",
    "Medulloblastoma": "수모세포종",
    "Ependymoma": "상의세포종",
    "Chordoma": "척삭종",
    "Mesothelioma": "악성 중피종",
    "ACC": "부신피질암",
    "Pheochromocytoma/Paraganglioma": "갈색세포종/부신외갈색세포종",
    "Thymic carcinoma": "흉선암",
    "Histiocytosis": "조직구증(히스티오사이토시스)",
}

# --------------------------- Helpers ---------------------------
def _is_korean(s: str) -> bool:
    return any('\uac00' <= ch <= '\ud7a3' for ch in (s or ""))

def _norm_key(s: str) -> str:
    if not s: return ""
    u = " ".join(s.strip().replace("_"," ").replace("-"," ").split())
    return u

# --------------------------- Group Builder ---------------------------
def build_onco_map() -> dict:
    """
    Five groups with an expanded set of diseases.
    Keys (Korean): 혈액암 / 림프종 / 육종 / 고형암 / 희귀암
    Values: dict of disease labels (keys only; values reserved for future).
    """
    heme = {
        "ALL": {}, "AML": {}, "APL": {}, "CML": {}, "CLL": {},
        "MDS": {}, "MPN": {}, "PV": {}, "ET": {}, "MF": {}, "MM": {}, "MGUS": {},
    }
    lymphoma = {
        "DLBCL": {}, "PMBCL": {}, "HGBL": {}, "BL": {},
        "FL": {}, "MZL": {}, "MCL": {}, "CHL": {}, "NLPHL": {},
        "PTCL-NOS": {}, "AITL": {}, "ALCL (ALK+)": {}, "ALCL (ALK-)": {},
        "ENKTL": {}, "MF/SS": {}, "Lymphoma": {},
    }
    sarcoma = {
        "Osteosarcoma": {}, "Ewing sarcoma": {}, "Rhabdomyosarcoma": {},
        "Synovial Sarcoma": {}, "Leiomyosarcoma": {}, "Liposarcoma": {},
        "MPNST": {}, "DFSP": {}, "UPS": {}, "Angiosarcoma": {},
    }
    solid = {
        "Breast": {}, "Colon": {}, "Rectal": {}, "CRC": {},
        "Gastric": {}, "Esophageal": {}, "Pancreatic": {},
        "Hepatocellular carcinoma": {}, "Cholangiocarcinoma": {}, "Gallbladder": {},
        "Lung": {}, "NSCLC": {}, "SCLC": {}, "Head & Neck": {},
        "Thyroid (PTC)": {}, "Thyroid (FTC)": {}, "MTC": {}, "ATC": {},
        "Kidney (RCC)": {}, "Urothelial": {}, "Prostate": {},
        "Ovary": {}, "Cervical": {}, "Endometrial": {},
        "Testicular (Seminoma)": {}, "Testicular (NSGCT)": {},
        "GIST": {}, "NET": {},
    }
    rare = {
        "Neuroblastoma": {}, "Wilms tumor": {}, "Hepatoblastoma": {}, "Retinoblastoma": {},
        "Medulloblastoma": {}, "Ependymoma": {}, "Chordoma": {}, "Mesothelioma": {},
        "ACC": {}, "Pheochromocytoma/Paraganglioma": {}, "Thymic carcinoma": {}, "Histiocytosis": {},
    }
    return {"혈액암": heme, "림프종": lymphoma, "육종": sarcoma, "고형암": solid, "희귀암": rare}

# --------------------------- Display ---------------------------
def dx_display(group: str, dx: str) -> str:
    group = (group or "").strip()
    dx_raw = (dx or "").strip()
    if _is_korean(dx_raw):
        return f"{group} - {dx_raw}" if group else dx_raw
    ko = _DX_KO.get(dx_raw) or _DX_KO.get(_norm_key(dx_raw).upper()) or _DX_KO.get(_norm_key(dx_raw))
    if ko:
        return f"{group} - {dx_raw} ({ko})" if group else f"{dx_raw} ({ko})"
    return f"{group} - {dx_raw}" if group else dx_raw

# --------------------------- Minimal DB-aware Recommendations ---------------------------
_REC = {
    # Hematologic
    "ALL": {"chemo": ["Vincristine", "Cyclophosphamide", "Doxorubicin", "Ara-C", "Methotrexate", "6-MP", "Prednisone"], "targeted": ["Imatinib", "Rituximab"]},
    "AML": {"chemo": ["Ara-C", "Etoposide", "Idarubicin", "Daunorubicin"], "targeted": []},
    "APL": {"chemo": ["Ara-C"], "targeted": ["ATRA", "Arsenic trioxide"]},
    "CML": {"chemo": [], "targeted": ["Imatinib", "Dasatinib", "Nilotinib"]},
    "CLL": {"chemo": ["Cyclophosphamide"], "targeted": ["Ibrutinib", "Obinutuzumab", "Rituximab"]},
    "MM": {"chemo": ["Cyclophosphamide"], "targeted": []},

    # Lymphoma
    "DLBCL": {"chemo": ["Cyclophosphamide", "Doxorubicin", "Vincristine", "Prednisone"], "targeted": ["Rituximab", "Polatuzumab Vedotin"]},
    "PMBCL": {"chemo": ["Cyclophosphamide", "Doxorubicin", "Vincristine", "Prednisone", "Etoposide"], "targeted": ["Rituximab"]},
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
    "ENKTL": {"chemo": ["Cyclophosphamide", "Doxorubicin", "Etoposide"], "targeted": []},
    "MF/SS": {"chemo": [], "targeted": []},
    "Lymphoma": {"chemo": ["Cyclophosphamide", "Doxorubicin", "Vincristine", "Prednisone"], "targeted": ["Rituximab"]},

    # Sarcoma
    "Osteosarcoma": {"chemo": ["Doxorubicin", "Cisplatin", "Methotrexate", "Ifosfamide", "Etoposide"], "targeted": []},
    "Ewing sarcoma": {"chemo": ["Vincristine", "Doxorubicin", "Cyclophosphamide", "Ifosfamide", "Etoposide"], "targeted": []},
    "Rhabdomyosarcoma": {"chemo": ["Vincristine", "Dactinomycin", "Cyclophosphamide", "Ifosfamide", "Etoposide"], "targeted": []},
    "Synovial Sarcoma": {"chemo": ["Ifosfamide", "Doxorubicin"], "targeted": []},
    "Leiomyosarcoma": {"chemo": ["Doxorubicin", "Ifosfamide"], "targeted": ["Pazopanib"]},
    "Liposarcoma": {"chemo": ["Doxorubicin", "Ifosfamide"], "targeted": []},
    "MPNST": {"chemo": ["Doxorubicin", "Ifosfamide"], "targeted": []},
    "DFSP": {"chemo": [], "targeted": ["Imatinib"]},
    "UPS": {"chemo": ["Doxorubicin", "Ifosfamide", "Paclitaxel"], "targeted": ["Pazopanib"]},
    "Angiosarcoma": {"chemo": ["Paclitaxel", "Doxorubicin"], "targeted": ["Bevacizumab", "Pazopanib"]},

    # Solid
    "Breast": {"chemo": ["Paclitaxel", "Docetaxel", "Doxorubicin", "Cyclophosphamide"], "targeted": ["Trastuzumab", "Pertuzumab", "T-DM1", "Trastuzumab deruxtecan", "Tucatinib"]},
    "Colon": {"chemo": ["Oxaliplatin", "Irinotecan", "Capecitabine", "5-FU"], "targeted": ["Bevacizumab", "Ramucirumab", "Regorafenib"]},
    "Rectal": {"chemo": ["Oxaliplatin", "5-FU", "Capecitabine"], "targeted": ["Bevacizumab"]},
    "Gastric": {"chemo": ["Oxaliplatin", "Capecitabine", "5-FU", "Irinotecan"], "targeted": ["Trastuzumab", "Ramucirumab"]},
    "Esophageal": {"chemo": ["Cisplatin", "5-FU", "Paclitaxel"], "targeted": ["Nivolumab", "Pembrolizumab"]},
    "Pancreatic": {"chemo": ["Gemcitabine", "FOLFIRINOX", "Nab-Paclitaxel"], "targeted": []},
    "Hepatocellular carcinoma": {"chemo": [], "targeted": ["Regorafenib", "Sorafenib", "Cabozantinib"]},
    "Cholangiocarcinoma": {"chemo": ["Gemcitabine", "Cisplatin"], "targeted": ["Pemigatinib"]},
    "Gallbladder": {"chemo": ["Gemcitabine", "Cisplatin"], "targeted": []},
    "Lung": {"chemo": ["Carboplatin", "Cisplatin", "Pemetrexed", "Docetaxel", "Paclitaxel"], "targeted": ["Osimertinib", "Nivolumab", "Pembrolizumab", "Alectinib", "Lorlatinib", "Capmatinib", "Entrectinib", "Crizotinib", "Sotorasib"]},
    "NSCLC": {"chemo": ["Carboplatin", "Pemetrexed"], "targeted": ["Osimertinib", "Alectinib", "Lorlatinib", "Capmatinib", "Sotorasib"]},
    "SCLC": {"chemo": ["Carboplatin", "Etoposide"], "targeted": ["Atezolizumab"]},
    "Head & Neck": {"chemo": ["Cisplatin", "5-FU", "Paclitaxel"], "targeted": ["Pembrolizumab"]},
    "Thyroid (PTC)": {"chemo": [], "targeted": []},
    "Thyroid (FTC)": {"chemo": [], "targeted": []},
    "MTC": {"chemo": [], "targeted": ["Vandetanib", "Cabozantinib"]},
    "ATC": {"chemo": ["Paclitaxel"], "targeted": ["BRAF/MEK"]},
    "Kidney (RCC)": {"chemo": [], "targeted": ["Sunitinib", "Pazopanib", "Nivolumab", "Cabozantinib"]},
    "Urothelial": {"chemo": ["Cisplatin", "Gemcitabine"], "targeted": ["Pembrolizumab"]},
    "Prostate": {"chemo": ["Docetaxel"], "targeted": []},
    "Ovary": {"chemo": ["Carboplatin", "Paclitaxel"], "targeted": ["Bevacizumab"]},
    "Cervical": {"chemo": ["Cisplatin", "Paclitaxel"], "targeted": ["Bevacizumab", "Pembrolizumab"]},
    "Endometrial": {"chemo": ["Carboplatin", "Paclitaxel"], "targeted": ["Pembrolizumab"]},
    "Testicular (Seminoma)": {"chemo": ["Cisplatin", "Etoposide", "Bleomycin"], "targeted": []},
    "Testicular (NSGCT)": {"chemo": ["Cisplatin", "Etoposide", "Bleomycin"], "targeted": []},
    "GIST": {"chemo": [], "targeted": ["Imatinib", "Sunitinib", "Regorafenib", "Ripretinib"]},
    "NET": {"chemo": [], "targeted": ["Octreotide", "Everolimus"]},

    # Rare
    "Neuroblastoma": {"chemo": ["Cyclophosphamide", "Cisplatin", "Etoposide"], "targeted": []},
    "Wilms tumor": {"chemo": ["Vincristine", "Dactinomycin", "Doxorubicin"], "targeted": []},
    "Hepatoblastoma": {"chemo": ["Cisplatin", "Doxorubicin"], "targeted": []},
    "Retinoblastoma": {"chemo": ["Carboplatin", "Vincristine", "Etoposide"], "targeted": []},
    "Medulloblastoma": {"chemo": ["Cisplatin", "Cyclophosphamide", "Vincristine"], "targeted": []},
    "Ependymoma": {"chemo": [], "targeted": []},
    "Chordoma": {"chemo": [], "targeted": ["Imatinib"]},
    "Mesothelioma": {"chemo": ["Cisplatin", "Pemetrexed"], "targeted": []},
    "ACC": {"chemo": [], "targeted": ["Cabozantinib"]},
    "Pheochromocytoma/Paraganglioma": {"chemo": [], "targeted": []},
    "Thymic carcinoma": {"chemo": ["Carboplatin", "Paclitaxel"], "targeted": []},
    "Histiocytosis": {"chemo": ["Vinblastine", "Prednisone"], "targeted": []},
}

def _dedup(seq):
    out, seen = [], set()
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
    d = (dx or "").strip()
    rec = _REC.get(d) or _REC.get(d.upper()) or _REC.get(d.title()) or {}
    chemo = _in_db_only(rec.get("chemo", []), db)
    targeted = _in_db_only(rec.get("targeted", []), db)
    return {"chemo": _dedup(chemo), "targeted": _dedup(targeted), "abx": []}
