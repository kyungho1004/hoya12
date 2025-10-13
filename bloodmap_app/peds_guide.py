
"""
peds_guide.py
- Pediatric caregiver helpers: extra inputs (sputum/wheeze/constipation & virus flags),
  caregiver explanations, and notes builder.

This module is self-contained and safe to import from Streamlit apps.
"""

from typing import Dict, Tuple, List, Optional
import streamlit as st


def render_peds_extra_inputs(key_prefix: str = "p") -> Dict[str, object]:
    """
    Render extra pediatric inputs in the UI and return their values as a dict.

    Keys used:
    - {key_prefix}_sputum
    - {key_prefix}_wheeze
    - {key_prefix}_constipation
    - {key_prefix}_flag_adeno
    - {key_prefix}_flag_rsv
    - {key_prefix}_flag_para
    - {key_prefix}_flag_bronch

    Returns:
        dict with keys: sputum, wheeze, constipation, flag_adeno, flag_rsv, flag_para, flag_bronchiolitis
    """
    c6, c7, c8 = st.columns(3)
    with c6:
        sputum = st.selectbox(
            "가래",
            ["없음", "조금", "누런/진득", "초록/끈적"],
            key=f"{key_prefix}_sputum",
        )
    with c7:
        wheeze = st.selectbox(
            "쌕쌕거림(천명)",
            ["없음", "조금", "보통", "심함"],
            key=f"{key_prefix}_wheeze",
        )
    with c8:
        constipation = st.selectbox(
            "변비",
            ["없음", "의심(3일↑)", "확실(5일↑/딱딱/통증)"],
            key=f"{key_prefix}_constipation",
        )

    st.markdown("### 바이러스/질환 의심(선택 사항)")
    v1, v2, v3, v4 = st.columns(4)
    with v1:
        flag_adeno = st.checkbox("아데노 의심", key=f"{key_prefix}_flag_adeno")
    with v2:
        flag_rsv = st.checkbox("RSV 의심", key=f"{key_prefix}_flag_rsv")
    with v3:
        flag_para = st.checkbox("파라인플루엔자 의심", key=f"{key_prefix}_flag_para")
    with v4:
        flag_bronchiolitis = st.checkbox("모세기관지염 의심", key=f"{key_prefix}_flag_bronch")

    return {
        "sputum": sputum,
        "wheeze": wheeze,
        "constipation": constipation,
        "flag_adeno": flag_adeno,
        "flag_rsv": flag_rsv,
        "flag_para": flag_para,
        "flag_bronchiolitis": flag_bronchiolitis,
    }


