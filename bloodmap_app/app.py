# -*- coding: utf-8 -*-
import streamlit as st

# ============================
# Basic Setup
# ============================
st.set_page_config(page_title="피수치 · 보호자 가이드", layout="wide")

# Floating feedback button (우측 하단)
st.markdown("""
<style>
.fb-float {position: fixed; right: 16px; bottom: 16px; z-index: 99999;}
.fb-btn {background:#2563eb;color:#fff;padding:12px 14px;border-radius:999px;
         box-shadow:0 8px 24px rgba(37,99,235,.35);font-weight:600;display:inline-flex;
         align-items:center;gap:8px;text-decoration:none}
.fb-btn:hover{background:#1e40af}
</style>
<div class="fb-float">
  <a class="fb-btn" href="mailto:lee729812@gmail.com?subject=%5B%ED%94%BC%EC%88%98%EC%B9%98%20%EC%95%B1%5D%20%EC%9D%98%EA%B2%AC%20%EB%B0%8F%20%EC%98%A4%EB%A5%98%20%EC%A0%9C%EB%B3%B4"
     target="_blank">✉️ 의견 보내기</a>
</div>
""", unsafe_allow_html=True)

# ============================
# Utilities & Data
# ============================
def wkey(s: str) -> str:
    return f"app_{s}"

def get_weights():
    if "weights" not in st.session_state:
        st.session_state["weights"] = {}
    return st.session_state["weights"]

def set_weights(newW):
    st.session_state["weights"] = dict(newW)

# 프리셋(필요에 맞게 확장 가능)
PRESETS = {
    "기본(Default)": {},
    "보수적(안전 우선)": {
        "w_temp_ge_38_5": 1.2, "w_dyspnea": 1.2, "w_confusion": 1.2, "w_oliguria": 1.2, "w_persistent_vomit": 1.2
    },
}

