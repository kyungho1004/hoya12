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
    "APL": "급성 전골수성 백혈병",
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


# Display 'code - 한글병기' without '암' and with compact spacing
# --- KOR DX DISPLAY (robust) ---
def _dx_norm_key(s: str) -> str:
    # normalize: lowercase, remove spaces, hyphens, slashes, plus/minus, and parentheses
    if not s:
        return ""
    t = str(s).lower()
    # drop parenthetical contents
    import re
    t = re.sub(r"\([^\)]*\)", "", t)
    # remove non-alnum (keep letters/numbers only)
    t = re.sub(r"[^a-z0-9]", "", t)
    return t

_DX_ALIAS = {
    # lymphoma common variants
    "dlbcl":"dlbcl",
    "diffuselargebcelllymphoma":"dlbcl",
    "aitl":"aitl",
    "angioimmunoblastictcelllymphoma":"aitl",
    "alcl":"alcl",
    "alclalk":"alcl",
    "alclalkplus":"alcl",
    "alclalkminus":"alcl",
    "fl":"fl",
    "follicularlymphoma":"fl",
    "hchl":"hchl", "hl":"hchl", "hodgkinlymphoma":"hchl",
    # leukemia examples
    "apl":"apl", "amlm3":"apl", "acutepromyelocyticleukemia":"apl",
    # add more as needed
}

def dx_display_kor(dx: str) -> str:
    key_upper = _norm(dx).upper() if '_norm' in globals() else str(dx).upper()
    # KO lookup: try exact map first
    ko = DX_KO.get(key_upper)
    if not ko:
        # try alias route using robust normalization
        k = _dx_norm_key(dx)
        alias = _DX_ALIAS.get(k)
        if alias:
            ko = DX_KO.get(alias.upper())
    if not ko:
        # fallback to original text as ko (but compacted)
        ko = str(dx)
    ko2 = str(ko).replace(" ", "")
    if ko2.endswith("암"):
        ko2 = ko2[:-1]
    return f"{key_upper.lower()} - {ko2}"
# --- /KOR DX DISPLAY ---

def dx_display_kor(dx: str) -> str:
    key = _norm(dx).upper()
    ko = DX_KO.get(key) or DX_KO.get(dx) or dx
    ko2 = (ko or "").replace(" ", "")
    # remove a trailing '암' if present (유방암 -> 유방, 간암 -> 간 등)
    if ko2.endswith("암"):
        ko2 = ko2[:-1]
    return f"{key.lower()} - {ko2}"

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




# === [PATCH 2025-10-25 KST] Enrich heme/lymphoma maps with new agents ===
def _extend_onco_map_20251025(m: Dict[str, Dict[str, Dict[str, list]]]) -> Dict[str, Dict[str, Dict[str, list]]]:
    def add(group, dx, kind, items):
        if group not in m:
            m[group] = {}
        if dx not in m[group]:
            m[group][dx] = {"chemo": [], "targeted": [], "abx": []}
        cur = m[group][dx].setdefault(kind, [])
        for it in items:
            if it not in cur:
                cur.append(it)

    # AML
    add("혈액암", "AML", "chemo", ["Vyxeos"])
    add("혈액암", "AML", "targeted", ["Venetoclax","Gilteritinib","Midostaurin","Ivosidenib","Enasidenib","Glasdegib"])

    # APL already mapped via ATRA/ATO in drug_db

    # CLL
    add("혈액암", "CLL", "targeted", ["Acalabrutinib","Zanubrutinib","Venetoclax","Obinutuzumab"])

    # MCL
    add("림프종", "MCL", "targeted", ["Acalabrutinib","Zanubrutinib","Lenalidomide"])

    # FL / DLBCL
    add("림프종", "FL", "targeted", ["Mosunetuzumab"])
    add("림프종", "DLBCL", "targeted", ["Tafasitamab","Epcoritamab","Glofitamab","Lenalidomide"])

    # Optionally add Myeloma (다발골수종) minimal map (no cell therapy)
    add("혈액암", "다발골수종", "chemo", ["Cyclophosphamide"])
    add("혈액암", "다발골수종", "targeted", ["Lenalidomide","Teclistamab","Selinexor"])

    return m

try:
    _prev_build = build_onco_map  # from existing module
    def build_onco_map():
        m = _prev_build() or {}
        return _extend_onco_map_20251025(m)
except Exception:
    pass
# === [/PATCH] ===



