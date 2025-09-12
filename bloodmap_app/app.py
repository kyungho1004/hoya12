# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import date

from core_utils import nickname_pin, clean_num, schedule_block
from drug_db import DRUG_DB, ensure_onco_drug_db, display_label
from onco_map import build_onco_map, auto_recs_by_dx, dx_display
from ui_results import results_only_after_analyze, render_adverse_effects, collect_top_ae_alerts
from lab_diet import lab_diet_guides
from peds_profiles import get_symptom_options
from peds_dose import acetaminophen_ml, ibuprofen_ml

# ---------------- 초기화 ----------------
ensure_onco_drug_db(DRUG_DB)
ONCO_MAP = build_onco_map()

st.set_page_config(page_title="BloodMap — 피수치가이드", page_icon="🩸", layout="centered")
st.title("BloodMap — 피수치가이드")

# 고지 + 즐겨찾기 + 체온계 + 카페
st.info(
    "이 앱은 의료행위가 아니며, **참고용**입니다. 진단·치료를 **대체하지 않습니다**.\n"
    "약 변경/복용 중단 등은 반드시 주치의와 상의하세요.\n"
    "이 앱은 개인정보를 수집하지 않으며, 어떠한 개인정보 입력도 요구하지 않습니다.\n\n"
    "⭐ **즐겨찾기**: 특수검사 제목 옆의 ★ 버튼을 누르면 상단 '즐겨찾기' 칩으로 고정됩니다.\n"
    "🏠 가능하면 **가정용 체온계**로 측정한 값을 입력하세요."
)
st.markdown("문의/버그 제보는 **[피수치 가이드 공식카페](https://cafe.naver.com/bloodmap)** 를 이용해주세요.")

nick, pin, key = nickname_pin()
st.divider()
has_key = bool(nick and pin and len(pin) == 4)

# ---------------- 유틸 ----------------
def _fever_bucket_from_temp(temp: float) -> str:
    if temp is None or temp < 37.0: return "없음"
    if temp < 37.5: return "37~37.5"
    if temp < 38.0: return "37.5~38"
    if temp < 38.5: return "37.5~38"
    if temp < 39.0: return "38.5~39"
    return "39+"

def _peds_diet_fallback(sym: dict, disease: str|None=None) -> list[str]:
    tips = []
    temp = (sym or {}).get("체온", 0) or 0
    symptom_days = int((sym or {}).get("증상일수", 0) or 0)
    diarrhea = (sym or {}).get("설사", "")
    if symptom_days >= 2:
        tips.append("증상 2일 이상 지속 → 수분·전해질 보충(ORS) 및 탈수 관찰")
    if diarrhea in ["4~6회","7회 이상"]:
        tips.append("기름지고 자극적인 음식 제한, 바나나·쌀죽·사과퓨레·토스트(BRAT) 참고")
    if temp >= 38.5:
        tips.append("체온 관리: 얇게 입히고 미온수 보온, 해열제는 1회분만 사용")
    tips.append("식사는 소량씩 자주, 구토 시 30분 쉬었다가 맑은 수분부터 재개")
    if disease:
        if disease in ["로타","장염","노로"]:
            tips.append("설사 멎을 때까지 유제품·과일주스는 줄이기")
        if disease in ["편도염","아데노"]:
            tips.append("따뜻한 수분·연식(죽/수프)으로 목 통증 완화")
    return tips

def _safe_label(k):
    try:
        return display_label(k)
    except Exception:
        return str(k)

def _filter_known(keys):
    return [k for k in (keys or []) if k in DRUG_DB]

