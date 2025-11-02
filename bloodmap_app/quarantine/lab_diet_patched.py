# -*- coding: utf-8 -*-
from typing import Dict, List, Tuple, Optional

def lab_diet_guides(labs: Dict, heme_flag: bool = False) -> List[str]:
    """
    피수치 기반 식이가이드(예시)
    labs: {'Alb':3.1, 'K':3.2, ...}
    heme_flag: 혈액암 카테고리 여부(철분+비타민C 경고)
    """
    L: List[str] = []

    def add(title, foods, caution=None):
        if foods:
            L.append(f"{title} → 권장 예시: {', '.join(foods)}")
        if caution:
            L.append(f"주의: {caution}")

    Alb = labs.get("Alb"); K = labs.get("K"); Hb = labs.get("Hb"); Na = labs.get("Na"); Ca = labs.get("Ca")
    Glu = labs.get("Glu"); AST=labs.get("AST"); ALT=labs.get("ALT"); Cr=labs.get("Cr"); BUN=labs.get("BUN")
    UA=labs.get("UA"); CRP=labs.get("CRP"); ANC=labs.get("ANC"); PLT=labs.get("PLT")

    if Alb is not None and Alb < 3.5:
        add("알부민 낮음", ["달걀","연두부","흰살 생선","닭가슴살","귀리죽"])
    if K is not None and K < 3.5:
        add("칼륨 낮음", ["바나나","감자","호박죽","고구마","오렌지"])
    if Hb is not None and Hb < 10:
        add("Hb 낮음(빈혈)", ["소고기","시금치","두부","달걀 노른자","렌틸콩"],
            caution="보충제는 식품이 아닙니다. (혈액암인 경우 철분제+비타민C 복용은 반드시 주치의와 상의)")
        if heme_flag:
            L.append("⚠️ 혈액암 환자: 철분제 + 비타민C 병용은 흡수 촉진 → 반드시 주치의와 상의 후 결정")
    if Na is not None and Na < 135:
        add("나트륨 낮음", ["전해질 음료","미역국","바나나","오트밀죽","삶은 감자"])
    if Ca is not None and Ca < 8.5:
        add("칼슘 낮음", ["연어통조림","두부","케일","브로콜리"], caution="참깨는 제외")
    if Glu is not None and Glu >= 140:
        add("혈당 높음", ["현미/귀리","두부 샐러드","채소 수프","닭가슴살","사과(소과)"],
            caution="당분 많은 간식/음료 피하기")
    if (Cr is not None and Cr > 1.2) or (BUN is not None and BUN > 20):
        add("신장 수치 상승", ["물/보리차 자주 조금씩","애호박/오이 수프","양배추찜","흰쌀죽","배/사과(소량)"],
            caution="단백질 과다 섭취·짠 음식 피하고, 탈수 주의")
    if (AST is not None and AST >= 50) or (ALT is not None and ALT >= 55):
        add("간수치 상승(AST/ALT)", ["구운 흰살생선","두부","삶은 야채","현미죽(소량)","올리브오일 드레싱 샐러드"],
            caution="기름진/튀김/술 피하기")
    if UA is not None and UA > 7:
        add("요산 높음", ["우유/요거트","달걀","감자","채소류","과일(체리 등)"],
            caution="내장·멸치·맥주 등 퓨린 높은 음식 제한")
    if CRP is not None and CRP >= 3:
        add("CRP 상승(염증)", ["토마토","브로콜리","블루베리","연어(완전 익히기)","올리브오일"],
            caution="생식 금지, 충분한 수분")
    if ANC is not None and ANC < 500:
        add("ANC<500 (호중구감소)", ["흰죽","계란찜(완숙)","연두부","잘 익힌 고기/생선","통조림 과일(시럽 제거)"],
            caution="생채소 금지 · 모든 음식은 완전히 익히기 또는 전자레인지 30초↑ · 멸균/살균 식품 권장 · 남은 음식은 2시간 지나면 폐기 · 껍질 있는 과일은 주치의와 상의")
    if PLT is not None and PLT < 20000:
        add("혈소판 낮음(PLT<20k)", ["계란찜","두부","바나나","오트밀죽","미역국"],
            caution="딱딱/자극 음식·술 피하고, 양치 시 부드러운 칫솔 사용")

    return L


