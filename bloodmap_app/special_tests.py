# -*- coding: utf-8 -*-
# special_tests.py — Final SAFE Build (2025-11-02 KST)
# - 절대 monkey-patch 하지 않음(RecursionError 원천 차단)
# - 혹시 외부에서 monkey-patch 한 흔적이 있으면 즉시 원복(방어적 처리)
# - 모든 위젯은 사용자별 네임스페이스 키 사용 → 중복 키 방지
# - 결과는 st.session_state['special_tests_store'][user] 에 저장
# - 보고서/내보내기를 위해 st.session_state['special_tests_report_md'] 도 병행 저장

from __future__ import annotations
import datetime as dt
from typing import Dict, Any
import streamlit as st

# -------- 0) 방어적 복구: 외부 monkey-patch 흔적이 있으면 원복 --------
try:
    if hasattr(st, "_bm_text_input_orig"):
        st.text_input = st._bm_text_input_orig  # type: ignore[attr-defined]
    if hasattr(st, "_bm_selectbox_orig"):
        st.selectbox = st._bm_selectbox_orig    # type: ignore[attr-defined]
    if hasattr(st, "_bm_text_area_orig"):
        st.text_area = st._bm_text_area_orig    # type: ignore[attr-defined]
except Exception:
    # 원복에 실패해도 UI는 정상 동작하도록 무시
    pass

# -------- 1) 공용 유틸 --------
try:
    from zoneinfo import ZoneInfo
    KST = ZoneInfo("Asia/Seoul")
except Exception:
    KST = None

def _now_kst_str() -> str:
    if KST:
        return dt.datetime.now(tz=KST).strftime("%Y-%m-%d %H:%M:%S KST")
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def _ns(s: str) -> str:
    """사용자별 위젯 키 네임스페이스."""
    who = st.session_state.get("key", "guest#PIN")
    return f"{who}:special:{s}"

def _store_result(payload: Dict[str, Any]) -> None:
    """세션 보관: 사용자별로 결과 저장 + 보고서용 md 동시 생성."""
    who = st.session_state.get("key", "guest#PIN")
    bucket = st.session_state.setdefault("special_tests_store", {})
    bucket[who] = {"ts": _now_kst_str(), "data": payload}
    # 보고서용 md 요약도 함께 적재(앱 보고서 탭에서 사용 가능)
    md_lines = ["## 특수검사 요약",
                f"- 저장시각: {bucket[who]['ts']}",
                "### 소변 스트립"]
    u = payload.get("urine", {})
    md_lines += [f"  - Albumin: {u.get('albumin','')}",
                 f"  - Glucose: {u.get('glucose','')}",
                 f"  - Ketone: {u.get('ketone','')}",
                 f"  - Nitrite: {u.get('nitrite','')}",
                 f"  - Leukocyte esterase: {u.get('leukocyte','')}",
                 f"  - 잠혈: {u.get('occult_blood','')}",
                 "### 대변 관찰"]
    s = payload.get("stool", {})
    md_lines += [f"  - 색상: {s.get('color','')}",
                 f"  - 질감: {s.get('texture','')}",
                 f"  - 피 섞임: {s.get('blood','')}",
                 f"  - 횟수/일: {s.get('freq','')}"]
    md_lines += ["### 신속/인후/탈수"]
    r = payload.get("rapid", {})
    md_lines += [f"  - CRP(신속): {r.get('crp','')}",
                 f"  - 인후 충혈: {r.get('throat','')}",
                 f"  - 탈수 의심: {r.get('dehydration','')}",
                 f"  - 코로나 신속: {r.get('covid_ag','')}"]
    adv = payload.get("advice", [])
    if adv:
        md_lines.append("### 권고")
        for t in adv:
            md_lines.append(f"- {t}")
    st.session_state["special_tests_report_md"] = "\n".join(md_lines)

def _get_last() -> Dict[str, Any]:
    who = st.session_state.get("key", "guest#PIN")
    bucket = st.session_state.get("special_tests_store", {})
    return bucket.get(who, {})