# === [PATCH 2025-10-25 KST] Solid tumor mapping + simple guidance notes ===
def _extend_onco_map_solid_20251025(m: Dict[str, Dict[str, Dict[str, list]]]) -> Dict[str, Dict[str, Dict[str, list]]]:
    def add(group, dx, kind, items):
        if group not in m: m[group] = {}
        if dx not in m[group]: m[group][dx] = {"chemo": [], "targeted": [], "abx": []}
        cur = m[group][dx].setdefault(kind, [])
        for it in items:
            if it not in cur: cur.append(it)
        return m

    # NSCLC
    add("고형암","NSCLC(EGFR)", "targeted", ["Osimertinib","Amivantamab","Mobocertinib"])
    add("고형암","NSCLC(ALK)",  "targeted", ["Alectinib","Brigatinib","Lorlatinib","Crizotinib"])
    add("고형암","NSCLC(ROS1/NTRK)", "targeted", ["Entrectinib","Larotrectinib"])
    add("고형암","NSCLC(MET)",  "targeted", ["Capmatinib","Tepotinib"])
    add("고형암","NSCLC(KRAS G12C)", "targeted", ["Sotorasib","Adagrasib"])

    # Breast
    add("고형암","유방암(HR+)", "targeted", ["Palbociclib","Ribociclib","Abemaciclib"])
    add("고형암","유방암(HER2+)", "targeted", ["Trastuzumab deruxtecan","Trastuzumab emtansine","Pertuzumab","Tucatinib"])
    add("고형암","유방암(PARP 대상)", "targeted", ["Olaparib","Talazoparib" if "Talazoparib" in globals() else "Olaparib"])

    # CRC
    add("고형암","대장암(RAS WT)", "targeted", ["Cetuximab","Panitumumab"])
    add("고형암","대장암(BRAF V600E)", "targeted", ["Encorafenib","Cetuximab"])
    add("고형암","대장암(후속)", "targeted", ["Regorafenib","Trifluridine/Tipiracil"])

    # GIST
    add("고형암","GIST", "targeted", ["Imatinib","Sunitinib","Regorafenib-GIST","Ripretinib"])

    # BTC(담도) / Thyroid / Fusion
    add("고형암","담도암(FGFR2)", "targeted", ["Pemigatinib","Futibatinib"])
    add("고형암","담도암(IDH1)", "targeted", ["Ivosidenib-Solid"])
    add("고형암","갑상선암(RET)", "targeted", ["Selpercatinib","Pralsetinib"])
    add("고형암","융합양성(NTRK)", "targeted", ["Larotrectinib","Entrectinib"])

    # RCC / HCC
    add("고형암","신장암", "targeted", ["Lenvatinib","Cabozantinib","Axitinib"])
    add("고형암","간암",   "targeted", ["Sorafenib","Lenvatinib"])

    # Lymphoma / Myeloma enrich (non-cell therapy)
    add("림프종","DLBCL(추가)", "targeted", ["Polatuzumab vedotin","Brentuximab vedotin"])
    add("혈액암","다발골수종(비세포)", "targeted", ["Pomalidomide","Carfilzomib","Ixazomib","Daratumumab"])

    return m

# Simple notes per diagnosis (non-breaking; UI safely ignores if not used)
def _get_dx_notes_solid_20251025() -> Dict[str, str]:
    return {
        "AML": "Vyxeos(빅시오스)은 고위험/재발성 AML에서 사용. Venetoclax 병용 시 TLS 예방(수액+UA) 중요.",
        "CLL": "BTK 억제제(출혈/AF 주의) vs BCL-2(VEN, TLS 예방) 치료축. 동반질환·선호도에 따라 선택.",
        "MCL": "BTK 억제제(자누/아칼라) 중심. 감염/출혈 모니터.",
        "DLBCL": "재발/불응에서 이중특이항체·ADC 옵션 존재. CRS/주입반응 안내 필요.",
        "FL": "저증량요법/항CD20 기반. 이중특이 항체는 CRS 주의.",
        "다발골수종": "IMiD/PI/anti‑CD38 조합. 감염 예방·혈전예방 고려.",
        "NSCLC(EGFR)": "오시머티닙 1차 표준. ILD 증상(기침/호흡곤란) 시 즉시 평가.",
        "NSCLC(ALK)": "Alectinib 1차 표준 축. 후속으로 브리가/로라.",
        "NSCLC(MET)": "부종·간효소↑ 흔함. 신장기능·간기능 추적.",
        "유방암(HR+)": "CDK4/6 억제제+내분비요법 표준. 호중구감소·LFT/QT(리보) 주의.",
        "유방암(HER2+)": "T‑DXd는 ILD 드묾. 호흡증상 모니터.",
        "대장암(RAS WT)": "anti‑EGFR 사용 시 **RAS/BRAF/좌측** 등 분자·해부학적 요소 고려.",
        "GIST": "라인에 따라 IM→SU→REGO→RIPR 순. 손발증후군 관리 중요.",
        "담도암(FGFR2)": "고인산혈증 흔함 → 인산 식이 조절/치료.",
        "갑상선암(RET)": "혈압/간효소 모니터, 드묾한 QT.",
        "신장암": "VEGFR TKI 고혈압·단백뇨·손발증후군 모니터.",
        "간암": "VEGFR TKI 중심; 간기능 악화 시 용량조절.",
    }

