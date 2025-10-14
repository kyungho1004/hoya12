
# -*- coding: utf-8 -*-
import os

# ---- PIN resolve helper: pull from "별명#PIN" or any digits(4~8) in session_state ----
def resolve_pin_from_session(default="guest"):
    import re, os, json, streamlit as st
    # Try cached _pin first
    pin = st.session_state.get("_pin", "")
    if isinstance(pin, str) and pin.isdigit() and 4 <= len(pin) <= 8:
        return pin
    # Scan all session_state values (strings)
    for k, v in st.session_state.items():
        if isinstance(v, str):
            m = re.search(r'#(\d{4,8})$', v.strip())
            if m:
                st.session_state["_pin"] = m.group(1)
                return m.group(1)
            if v.strip().isdigit() and 4 <= len(v.strip()) <= 8:
                st.session_state["_pin"] = v.strip()
                return v.strip()
    # fallback
    st.session_state["_pin"] = default
    return default

# Ensure profile dir exists
def ensure_profile_dir():
    import os
    base = "/mnt/data/profile"
    try:
        os.makedirs(base, exist_ok=True)
    except Exception:
        pass
    return base

import datetime as dt
import pandas as pd
import streamlit as st
from textwrap import dedent

st.set_page_config(page_title="피수치 홈페이지 (합본 최종본)", layout="wide")

# -------- Helper: import modules safely & call-first utility --------
def _safe_import(name):
    try:
        return __import__(name)
    except Exception:
        return None

def _call_first(mod, names, *args, **kwargs):
    """Try to call the first existing attribute in names on module mod."""
    if not mod:
        return False
    for n in names:
        fn = getattr(mod, n, None)
        if callable(fn):
            try:
                fn(*args, **kwargs)
                return True
            except Exception as e:
                st.error(f"{mod.__name__}.{n} 실행 오류: {e}")
                return True  # found but errored: don't keep trying others
    return False

ui_results = _safe_import("ui_results")
onco_map = _safe_import("onco_map")
special_tests = _safe_import("special_tests")
lab_diet = _safe_import("lab_diet")
pdf_export = _safe_import("pdf_export")
branding = _safe_import("branding")
core_utils = _safe_import("core_utils")
peds_dose = _safe_import("peds_dose")
drug_db = _safe_import("drug_db")

def wkey(s: str) -> str:
    return f"w_{s}"

# ---------- Helper: Style ----------
def badge(level: str, text: str):
    if level == "good":
        st.success(text, icon="🟢")
    elif level == "warn":
        st.warning(text, icon="🟡")
    else:
        st.error(text, icon="🚨")

# ---------- Pediatric: caregiver explanations ----------
def render_symptom_explain_peds(*, nasal, cough, stool, fever, eye, phlegm, wheeze, max_temp=None):
    st.markdown("#### 보호자 설명")
    items = []
    if nasal != "없음":
        items.append("- **콧물**: 생리식염수 세척, 콧속 보습. 누런 콧물 지속/고열 동반 시 진료.")
    if cough != "없음":
        items.append("- **기침**: 따뜻한 물 소량 자주. 꿀(만 1세 이상). 호흡 곤란 시 즉시 병원.")
    if stool != "없음":
        items.append("- **설사**: 탈수 주의. ORS(경구 수액) 소량 자주. 혈변·고열·무기력 시 진료.")
    if fever != "없음":
        items.append("- **발열**: 미온수 닦기. 해열제는 필요 시만. 해열제 간격 준수(아세트아미노펜 ≥4h, 이부프로펜 ≥6h).")
    if eye != "없음":
        items.append("- **눈곱/결막**: 미온수로 부드럽게. 끈끈한 고름 지속·심한 충혈은 진료.")
    if wheeze in ["보통","심함"]:
        items.append("- **쌕쌕거림(천명)**: 가슴 함몰·청색증·호흡 곤란 시 **즉시 병원**.")
    if phlegm in ["보통","심함"]:
        items.append("- **가래**: 수분 섭취, 실내 환기. 가습 과도 사용 금지. 흉통/고열 지속 시 상담.")
    if max_temp is not None:
        items.append(f"- **최고 체온**: {max_temp:.1f}℃ (기록 기준)")
    if items:
        st.markdown("\n".join(items))
    else:
        st.markdown(dedent("""
        - **기본 관리**: 수분 섭취, 실내 환기, 충분한 휴식.
        - **해열제 안전 간격**: 아세트아미노펜 **4시간 이상**, 이부프로펜 **6시간 이상**.
        - **즉시 진료 신호**: 호흡 곤란/청색증/경련/의식저하, **혈변/검은변**, 탈수 소견(눈물↓·입마름).
        """).strip())