def _export_report(ctx: dict, lines_blocks=None):
    footer = (
        "\n\n---\n"
        "본 수치는 참고용이며, 해석 결과는 개발자와 무관합니다.\n"
        "약 변경, 복용 중단 등은 반드시 주치의와 상의 후 결정하시기 바랍니다.\n"
        "이 앱은 개인정보를 절대 수집하지 않으며, 어떠한 개인정보 입력도 요구하지 않습니다.\n"
        "버그/문의는 [피수치 가이드 공식카페](https://cafe.naver.com/bloodmap) 를 통해 해주세요.\n"
    )
    title = f"# BloodMap 결과 ({ctx.get('mode','')})\n\n"
    body = []
    if ctx.get("mode") == "암":
        body.append(f"- 카테고리: {ctx.get('group')}")
        body.append(f"- 진단: {ctx.get('dx_label') or ctx.get('dx')}")
    if ctx.get("mode") in ["소아","일상"]:
        body.append(f"- 대상: {ctx.get('who','소아')}")
        if ctx.get("symptoms"):
            body.append("- 증상: " + ", ".join(f"{k}:{v}" for k,v in ctx["symptoms"].items()))
        if ctx.get("temp") is not None:
            body.append(f"- 체온: {ctx.get('temp')} ℃")
        if ctx.get("days_since_onset") is not None:
            body.append(f"- 경과일수: {ctx.get('days_since_onset')}일")
    if ctx.get("preds"):
        preds_text = "; ".join(f"{p['label']}({p['score']})" for p in ctx["preds"])
        body.append(f"- 자동 추정: {preds_text}")
    if ctx.get("triage"):
        body.append(f"- 트리아지: {ctx['triage']}")
    if ctx.get("labs"):
        labs_t = "; ".join(f"{k}:{v}" for k,v in ctx["labs"].items() if v is not None)
        if labs_t:
            body.append(f"- 주요 수치: {labs_t}")
    if lines_blocks:
        for title2, lines in lines_blocks:
            if lines:
                body.append(f"\n## {title2}\n" + "\n".join(f"- {L}" for L in lines))
    md = title + "\n".join(body) + footer
    txt = md.replace("# ","").replace("## ","")
    return md, txt

# ---------------- 모드 선택 ----------------
mode = st.radio("모드 선택", ["암", "일상", "소아"], horizontal=True)

# ---------------- 암 모드 ----------------
if mode == "암":
    st.markdown("### 1) 암 선택")
    group = st.selectbox("암 카테고리", ["혈액암","림프종","고형암","육종","희귀암"])
    dx_options = list(ONCO_MAP.get(group, {}).keys())

    def _dx_fmt(opt: str) -> str:
        try: return dx_display(group, opt)
        except Exception: return f"{group} - {opt}"

    dx = st.selectbox("진단(영문+한글)", dx_options or ["직접 입력"], format_func=_dx_fmt)
    if dx == "직접 입력":
        dx = st.text_input("진단(영문/축약 직접 입력)", value="")
    if dx: st.caption(_dx_fmt(dx))

    # (자동 예시 섹션 삭제됨)

    st.markdown("### 2) 개인 선택")
    from drug_db import picklist, key_from_label
    rec_local = auto_recs_by_dx(group, dx, DRUG_DB, ONCO_MAP)  # 옵션 생성용
    chemo_opts    = picklist(rec_local.get("chemo", []))
    targeted_opts = picklist(rec_local.get("targeted", []))
    abx_opts      = picklist([
        "Piperacillin/Tazobactam","Cefepime","Meropenem","Imipenem/Cilastatin","Aztreonam",
        "Amikacin","Vancomycin","Linezolid","Daptomycin","Ceftazidime","Levofloxacin","TMP-SMX",
        "Metronidazole","Amoxicillin/Clavulanate"
    ])
    c1,c2,c3 = st.columns(3)
    with c1: user_chemo_labels = st.multiselect("항암제(개인)", chemo_opts, default=[])
    with c2: user_targeted_labels = st.multiselect("표적/면역(개인)", targeted_opts, default=[])
    with c3: user_abx_labels = st.multiselect("항생제(개인)", abx_opts, default=[])
    user_chemo    = [key_from_label(x) for x in user_chemo_labels]
    user_targeted = [key_from_label(x) for x in user_targeted_labels]
    user_abx      = [key_from_label(x) for x in user_abx_labels]

    st.markdown("### 3) 피수치 입력 (숫자만)")
    LABS_ORDER = [
        ("WBC","WBC(백혈구)"), ("Hb","Hb(혈색소)"), ("PLT","PLT(혈소판)"), ("ANC","ANC(호중구)"),
        ("Ca","Ca(칼슘)"), ("Na","Na(소디움)"), ("K","K(칼륨)"),
        ("Alb","Alb(알부민)"), ("Glu","Glu(혈당)"), ("TP","TP(총단백)"),
        ("AST","AST"), ("ALT","ALT"), ("LDH","LDH"),
        ("CRP","CRP"), ("Cr","Cr(크레아티닌)"), ("UA","UA(요산)"), ("TB","TB(총빌리루빈)"), ("BUN","BUN")
    ]
    labs = {code: clean_num(st.text_input(label, placeholder="예: 4500")) for code, label in LABS_ORDER}

    # 특수검사
    from special_tests import special_tests_ui
    sp_lines = special_tests_ui()
    lines_blocks = []
    if sp_lines: lines_blocks.append(("특수검사 해석", sp_lines))

    # 저장/그래프
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
            "labs": labs, "user_chemo": user_chemo, "user_targeted": user_targeted, "user_abx": user_abx,
            "lines_blocks": lines_blocks
        }
    schedule_block()