# ============================
# Caregiver Guide helpers
# ============================
def _peds_homecare_details_soft(
    *, score, stool, fever, cough, eye,
    oliguria, ear_pain, rash, hives, abd_pain, migraine, hfmd
):
    st.markdown("### 보호자 상세 가이드")

    def _box(title, items):
        st.markdown(f"**{title}**")
        for it in items:
            st.write("- " + it)

    # 공통 안내
    _box("🟡 오늘 집에서 살펴보면 좋아요", [
        "미온수나 ORS를 소량씩 자주 드셔보세요.",
        "실내는 가볍고 편안한 복장, 환기와 가습을 적당히 해 주세요.",
        "해열제는 간격을 지키면 도움이 됩니다: APAP 4시간 이상, IBU 6시간 이상.",
    ])

    # 장염/설사 의심
    if score.get("장염 의심", 0) > 0 or stool in ["3~4회", "5~6회", "7회 이상"]:
        _box("💧 장염/설사 의심 — 집에서", [
            "ORS 또는 미온수/맑은 국물을 조금씩 자주 드셔보세요. 구토가 있으면 10–15분 쉬고 다시 시도해요.",
            "기름지거나 자극적인 음식, 유제품은 잠시 쉬어가요.",
            "죽·바나나·사과퓨레·토스트처럼 부드러운 음식부터 천천히 시작해요.",
            "배변·소변·체온 변화를 간단히 기록해 두시면 도움이 됩니다.",
        ])

    # 결막염 의심
    if score.get("결막염 의심", 0) > 0 or eye in ["노랑-농성", "양쪽"]:
        _box("👁️ 결막염 의심 — 집에서", [
            "손 씻기를 자주 해 주세요. 수건·베개는 함께 사용하지 않아요.",
            "생리식염수로 부드럽게 씻어내고, 분비물은 안쪽→바깥쪽 방향으로 닦아줘요.",
            "불편감이 있으면 짧게 냉찜질을 시도해 볼 수 있어요(얼음은 직접 대지 않기).",
            "안약·항생제는 **의료진과 상의 후** 사용해 주세요.",
        ])

    # 상기도/독감 계열
    if score.get("상기도/독감 계열", 0) > 0 or cough in ["조금", "보통", "심함"] or fever not in ["없음", "37~37.5 (미열)"]:
        _box("🤧 상기도/독감 계열 — 집에서", [
            "미온수 자주 마시기, 충분한 휴식이 도움이 됩니다.",
            "콧물이 많으면 생리식염수 세척 후 안전하게 흡인해요.",
            "기침이 심하면 따뜻한 음료가 조금 편안함을 줄 수 있어요. 욕실 스팀은 짧게만 해요.",
            "해열제는 안내된 간격과 용량을 지켜 주세요.",
        ])

    # 발열 38℃ 전후 — 집에서
    if fever in ["38~38.5", "38.5~39", "39 이상"]:
        _box("🌡️ 발열 38℃ 전후 — 집에서", [
            "실내 온도를 약 25–26℃로 유지해 주세요(너무 춥거나 덥지 않게).",
            "미지근한 물로 몸을 부드럽게 닦아주면 열 내려가는 데 도움이 될 수 있어요(차가운 찜질은 피해요).",
            "미온수나 ORS를 **조금씩 자주** 마시도록 해 주세요(한 번에 많이 X).",
            "손발을 만져 보세요. 손발이 **따뜻**하면 열이 잡히는 중일 수 있어요.",
            "손발이 **차가우면** 아직 해열제 효과가 나타나기 전일 수 있어요. **30–60분 뒤 체온을 다시 확인**해 주세요.",
            "해열제 간격은 **APAP 4시간 이상**, **IBU 6시간 이상**을 지켜 주세요(중복 복용은 피합니다).",
        ])

    # 탈수/신장 문제
    if score.get("탈수/신장 문제", 0) > 0 or oliguria:
        _box("🚰 탈수/신장 문제 — 집에서", [
            "입술·혀 마름, 눈물 감소, 소변량 변화를 주의 깊게 살펴봐 주세요.",
            "소변이 6–8시간 이상 없으면 진료가 필요할 수 있어요.",
            "구토가 있으면 10–15분 쉬었다가 ORS를 다시 소량씩 시도해요.",
        ])

    # 출혈성 경향
    if score.get("출혈성 경향", 0) > 0:
        _box("🩸 출혈성 경향 — 집에서", [
            "양치·콧속 세척은 부드럽게 해 주세요. 코 풀 때는 한쪽씩 천천히.",
            "점상출혈/멍이 늘거나 코피가 10분 이상 이어지면 진료를 권해요.",
            "출혈 성향이 있으면 이부프로펜은 피하고, 해열은 APAP 위주가 안전해요.",
        ])

    # 중이염/귀질환
    if score.get("중이염/귀질환", 0) > 0 or ear_pain:
        _box("👂 중이염/귀질환 — 집에서", [
            "통증 조절은 지시된 해열·진통제 간격을 지켜주세요.",
            "코막힘이 심하면 생리식염수 세척이 도움이 될 수 있어요.",
            "귀 안에 물을 넣거나 면봉을 깊게 사용하는 것은 피해주세요.",
        ])

    # 피부발진/경미한 알레르기
    if score.get("피부발진/경미한 알레르기", 0) > 0 or rash or hives:
        _box("🌿 피부발진/가벼운 알레르기 — 집에서", [
            "미지근한 물로 짧게 샤워하고, 보습제를 발라주세요.",
            "면 소재 옷이 편안해요. 긁지 않도록 손톱을 정리해 주세요.",
            "새 세제/음식 노출이 있었다면 잠시 중단해 보세요. 호흡곤란·입술부종은 즉시 진료가 필요해요.",
        ])

    # 복통 평가
    if score.get("복통 평가", 0) > 0 or abd_pain:
        _box("🤢 복통 — 집에서", [
            "배마사지 거부, 국소 압통, 구부정한 자세가 계속되면 악화 신호일 수 있어요.",
            "자극이 적고 소화가 쉬운 음식부터 천천히 드셔보세요.",
            "혈변·담즙성 구토·고열이 함께 보이면 바로 진료를 권해요.",
        ])

    # 알레르기 주의
    if score.get("알레르기 주의", 0) > 0:
        _box("⚠️ 알레르기 — 집에서", [
            "새로운 음식·약 복용 여부를 메모해 두면 진료에 도움이 돼요.",
            "입술·혀·목 부종, 숨 가쁨, 쉰목소리는 즉시 응급실이 좋아요.",
        ])

    # 편두통 의심
    if score.get("편두통 의심", 0) > 0 or migraine:
        _box("🧠 편두통 — 집에서", [
            "조용하고 어두운 환경에서 쉬고, 수분을 보충해 주세요.",
            "빛·소리 자극을 줄이면 편안해질 수 있어요.",
            "갑작스럽고 매우 심한 두통이나 신경학적 증상이 보이면 바로 진료가 필요해요.",
        ])

    # 수족구 의심
    if score.get("수족구 의심", 0) > 0 or hfmd:
        _box("🖐️ 수족구 — 집에서", [
            "손발·입 병변으로 통증이 있을 수 있어요. 부드럽고 차가운 음식이 편할 수 있어요.",
            "자극적인 음식은 잠시 피하고, 수분을 충분히 보충해 주세요.",
            "탈수 신호(소변 감소, 입 마름)가 보이면 진료를 권해요.",
        ])

    # (별도 임계치) 아데노바이러스 가능성
    # 조건: 결막염 점수≥30 또는 눈 소견(노랑-농성/양쪽) + (38℃ 이상 발열) + 상기도 점수≥20 또는 기침 보통/심함
    aden_eye = (eye in ["노랑-농성", "양쪽"]) or (score.get("결막염 의심", 0) >= 30)
    aden_fever = fever in ["38~38.5", "38.5~39", "39 이상"]
    aden_uri = (score.get("상기도/독감 계열", 0) >= 20) or (cough in ["보통", "심함"])
    if aden_eye and aden_fever and aden_uri:
        _box("🧬 아데노바이러스 가능성 — 참고", [
            "여러 소견이 함께 보일 때 가능성을 의심해 볼 수 있어요.",
            "가정에서는 확진이 어렵기 때문에, 증상이 이어지면 진료에서 확인받는 것을 권해요.",
            "손 위생과 개인 물품 분리는 전파를 줄이는 데 도움이 됩니다.",
        ])

    st.markdown("---")
    _box("🔴 바로 진료/연락이 좋아요", [
        "체온 **38.5℃ 이상이 계속되거나 39℃ 이상**일 때",
        "지속 구토(>6시간), **소변량 급감**, 축 늘어짐/의식 흐림이 보일 때",
        "호흡이 힘들거나 푸르스름해 보이거나, 입술·혀가 붓는 느낌이 들 때",
        "혈변/검은 변, 눈 분비물이 **농성 + 양쪽**으로 심할 때",
        "활력징후(맥박·호흡·의식)를 살펴 주세요. **처짐**이나 **경련 병력/의심**이 보이면 지체 없이 병원 진료가 좋아요.",
    ])
    st.caption(":red[응급이 의심되면 지체하지 말고 119 또는 가까운 응급실을 이용해 주세요.]")

