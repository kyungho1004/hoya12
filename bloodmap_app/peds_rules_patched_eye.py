
# -*- coding: utf-8 -*-
from typing import Dict, List

def _score(ok: bool, w: float) -> float:
    return w if ok else 0.0

def predict_from_symptoms(sym: Dict[str,str], temp_c: float, age_m: int|None=None) -> List[Dict]:
    nasal = (sym.get("콧물") or "").strip()
    cough = (sym.get("기침") or "").strip()
    diarrhea = (sym.get("설사") or "").strip()
    eye = (sym.get("눈꼽") or "").strip()
    fever = (sym.get("발열") or "").strip()
    age_m = age_m or 0

    very_high = (temp_c or 0) >= 39.0
    high = (temp_c or 0) >= 38.5
    mild = 37.5 <= (temp_c or 0) < 38.5

    cand = {
        "감기/상기도바이러스": 0.0,
        "독감(인플루엔자) 의심": 0.0,
        "장염(로타/노로 등) 의심": 0.0,
        "아데노/편도염 가능": 0.0,
        "중이염 가능(동반 의심)": 0.0,
        "세균성 결막염 가능": 0.0,
        "아데노바이러스 결막염 가능": 0.0,
        "알레르기성 결막염 가능": 0.0,
    }
    reasons: Dict[str, List[str]] = {k: [] for k in cand}

    # 기존 규칙
    s = 0.0
    s += _score(nasal in ["투명","흰색","노랑(초록)"], 20)
    s += _score(cough in ["가끔","자주"], 20)
    s += _score(mild, 10)
    s += _score(not very_high, 5)
    if s: reasons["감기/상기도바이러스"].append("콧물/기침 + 미열 위주")
    cand["감기/상기도바이러스"] += s

    s = 0.0
    s += _score(very_high, 35)
    s += _score(cough in ["자주","심함"], 25)
    s += _score(nasal in ["없음","투명","흰색"], 10)
    if s: reasons["독감(인플루엔자) 의심"].append("고열 + 기침 중심")
    cand["독감(인플루엔자) 의심"] += s

    s = 0.0
    s += _score(diarrhea in ["4~6회","7회 이상","5~6회","3~4회"], 35)
    s += _score(high or mild, 10)
    if s: reasons["장염(로타/노로 등) 의심"].append("설사 다회 + 발열/미열")
    cand["장염(로타/노로 등) 의심"] += s

    s = 0.0
    s += _score(high, 20)
    s += _score(nasal in ["누런","피 섞임"], 20)
    s += _score(cough in ["없음","가끔"], 10)
    if s: reasons["아데노/편도염 가능"].append("고열 + 끈적/혈성 콧물 또는 기침 적음")
    cand["아데노/편도염 가능"] += s

    s = 0.0
    s += _score(nasal in ["누런","피 섞임"], 20)
    s += _score(high, 10)
    s += _score(cough in ["없음","가끔"], 5)
    if s: reasons["중이염 가능(동반 의심)"].append("탁한 콧물 + 발열")
    cand["중이염 가능(동반 의심)"] += s

    # 신규: 결막염 관련
    # 세균성: 농성 + 한쪽 시작 가점, 양쪽 보조
    s = 0.0
    s += _score(eye == "노랑-농성", 35)
    s += _score(eye == "한쪽", 10)
    s += _score(eye == "양쪽", 5)
    s -= _score(eye == "맑음", 10)
    if s: reasons["세균성 결막염 가능"].append("농성 눈꼽 ± 한쪽 시작")
    cand["세균성 결막염 가능"] += max(0.0, s)

    # 아데노바이러스 결막염: 발열 + 상기도 + 양측
    s = 0.0
    s += _score(high or very_high, 10)
    s += _score(nasal not in ["없음",""], 10)
    s += _score(eye == "양쪽", 15)
    s -= _score(eye == "노랑-농성", 10)
    if s: reasons["아데노바이러스 결막염 가능"].append("발열 + 상기도 + 양측")
    cand["아데노바이러스 결막염 가능"] += max(0.0, s)

    # 알레르기성: 맑음 + 가려움 + 투명 콧물
    s = 0.0
    s += _score(eye == "맑음", 15)
    s += _score(eye == "가려움 동반", 20)
    s += _score(nasal in ["투명"], 10)
    if s: reasons["알레르기성 결막염 가능"].append("맑은 눈물/가려움 + 투명 콧물")
    cand["알레르기성 결막염 가능"] += s

    items: List[Dict] = []
    for k, v in cand.items():
        score = max(0.0, min(100.0, v))
        items.append({"label": k, "score": round(score, 1), "reasons": reasons[k]})
    items.sort(key=lambda x: x["score"], reverse=True)
    return items[:3]

def triage_advise(temp_c: float, age_m: int|None, diarrhea_opt: str) -> str:
    age_m = age_m or 0
    if age_m < 3 and temp_c >= 38.0:
        return "🟥 3개월 미만 + 발열 → 즉시 병원 권고"
    if temp_c >= 39.0:
        return "🟥 39.0℃ 이상 → 즉시 병원 연락/내원 권고"
    if diarrhea_opt in ["7회 이상"] and temp_c >= 38.5:
        return "🟧 다회 설사 + 고열 → 오늘 중 외래/선별진료 권고"
    if 38.5 <= temp_c < 39.0:
        return "🟧 38.5~39.0℃ → 해열제 투여 + 외래 상담 고려"
    return "🟩 37.5~38.5℃ 또는 저열 → 수분/휴식, 경과관찰(증가 시 연락)"