# ---------------- 일상 모드 ----------------
elif mode == "일상":
    st.markdown("### 1) 대상 선택")
    who = st.radio("대상", ["소아","성인"], horizontal=True)
    days_since_onset = st.number_input("증상 시작 후 경과일수(일)", min_value=0, step=1, value=0)
    st.markdown("### 2) 증상 체크(간단)")

    if who == "소아":
        from peds_rules import predict_from_symptoms, triage_advise
        opts = get_symptom_options("기본")
        c1,c2,c3,c4,c5 = st.columns(5)
        with c1: nasal = st.selectbox("콧물", opts["콧물"])
        with c2: cough = st.selectbox("기침", opts["기침"])
        with c3: diarrhea = st.selectbox("설사(횟수/일)", opts["설사"])
        with c4: symptom_days = st.number_input("**증상일수**(일)", min_value=0, step=1, value=0)
        with c5: temp = st.number_input("체온(℃)", min_value=0.0, step=0.1, value=0.0)

        age_m = st.number_input("나이(개월)", min_value=0, step=1)
        weight = st.number_input("체중(kg)", min_value=0.0, step=0.1)

        apap_ml, apap_w = acetaminophen_ml(age_m, weight or None)
        ibu_ml,  ibu_w  = ibuprofen_ml(age_m, weight or None)
        d1,d2 = st.columns(2)
        with d1: st.metric("아세트아미노펜 시럽", f"{apap_ml} mL", help=f"계산 체중 {apap_w} kg 기준")
        with d2: st.metric("이부프로펜 시럽",   f"{ibu_ml} mL",  help=f"계산 체중 {ibu_w} kg 기준")

        fever_cat = _fever_bucket_from_temp(temp)
        symptoms = {"콧물":nasal,"기침":cough,"설사":diarrhea,"증상일수":symptom_days,"체온":temp,"발열":fever_cat}
        preds = predict_from_symptoms(symptoms, temp, age_m)
        st.markdown("#### 🤖 증상 기반 자동 추정")
        for p in preds: st.write(f"- **{p['label']}** · 신뢰도 {p['score']}점")
        triage = triage_advise(temp, age_m, diarrhea)
        st.info(triage)

        st.subheader("🥗 식이가이드")
        tips = _peds_diet_fallback(symptoms, disease=None)
        for L in tips: st.write("- " + L)

        if st.button("🔎 해석하기", key="analyze_daily_child"):
            st.session_state["analyzed"] = True
            st.session_state["analysis_ctx"] = {
                "mode":"일상","who":"소아","symptoms":symptoms,
                "temp":temp,"age_m":age_m,"weight":weight or None,
                "apap_ml":apap_ml,"ibu_ml":ibu_ml,"preds":preds,"triage":triage,
                "days_since_onset": days_since_onset
            }

    else:  # 성인
        from adult_rules import predict_from_symptoms, triage_advise, get_adult_options
        opts = get_adult_options()
        c1,c2,c3,c4,c5 = st.columns(5)
        with c1: nasal = st.selectbox("콧물", opts["콧물"])
        with c2: cough = st.selectbox("기침", opts["기침"])
        with c3: diarrhea = st.selectbox("설사(횟수/일)", opts["설사"])
        with c4: symptom_days = st.number_input("**증상일수**(일)", min_value=0, step=1, value=0)
        with c5: temp = st.number_input("체온(℃)", min_value=0.0, step=0.1, value=0.0)

        comorb = st.multiselect("주의 대상", ["임신 가능성","간질환 병력","신질환 병력","위장관 궤양/출혈력","항응고제 복용","고령(65+)"])

        fever_cat = _fever_bucket_from_temp(temp)
        symptoms = {"콧물":nasal,"기침":cough,"설사":diarrhea,"증상일수":symptom_days,"체온":temp,"발열":fever_cat}

        preds = predict_from_symptoms(symptoms, temp, comorb)
        st.markdown("#### 🤖 증상 기반 자동 추정")
        for p in preds: st.write(f"- **{p['label']}** · 신뢰도 {p['score']}점")
        triage = triage_advise(temp, comorb)
        st.info(triage)

        st.markdown("#### 🌡️ 해열제(성인) 참고")
        st.write("- 아세트아미노펜 500–1,000 mg 1회, 1일 최대 3,000 mg (간질환·음주 시 감량)")
        st.write("- 이부프로펜 200–400 mg 1회, 1일 최대 1,200 mg (위장관출혈/임신 3기 금기)")

        if st.button("🔎 해석하기", key="analyze_daily_adult"):
            st.session_state["analyzed"] = True
            st.session_state["analysis_ctx"] = {
                "mode":"일상","who":"성인","symptoms":symptoms,
                "temp":temp,"comorb":comorb,"preds":preds,"triage":triage,
                "days_since_onset": days_since_onset
            }

