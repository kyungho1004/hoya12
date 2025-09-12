# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import date

# ---- 유틸(지역) ----
def _is_korean(s: str) -> bool:
    return any('\uac00' <= ch <= '\ud7a3' for ch in (s or ""))

def _norm(s: str) -> str:
    if not s:
        return ""
    s2 = (s or "").strip()
    return s2.upper().replace(" ", "") or s2

DX_KO_LOCAL = {"APL":"급성 전골수구성 백혈병","AML":"급성 골수성 백혈병","ALL":"급성 림프구성 백혈병",
               "CML":"만성 골수성 백혈병","CLL":"만성 림프구성 백혈병","DLBCL":"미만성 거대 B세포 림프종"}

def local_dx_display(group: str, dx: str) -> str:
    dx = (dx or "").strip()
    if _is_korean(dx): return f"{group} - {dx}"
    key = _norm(dx); ko = DX_KO_LOCAL.get(key) or DX_KO_LOCAL.get(dx)
    return f"{group} - {dx} ({ko})" if ko else f"{group} - {dx}"

# ---- 외부 모듈 ----
from core_utils import nickname_pin, clean_num, schedule_block
from drug_db import DRUG_DB, ensure_onco_drug_db, display_label
from onco_map import build_onco_map, auto_recs_by_dx, dx_display
from ui_results import results_only_after_analyze, render_adverse_effects
from lab_diet import lab_diet_guides
from peds_profiles import get_symptom_options
from peds_dose import acetaminophen_ml, ibuprofen_ml

# 일상 모드 규칙
from peds_rules import predict_from_symptoms as peds_predict, triage_advise as peds_triage
from adult_rules import predict_from_symptoms as adult_predict, triage_advise as adult_triage, get_adult_options

# Init
ensure_onco_drug_db(DRUG_DB)
ONCO_MAP = build_onco_map()

st.set_page_config(page_title="BloodMap — 피수치가이드", page_icon="🩸", layout="centered")
st.title("BloodMap — 피수치가이드")

st.info(
    "본 수치는 참고용이며, 해석 결과는 개발자와 무관합니다.\n"
    "약 변경/복용 중단 등은 반드시 주치의와 상의하세요.\n"
    "이 앱은 개인정보를 수집하지 않으며, 어떠한 개인정보 입력도 요구하지 않습니다."
)

nick, pin, key = nickname_pin()
st.divider()
has_key = bool(nick and pin and len(pin) == 4)

# ---- 모드 선택 ----
mode = st.radio("모드 선택", ["암", "일상", "소아"], horizontal=True)