def render_symptom_explain_peds(
    *,
    stool: str,
    fever: str,
    persistent_vomit: bool,
    oliguria: bool,
    cough: str,
    nasal: str,
    eye: str,
    abd_pain: bool,
    ear_pain: bool,
    rash: bool,
    hives: bool,
    migraine: bool,
    hfmd: bool,
    max_temp: Optional[float] = None,
    # 신규 인자
    sputum: str = "없음",
    wheeze: str = "없음",
    constipation: str = "없음",
    flag_adeno: bool = False,
    flag_rsv: bool = False,
    flag_para: bool = False,
    flag_bronchiolitis: bool = False,
    age_years: Optional[float] = None,
) -> Dict[str, Tuple[List[str], List[str]]]:
    """
    Render caregiver explanations for selected symptoms and return compiled dict.
    Each dict value is a tuple: (home_tips, when_to_visit)
    """
    tips: Dict[str, Tuple[List[str], List[str]]] = {}
    fever_threshold = 38.5
    er_threshold = 39.0

    # 발열
    if fever != "없음":
        t = [
            "체온은 같은 부위에서 재세요(겨드랑이↔이마 혼용 금지).",
            "미온수(미지근한 물) 닦기, 얇은 옷 입히기.",
            "아세트아미노펜(APAP) ≥ 4시간, 이부프로펜(IBU) ≥ 6시간 간격 준수.",
            "수분 섭취를 늘리고, 활동량은 줄여 휴식해요.",
        ]
        w = [
            f"**{fever_threshold}℃ 이상 지속**되거나 **{er_threshold}℃ 이상**이면 의료진 상담.",
            "경련, 지속 구토/의식저하, 발진 동반 고열이면 즉시 병원.",
            "3~5일 이상 발열 지속 시 진료 권장.",
        ]
        if max_temp is not None:
            try:
                mt = float(max_temp)
            except Exception:
                mt = None
            if mt is not None:
                if mt >= er_threshold:
                    w.insert(0, f"현재 최고 체온 **{mt:.1f}℃** → **즉시 병원 권고**.")
                elif mt >= fever_threshold:
                    w.insert(0, f"현재 최고 체온 **{mt:.1f}℃** → 해열/수분 보충 후 **면밀 관찰**.")
        tips["발열"] = (t, w)

    # 호흡기(가래/쌕쌕 포함)
    if cough != "없음" or nasal != "없음" or sputum != "없음" or wheeze != "없음":
        t = [
            "가습·통풍·미온수 샤워 등으로 점액 배출을 돕습니다.",
            "코막힘 심하면 생리식염수 분무/흡인기로 콧물을 제거합니다.",
            "수면 시 머리 쪽을 약간 높여 줍니다.",
        ]
        if sputum in ["누런/진득", "초록/끈적"]:
            t.append("진득/초록 가래일수록 **수분 섭취**와 **실내 가습**이 도움이 됩니다.")
        if wheeze in ["보통", "심함"]:
            t.append("쌕쌕거림이 들리면 **흥분/울음을 줄이고**, 조용한 환경에서 휴식하세요.")
        w = [
            "숨이 차 보이거나, 입술이 퍼렇게 보이면 즉시 병원.",
            "가슴함몰/늑간함몰, 호흡 수가 빠른 경우 진료 필요.",
        ]
        tips["호흡기(기침/콧물/가래/쌕쌕)"] = (t, w)

    # 장 증상
    if stool != "없음" or persistent_vomit or oliguria:
        t = [
            "ORS 용액으로 5~10분마다 **소량씩 자주** 먹이기(토하면 10~15분 쉬고 재시도).",
            "기름진 음식·생야채·우유는 일시적으로 줄이기.",
            "항문 주위는 미온수 세정 후 완전 건조, 필요 시 보습막(연고) 얇게.",
        ]
        w = [
            "혈변/검은변, 심한 복통·지속 구토, **2시간 이상 소변 없음**이면 병원.",
            "탈수 의심(눈물 감소, 입마름, 축 처짐) 시 진료.",
        ]
        tips["장 증상(설사/구토/소변감소)"] = (t, w)

    # 변비
    if constipation != "없음":
        t = [
            "미지근한 물을 자주, 채소·과일·통곡물 등 **섬유소**를 **천천히** 늘립니다.",
            "가능한 범위에서 **걷기/가벼운 스트레칭**으로 장 운동을 돕습니다.",
            "식후 15~30분에 **변기 앉기 습관**을 매일 같은 시간에 들입니다.",
            "과도한 우유/치즈, 과자류 위주의 식사는 줄입니다.",
        ]
        w = [
            "**혈변/검은 변**, 심한 복통·구토 동반, **1주 이상 지속** 시 병원 상담.",
            "항문열 상처 의심 시 진료.",
        ]
        tips["변비 관리(보호자용)"] = (t, w)

    # 눈/복통/귀/피부/두통/수족구
    if eye != "없음":
        tips["눈 증상"] = (
            ["눈곱은 끓였다 식힌 미온수로 안쪽→바깥쪽 닦기(1회 1거즈).", "손 위생 철저, 수건/베개 공유 금지."],
            ["빛 통증/눈 붓기/고열 동반 시 진료.", "농성 분비물과 고열 동반 시 병원."],
        )
    if abd_pain:
        tips["복통"] = (
            ["복부 따뜻하게, 튀김/매운맛 일시 제한.", "통증 위치·시간·식사/배변 연관성 기록."],
            ["우하복부 지속 통증·보행 악화·구토/발열 동반 시 즉시 진료(충수염 감별).", "복부 팽만·혈변/흑변 동반 시 병원."],
        )
    if ear_pain:
        tips["귀 통증(중이염 의심)"] = (
            ["눕기 불편 시 머리 살짝 높이기.", "코막힘 동반 시 생리식염수/가습으로 비염 관리."],
            ["고열/구토 동반, 48시간 이상 통증 지속 시 진료.", "귀 뒤 붓고 심한 통증이면 즉시 병원."],
        )
    if rash or hives:
        tips["피부(발진/두드러기)"] = (
            ["시원한 환경, 땀/마찰 줄이기, 보습제 도포.", "의심 음식/약물은 중단 후 의료진 상의."],
            ["얼굴·입술·혀 붓기/호흡곤란/전신 두드러기 → 즉시 병원.", "수포/고열 동반 전신 발진은 진료."],
        )
    if migraine:
        tips["두통/편두통"] = (
            ["어두운 조용한 곳에서 휴식, 수분 보충.", "해열·진통제 간격 준수(성분 중복 주의)."],
            ["'번개두통', 신경학적 이상(구음장애/편측마비/경련) 시 즉시 병원.", "점점 심해지며 구토/시야 이상 동반 시 진료."],
        )
    if hfmd:
        tips["수족구 의심"] = (
            ["입안 통증 시 차갑거나 미지근한 부드러운 음식.", "수분 보충, 부드러운 양치로 구강 위생 유지."],
            ["침 흘림/섭취 거부로 거의 못 먹으면 병원.", "고열 3일+, 무기력 심하면 진료."],
        )

    # 저호중구 식품 안전
    anc_val = None
    try:
        anc_str = str(st.session_state.get("labs_dict", {}).get("ANC", ""))
        anc_val = float(anc_str.replace(",", "."))
    except Exception:
        anc_val = None
    if anc_val is not None and anc_val < 1000:
        tips["저호중구 음식 안전"] = (
            ["생야채/껍질 과일은 피하고 **완전 가열** 후 섭취.", "남은 음식은 **2시간 이후 섭취 비권장**, 멸균·살균 식품 권장."],
            ["38.0℃ 이상 발열 시 바로 병원 연락(38.5℃/39℃ 이상은 상위 조치)."],
        )

    # 바이러스/질환 패널
    age_m: Optional[float] = None
    if age_years is not None:
        try:
            age_m = float(age_years) * 12.0
        except Exception:
            age_m = None

    if flag_bronchiolitis or (wheeze in ["보통", "심함"] and (age_m is not None and age_m < 24)):
        tips["모세기관지염(브론키올리티스) 의심"] = (
            [
                "주로 **영/유아**에서 바이러스로 발생. 쌕쌕/가슴함몰이 보일 수 있어요.",
                "코가 막히면 **생리식염수** 후 흡인기로 코 청소를 자주 해주세요.",
                "수분 섭취, 휴식, 울음/흥분 줄이기가 중요해요.",
            ],
            [
                "호흡이 빨라지거나 **가슴함몰/청색증** 보이면 **즉시 병원**.",
                "수유/수분 섭취가 크게 줄면 탈수 위험 → 병원.",
            ],
        )

    if flag_rsv:
        tips["RSV(호흡기세포융합바이러스) 의심"] = (
            [
                "영·유아 **하기도 감염**의 흔한 원인. 콧물/기침 뒤에 쌕쌕이 생길 수 있어요.",
                "코 청소, 가습, 수분 보충이 가장 중요합니다.",
            ],
            [
                "호흡부전 징후(청색증/함몰/숨찬 표정)면 **응급평가**.",
                "미숙아/심폐질환 기저가 있으면 더 낮은 역치로 병원 상담.",
            ],
        )

    if flag_adeno:
        tips["아데노바이러스 의심"] = (
            [
                "고열과 **결막염/인후통/설사**가 함께 올 수 있어요.",
                "손 씻기, 수건/식기 구분 등 **전파 차단**이 중요합니다.",
            ],
            [
                "고열이 **3일 이상** 지속, **탈수**나 무기력 심하면 병원.",
                "심한 안통/눈부심(광과민) 있으면 진료.",
            ],
        )

    if flag_para:
        tips["파라인플루엔자(크루프) 의심"] = (
            [
                "**짖는 듯한 기침(개짖는 소리)**, 쉰목소리, 밤에 심해지는 **크루프** 양상일 수 있어요.",
                "따뜻한 김/샤워실, 또는 바깥 **차가운 공기**가 일시적으로 도움이 되기도 합니다.",
            ],
            [
                "**안정 시에도 쌕쌕/흡기 시 쇳소리(스트리도르)**가 들리면 **즉시 병원**.",
                "호흡곤란/침흘림/식이 불가 시 응급평가.",
            ],
        )

    # 화면 렌더
    compiled = {}
    if tips:
        with st.expander("👪 증상별 보호자 설명", expanded=False):
            for k, (t, w) in tips.items():
                st.markdown(f"### {k}")
                if t:
                    st.markdown("**가정 관리 팁**")
                    for x in t:
                        st.markdown(f"- {x}")
                if w:
                    st.markdown("**병원 방문 기준**")
                    for x in w:
                        st.markdown(f"- {x}")
                st.markdown("---")
        compiled = tips

    st.session_state["peds_explain"] = compiled
    return compiled


