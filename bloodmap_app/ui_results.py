# -*- coding: utf-8 -*-
"""
ui_results.py
-------------
UI helpers: results gate, adverse effects rendering, pediatric diet guide.
"""

from typing import Dict, List, Any, Tuple


def results_only_after_analyze(st) -> bool:
    """
    If analysis was triggered, returns True and shows a dedicated "결과" header.
    Caller should render only the result panels and then st.stop().
    """
    if st.session_state.get("analyzed"):
        st.divider()
        st.markdown("## 결과")
        st.caption("아래에는 피수치 해석과 식이가이드, 약물 부작용만 표시합니다.")
        return True
    return False


def render_adverse_effects(st, regimen: List[str], DRUG_DB: Dict[str, Dict[str, Any]]) -> None:
    """
    Render adverse effects for a list of drug keys.
    """
    if not regimen:
        return
    st.markdown("#### 💊 약물 부작용(요약)")
    for key in regimen:
        info = (DRUG_DB or {}).get(key) or (DRUG_DB or {}).get(key.lower()) or (DRUG_DB or {}).get((key or "").strip())
        if not info:
            st.write(f"- {key}: 데이터 없음")
            continue
        alias = info.get("alias", key)
        moa = info.get("moa", "")
        ae  = info.get("ae", "")
        st.write(f"- **{key} ({alias})**")
        if moa: st.caption(f"  · 기전/특징: {moa}")
        if ae:  st.caption(f"  · 주의/부작용: {ae}")


def peds_diet_guide(disease: str, vals: Dict) -> Tuple[List[str], List[str], List[str]]:
    """
    Pediatric diet guide (includes otitis media).
    """
    d = (disease or "").lower()
    foods: List[str] = []
    avoid: List[str] = []
    tips:  List[str] = []

    if ("로타" in d) or ("장염" in d) or ("노로" in d):
        foods = ["쌀미음/야채죽", "바나나", "삶은 감자·당근", "구운 식빵/크래커", "연두부"]
        avoid = ["과일 주스·탄산", "튀김/매운 음식", "생채소/껍질 있는 과일", "유당 많은 음식(설사 악화 시)"]
        tips  = ["소량씩 자주 ORS 보충", "구토 후 10분 쉬고 한 모금씩", "모유 수유 중이면 지속"]
    elif "독감" in d:
        foods = ["닭고기·야채죽", "계란찜", "연두부", "사과퓨레/배숙", "미지근한 국물"]
        avoid = ["매운/자극적인 음식", "튀김/기름진 음식", "카페인 음료"]
        tips  = ["고열·근육통 완화되면 빠르게 평소 식사로 회복", "수분 충분히"]
    elif ("rsv" in d) or ("상기도염" in d) or ("파라" in d):
        foods = ["미지근한 물/보리차", "맑은 국/미음", "연두부", "계란찜", "바나나/사과퓨레"]
        avoid = ["차갑고 자극적인 간식 과다", "기름진 음식", "질식 위험 작은 알갱이(견과류 등)"]
        tips  = ["작게·자주 먹이기", "가습/코세척, 밤 기침 대비 베개 높이기"]
    elif "아데노" in d:
        foods = ["부드러운 죽", "계란찜", "연두부", "사과퓨레", "감자/당근 삶은 것"]
        avoid = ["매운/자극", "튀김", "과도한 단 음료"]
        tips  = ["결막염 동반 시 위생 철저(수건 분리)"]
    elif "마이코" in d:
        foods = ["닭가슴살죽", "계란찜", "연두부", "흰살생선 죽", "담백한 국"]
        avoid = ["매운/자극", "튀김/기름진 음식", "카페인 음료"]
        tips  = ["기침 심하면 자극 음식 피하고 수분 늘리기"]
    elif "수족구" in d:
        foods = ["차갑지 않은 부드러운 음식", "바나나", "요거트(자극 적음)", "연두부", "계란찜"]
        avoid = ["뜨겁고 매운 음식", "산성 강한 과일(오렌지/파인애플 등)", "튀김"]
        tips  = ["삼킴 통증 시 온도/질감 조절, 탈수 주의"]
    elif "편도염" in d:
        foods = ["부드러운 죽/미음", "계란찜", "연두부", "따뜻한 국물", "바나나"]
        avoid = ["매운/딱딱한 음식", "튀김"]
        tips  = ["통증 조절하며 수분 충분히"]
    elif "코로나" in d:
        foods = ["부드러운 죽", "연두부/계란찜", "사과퓨레", "바나나", "맑은 국"]
        avoid = ["매운/자극", "튀김/기름진 음식"]
        tips  = ["가족 간 전파 예방, 수분 충분히"]
    # 중이염 (otitis media)
    elif ("중이염" in d) or ("otitis" in d) or ("aom" in d) or ("acute otitis" in d):
        foods = ["미지근한 국/죽", "계란찜", "연두부", "바나나", "부드러운 밥/죽(질감 조절)"]
        avoid = ["아주 뜨겁거나 차가운 음식", "매운/자극적인 음식", "튀김/기름진 음식"]
        tips  = [
            "통증 심하면 진통·해열제 고려(권장 용법 준수)",
            "코막힘 동반 시 가습/생리식염수 비강세척",
            "48–72시간 내 호전 없거나 고열/구토 지속 시 병원 상담",
            "반복 중이염/이루(귀 분비물) 보이면 이비인후과 진료",
        ]
    else:
        foods = ["부드러운 죽/미음", "계란찜", "연두부", "사과퓨레", "따뜻한 국물"]
        avoid = ["매운/자극", "튀김"]
        tips  = ["3일 이상 고열 지속/악화 시 진료 권고"]

    return foods, avoid, tips