# -------- 2) 공개 엔트리포인트 --------
def special_tests_ui() -> None:
    """
    특수검사 UI (안전판).
    - 절대 Streamlit 원본 위젯을 감싸거나 재정의하지 않음.
    - 모든 위젯에 사용자 키 네임스페이스(_ns) 적용.
    - 결과는 세션에 저장되며, 보고서 탭에서 재사용 가능(st.session_state['special_tests_report_md']).
    """
    st.markdown("### 🔬 특수검사 (소변/대변/신속검사)")

    # 2-1) 소변 스트립
    st.markdown("**① 소변 스트립 결과**")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        alb = st.selectbox("Albumin(뇨)", ["없음", "+", "++", "+++"], index=0, key=_ns("ur_alb"))
    with c2:
        glu = st.selectbox("Glucose(뇨)", ["없음", "+", "++", "+++"], index=0, key=_ns("ur_glu"))
    with c3:
        ket = st.selectbox("Ketone(뇨)", ["없음", "+", "++", "+++"], index=0, key=_ns("ur_ket"))
    with c4:
        nit = st.selectbox("Nitrite", ["음성", "양성"], index=0, key=_ns("ur_nit"))
    with c5:
        leu = st.selectbox("Leukocyte esterase", ["음성", "양성"], index=0, key=_ns("ur_leu"))
    with c6:
        blood = st.selectbox("잠혈(뇨)", ["음성", "양성"], index=0, key=_ns("ur_bld"))

    # 2-2) 대변 관찰
    st.markdown("---")
    st.markdown("**② 대변 관찰**")
    d1, d2, d3, d4 = st.columns(4)
    with d1:
        stool_color = st.selectbox("색상", ["갈색", "노란색", "녹색", "회색/백색", "검은색(흑색변)"], key=_ns("stool_color"))
    with d2:
        stool_tex = st.selectbox("질감", ["정상", "묽음(설사)", "끈적/점액", "딱딱"], key=_ns("stool_tex"))
    with d3:
        stool_bld = st.selectbox("피 섞임", ["없음", "소량 선홍색", "점액/혈변", "검은색 의심"], key=_ns("stool_bld"))
    with d4:
        stool_freq = st.selectbox("횟수/일", ["0", "1~2", "3~4", "5~6", "7 이상"], key=_ns("stool_freq"))

    # 2-3) 신속/인후/탈수
    st.markdown("---")
    st.markdown("**③ 신속/인후/탈수 체크**")
    r1, r2, r3, r4 = st.columns(4)
    with r1:
        crp_rapid = st.selectbox("CRP(신속)", ["미실시", "<10", "10~40", "≥40"], key=_ns("crp_rapid"))
    with r2:
        throat = st.selectbox("인후 충혈", ["없음", "경도", "중등도", "심함"], key=_ns("throat_red"))
    with r3:
        dehydration = st.selectbox("탈수 의심", ["없음", "경도", "중등도", "심함"], key=_ns("dehydration"))
    with r4:
        covid = st.selectbox("코로나 신속", ["미실시", "음성", "양성"], key=_ns("covid_ag"))

    # 2-4) 권고 로직(간결/안전)
    tips = []
    # 소변
    if nit == "양성" or leu == "양성":
        tips.append("요로감염 가능성 → 통증/빈뇨/발열 동반 시 평가 권장")
    if blood == "양성":
        tips.append("소변 잠혈 양성 → 반복 양성 시 추가 검사 고려")
    # 대변
    if stool_tex == "묽음(설사)" and stool_freq in ("5~6", "7 이상"):
        tips.append("설사 다빈도 → 수분/전해질 보충(ORS) 및 탈수 관찰")
    if stool_bld in ("점액/혈변", "검은색 의심"):
        tips.append("혈변/흑색변 의심 → 즉시 의료진 상담 권장")
    # CRP/인후
    if crp_rapid in ("10~40", "≥40") and throat in ("중등도", "심함"):
        tips.append("염증 수치 상승 + 인후 충혈 → 세균성 감염 가능성 고려")
    # 탈수
    if dehydration in ("중등도", "심함"):
        tips.append("탈수 의심 → 소변량 감소/구토 지속 시 빠른 내원 필요")

    # 2-5) 저장 + 화면 출력
    payload = {
        "urine": {
            "albumin": alb, "glucose": glu, "ketone": ket,
            "nitrite": nit, "leukocyte": leu, "occult_blood": blood,
        },
        "stool": {
            "color": stool_color, "texture": stool_tex,
            "blood": stool_bld, "freq": stool_freq,
        },
        "rapid": {
            "crp": crp_rapid, "throat": throat,
            "dehydration": dehydration, "covid_ag": covid,
        },
        "advice": tips,
    }
    _store_result(payload)

    st.markdown("#### 요약")
    if tips:
        for t in tips:
            st.warning("• " + t)
    else:
        st.info("현재 입력으로는 뚜렷한 경고사항이 없습니다. 증상 변화 시 다시 기록해주세요.")

    with st.expander("최근 입력(현재 사용자 세션 저장본)"):
        last = _get_last()
        if last:
            st.write(f"저장시각: {last.get('ts')}")
            st.json(last.get("data", {}))
        else:
            st.caption("아직 저장된 항목이 없습니다.")
