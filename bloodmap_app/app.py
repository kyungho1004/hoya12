
import streamlit as st

st.set_page_config(page_title="BloodMap App (Safe Tabs + Peds Guide)", page_icon="🩺", layout="wide")

# --- Optional banner ---
try:
    from branding import render_deploy_banner
    try:
        render_deploy_banner()
    except Exception:
        st.caption("KST 기준. 제작/자문: Hoya/GPT — 기존 기능은 보존되며, 아래 항목은 안전하게 '추가'만 됩니다.")
except Exception:
    st.caption("KST 기준. 제작/자문: Hoya/GPT — 기존 기능은 보존되며, 아래 항목은 안전하게 '추가'만 됩니다.")

# ======================================================
#                 Tabs (안전 맵 방식, B안)
# ======================================================
TAB_TITLES = [
    "홈", "소아", "검사결과", "보고서", "복약/용법", "교육/가이드", "설정", "진단",
]
_tabs = st.tabs(TAB_TITLES)
TAB_MAP = {title: tab for title, tab in zip(TAB_TITLES, _tabs)}

def _get_tab_safe(*titles):
    for t in titles:
        if t in TAB_MAP:
            return TAB_MAP[t]
    return st.container()

# 표준 탭 변수(다국어/변형 커버, 없으면 container 반환)
t_home     = _get_tab_safe("홈","Home")
t_peds     = _get_tab_safe("소아","Peds","소아과")
t_labs     = _get_tab_safe("검사결과","Labs","Lab","검사")
t_report   = _get_tab_safe("보고서","Report")
t_meds     = _get_tab_safe("복약/용법","약","약물","Meds","Medication")
t_edu      = _get_tab_safe("교육/가이드","가이드","Edu","Guide")
t_settings = _get_tab_safe("설정","Settings")
t_dx       = _get_tab_safe("진단","진단/평가","Diagnosis","Dx")

# 최종 보루: 혹시 코드 어딘가에서 다음 변수들을 with에 쓰더라도 미리 만들어 둠
for _var in ["t_emerg","t_admin","t_weights","t_triage","t_tools","t_rx","t_dx","t_labs"]:
    if _var not in globals():
        globals()[_var] = st.container()

# ======================================================
#         Weights helpers (uses session_state only)
# ======================================================
DEFAULT_WEIGHTS = {
    # 혈액/감염
    "w_anc_lt500": 1.0, "w_anc_500_999": 1.0, "w_crp_ge10": 1.0,
    "w_hb_lt7": 1.0, "w_plt_lt20k": 1.0,
    # 활력/고위험
    "w_temp_38_0_38_4": 1.0, "w_temp_ge_38_5": 1.0, "w_hr_gt130": 1.0,
    "w_dyspnea": 1.0, "w_confusion": 1.0,
    # 출혈/소화/신경
    "w_melena": 1.0, "w_hematochezia": 1.0, "w_persistent_vomit": 1.0, "w_oliguria": 1.0,
    "w_petechiae": 1.0, "w_thunderclap": 1.0, "w_visual_change": 1.0, "w_chest_pain": 1.0,
}

def get_weights():
    if "weights" not in st.session_state:
        st.session_state["weights"] = dict(DEFAULT_WEIGHTS)
    return st.session_state["weights"]

def set_weights(W: dict):
    st.session_state["weights"] = dict(W)

