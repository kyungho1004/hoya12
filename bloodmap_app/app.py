
# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import date, timedelta, timezone, datetime

from core_utils import nickname_pin, clean_num, schedule_block
from drug_db import DRUG_DB, ensure_onco_drug_db, display_label
from onco_map import build_onco_map, auto_recs_by_dx, dx_display
from ui_results import results_only_after_analyze, render_adverse_effects, collect_top_ae_alerts
from lab_diet import lab_diet_guides
from peds_profiles import get_symptom_options
from peds_dose import acetaminophen_ml, ibuprofen_ml
from pdf_export import export_md_to_pdf

from carelog_ref import render as render_carelog, load as carelog_load, analyze_symptoms
from antipyretic_guard_ref import render_guard as render_antipy_guard
from metrics_ref import bump as bump_metrics

ensure_onco_drug_db(DRUG_DB)
ONCO_MAP = build_onco_map()

KST = timezone(timedelta(hours=9))
st.set_page_config(page_title="BloodMap — p10-ref3 (모바일 1열)", page_icon="🩸", layout="centered")
st.title("BloodMap — p10 (모바일 최적화)")
st.caption("v2025-09-22 p10-ref3")

nick, pin, key = nickname_pin()
uid = f"{nick}_{pin}" if (nick and pin) else "guest_0000"

with st.sidebar:
    try:
        d = bump_metrics(uid)
        st.markdown("### 👥 방문자")
        st.caption(f"오늘 {d.get('today','—')} · 총 {d.get('total_visits',0)} · 고유 {len(d.get('unique',{}))}")
    except Exception as e:
        st.caption(f"방문자 통계 오류: {e}")

mode = st.radio("모드 선택", ["암", "일상", "소아"], horizontal=True, key=f"mode_{uid}")
place_carelog_under_special = st.toggle("특수해석 밑에 케어로그 표시", value=True, key=f"carelog_pos_{uid}")
cols_per_row = st.select_slider("입력칸 배열(모바일 1열 추천)", options=[1,2,3,4], value=1, key=f"cols_{uid}")

def labs_block(uid:str, cols_per_row:int=1):
    st.markdown("### 2) 피수치 입력 (숫자만) — 한글 주석 포함")
    LABS = [
        ("WBC","WBC(백혈구)"),
        ("Hb","Hb(혈색소)"),
        ("PLT","PLT(혈소판)"),
        ("ANC","ANC"),
        ("Ca","Ca(칼슘)"),
        ("Na","Na(나트륨)"),
        ("K","K(칼륨)"),
        ("Alb","Alb(알부민)"),
        ("Glu","Glu(혈당)"),
        ("AST","AST(간수치)"),
        ("ALT","ALT(간수치)"),
        ("Cr","Cr(크레아티닌)"),
        ("CRP","CRP(C-반응단백)"),
        ("Cl","Cl(염소)"),
        ("UA","UA(요산)"),
        ("T.B","T.B(총빌리루빈)"),
        ("CR","CR(별칭/이전 표기)"),
    ]
    vals = {}
    # Single-column (or chosen columns per row)
    for i, (code, label) in enumerate(LABS):
        if cols_per_row == 1:
            vals[code] = clean_num(st.text_input(label, key=f"lab_{code}_{uid}"))
        else:
            if i % cols_per_row == 0:
                cols = st.columns(cols_per_row)
            with cols[i % cols_per_row]:
                vals[code] = clean_num(st.text_input(label, key=f"lab_{code}_{uid}"))
    # Alias merge
    if vals.get("CR") is not None and (vals.get("Cr") is None):
        vals["Cr"] = vals["CR"]
    return vals