def render_constipation_quickguide():
    with st.expander("🚽 변비 관리(보호자용)", expanded=False):
        st.markdown(dedent("""
        - **수분 섭취 늘리기**: 미지근한 물을 자주. 섬유소(과일·채소·통곡물)는 **천천히** 늘리기.
        - **활동 유도**: 가능한 범위에서 **걷기/가벼운 스트레칭**.
        - **배변 습관**: 매일 같은 시간(식후 15~30분) **화장실 앉기**.
        - **피해야 할 것**: 과도한 우유/치즈, 과자류 위주 식사.
        - **경고 신호**: **혈변/검은변**, 심한 복통·구토 동반, **1주 이상 지속** 시 병원 상담.
        """).strip())

def render_skin_care_quickguide():
    with st.expander("🧴 피부 관리(보호자용)", expanded=False):
        st.markdown(dedent("""
        - **미온수 샤워** 후 문지르지 말고 톡톡. **무향 보습제**를 샤워 후 3분 내 충분히.
        - **손톱 정리**로 긁힘 예방. **햇빛 차단**(모자/얇은 긴소매, 필요시 저자극 선크림).
        - **피해야 할 것**: 때타월, 알코올 스왑 남용, 강한 향/자극 제품.
        - **경고 신호**: **물집/심한 진물/발열 동반 발진**은 병원 상담.
        """).strip())

def render_caregiver_notes_peds(*, nasal, cough, stool, fever, eye, phlegm, wheeze, max_temp=None):
    # 요약 저장
    sx = []
    for label, val in [("콧물", nasal), ("기침", cough), ("설사", stool), ("발열", fever), ("눈곱/결막", eye)]:
        if val != "없음":
            sx.append(f"{label}:{val}")
    if phlegm != "없음":
        sx.append(f"가래:{phlegm}")
    if wheeze != "없음":
        sx.append(f"쌕쌕거림:{wheeze}")
    if max_temp is not None:
        sx.append(f"최고체온:{max_temp:.1f}℃")
    note = "- " + ", ".join(sx) if sx else ""
    st.session_state["peds_notes"] = note
    render_symptom_explain_peds(
        nasal=nasal, cough=cough, stool=stool, fever=fever, eye=eye,
        phlegm=phlegm, wheeze=wheeze, max_temp=max_temp
    )

# ---------- Tabs ----------
tabs = ["홈","혈액수치","암/항암","소아","특수검사","보고서","그래프"]
t_home, t_labs, t_onco, t_peds, t_special, t_report, t_graph = st.tabs(tabs)

with t_home:
    st.markdown("### 피수치 홈페이지 (합본 최종본)")
    _call_first(branding, ["render_deploy_banner","render_header"])
    st.caption("소아(가래/천명/가이드), 보고서(소아 요약), 그래프 탭 분리를 포함한 최종 합본입니다.")

with t_labs:
    st.markdown("### 혈액수치")
    ran = _call_first(ui_results, [
        "results_only_after_analyze",
        "render_labs",
        "render_results",
        "main",
        "render",
    ])
    if not ran:
        st.info("혈액수치 UI 엔트리를 찾지 못했습니다. ui_results.py의 엔트리 함수명을 알려주면 고정 연결해 드릴게요.")

with t_onco:
    st.markdown("### 암/항암")
    ran = _call_first(onco_map, [
        "build_onco_map",
        "render_onco",
        "dx_display",   # 일부 레거시에선 뷰어 역할
        "main",
        "render",
    ])
    if not ran:
        st.info("암/항암 UI 엔트리를 찾지 못했습니다. onco_map.py의 엔트리 함수명을 알려주면 고정 연결해 드릴게요.")

