
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

    very_high = (temp_c or 0) >= 39.0
    high = (temp_c or 0) >= 38.5
    mild = 37.5 <= (temp_c or 0) < 38.5

    cand = {
        "감기/상기도바이러스": 0.0,
        "독감(인플루엔자) 의심": 0.0,
        "코로나 가능": 0.0,
        "장염(바이러스) 의심": 0.0,
        "세균성 편도/부비동염 가능": 0.0,
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
    if s: reasons["감기/상기도바이러스"].append("콧물/기침 + 미열 위주")
    cand["감기/상기도바이러스"] += s

    s = 0.0
    s += _score(very_high, 35)
    s += _score(cough in ["자주","심함"], 25)
    if s: reasons["독감(인플루엔자) 의심"].append("고열 + 기침 중심")
    cand["독감(인플루엔자) 의심"] += s

    s = 0.0
    s += _score(high and cough in ["자주","심함"], 20)
    s += _score(nasal in ["없음","투명","흰색"], 10)
    if s: reasons["코로나 가능"].append("고열 + 기침, 콧물 적음")
    cand["코로나 가능"] += s

    s = 0.0
    s += _score(diarrhea in ["4~6회","7회 이상"], 35)
    s += _score(high, 10)
    if s: reasons["장염(바이러스) 의심"].append("설사 다회 + 발열 동반")
    cand["장염(바이러스) 의심"] += s

    s = 0.0
    s += _score(nasal in ["누런","피 섞임"], 20)
    s += _score(high, 10)
    s += _score(cough in ["없음","가끔"], 5)
    if s: reasons["세균성 편도/부비동염 가능"].append("탁한/혈성 콧물 + 발열")
    cand["세균성 편도/부비동염 가능"] += s

    # 신규: 결막염 관련 가중치
    # 세균성: 농성 + (한쪽 시작) 가점, 양쪽 보조 / 맑음 감점
    s = 0.0
    s += _score(eye == "노랑-농성", 35)
    s += _score(eye == "한쪽", 10)
    s += _score(eye == "양쪽", 5)
    s -= _score(eye == "맑음", 10)
    if s: reasons["세균성 결막염 가능"].append("농성 눈꼽 ± 한쪽 시작")
    cand["세균성 결막염 가능"] += max(0.0, s)

    # 아데노바이러스 결막염: 고열 + 상기도 동반 + 양측성 경향, 농성은 감점
    s = 0.0
    s += _score(high, 15)
    s += _score(nasal not in ["없음",""], 10)
    s += _score(eye == "양쪽", 15)
    s -= _score(eye == "노랑-농성", 10)
    if s: reasons["아데노바이러스 결막염 가능"].append("발열 + 상기도 + 양측")
    cand["아데노바이러스 결막염 가능"] += max(0.0, s)

    # 알레르기성 결막염: 맑은 분비물 + 가려움 + 투명 콧물
    s = 0.0
    s += _score(eye == "맑음", 15)
    s += _score(eye == "가려움 동반", 20)
    s += _score(nasal in ["투명"], 10)
    if s: reasons["알레르기성 결막염 가능"].append("맑은 눈물/가려움 + 투명 콧물")
    cand["알레르기성 결막염 가능"] += s

    items = [{"label": k, "score": round(max(0.0, min(100.0, v)), 1)} for k, v in cand.items()]
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
