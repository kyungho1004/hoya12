
# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import date, timedelta, timezone, datetime

# ---- 프로젝트 모듈(이미 보유 가정) ----
from core_utils import nickname_pin, clean_num, schedule_block
from drug_db import DRUG_DB, ensure_onco_drug_db, display_label
from onco_map import build_onco_map, auto_recs_by_dx, dx_display
from ui_results import results_only_after_analyze, render_adverse_effects, collect_top_ae_alerts
from lab_diet import lab_diet_guides
from peds_profiles import get_symptom_options
from peds_dose import acetaminophen_ml, ibuprofen_ml
from pdf_export import export_md_to_pdf

# ---- 내장 보조(이 파일 안에 포함) ----
from datetime import timezone, timedelta
KST = timezone(timedelta(hours=9))

def _data_root():
    import os
    for d in [os.getenv("BLOODMAP_DATA_ROOT","").strip(), "/mnt/data", os.path.join(os.getenv("TMPDIR") or "/tmp","bloodmap_data")]:
        if not d: continue
        try:
            os.makedirs(d, exist_ok=True)
            p = os.path.join(d, ".probe"); open(p,"w").write("ok"); os.remove(p)
            return d
        except Exception:
            continue
    d = os.path.join(os.getenv("TMPDIR") or "/tmp","bloodmap_data"); os.makedirs(d, exist_ok=True); return d

# --- carelog (개인별 24h) ---
import os, json
def _carelog_path(uid:str)->str:
    p = os.path.join(_data_root(), "care_log", f"{uid}.json")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    return p
def carelog_load(uid:str):
    try: return json.load(open(_carelog_path(uid),"r",encoding="utf-8"))
    except Exception: return []
def carelog_save(uid:str, data):
    tmp = _carelog_path(uid)+".tmp"
    json.dump(data, open(tmp,"w",encoding="utf-8"), ensure_ascii=False, indent=2); os.replace(tmp, _carelog_path(uid))
def carelog_add(uid:str, e:dict):
    d = carelog_load(uid); d.append(e); carelog_save(uid, d)

def analyze_symptoms(entries):
    em, gen = [], []
    from collections import Counter
    kinds = [e.get("kind") for e in entries if e.get("type") in ("vomit","diarrhea")]
    has_green_vomit = any(k and "초록" in k for k in kinds)
    has_bloody = any(k and ("혈변" in k or "검은" in k or "녹색혈변" in k) for k in kinds)
    fevers = [float(e.get("temp") or 0) for e in entries if e.get("type")=="fever"]
    has_high_fever = any(t >= 39.0 for t in fevers)
    # 단순 카운트
    vomit_ct = sum(1 for e in entries if e.get("type")=="vomit")
    diarr_ct = sum(1 for e in entries if e.get("type")=="diarrhea")
    if has_bloody: em.append("혈변/검은변/녹색혈변")
    if has_green_vomit: em.append("초록(담즙) 구토")
    if vomit_ct >= 3: em.append("2시간 내 구토 ≥3회")
    if diarr_ct >= 6: em.append("24시간 설사 ≥6회")
    if has_high_fever: em.append("고열 ≥39.0℃")
    gen = ["혈변/검은변","초록 구토","의식저하/경련/호흡곤란","6시간 무뇨·중증 탈수","고열 지속","심한 복통/팽만/무기력"]
    return em, gen

