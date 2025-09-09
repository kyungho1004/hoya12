# -*- coding: utf-8 -*-
"""Drug lists and selections by cancer categories/diagnoses, incl. targeted and antibiotics."""

# === Diagnoses by category ===
HEMATO = ["AML","APL","ALL","CML","CLL"]

LYMPHOMA = ["DLBCL","PMBCL","FL12","FL3A","FL3B","MCL","MZL","HGBL","BL"]

SOLID = [
    "폐선암","폐편평","소세포폐암",
    "유방암(HR+)","유방암(HER2+)","유방암(TNBC)",
    "위암","대장암 좌측","대장암 우측","직장암",
    "간암(HCC)","췌장암","담낭/담관암","신장암","갑상선암",
    "난소암","자궁내막암","전립선암","흑색종","두경부암"
]

SARCOMA = ["연부조직육종","골육종","유잉육종"]

RARE = ["GIST","신경내분비종양(NET)"]

# === Default chemo/support per diagnosis ===
HEME_DEFAULT = {
    "AML": ["Ara-C (Cytarabine, IV)","Idarubicin","Daunorubicin","Midostaurin (FLT3)"],
    "APL": ["ATRA (Vesanoid)","Arsenic Trioxide","MTX (메토트렉세이트)","6-MP (6-머캅토퓨린)"],
    "ALL": ["Vincristine","Dexamethasone","MTX","6-MP","Asparaginase"],
    "CML": ["Imatinib","Dasatinib","Nilotinib","Bosutinib","Ponatinib"],
    "CLL": ["Ibrutinib","Acalabrutinib","Venetoclax","Obinutuzumab"],
}

LYM_DEFAULT = {
    "DLBCL": ["R-CHOP","Pola-R-CHP","DA-EPOCH-R","R-ICE","R-DHAP","R-GDP","R-GemOx"],
    "PMBCL": ["DA-EPOCH-R","R-ICE","R-DHAP"],
    "FL12": ["BR","R-CVP","R-CHOP","Lenalidomide + Rituximab"],
    "FL3A": ["R-CHOP","Pola-R-CHP","BR"],
    "FL3B": ["R-CHOP","Pola-R-CHP","DA-EPOCH-R"],
    "MCL": ["BR","R-CHOP","Ibrutinib","Acalabrutinib","Zanubrutinib"],
    "MZL": ["BR","R-CVP","R-CHOP"],
    "HGBL": ["R-CHOP","Pola-R-CHP","DA-EPOCH-R"],
    "BL": ["CODOX-M/IVAC-R","Hyper-CVAD-R","R-ICE"],
}

SOLID_DEFAULT = {
    "폐선암": ["플라티넘 병용","PD-1/PD-L1 면역치료"],
    "폐편평": ["플라티넘 병용","PD-1/PD-L1 면역치료"],
    "소세포폐암": ["플라티넘 + Etoposide","Atezolizumab/Durvalumab 병용"],
    "유방암(HR+)": ["Tamoxifen","Aromatase Inhibitor","CDK4/6 억제제"],
    "유방암(HER2+)": ["Trastuzumab + Pertuzumab","T-DM1"],
    "유방암(TNBC)": ["백금계 병용","Pembrolizumab(조건부)"],
    "위암": ["Fluoropyrimidine + Platinum","Ramucirumab"],
    "대장암 좌측": ["FOLFOX/FOLFIRI","Bevacizumab"],
    "대장암 우측": ["FOLFOX/FOLFIRI","Bevacizumab"],
    "직장암": ["FOLFOX","방사선병용"],
    "간암(HCC)": ["Atezolizumab + Bevacizumab","Durvalumab + Tremelimumab(STRIDE)","Sorafenib","Lenvatinib"],
    "췌장암": ["FOLFIRINOX","Gemcitabine + nab-Paclitaxel"],
    "담낭/담관암": ["Gemcitabine + Cisplatin","Durvalumab 병용"],
    "신장암": ["IO/TKI 병용 (Pembrolizumab + Axitinib 등)","TKI 단독"],
    "갑상선암": ["Levothyroxine 보조","Sorafenib/Lenvatinib(진행)"],
    "난소암": ["Carboplatin + Paclitaxel","Bevacizumab 추가 가능"],
    "자궁내막암": ["Carboplatin + Paclitaxel","Pembrolizumab( MSI-H )"],
    "전립선암": ["Androgen Deprivation","Abiraterone/Enzalutamide","Docetaxel"],
    "흑색종": ["PD-1 ± CTLA-4 면역치료","BRAF/MEK 억제제(변이)"],
    "두경부암": ["플라티넘 기반 + 면역치료"],
}

