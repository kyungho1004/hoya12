
# -*- coding: utf-8 -*-
from typing import Dict, List, Optional

def _score(ok: bool, w: float) -> float:
    return w if ok else 0.0

def _label_to_count(val, adult: bool=False) -> int:
    s = str(val or "").strip()
    if not s: return 0
    try:
        return int(float(s))
    except Exception:
        pass
    if "7" in s: return 7
    if "6" in s or "5" in s: return 5
    if "4" in s or "3" in s: return 4 if adult else 3
    if "2" in s: return 2
    if "1" in s: return 1
    return 0

def predict_from_symptoms(sym: Dict[str, str], temp_c: float, age_m: Optional[int] = None) -> List[Dict]:
    """
    소아 '일상' 예측 로직 (정밀화 v2):
    - 장염을 '로타', '노로', '바이럴 장염(비특이)'로 분리
    - '미열(37.5~38.5) + 콧물 없음 + 설사 다회' 튜닝: 장염 ↑, 아데노 감점
    - '눈꼽'이 끼는 경우: 상기도바이러스(감기) 가중치 소폭 ↑, 아데노/편도염 신뢰도 ↓
    """
    age_m = age_m or 0
    nasal = (sym.get("콧물") or "").strip()
    cough = (sym.get("기침") or "").strip()
    diarrhea_opt = sym.get("설사")
    vomit_opt = sym.get("구토")
    eye = (sym.get("눈꼽") or "").strip()

    dcnt = _label_to_count(diarrhea_opt)
    vcnt = _label_to_count(vomit_opt)
    high = (temp_c or 0) >= 38.5
    mild = 37.5 <= (temp_c or 0) < 38.5
    no_uri = (nasal in ["없음", ""]) and (cough in ["없음", ""])  # 상기도 증상 부재
    uri_some = not no_uri
    eye_present = eye not in ["", "없음"]

    # 후보군
    cand = {
        "바이럴 장염(비특이)": 0.0,
        "로타바이러스 장염": 0.0,
        "노로바이러스 장염": 0.0,
        "감기/상기도바이러스": 0.0,
        "독감(인플루엔자) 의심": 0.0,
        "아데노/편도염 가능": 0.0,
        "중이염 가능(동반 의심)": 0.0,
        "세균성 결막염 가능": 0.0,
        "아데노바이러스 결막염 가능": 0.0,
        "알레르기성 결막염 가능": 0.0,
    }
    reasons: Dict[str, List[str]] = {k: [] for k in cand}

    # --- 장염 3분기 ---
    # (A) 로타
    s = 0.0
    s += _score(age_m <= 60, 12)
    s += _score(dcnt >= 5, 28) or _score(dcnt >= 4, 22)
    s += _score(vcnt >= 2, 12)
    s += _score(mild or high, 6)
    s += _score(no_uri, 12)
    s -= _score(nasal not in ["없음", ""], 6)
    if s < 0: s = 0.0
    if s: reasons["로타바이러스 장염"].append("영유아 + 설사 다회 + 구토 + (미)발열 + 상기도 거의 없음")
    cand["로타바이러스 장염"] += s

    # (B) 노로
    s = 0.0
    s += _score(vcnt >= 3, 28)
    s += _score(1 <= dcnt <= 5, 10)
    s += _score(not high, 8)
    s += _score(no_uri, 10)
    s += _score(age_m >= 24, 6)
    if s < 0: s = 0.0
    if s: reasons["노로바이러스 장염"].append("구토 우세 + 설사 중등 + 고열 아님 + 상기도 없음")
    cand["노로바이러스 장염"] += s

    # (C) 비특이 바이럴 장염
    s = 0.0
    s += _score(dcnt >= 3, 24)
    s += _score(no_uri, 10)
    s += _score(mild or (not high), 6)
    s += _score(vcnt >= 1, 6)
    if s < 0: s = 0.0
    if s: reasons["바이럴 장염(비특이)"].append("설사 다회 + (미)발열 + 상기도 없음")
    cand["바이럴 장염(비특이)"] += s

    # --- 상기도/독감 ---
    s = 0.0
    s += _score(nasal not in ["없음", ""], 15)
    s += _score(cough in ["조금", "보통", "심함"], 12)
    s += _score(eye_present, 6)           # 👁️ 눈꼽 있으면 감기 쪽 가중
    s += _score(eye == "양쪽", 4)         # 양측이면 추가 가중
    s -= _score(dcnt >= 3 and no_uri, 8)  # 설사 다회 + URI 없음이면 감기 감점
    if s < 0: s = 0.0
    if s: reasons["감기/상기도바이러스"].append("콧물/기침 동반(+눈꼽)")
    cand["감기/상기도바이러스"] += s

    s = 0.0
    s += _score(high, 32)
    s += _score(cough in ["보통", "심함"], 8)
    s += _score(nasal in ["없음","투명","흰색"], 5)
    if s < 0: s = 0.0
    if s: reasons["독감(인플루엔자) 의심"].append("고열 중심 + 기침 동반")
    cand["독감(인플루엔자) 의심"] += s

    # --- 아데노/편도염 (신뢰도 하향) ---
    s = 0.0
    s += _score(high, 14)          # ⬇️ 18 → 14
    s += _score(uri_some, 8)       # ⬇️ 10 → 8
    # 핵심 튜닝: '미열 + 콧물 없음 + 설사 다회'이면 아데노 감점(강화)
    s -= _score((dcnt >= 3) and (not high) and no_uri, 22)  # ⬆️ 18 → 22
    # 눈꼽이 있으나 고열이 아니면 추가 감점(결막염으로 분배)
    s -= _score(eye_present and (not high), 6)
    s = max(0.0, s * 0.8)          # 전반적 신뢰도 20% 하향
    if s: reasons["아데노/편도염 가능"].append("고열/상기도 소견(신뢰도 하향 적용)")
    cand["아데노/편도염 가능"] += s

    # --- 중이염 ---
    s = 0.0
    s += _score(nasal in ["누런","피 섞임","노랑(초록)"], 16)
    s += _score(cough in ["없음","조금"], 6)
    s += _score(high, 6)
    s -= _score(dcnt >= 3, 6)
    if s < 0: s = 0.0
    if s: reasons["중이염 가능(동반 의심)"].append("탁한 콧물 + 발열 ± 기침 적음")
    cand["중이염 가능(동반 의심)"] += s

    # --- 결막염 세부 (가중치 소폭 조정) ---
    # 세균성
    s = 0.0
    s += _score(eye == "노랑-농성", 28)
    s += _score(eye == "한쪽", 10)
    s += _score(eye == "양쪽", 5)
    s -= _score(eye == "맑음", 8)
    if s: reasons["세균성 결막염 가능"].append("농성 눈꼽 ± 한쪽 시작")
    cand["세균성 결막염 가능"] += max(0.0, s)

    # 아데노바이러스 결막염 (신뢰도 소폭 하향)
    s = 0.0
    s += _score(high, 8)        # ⬇️ 10 → 8
    s += _score(uri_some, 6)    # ⬇️ 8 → 6
    s += _score(eye == "양쪽", 10)  # ⬇️ 12 → 10
    s -= _score(eye == "노랑-농성", 8)
    if s: reasons["아데노바이러스 결막염 가능"].append("발열 + 상기도 + 양측(신뢰도 하향)")
    cand["아데노바이러스 결막염 가능"] += max(0.0, s)

    # 알레르기성
    s = 0.0
    s += _score(eye == "맑음", 12)
    s += _score(eye == "가려움 동반", 16)
    s += _score(nasal in ["투명"], 8)
    if s: reasons["알레르기성 결막염 가능"].append("맑은 눈물/가려움 + 투명 콧물")
    cand["알레르기성 결막염 가능"] += s

    # 정렬 및 상위 3개
    items = [{"label": k, "score": round(max(0.0, min(100.0, v)), 1)} for k, v in cand.items()]
    items.sort(key=lambda x: x["score"], reverse=True)
    return items[:3]

def triage_advise(temp_c: float, age_m: Optional[int], diarrhea_opt) -> str:
    age_m = age_m or 0
    dcnt = _label_to_count(diarrhea_opt)
    if age_m < 3 and temp_c >= 38.0:
        return "🟥 3개월 미만 + 발열 → 즉시 병원 권고"
    if temp_c >= 39.0:
        return "🟥 39.0℃ 이상 → 즉시 병원 연락/내원 권고"
    if dcnt >= 7 and temp_c >= 38.5:
        return "🟧 다회 설사(≥7) + 고열 → 오늘 중 외래/선별진료 권고"
    if 38.5 <= temp_c < 39.0:
        return "🟧 38.5~39.0℃ → 해열제 투여 + 외래 상담 고려"
    return "🟩 37.5~38.5℃ 또는 저열 → 수분/ORS, 경과관찰(증가 시 연락)"
