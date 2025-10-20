
# -*- coding: utf-8 -*-
"""
onco_map.py (v3.1, strengthened)
- 5 groups: 혈액암 / 림프종 / 육종 / 고형암 / 희귀암
- build_onco_map(): grouped dict
- dx_display(group, dx): "group - EN (KO)" unless already Korean
- auto_recs_by_dx(group, dx, db): returns only keys that exist in provided DRUG_DB
"""

from __future__ import annotations

# ---------- Korean names ----------
_DX_KO = {
    # Hematologic
    "ALL": "급성 림프구성 백혈병",
    "AML": "급성 골수성 백혈병",
    "APL": "급성 전골수성 백혈병",
    "CML": "만성 골수성 백혈병",
    "CLL": "만성 림프구성 백혈병",
    "PCNSL": "원발성 중추신경계 림프종",
    # Lymphoma
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
    # Solid
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
    "Kidney (RCC)": "신세포암",
    "Urothelial": "요로상피암",
    "Prostate": "전립선암",
    "Ovary": "난소암",
    "Cervical": "자궁경부암",
    "Endometrial": "자궁내막암",
    "Testicular (Seminoma)": "고환종양(세미노마)",
    "Testicular (NSGCT)": "고환종양(비세미노마)",
    "GIST": "위장관기저종양",
    "NET": "신경내분비종양",
    # Sarcoma
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
    # Rare
    "Neuroblastoma": "신경모세포종",
    "Wilms tumor": "윌름스 종양",
    "Hepatoblastoma": "간모세포종",
    "Retinoblastoma": "망막모세포종",
    "Medulloblastoma": "수모세포종",
    "Ependymoma": "상의세포종",
    "Germinoma": "배세포종(중추신경계)",
    "Chordoma": "척삭종",
    "Desmoid tumor": "데스모이드 종양",
    "Mesothelioma": "악성 중피종",
    "ACC": "부신피질암",
    "Pheochromocytoma/Paraganglioma": "갈색세포종/부신외갈색세포종",
    "Thymic carcinoma": "흉선암",
    "Thymoma": "흉선종",
    "Histiocytosis": "조직구증(히스티오사이토시스)",
}

def _is_korean(s: str) -> bool:
    return any('\uac00' <= ch <= '\ud7a3' for ch in (s or ""))

def _norm_key(s: str) -> str:
    if not s: return ""
    u = " ".join(s.strip().replace("_"," ").replace("-"," ").split())
    return u

