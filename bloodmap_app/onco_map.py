# -*- coding: utf-8 -*-
from typing import Dict, List, Any

# -----------------------------
# Korean label helpers
# -----------------------------
def _is_korean(s: str) -> bool:
    return any('\uac00' <= ch <= '\ud7a3' for ch in (s or ""))

def _norm(s: str) -> str:
    if not s:
        return ""
    s2 = (s or "").strip()
    code = s2.upper().replace(" ", "")
    # normalize common codes
    CODE_ALIASES = {
        "DLBCL": "DLBCL", "PMBCL": "PMBCL", "HGBL": "HGBL", "BL": "BL",
        "APL": "APL", "AML": "AML", "ALL": "ALL", "CML": "CML", "CLL": "CLL", "PCNSL": "PCNSL"
    }
    return CODE_ALIASES.get(code, s2)

# Korean display names (병기)
DX_KO: Dict[str, str] = {
    # Hematology
    "APL": "급성 전골수구성 백혈병",
    "AML": "급성 골수성 백혈병",
    "ALL": "급성 림프구성 백혈병",
    "CML": "만성 골수성 백혈병",
    "CLL": "만성 림프구성 백혈병",
    "PCNSL": "원발성 중추신경계 림프종",

    # Lymphoma (with common Korean synonyms)
    "DLBCL": "미만성 거대 B세포 림프종",
    "B거대세포종": "미만성 거대 B세포 림프종",
    "B 거대세포종": "미만성 거대 B세포 림프종",
    "B거대세포 림프종": "미만성 거대 B세포 림프종",
    "b거대세포종": "미만성 거대 B세포 림프종",
    "PMBCL": "원발성 종격동 B세포 림프종",
    "HGBL": "고등급 B세포 림프종",
    "BL": "버킷 림프종",
    "FL": "여포성 림프종",
    "MZL": "변연부 림프종",
    "MALT lymphoma": "점막연관 변연부 B세포 림프종",
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

    # Solid & Rare
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
# -----------------------------
# Canonical drug key mapping
# -----------------------------
KEY_ALIAS = {
    "Ara-C": "Cytarabine",
    "ATO": "Arsenic Trioxide",
    "ATRA": "ATRA",
    "6-MP": "6-MP",
    "5-FU": "5-FU",
    "T-DM1": "T-DM1",
    "ALCL (ALK−)": "ALCL (ALK-)"
}
def _canon(key: str) -> str:
    return KEY_ALIAS.get(key, key)


def dx_display(group: str, dx: str) -> str:
    dx = (dx or "").strip()
    key = _norm(dx)
    ko = DX_KO.get(key) or DX_KO.get(dx)
    if _is_korean(dx):
        return f"{group} - {dx}"
    if ko:
        return f"{group} - {dx} ({ko})"
    return f"{group} - {dx}"

# -----------------------------
# Treatment map
# -----------------------------
def build_onco_map() -> Dict[str, Dict[str, Dict[str, List[str]]]]:
    return {
        "혈액암": {
            "APL": {"chemo": ["ATRA", "Arsenic Trioxide", "Idarubicin", "MTX", "6-MP", "Cytarabine"], "targeted": [], "abx": []},
            "AML": {"chemo": ["Cytarabine","Daunorubicin","Idarubicin"], "targeted": [], "abx": []},
            "ALL": {"chemo": ["Vincristine","Ara-C","MTX","6-MP","Cyclophosphamide","Prednisone"], "targeted": [], "abx": []},
            "CML": {"chemo": [], "targeted": ["Imatinib"], "abx": []},
            "CLL": {"chemo": ["Cyclophosphamide","Prednisone","Chlorambucil"], "targeted": ["Rituximab"], "abx": []},
            "PCNSL": {"chemo": ["MTX","Ara-C"], "targeted": ["Rituximab"], "abx": []},
        },
        "림프종": {
            "DLBCL": {"chemo": ["Cyclophosphamide","Doxorubicin","Vincristine","Prednisone"], "targeted": ["Rituximab","Polatuzumab Vedotin"], "abx": []},
            "B거대세포종": {"chemo": ["Cyclophosphamide","Doxorubicin","Vincristine","Prednisone"], "targeted": ["Rituximab"], "abx": []},
            "PMBCL": {"chemo": ["Cyclophosphamide","Doxorubicin","Vincristine","Prednisone"], "targeted": ["Rituximab","Pembrolizumab"], "abx": []},
            "HGBL": {"chemo": ["Etoposide","Doxorubicin","Cyclophosphamide","Vincristine","Prednisone"], "targeted": ["Rituximab"], "abx": []},
            "BL": {"chemo": ["Cyclophosphamide","Doxorubicin","Vincristine","MTX","Ara-C"], "targeted": ["Rituximab"], "abx": []},
            "FL": {"chemo": ["Cyclophosphamide","Doxorubicin","Vincristine","Prednisone","Bendamustine"], "targeted": ["Rituximab","Obinutuzumab"], "abx": []},
            "MZL": {"chemo": ["Bendamustine","Chlorambucil"], "targeted": ["Rituximab"], "abx": []},
            "MALT lymphoma": {"chemo": ["Chlorambucil"], "targeted": ["Rituximab"], "abx": []},
            "MCL": {"chemo": ["Cyclophosphamide","Doxorubicin","Vincristine","Prednisone","Bendamustine"], "targeted": ["Rituximab","Ibrutinib"], "abx": []},
            "cHL": {"chemo": ["Doxorubicin","Bleomycin","Vinblastine","Dacarbazine"], "targeted": ["Brentuximab Vedotin","Nivolumab","Pembrolizumab"], "abx": []},
            "NLPHL": {"chemo": ["Cyclophosphamide","Doxorubicin","Vincristine","Prednisone"], "targeted": ["Rituximab"], "abx": []},
            "PTCL-NOS": {"chemo": ["Cyclophosphamide","Doxorubicin","Vincristine","Prednisone"], "targeted": [], "abx": []},
            "AITL": {"chemo": ["Cyclophosphamide","Doxorubicin","Vincristine","Prednisone"], "targeted": [], "abx": []},
            "ALCL (ALK+)": {"chemo": ["Cyclophosphamide","Doxorubicin","Vincristine","Prednisone"], "targeted": ["Brentuximab Vedotin"], "abx": []},
            "ALCL (ALK−)": {"chemo": ["Cyclophosphamide","Doxorubicin","Vincristine","Prednisone"], "targeted": ["Brentuximab Vedotin"], "abx": []},
        },
        "고형암": {
            "폐선암": {"chemo": ["Cisplatin","Pemetrexed"], "targeted": ["Osimertinib","Alectinib","Crizotinib","Larotrectinib","Entrectinib","Capmatinib","Sotorasib","Lorlatinib"], "abx": []},
            "유방암": {"chemo": ["Doxorubicin","Cyclophosphamide","Paclitaxel"], "targeted": ["Trastuzumab","Pertuzumab","T-DM1","Trastuzumab deruxtecan","Lapatinib","Tucatinib"], "abx": []},
            "대장암": {"chemo": ["Oxaliplatin","5-FU","Irinotecan","Capecitabine"], "targeted": ["Bevacizumab","Cetuximab","Panitumumab","Regorafenib"], "abx": []},
            "위암": {"chemo": ["Cisplatin","5-FU","Capecitabine"], "targeted": ["Trastuzumab","Ramucirumab"], "abx": []},
            "간세포암": {"chemo": [], "targeted": ["Sorafenib","Lenvatinib","Atezolizumab","Bevacizumab","Durvalumab"], "abx": []},
            "췌장암": {"chemo": ["Oxaliplatin","Irinotecan","5-FU","Gemcitabine","Nab-Paclitaxel"], "targeted": [], "abx": []},
            "난소암": {"chemo": ["Carboplatin","Paclitaxel","Topotecan"], "targeted": ["Bevacizumab","Olaparib","Niraparib"], "abx": []},
            "자궁경부암": {"chemo": ["Cisplatin"], "targeted": ["Bevacizumab"], "abx": []},
            "방광암": {"chemo": ["Gemcitabine","Cisplatin"], "targeted": ["Pembrolizumab","Nivolumab","Atezolizumab"], "abx": []},
            "식도암": {"chemo": ["Cisplatin","5-FU"], "targeted": [], "abx": []},
            "GIST": {"chemo": [], "targeted": ["Imatinib","Sunitinib","Regorafenib","Ripretinib"], "abx": []},
            "NET": {"chemo": [], "targeted": ["Everolimus","Octreotide"], "abx": []},
            "MTC": {"chemo": [], "targeted": ["Vandetanib","Cabozantinib","Selpercatinib","Pralsetinib"], "abx": []},
        },
        "육종": {
            "Osteosarcoma": {"chemo": ["MTX","Doxorubicin","Cisplatin"], "targeted": [], "abx": []},
            "Ewing sarcoma": {"chemo": ["Vincristine","Doxorubicin","Cyclophosphamide","Ifosfamide","Etoposide"], "targeted": [], "abx": []},
            "Rhabdomyosarcoma": {"chemo": ["Vincristine","Dactinomycin","Cyclophosphamide"], "targeted": [], "abx": []},
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
            "MTC": {"chemo": [], "targeted": ["Vandetanib","Cabozantinib","Selpercatinib","Pralsetinib"], "abx": []},
        },
    }

def auto_recs_by_dx(group: str, dx: str, DRUG_DB: Dict[str, Dict[str, Any]] = None,
                    ONCO_MAP: Dict[str, Dict[str, Dict[str, List[str]]]] = None) -> Dict[str, List[str]]:
    """Return drug lists for the selected diagnosis with safe canonicalization."""
    out = {"chemo": [], "targeted": [], "abx": []}
    omap = ONCO_MAP or build_onco_map()
    gmap = omap.get(group or "", {})
    dmap = gmap.get(dx or "", {})
    for k in out.keys():
        picks = [ _canon(p) for p in dmap.get(k, []) ]
        if DRUG_DB:
            # include if key exists OR lower() exists OR alias exists
            filtered = []
            for p in picks:
                if p in DRUG_DB or p.lower() in DRUG_DB:
                    filtered.append(p)
                    continue
                # alias check
                for kk, vv in DRUG_DB.items():
                    if isinstance(vv, dict) and vv.get("alias") == p:
                        filtered.append(kk)
                        break
            out[k] = filtered or picks
        else:
            out[k] = picks
    return out


# === AML 유지항암(6-MP/MTX) 보강: build_onco_map 래핑 ===
try:
    __orig_build_onco_map = build_onco_map
except NameError:
    __orig_build_onco_map = None

def build_onco_map():
    M = __orig_build_onco_map() if __orig_build_onco_map else {}
    try:
        heme = M.get("혈액암", {})
        aml = heme.get("AML", {})
        # maintenance ensure
        maint = list(aml.get("maintenance") or [])
        for x in ["6-MP", "MTX"]:
            if x not in maint:
                maint.append(x)
        aml["maintenance"] = maint
        # chemo에도 fallback로 추가(중복 방지)
        chemo = list(aml.get("chemo") or [])
        for x in ["6-MP", "MTX"]:
            if x not in chemo:
                chemo.append(x)
        aml["chemo"] = chemo
        heme["AML"] = aml
        M["혈액암"] = heme
    except Exception:
        pass
    return M