with t_peds:
    st.markdown("### 소아 증상 기반 점수 + 보호자 설명 + 해열제 계산")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        nasal = st.selectbox("콧물", ["없음","조금","보통","심함"], key=wkey("p_nasal"))
    with c2:
        cough = st.selectbox("기침", ["없음","조금","보통","심함"], key=wkey("p_cough"))
    with c3:
        stool = st.selectbox("설사", ["없음","조금","보통","심함"], key=wkey("p_stool"))
    with c4:
        fever = st.selectbox("발열", ["없음","조금","보통","심함"], key=wkey("p_fever"))
    with c5:
        eye = st.selectbox("눈곱/결막", ["없음","조금","보통","심함"], key=wkey("p_eye"))

    # 신규: 가래/천명 한 묶음
    r1a, r1b = st.columns(2)
    with r1a:
        phlegm = st.selectbox("가래(객담)", ["없음","조금","보통","심함"], key=wkey("p_phlegm"))
    with r1b:
        wheeze = st.selectbox("쌕쌕거림(천명)", ["없음","조금","보통","심함"], key=wkey("p_wheeze"))

    st.divider()
    colA, colB = st.columns([2,1])
    with colA:
        dur = st.selectbox("증상 지속일수", ["선택 안 함","<1일","1-3일","4-7일",">7일"], key=wkey("p_dur"))
        max_temp = st.number_input("최고 체온(℃)", value=36.5, step=0.1, key=wkey("p_maxtemp"))
    with colB:
        danger1 = st.checkbox("경련/의식저하", key=wkey("p_d1"))
        danger2 = st.checkbox("혈변/검은변", key=wkey("p_d2"))
        danger3 = st.checkbox("야간/새벽 악화", key=wkey("p_d3"))
        danger4 = st.checkbox("탈수 의심(눈물·입마름)", key=wkey("p_d4"))

    # 점수
    score = {"전반 안정":0, "호흡기 주의":0, "소화기 주의":0, "응급 경고":0}
    map4 = {"없음":0,"조금":10,"보통":20,"심함":35}
    score["호흡기 주의"] += map4.get(nasal,0) + map4.get(cough,0) + map4.get(eye,0)
    score["소화기 주의"] += map4.get(stool,0)
    if wheeze in ["조금","보통","심함"]:
        score["호흡기 주의"] += {"조금":15,"보통":25,"심함":40}[wheeze]
    if phlegm in ["보통","심함"]:
        score["호흡기 주의"] += {"보통":10,"심함":15}[phlegm]
    if any([danger1, danger2, danger4]) or (fever in ["보통","심함"] and max_temp >= 39.0):
        score["응급 경고"] += 50

    if score["응급 경고"] >= 50:
        badge("bad", "호흡곤란/탈수/고열 지속 등 **즉시 진료 필요** 신호입니다.")
    elif score["호흡기 주의"] + score["소화기 주의"] >= 45:
        badge("warn", "현재는 **주의** 단계입니다. 악화 시 상위 단계 조치를 따르세요.")
    else:
        badge("good", "현재는 비교적 안정 신호입니다. 악화 시 바로 상위 단계 조치를 따르세요.")

    render_caregiver_notes_peds(
        nasal=nasal, cough=cough, stool=stool, fever=fever, eye=eye,
        phlegm=phlegm, wheeze=wheeze, max_temp=max_temp
    )

    st.divider()
    render_constipation_quickguide()
    render_skin_care_quickguide()

    # (선택) 해열제/소아용량 모듈이 있으면 표시
    _call_first(peds_dose, ["render_peds_dose","render","main"])

with t_special:
    st.markdown("### 특수검사")
    ran = _call_first(special_tests, [
        "special_tests_ui",
        "render_special_tests",
        "main",
        "render",
    ])
    if not ran:
        st.info("특수검사 UI 엔트리를 찾지 못했습니다. special_tests.py의 엔트리 함수명을 알려주면 고정 연결해 드릴게요.")

with t_report:
    st.markdown("### 보고서 미리보기")
    lines = []
    lines.append("# 보고서")
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    lines.append(f"- 생성시각: {now}")
    lines.append("")
    peds_notes_val = st.session_state.get("peds_notes","").strip()
    if peds_notes_val:
        lines.append("## 👶 소아 증상 요약")
        lines.append(peds_notes_val)
        lines.append("")
    md = "\n".join(lines)
    st.markdown(md)
    cols = st.columns(2)
    with cols[0]:
        st.download_button("보고서(.md) 다운로드", md.encode("utf-8"), file_name="report.md")
    with cols[1]:
        if pdf_export and hasattr(pdf_export, "export_md_to_pdf"):
            try:
                pdf_bytes = pdf_export.export_md_to_pdf(md)
                st.download_button("보고서(.pdf) 다운로드", data=pdf_bytes, file_name="report.pdf", mime="application/pdf")
            except Exception as e:
                st.caption(f"PDF 변환 실패: {e}")
        else:
            st.caption("PDF 변환 모듈이 없어서 .md만 다운로드됩니다.")

with t_graph:
    st.markdown("### 📈 그래프")
    base = "./graphs"
    os.makedirs(base, exist_ok=True)
    st.caption(f"CSV 폴더: {os.path.abspath(base)}")
    files = [f for f in os.listdir(base) if f.lower().endswith(".csv")]
    if not files:
        st.info("표시할 CSV가 없습니다. 폴더에 WBC/Hb/PLT/ANC/CRP 컬럼이 포함된 CSV를 넣어주세요.")
    else:
        pick = st.selectbox("파일 선택", files, key=wkey("graph_file"))
        import pandas as _pd
        df = _pd.read_csv(os.path.join(base, pick))
        st.caption("열에 WBC, Hb, PLT, ANC, CRP가 있으면 자동 표시합니다.")
        for col in ["WBC","Hb","PLT","ANC","CRP"]:
            if col in df.columns:
                st.line_chart(df[[col]], height=220)

st.caption("© 피수치 홈페이지 프로젝트 - 합본 최종본")
