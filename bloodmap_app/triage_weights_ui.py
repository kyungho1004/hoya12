
# -*- coding: utf-8 -*-
"""
triage_weights_ui.py
Streamlit UI for intuitive "응급도 가중치 (편집 + 프리셋)"
- 프리셋 버튼 행 + 편집 토글
- 컬러 밴드 점수계 + 상위 기여 요인 칩
- 가중치 슬라이더(잠금/해제) + 신호 강도 슬라이더
- 프리셋 저장/불러오기(Export/Import)
"""
from typing import Dict, Optional
import streamlit as st
import json
from triage_weights import FACTORS, TriageConfig, compute_score, rank_contributors, get_presets

def _band(score: float) -> str:
    if score >= 80: return "🔴 긴급 (80–100)"
    if score >= 60: return "🟠 주의 (60–79)"
    if score >= 40: return "🟡 관찰 (40–59)"
    return "🟢 안정 (0–39)"

def _band_color(score: float) -> str:
    if score >= 80: return "#ef4444"
    if score >= 60: return "#f97316"
    if score >= 40: return "#eab308"
    return "#22c55e"

def _pill(text: str, color: str = "#e5e7eb"):
    st.markdown(f"<span style='display:inline-block;padding:4px 8px;border-radius:9999px;background:{color};font-size:0.9rem'>{text}</span>", unsafe_allow_html=True)

def render_triage_weights_ui(state_key_prefix: str = "triage") -> None:
    st.subheader("⚖️ 응급도 가중치 (프리셋/편집)")

    # 상태 초기화
    if f"{state_key_prefix}_cfg" not in st.session_state:
        st.session_state[f"{state_key_prefix}_cfg"] = TriageConfig()

    cfg: TriageConfig = st.session_state[f"{state_key_prefix}_cfg"]

    # 프리셋 선택/적용
    with st.container(border=True):
        st.caption("프리셋 한 번에 적용하고, 필요하면 세부 가중치를 잠금/편집하세요.")
        cols = st.columns(5)
        presets = get_presets()
        names = list(presets.keys())
        for i, name in enumerate(names):
            with cols[i % 5]:
                if st.button(name, key=f"{state_key_prefix}_preset_{i}"):
                    for f in FACTORS:
                        if not cfg.locked[f]:
                            cfg.weights[f] = float(presets[name][f])

        # 사용자 프리셋 저장/불러오기
        with st.expander("프리셋 저장/불러오기"):
            colA, colB = st.columns([1,1])
            with colA:
                # Export
                user_json = json.dumps(cfg.as_dict(), ensure_ascii=False, indent=2)
                st.download_button("현재 설정 Export(.json)",
                    data=user_json.encode("utf-8"),
                    file_name="triage_config.json",
                    mime="application/json",
                    key=f"{state_key_prefix}_export")
            with colB:
                # Import
                up = st.file_uploader("불러오기(.json)", type=["json"], key=f"{state_key_prefix}_import")
                if up is not None:
                    try:
                        data = json.loads(up.read().decode("utf-8"))
                        st.session_state[f"{state_key_prefix}_cfg"] = TriageConfig.from_dict(data)
                        st.success("불러오기 완료")
                    except Exception as e:
                        st.error(f"불러오기 실패: {e}")

    # 가중치/신호 편집
    st.markdown("### 편집")
    with st.container(border=True):
        edit_cols = st.columns([1.1, 1.1, 0.8, 1.0])
        edit_cols[0].markdown("**요인**")
        edit_cols[1].markdown("**가중치(0.5–2.0)**")
        edit_cols[2].markdown("**잠금**")
        edit_cols[3].markdown("**신호 강도(0–5)**")

        for i, f in enumerate(FACTORS):
            c1, c2, c3, c4 = st.columns([1.1, 1.1, 0.8, 1.0])
            c1.write(f)
            cfg.weights[f] = c2.slider("", 0.5, 2.0, float(cfg.weights[f]), 0.1, key=f"{state_key_prefix}_w_{i}", disabled=cfg.locked[f])
            cfg.locked[f] = c3.checkbox("🔒", value=bool(cfg.locked[f]), key=f"{state_key_prefix}_lock_{i}")
            cfg.signals[f] = c4.slider("", 0.0, 5.0, float(cfg.signals[f]), 0.5, key=f"{state_key_prefix}_s_{i}")

    # 점수 섹션
    score, contrib, max_raw = compute_score(cfg)
    band = _band(score)
    color = _band_color(score)
    st.markdown("### 현재 응급도 지수")
    st.markdown(f"<div style='padding:12px;border-radius:12px;background:{color};color:white;font-weight:700;font-size:1.1rem'>"
                f"응급도 지수: {score} / 100 · {band}</div>", unsafe_allow_html=True)

    st.caption("상위 기여 요인")
    top3 = rank_contributors(contrib, 3)
    for name, val in top3:
        pct = "높음" if val>=2.5 else ("중간" if val>=1.2 else "낮음")
        _pill(f"{name} · {pct}", "#f3f4f6")

    # 설명 블록
    with st.expander("점수 계산 방식(설명)"):
        st.write("""
- 각 요인의 **신호 강도(0–5)** × **가중치(0.5–2.0)**를 합산합니다.
- 이 합계를 '모든 요인이 5점'이라고 가정한 **최대 가능치** 대비 백분율로 표준화하여 **0–100점**으로 표시합니다.
- **프리셋**은 가중치의 시작점을 빠르게 바꾸는 역할을 하고, **잠금(🔒)**을 켜면 프리셋을 눌러도 해당 요인은 변하지 않습니다.
""")

    # 레드플래그 힌트
    with st.expander("레드 플래그 힌트(권장 임계값 예시)"):
        st.write("""
- **80점 이상**: 즉시 진료/응급실 고려.
- **60–79점**: 빠른 외래/긴밀 모니터링.
- **40–59점**: 경과 관찰 + 재평가 예약.
- **0–39점**: 가정 관리 + 교육자료 제공.
""")