# expose via safe getter
def get_dx_notes() -> Dict[str, str]:
    notes = {}
    try:
        if callable(_get_dx_notes_solid_20251025):
            notes.update(_get_dx_notes_solid_20251025())
    except Exception:
        pass
    try:
        return notes
    except Exception:
        return {}

# Hook build + notes
try:
    _prev_build2 = build_onco_map
    def build_onco_map():
        m = _prev_build2() or {}
        return _extend_onco_map_solid_20251025(m)
except Exception:
    pass
# === [/PATCH] ===



# === [PATCH 2025-10-25 KST] Map user-listed agents to diagnoses + notes ===
def _extend_onco_map_user_20251025(m: Dict[str, Dict[str, Dict[str, list]]]) -> Dict[str, Dict[str, Dict[str, list]]]:
    def add(group, dx, kind, items):
        if group not in m: m[group] = {}
        if dx not in m[group]: m[group][dx] = {"chemo": [], "targeted": [], "abx": []}
        cur = m[group][dx].setdefault(kind, [])
        for it in items:
            if it not in cur: cur.append(it)
        return m

    # Heme
    add("혈액암","MDS", "targeted", ["Azacitidine","Decitabine"])
    add("혈액암","AML", "targeted", ["Azacitidine","Decitabine","Gilteritinib","Venetoclax"])
    add("혈액암","CLL", "targeted", ["Venetoclax","Idelalisib","Zanubrutinib"])
    add("림프종","FL",  "targeted", ["Idelalisib","Lenalidomide"])
    add("혈액암","다발골수종", "targeted", ["Carfilzomib","Daratumumab","Belantamab mafodotin","Elotuzumab"])

    # Solid
    add("고형암","요로상피암", "targeted", ["Enfortumab vedotin"])
    add("고형암","삼중음성 유방암", "targeted", ["Sacituzumab govitecan"])
    add("고형암","GIST(PDGFRA D842V)", "targeted", ["Avapritinib"])
    add("고형암","유방암(HR+, PIK3CA)", "targeted", ["Alpelisib"])
    add("고형암","유방암(PARP)", "targeted", ["Talazoparib"])
    add("고형암","소세포폐암(골수보호)", "targeted", ["Trilaciclib"])

    return m

def _get_dx_notes_user_20251025() -> Dict[str, str]:
    return {
        "MDS": "저메틸화제(AZA/DEC) 표준 치료축. 골수억제·감염 모니터.",
        "AML": "재발/불응 FLT3 변이는 Gilteritinib 고려. VEN 병용 시 TLS 예방 필수.",
        "CLL": "BTKi vs BCL-2 vs PI3Kδ(출혈/AF vs TLS vs 간독성/대장염) 프로파일 고려.",
        "FL": "Idelalisib는 간독성/대장염/폐렴 등에 주의, Lenalidomide 병용 옵션.",
        "다발골수종": "anti-CD38/IMiD/PI/ADC 다양—감염·혈전·각막(벨란타맙) 모니터.",
        "요로상피암": "Enfortumab vedotin: 피부/신경병증·고혈당 모니터.",
        "삼중음성 유방암": "Sacituzumab govitecan: 호중구감소·설사 관리 중요.",
        "GIST(PDGFRA D842V)": "Avapritinib 특이 적합. 인지 변화 시 보고.",
        "유방암(HR+, PIK3CA)": "Alpelisib: **고혈당** 흔함—혈당 관리·피부발진 주의.",
        "유방암(PARP)": "Talazoparib: 빈혈·혈소판↓—CBC 모니터.",
        "소세포폐암(골수보호)": "Trilaciclib: 화학요법 전 투여하여 호중구감소 감소 목적.",
    }

# Wire up
try:
    _prev_build3 = build_onco_map
    def build_onco_map():
        m = _prev_build3() or {}
        return _extend_onco_map_user_20251025(m)
except Exception:
    pass

# Merge notes
try:
    _prev_get_notes = get_dx_notes  # may exist from prior patch
except Exception:
    _prev_get_notes = None

def get_dx_notes() -> Dict[str, str]:
    notes = {}
    if callable(_prev_get_notes):
        try:
            notes.update(_prev_get_notes())
        except Exception:
            pass
    try:
        notes.update(_get_dx_notes_user_20251025())
    except Exception:
        pass
    return notes
# === [/PATCH] ===