def build_peds_notes(
    *,
    stool: str,
    fever: str,
    persistent_vomit: bool,
    oliguria: bool,
    cough: str,
    nasal: str,
    eye: str,
    abd_pain: bool,
    ear_pain: bool,
    rash: bool,
    hives: bool,
    migraine: bool,
    hfmd: bool,
    duration: Optional[str] = None,
    score: Optional[Dict[str, float]] = None,
    max_temp: Optional[float] = None,
    red_seizure: bool = False,
    red_bloodstool: bool = False,
    red_night: bool = False,
    red_dehydration: bool = False,
    # 신규 인자
    sputum: str = "없음",
    wheeze: str = "없음",
    constipation: str = "없음",
    flag_adeno: bool = False,
    flag_rsv: bool = False,
    flag_para: bool = False,
    flag_bronchiolitis: bool = False,
) -> str:
    """
    Summarize pediatric symptoms into a human-readable text block (report/notes).
    """
    lines: List[str] = []
    if duration:
        lines.append(f"[지속일수] {duration}")
    if max_temp is not None:
        try:
            lines.append(f"[최고 체온] {float(max_temp):.1f}℃")
        except Exception:
            lines.append(f"[최고 체온] {max_temp}")

    sx: List[str] = []
    if fever != "없음":
        sx.append(f"발열:{fever}")
    if cough != "없음":
        sx.append(f"기침:{cough}")
    if nasal != "없음":
        sx.append(f"콧물:{nasal}")
    if stool != "없음":
        sx.append(f"설사:{stool}")
    if sputum != "없음":
        sx.append(f"가래:{sputum}")
    if wheeze != "없음":
        sx.append(f"쌕쌕:{wheeze}")
    if constipation != "없음":
        sx.append(f"변비:{constipation}")
    if eye != "없음":
        sx.append(f"눈:{eye}")
    if persistent_vomit:
        sx.append("지속 구토")
    if oliguria:
        sx.append("소변량 급감")
    if abd_pain:
        sx.append("복통/배마사지 거부")
    if ear_pain:
        sx.append("귀 통증")
    if rash:
        sx.append("발진/두드러기")
    if hives:
        sx.append("알레르기 의심")
    if migraine:
        sx.append("편두통 의심")
    if hfmd:
        sx.append("수족구 의심")

    flags: List[str] = []
    if flag_adeno:
        flags.append("아데노 의심")
    if flag_rsv:
        flags.append("RSV 의심")
    if flag_para:
        flags.append("파라인플루엔자 의심")
    if flag_bronchiolitis:
        flags.append("모세기관지염 의심")
    if flags:
        lines.append("[질환 추정] " + ", ".join(flags))

    if red_seizure:
        lines.append("[위험 징후] 경련/의식저하")
    if red_bloodstool:
        lines.append("[위험 징후] 혈변/검은변")
    if red_night:
        lines.append("[위험 징후] 야간 악화/새벽 악화")
    if red_dehydration:
        lines.append("[위험 징후] 탈수 의심(눈물 감소/구강 건조/소변 급감)")

    if sx:
        lines.append("[증상] " + ", ".join(sx))

    if isinstance(score, dict):
        top3 = sorted(score.items(), key=lambda x: x[1], reverse=True)[:3]
        top3 = [(k, v) for k, v in top3 if v > 0]
        if top3:
            lines.append("[상위 점수] " + " / ".join([f"{k}:{v}" for k, v in top3]))

    if not lines:
        lines.append("(특이 소견 없음)")

    return "\n".join(lines)