def render_caregiver_notes_peds(
    stool, fever, persistent_vomit, oliguria, cough, nasal, eye, abd_pain, ear_pain, rash, hives, migraine, hfmd
):
    # 간단 점수화(예시)
    score = {
        "장염 의심": 40 if stool in ["3~4회", "5~6회", "7회 이상"] else 0,
        "결막염 의심": 30 if eye in ["노랑-농성", "양쪽"] else 0,
        "상기도/독감 계열": 20 if (cough in ["조금", "보통", "심함"] or fever in ["38~38.5","38.5~39","39 이상"]) else 0,
        "탈수/신장 문제": 20 if oliguria else 0,
        "출혈성 경향": 0,
        "중이염/귀질환": 10 if ear_pain else 0,
        "피부발진/경미한 알레르기": 10 if (rash or hives) else 0,
        "복통 평가": 10 if abd_pain else 0,
        "알레르기 주의": 5 if hives else 0,
        "편두통 의심": 10 if migraine else 0,
        "수족구 의심": 10 if hfmd else 0,
    }
    ordered = sorted(score.items(), key=lambda x: x[1], reverse=True)
    st.write("• " + " / ".join([f"{k}: {v}" for k, v in ordered if v > 0]))

    # 상세 가이드
    _peds_homecare_details_soft(
        score=score, stool=stool, fever=fever, cough=cough, eye=eye,
        oliguria=oliguria, ear_pain=ear_pain, rash=rash, hives=hives,
        abd_pain=abd_pain, migraine=migraine, hfmd=hfmd
    )

