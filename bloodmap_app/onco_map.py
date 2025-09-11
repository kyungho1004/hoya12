# -*- coding: utf-8 -*-
from typing import Dict, List, Any

def _is_korean(s: str) -> bool:
    return any('\uac00' <= ch <= '\ud7a3' for ch in (s or ""))

def _norm(s: str) -> str:
    if not s:
        return ""
    s2 = (s or "").strip()
    # unify spaces and case for well-known codes
    code = s2.upper().replace(" ", "")
    # Common uppercase codes
    CODE_ALIASES = {
        "DLBCL": "DLBCL",
        "PMBCL": "PMBCL",
        "HGBL": "HGBL",
        "BL": "BL",
        "APL": "APL",
        "AML": "AML",
        "ALL": "ALL",
        "CML": "CML",
        "CLL": "CLL",
        "PCNSL": "PCNSL",
    }
    if code in CODE_ALIASES:
        return CODE_ALIASES[code]
    # If already in dict under original string keep it
    return s2

# Korean labels dictionary (both English codes and Korean synonyms are keys)
DX_KO: Dict[str, str] = {
    # Hematologic malignancies
    "APL": "급성 전골수구성 백혈병",
    "AML": "급성 골수성 백혈병",
    "ALL": "급성 림프구성 백혈병",
    "CML": "만성 골수성 백혈병",
    "CLL": "만성 림프구성 백혈병",
    "PCNSL": "원발성 중추신경계 림프종",

    # Lymphomas (B/T/NK)
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

    # Sarcomas
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

    # Solid + Rare (kept concise)
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

def dx_display(group: str, dx: str) -> str:
    dx = (dx or "").strip()
    key = _norm(dx)
    ko = DX_KO.get(key) or DX_KO.get(dx)
    # If dx already contains Korean characters, don't duplicate
    if _is_korean(dx):
        return f"{group} - {dx}"
    if ko:
        return f"{group} - {dx} ({ko})"
    # If not found, return as-is
    return f"{group} - {dx}"

def build_onco_map() -> Dict[str, Dict[str, Dict[str, List[str]]]]:
    # Minimal stub; your full map can be placed here. The app only needs dx_display for KO labels.
    return {}
