
# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import date, timedelta, timezone, datetime

# === 프로젝트 내부 모듈 (사용자 코드 기준) ===
from core_utils import nickname_pin, clean_num, schedule_block
from drug_db import DRUG_DB, ensure_onco_drug_db, display_label
from onco_map import build_onco_map, auto_recs_by_dx, dx_display
from ui_results import results_only_after_analyze, render_adverse_effects, collect_top_ae_alerts
from lab_diet import lab_diet_guides
from peds_profiles import get_symptom_options
from peds_dose import acetaminophen_ml, ibuprofen_ml
from pdf_export import export_md_to_pdf

# === 추가 애드온(이번 패치) ===
from carelog_ref import render as render_carelog, load as carelog_load, analyze_symptoms
from antipyretic_guard_ref import render_guard as render_antipy_guard
from metrics_ref import bump as bump_metrics

# -------- 초기화/헤더 --------
ensure_onco_drug_db(DRUG_DB)
ONCO_MAP = build_onco_map()

KST = timezone(timedelta(hours=9))
st.set_page_config(page_title="BloodMap — MASTER p10", page_icon="🩸", layout="centered")
st.title("BloodMap — MASTER p10 (참조 구조 적용)")
st.caption("v2025-09-22")

st.info("**참고용** 도구입니다. 진단/치료를 대체하지 않습니다.")

nick, pin, key = nickname_pin()
uid = f"{nick}_{pin}" if (nick and pin) else "guest_0000"

with st.sidebar:
    try:
        d = bump_metrics(uid)
        st.markdown("### 👥 방문자")
        st.caption(f"오늘 {d.get('today','—')} · 총 {d.get('total_visits',0)} · 고유 {len(d.get('unique',{}))}")
    except Exception as e:
        st.caption(f"방문자 통계 오류: {e}")

st.divider()
mode = st.radio("모드 선택", ["암", "일상", "소아"], horizontal=True, key=f"mode_{uid}")

# 공통 유틸
def _one_line_selection(ctx: dict) -> str:
    def names(keys):
        try:
            from drug_db import display_label
            return ", ".join(display_label(k) for k in (keys or []) if k in DRUG_DB)
        except Exception:
            return ", ".join(keys or [])
    parts = []
    a = names(ctx.get("user_chemo"));    b = names(ctx.get("user_targeted")); c = names(ctx.get("user_abx"))
    if a: parts.append(f"항암제: {a}")
    if b: parts.append(f"표적/면역: {b}")
    if c: parts.append(f"항생제: {c}")
    return " · ".join(parts) if parts else "선택된 약물이 없습니다."

def _export_report(ctx: dict, lines_blocks=None):
    footer = (
        "\n\n---\n본 수치는 참고용이며, 해석 결과는 개발자와 무관합니다.\n"
        "약 변경·복용 중단 등은 반드시 **주치의와 상담**하십시오.\n"
    )
    title = f"# BloodMap 결과 ({ctx.get('mode','')})\n\n"
    body = []
    if ctx.get("mode") == "암":
        body += [f"- 카테고리: {ctx.get('group')}", f"- 진단: {ctx.get('dx_label') or ctx.get('dx')}"]
    if ctx.get("symptoms"): body.append("- 증상: " + ", ".join(f"{k}:{v}" for k,v in ctx["symptoms"].items()))
    if ctx.get("triage_high"): body.append("- 🆘 응급도: " + " · ".join(ctx["triage_high"]))
    if ctx.get("care_lines"): body.append("\n## 🗒️ 최근 24h 케어로그\n" + "\n".join(ctx["care_lines"]))
    if ctx.get("diet_lines"): body.append("\n## 🍽️ 식이가이드\n" + "\n".join(f"- {x}" for x in ctx["diet_lines"]))
    if ctx.get("labs"):
        labs_t = "; ".join(f"{k}:{v}" for k,v in ctx["labs"].items() if v is not None)
        if labs_t: body.append(f"- 주요 수치: {labs_t}")
    if ctx.get("mode") == "암":
        body.append("\n## 🗂️ 선택 요약\n- " + _one_line_selection(ctx))
    md = title + "\n".join(body) + footer
    txt = md.replace("# ","").replace("## ","")
    return md, txt

