# -*- coding: utf-8 -*-
"""
peds_guide.py — Pediatric helper module (score-based caregiver guidance, KST examples)
Exports:
- render_caregiver_notes_peds
- render_symptom_explain_peds
- build_peds_notes
"""

from typing import Optional, Dict, Tuple, List
import streamlit as st

def wkey(x):
    try:
        return f"{x}_{st.session_state.get('_uid','')}".strip('_')
    except Exception:
        return str(x)

__all__ = ["render_caregiver_notes_peds","render_symptom_explain_peds","build_peds_notes"]

# -------- Pediatric helpers (weight-based dosing, ORS) --------
def _get_age_years():
    try:
        import streamlit as st
        v = st.session_state.get(wkey("age_years"), None)
        if v is None:
            return None
        return float(str(v).replace(",", "."))
    except Exception:
        return None

def _get_weight_kg():
    try:
        import streamlit as st
        v = st.session_state.get(wkey("weight_kg"), None)
        if v is None:
            return None
        w = float(str(v).replace(",", "."))
        return w if w > 0 else None
    except Exception:
        return None

def apap_ibuprofen_guidance_kst():
    """
    Return detailed APAP/IBU guidance strings, optionally weight-based if weight_kg exists in session state.
    """
    wt = _get_weight_kg()
    age_y = _get_age_years()
    apap_range = "아세트아미노펜(APAP) **10–15 mg/kg** 4–6시간 간격, **하루 최대 60 mg/kg (절대 4회 초과 금지)**"
    ibu_range  = "이부프로펜(IBU) **5–10 mg/kg** 6–8시간 간격, **하루 최대 40 mg/kg** (⚠️ **생후 6개월 미만 금지**, 탈수·신장질환 주의)"
    kst_examples = "예시(한국시간): 10:00에 APAP → 다음 14:00 / 12:00에 IBU → 다음 18:00"

    dose_lines = [apap_range, ibu_range, kst_examples]

    if wt is not None:
        # single-dose ranges
        apap_min = round(wt*10)   # mg
        apap_max = round(wt*15)
        ibu_min  = round(wt*5)
        ibu_max  = round(wt*10)
        # daily max
        apap_dmax = round(wt*60)
        ibu_dmax  = round(wt*40)
        dose_lines.append(f"(체중 {wt:.1f}kg 기준) APAP 1회 **{apap_min}–{apap_max} mg**, 1일 최대 **{apap_dmax} mg**")
        dose_lines.append(f"(체중 {wt:.1f}kg 기준) IBU 1회 **{ibu_min}–{ibu_max} mg**, 1일 최대 **{ibu_dmax} mg**")
        if age_y is not None and age_y < 0.5:
            dose_lines.append("⚠️ 생후 6개월 미만: **IBU 금지**, APAP만 고려(의료진 지시 우선).")
    return dose_lines

def ors_guidance():
    """
    Return ORS prep and dosing lines (WHO recipe + sip plan).
    """
    lines = [
        "가정 ORS 배합(WHO 가정 레시피): **끓였다 식힌 물 1L + 설탕 평평한 티스푼 6 + 소금 평평한 1/2 티스푼**.",
        "상용 ORS는 라벨 지시대로. **과농도 금지**(더는 설탕/소금 추가하지 않기).",
        "복용법: 구토가 없으면 **5–10분마다 소량씩** 제공. 구토 시 **30분 휴식 후 매우 소량**으로 재시작.",
    ]
    wt = _get_weight_kg()
    if wt is not None:
        # WHO: rehydration 75 mL/kg in 4 hours, then 10 mL/kg per stool for maintenance
        rehyd = int(round(wt * 75))
        maint = int(round(wt * 10))
        lines.append(f"(체중 {wt:.1f}kg) 초기 4시간 **총 {rehyd} mL** 목표, 이후 설사 1회마다 **{maint} mL** 추가.")
    return lines


# -------- Score utilities --------
def _severity_band(total:int)->Tuple[str,str]:
    # Total-based quick band (tunable)
    if total >= 60:
        return "🚨 고위험", "즉시 병원/응급실 고려"
    if total >= 40:
        return "⚠️ 주의", "가까운 시간 내 병원 확인 권장"
    if total >= 20:
        return "🟡 관찰", "가정관리 + 경과 관찰"
    return "🟢 안정", "가정관리로 충분 (변화 시 재평가)"

def _top_drivers(score:Dict[str,int], k:int=3)->List[Tuple[str,int]]:
    return sorted([(k_,v) for k_,v in (score or {}).items() if v>0], key=lambda x: x[1], reverse=True)[:k]