# ---------------- 소아(질환) 모드 ----------------
else:
    ctop = st.columns(4)
    with ctop[0]: disease = st.selectbox("소아 질환", ["로타","독감","RSV","아데노","마이코","수족구","편도염","코로나","중이염"], index=0)
    with ctop[1]: temp = st.number_input("체온(℃)", min_value=0.0, step=0.1)
    with ctop[2]: age_m = st.number_input("나이(개월)", min_value=0, step=1)
    with ctop[3]: weight = st.number_input("체중(kg)", min_value=0.0, step=0.1)

    opts = get_symptom_options(disease)
    st.markdown("### 증상 체크")
    c1,c2,c3,c4 = st.columns(4)
    with c1: nasal = st.selectbox("콧물", opts["콧물"])
    with c2: cough = st.selectbox("기침", opts["기침"])
    with c3: diarrhea = st.selectbox("설사(횟수/일)", opts["설사"])
    with c4: symptom_days = st.number_input("**증상일수**(일)", min_value=0, step=1, value=0)

    apap_ml, apap_w = acetaminophen_ml(age_m, weight or None)
    ibu_ml,  ibu_w  = ibuprofen_ml(age_m, weight or None)
    dc = st.columns(2)
    with dc[0]: st.metric("아세트아미노펜 시럽", f"{apap_ml} mL", help=f"계산 체중 {apap_w} kg")
    with dc[1]: st.metric("이부프로펜 시럽", f"{ibu_ml} mL", help=f"계산 체중 {ibu_w} kg")

    fever_cat = _fever_bucket_from_temp(temp)
    symptoms = {"콧물":nasal,"기침":cough,"설사":diarrhea,"증상일수":symptom_days,"체온":temp,"발열":fever_cat}

    if st.button("🔎 해석하기", key="analyze_peds"):
        st.session_state["analyzed"] = True
        st.session_state["analysis_ctx"] = {
            "mode":"소아", "disease": disease,
            "symptoms": symptoms,
            "temp": temp, "age_m": age_m, "weight": weight or None,
            "apap_ml": apap_ml, "ibu_ml": ibu_ml, "vals": {}
        }

