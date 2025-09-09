# -*- coding: utf-8 -*-
"""Drug lists and selections by cancer categories/diagnoses, incl. targeted and antibiotics."""

# === Diagnoses by category ===
HEMATO = [
    "AML", "APL", "ALL", "CML", "CLL"
]

LYMPHOMA = [
    "DLBCL", "PMBCL", "FL12", "FL3A", "FL3B", "MCL", "MZL", "HGBL", "BL"
]

SOLID = [
    "폐선암", "유방암", "위암", "대장암", "간암"
]

SARCOMA = [
    "연부조직육종", "골육종", "유잉육종"
]

RARE = [
    "GIST", "담관암"
]

# === Default chemo/support per diagnosis ===
HEME_DEFAULT = {
    "AML": ["Ara-C (Cytarabine, IV)", "Idarubicin", "Daunorubicin", "Midostaurin (FLT3)"],
    "APL": ["ATRA (Vesanoid)", "Arsenic Trioxide", "MTX (메토트렉세이트)", "6-MP (6-머캅토퓨린)"],
    "ALL": ["Vincristine", "Dexamethasone", "MTX", "6-MP", "Asparaginase"],
    "CML": ["Imatinib", "Dasatinib", "Nilotinib", "Bosutinib", "Ponatinib"],
    "CLL": ["Ibrutinib", "Acalabrutinib", "Venetoclax", "Obinutuzumab"],
}

LYM_DEFAULT = {
    "DLBCL": ["R-CHOP", "Pola-R-CHP", "DA-EPOCH-R", "R-ICE", "R-DHAP", "R-GDP", "R-GemOx"],
    "PMBCL": ["DA-EPOCH-R", "R-ICE", "R-DHAP"],
    "FL12": ["BR", "R-CVP", "R-CHOP", "Lenalidomide + Rituximab"],
    "FL3A": ["R-CHOP", "Pola-R-CHP", "BR"],
    "FL3B": ["R-CHOP", "Pola-R-CHP", "DA-EPOCH-R"],
    "MCL": ["BR", "R-CHOP", "Ibrutinib", "Acalabrutinib", "Zanubrutinib"],
    "MZL": ["BR", "R-CVP", "R-CHOP"],
    "HGBL": ["R-CHOP", "Pola-R-CHP", "DA-EPOCH-R"],
    "BL": ["CODOX-M/IVAC-R", "Hyper-CVAD-R", "R-ICE"],
}

SOLID_DEFAULT = {
    "폐선암": ["플라티넘 병용", "PD-1/PD-L1 면역치료"],
    "유방암": ["Tamoxifen", "Aromatase Inhibitor"],
    "위암": ["Fluoropyrimidine + Platinum", "Ramucirumab"],
    "대장암": ["FOLFOX/FOLFIRI", "Bevacizumab"],
    "간암": ["Atezolizumab + Bevacizumab", "Sorafenib", "Lenvatinib"],
}

SARCOMA_DEFAULT = {
    "연부조직육종": ["Doxorubicin", "Ifosfamide", "Trabectedin"],
    "골육종": ["MAP (MTX, Doxorubicin, Cisplatin)"],
    "유잉육종": ["VDC/IE"],
}

RARE_DEFAULT = {
    "GIST": ["Imatinib", "Sunitinib", "Regorafenib"],
    "담관암": ["Gemcitabine + Cisplatin", "Pemigatinib (FGFR2)"],
}

# === Targeted therapies (biomarker-driven) ===
TARGETED = {
    # Solid
    ("고형암", "폐선암", "EGFR"): ["Osimertinib (EGFR TKI)"],
    ("고형암", "폐선암", "ALK"): ["Alectinib (ALK TKI)"],
    ("고형암", "폐선암", "ROS1"): ["Crizotinib (ROS1 TKI)"],
    ("고형암", "유방암", "HER2"): ["Trastuzumab (HER2)"],
    ("고형암", "대장암", "RAS WT"): ["Cetuximab (EGFR mAb)"],
    ("희귀암", "GIST", "KIT/PDGFRA"): ["Imatinib"],
}

# === Common antibiotics used in oncology (caregiver-friendly names) ===
ABX_COMMON = [
    "피페라실린/타조박탐(광범위 베타락탐)", 
    "세프트리악손(주사 3세대 세팔로스포린)",
    "레보플록사신(경구 퀴놀론)",
    "메트로니다졸(혐기성)",
    "반코마이신(MRSA 가능)",
]

def list_diagnoses(group: str):
    if group == "혈액암":
        return HEMATO
    if group == "림프종":
        return LYMPHOMA
    if group == "고형암":
        return SOLID
    if group == "육종":
        return SARCOMA
    if group == "희귀암":
        return RARE
    return []

def get_default_drugs(group: str, dx: str):
    if group == "혈액암":
        return HEME_DEFAULT.get(dx, [])
    if group == "림프종":
        return LYM_DEFAULT.get(dx, [])
    if group == "고형암":
        return SOLID_DEFAULT.get(dx, [])
    if group == "육종":
        return SARCOMA_DEFAULT.get(dx, [])
    if group == "희귀암":
        return RARE_DEFAULT.get(dx, [])
    return []

def get_targeted(group: str, dx: str, biomarker: str):
    return TARGETED.get((group, dx, biomarker), [])

def common_antibiotics():
    return ABX_COMMON