# -------- Report text builder --------
def build_peds_notes(
    *, stool, fever, persistent_vomit, oliguria, cough, nasal, eye, abd_pain, ear_pain,
    rash, hives, migraine, hfmd, sputum=None, wheeze=None,
    duration=None, score:Optional[Dict[str,int]]=None, max_temp=None,
    red_seizure=False, red_bloodstool=False, red_night=False, red_dehydration=False,
    sore_throat=False, chest_ret=False, rr=None
) -> str:
    """소아 증상 선택을 요약하여 보고서용 텍스트를 생성."""
    lines = []
    if duration:
        lines.append(f"[지속일수] {duration}")
    sx = []
    if fever != "없음": sx.append(f"발열:{fever}")
    if max_temp not in (None, ""): 
        try: sx.append(f"최고체온:{float(max_temp):.1f}℃")
        except Exception: pass
    if cough != "없음": sx.append(f"기침:{cough}")
    if nasal != "없음": sx.append(f"콧물:{nasal}")
    if sputum and sputum != "없음": sx.append(f"가래:{sputum}")
    if wheeze and wheeze != "없음": sx.append(f"천명:{wheeze}")
    if sore_throat: sx.append("인후통")
    if chest_ret: sx.append("흉곽 함몰")
    if isinstance(rr, (int,float)) and rr: 
        try: sx.append(f"호흡수:{int(rr)}/분")
        except Exception: pass
    if stool != "없음": sx.append(f"설사:{stool}")
    if persistent_vomit: sx.append("지속 구토")
    if oliguria: sx.append("소변량 급감")
    if eye != "없음": sx.append(f"눈:{eye}")
    if abd_pain: sx.append("복통/배마사지 거부")
    if ear_pain: sx.append("귀 통증")
    if rash: sx.append("발진")
    if hives: sx.append("두드러기")
    if migraine: sx.append("편두통 의심")
    if hfmd: sx.append("수족구 의심")
    if red_seizure: sx.append("경련")
    if red_bloodstool: sx.append("혈변")
    if red_night: sx.append("밤중 악화")
    if red_dehydration: sx.append("탈수의심")
    if sx:
        lines.append(" · ".join(sx))

    # 점수 요약
    if score:
        total = sum(int(v) for v in score.values())
        flag, hint = _severity_band(total)
        tops = _top_drivers(score, 3)
        tops_str = " / ".join([f"{k} {v}" for k,v in tops]) if tops else "해당 없음"
        lines.append(f"[점수합] {total}점 — {flag} · {hint}")
        lines.append(f"[주요 원인] {tops_str}")
    return "\n".join(lines)

