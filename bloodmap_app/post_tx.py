# post_tx.py — 이식 후 관리(기간별) 섹션 (패치 방식, 비파괴)
from __future__ import annotations
from dataclasses import dataclass

@dataclass
class Phase:
    name: str
    range: str   # human readable
    risk: str
    focus: list[str]
    actions: list[str]
    callout: list[str]

PHASES = [
    Phase(
        name="초기 안정화",
        range="D+0 ~ D+30",
        risk="발열·패혈증, 점막염, 백혈구 감소, 수분·전해질 불균형",
        focus=[
            "엄격한 손 위생 · 마스크",
            "매 끼니 익힌 음식 위주(생·반숙 금지)",
            "입안 상처/백태, 설사/복통, 기침·가래, 배뇨통/탁뇨 관찰",
            "규칙적 복약(면역억제제·보조약) — 시간 엄수",
        ],
        actions=[
            "수분 충분(의료진 지시 범위), ORS 활용(설사/구토 시)",
            "발열 시 기존 해열제 가드레일(APAP≥4h/IBU≥6h, 24h 총량) 준수",
            "체중·체온·소변량 간단 기록(케어 로그 활용)",
        ],
        callout=[
            "≥38.5℃ 또는 **발열+호중구감소**: 병원 연락",
            "≥39.0℃: 즉시 병원(응급실 고려)",
            "혈변/검은변, 심한 탈수 징후 시 의료진 상담",
        ],
    ),
    Phase(
        name="확장 주의기",
        range="D+31 ~ D+100",
        risk="기회감염, 급성 GVHD, 약물 독성(간/신장/골수)",
        focus=[
            "손 위생/마스크 유지(혼잡·밀폐공간 최소화)",
            "식이 다변화는 의료진 허가 범위 내에서 점진적",
            "피부·간·신장 모니터링(발진/가려움, 갈색뇨, 부종 등)",
        ],
        actions=[
            "정기 채혈(ANC, CRP, 간·신장, eGFR) — 기존 피수치 해석 표로 확인",
            "예방접종/금기 식품은 반드시 주치의와 상의",
            "케어 로그에 투약/증상 지속 기록(패턴 확인)",
        ],
        callout=[
            "새 발진·황달·소변량 감소·부종: 의료진 상담",
            "지속 열/기침·가래 악화/흉통·호흡곤란: 병원 평가",
        ],
    ),
    Phase(
        name="회복 전환기",
        range="D+101 ~ D+180",
        risk="만성 GVHD 초동, 영양 불균형, 체력 저하",
        focus=[
            "단백·칼로리 균형, 수분 유지",
            "점진적 활동·근지구력 회복(과로 금지)",
            "구강·피부·눈건조 등 만성 GVHD 초기 증상 체크",
        ],
        actions=[
            "피수치 추이 그래프(ANC/Hb/PLT/CRP/eGFR)로 회복 경향 확인",
            "의료진이 허용하면 식이 스펙트럼 확대(비가열 식품은 단계적)",
        ],
        callout=[
            "구강 궤양/안구건조 심화, 피부 경화·쪼김: 의료진 상담",
            "원인불명 체중감소·미열 지속 시 평가 필요",
        ],
    ),
    Phase(
        name="장기 관리",
        range="D+181 이후",
        risk="만성 합병증, 백신 일정(재접종), 재발 감시",
        focus=[
            "정기 외래/채혈·영상 추적 준수",
            "백신 스케줄(재접종) — 센터 프로토콜 준수",
            "생활습관(수면·영양·운동) 리듬 회복",
        ],
        actions=[
            "케어 로그로 증상/투약 간헐 점검 지속",
            "필요 시 심리적 지지/사회복귀 지원 연계",
        ],
        callout=[
            "지속 증상/새로운 경고 신호는 즉시 의료진과 상의",
        ],
    ),
]

def _phase_from_days(days: int) -> Phase:
    if days <= 30:
        return PHASES[0]
    if days <= 100:
        return PHASES[1]
    if days <= 180:
        return PHASES[2]
    return PHASES[3]

def render(st, wkey=lambda x: x, profile=None):
    """기간 입력 → 해당 단계 카드+체크리스트/행동/연락 기준을 표시."""
    with st.expander("🧬 이식 후 관리(기간별)", expanded=False):
        col = st.columns([1, 1, 1, 1])
        with col[0]:
            days = st.number_input("이식 후 경과일(D+)", min_value=0, step=1, key=wkey("ptx_days"))
        with col[1]:
            tx_type = st.selectbox("이식 유형", ["자체", "동종(공여자)"], key=wkey("ptx_type"))
        with col[2]:
            infx = st.selectbox(
                "감염 고위험 요인",
                ["없음", "최근 항생제/중심정맥관", "장기 스테로이드"],
                key=wkey("ptx_risk"),
            )
        with col[3]:
            st.write("")

        phase = _phase_from_days(int(days))

        st.markdown(f"#### 📅 단계: **{phase.name}** · {phase.range}")
        st.markdown(f"**주요 위험:** {phase.risk}")

        st.markdown("##### 🎯 중점")
        for t in phase.focus:
            st.write(f"- {t}")

        st.markdown("##### ✅ 권장 행동")
        for a in phase.actions:
            st.write(f"- {a}")

        st.markdown("##### ☎️ 연락/주의 기준")
        for c in phase.callout:
            st.write(f"- {c}")

        st.divider()
        st.markdown(
            "> ℹ️ 본 안내는 보호자 참고용이며, **최종 판단은 의료진 지시**를 따릅니다. "
            "기존 케어로그(해열제 가드레일/APAP·IBU 24h/쿨다운), eGFR 계산, 위험 배너 로직은 이 섹션과 **독립적으로 유지**됩니다."
        )