# === 암 모드 ===
if mode == "암":
    st.markdown("### 1) 암 선택")
    group = st.selectbox("암 카테고리", list(ONCO_MAP.keys()) or ["혈액암"], key=f"oncog_{uid}")
    dx_options = list(ONCO_MAP.get(group, {}).keys()) or ["직접 입력"]
    dx = st.selectbox("진단(영문+한글)", dx_options, key=f"oncodx_{uid}", format_func=lambda x: dx_display(group, x) if x else x)
    if dx == "직접 입력": dx = st.text_input("진단(직접 입력)", key=f"oncodx_manual_{uid}")
    if dx: st.caption(dx_display(group, dx))

    from drug_db import picklist, key_from_label
    rec_local = auto_recs_by_dx(group, dx, DRUG_DB, ONCO_MAP)
    c1,c2,c3 = st.columns(3)
    with c1: user_chemo_labels    = st.multiselect("항암제(개인)", picklist(rec_local.get("chemo", [])), key=f"chemo_{uid}")
    with c2: user_targeted_labels = st.multiselect("표적/면역(개인)", picklist(rec_local.get("targeted", [])), key=f"targeted_{uid}")
    with c3: user_abx_labels      = st.multiselect("항생제(개인)", picklist(rec_local.get("abx", [])), key=f"abx_{uid}")
    user_chemo    = [key_from_label(x) for x in user_chemo_labels]
    user_targeted = [key_from_label(x) for x in user_targeted_labels]
    user_abx      = [key_from_label(x) for x in user_abx_labels]

    labs = labs_block(uid, cols_per_row)

    # 특수검사 (optional)
    lines_blocks = []
    try:
        from special_tests import special_tests_ui
        sp_lines = special_tests_ui()
    except Exception:
        sp_lines = []
    if sp_lines: lines_blocks.append(("특수검사 해석", sp_lines))

    # 케어로그
    care_lines = []; care_entries = []
    if place_carelog_under_special:
        st.divider(); st.subheader("케어 · 해열제")
        care_lines, care_entries = render_carelog(uid, nick)
        render_antipy_guard({"age": 30, "weight": 60}, {"PLT": labs.get("PLT")}, care_entries)

    if st.button("🔎 해석하기", key=f"analyze_cancer_{uid}"):
        st.session_state["analyzed"] = True
        st.session_state["analysis_ctx"] = {
            "mode":"암","group":group,"dx":dx,"dx_label": dx_display(group, dx),
            "labs": labs, "user_chemo": user_chemo, "user_targeted": user_targeted, "user_abx": user_abx,
            "lines_blocks": lines_blocks, "care_lines": care_lines, "triage_high": analyze_symptoms(care_entries)[0] if care_entries else []
        }
    schedule_block()

# === 일상 / 소아 ===
else:
    who = st.radio("대상", ["소아","성인"], horizontal=True, key=f"who_{uid}") if mode=="일상" else "소아"
    if who == "소아":
        from peds_rules import predict_from_symptoms, triage_advise
        opts = get_symptom_options("기본")
        eye_opts = opts.get("눈꼽", ["없음","맑음","노랑-농성","가려움 동반","한쪽","양쪽"])
        c1,c2,c3,c4,c5,c6 = st.columns(6)
        with c1: nasal = st.selectbox("콧물", opts["콧물"], key=f"nasal_{uid}")
        with c2: cough = st.selectbox("기침", opts["기침"], key=f"cough_{uid}")
        with c3: diarrhea = st.selectbox("설사(횟수/일)", opts["설사"], key=f"diarr_{uid}")
        with c4: vomit = st.selectbox("구토(횟수/일)", ["없음","1~2회","3~4회","4~6회","7회 이상"], key=f"vomit_{uid}")
        with c5: temp = st.number_input("체온(℃)", min_value=0.0, step=0.1, value=0.0, key=f"temp_{uid}")
        with c6: eye = st.selectbox("눈꼽", eye_opts, key=f"eye_{uid}")
        age_m = st.number_input("나이(개월)", min_value=0, step=1, key=f"age_m_{uid}")
        weight = st.number_input("체중(kg)", min_value=0.0, step=0.1, key=f"wt_{uid}")
        apap_ml, _ = acetaminophen_ml(age_m, weight or None); ibu_ml, _ = ibuprofen_ml(age_m, weight or None)
        st.caption(f"APAP 평균 1회분: {apap_ml} ml · IBU 평균 1회분: {ibu_ml} ml")

        # 증상 기반 예측/트리아지
        from peds_rules import predict_from_symptoms, triage_advise
        symptoms = {"콧물":nasal,"기침":cough,"설사":diarrhea,"구토":vomit,"체온":temp,"눈꼽":eye}
        preds = predict_from_symptoms(symptoms, temp, age_m)
        st.markdown("#### 🤖 증상 기반 자동 추정")
