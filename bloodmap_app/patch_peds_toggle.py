# -*- coding: utf-8 -*-
"""
patch_peds_toggle.py
--------------------
Drop this file into your project (e.g., bloodmap_app/patch_peds_toggle.py)
and use it in app.py like so:

    from patch_peds_toggle import (
        peds_diet_guide,
        render_peds_diet_guide_block,
        render_cancer_example_toggle,
    )

Then replace your existing blocks with:
    render_peds_diet_guide_block(st, disease, vals, report_sections)
    render_cancer_example_toggle(st, dx, group, report_sections, CHEMO, TARGETED, ABX_ONCO, _labelize, auto_recs)

This removes the UnboundLocalError, fixes the [0:NULL] artifacts,
and adds a toggle to "2) 암 선택시(예시)".
"""

from typing import Tuple, List, Dict, Callable


def peds_diet_guide(disease: str, vals: Dict) -> Tuple[List[str], List[str], List[str]]:
    """
    소아 감염질환/상기도염 등에서 간단 식이가이드 반환.
    - disease: UI에서 사용자가 고른 질환명(string)
    - vals   : 현재 수치 dict (미사용이지만 시그니처 유지)
    Returns: (foods, avoid, tips)
    """
    d = (disease or "").lower()
    foods: List[str] = []
    avoid: List[str] = []
    tips: List[str] = []

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
    else:
        # 기본 제안(질환 미선택/기타)
        foods = ["부드러운 죽/미음", "계란찜", "연두부", "사과퓨레", "따뜻한 국물"]
        avoid = ["매운/자극", "튀김"]
        tips  = ["3일 이상 고열 지속/악화 시 진료 권고"]

    return foods, avoid, tips


def render_peds_diet_guide_block(st, disease: str, vals: Dict, report_sections: List):
    """
    Streamlit UI 출력 블록 (NULL 아티팩트 없이 깔끔 출력)
    """
    with st.expander("🥗 식이가이드 (예시)", expanded=True):
        foods, avoid, tips = peds_diet_guide(disease, vals)

        st.markdown("**권장 예시**")
        for f in foods:
            st.markdown(f"- {f}")

        st.markdown("**피해야 할 예시**")
        for a in avoid:
            st.markdown(f"- {a}")

        if tips:
            st.markdown("**케어 팁**")
            for t in tips:
                st.markdown(f"- {t}")

        # 보고서에 포함
        try:
            title = f"소아 식이가이드 — {disease or '기타'}"
            rows = [f"권장: {', '.join(foods)}", f"회피: {', '.join(avoid)}"]
            if tips:
                rows.append(f"팁: {', '.join(tips)}")
            report_sections.append((title, rows))
        except Exception:
            # 보고서 구조가 없거나 형식 다르면 그냥 패스
            pass


def render_cancer_example_toggle(
    st,
    dx: str,
    group: str,
    report_sections: List,
    CHEMO: List[str],
    TARGETED: List[str],
    ABX_ONCO: List[str],
    _labelize: Callable[[List[str], List[str]], List[str]],
    auto_recs: Callable[[str], Dict[str, List[str]]],
):
    """
    '2) 암 선택시(예시)' 블록을 토글로 출력.
    - dx: 선택된 진단명 (영어+진단)
    - group: 암 카테고리(예: '혈액암', '고형암', '림프종', '육종', '희귀암')
    """
    st.markdown("### 2) 암 선택시(예시)")
    show_auto = st.toggle("자동 예시 보기", value=True, key="auto_example_patch")
    if not show_auto:
        return

    rec = auto_recs(dx) or {}
    chemo = rec.get("chemo") or []
    targeted = rec.get("targeted") or []
    abx = rec.get("abx") or []

    if any([chemo, targeted, abx]):
        colr = st.columns(3)
        with colr[0]:
            st.markdown("**항암제 예시**")
            for lab in _labelize(chemo, CHEMO):
                st.markdown(f"- {lab}")
        with colr[1]:
            st.markdown("**표적/면역 예시**")
            for lab in _labelize(targeted, TARGETED):
                st.markdown(f"- {lab}")
        with colr[2]:
            st.markdown("**항생제(발열/호중구감소 시)**")
            for lab in _labelize(abx, ABX_ONCO):
                st.markdown(f"- {lab}")

        st.caption("※ 실제 치료는 환자 상태/바이오마커/가이드라인/의료진 판단에 따릅니다.")

        # 보고서 저장: [암 카테고리] + [영어+진단명] 형태
        try:
            dx_label = f"{group} - {dx}"
            report_sections.append((
                "암 자동 예시",
                [
                    f"진단: {dx_label}",
                    f"항암제: {', '.join(chemo) or '-'}",
                    f"표적/면역: {', '.join(targeted) or '-'}",
                    f"항생제: {', '.join(abx) or '-'}",
                ]
            ))
        except Exception:
            pass