# ------------------ 암 모드 ------------------
if mode == "암":
    st.markdown("### 1) 암 선택")
    group = st.selectbox("암 카테고리", ["혈액암","림프종","고형암","육종","희귀암"])
    dx_options = list(ONCO_MAP.get(group, {}).keys())

    def _dx_fmt(opt: str) -> str:
        try: return dx_display(group, opt)
        except Exception:
            try: return local_dx_display(group, opt)
            except Exception: return f"{group} - {opt}"

    dx = st.selectbox("진단(영문+한글)", dx_options or ["직접 입력"], format_func=_dx_fmt)
    if dx == "직접 입력":
        dx = st.text_input("진단(영문/축약 직접 입력)", value="")
    if dx:
        st.caption(_dx_fmt(dx))

    if group == "혈액암":
        msg = "혈액암 환자에서 **철분제 + 비타민 C**는 흡수 촉진 가능성이 있어, 복용 전 반드시 주치의와 상의하세요."
        st.warning(msg)

    st.markdown("### 2) 자동 예시(토글)")
    if st.toggle("자동 예시 보기", value=True):
        rec = auto_recs_by_dx(group, dx, DRUG_DB, ONCO_MAP)
        c = st.columns(3)
        with c[0]:
            st.markdown("**항암제(예시)**")
            for d in rec["chemo"]: st.write("- " + display_label(d))
        with c[1]:
            st.markdown("**표적/면역(예시)**")
            for d in rec["targeted"]: st.write("- " + display_label(d))
        with c[2]:
            st.markdown("**항생제(참고)**")
            for d in rec["abx"]: st.write("- " + display_label(d))

    st.markdown("### 3) 개인 선택")
    from drug_db import picklist, key_from_label
    rec_local = auto_recs_by_dx(group, dx, DRUG_DB, ONCO_MAP)
    chemo_opts    = picklist(rec_local.get("chemo", []))
    targeted_opts = picklist(rec_local.get("targeted", []))
    abx_opts      = picklist(["Piperacillin/Tazobactam","Cefepime","Meropenem","Imipenem/Cilastatin","Aztreonam",
                              "Amikacin","Vancomycin","Linezolid","Daptomycin","Ceftazidime","Levofloxacin","TMP-SMX",
                              "Metronidazole","Amoxicillin/Clavulanate"])

    c1,c2,c3 = st.columns(3)
    with c1: user_chemo_labels = st.multiselect("항암제(개인)", chemo_opts, default=[])
    with c2: user_targeted_labels = st.multiselect("표적/면역(개인)", targeted_opts, default=[])
    with c3: user_abx_labels = st.multiselect("항생제(개인)", abx_opts, default=[])

    user_chemo    = [key_from_label(x) for x in user_chemo_labels]
    user_targeted = [key_from_label(x) for x in user_targeted_labels]
    user_abx      = [key_from_label(x) for x in user_abx_labels]

    st.markdown("### 4) 피수치 입력 (숫자만)")
    LABS_ORDER = [
        ("WBC","WBC(백혈구)"), ("Hb","Hb(혈색소)"), ("PLT","PLT(혈소판)"), ("ANC","ANC(호중구)"),
        ("Ca","Ca(칼슘)"), ("Na","Na(소디움)"), ("K","K(칼륨)"),
        ("Alb","Alb(알부민)"), ("Glu","Glu(혈당)"), ("TP","TP(총단백)"),
        ("AST","AST"), ("ALT","ALT"), ("LDH","LDH"),
        ("CRP","CRP"), ("Cr","Cr(크레아티닌)"), ("UA","UA(요산)"), ("TB","TB(총빌리루빈)"), ("BUN","BUN")
    ]
    labs = {}
    for code, label in LABS_ORDER:
        labs[code] = clean_num(st.text_input(label, placeholder="예: 4500"))

    from special_tests import special_tests_ui
    sp_lines = special_tests_ui()
    if sp_lines:
        st.markdown("#### 🧬 특수검사 해석")
        for L in sp_lines: st.write("- " + L)

    st.markdown("#### 💾 저장/그래프")
    when = st.date_input("측정일", value=date.today())
    if st.button("📈 피수치 저장/추가"):
        st.session_state.setdefault("lab_hist", {}).setdefault(key, pd.DataFrame())
        df_prev = st.session_state["lab_hist"][key]
        row = {"Date": when.strftime("%Y-%m-%d")}
        labels = [label for _, label in LABS_ORDER]
        for code, label in LABS_ORDER: row[label] = labs.get(code)
        newdf = pd.DataFrame([row])
        if df_prev is None or df_prev.empty: df = newdf
        else:
            df = pd.concat([df_prev, newdf], ignore_index=True).drop_duplicates(subset=["Date"], keep="last").sort_values("Date")
        for col in (["Date"]+labels):
            if col not in df.columns: df[col] = pd.NA
        df = df.reindex(columns=(["Date"]+labels))
        st.session_state["lab_hist"][key] = df
        st.success("저장 완료!")

    dfh = st.session_state.get("lab_hist", {}).get(key)
    if has_key and isinstance(dfh, pd.DataFrame) and not dfh.empty:
        st.markdown("##### 📊 추이 그래프")
        nonnull = [c for c in dfh.columns if (c!="Date" and dfh[c].notna().any())]
        default_pick = [c for c in ["WBC(백혈구)","Hb(혈색소)","PLT(혈소판)","CRP","ANC(호중구)"] if c in nonnull]
        pick = st.multiselect("지표 선택", options=nonnull, default=default_pick)
        if pick: st.line_chart(dfh.set_index("Date")[pick], use_container_width=True)
        st.dataframe(dfh[["Date"]+nonnull], use_container_width=True, height=220)
    elif not has_key:
        st.info("그래프는 별명 + PIN(4자리) 저장 시 표시됩니다.")
    else:
        st.info("저장된 히스토리가 없습니다. 값을 입력하고 ‘피수치 저장/추가’를 눌러 보세요.")

    if st.button("🔎 해석하기", key="analyze_cancer"):
        st.session_state["analyzed"] = True
        st.session_state["analysis_ctx"] = {
            "mode":"암","group":group,"dx":dx,"dx_label": dx_display(group, dx),
            "labs": labs, "user_chemo": user_chemo, "user_targeted": user_targeted, "user_abx": user_abx
        }
    schedule_block()