# ======================================================
#      Pediatric score-based caregiver guidance
# ======================================================
def render_peds_score_guidance(score: dict | None, *, max_temp=None):
    """점수 dict(한글 카테고리 키)를 높음/보통/낮음으로 묶어 가정관리/병원기준 안내.
       키 예시: "장염 의심","상기도/독감 계열","결막염 의심","탈수/신장 문제","출혈성 경향",
               "중이염/귀질환","피부발진/경미한 알레르기","복통 평가","알레르기 주의","편두통 의심","수족구 의심"
    """
    import math
    if not isinstance(score, dict) or not score:
        st.caption("증상 점수 정보가 없어 기본 설명만 제공합니다.")
        return

    HIGH, MID = 2.0, 1.0
    tiers = {"높음": [], "보통": [], "낮음": []}

    def add(title, home_tips, visit_rules, level): tiers[level].append((title, home_tips, visit_rules))
    def level_of(v): return "높음" if v >= HIGH else ("보통" if v >= MID else "낮음")

    mapping = [
        ("장염 의심","장염 의심",
         ["🥤 ORS 5–10분 간격 소량씩", "기름진 음식·생야채·우유 일시 제한", "구토 멎으면 양 서서히 증량", "항문 주위 미온수 세정 후 건조·보습막"],
         ["혈변/흑색변·지속 구토·2시간↑ 무뇨는 병원", "축 처짐/입마름/눈물↓ 등 탈수 의심 시 진료"]),
        ("상기도/독감 계열","상기도/독감 계열",
         ["가습·통풍·미온수 샤워", "생리식염수 분무(소아)", "수면 시 머리 약간 높이기", "해열제 간격 준수(APAP≥4h, IBU≥6h)"],
         ["호흡곤란·청색증은 즉시 병원", "2주↑ 기침 또는 흉통/쌕쌕거림 동반 시 진료"]),
        ("결막염 의심","결막염 의심",
         ["미온수로 안→바깥 닦기(1회 1거즈)", "손 위생, 수건·베개 공유 금지"],
         ["광과민/통증·부종 심하면 진료", "농성 분비물+고열이면 병원"]),
        ("탈수/신장 문제","탈수/신장 문제",
         ["수분/ORS 자주 조금씩 보충", "소변 양·색/체중 기록", "고열 시 미온수 닦기·휴식"],
         ["2시간↑ 무뇨, 입마름/눈물↓은 병원", "어지럼/무기력 심하면 진료"]),
        ("출혈성 경향","출혈성 경향",
         ["강한 마찰·딱딱한 음식·세게 코풀기 줄이기", "부드러운 칫솔 사용"],
         ["지속 코피/잇몸출혈·흑색변/혈변은 병원", "큰 멍이 쉽게 생기면 진료"]),
        ("중이염/귀질환","중이염/귀질환",
         ["누우면 악화 → 머리 약간 높여 수면", "비염 관리(생리식염수·가습)"],
         ["고열·구토 동반/48h↑ 통증 지속 시 진료", "귀 뒤 붓고 심통증은 즉시 병원"]),
        ("피부발진/경미한 알레르기","피부발진/경미한 알레르기",
         ["시원한 환경·마찰 줄이기·보습", "의심 음식/약물 일시 중단·기록"],
         ["얼굴·입술·혀 붓기/호흡곤란은 즉시 병원", "수포·고열 동반 전신 발진은 진료"]),
        ("복통 평가","복통 평가",
         ["복부 따뜻하게·자극적 음식 제한", "통증 위치/시간/식사·배변 연관 기록"],
         ["우하복부 지속 통증/보행 악화/구토·발열 동반은 즉시 진료", "복부 팽만·혈변/흑색변 동반은 병원"]),
        ("알레르기 주의","알레르기 주의",
         ["의심 음식/약물 중단", "시원한 환경·보습·냉찜질"],
         ["호흡곤란/얼굴·입술·혀 붓기/전신 두드러기는 즉시 병원"]),
        ("편두통 의심","편두통 의심",
         ["어두운 조용한 환경·수분 보충", "진통제 간격 엄수(중복 주의)"],
         ["번개두통·신경학적 이상은 즉시 병원", "점차 악화·구토/시야 이상 동반 시 진료"]),
        ("수족구 의심","수족구 의심",
         ["차갑거나 미지근한 부드러운 음식", "수분 보충·부드러운 양치"],
         ["섭취 거부/침 흘림 심하면 병원", "고열 3일↑·무기력 심하면 진료"]),
    ]

    # 점수→레벨 분류
    for key, title, home_tips, visit_rules in mapping:
        v = float(score.get(key, 0) or 0)
        lvl = "높음" if v >= HIGH else ("보통" if v >= MID else "낮음")
        tiers[lvl].append((title, home_tips, visit_rules))

    # 최고 체온 보정
    if max_temp is not None:
        try:
            mt = float(max_temp)
            if mt >= 39.0:
                tiers["높음"].insert(0, ("최고 체온", [], [f"현재 최고 {mt:.1f}℃ → 즉시 병원 권고 수준입니다."]))
            elif mt >= 38.5:
                tiers["보통"].insert(0, ("최고 체온", [], [f"현재 최고 {mt:.1f}℃ → 해열/수분 보충 후 면밀 관찰 필요."]))
        except Exception:
            pass

    # 저호중구 식품안전(있으면 상단)
    try:
        anc_val = float(str(st.session_state.get("labs_dict", {}).get("ANC", "")).replace(",", "."))
    except Exception:
        anc_val = None
    if anc_val is not None and anc_val < 1000:
        tiers["높음"].insert(0, ("저호중구 음식 안전",
            ["생야채/껍질 과일 피하기·**완전 가열**", "남은 음식 **2시간 이후 비권장**, 멸균·살균 식품 권장"],
            ["38.0℃↑ 발열 시 병원 연락, 38.5~39℃ 이상은 상위 조치"]))

    with st.expander("👪 증상 점수 기반 보호자 가이드", expanded=False):
        for lvl in ["높음", "보통", "낮음"]:
            items = tiers[lvl]
            if not items: 
                continue
            st.markdown(f"### {lvl} 우선 순위")
            for title, home_tips, visit_rules in items:
                st.markdown(f"**{title}**")
                if home_tips:
                    st.markdown("가정 관리")
                    for x in home_tips: st.markdown(f"- {x}")
                if visit_rules:
                    st.markdown("병원 방문 기준")
                    for x in visit_rules: st.markdown(f"- {x}")
                st.markdown("---")