# -------- Caregiver explanations (score-aware) --------
def render_symptom_explain_peds(
    *, stool, fever, persistent_vomit, oliguria, cough, nasal, eye, abd_pain, ear_pain,
    rash, hives, migraine, hfmd, max_temp=None, sputum=None, wheeze=None,
    sore_throat=False, chest_ret=False, rr=None, score:Optional[Dict[str,int]]=None
):
    """선택된 증상에 대한 보호자 설명(가정 관리 팁 + 병원 방문 기준)을 상세 렌더 + 점수기반 보강."""
    tips = {}

    # --- 공통 상단: 점수 기반 프레임 ---
    total = sum(int(v) for v in (score or {}).values()) if score else 0
    band, band_hint = _severity_band(total)
    if score:
        with st.container(border=True):
            st.markdown(f"### 📊 현재 위험 요약: **{band}**")
            st.caption(band_hint)
            tops = _top_drivers(score, 3)
            if tops:
                st.markdown("**주요 기여도 TOP3**")
                for k, v in tops:
                    st.write(f"- {k} : {v}점")
            st.divider()

    # --- Fever ---
    if fever != "없음" or (max_temp not in (None, "")):
        t = [
            "같은 부위에서 재세요(겨드랑이↔이마 혼용 금지).",
            "미온수 닦기, 얇은 옷, 실내 환기.",
            "아세트아미노펜(APAP) 또는 이부프로펜(IBU) 간격 준수(APAP ≥ 4시간, IBU ≥ 6시간).",
            "수분 섭취를 늘리고 활동을 줄이기.",
            "예시(한국시간): 10:00에 APAP 15mg/kg → 다음 14:00 가능 / 12:00에 IBU 10mg/kg → 다음 18:00 가능.",
        ]
        w = [
            "39.0℃ 이상 지속, 처치에도 힘들어하거나 처짐 심하면 진료.",
            "경련/의식저하/호흡곤란 동반 시 즉시 병원.",
        ]
        tips["발열 관리"] = (t, w)
    try:
        _ay = _get_age_years()
    except Exception:
        _ay = None
    extra = []
    if _ay is not None and _ay < 0.25:
        extra.append("⚠️ **생후 3개월 미만**의 38.0℃ 이상 발열은 **응급 평가 권장** — 즉시 의료진과 상의/내원.")
    for dl in apap_ibuprofen_guidance_kst():
        extra.append(dl)
    if extra:
        tips["발열 관리"] = (t + extra, w)


    # --- URI / 독감 계열 ---
    if cough in ["조금","보통","심함"] or nasal in ["투명","진득","누런"]:
        t = [
            "코막힘 심하면 생리식염수 분무 후 비강 흡인.",
            "기침 심하면 활동 줄이고, 수분 소량 자주.",
        ]
        w = [
            "기침이 2주 이상 지속, 흉통/청색증/쌕쌕거림 동반 시 진료.",
        ]
        tips["상기도/독감 계열"] = (t, w)

    # --- Conjunctivitis/Adeno ---
    fever_high = False
    try:
        fever_high = (float(max_temp) >= 38.5) if max_temp not in (None, "") else (fever in ["38.5~39","39 이상"])
    except Exception:
        fever_high = (fever in ["38.5~39","39 이상"])

    if (eye in ["노랑-농성","양쪽"]) and fever_high:
        t = [
            "분비물은 안쪽→바깥쪽, 1회 1거즈로 닦기.",
            "손 위생 철저, 수건/베개 공유 금지, 일회용 티슈 사용.",
            "인후통 있으면 차가운/부드러운 음식 권장.",
            "목 통증 완화: 찬물·아이스크림 조금씩.",
            "수면 전 자극 음식 피하기.",
        ]
        w = [
            "고열이 3~4일 이상, 눈 통증·빛 통증 심하면 진료.",
            "탈수(구강건조·눈물감소)나 무기력 심하면 병원.",
        ]
        if sore_throat:
            t.append("인후통 동반: 휴식·수분·진통해열제 병행, 가글 습관 유지(처방 범위 내).")
        tips["아데노바이러스(인후결막열) 의심"] = (t, w)
    t.extend(["눈 분비물 가라앉을 때까지 **공용 수건/베개 금지**.", "증상 심할 땐 **등원/등교 보류** 권고(의료진 판단 우선)."])
    tips["아데노바이러스(인후결막열) 의심"] = (t, w)


    # --- RSV / Bronchiolitis ---
    # Age (years) from session if available
    try:
        _age_years = float(str(st.session_state.get(wkey("age_years"), 0)).replace(",", "."))
    except Exception:
        _age_years = None

    is_uri = (cough in ["조금","보통","심함"] or nasal in ["투명","진득","누런"])
    if (wheeze and wheeze != "없음") and is_uri:
        rsv_title = "RSV/모세기관지염 의심(특히 2세 미만)" if (_age_years is not None and _age_years <= 2.0) else "RSV/모세기관지염 의심"
        t = [
            "생리식염수 분무 후 비강 흡인으로 막힘 완화.",
            "작은 양을 자주 수분/수유.",
            "수면 시 머리 약간 높이고, 옆구리 체위 바꾸기.",
            "가정용 산소/네뷸라이저는 반드시 의료진 지시에 따르기.",
        ]
        w = [
            "호흡수 증가, 가슴 함몰(흉곽 함몰), 콧벌렁임, 청색증 보이면 즉시 응급실.",
            "먹는 양이 절반 이하, 탈수 징후 시 진료.",
        ]
        if chest_ret:
            w.insert(0, "흉곽 함몰 관찰됨 → **즉시 병원** 권장.")
        # Tachypnea by WHO
        rr_val = None
        try:
            rr_val = int(rr) if rr not in (None,"") else None
        except Exception:
            rr_val = None
        if rr_val is not None:
            thr = 30
            if _age_years is None: thr = 40
            else:
                if _age_years < (2/12): thr = 60
                elif _age_years < 1: thr = 50
                elif _age_years <= 5: thr = 40
                else: thr = 30
            if rr_val >= thr:
                w.insert(0, f"호흡수 {rr_val}/분 ≥ 연령 기준({thr}/분) → **응급 평가 필요**.")
        tips[rsv_title] = (t, w)
    t.extend(["수유/수분은 **소량·자주**로 피로 줄이기.", "실내 가습/미온수 목욕 등 **가습 환경** 유지(과도한 냉방 금지)."])
    tips[rsv_title] = (t, w)


    # --- GI / Dehydration ---
    if stool != "없음" or persistent_vomit or oliguria:
        t = [
            "OR S(WHO) 또는 전해질 음료를 소량·자주.",
            "구토 30분간 휴식 후, 5~10분 간격 극소량부터 재시도.",
            "소변/눈물/입마름·축 처짐 체크.",
        ]
        w = [
            "혈변/검은변, 심한 복통·지속 구토, 2시간 이상 무뇨 → 진료.",
            "탈수 의심(눈물 감소·구강건조·무기력) 시 병원.",
        ]
        tips["장 증상(설사/구토/소변감소)"] = (t, w)

    # 변비는 별도 조건으로 분리하여 선택된 경우에만 안내
    try:
        _stool_str = str(stool) if stool is not None else ""
    except Exception:
        _stool_str = ""
    if isinstance(_stool_str, str) and ("변비" in _stool_str):
        t_c = [
            "수분 섭취 늘리기, 섬유질(과일·야채) 보강.",
            "배변습관 일정화(식후 10~15분 변기 앉기), 무리한 힘주기 피하기.",
        ]
        w_c = [
            "복통 심함, 항문열상 의심, 체중감소·구토 동반 시 진료.",
        ]
        tips["변비 관리"] = (t_c, w_c)
    for _ln in ors_guidance():
        t.append(_ln)
    tips["장 증상(설사/구토/소변감소)"] = (t, w)



    # 변비는 별도 조건으로 분리하여 선택된 경우에만 안내
    try:
        _stool_str = str(stool) if stool is not None else ""
    except Exception:
        _stool_str = ""
    if isinstance(_stool_str, str) and ("변비" in _stool_str):
        t_c = [
            "수분 섭취 늘리기, 섬유질(과일·야채) 보강.",
            "배변습관 일정화(식후 10~15분 변기 앉기), 무리한 힘주기 피하기.",
        ]
        w_c = [
            "복통 심함, 항문열상 의심, 체중감소·구토 동반 시 진료.",
        ]
        tips["변비 관리"] = (t_c, w_c)
    # --- Chest pain / Dyspnea hard flags handled elsewhere ---

    # ---- Render tips ----
    for title, (t, w) in tips.items():
        with st.expander(f"👪 {title}", expanded=True):
            st.markdown("**가정 관리**")
            for x in t: st.markdown(f"- {x}")
            st.markdown("**병원/응급 기준**")
            for x in w: st.markdown(f"- {x}")