# =================== 암 모드 ===================
if mode == "암":
    st.markdown("### 1) 암 선택")
    group = st.selectbox("암 카테고리", list(ONCO_MAP.keys()) or ["혈액암"], key=f"oncog_{uid}")
    dx_options = list(ONCO_MAP.get(group, {}).keys()) or ["직접 입력"]
    dx = st.selectbox("진단(영문+한글)", dx_options, key=f"oncodx_{uid}", format_func=lambda x: dx_display(group, x) if x else x)
    if dx == "직접 입력":
        dx = st.text_input("진단(직접 입력)", key=f"oncodx_manual_{uid}")
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

    st.markdown("### 2) 피수치 입력 (숫자만)")
    LABS_ORDER = [("WBC","WBC"),("Hb","Hb"),("PLT","PLT"),("ANC","ANC"),
                  ("Ca","Ca"),("Na","Na"),("K","K"),("Alb","Alb"),("Glu","Glu"),("AST","AST"),("ALT","ALT"),
                  ("Cr","Cr"),("CRP","CRP")]
    labs = {code: clean_num(st.text_input(label, key=f"lab_{label}_{uid}")) for code, label in LABS_ORDER}

    # 특수검사 (기존 모듈 없을 때 대비)
    try:
        from special_tests import special_tests_ui
        sp_lines = special_tests_ui()
    except Exception:
        sp_lines = []
    lines_blocks = []
    if sp_lines: lines_blocks.append(("특수검사 해석", sp_lines))

    # 저장/그래프 (세션 보존)
    st.markdown("#### 💾 저장/그래프")
    when = st.date_input("측정일", value=date.today(), key=f"when_{uid}")
    if st.button("📈 피수치 저장/추가", key=f"save_{uid}"):
        st.session_state.setdefault("lab_hist", {}).setdefault(uid, pd.DataFrame())
        df_prev = st.session_state["lab_hist"][uid]
        row = {"Date": when.strftime("%Y-%m-%d")}
        for code, label in LABS_ORDER: row[label] = labs.get(code)
        newdf = pd.DataFrame([row])
        df = (pd.concat([df_prev, newdf], ignore_index=True) if (isinstance(df_prev, pd.DataFrame) and not df_prev.empty) else newdf)
        df = df.drop_duplicates(subset=["Date"], keep="last").sort_values("Date")
        st.session_state["lab_hist"][uid] = df
        st.success("저장 완료!")

    dfh = st.session_state.get("lab_hist", {}).get(uid)
    if isinstance(dfh, pd.DataFrame) and not dfh.empty:
        st.markdown("##### 📊 추이 그래프")
        nonnull = [c for c in dfh.columns if (c!="Date" and dfh[c].notna().any())]
        default_pick = [c for c in ["WBC","Hb","PLT","CRP","ANC"] if c in nonnull]
        pick = st.multiselect("지표 선택", options=nonnull, default=default_pick, key=f"graphpick_{uid}")
        if pick: st.line_chart(dfh.set_index("Date")[pick], use_container_width=True)
        st.dataframe(dfh[["Date"]+nonnull], use_container_width=True, height=220)

    if st.button("🔎 해석하기", key=f"analyze_cancer_{uid}"):
        st.session_state["analyzed"] = True
        st.session_state["analysis_ctx"] = {
            "mode":"암","group":group,"dx":dx,"dx_label": dx_display(group, dx),
            "labs": labs, "user_chemo": user_chemo, "user_targeted": user_targeted, "user_abx": user_abx,
            "lines_blocks": lines_blocks
        }
    schedule_block()

# =================== 일상 / 소아 ===================
else:
    who = st.radio("대상", ["소아","성인"], horizontal=True, key=f"who_{uid}") if mode=="일상" else "소아"
    # 증상 입력(간단): 기존 구조 준수
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
        from peds_dose import acetaminophen_ml, ibuprofen_ml
        apap_ml, _ = acetaminophen_ml(age_m, weight or None); ibu_ml, _ = ibuprofen_ml(age_m, weight or None)
        st.caption(f"APAP 평균 1회분: {apap_ml} ml · IBU 평균 1회분: {ibu_ml} ml")

        def _fever_bucket_from_temp(temp: float|None) -> str:
            if temp is None: return ""
            if temp < 37.5: return "정상"
            if temp < 38.0: return "37.5~38"
            if temp < 38.5: return "38.0~38.5"
            if temp < 39.0: return "38.5~39"
            return "39+"
        fever_cat = _fever_bucket_from_temp(temp)
        symptoms = {"콧물":nasal,"기침":cough,"설사":diarrhea,"구토":vomit,"체온":temp,"발열":fever_cat,"눈꼽":eye}
        preds = predict_from_symptoms(symptoms, temp, age_m)
        st.markdown("#### 🤖 증상 기반 자동 추정")
        for p in preds or []:
            st.write(f"- **{p.get('label')}** · 신뢰도 {int(p.get('score',0))}/100")

        triage = triage_advise(temp, age_m, diarrhea)
        st.info(triage)
        diet_lines = lab_diet_guides({}, heme_flag=False)  # 수치 없을 시 일반 가이드

        # === 케어로그 + 안전가드 ===
        st.divider(); st.subheader("케어 · 해열제")
        care_lines, care_entries = render_carelog(uid, nick)
        render_antipy_guard({"age": int(age_m/12), "weight": weight}, {}, care_entries)

        if st.button("🔎 해석하기", key=f"analyze_daily_child_{uid}"):
            st.session_state["analyzed"] = True
            st.session_state["analysis_ctx"] = {
                "mode":"일상","who":"소아","symptoms":symptoms,
                "temp":temp,"age_m":age_m,"weight":weight or None,
                "preds":preds,"triage":triage, "diet_lines": diet_lines,
                "care_lines": care_lines, "triage_high": analyze_symptoms(care_entries)[0]
            }

    else:  # 성인(일상)
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
        fever_cat = "정상" if temp < 37.5 else "38+"
        symptoms = {"콧물":nasal,"기침":cough,"설사":diarrhea,"구토":vomit,"체온":temp,"발열":fever_cat,"눈꼽":eye}
        preds = predict_from_symptoms(symptoms, temp, comorb)
        st.markdown("#### 🤖 증상 기반 자동 추정")
        for p in preds or []:
            st.write(f"- **{p.get('label')}** · 신뢰도 {int(p.get('score',0))}/100")
        triage = triage_advise(temp, comorb)
        st.info(triage)
        diet_lines = lab_diet_guides({}, heme_flag=False)

        st.divider(); st.subheader("케어 · 해열제")
        care_lines, care_entries = render_carelog(uid, nick)
        render_antipy_guard({"age": 30, "weight": 60}, {}, care_entries)

        if st.button("🔎 해석하기", key=f"analyze_daily_adult_{uid}"):
            st.session_state["analyzed"] = True
            st.session_state["analysis_ctx"] = {
                "mode":"일상","who":"성인","symptoms":symptoms,
                "temp":temp,"comorb":comorb,"preds":preds,"triage":triage,"diet_lines": diet_lines,
                "care_lines": care_lines, "triage_high": analyze_symptoms(care_entries)[0]
            }

