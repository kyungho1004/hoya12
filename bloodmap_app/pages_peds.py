# -*- coding: utf-8 -*-
"""
pages_peds.py — Phase 1 extractor for the 👶 소아 탭.

원칙:
1) 기존 app.py 삭제 금지, 존재 시 이 모듈을 먼저 호출(없으면 기존 경로 유지)
2) 1차: '퀵 섹션(GI/호흡기)'만 외부화. 나머지는 app.py 그대로.
3) /mnt/data 경로·APAP/IBU 가드레일·케어로그·eGFR·응급 배너 등 절대 손대지 않음.
"""
from __future__ import annotations
import importlib
import streamlit as st

def _safe_import(name: str):
    try:
        return importlib.import_module(name)
    except Exception:
        return None

_peds_guide = _safe_import("peds_guide")
_peds_dose  = _safe_import("peds_dose")
_core_utils = _safe_import("core_utils")

def wkey(x: str) -> str:
    try:
        return f"{x}_{st.session_state.get('_uid','')}".strip('_')
    except Exception:
        return str(x)

def render_peds_tab_phase1() -> None:
    st.subheader("👶 소아 퀵 섹션 (GI/호흡기)")
    st.caption("※ 점진적 분리 중 — 기능은 동일, 경로만 외부화(패치 방식)")

    # 앵커(기존 링크 유지)
    st.markdown('<div id="peds_constipation"></div>', unsafe_allow_html=True)
    st.markdown('<div id="peds_diarrhea"></div>', unsafe_allow_html=True)
    st.markdown('<div id="peds_vomit"></div>', unsafe_allow_html=True)
    st.markdown('<div id="peds_antipyretic"></div>', unsafe_allow_html=True)
    st.markdown('<div id="peds_ors"></div>', unsafe_allow_html=True)
    st.markdown('<div id="peds_respiratory"></div>', unsafe_allow_html=True)

    # 기존 가이드 함수 재사용
    if _peds_guide is not None:
        if hasattr(_peds_guide, "render_section_constipation"):
            try:
                _peds_guide.render_section_constipation()
            except Exception:
                pass
        if hasattr(_peds_guide, "render_section_diarrhea"):
            try:
                _peds_guide.render_section_diarrhea()
            except Exception:
                pass
        if hasattr(_peds_guide, "render_section_vomit"):
            try:
                _peds_guide.render_section_vomit()
            except Exception:
                pass

    # 해열제/ORS는 계산·가드레일이 app.py에 있으므로 여기선 요약만
    with st.expander("해열제 안내(요약) · 자세한 계산은 아래 본문 섹션 참조", expanded=False):
        st.markdown(
            "- **아세트아미노펜(APAP)**: 10–15 mg/kg, **4시간 간격**, 24시간 총량 초과 금지(앱 가드레일 적용)\n"
            "- **이부프로펜(IBU)**: 5–10 mg/kg, **6시간 간격**, 위장장애 시 중단 및 상담\n"
            "- **주의**: 38.5℃ 이상 지속, 39℃ 이상 즉시 연락(앱 경보 참고)"
        )
    with st.expander("ORS(수분보충) 요약", expanded=False):
        st.markdown(
            "- 묽은 설사/구토 시 **소량·자주** 섭취\n"
            "- 탈수 체크리스트는 케어로그 기반 앱 본문에서 자동 안내\n"
            "- **2시간 이상 무뇨/축 늘어짐/반복 구토** 시 즉시 연락"
        )

def render_peds_page() -> None:
    # app.py에서 탭 내부에 삽입 호출
    render_peds_tab_phase1()


# ------------------------------
# Phase-2 (읽기 전용 UI 외부화)
#  - 전문용어 자동 풀이(트리거/토글)
#  - 케어로그·스케줄 안내(문구/레이아웃만)
#  - 점수 "표시부" 프록시: 계산은 기존 app.py가 주도, 이 모듈은 있으면 렌더만 시도
# ------------------------------

