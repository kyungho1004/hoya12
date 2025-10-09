# -*- coding: utf-8 -*-
"""
triage_weights_ui.py
Streamlit UI for intuitive "응급도 가중치 (편집 + 프리셋)"
- 보기 모드: 간단 / 자세히
  • 간단: 프리셋 + 3단계 토글(없음/약간/뚜렷) + 컬러밴드 + 상위 기여 요인
  • 자세히: 가중치/신호 슬라이더, 잠금, Export/Import
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

def _render_header(score: float, contrib: Dict[str, float]):
    band = _band(score)
    color = _band_color(score)
    st.markdown(f"<div style='padding:12px;border-radius:12px;background:{color};color:white;font-weight:700;font-size:1.1rem'>"
                f"응급도 지수: {score} / 100 · {band}</div>", unsafe_allow_html=True)
    st.caption("상위 기여 요인")
    top3 = rank_contributors(contrib, 3)
    for name, val in top3:
        pct = "높음" if val>=2.5 else ("중간" if val>=1.2 else "낮음")
        _pill(f"{name} · {pct}", "#f3f4f6")    

def render_triage_weights_ui(state_key_prefix: str = "triage") -> None:
    st.subheader("⚖️ 응급도 가중치 (프리셋/편집)")

    # 상태 초기화
    if f"{state_key_prefix}_cfg" not in st.session_state:
        st.session_state[f"{state_key_prefix}_cfg"] = TriageConfig()

    cfg: TriageConfig = st.session_state[f"{state_key_prefix}_cfg"]

    # 모드 선택
    mode = st.radio("보기 모드", ["간단", "자세히"], horizontal=True, key=f"{state_key_prefix}_mode")

    # 프리셋 행
    with st.container(border=True):
        st.caption("프리셋 → 시작점을 빠르게 바꾸고, 필요하면 세부 조정하세요.")
        cols = st.columns(5)
        presets = get_presets()
        names = list(presets.keys())
        for i, name in enumerate(names):
            with cols[i % 5]:
                if st.button(name, key=f"{state_key_prefix}_preset_{i}"):
                    for f in FACTORS:
                        # 잠금은 '자세히' 모드에서만 쓰므로 간단 모드에서는 항상 적용
                        if mode == "자세히" and cfg.locked.get(f, False):
                            continue
                        cfg.weights[f] = float(presets[name][f])

    if mode == "간단":
        # 3단계 토글: 없음(0) / 약간(2.5) / 뚜렷(5)
        with st.container(border=True):
            st.markdown("### 증상/소견 강도 (간단 토글)")
            rows = [st.columns(3) for _ in range((len(FACTORS)+2)//3)]
            idx = 0
            for r in rows:
                for c in r:
                    if idx >= len(FACTORS):
                        break
                    f = FACTORS[idx]
                    sel = c.radio(f, ["없음","약간","뚜렷"],
                                  index=0 if cfg.signals[f]<=0.1 else (1 if cfg.signals[f] < 4 else 2),
                                  key=f"{state_key_prefix}_simple_{idx}")
                    cfg.signals[f] = 0.0 if sel=="없음" else (2.5 if sel=="약간" else 5.0)
                    idx += 1

        score, contrib, _ = compute_score(cfg)
        _render_header(score, contrib)

        with st.expander("점수 계산 방식(설명)"):
            st.write("""
- **간단 모드**에서는 각 요인을 *없음/약간/뚜렷*으로 고르며, 각각 0 / 2.5 / 5점으로 환산합니다.
- 프리셋은 가중치의 '영향력'만 바꾸며, 간단 모드에서는 잠금 개념 없이 모두 적용됩니다.
- 최종 점수는 0~100점으로 표준화되어 컬러 밴드로 표시됩니다.
""")
    else:
        # 자세히: 기존 에디터
        st.markdown("### 편집 (가중치/신호/잠금)")
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

        score, contrib, _ = compute_score(cfg)
        _render_header(score, contrib)

        # Export/Import
        with st.expander("프리셋 저장/불러오기"):
            colA, colB = st.columns([1,1])
            with colA:
                user_json = json.dumps(cfg.as_dict(), ensure_ascii=False, indent=2)
                st.download_button("현재 설정 Export(.json)",
                    data=user_json.encode("utf-8"),
                    file_name="triage_config.json",
                    mime="application/json",
                    key=f"{state_key_prefix}_export")
            with colB:
                up = st.file_uploader("불러오기(.json)", type=["json"], key=f"{state_key_prefix}_import")
                if up is not None:
                    try:
                        import json as _json
                        data = _json.loads(up.read().decode("utf-8"))
                        st.session_state[f"{state_key_prefix}_cfg"] = TriageConfig.from_dict(data)
                        st.success("불러오기 완료")
                    except Exception as e:
                        st.error(f"불러오기 실패: {e}")