# ================ 결과 게이트 ================
if results_only_after_analyze(st):
    ctx = st.session_state.get("analysis_ctx", {})
    m = ctx.get("mode")
    if m == "암":
        st.subheader("🧪 피수치 요약")
        labs = ctx.get("labs", {})
        if labs:
            rcols = st.columns(len(labs))
            for i, (k, v) in enumerate(labs.items()):
                with rcols[i % len(rcols)]: st.metric(k, v)
        if ctx.get("dx_label"): st.caption(f"진단: **{ctx['dx_label']}**")
        alerts = collect_top_ae_alerts((ctx.get("user_chemo") or []) + (ctx.get("user_abx") or []), db=DRUG_DB)
        if alerts: st.error("\n".join(alerts))
        # 특수검사
        for title2, lines2 in ctx.get("lines_blocks") or []:
            if lines2: st.subheader("🧬 "+title2); [st.write("- "+L) for L in lines2]
        # 식이가이드
        st.subheader("🍽️ 식이가이드")
        diet_lines = lab_diet_guides(labs or {}, heme_flag=(ctx.get("group")=="혈액암")); [st.write("- "+L) for L in diet_lines]
        ctx["diet_lines"] = diet_lines
        # 부작용 요약
        st.subheader("💊 부작용")
        from drug_db import key_from_label
        ckeys = [k for k in (ctx.get("user_chemo") or []) if k in DRUG_DB]
        akeys = [k for k in (ctx.get("user_abx") or []) if k in DRUG_DB]
        if ckeys: st.markdown("**항암제(세포독성)**"); render_adverse_effects(st, ckeys, DRUG_DB)
        if akeys: st.markdown("**항생제**"); render_adverse_effects(st, akeys, DRUG_DB)
        # 보고서
        st.subheader("📝 보고서 저장")
        md, txt = _export_report(ctx, ctx.get("lines_blocks"))
        st.download_button("⬇️ Markdown", data=md, file_name="BloodMap_Report.md", key=f"dl_md_{uid}")
        st.download_button("⬇️ TXT", data=txt, file_name="BloodMap_Report.txt", key=f"dl_txt_{uid}")
        try:
            pdf_bytes = export_md_to_pdf(md); st.download_button("⬇️ PDF", data=pdf_bytes, file_name="BloodMap_Report.pdf", mime="application/pdf", key=f"dl_pdf_{uid}")
        except Exception as e:
            st.caption(f"PDF 변환 오류: {e}")
    else:
        st.subheader("👪 증상 요약")
        for k,v in (ctx.get("symptoms") or {}).items(): st.write(f"- {k}: {v}")
        if ctx.get("care_lines"):
            st.subheader("🗒️ 최근 24h 케어로그"); [st.write(L) for L in ctx["care_lines"]]
        if ctx.get("triage_high"):
            st.error("🚨 응급도: " + " · ".join(ctx["triage_high"]))
        st.subheader("🍽️ 식이가이드"); [st.write("- "+str(L)) for L in (ctx.get("diet_lines") or [])]
        st.subheader("📝 보고서 저장")
        md, txt = _export_report(ctx, None)
        st.download_button("⬇️ Markdown", data=md, file_name="BloodMap_Report.md", key=f"dl_md2_{uid}")
        st.download_button("⬇️ TXT", data=txt, file_name="BloodMap_Report.txt", key=f"dl_txt2_{uid}")
        try:
            pdf_bytes = export_md_to_pdf(md); st.download_button("⬇️ PDF", data=pdf_bytes, file_name="BloodMap_Report.pdf", mime="application/pdf", key=f"dl_pdf2_{uid}")
        except Exception as e:
            st.caption(f"PDF 변환 오류: {e}")
    st.stop()