# ======================================================
#          Expert sliders panel (wrapped in expander)
# ======================================================
def render_expert_sliders():
    W = get_weights()
    grid = [
        ("ANC<500", "w_anc_lt500"),
        ("ANC 500~999", "w_anc_500_999"),
        ("발열 38.0~38.4", "w_temp_38_0_38_4"),
        ("고열 ≥38.5", "w_temp_ge_38_5"),
        ("혈소판 <20k", "w_plt_lt20k"),
        ("중증빈혈 Hb<7", "w_hb_lt7"),
        ("CRP ≥10", "w_crp_ge10"),
        ("HR>130", "w_hr_gt130"),
        ("혈뇨", "w_hematuria"),
        ("흑색변", "w_melena"),
        ("혈변", "w_hematochezia"),
        ("흉통", "w_chest_pain"),
        ("호흡곤란", "w_dyspnea"),
        ("의식저하", "w_confusion"),
        ("소변량 급감", "w_oliguria"),
        ("지속 구토", "w_persistent_vomit"),
        ("점상출혈", "w_petechiae"),
        ("번개두통", "w_thunderclap"),
        ("시야 이상", "w_visual_change"),
    ]
    cols = st.columns(3)
    newW = dict(W)
    for i, (label, keyid) in enumerate(grid):
        with cols[i % 3]:
            newW[keyid] = st.slider(label, 0.0, 3.0, float(W.get(keyid, 1.0)), 0.1, key=f"sl_{keyid}")
    if newW != W:
        set_weights(newW)
        st.success("가중치 변경 사항 저장됨.")

