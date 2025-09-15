# -*- coding: utf-8 -*-
from typing import Dict, List

def get_adult_options():
    return {
        "콧물": ["없음","투명","흰색","노랑(초록)","누런","피 섞임"],
        "기침": ["없음","가끔","자주","심함"],
        "설사": ["없음","1~3회","4~6회","7회 이상"],
        "발열": ["없음","37.5~38","38~38.5","38.5~39","39+"],
        "눈꼽": ["없음","맑음","노랑-농성","가려움 동반","한쪽","양쪽"],
    }

def _score(ok: bool, w: float) -> float:
    return w if ok else 0.0

def predict_from_symptoms(sym: Dict[str,str], temp_c: float, comorb: List[str]) -> List[Dict]:
    nasal = (sym.get("콧물") or "").strip()
    cough = (sym.get("기침") or "").strip()
    diarrhea = (sym.get("설사") or "").strip()
    eye = (sym.get("눈꼽") or "").strip()

    high = (temp_c or 0) >= 38.5
    very_high = (temp_c or 0) >= 39.0

    cand = {
        "감기/상기도바이러스": 0.0,
        "독감(인플루엔자) 의심": 0.0,
        "장염(바이러스) 의심": 0.0,
        "세균성 편도/부비동염 가능": 0.0,
        "세균성 결막염 가능": 0.0,
        "아데노바이러스 결막염 가능": 0.0,
        "알레르기성 결막염 가능": 0.0,
    }
    reasons = {k: [] for k in cand}

    # 상기도바이러스
    s = 0.0
    s += _score(nasal not in ["없음",""], 20)
    s += _score(cough in ["가끔","자주","심함"], 15)
    s += _score(not high, 5)
    if s: reasons["감기/상기도바이러스"].append("콧물/기침 + 발열 낮음")
    cand["감기/상기도바이러스"] += s

    # 독감
    s = 0.0
    s += _score(very_high, 35)
    s += _score(cough in ["자주","심함"], 15)
    if s: reasons["독감(인플루엔자) 의심"].append("고열 + 기침 중심")
    cand["독감(인플루엔자) 의심"] += s

    # 장염(바이러스)
    s = 0.0
    s += _score(diarrhea in ["4~6회","7회 이상"], 35)
    s += _score(cough in ["없음","가끔"], 5)
    s += _score(nasal in ["없음","투명",""], 5)
    if s: reasons["장염(바이러스) 의심"].append("설사 다회 + 상기도 소견 적음")
    cand["장염(바이러스) 의심"] += s

    # 세균성 편도/부비동염
    s = 0.0
    s += _score(nasal in ["누런","노랑(초록)","피 섞임"], 20)
    s += _score(high, 10)
    s += _score(cough in ["없음","가끔"], 5)
    if s: reasons["세균성 편도/부비동염 가능"].append("탁한/혈성 콧물 + 발열")
    cand["세균성 편도/부비동염 가능"] += s

    # 세균성 결막염
    s = 0.0
    s += _score("노랑" in eye or "농성" in eye, 20)
    s += _score("한쪽" in eye, 15)
    s += _score("양쪽" in eye, 10)
    s -= _score("맑음" in eye, 10)
    if s: reasons["세균성 결막염 가능"].append("농성 눈꼽 + 한쪽 시작 경향")
    cand["세균성 결막염 가능"] += s

    # 아데노바이러스 결막염
    s = 0.0
    s += _score(high, 10)
    s += _score(nasal not in ["없음",""], 5)
    s += _score("양쪽" in eye, 10)
    s -= _score("노랑" in eye or "농성" in eye, 5)
    if s: reasons["아데노바이러스 결막염 가능"].append("발열/상기도 동반 + 양측")
    cand["아데노바이러스 결막염 가능"] += s

    # 알레르기성 결막염
    s = 0.0
    s += _score("맑음" in eye, 10)
    s += _score("가려움" in eye, 15)
    s += _score(nasal in ["투명","없음"], 5)
    if s: reasons["알레르기성 결막염 가능"].append("맑은 분비물 + 가려움")
    cand["알레르기성 결막염 가능"] += s

    items = []
    for k, v in cand.items():
        items.append({"label": k, "score": round(max(0.0, min(100.0, v)), 1), "reasons": reasons[k]})
    items.sort(key=lambda x: x["score"], reverse=True)
    return items[:3]

def adult_high_risk(comorb: List[str]) -> bool:
    return any(x in comorb for x in ["임신 가능성","간질환 병력","신질환 병력","위장관 궤양/출혈력","항응고제 복용","고령(65+)"])

def triage_advise(temp_c: float, comorb: List[str]) -> str:
    if temp_c >= 39.0:
        return "🟥 39.0℃ 이상 → 즉시 병원 연락/내원 권고"
    if adult_high_risk(comorb) and temp_c >= 38.0:
        return "🟧 기저질환/임신 가능성 + 발열 → 오늘 중 외래/선별진료 고려"
    if 38.5 <= temp_c < 39.0:
        return "🟧 38.5~39.0℃ → 해열제 복용 + 외래 상담 고려"
    return "🟩 37.5~38.5℃ 또는 저열 → 수분/휴식, 자가 경과관찰"