# ------------------ 일상 모드 (소아/성인) ------------------
elif mode == "일상":
    st.markdown("### 1) 대상 선택")
    who = st.radio("대상", ["소아","성인"], horizontal=True)
    st.markdown("### 2) 증상 체크(간단)")

    if who == "소아":
        opts = get_symptom_options("기본")
        c1,c2,c3,c4 = st.columns(4)
        with c1: nasal = st.selectbox("콧물", opts["콧물"])
        with c2: cough = st.selectbox("기침", opts["기침"])
        with c3: diarrhea = st.selectbox("설사(횟수/일)", opts["설사"])
        with c4: fever = st.selectbox("발열", opts["발열"])
        temp = st.number_input("현재 체온(℃)", min_value=0.0, step=0.1, value=0.0)
        age_m = st.number_input("나이(개월)", min_value=0, step=1)
        weight = st.number_input("체중(kg)", min_value=0.0, step=0.1)

        # 해열제 1회분 자동계산
        apap_ml, apap_w = acetaminophen_ml(age_m, weight or None)
        ibu_ml,  ibu_w  = ibuprofen_ml(age_m, weight or None)
        d1,d2 = st.columns(2)
        with d1: st.metric("아세트아미노펜 시럽", f"{apap_ml} mL", help=f"계산 체중 {apap_w} kg 기준")
        with d2: st.metric("이부프로펜 시럽",   f"{ibu_ml} mL",  help=f"계산 체중 {ibu_w} kg 기준")

        preds = peds_predict({"콧물":nasal,"기침":cough,"설사":diarrhea,"발열":fever}, temp, age_m)
        st.markdown("#### 🤖 증상 기반 자동 추정")
        for p in preds:
            st.write(f"- **{p['label']}** · 신뢰도 {p['score']}점")
            for r in p["reasons"]: st.caption("  · "+r)
        st.info(peds_triage(temp, age_m, diarrhea))

        if st.button("🔎 해석하기", key="analyze_daily_child"):
            st.session_state["analyzed"] = True
            st.session_state["analysis_ctx"] = {
                "mode":"일상","who":"소아","symptoms":{"콧물":nasal,"기침":cough,"설사":diarrhea,"발열":fever},
                "temp":temp,"age_m":age_m,"weight":weight or None,
                "apap_ml":apap_ml,"ibu_ml":ibu_ml,"preds":preds,"triage":peds_triage(temp, age_m, diarrhea)
            }

    else:  # 성인
        opts = get_adult_options()
        c1,c2,c3,c4 = st.columns(4)
        with c1: nasal = st.selectbox("콧물", opts["콧물"])
        with c2: cough = st.selectbox("기침", opts["기침"])
        with c3: diarrhea = st.selectbox("설사(횟수/일)", opts["설사"])
        with c4: fever = st.selectbox("발열", opts["발열"])
        temp = st.number_input("현재 체온(℃)", min_value=0.0, step=0.1, value=0.0)
        comorb = st.multiselect("주의 대상", ["임신 가능성","간질환 병력","신질환 병력","위장관 궤양/출혈력","항응고제 복용","고령(65+)"])

        preds = adult_predict({"콧물":nasal,"기침":cough,"설사":diarrhea,"발열":fever}, temp, comorb)
        st.markdown("#### 🤖 증상 기반 자동 추정")
        for p in preds:
            st.write(f"- **{p['label']}** · 신뢰도 {p['score']}점")
            for r in p["reasons"]: st.caption("  · "+r)
        st.info(adult_triage(temp, comorb))

        st.markdown("#### 🌡️ 해열제(성인) 참고")
        st.write("- 아세트아미노펜 500–1,000 mg 1회, 1일 최대 3,000 mg (간질환·음주 시 더 낮게, 의료진과 상의)")
        st.write("- 이부프로펜 200–400 mg 1회, 1일 최대 1,200 mg (위장관 출혈/신장질환/임신 3기 금기)")

        if st.button("🔎 해석하기", key="analyze_daily_adult"):
            st.session_state["analyzed"] = True
            st.session_state["analysis_ctx"] = {
                "mode":"일상","who":"성인","symptoms":{"콧물":nasal,"기침":cough,"설사":diarrhea,"발열":fever},
                "temp":temp,"comorb":comorb,"preds":preds,"triage":adult_triage(temp, comorb)
            }