SARCOMA_DEFAULT = {
    "연부조직육종": ["Doxorubicin","Ifosfamide","Trabectedin"],
    "골육종": ["MAP (MTX, Doxorubicin, Cisplatin)"],
    "유잉육종": ["VDC/IE"],
}

RARE_DEFAULT = {
    "GIST": ["Imatinib","Sunitinib","Regorafenib"],
    "신경내분비종양(NET)": ["Octreotide/Lanreotide","Everolimus","Sunitinib"],
}

# === Targeted therapies (biomarker-driven) ===
TARGETED = {
    # Lung
    ("고형암","폐선암","EGFR"): ["Osimertinib (EGFR TKI)"],
    ("고형암","폐선암","ALK"): ["Alectinib (ALK TKI)"],
    ("고형암","폐선암","ROS1"): ["Crizotinib/Entrectinib"],
    ("고형암","폐선암","RET"): ["Selpercatinib/Pralsetinib"],
    ("고형암","폐선암","BRAF V600E"): ["Dabrafenib + Trametinib"],
    ("고형암","폐선암","METex14"): ["Capmatinib/Tepotinib"],
    ("고형암","폐선암","KRAS G12C"): ["Sotorasib/Adagrasib"],
    # Breast
    ("고형암","유방암(HER2+)","HER2"): ["Trastuzumab","Pertuzumab","T-DM1","Tucatinib + Trastuzumab"],
    ("고형암","유방암(HR+)","PIK3CA"): ["Alpelisib"],
    ("고형암","유방암(HR+)","BRCA"): ["Olaparib/Talazoparib"],
    # CRC
    ("고형암","대장암 좌측","RAS WT"): ["Cetuximab/Panitumumab"],
    ("고형암","대장암 우측","MSI-H"): ["Pembrolizumab/Nivolumab+Ipilimumab"],
    ("고형암","대장암 좌측","BRAF V600E"): ["Encorafenib + Cetuximab"],
    ("고형암","대장암 좌측","HER2"): ["Trastuzumab + Tucatinib"],
    # Gastric
    ("고형암","위암","HER2"): ["Trastuzumab"],
    ("고형암","위암","CLDN18.2"): ["Zolbetuximab"],
    # HCC
    ("고형암","간암(HCC)","VEGF"): ["Bevacizumab/Ramucirumab(AFP≥400)"],
    # Cholangiocarcinoma
    ("고형암","담낭/담관암","FGFR2"): ["Pemigatinib/Futibatinib"],
    ("고형암","담낭/담관암","IDH1"): ["Ivosidenib"],
    # Thyroid
    ("고형암","갑상선암","RET"): ["Selpercatinib"],
    ("고형암","갑상선암","NTRK"): ["Larotrectinib/Entrectinib"],
    # Melanoma
    ("고형암","흑색종","BRAF V600E"): ["Dabrafenib + Trametinib"],
}

# === Common antibiotics used in oncology (caregiver-friendly names) ===
ABX_COMMON = [
    "피페라실린/타조박탐(광범위 베타락탐)", 
    "세프트리악손(주사 3세대 세팔로)", 
    "레보플록사신(경구 퀴놀론)",
    "메트로니다졸(혐기성)",
    "반코마이신(MRSA 가능)",
]

def list_diagnoses(group: str):
    return {
        "혈액암": HEMATO,
        "림프종": LYMPHOMA,
        "고형암": SOLID,
        "육종": SARCOMA,
        "희귀암": RARE,
    }.get(group, [])

def get_default_drugs(group: str, dx: str):
    return {
        "혈액암": HEME_DEFAULT,
        "림프종": LYM_DEFAULT,
        "고형암": SOLID_DEFAULT,
        "육종": SARCOMA_DEFAULT,
        "희귀암": RARE_DEFAULT,
    }.get(group, {}).get(dx, [])

def get_targeted(group: str, dx: str, biomarker: str):
    return TARGETED.get((group, dx, biomarker), [])

def common_antibiotics():
    return ABX_COMMON

# --- Solid tumor groups (for UX) ---
SOLID_GROUPS = {
    "폐암": ["폐선암","폐편평","소세포폐암"],
    "유방암": ["유방암(HR+)","유방암(HER2+)","유방암(TNBC)"],
    "소화기": ["위암","대장암 좌측","대장암 우측","직장암","췌장암","담낭/담관암"],
    "간/신장/갑상선": ["간암(HCC)","신장암","갑상선암"],
    "부인과": ["난소암","자궁내막암"],
    "비뇨기": ["전립선암"],
    "피부/두경부": ["흑색종","두경부암"],
    "기타": [],
}

def list_solid_groups():
    return list(SOLID_GROUPS.keys())

def list_solid_by_group(group_name: str):
    return SOLID_GROUPS.get(group_name, [])