top = sorted(preds or [], key=lambda x: x.get('score',0), reverse=True)[:3]
for p in top:
    label = p.get('label')
    score = p.get('score',0)
    pct = f"{int(round(float(score)))}%" if score is not None else ""
    st.write(f"- **{label}** · 신뢰도 {pct}")
        st.info(triage_advise(temp, age_m, diarrhea))

        care_lines = []; care_entries = []
        if place_carelog_under_special:
            st.divider(); st.subheader("케어 · 해열제")
            care_lines, care_entries = render_carelog(uid, nick)
            render_antipy_guard({"age": int(age_m/12), "weight": weight}, {}, care_entries)

        if st.button("🔎 해석하기", key=f"analyze_daily_child_{uid}"):
            st.session_state["analyzed"] = True
            st.session_state["analysis_ctx"] = {
                "mode":"일상","who":"소아",
                "symptoms":{"콧물":nasal,"기침":cough,"설사":diarrhea,"구토":vomit,"체온":temp,"눈꼽":eye},
                "diet_lines": lab_diet_guides({}, heme_flag=False),
                "care_lines": care_lines, "triage_high": analyze_symptoms(care_entries)[0] if care_entries else []
            }
    else:
        from adult_rules import predict_from_symptoms, triage_advise, get_adult_options
        opts = get_adult_options()
        c1,c2,c3,c4,c5,c6 = st.columns(6)
        with c1: nasal = st.selectbox("콧물", opts["콧물"], key=f"nasal_ad_{uid}")
        with c2: cough = st.selectbox("기침", opts["기침"], key=f"cough_ad_{uid}")
        with c3: diarrhea = st.selectbox("설사(횟수/일)", opts["설사"], key=f"diarr_ad_{uid}")
        with c4: vomit = st.selectbox("구토(횟수/일)", ["없음","1~3회","4~6회","7회 이상"], key=f"vomit_ad_{uid}")
        with c5: temp = st.number_input("체온(℃)", min_value=0.0, step=0.1, value=0.0, key=f"temp_ad_{uid}")
        with c6: eye = st.selectbox("눈꼽", opts.get("눈꼽", ["없음","맑음","노랑-농성","가려움 동반","한쪽","양쪽"]), key=f"eye_ad_{uid}")
        comorb = st.multiselect("주의 대상", ["임신 가능성","간질환 병력","신질환 병력","위장관 궤양/출혈력","항응고제 복용","고령(65+)"], key=f"comorb_{uid}")

        # 증상 기반 예측/트리아지
        from adult_rules import predict_from_symptoms, triage_advise, get_adult_options
        symptoms = {"콧물":nasal,"기침":cough,"설사":diarrhea,"구토":vomit,"체온":temp,"눈꼽":eye,"병력":",".join(comorb)}
        preds = predict_from_symptoms(symptoms, temp, comorb)
        st.markdown("#### 🤖 증상 기반 자동 추정")
top = sorted(preds or [], key=lambda x: x.get('score',0), reverse=True)[:3]
for p in top:
    label = p.get('label')
    score = p.get('score',0)
    pct = f"{int(round(float(score)))}%" if score is not None else ""
    st.write(f"- **{label}** · 신뢰도 {pct}")
        st.info(triage_advise(temp, comorb))

        care_lines = []; care_entries = []
        if place_carelog_under_special:
            st.divider(); st.subheader("케어 · 해열제")
            care_lines, care_entries = render_carelog(uid, nick)
            render_antipy_guard({"age": 30, "weight": 60}, {}, care_entries)

        if st.button("🔎 해석하기", key=f"analyze_daily_adult_{uid}"):
            st.session_state["analyzed"] = True
            st.session_state["analysis_ctx"] = {
                "mode":"일상","who":"성인",
                "symptoms":{"콧물":nasal,"기침":cough,"설사":diarrhea,"구토":vomit,"체온":temp,"눈꼽":eye,"병력":",".join(comorb)},
                "diet_lines": lab_diet_guides({}, heme_flag=False),
                "care_lines": care_lines, "triage_high": analyze_symptoms(care_entries)[0] if care_entries else []
            }

# 결과 뷰
if results_only_after_analyze(st):
    ctx = st.session_state.get("analysis_ctx", {})
    if ctx.get("care_lines"):
        st.subheader("🗒️ 최근 24h 케어로그"); [st.write(L) for L in ctx["care_lines"]]
    if ctx.get("triage_high"):
        st.error("🚨 응급도: " + " · ".join(ctx["triage_high"]))
    st.subheader("📝 보고서 저장")
    md, txt = ("", "")  # 간결화 (상위 버전과 동일한 방식으로 구성 가능)
    st.stop()