# ------------------ 소아 모드(질환 선택) ------------------
else:
    ctop = st.columns(3)
    with ctop[0]: disease = st.selectbox("소아 질환", ["로타","독감","RSV","아데노","마이코","수족구","편도염","코로나","중이염"], index=0)
    with ctop[1]: temp = st.number_input("체온(℃)", min_value=0.0, step=0.1)
    with ctop[2]:
        age_m = st.number_input("나이(개월)", min_value=0, step=1)
        weight = st.number_input("체중(kg)", min_value=0.0, step=0.1)

    opts = get_symptom_options(disease)
    st.markdown("### 증상 체크")
    c1,c2,c3,c4 = st.columns(4)
    with c1: nasal = st.selectbox("콧물", opts["콧물"])
    with c2: cough = st.selectbox("기침", opts["기침"])
    with c3: diarrhea = st.selectbox("설사(횟수/일)", opts["설사"])
    with c4:
        fever_opts = (opts.get("발열") if isinstance(opts, dict) else None) or ["없음","37~37.5","37.5~38","38.5~39","39+"]
        fever = st.selectbox("발열", fever_opts)

    apap_ml, apap_w = acetaminophen_ml(age_m, weight or None)
    ibu_ml,  ibu_w  = ibuprofen_ml(age_m, weight or None)
    dc = st.columns(2)
    with dc[0]: st.metric("아세트아미노펜 시럽", f"{apap_ml} mL", help=f"계산 체중 {apap_w} kg")
    with dc[1]: st.metric("이부프로펜 시럽", f"{ibu_ml} mL", help=f"계산 체중 {ibu_w} kg")

    if st.button("🔎 해석하기", key="analyze_peds"):
        st.session_state["analyzed"] = True
        st.session_state["analysis_ctx"] = {
            "mode":"소아", "disease": disease,
            "symptoms": {"콧물": nasal, "기침": cough, "설사": diarrhea, "발열": fever},
            "temp": temp, "age_m": age_m, "weight": weight or None,
            "apap_ml": apap_ml, "ibu_ml": ibu_ml, "vals": {}
        }

# ------------------ 결과 전용 게이트 ------------------
if results_only_after_analyze(st):
    ctx = st.session_state.get("analysis_ctx", {})
    m = ctx.get("mode")

    if m == "암":
        labs = ctx.get("labs", {})
        st.subheader("🧪 피수치 요약")
        if labs:
            rcols = st.columns(len(labs))
            for i, (k, v) in enumerate(labs.items()):
                with rcols[i]: st.metric(k, v)
        if ctx.get("dx_label"): st.caption(f"진단: **{ctx['dx_label']}**")

        st.subheader("🗂️ 선택 요약")
        s1,s2,s3 = st.columns(3)
        with s1:
            st.markdown("**항암제(개인)**")
            for k in (ctx.get("user_chemo") or []): st.write("- " + display_label(k))
        with s2:
            st.markdown("**표적/면역(개인)**")
            for k in (ctx.get("user_targeted") or []): st.write("- " + display_label(k))
        with s3:
            st.markdown("**항생제(개인)**")
            for k in (ctx.get("user_abx") or []): st.write("- " + display_label(k))

        st.subheader("💊 항암제(세포독성) 부작용")
        render_adverse_effects(st, ctx.get("user_chemo") or [], DRUG_DB)
        st.subheader("🧫 항생제 부작용")
        render_adverse_effects(st, ctx.get("user_abx") or [], DRUG_DB)

        st.subheader("🥗 피수치 기반 식이가이드 (예시)")
        lines = lab_diet_guides(labs, heme_flag=(ctx.get("group")=="혈액암"))
        for L in lines: st.write("- " + L)

        st.subheader("💊 약물 부작용(자동 예시)")
        rec = auto_recs_by_dx(ctx.get("group"), ctx.get("dx"), DRUG_DB, ONCO_MAP)
        regimen = (rec.get("chemo") or []) + (rec.get("targeted") or [])
        render_adverse_effects(st, regimen, DRUG_DB)

    elif m == "일상":
        st.subheader("👪 증상 요약")
        sy = ctx.get("symptoms", {})
        sy_cols = st.columns(4)
        for i, k in enumerate(sy.keys()):
            with sy_cols[i % 4]: st.metric(k, sy[k])

        preds = ctx.get("preds") or []
        if preds:
            st.subheader("🤖 증상 기반 자동 추정")
            for p in preds: st.write(f"- **{p['label']}** · 신뢰도 {p['score']}점")
        if ctx.get("triage"): st.info(ctx["triage"])

        if ctx.get("who") == "소아":
            st.subheader("🌡️ 해열제 1회분(평균)")
            d1,d2 = st.columns(2)
            with d1: st.metric("아세트아미노펜 시럽", f"{ctx.get('apap_ml')} mL")
            with d2: st.metric("이부프로펜 시럽", f"{ctx.get('ibu_ml')} mL")
        else:
            st.subheader("🌡️ 해열제(성인) 참고")
            st.write("- 아세트아미노펜 500–1,000 mg 1회, 1일 최대 3,000 mg")
            st.write("- 이부프로펜 200–400 mg 1회, 1일 최대 1,200 mg")

    elif m == "소아":
        st.subheader("👶 증상 요약")
        sy = ctx.get("symptoms", {})
        sy_cols = st.columns(4)
        for i, k in enumerate(sy.keys()):
            with sy_cols[i % 4]: st.metric(k, sy[k])

        st.subheader("🌡️ 해열제 1회분(평균)")
        d1,d2 = st.columns(2)
        with d1: st.metric("아세트아미노펜 시럽", f"{ctx.get('apap_ml')} mL")
        with d2: st.metric("이부프로펜 시럽", f"{ctx.get('ibu_ml')} mL")

    st.stop()