def render_carelog(uid:str, nick:str):
    st.markdown("### 🗒️ 케어로그")
    c1,c2,c3 = st.columns(3)
    with c1:
        if st.button("발열 +", key=f"btn_fever_{uid}"):
            t = st.number_input("현재 체온(℃)", value=38.0, step=0.1, key=f"temp_now_{uid}")
            carelog_add(uid, {"type":"fever","temp":t,"ts": datetime.now(KST).isoformat()})
            st.success("발열 기록됨")
    with c2:
        vk = st.selectbox("구토 유형", ["흰","노랑","초록(담즙)","기타"], index=1, key=f"vomit_kind_{uid}")
        if st.button("구토 +", key=f"btn_vomit_{uid}"):
            carelog_add(uid, {"type":"vomit","kind":vk,"ts": datetime.now(KST).isoformat()})
            st.success("구토 기록됨")
    with c3:
        dk = st.selectbox("설사 유형", ["노랑","진한노랑","거품","녹색","녹색혈변","혈변","검은색","기타"], index=0, key=f"diarr_kind_{uid}")
        if st.button("설사 +", key=f"btn_diarr_{uid}"):
            carelog_add(uid, {"type":"diarrhea","kind":dk,"ts": datetime.now(KST).isoformat()})
            st.success("설사 기록됨")

    st.divider()
    show = st.toggle("최근 로그 보기", value=False, key=f"toggle_show_{uid}")
    win = st.segmented_control("표시 시간창", options=[2,6,12,24], format_func=lambda h: f"{h}h", key=f"win_{uid}")
    if not show:
        st.caption("※ 입력 후 ‘최근 로그 보기’를 켜면 표시됩니다.")
        return [], []

    # 24h 필터
    now = datetime.now(KST)
    entries = [e for e in carelog_load(uid) if (now - datetime.fromisoformat(e.get("ts"))).total_seconds() <= int(win)*3600]
    if not entries:
        st.info(f"최근 {win}시간 이내 기록 없음.")
        return [], []
    st.markdown(f"#### 최근 {win}h — {nick} ({uid})")
    def _ko_line(e):
        t = e.get("type"); ts = e.get("ts","")
        if t == "fever": return f"- {ts} · 발열 {e.get('temp')}℃"
        if t == "apap": return f"- {ts} · APAP {e.get('mg')} mg"
        if t == "ibu":  return f"- {ts} · IBU {e.get('mg')} mg"
        if t == "vomit":
            k = e.get("kind"); return f"- {ts} · 구토" + (f" ({k})" if k else "")
        if t == "diarrhea":
            k = e.get("kind"); return f"- {ts} · 설사" + (f" ({k})" if k else "")
        return f"- {ts} · {t}"
    lines = [_ko_line(e) for e in sorted(entries, key=lambda x: x.get("ts",""))]
    for L in lines: st.write(L)
    em, gen = analyze_symptoms(entries)
    if em: st.error("🚨 응급도: " + " · ".join(em))
    st.caption("일반 응급실 기준: " + " · ".join(gen))
    return lines, entries

# --- antipyretic guard ---
def render_antipy_guard(profile: dict, labs: dict, care_entries: list):
    def _within_24h(ts):
        try: return (datetime.now(KST) - datetime.fromisoformat(ts)).total_seconds() <= 24*3600
        except Exception: return False
    apap_total = 0.0; ibu_total = 0.0; last_apap=None; last_ibu=None
    for e in care_entries or []:
        if not _within_24h(e.get("ts","")): continue
        if e.get("type") == "apap":
            apap_total += float(e.get("mg") or 0); last_apap = e.get("ts")
        if e.get("type") == "ibu":
            ibu_total += float(e.get("mg") or 0); last_ibu = e.get("ts")
    age = int(profile.get("age", 18) if isinstance(profile, dict) else 18); is_adult = age >= 18
    weight = float(profile.get("weight", 0) if isinstance(profile, dict) else 0)
    lim_apap = min(4000.0 if is_adult else 75.0*(weight or 0), 4000.0)
    lim_ibu  = min(1200.0 if is_adult else 30.0*(weight or 0), 1200.0)
    def _next(last_ts, h):
        if not last_ts: return None
        try: return (datetime.fromisoformat(last_ts) + timedelta(hours=h)).strftime("%H:%M")
        except Exception: return None
    st.caption(f"APAP 24h: {int(apap_total)}/{int(lim_apap)} mg · 다음가능: {_next(last_apap,4) or '—'}")
    st.caption(f"IBU 24h: {int(ibu_total)}/{int(lim_ibu)} mg · 다음가능: {_next(last_ibu,6) or '—'}")
    # Safety
    plt = labs.get("PLT"); egfr = labs.get("eGFR"); ast_v = labs.get("AST"); alt_v = labs.get("ALT")
    if isinstance(plt,(int,float)) and plt < 50000: st.error("IBU 금지: PLT < 50k")
    if isinstance(egfr,(int,float)) and egfr < 60: st.warning("eGFR < 60: IBU 주의")
    if (isinstance(ast_v,(int,float)) and ast_v > 120) or (isinstance(alt_v,(int,float)) and alt_v > 120): st.warning("AST/ALT > 120: APAP 간기능 주의")

