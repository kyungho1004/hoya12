# -*- coding: utf-8 -*-
"""Drug lists by cancer types.
NOTE: Names include Korean where possible. Mechanisms/notes kept brief for skeleton.
Critical: APL includes MTX & 6-MP as requested.
"""

# Hematologic malignancies
HEME = {
    "AML": ["Ara-C (Cytarabine)", "Idarubicin", "Daunorubicin", "Midostaurin (FLT3)"],
    "APL": ["ATRA (All-Trans Retinoic Acid)", "Arsenic Trioxide", "MTX (메토트렉세이트)", "6-MP (6-머캅토퓨린)"],
    "ALL": ["Vincristine", "Dexamethasone", "MTX", "6-MP", "Asparaginase"],
    "CML": ["Imatinib", "Dasatinib", "Nilotinib", "Bosutinib", "Ponatinib"],
    "CLL": ["Ibrutinib", "Acalabrutinib", "Venetoclax", "Obinutuzumab"],
}

# Lymphoma subtypes (default regimens; skeleton)
LYMPHOMA = {
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

# Solid tumors (very brief examples)
SOLID = {
    "폐선암": ["EGFR TKI (Osimertinib)", "ALK TKI (Alectinib)", "PD-1 inhibitor"],
    "유방암": ["Tamoxifen", "Aromatase Inhibitor", "HER2 agent (Trastuzumab)"],
    "위암": ["Fluoropyrimidine + Platinum", "Ramucirumab", "Trastuzumab (HER2+)"],
    "대장암": ["FOLFOX/FOLFIRI", "Bevacizumab", "Cetuximab (RAS WT)"],
    "간암": ["Atezolizumab + Bevacizumab", "Sorafenib", "Lenvatinib"],
}

# Sarcomas (skeleton)
SARCOMA = {
    "연부조직육종": ["Doxorubicin", "Ifosfamide", "Trabectedin"],
    "골육종": ["MAP (MTX, Doxorubicin, Cisplatin)"],
    "유잉육종": ["VDC/IE"],
}

# Rare cancers (skeleton)
RARE = {
    "GIST": ["Imatinib", "Sunitinib", "Regorafenib"],
    "담관암": ["Gemcitabine + Cisplatin", "Pemigatinib (FGFR2)"],
}

def get_drugs(group: str, diagnosis: str):
    """Return list of default drugs for a (group, diagnosis).
    group one of: '혈액암', '림프종', '고형암', '육종', '희귀암'
    """
    group_map = {
        "혈액암": HEME,
        "림프종": LYMPHOMA,
        "고형암": SOLID,
        "육종": SARCOMA,
        "희귀암": RARE,
    }
    table = group_map.get(group, {})
    # For lymphoma, accept common aliases
    lymphoma_key_map = {"B거대세포": "DLBCL", "DLBCL": "DLBCL", "FL1/2": "FL12", "FL3A": "FL3A", "FL3B": "FL3B"}
    if group == "림프종":
        diagnosis = lymphoma_key_map.get(diagnosis, diagnosis)
    return list(dict.fromkeys(table.get(diagnosis, [])))
