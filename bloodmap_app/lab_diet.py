# -*- coding: utf-8 -*-
"""
lab_diet.py — 피수치 기반 식이가이드
- ANC 단계별 가이드 포함 (<500 / 500–1000 / ≥1000)
- 기본 영양 가이드(알부민/칼륨/헤모글로빈/나트륨/칼슘)
※ 영양제(철분제 등)는 추천하지 않음. 음식 위주로만 제시.
"""
from __future__ import annotations
from typing import Dict, List, Optional

def _num(x):
    try:
        if x is None: return None
        if isinstance(x, (int, float)): return float(x)
        s = str(x).replace(",", "").strip()
        s2 = "".join(ch for ch in s if (ch.isdigit() or ch == "." or ch == "-"))
        return float(s2) if s2 else None
    except Exception:
        return None

def _append(lst: List[str], text: str):
    if text and text not in lst:
        lst.append(text)

def _anc_bucket(anc: Optional[float]) -> Optional[str]:
    if anc is None:
        return None
    try:
        a = float(anc)
    except Exception:
        return None
    if a < 500: return "<500"
    if a < 1000: return "500-1000"
    return ">=1000"

def _anc_diet_lines(anc: Optional[float]) -> List[str]:
    band = _anc_bucket(anc)
    lines: List[str] = []
    if not band:
        return lines
    if band == "<500":
        _append(lines, "🚨 ANC < 500: **생채소 금지**·익힌 음식 **또는 전자레인지 30초 이상** 조리")
        _append(lines, "🚨 **멸균/살균 식품** 권장(우유·음료 등은 멸균 제품 우선)")
        _append(lines, "🚨 조리 후 **2시간 지난 음식은 권장하지 않습니다**(남김 보관 지양)")
        _append(lines, "🚨 외식·뷔페·날음식(회/반숙/생계란) **금지**")
        _append(lines, "🚨 **껍질 있는 과일**은 주치의와 상의 후 섭취 여부 결정(필요 시 **깨끗이 세척 후 껍질 제거**)")
    elif band == "500-1000":
        _append(lines, "🟧 ANC 500–1000: 날음식/덜 익힌 음식 피하고 **충분히 가열**")
        _append(lines, "🟧 샐러드/생채소는 **가급적 피함**, 섭취 시 깨끗이 세척 후 **데치기** 권장")
        _append(lines, "🟧 조리 후 **2시간** 넘긴 음식은 피하기")
        _append(lines, "🟧 손 씻기·조리도구 분리(도마/칼) 등 **위생 수칙 강화**")
    else:  # ">=1000"
        _append(lines, "🟢 ANC ≥ 1000: 일반 위생 수칙 하에 **일반 식사 가능**")
        _append(lines, "🟢 날음식은 여전히 **주의**(신선도/위생 불확실 시 피함)")
    return lines

# 기본 영양 가이드(요청 목록 고정)
FOOD_GUIDES = {
    "Alb_low": ["달걀", "연두부", "흰살 생선", "닭가슴살", "귀리죽"],
    "K_low":   ["바나나", "감자", "호박죽", "고구마", "오렌지"],
    "Hb_low":  ["소고기", "시금치", "두부", "달걀 노른자", "렌틸콩"],
    "Na_low":  ["전해질 음료", "미역국", "바나나", "오트밀죽", "삶은 감자"],
    "Ca_low":  ["연어통조림", "두부", "케일", "브로콜리", "참깨 제외"],
}

def _food_line(title: str, foods: List[str]) -> str:
    return f"{title}: " + ", ".join(foods[:5])

def lab_diet_guides(labs: Dict[str, float], heme_flag: bool = False) -> List[str]:
    """
    입력된 주요 수치(labs)에 따라 식이가이드를 생성합니다.
    labs: {'ANC':…, 'Alb':…, 'K':…, 'Hb':…, 'Na':…, 'Ca':…} 등
    """
    lines: List[str] = []
    anc = _num((labs or {}).get("ANC"))
    alb = _num((labs or {}).get("Alb"))
    k   = _num((labs or {}).get("K"))
    hb  = _num((labs or {}).get("Hb"))
    na  = _num((labs or {}).get("Na"))
    ca  = _num((labs or {}).get("Ca"))

    # 1) ANC 가이드
    lines.extend(_anc_diet_lines(anc))

    # 2) 기본 식품 추천(수치 낮음 위주)
    if alb is not None and alb < 3.5:
        _append(lines, "Alb 낮음 — 단백질 보충 권장")
        _append(lines, _food_line("추천 음식(Alb 낮음)", FOOD_GUIDES["Alb_low"]))
    if k is not None and k < 3.5:
        _append(lines, _food_line("추천 음식(칼륨 낮음)", FOOD_GUIDES["K_low"]))
    if hb is not None and hb < 10.0:
        _append(lines, _food_line("추천 음식(Hb 낮음)", FOOD_GUIDES["Hb_low"]))
        _append(lines, "⚠️ 철분제는 **권장하지 않음**(항암 치료 중/백혈병 환자). 복용 전 반드시 주치의와 상담.")
        _append(lines, "ℹ️ 철분제 + 비타민C는 흡수를 촉진하나, **복용 여부는 주치의와 결정**하십시오.")
    if na is not None and na < 135:
        _append(lines, _food_line("추천 음식(나트륨 낮음)", FOOD_GUIDES["Na_low"]))
    if ca is not None and ca < 8.5:
        _append(lines, _food_line("추천 음식(칼슘 낮음)", FOOD_GUIDES["Ca_low"]))

    # 3) 공통 위생/안전
    _append(lines, "조리/섭취 전후 **손 씻기**, 생/익은 음식 도마 분리, 충분한 **가열/데치기**")
    return lines