# --- metrics ---
def bump_metrics(uid:str)->dict:
    import json
    PATH = os.path.join(_data_root(), "metrics", "visits.json")
    os.makedirs(os.path.dirname(PATH), exist_ok=True)
    try: d = json.load(open(PATH,"r",encoding="utf-8"))
    except Exception: d = {"total_visits":0,"unique":{}}
    d["total_visits"] = int(d.get("total_visits",0))+1
    uniq = d.setdefault("unique",{}); uniq[uid] = int(uniq.get(uid,0))+1
    d["today"] = datetime.now(KST).date().isoformat()
    json.dump(d, open(PATH,"w",encoding="utf-8"), ensure_ascii=False, indent=2)
    return d

# ----------------- APP -----------------
ensure_onco_drug_db(DRUG_DB)
ONCO_MAP = build_onco_map()

st.set_page_config(page_title="BloodMap — APP(모바일/보고서/예측)", page_icon="🩸", layout="centered")
st.title("BloodMap — APP (모바일 최적화 · 예측/보고서 포함)")
st.caption("v2025-09-22")

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
    for i, (code, label) in enumerate(LABS):
        if cols_per_row == 1:
            vals[code] = clean_num(st.text_input(label, key=f"lab_{code}_{uid}"))
        else:
            if i % cols_per_row == 0:
                cols = st.columns(cols_per_row)
            with cols[i % cols_per_row]:
                vals[code] = clean_num(st.text_input(label, key=f"lab_{code}_{uid}"))
    if vals.get("CR") is not None and (vals.get("Cr") is None):
        vals["Cr"] = vals["CR"]
    return vals

def export_report(ctx: dict):
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
        labs = ctx["labs"].copy()
        if "CR" in labs and "Cr" not in labs: labs["Cr"] = labs["CR"]
        labs_t = "; ".join(f"{k}:{v}" for k,v in labs.items() if v is not None)
        if labs_t: body.append(f"- 주요 수치: {labs_t}")
    if ctx.get("mode") == "암":
        def _one_line_selection(ctx):
            def names(keys):
                try:
                    return ", ".join(display_label(k) for k in (keys or []) if k in DRUG_DB)
                except Exception:
                    return ", ".join(keys or [])
            parts = []
            a = names(ctx.get("user_chemo")); b = names(ctx.get("user_targeted")); c = names(ctx.get("user_abx"))
            if a: parts.append(f"항암제: {a}")
            if b: parts.append(f"표적/면역: {b}")
            if c: parts.append(f"항생제: {c}")
            return " · ".join(parts) if parts else "선택된 약물이 없습니다."
        body.append("\n## 🗂️ 선택 요약\n- " + _one_line_selection(ctx))
    md = title + "\n".join(body) + footer
    txt = md.replace("# ","").replace("## ","")
    return md, txt

