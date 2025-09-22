# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import List, Dict, Optional, Tuple
from safety import urgent_banners, symptom_emergencies
from drug_db import display_label

def build_report_blocks(ctx: dict, care_24h: List[dict], care_2h: List[dict], ae_by_keys: List[str]) -> List[Tuple[str, List[str]]]:
    blocks: List[Tuple[str, List[str]]] = []

    # 🆘 증상 기반 응급도(피수치 없이)
    emerg = symptom_emergencies(care_2h, care_24h)
    lines = []
    lines += emerg
    lines += ["일반 응급실 기준(항상 노출): 혈변/검은변, 초록 구토, 의식저하/경련/호흡곤란, 6h 무뇨·중증 탈수, 고열 지속, 심한 복통/팽만/무기력"]
    blocks.append(("🆘 증상 기반 응급도(피수치 없이)", lines))

    # 🗒️ 케어로그(최근 24시간): 요약 카운트
    fever_n = sum(1 for e in care_24h if e.get("type")=="fever")
    vom_n   = sum(1 for e in care_24h if e.get("type")=="vomit")
    dia_n   = sum(1 for e in care_24h if e.get("type")=="diarrhea")
    apap_n  = sum(1 for e in care_24h if e.get("type")=="apap")
    ibu_n   = sum(1 for e in care_24h if e.get("type")=="ibu")
    lines = [f"발열 {fever_n}회 · 구토 {vom_n}회 · 설사 {dia_n}회 · APAP {apap_n}회 · IBU {ibu_n}회"]
    blocks.append(("🗒️ 케어로그(최근 24h)", lines))

    # 💊 선택 약물 부작용: 중요 요약 → 상세
    if ae_by_keys:
        top = []
        for k in ae_by_keys:
            lbl = display_label(k)
            top.append(f"{lbl}")
        lines = ["중요 경고 요약(상세는 앱 본문 참고): " + ", ".join(top)]
        blocks.append(("💊 선택 약물 부작용", lines))

    return blocks