def render_caregiver_notes_peds(
    *, stool, fever, persistent_vomit, oliguria, cough, nasal, eye, abd_pain, ear_pain,
    rash, hives, migraine, hfmd, sputum=None, wheeze=None, max_temp=None,
    sore_throat=False, chest_ret=False, rr=None, score:Optional[Dict[str,int]]=None
):
    # 최고체온 안전 추출
    try:
        _mt_raw = st.session_state.get(wkey("cur_temp"))
        if max_temp in (None, "") and _mt_raw not in (None, ""):
            max_temp = float(str(_mt_raw).replace(",", "."))
    except Exception:
        pass

    # 점수 요약 텍스트(보고서용) 미리 생성
    rep_text = build_peds_notes(
        stool=stool, fever=fever, persistent_vomit=persistent_vomit, oliguria=oliguria,
        cough=cough, nasal=nasal, eye=eye, abd_pain=abd_pain, ear_pain=ear_pain,
        rash=rash, hives=hives, migraine=migraine, hfmd=hfmd, sputum=sputum, wheeze=wheeze,
        duration=st.session_state.get(wkey("p_dur"), None), score=score, max_temp=max_temp,
        red_seizure=st.session_state.get(wkey("p_red_seizure"), False),
        red_bloodstool=st.session_state.get(wkey("p_red_bloodstool"), False),
        red_night=st.session_state.get(wkey("p_red_night"), False),
        red_dehydration=st.session_state.get(wkey("p_red_dehydration"), False),
        sore_throat=sore_throat, chest_ret=chest_ret, rr=rr,
    )
    st.markdown("### 🧾 선택 요약")
    st.code(rep_text, language="text")
    st.caption("※ 이 안내는 참고용이며, 최종 판단은 의료진의 진료에 따릅니다.")

    # 상세 설명
    render_symptom_explain_peds(
        stool=stool, fever=fever, persistent_vomit=persistent_vomit, oliguria=oliguria,
        cough=cough, nasal=nasal, eye=eye, abd_pain=abd_pain, ear_pain=ear_pain,
        rash=rash, hives=hives, migraine=migraine, hfmd=hfmd, max_temp=max_temp,
        sputum=sputum, wheeze=wheeze, sore_throat=sore_throat, chest_ret=chest_ret, rr=rr, score=score
    )