# === 암 모드 ===
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

    labs = labs_block(uid, cols_per_row)

    # 특수검사(있으면 표시)
    lines_blocks = []
    try:
        from special_tests import special_tests_ui
        sp_lines = special_tests_ui()
    except Exception:
        sp_lines = []
    if sp_lines: lines_blocks.append(("특수검사 해석", sp_lines))

    # 케어로그(특수해석 밑에)
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
        # 입력
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

        # 증상 기반 예측/트리아지 (상위3, %)
        from peds_rules import predict_from_symptoms, triage_advise
        symptoms = {"콧물":nasal,"기침":cough,"설사":diarrhea,"구토":vomit,"체온":temp,"눈꼽":eye}
        preds = predict_from_symptoms(symptoms, temp, age_m)
        st.markdown("#### 🤖 증상 기반 자동 추정")
        top = sorted(preds or [], key=lambda x: x.get('score',0), reverse=True)[:3]
        for p in top:
            label = p.get('label'); score = p.get('score',0); pct = f"{int(round(float(score)))}%" if score is not None else ""
            st.write(f"- **{label}** · 신뢰도 {pct}")
        triage = triage_advise(temp, age_m, diarrhea)
        st.info(triage)

        # 케어로그 위치
        care_lines = []; care_entries = []
        if place_carelog_under_special:
            st.divider(); st.subheader("케어 · 해열제")
            care_lines, care_entries = render_carelog(uid, nick)
            render_antipy_guard({"age": int(age_m/12), "weight": weight}, {}, care_entries)

        if st.button("🔎 해석하기", key=f"analyze_daily_child_{uid}"):
            st.session_state["analyzed"] = True
            st.session_state["analysis_ctx"] = {
                "mode":"일상","who":"소아",
                "symptoms":symptoms, "diet_lines": lab_diet_guides({}, heme_flag=False),
                "care_lines": care_lines, "triage_high": analyze_symptoms(care_entries)[0] if care_entries else []
            }
    else:
        # 성인
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

        symptoms = {"콧물":nasal,"기침":cough,"설사":diarrhea,"구토":vomit,"체온":temp,"눈꼽":eye,"병력":",".join(comorb)}
        preds = predict_from_symptoms(symptoms, temp, comorb)
        st.markdown("#### 🤖 증상 기반 자동 추정")
        top = sorted(preds or [], key=lambda x: x.get('score',0), reverse=True)[:3]
        for p in top:
            label = p.get('label'); score = p.get('score',0); pct = f"{int(round(float(score)))}%" if score is not None else ""
            st.write(f"- **{label}** · 신뢰도 {pct}")
        triage = triage_advise(temp, comorb)
        st.info(triage)

        care_lines = []; care_entries = []
        if place_carelog_under_special:
            st.divider(); st.subheader("케어 · 해열제")
            care_lines, care_entries = render_carelog(uid, nick)
            render_antipy_guard({"age": 30, "weight": 60}, {}, care_entries)

        if st.button("🔎 해석하기", key=f"analyze_daily_adult_{uid}"):
            st.session_state["analyzed"] = True
            st.session_state["analysis_ctx"] = {
                "mode":"일상","who":"성인",
                "symptoms":symptoms, "diet_lines": lab_diet_guides({}, heme_flag=False),
                "care_lines": care_lines, "triage_high": analyze_symptoms(care_entries)[0] if care_entries else []
            }

# 결과/보고서
if results_only_after_analyze(st):
    ctx = st.session_state.get("analysis_ctx", {})
    if ctx.get("care_lines"):
        st.subheader("🗒️ 최근 24h 케어로그"); [st.write(L) for L in ctx["care_lines"]]
    if ctx.get("triage_high"):
        st.error("🚨 응급도: " + " · ".join(ctx["triage_high"]))
    st.subheader("📝 보고서 저장")
    md, txt = export_report(ctx)
    st.download_button("⬇️ Markdown", data=md, file_name="BloodMap_Report.md", key=f"dl_md_{uid}")
    st.download_button("⬇️ TXT", data=txt, file_name="BloodMap_Report.txt", key=f"dl_txt_{uid}")
    try:
        pdf_bytes = export_md_to_pdf(md); st.download_button("⬇️ PDF", data=pdf_bytes, file_name="BloodMap_Report.pdf", mime="application/pdf", key=f"dl_pdf_{uid}")
    except Exception as e:
        st.caption(f"PDF 변환 오류: {e}")
    st.stop()
