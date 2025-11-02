# -*- coding: utf-8 -*-
"""
special_tests.py — 안전판 (monkeypatch 없음, 고유 key 사용)
- 전역으로 st 위젯을 재바인딩하지 않습니다.
- 진입점: special_tests_ui(), render_special_tests(), injector()
- 모든 위젯은 세션 접두사 기반 고유 key를 사용합니다.
- 프로젝트 고정 원칙 반영: 설사 단순 분류(메모리에 #75), 안내 문구 포함.
"""

from __future__ import annotations
import streamlit as st
from typing import List

# 원본 포인터(존재 시) → 전역 monkeypatch 없이 호출
_TI = getattr(st, "_bm_text_input_orig", st.text_input)
_SB = getattr(st, "_bm_selectbox_orig",  st.selectbox)
_TA = getattr(st, "_bm_text_area_orig",  st.text_area)
_CHK = st.checkbox
_BTN = st.button
_MD  = st.markdown
_INF = st.info
_WRN = st.warning
_SUC = st.success

def _uid() -> str:
    return (st.session_state.get("user_key_raw")
            or st.session_state.get("key")
            or "guest")

def _k(key: str) -> str:
    return f"st_{_uid()}_{key}"

def _header() -> None:
    _MD("### 특수검사 해석")
    st.caption("※ 본 해석은 참고용이며, 정확한 진단은 의료진 판단에 따릅니다.")

def _section_ua() -> None:
    _MD("#### 소변 검사(U/A)")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: alb = _SB("Albumin (알부민뇨)", ["없음","+","++","+++"], index=0, key=_k("ua_alb"))
    with c2: ket = _SB("Ketone (케톤)", ["없음","+","++","+++"], index=0, key=_k("ua_ket"))
    with c3: bld = _SB("Blood (혈뇨)", ["없음","+","++","+++"], index=0, key=_k("ua_bld"))
    with c4: nit = _SB("Nitrite (아질산염)", ["음성","양성"], index=0, key=_k("ua_nit"))
    with c5: glu = _SB("Glucose (당)", ["없음","+","++","+++"], index=0, key=_k("ua_glu"))

    tips: List[str] = []
    if nit == "양성":
        tips.append("요로감염 가능성: 발열·복통·배뇨통 동반 시 진료 권고")
    if bld in ("++","+++") and alb in ("++","+++"):
        tips.append("사구체염 의심: 부종·혈압 확인 및 진료 권고")
    if ket in ("++","+++") and glu in ("++","+++"):
        tips.append("당뇨성 케톤산증 의심: 탈수/구토/호흡곤란 시 응급실 권고")
    if tips:
        for t in tips:
            _WRN("• " + t)
    else:
        _INF("특이소견 없음에 가까움. 증상과 함께 관찰하세요.")

def _section_diarrhea() -> None:
    _MD("#### 설사 간단 분류(보호자용)")
    color = _SB("변 색상", ["노란색","녹색","피 섞임","검은색","정상/갈색"], key=_k("d_color"))
    freq  = _SB("횟수", ["1~3회/일","4회 이상/일"], key=_k("d_freq"))
    mucus = _SB("점액", ["없음","조금","많음"], key=_k("d_mucus"))
    if freq == "4회 이상/일" or color in ("피 섞임","검은색"):
        _WRN("🚨 경고: 탈수/혈변 위험. 수분 보충 및 의료진 상담 권장.")
    st.caption("※ 설정(#75): 정밀 계산 없이 단순 분류. 최종 판단은 의료진에게.")

def _section_mucositis() -> None:
    _MD("#### 구내염 자가 관리")
    sev = _SB("통증 정도", ["없음","약함","중간","심함"], key=_k("muc_sev"))
    _INF("처방받은 가글을 사용하세요. 약국 생리식염수는 **1주 이상 연속 사용 금지**.")
    if sev in ("중간","심함"):
        _WRN("통증 조절 필요. 음식/수분 섭취 어려우면 진료 권장.")

def _section_notes() -> None:
    _MD("#### 메모")
    _TA("특수검사 관련 메모(선택)", key=_k("memo_st"))

def special_tests_ui():
    _header()
    _section_ua()
    _section_diarrhea()
    _section_mucositis()
    _section_notes()
    _SUC("특수검사 UI 로드 완료(안전판, monkeypatch 없음).")

# 호환용 진입점들
def render_special_tests():
    return special_tests_ui()

def injector():
    return special_tests_ui()
