# -*- coding: utf-8 -*-
from __future__ import annotations

def render_peds_extras(st):
    """
    소아 모드 추가 UI: '일상/질환' 선택, '지속 일수', '예상 진단명(참고용)'
    - 독립 동작: 기존 앱 상태에 의존하지 않고 별도 섹션으로 렌더
    - 앱 어디에 붙어도 안전 (import 후 그냥 호출)
    """
    st.markdown("---")
    st.subheader("소아 추가 옵션")
    col1, col2 = st.columns([1,1])
    with col1:
        mode = st.radio("모드", ["일상", "질환"], horizontal=True, key="peds_mode")
    with col2:
        days = st.number_input("지속 일수", min_value=0, max_value=30, value=0, step=1, key="peds_days")

    # 기본 증상 입력 (앱 내 다른 곳에서 이미 받는다면 생략 가능)
    with st.expander("증상 입력(간단)"):
        c1, c2, c3 = st.columns(3)
        with c1:
            fever = st.selectbox("발열", ["없음", "미열(37.5~38.4)", "고열(≥38.5)"], index=0, key="peds_fever")
            cough = st.selectbox("기침", ["없음", "마른기침", "가래기침", "쌕쌕거림"], index=0, key="peds_cough")
        with c2:
            rhin = st.selectbox("콧물", ["없음", "투명", "노랑(초록)"], index=0, key="peds_rhin")
            vomi = st.selectbox("구토", ["없음", "있음"], index=0, key="peds_vomi")
        with c3:
            diarr = st.selectbox("설사", ["없음", "물설사", "피 섞임"], index=0, key="peds_diarr")

    dx = _predict_peds_dx(mode, days, fever, cough, rhin, vomi, diarr)
    st.info(f"예상 진단명(참고용): **{dx}**")

    st.caption("※ 참고용 안내입니다. 정확한 진단은 의료진의 판단에 따릅니다.")
    return {"mode": mode, "days": days, "pred_dx": dx}

def _predict_peds_dx(mode, days, fever, cough, rhin, vomi, diarr) -> str:
    \"\"\"단순 규칙 기반 예측 (보호자용 안내 레벨)\"\"\"
    hi_fever = (fever == "고열(≥38.5)")
    feverish = (fever != "없음")
    greenish = (rhin == "노랑(초록)")
    watery = (diarr == "물설사")
    blood_stool = (diarr == "피 섞임")
    wheeze = (cough == "쌕쌕거림")
    dry_cough = (cough == "마른기침")

    # 소화기 우선 규칙
    if watery and (vomi == "있음"):
        return "로타/노로 바이러스 가능성"
    if blood_stool:
        return "장염(세균 가능성)"
    # 호흡기 규칙
    if hi_fever and dry_cough:
        return "인플루엔자(독감) 의심"
    if wheeze or (feverish and rhin == "투명" and days <= 7):
        return "RSV/바이러스성 상기도염 가능성"
    if greenish and days >= 3:
        return "부비동염(세균성) 가능성"
    # 기본
    if feverish or rhin != "없음" or cough != "없음":
        return "감기(바이러스성 상기도감염) 가능성"
    return "정상 범위(경과 관찰)"