# ===== 신규: Streamlit 패널(피수치 가이드 + 소아 보호자 가이드 한 화면) =====
def lab_diet_panel(labs: Dict, heme_flag: bool = False, *, show_peds: bool = True) -> Tuple[List[str], Optional[Dict]]:
    """
    Streamlit 기반 출력 패널: 피수치 식이가이드와 (옵션) 소아 보호자 가이드를 함께 렌더.
    Returns:
        (diet_list, peds_compiled or None)
    """
    import streamlit as st
    diet_list = lab_diet_guides(labs, heme_flag=heme_flag)

    with st.expander("🍽️ 피수치 기반 식이가이드", expanded=True):
        if diet_list:
            for row in diet_list:
                st.markdown(f"- {row}")
        else:
            st.info("현재 입력된 수치로는 별도 식이가이드 권고가 없습니다.")

    compiled = None
    if show_peds:
        # 지표상 ANC<1000 이면 식품안전도 강하게 안내되는 만큼, 보호자 호흡기 가이드도 같이 노출
        from peds_guide import render_peds_extra_inputs, render_symptom_explain_peds

        st.markdown("---")
        st.subheader("👶 소아 보호자 가이드")
        st.caption("가래/쌕쌕/변비 및 RSV·아데노·파라인플루엔자·모세기관지염 의심 시 가정 관리 팁과 병원 방문 기준을 안내합니다.")

        # 기본 증상 입력(간단 선택만 제공; 상세 입력은 상위 탭에서 확장 가능)
        c1, c2, c3 = st.columns(3)
        with c1:
            fever = st.selectbox("발열", ["없음","미열","고열"], key="ld_fever")
        with c2:
            cough = st.selectbox("기침", ["없음","조금","보통","심함"], key="ld_cough")
        with c3:
            nasal = st.selectbox("콧물", ["없음","조금","보통","심함"], key="ld_nasal")

        c4, c5, c6 = st.columns(3)
        with c4:
            stool = st.selectbox("설사", ["없음","조금","보통","심함"], key="ld_stool")
        with c5:
            eye = st.selectbox("눈(충혈/눈곱)", ["없음","조금","심함"], key="ld_eye")
        with c6:
            max_temp = st.text_input("최고 체온(℃)", "", key="ld_maxt")

        # 신규 추가 입력
        extra = render_peds_extra_inputs(key_prefix="ld")

        compiled = render_symptom_explain_peds(
            stool=st.session_state.get("ld_stool","없음"),
            fever=st.session_state.get("ld_fever","없음"),
            persistent_vomit=st.session_state.get("ld_vomit", False),
            oliguria=st.session_state.get("ld_oliguria", False),
            cough=st.session_state.get("ld_cough","없음"),
            nasal=st.session_state.get("ld_nasal","없음"),
            eye=st.session_state.get("ld_eye","없음"),
            abd_pain=st.session_state.get("ld_abd_pain", False),
            ear_pain=st.session_state.get("ld_ear_pain", False),
            rash=st.session_state.get("ld_rash", False),
            hives=st.session_state.get("ld_hives", False),
            migraine=st.session_state.get("ld_migraine", False),
            hfmd=st.session_state.get("ld_hfmd", False),
            max_temp=st.session_state.get("ld_maxt") or None,
            sputum=extra["sputum"], wheeze=extra["wheeze"], constipation=extra["constipation"],
            flag_adeno=extra["flag_adeno"], flag_rsv=extra["flag_rsv"],
            flag_para=extra["flag_para"], flag_bronchiolitis=extra["flag_bronchiolitis"],
            age_years=st.session_state.get("age_years", None),
        )

    return diet_list, compiled
