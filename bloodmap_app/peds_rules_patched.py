# -*- coding: utf-8 -*-
from typing import Dict, List, Optional

def _score(ok: bool, w: float) -> float:
    return w if ok else 0.0

def _diarrhea_to_count(val) -> int:
    """라벨('4~6회','7회 이상') 또는 숫자 -> 정수 횟수로 변환"""
    try:
        if isinstance(val, (int, float)):
            return int(val)
    except Exception:
        pass
    s = str(val or "")
    if "7" in s: return 7
    if "6" in s or "5" in s or "4" in s: return 5
    if "3" in s: return 3
    if "2" in s: return 2
    if "1" in s: return 1
    try:
        return int(float(s))
    except Exception:
        return 0

def predict_from_symptoms(sym: Dict[str, str], temp_c: float, age_m: Optional[int] = None) -> List[Dict]:
    """소아 일상 증상 기반 간단 추정 (Top-3)"""
    nasal = (sym.get("콧물") or "").strip()
    cough = (sym.get("기침") or "").strip()
    diarrhea_opt = sym.get("설사")
    fever_cat = (sym.get("발열") or "").strip()
    eye = (sym.get("눈꼽") or "").strip()
    age_m = age_m or 0

    dcnt = _diarrhea_to_count(diarrhea_opt)
    high = (temp_c or 0) >= 38.5
    mild = 37.5 <= (temp_c or 0) < 38.5
    no_uri = (nasal in ["없음", ""]) and (cough in ["없음", ""])
    uri_some = not no_uri

    cand = {
        "바이럴 위장관염(로타/노로)": 0.0,
        "감기/상기도바이러스": 0.0,
        "독감(인플루엔자) 의심": 0.0,
        "아데노/편도염 가능": 0.0,
        "세균성 결막염 가능": 0.0,
        "알레르기성 결막염 가능": 0.0,
        "RSV 가능(특히 영유아)": 0.0,
        "중이염 가능(동반 의심)": 0.0,
    }
    reasons = {k: [] for k in cand}

    # 위장관염(로타/노로)
    s = 0.0
    s += _score(dcnt >= 4, 40)
    s += _score(cough in ["없음", "가끔"], 10)
    s += _score(nasal in ["없음", "투명", ""], 10)
    s += _score(mild, 8)
    s += _score(not high, 5)
    if s: reasons["바이럴 위장관염(로타/노로)"].append("설사 다회(≥4) + 상기도 거의 없음 + 미열")
    cand["바이럴 위장관염(로타/노로)"] += s

    # 감기/상기도바이러스
    s = 0.0
    s += _score(nasal not in ["없음", "", "투명"], 15)
    s += _score(cough in ["가끔", "자주", "심함"], 10)
    s += _score(dcnt <= 2, 5)
    s -= _score(dcnt >= 3, 10)
    if s: reasons["감기/상기도바이러스"].append("콧물/기침 동반 + 설사 적음")
    cand["감기/상기도바이러스"] += s

    # 독감
    s = 0.0
    s += _score(high, 30)
    s += _score((temp_c or 0) >= 39.0, 10)
    s += _score(cough in ["가끔", "자주", "심함"], 5)
    if s: reasons["독감(인플루엔자) 의심"].append("고열(≥38.5)")
    cand["독감(인플루엔자) 의심"] += s

    # 아데노/편도염
    s = 0.0
    s += _score(high, 20)
    s += _score(uri_some, 10)
    s -= _score((dcnt >= 3) and (not high) and (not uri_some), 15)
    if s: reasons["아데노/편도염 가능"].append("고열/상기도 소견")
    cand["아데노/편도염 가능"] += s

    # 세균성 결막염 (농성 + 한쪽 → 양쪽)
    s = 0.0
    s += _score("노랑" in eye or "농성" in eye, 20)
    s += _score("한쪽" in eye, 15)
    s += _score("양쪽" in eye, 10)
    s -= _score("맑음" in eye, 10)
    if s: reasons["세균성 결막염 가능"].append("농성 눈꼽 + 한쪽 시작 경향")
    cand["세균성 결막염 가능"] += s

    # 알레르기성 결막염
    s = 0.0
    s += _score("맑음" in eye, 10)
    s += _score("가려움" in eye, 15)
    s += _score(nasal in ["투명", "없음"], 5)
    if s: reasons["알레르기성 결막염 가능"].append("맑은 분비물 + 가려움")
    cand["알레르기성 결막염 가능"] += s

    # RSV
    s = 0.0
    s += _score(age_m <= 24, 20)
    s += _score(cough in ["자주", "심함"], 20)
    s += _score(nasal not in ["없음", ""], 5)
    if s: reasons["RSV 가능(특히 영유아)"].append("24개월 이하 + 기침 심함")
    cand["RSV 가능(특히 영유아)"] += s

    # 중이염
    s = 0.0
    s += _score(nasal in ["노랑(초록)", "누런"], 20)
    s += _score(high, 10)
    s += _score(cough in ["없음", "가끔"], 5)
    s -= _score(dcnt >= 3, 10)
    if s: reasons["중이염 가능(동반 의심)"].append("농성 콧물 + 발열")
    cand["중이염 가능(동반 의심)"] += s

    items = [{"label": k, "score": round(max(0.0, min(100.0, v)), 1)} for k, v in cand.items()]
    items.sort(key=lambda x: x["score"], reverse=True)
    # 상위 3개
    return items[:3]

def triage_advise(temp_c: float, age_m: Optional[int], diarrhea_opt) -> str:
    """소아 일상 간단 트리아지 (설사 횟수 라벨/숫자 모두 허용)"""
    age_m = age_m or 0
    dcnt = _diarrhea_to_count(diarrhea_opt)
    if age_m < 3 and temp_c >= 38.0:
        return "🟥 3개월 미만 + 발열 → 즉시 병원 권고"
    if temp_c >= 39.0:
        return "🟥 39.0℃ 이상 → 즉시 병원 연락/내원 권고"
    if dcnt >= 7 and temp_c >= 38.5:
        return "🟧 다회 설사(≥7) + 고열 → 오늘 중 외래/선별진료 권고"
    if 38.5 <= temp_c < 39.0:
        return "🟧 38.5~39.0℃ → 해열제 투여 + 외래 상담 고려"
    return "🟩 37.5~38.5℃ 또는 저열 → 수분/ORS, 경과관찰(증가 시 연락)"