def build_onco_map() -> dict:
    heme = {"ALL": {}, "AML": {}, "APL": {"chemo": ["Ara-C","Daunorubicin","Idarubicin", "MTX", "6-MP"], "targeted": ["ATRA","Arsenic Trioxide"]}, "CML": {}, "CLL": {}, "PCNSL": {"chemo": ["MTX", "Ara-C"], "targeted": ["Rituximab"]}}
    lymphoma = {
        "DLBCL": {}, "PMBCL": {}, "HGBL": {}, "BL": {},
        "FL": {}, "MZL": {}, "MCL": {}, "CHL": {}, "NLPHL": {},
        "PTCL-NOS": {}, "AITL": {}, "ALCL (ALK+)": {}, "ALCL (ALK-)": {}, "ENKTL": {},
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
        "Thymoma": {"chemo": ["Carboplatin","Paclitaxel"], "targeted": [], "abx": []},
        "Desmoid tumor": {"chemo": [], "targeted": ["Imatinib"], "abx": []},
        "Germinoma": {"chemo": ["Carboplatin","Etoposide"], "targeted": [], "abx": []},
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

# Minimal recommendation seeds (use only keys likely present; final filter happens by DB)
_REC = {
    "ALL": {"chemo": ["6-MP, Ara-C, Cyclophosphamide, Doxorubicin, MTX, Prednisone, Vincristine"], "targeted": ["Imatinib","Rituximab"]},
    "AML": {"chemo": ["Ara-C","Etoposide","Doxorubicin"], "targeted": []},
    "APL": {"chemo": ["Ara-C","Daunorubicin","Idarubicin"], "targeted": ["ATRA","Arsenic Trioxide"]},
    "CML": {"chemo": [], "targeted": ["Imatinib"]},
    "CLL": {"chemo": ["Cyclophosphamide","Chlorambucil","Prednisone"], "targeted": ["Ibrutinib","Obinutuzumab","Rituximab"]},
    "PCNSL": {"chemo": ["Ara-C"], "targeted": ["Rituximab"]},

    "DLBCL": {"chemo": ["Cyclophosphamide","Doxorubicin","Vincristine","Prednisone"], "targeted": ["Rituximab","Polatuzumab Vedotin"]},
    "PMBCL": {"chemo": ["Cyclophosphamide","Doxorubicin","Vincristine","Prednisone","Etoposide"], "targeted": ["Rituximab"]},
    "HGBL": {"chemo": ["Cyclophosphamide","Doxorubicin","Vincristine","Prednisone","Etoposide"], "targeted": ["Rituximab"]},
    "BL": {"chemo": ["Cyclophosphamide","Doxorubicin","Vincristine","Ara-C"], "targeted": ["Rituximab"]},
    "FL": {"chemo": ["Cyclophosphamide","Doxorubicin","Vincristine","Prednisone","Bendamustine"], "targeted": ["Rituximab","Obinutuzumab"]},
    "MZL": {"chemo": ["Cyclophosphamide","Bendamustine","Chlorambucil"], "targeted": ["Rituximab","Obinutuzumab"]},
    "MCL": {"chemo": ["Cyclophosphamide","Bendamustine"], "targeted": ["Ibrutinib","Rituximab"]},
    "CHL": {"chemo": ["Doxorubicin","Vinblastine","Dacarbazine","Bleomycin"], "targeted": ["Brentuximab Vedotin","Nivolumab","Pembrolizumab"]},
    "NLPHL": {"chemo": ["Cyclophosphamide","Doxorubicin","Vincristine","Prednisone"], "targeted": ["Rituximab"]},
    "PTCL-NOS": {"chemo": ["Cyclophosphamide","Doxorubicin","Etoposide"], "targeted": []},
    "AITL": {"chemo": ["Cyclophosphamide","Doxorubicin","Etoposide"], "targeted": []},
    "ALCL (ALK+)": {"chemo": ["Cyclophosphamide","Doxorubicin","Etoposide"], "targeted": ["Brentuximab Vedotin"]},
    "ALCL (ALK-)": {"chemo": ["Cyclophosphamide","Doxorubicin","Etoposide"], "targeted": ["Brentuximab Vedotin"]},
    "ENKTL": {"chemo": ["Cyclophosphamide","Doxorubicin","Etoposide"], "targeted": []},

    "Osteosarcoma": {"chemo": ["Doxorubicin","Cisplatin","Ifosfamide","Etoposide"], "targeted": []},
    "Ewing sarcoma": {"chemo": ["Vincristine","Doxorubicin","Cyclophosphamide","Ifosfamide","Etoposide"], "targeted": []},
    "Rhabdomyosarcoma": {"chemo": ["Vincristine","Dactinomycin","Cyclophosphamide","Ifosfamide","Etoposide"], "targeted": []},
    "Synovial Sarcoma": {"chemo": ["Ifosfamide","Doxorubicin"], "targeted": []},
    "Leiomyosarcoma": {"chemo": ["Doxorubicin","Ifosfamide","Trabectedin","Gemcitabine","Docetaxel"], "targeted": ["Pazopanib"]},
    "Liposarcoma": {"chemo": ["Doxorubicin","Ifosfamide","Trabectedin"], "targeted": []},
    "MPNST": {"chemo": ["Doxorubicin","Ifosfamide"], "targeted": []},
    "DFSP": {"chemo": [], "targeted": ["Imatinib"]},
    "UPS": {"chemo": ["Doxorubicin","Ifosfamide","Paclitaxel","Gemcitabine","Docetaxel"], "targeted": ["Pazopanib"]},
    "Angiosarcoma": {"chemo": ["Paclitaxel","Doxorubicin"], "targeted": ["Bevacizumab","Pazopanib"]},

    "Breast": {"chemo": ["Paclitaxel","Docetaxel","Doxorubicin","Cyclophosphamide"], "targeted": ["Trastuzumab","Pertuzumab","T-DM1","Trastuzumab deruxtecan","Tucatinib","Lapatinib"]},
    "Colon": {"chemo": ["Oxaliplatin","Irinotecan","Capecitabine","5-FU"], "targeted": ["Bevacizumab","Ramucirumab","Regorafenib"]},
    "Rectal": {"chemo": ["Oxaliplatin","5-FU","Capecitabine"], "targeted": ["Bevacizumab"]},
    "Gastric": {"chemo": ["Oxaliplatin","Capecitabine","5-FU","Irinotecan"], "targeted": ["Trastuzumab","Ramucirumab"]},
    "Esophageal": {"chemo": ["Cisplatin","5-FU","Paclitaxel"], "targeted": ["Nivolumab","Pembrolizumab"]},
    "Pancreatic": {"chemo": ["Gemcitabine","Oxaliplatin","Irinotecan"], "targeted": []},
    "Hepatocellular carcinoma": {"chemo": [], "targeted": ["Regorafenib","Cabozantinib"]},
    "Cholangiocarcinoma": {"chemo": ["Gemcitabine","Cisplatin"], "targeted": []},
    "Gallbladder": {"chemo": ["Gemcitabine","Cisplatin"], "targeted": []},
    "Lung": {"chemo": ["Carboplatin","Cisplatin","Pemetrexed","Docetaxel","Paclitaxel"], "targeted": ["Larotrectinib", "Osimertinib","Nivolumab","Pembrolizumab","Alectinib","Lorlatinib","Capmatinib","Entrectinib","Crizotinib","Sotorasib"]},
    "NSCLC": {"chemo": ["Carboplatin","Pemetrexed"], "targeted": ["Larotrectinib", "Osimertinib","Alectinib","Lorlatinib","Capmatinib","Sotorasib"]},
    "SCLC": {"chemo": ["Carboplatin","Etoposide"], "targeted": []},
    "Head & Neck": {"chemo": ["Cisplatin","5-FU","Paclitaxel"], "targeted": ["Pembrolizumab"]},
    "Thyroid (PTC)": {"chemo": [], "targeted": []},
    "Thyroid (FTC)": {"chemo": [], "targeted": []},
    "MTC": {"chemo": [], "targeted": ["Vandetanib","Cabozantinib","Selpercatinib","Pralsetinib"]},
    "ATC": {"chemo": ["Paclitaxel"], "targeted": []},
    "Kidney (RCC)": {"chemo": [], "targeted": ["Sunitinib","Pazopanib","Nivolumab","Cabozantinib"]},
    "Urothelial": {"chemo": ["Cisplatin","Gemcitabine"], "targeted": ["Pembrolizumab"]},
    "Prostate": {"chemo": ["Docetaxel"], "targeted": []},
    "Ovary": {"chemo": ["Carboplatin","Paclitaxel","Topotecan"], "targeted": ["Bevacizumab"]},
    "Cervical": {"chemo": ["Cisplatin","Paclitaxel"], "targeted": ["Bevacizumab","Pembrolizumab"]},
    "Endometrial": {"chemo": ["Carboplatin","Paclitaxel"], "targeted": ["Pembrolizumab"]},
    "Testicular (Seminoma)": {"chemo": ["Cisplatin","Etoposide","Bleomycin"], "targeted": []},
    "Testicular (NSGCT)": {"chemo": ["Cisplatin","Etoposide","Bleomycin"], "targeted": []},
    "GIST": {"chemo": [], "targeted": ["Imatinib","Sunitinib","Regorafenib","Ripretinib"]},
    "NET": {"chemo": [], "targeted": ["Octreotide","Everolimus"]},

    "Neuroblastoma": {"chemo": ["Cyclophosphamide","Cisplatin","Etoposide"], "targeted": []},
    "Wilms tumor": {"chemo": ["Vincristine","Dactinomycin","Doxorubicin"], "targeted": []},
    "Hepatoblastoma": {"chemo": ["Cisplatin","Doxorubicin"], "targeted": []},
    "Retinoblastoma": {"chemo": ["Carboplatin","Vincristine","Etoposide"], "targeted": []},
    "Medulloblastoma": {"chemo": ["Cisplatin","Cyclophosphamide","Vincristine"], "targeted": []},
    "Ependymoma": {"chemo": [], "targeted": []},
    "Chordoma": {"chemo": [], "targeted": ["Imatinib"]},
    "Mesothelioma": {"chemo": ["Cisplatin","Pemetrexed"], "targeted": []},
    "ACC": {"chemo": [], "targeted": ["Cabozantinib"]},
    "Pheochromocytoma/Paraganglioma": {"chemo": [], "targeted": []},
    "Thymic carcinoma": {"chemo": ["Carboplatin","Paclitaxel"], "targeted": []},
    "Histiocytosis": {"chemo": ["Vinblastine","Prednisone"], "targeted": []},
}

def _dedup(seq):
    out, seen = [], set()
    for x in seq or []:
        if x not in seen:
            out.append(x); seen.add(x)
    return out

def _in_db_only(keys, db):
    return [k for k in (keys or []) if k in (db or {})]

def auto_recs_by_dx(group: str, dx: str, db=None):
    d = (dx or "").strip()
    rec = _REC.get(d) or _REC.get(d.upper()) or _REC.get(d.title()) or {}
    chemo = _in_db_only(rec.get("chemo", []), db)
    targeted = _in_db_only(rec.get("targeted", []), db)
    return {"chemo": _dedup(chemo), "targeted": _dedup(targeted), "abx": []}
