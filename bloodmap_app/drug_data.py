# -*- coding: utf-8 -*-
def ko(name: str) -> str:
    # 간단 한글 병기 보조
    table = {
        "Imatinib": "이미티닙 (Imatinib)",
        "Sunitinib": "수니티닙 (Sunitinib)",
        "Regorafenib": "레고라페닙 (Regorafenib)",
        "Trastuzumab": "트라스투주맙 (Trastuzumab)",
        "Pertuzumab": "퍼투주맙 (Pertuzumab)",
        "Osimertinib": "오시머티닙 (Osimertinib)",
        "Alectinib": "알렉티닙 (Alectinib)",
    }
    return table.get(name, name)

solid_targeted = {
    "폐암(EGFR 변이)": ["Osimertinib"],
    "폐암(ALK 재배열)": ["Alectinib"],
    "유방암(HER2+)": ["Trastuzumab", "Pertuzumab"],
    "위장관기질종양(GIST)": ["Imatinib", "Sunitinib", "Regorafenib"],
}