def _term_glossary_items():
    return [
        ("QT 연장", "심전도 상 QT 간격이 길어지는 현상. 일부 약물(예: 항암제/항생제/항히스타민)에서 드물게 발생. "
         "실신/어지럼/심계항진 시 즉시 연락. 기존 심장질환·전해질 이상(저칼륨/저마그네슘) 있으면 주의."),
        ("RA 증후군(분화증후군)", "레티노이드/베사노이드 계열 사용 시 발생 가능. 발열, 호흡곤란, 체액저류, 폐침윤 등. "
         "의심 시 즉시 의료진 연락 및 약물 조정 필요."),
        ("손발증후군", "손바닥/발바닥 홍반·따가움·통증. 5‑FU/캡시타빈 등에서 발생. 마찰·열 피하고 보습·냉찜질."),
        ("골수억제", "WBC/Hb/PLT 감소로 감염·빈혈·출혈 위험 증가. 발열·출혈·어지럼 시 즉시 연락."),
        ("간독성(트랜스아미나제 상승)", "AST/ALT 상승. 심한 피로·황달·오심 시 상담. 병용 약(아세트아미노펜 과량 등) 주의."),
        ("신독성", "Cr 상승/소변 감소. 탈수 시 악화. 충분한 수분 섭취 및 신기능 모니터."),
    ]

def render_term_glossary(expanded: bool = False):
    import streamlit as st
    with st.expander("📘 전문용어 바로풀기 (자동 풀이)", expanded=expanded):
        for term, desc in _term_glossary_items():
            st.markdown(f"- **{term}** — {desc}")

def render_carelog_tips():
    import streamlit as st
    with st.expander("📝 케어로그·스케줄 안내 (읽기 전용)", expanded=False):
        st.markdown(
            "- 앱의 케어로그는 **한국시간(KST)** 타임스탬프, **APAP 4시간/IBU 6시간 쿨다운**, **24시간 총량 가드**가 자동 적용됩니다.\n"
            "- **TXT/ICS/PDF/QR** 내보내기 지원: 복약 알림(ICS)으로 다음 복용 시간을 캘린더에 추가할 수 있습니다.\n"
            "- 🚨 최근 30분 내 위험 이벤트가 기록되면 상단 경고 배너가 자동 노출됩니다.\n"
            "- 케어로그 저장 경로: `/mnt/data/care_log` (외부 저장 유지)."
        )

def render_peds_scores_display_enhanced():
    """점수의 '표시부'만 외부 렌더. 계산은 기존 app.py 로직에 위임.
    - 가능한 경우, 내부 렌더러 호출(있으면 사용; 없으면 무시)
    - 존재하지 않거나 예외 시 조용히 폴백
    """
    import streamlit as st, importlib
    # 우선순위: ui_results -> peds_guide
    for mod_name, attr in [("ui_results", "render_peds_scores_display"),
                           ("peds_guide", "render_peds_scores_display")]:
        try:
            mod = importlib.import_module(mod_name)
            if hasattr(mod, attr):
                getattr(mod, attr)()
                return
        except Exception:
            pass
    # 폴백 안내(계산/표시는 기존 app.py 본문에서 처리됨)
    st.caption("※ 점수 계산·표시는 앱 본문 로직에서 수행됩니다(외부 표시부 연결 없음).")

# 기존 진입점 확장: Phase-1 본문 아래에 Phase-2 읽기 전용 블록을 자연스레 붙임
def render_peds_page() -> None:
    render_peds_tab_phase1()
    render_term_glossary(expanded=False)
    render_carelog_tips()
    # 점수 표시부는 화면 하단에 소폭 여백 후 시도
    try:
        import streamlit as st
        st.markdown("---")
    except Exception:
        pass
    render_peds_scores_display_enhanced()




# ------------------------------
# Phase-3 (표시 레이아웃 강화 — 계산은 기존 app.py)
# ------------------------------

def render_peds_scores_display_enhanced():
    """표시 레이아웃만 개선. 계산/데이터는 기존 본문 로직(앱)을 그대로 사용.
    내부적으로 render_peds_scores_display_enhanced()를 호출한다.
    """
    import streamlit as st
    st.markdown('<div id="peds_scores"></div>', unsafe_allow_html=True)
    with st.container():
        st.markdown("#### 📊 소아 점수 표시 (표시 전용)")
        with st.expander("안내 보기", expanded=False):
            st.markdown(
                "- 이 섹션은 **표시 전용**입니다. 점수/경보 계산은 기존 앱 본문이 수행합니다.\n"
                "- 오류 시 자동으로 **기존 본문 표시로 폴백**합니다.\n"
                "- 레이아웃만 개선되며, /mnt/data 경로·가드레일·케어로그 등은 변경되지 않습니다."
            )
        # 실제 표시부 호출(있으면 사용)
        render_peds_scores_display_enhanced()

