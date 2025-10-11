
import streamlit as st

st.set_page_config(page_title="응급도 가중치(친절 모드)", page_icon="🩺", layout="wide")

# --- 배너(있으면 사용) ---
try:
    from branding import render_deploy_banner
    try:
        render_deploy_banner()
    except Exception:
        st.caption("한국시간(KST) 기준. 세포·면역 치료 항목은 혼돈 방지를 위해 표기하지 않습니다. 제작·자문: Hoya/GPT")
except Exception:
    st.caption("한국시간(KST) 기준. 제작·자문: Hoya/GPT")

st.title("응급도 가중치 (편집 + 프리셋)")
st.caption("숫자 슬라이더 대신 **낮음/보통/높음**으로 쉽게 조정할 수 있어요. 필요하면 전문가 슬라이더도 열 수 있습니다.")

def render_emerg_weights_ui():
    # ---- 프리셋 & 보호 토글 ----
    col_p1, col_p2, col_p3 = st.columns([2,1,1])
    with col_p1:
        preset = st.selectbox(
            "프리셋 선택",
            ["기본(권장)", "보수적(민감도↑)", "적극적(특이도↑)"],
            help="보호자에게는 '기본(권장)'이 가장 쉬워요.",
            key="ew_preset"
        )
    with col_p2:
        lock_preset = st.toggle("프리셋 값 보호", value=True, help="실수로 바뀌지 않게 잠가요.", key="ew_lock")
    with col_p3:
        reset = st.button("기본값으로 초기화", key="ew_reset")

    # ---- 프리셋 값 정의 ----
    base = {
        # 혈액/감염
        "anc_lt_500": 1.0, "anc_500_999": 0.7, "crp_ge_10": 0.6,
        "hb_lt_7": 0.8, "plt_lt_20k": 0.9,
        # 활력/고위험 신호
        "fever_38_0_38_4": 0.6, "fever_ge_38_5": 1.0, "hr_gt_130": 0.7,
        "resp_distress": 1.0, "loc_altered": 1.0,
        # 출혈/소화
        "melena": 1.0, "hematochezia": 1.0, "persistent_vomit": 0.9, "oliguria": 0.8, "migraine_severe": 0.6,
    }
    conservative = {k: min(1.0, v + 0.15) for k, v in base.items()}       # 민감도↑
    aggressive   = {k: max(0.0, v - 0.15) for k, v in base.items()}       # 특이도↑
    preset_map = {"기본(권장)": base, "보수적(민감도↑)": conservative, "적극적(특이도↑)": aggressive}

    # 세션 초기화/리셋
    if "emerg_weights" not in st.session_state or reset:
        st.session_state["emerg_weights"] = preset_map["기본(권장)"].copy()

    # 프리셋 적용
    col_apply1, col_apply2 = st.columns([1,5])
    with col_apply1:
        if st.button("프리셋 적용", key="ew_apply") or lock_preset:
            st.session_state["emerg_weights"].update(preset_map.get(preset, base))

    # ---- 간단 모드 (권장) ----
    st.markdown("### 간단 보기 (권장)")
    st.caption("아래는 쉬운 말로 구성된 핵심 항목이에요. **그대로 사용해도 충분**합니다.")

    def lvl_select(label, key, why, default=None):
        """낮음/보통/높음 3단 선택으로 변환"""
        levels = {"낮음": 0.4, "보통": 0.7, "높음": 1.0}
        if default is None:
            default = {1.0:"높음",0.7:"보통",0.4:"낮음"}.get(st.session_state["emerg_weights"].get(key,0.7),"보통")
        col1, col2 = st.columns([2,3])
        with col1:
            st.markdown(f"**{label}**")
            st.caption(why)
        with col2:
            choice = st.select_slider("가중치", options=list(levels.keys()), value=default, key=f"lv_{key}",
                                      help="긴급도 계산에서 이 항목의 영향력을 고릅니다.")
        st.session_state["emerg_weights"][key] = levels[choice]

    with st.container():
        st.markdown("#### 🩸 혈액/감염")
        lvl_select("호중구 **매우 낮음** (ANC<500)", "anc_lt_500", "감염 위험이 매우 큽니다.")
        lvl_select("호중구 낮음 (ANC 500~999)", "anc_500_999", "감염 위험이 큽니다.")
        lvl_select("염증 수치 높음 (CRP≥10)", "crp_ge_10", "감염·염증 가능성 시사.")

        st.markdown("#### ❤️ 활력/고위험 신호")
        lvl_select("고열 ≥38.5℃", "fever_ge_38_5", "고열은 탈수·세균성 감염 위험 신호.")
        lvl_select("미열 38.0~38.4℃", "fever_38_0_38_4", "경과 관찰이 필요합니다.")
        lvl_select("호흡곤란", "resp_distress", "숨이 차 보이거나, 흉부 함몰/청색증.")
        lvl_select("의식 저하/이상", "loc_altered", "무기력/반응 둔화/경련 등.")

        st.markdown("#### 🍽️ 소화/출혈")
        lvl_select("검은 변(흑색변)", "melena", "상부위장관 출혈 의심.")
        lvl_select("혈변", "hematochezia", "하부위장관 출혈 의심.")
        lvl_select("지속 구토", "persistent_vomit", "탈수·전해질 이상 위험.")
        lvl_select("소변량 급감", "oliguria", "탈수/신장 기능 저하 의심.")

    # ---- 전문가(의료진) 설정 ----
    with st.expander("전문가(의료진) 설정 — 세밀 조정", expanded=False):
        st.caption("의료진/숙련 보호자를 위한 세밀 슬라이더입니다.")
        cols = st.columns(3)
        keys = [
            ("anc_lt_500","ANC<500"),("anc_500_999","ANC 500–999"),("fever_38_0_38_4","발열 38.0–38.4"),
            ("fever_ge_38_5","고열 ≥38.5"),("hb_lt_7","중증빈혈 Hb<7"),("plt_lt_20k","혈소판 <20k"),
            ("crp_ge_10","CRP ≥10"),("hr_gt_130","HR>130"),("resp_distress","호흡곤란"),
            ("melena","흑색변"),("hematochezia","혈변"),("persistent_vomit","지속 구토"),
            ("oliguria","소변량 급감"),("loc_altered","의식저하"),("migraine_severe","번개두통")
        ]
        for i, (k, label) in enumerate(keys):
            with cols[i % 3]:
                st.session_state["emerg_weights"][k] = st.slider(
                    label, 0.0, 1.0, float(st.session_state["emerg_weights"].get(k, 0.7)), 0.05,
                    help="가중치가 높을수록 긴급도 점수에 더 크게 반영됩니다.", key=f"sl_{k}"
                )

    # ---- 결과 미리보기 ----
    st.markdown("---")
    w = st.session_state["emerg_weights"]
    # 예시 시나리오 2가지 문장으로 가시화
    preview = []
    score1 = w["fever_ge_38_5"] + w["resp_distress"]
    preview.append(f"• **고열(≥38.5℃) + 호흡곤란** → 가중치 합 {score1:.2f} (응급 권고 가능성 매우 높음)")
    score2 = w["anc_lt_500"] + w["fever_ge_38_5"] + w["crp_ge_10"]
    preview.append(f"• **호중구<500 + 고열 + CRP≥10** → 가중치 합 {score2:.2f} (패혈증 위험 평가 우선)")
    st.info("**현재 설정 미리보기**\n\n" + "\n".join(preview))

    return st.session_state["emerg_weights"]

weights = render_emerg_weights_ui()

# 하단 고정 안내
st.caption("이 도구는 참고용 안내이며, 최종 진단은 의료진의 판단을 따릅니다. 증상이 빠르게 악화되면 즉시 병원을 방문하세요.")