# ---------------- 결과 게이트 ----------------
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

        # 중요 경고 요약
        alerts = collect_top_ae_alerts((_filter_known(ctx.get("user_chemo"))) + (_filter_known(ctx.get("user_abx"))))
        if alerts: st.error("\n".join(alerts))

        # 선택 요약 (선택된 것만)
        st.subheader("🗂️ 선택 요약")
        def _render_selected(title, keys):
            keys = _filter_known(keys)
            if not keys: return 0
            st.markdown(f"**{title}**")
            for k in keys:
                st.write("- " + _safe_label(k))
            return len(keys)
        shown = 0
        shown += _render_selected("항암제(개인)", ctx.get("user_chemo"))
        shown += _render_selected("표적/면역(개인)", ctx.get("user_targeted"))
        shown += _render_selected("항생제(개인)", ctx.get("user_abx"))
        if shown == 0:
            st.caption("선택한 약물이 없습니다.")

        # ✅ 부작용 — 옛날처럼 st.markdown(...)로 감싸지 말고, 새 시그니처대로 직접 렌더
        st.subheader("💊 항암제(세포독성) 부작용")
        render_adverse_effects(st, _filter_known(ctx.get("user_chemo")), DRUG_DB)
        st.subheader("🧫 항생제 부작용")
        render_adverse_effects(st, _filter_known(ctx.get("user_abx")), DRUG_DB)

        # 식이가이드 (랩 기반)
        st.subheader("🥗 피수치 기반 식이가이드 (예시)")
        lines = lab_diet_guides(labs, heme_flag=(ctx.get("group")=="혈액암"))
        for L in lines: st.write("- " + L)

        # 특수검사 해석
        for title2, lines2 in (ctx.get("lines_blocks") or []):
            if lines2:
                st.subheader("🧬 " + title2)
                for L in lines2: st.write("- " + L)

        # 보고서 저장
        st.subheader("📝 보고서 저장")
        md, txt = _export_report(ctx, ctx.get("lines_blocks"))
        st.download_button("⬇️ Markdown (.md)", data=md, file_name="BloodMap_Report.md")
        st.download_button("⬇️ 텍스트 (.txt)", data=txt, file_name="BloodMap_Report.txt")

    elif m == "일상":
        st.subheader("👪 증상 요약")
        sy = ctx.get("symptoms", {})
        sy_cols = st.columns(4)
        for i, k in enumerate(sy.keys()):
            with sy_cols[i % 4]: st.metric(k, sy[k])
        if ctx.get("days_since_onset") is not None:
            st.caption(f"경과일수: {ctx['days_since_onset']}일")
        if ctx.get("temp") is not None:
            st.caption(f"체온: {ctx['temp']} ℃")

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

            st.subheader("🥗 식이가이드")
            tips = _peds_diet_fallback(ctx.get("symptoms", {}), disease=None)
            for L in tips: st.write("- " + L)
        else:
            st.subheader("🌡️ 해열제(성인) 참고")
            st.write("- 아세트아미노펜 500–1,000 mg 1회, 1일 최대 3,000 mg")
            st.write("- 이부프로펜 200–400 mg 1회, 1일 최대 1,200 mg")

        # 보고서 저장
        st.subheader("📝 보고서 저장")
        md, txt = _export_report(ctx, None)
        st.download_button("⬇️ Markdown (.md)", data=md, file_name="BloodMap_Report.md")
        st.download_button("⬇️ 텍스트 (.txt)", data=txt, file_name="BloodMap_Report.txt")

    elif m == "소아":
        st.subheader("👶 증상 요약")
        sy = ctx.get("symptoms", {})
        sy_cols = st.columns(4)
        for i, k in enumerate(sy.keys()):
            with sy_cols[i % 4]: st.metric(k, sy[k])
        if ctx.get("temp") is not None:
            st.caption(f"체온: {ctx['temp']} ℃")

        st.subheader("🌡️ 해열제 1회분(평균)")
        d1,d2 = st.columns(2)
        with d1: st.metric("아세트아미노펜 시럽", f"{ctx.get('apap_ml')} mL")
        with d2: st.metric("이부프로펜 시럽", f"{ctx.get('ibu_ml')} mL")

        st.subheader("🥗 식이가이드")
        tips = _peds_diet_fallback(ctx.get("symptoms", {}), disease=ctx.get("disease"))
        for L in tips: st.write("- " + L)

        # 보고서 저장
        st.subheader("📝 보고서 저장")
        md, txt = _export_report(ctx, None)
        st.download_button("⬇️ Markdown (.md)", data=md, file_name="BloodMap_Report.md")
        st.download_button("⬇️ 텍스트 (.txt)", data=txt, file_name="BloodMap_Report.txt")

    st.caption("본 도구는 참고용입니다. 의료진의 진단/치료를 대체하지 않습니다.")
    st.caption("문의/버그 제보: [피수치 가이드 공식카페](https://cafe.naver.com/bloodmap)")
    st.stop()