# ============================
# Tabs
# ============================
tab_labels = ["HOME", "소아"]
t_home, t_peds = st.tabs(tab_labels)

# ---- HOME (메인: 프리셋만 노출) ----
with t_home:
    st.subheader("응급도 가중치 (편집 + 프리셋)")

    left, mid, right = st.columns([1.5, 1, 1])
    with left:
        preset_name = st.selectbox("프리셋 선택", list(PRESETS.keys()), index=0, key=wkey("preset_sel"))
    with mid:
        if st.button("프리셋 적용", key=wkey("preset_apply")):
            base = PRESETS.get(preset_name, {})
            set_weights(base)
            st.success("프리셋을 적용했어요.")
    with right:
        if st.button("기본값으로 초기화", key=wkey("preset_reset")):
            set_weights({})
            st.info("기본값으로 초기화했습니다.")

    W = get_weights()
    with st.expander("현재 가중치 보기(읽기 전용)", expanded=False):
        try:
            st.json({k: float(W.get(k, 1.0)) for k in sorted(W.keys())})
        except Exception:
            st.write(W)
    st.caption("메인 화면에서는 프리셋만 변경할 수 있어요. 세부 가중치 슬라이더는 숨겼습니다.")

    st.divider()
    # 홈 CTA: 소아 탭으로 이동
    cta = st.button("👶 소아 증상 → 바로 안내", use_container_width=True)
    if cta:
        st.components.v1.html("""
        <script>
          const tabs = Array.from(parent.document.querySelectorAll('button[role="tab"]'));
          const target = tabs.find(b => /소아/.test(b.textContent));
          if (target){ target.click(); }
        </script>
        """, height=0)

# ---- PEDS ----
with t_peds:
    st.subheader("소아 보호자 가이드 (증상 입력 → 자동 안내)")

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        nasal = st.selectbox("콧물", ["해당 없음", "맑음", "끈적"], index=0, key=wkey("p_nasal"))
    with c2:
        cough = st.selectbox("기침", ["없음", "조금", "보통", "심함"], index=0, key=wkey("p_cough"))
    with c3:
        stool = st.selectbox("설사", ["해당 없음", "1~2회", "3~4회", "5~6회", "7회 이상"], index=0, key=wkey("p_stool"))
    with c4:
        fever = st.selectbox("발열", ["없음", "37~37.5 (미열)", "38~38.5", "38.5~39", "39 이상"], index=0, key=wkey("p_fever"))
    with c5:
        eye = st.selectbox("눈꼽/결막", ["해당 없음", "맑음", "양쪽", "노랑-농성"], index=0, key=wkey("p_eye"))

    r1, r2, r3 = st.columns(3)
    with r1:
        abd_pain = st.checkbox("복통/압통", key=wkey("p_abd_pain"))
        ear_pain = st.checkbox("귀 통증/만지면 울음", key=wkey("p_ear_pain"))
        rash = st.checkbox("피부 발진", key=wkey("p_rash"))
    with r2:
        hives = st.checkbox("두드러기", key=wkey("p_hives"))
        migraine = st.checkbox("편두통 의심", key=wkey("p_migraine"))
        hfmd = st.checkbox("수족구 의심", key=wkey("p_hfmd"))
    with r3:
        persistent_vomit = st.checkbox("지속 구토(>6시간)", key=wkey("p_pvomit"))
        oliguria = st.checkbox("소변량 급감", key=wkey("p_oliguria"))

    # 자동 해석: 즉시 보호자 가이드 표시
    render_caregiver_notes_peds(
        stool=stool, fever=fever, persistent_vomit=persistent_vomit, oliguria=oliguria,
        cough=cough, nasal=nasal, eye=eye, abd_pain=abd_pain, ear_pain=ear_pain,
        rash=rash, hives=hives, migraine=migraine, hfmd=hfmd
    )