# ======================================================
#                 HOME (초보자 + 전문가)
# ======================================================
with t_home:
    st.header("홈")
    st.subheader("응급도 가중치")
    st.caption("초보자용은 위에서 간단하게, 전문가용은 아래에서 세밀하게 조정합니다. 기존 계산 로직은 그대로 유지됩니다.")

    # --- 🔰 초보자용 간단 설정 ---
    st.markdown("#### 🔰 초보자용 간단 설정")
    st.caption("어려우면 이 부분만 조정해도 충분합니다. 세밀한 값은 아래 '전문가용'에서 바꿀 수 있어요.")
    W_simple = dict(get_weights())

    def _apply_group(level, keys, base=1.0):
        mapping = {"낮음": 0.9, "보통": 1.0, "높음": 1.2}
        w = mapping.get(level, 1.0)
        for k in keys:
            W_simple[k] = round(base * w, 2)

    colS1, colS2, colS3 = st.columns(3)
    with colS1:
        inf_lvl = st.select_slider("발열·감염 민감도", options=["낮음","보통","높음"], value="보통",
                                   help="고열/CRP/호중구 감소에 대한 가중치")
    with colS2:
        bleed_lvl = st.select_slider("출혈 위험 민감도", options=["낮음","보통","높음"], value="보통",
                                     help="혈소판 감소/출혈 징후에 대한 가중치")
    with colS3:
        neuro_lvl = st.select_slider("신경·호흡 민감도", options=["낮음","보통","높음"], value="보통",
                                     help="의식저하/흉통/호흡곤란/번개두통/시야이상")

    _apply_group(inf_lvl,   ["w_temp_ge_38_5","w_temp_38_0_38_4","w_crp_ge10","w_anc_lt500","w_anc_500_999"])
    _apply_group(bleed_lvl, ["w_plt_lt20k","w_petechiae","w_melena","w_hematochezia"])
    _apply_group(neuro_lvl, ["w_confusion","w_chest_pain","w_dyspnea","w_thunderclap","w_visual_change","w_hr_gt130"])

    if W_simple != get_weights():
        set_weights(W_simple)
        st.success("초보자용 설정이 적용되었습니다.")

    st.markdown("---")
    with st.expander("전문가용 세밀 조정(슬라이더)", expanded=False):
        render_expert_sliders()

# ======================================================
#                 PEDS (점수 가이드)
# ======================================================
with t_peds:
    st.header("소아")
    st.caption("소아 보호자 가이드는 점수(score)와 최고 체온을 기준으로 친절하게 정리됩니다.")

    # 기존 앱에서 만든 score / max_temp가 있으면 재사용
    score = st.session_state.get("peds_score") or {}
    max_temp = st.session_state.get("max_temp")

    # 점수가 전혀 없을 때를 대비한 가벼운 입력(원본 앱엔 영향 없음)
    with st.expander("점수 입력(없으면 건너뜀)", expanded=False):
        if not score:
            # 한국어 카테고리 키 초기 템플릿
            init = {
                "장염 의심": 0, "상기도/독감 계열": 0, "결막염 의심": 0, "탈수/신장 문제": 0, "출혈성 경향": 0,
                "중이염/귀질환": 0, "피부발진/경미한 알레르기": 0, "복통 평가": 0, "알레르기 주의": 0, "편두통 의심": 0, "수족구 의심": 0
            }
            cols = st.columns(3)
            new_score = {}
            items = list(init.items())
            for i, (k, _) in enumerate(items):
                with cols[i % 3]:
                    new_score[k] = st.slider(k, 0.0, 3.0, 0.0, 0.5, key=f"ps_{k}")
            score = new_score
        if max_temp is None:
            max_temp = st.number_input("최고 체온(°C)", min_value=34.0, max_value=43.5, step=0.1, format="%.1f")

    # 가이드 렌더
    try:
        render_peds_score_guidance(score, max_temp=max_temp)
    except Exception as _e:
        st.caption(f"점수 가이드 로딩 중: {_e}")

# ======================================================
#              LABS / REPORT / OTHERS (placeholders)
# ======================================================
with t_labs:
    st.header("검사결과")
    st.caption("기존 피수치(랩) UI를 그대로 사용하세요. 본 파일은 탭 안전화만 제공하며, 기존 코드를 삭제하지 않습니다.")
    # 기존 앱에서 labs_dict 등을 세션에 저장하면 그대로 활용됩니다.
with t_report:
    st.header("보고서")
    st.caption("기존 보고서 생성 로직을 그대로 사용하세요. (여기서는 삭제/변경하지 않음)")
with t_meds:
    st.header("복약/용법")
    st.caption("기존 약물/용법 UI를 그대로 사용하세요.")
with t_dx:
    st.header("진단")
    st.caption("기존 암 관련 평가/의사결정 로직을 그대로 사용하세요. (탭 NameError만 방지)")
with t_edu:
    st.header("교육/가이드")
    st.caption("기존 교육자료/가이드 UI 그대로.")
with t_settings:
    st.header("설정")
    st.caption("환경 설정/프리셋 등 기존 로직을 그대로 사용하세요.")
