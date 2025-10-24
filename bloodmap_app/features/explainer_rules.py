"""
Keyword explainer rules (structured). This module is optional.
If ui_results already renders keyword chips, that behavior remains the default.
These rules allow local rendering when desired.
"""
from __future__ import annotations
from typing import List, Dict, Any

# Minimal, high-yield examples (expand as needed)
# Each rule has patterns (regex) and an HTML chip (pre-styled via ensure_keyword_explainer_style).
RULES: List[Dict[str, Any]] = [
    # QT prolongation (exact QT / QTc; avoid matching arbitrary 'Qt' code)
    {
        "name": "QT 연장",
        "patterns": [r"\bQTc?\b", r"QTc\s*(?:≥|>=|>\s*)?\s*500"],
        "html": "<span class='explain-chip'>QT 연장: 실신·돌연사 위험 ↑ → ECG 추적</span>",
    },
    # Hand-foot syndrome (띄어쓰기/연결어 변형 포함)
    {
        "name": "손발증후군",
        "patterns": [r"손\s*발\s*증\s*후\s*군", r"hand[- ]?foot"],
        "html": "<span class='explain-chip'>손발증후군: 손발 붉어짐·벗겨짐 → 보습·마찰 줄이기</span>",
    },
    # RA syndrome / differentiation syndrome (for APL context, generic wording)
    {
        "name": "RA 증후군",
        "patterns": [r"RA\s*증\s*후\s*군", r"differentiation\s+syndrome"],
        "html": "<span class='explain-chip'>RA 증후군: 호흡곤란·부종 → 스테로이드 고려, 즉시 연락</span>",
    },
    # ILD / pneumonitis
    {
        "name": "ILD",
        "patterns": [r"\bILD\b", r"폐[ ]?렴\b", r"pneumonitis"],
        "html": "<span class='explain-chip'>ILD: 호흡곤란/기침·저산소 → CT·스테로이드 고려</span>",
    },
    # TLS
    {
        "name": "TLS",
        "patterns": [r"\bTLS\b", r"tumor\s+lysis"],
        "html": "<span class='explain-chip'>TLS: 수분·전해질·요산관리 → 즉시 연락</span>",
    },
    # FN
    {
        "name": "호중구감소성 발열",
        "patterns": [r"발열\s*·?\s*호중구\s*감소|\bFN\b|febrile\s+neutropenia"],
        "html": "<span class='explain-chip'>호중구감소성 발열: 응급 · 즉시 연락</span>",
    },
    # LFT elevation
    {
        "name": "간효소 상승",
        "patterns": [r"AST|ALT|간[ ]?효소\s*상승|transaminase\s+elev"],
        "html": "<span class='explain-chip'>간효소 상승: 약중단/감량·추적 검사</span>",
    },
    # Proteinuria
    {
        "name": "단백뇨",
        "patterns": [r"단백뇨|proteinuria"],
        "html": "<span class='explain-chip'>단백뇨: 소변·신기능 추적, 용량조절 고려</span>",
    },
    # Stomatitis
    {
        "name": "구내염",
        "patterns": [r"구내염|stomatitis|mucositis"],
        "html": "<span class='explain-chip'>구내염: 자극 피하고 가글·통증조절</span>",
    },
    # Thrombosis/embolism
    {
        "name": "혈전·색전",
        "patterns": [r"혈전|색전|thrombo|embol"],
        "html": "<span class='explain-chip'>혈전·색전: 흉통/호흡곤란 즉시 연락</span>",
    },
    # Nephrotoxicity
    {
        "name": "신독성",
        "patterns": [r"신독성|nephrotox"],
        "html": "<span class='explain-chip'>신독성: 수분·Cr 추적, 용량조절</span>",
    },
    # Diarrhea / dehydration
    {
        "name": "설사·탈수",
        "patterns": [r"설사|diarrhea|탈수|dehydrat"],
        "html": "<span class='explain-chip'>설사·탈수: ORS/수분, 중증 시 연락</span>",
    },
    # Cardiotoxicity
    {
        "name": "심근독성",
        "patterns": [r"심근[ ]?독성|cardiotox|EF\s*↓|LVEF"],
        "html": "<span class='explain-chip'>심근독성: 흉통/호흡곤란·심계항진 → 즉시 연락</span>",
    },
    # Myelosuppression
    {
        "name": "골수억제",
        "patterns": [r"골수\s*억제|myelosupp"],
        "html": "<span class='explain-chip'>골수억제: CBC 추적·감염 주의</span>",
    },
]
