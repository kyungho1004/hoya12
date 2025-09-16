# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import List, Tuple, Dict

def _in_text(text: str, words: List[str]) -> bool:
    s = (text or "").lower()
    return any(w.lower() in s for w in words)

def compute_interactions(
    drug_keys: List[str],
    labs: Dict[str, float] | None = None,
    other_meds_text: str | None = None,
) -> List[Tuple[str, str]]:
    """
    선택 약물 조합의 **상호작용/금기** 규칙을 간단히 검사합니다.
    반환: (등급, 메시지) 튜플 리스트. 등급은 "🚨 심각" 또는 "⚠️ 주의".

    룰(예시):
    - 6-MP × allopurinol (XO 억제)
    - MTX × NSAIDs (+신기능)
    - linezolid × SSRI (세로토닌증후군)
    - ATO × QT연장/저K·저Mg
    - Levofloxacin 단독 QT 주의(보조)
    """
    labs = labs or {}
    other = (other_meds_text or "").lower()
    picks = [ (k or "").strip().strip("'\"") for k in (drug_keys or []) ]
    picks_l = [p.lower() for p in picks]

    def has(keys: List[str]) -> bool:
        return any(k.lower() in picks_l for k in keys)

    alerts: List[Tuple[str, str]] = []

    # 6-MP × allopurinol
    if has(["6-MP", "Mercaptopurine"]) and _in_text(other, ["allopurinol", "알로푸리놀"]):
        alerts.append(("🚨 심각", "6‑MP + 알로푸리놀 → XO 억제에 의한 6‑MP 대사 저하/독성 ↑. 6‑MP 용량 대폭 감량 필요(의사 지시)."))

    # MTX × NSAIDs (+ 신기능)
    if has(["MTX", "Methotrexate"]):
        nsaid_hits = _in_text(other, ["NSAID","이부프로펜","ibuprofen","naproxen","diclofenac","indomethacin","ketorolac"])
        renal_worse = False
        try:
            cr = float(labs.get("Cr") or labs.get("Cr,크레아티닌") or 0)
            bun = float(labs.get("BUN") or 0)
            renal_worse = (cr and cr > 1.2) or (bun and bun > 20)
        except Exception:
            pass
        if nsaid_hits and renal_worse:
            alerts.append(("🚨 심각", "메토트렉세이트 + NSAIDs + 신기능 저하 → MTX 배설 지연/독성 ↑. 병용 회피/용량/모니터링 의사 지시 필요."))
        elif nsaid_hits:
            alerts.append(("⚠️ 주의", "메토트렉세이트 + NSAIDs → MTX 배설 감소 가능. 탈수/고용량/신기능 저하 시 위험 ↑."))

    # Linezolid × SSRI
    if has(["Linezolid"]):
        if _in_text(other, ["SSRI","fluoxetine","sertraline","paroxetine","citalopram","escitalopram","플루옥세틴","설트랄린","파록세틴","시탈로프람","에스시탈로프람"]):
            alerts.append(("🚨 심각", "리네졸리드 + SSRI/SNRI 등 → 세로토닌 증후군 위험. 대체/중단 및 모니터링 의사 지시."))

    # ATO × QT/전해질
    if has(["Arsenic Trioxide","ATO"]):
        low_k = False
        low_mg = False
        try:
            k = float(labs.get("K") or 0)
            if k and k < 3.5: low_k = True
        except Exception:
            pass
        if _in_text(other, ["저마그네슘","hypomagnesemia","low magnesium","Mg <"]):
            low_mg = True
        qt_drugs = ["levofloxacin","moxifloxacin","ciprofloxacin","ondansetron","haloperidol","citalopram","amiodarone","sotalol","퀴놀론","레보플록사신"]
        if low_k or low_mg or _in_text(other, qt_drugs) or _in_text(" ".join(picks_l), qt_drugs) or has(["Levofloxacin"]):
            alerts.append(("🚨 심각", "산화비소(ATO) + QT 연장 위험요인(저K/저Mg/퀴놀론계 등) → TdP 위험. ECG/전해질 교정 및 위험 약물 병용 피하기."))
        else:
            alerts.append(("⚠️ 주의", "산화비소(ATO) → QT 연장 가능. K/Mg 정상 유지 및 ECG 모니터링 권장."))

    # Levofloxacin 보조 경고
    if has(["Levofloxacin"]):
        alerts.append(("⚠️ 주의", "레보플록사신 → QT 연장 가능. 기존 QT 연장 약물/저K/저Mg와 병용 주의."))

    # Deduplicate
    seen = set()
    out: List[Tuple[str, str]] = []
    for level, msg in alerts:
        if msg not in seen:
            out.append((level, msg))
            seen.add(msg)
    return out
