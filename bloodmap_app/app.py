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
from pdf_export import export_md_to_pdf

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


def _one_line_selection(ctx: dict) -> str:
    def names(keys):
        return ", ".join(_safe_label(k) for k in _filter_known(keys))
    parts = []
    a = names(ctx.get("user_chemo"))
    if a: parts.append(f"항암제: {a}")
    b = names(ctx.get("user_targeted"))
    if b: parts.append(f"표적/면역: {b}")
    c = names(ctx.get("user_abx"))
    if c: parts.append(f"항생제: {c}")
    return " · ".join(parts) if parts else "선택된 약물이 없습니다."

_PEDS_NOTES = {
    "RSV": "모세기관지염: 아기 하기도에 가래가 끼고 배출이 어려워 쌕쌕/호흡곤란이 생길 수 있어요.",
    "로타": "로타바이러스 장염: 구토·물설사로 탈수 위험, ORS로 수분 보충이 중요해요.",
    "노로": "노로바이러스 장염: 집단 유행, 구토가 두드러지며 철저한 손위생이 중요해요.",
    "독감": "인플루엔자: 갑작스런 고열·근육통, 48시간 내 항바이러스제 고려가 돼요.",
    "아데노": "아데노바이러스: 결막염/인두염/장염 등 다양한 증상, 고열이 오래갈 수 있어요.",
    "마이코": "마이코플라즈마: 마른기침이 오래가며 비정형폐렴 가능, 항생제 필요 여부는 진료로 확인하세요.",
    "수족구": "수족구병: 손·발·입 수포/궤양 + 열, 탈수 주의. 대개 대증치료로 호전돼요.",
    "편도염": "편도염/인후염: 목통증·고열, 세균성 의심 시 항생제를 쓰기도 해요.",
    "코로나": "코로나19: 발열·기침·인후통, 고위험군은 모니터링과 격리 수칙이 중요해요.",
    "중이염": "급성 중이염: 귀통증·열, 진찰 결과에 따라 진통제/항생제 여부를 결정해요.",
}
def disease_short_note(name: str) -> str:
    return _PEDS_NOTES.get(name, "")

def _export_buttons(md: str, txt: str):
    st.download_button("⬇️ Markdown (.md)", data=md, file_name="BloodMap_Report.md")
    st.download_button("⬇️ 텍스트 (.txt)", data=txt, file_name="BloodMap_Report.txt")
    try:
        pdf_bytes = export_md_to_pdf(md)
        st.download_button("⬇️ PDF (.pdf)", data=pdf_bytes, file_name="BloodMap_Report.pdf", mime="application/pdf")
    except Exception as e:
        st.caption(f"PDF 변환 중 오류: {e}")


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
            body.append("- 증상: " + ", ".join(f"{k}:{v}" for k,v in ctx['symptoms'].items()))
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

# 약물 요약(암 모드 전용) — 영문+한글 병기
if ctx.get("mode") == "암":
    from drug_db import display_label
    _chemo = [display_label(x) for x in (ctx.get("user_chemo") or []) if x]
    _targ  = [display_label(x) for x in (ctx.get("user_targeted") or []) if x]
    _abx   = [display_label(x) for x in (ctx.get("user_abx") or []) if x]
    if _chemo:
        body.append("\\n## 🧪 항암제(개인)\\n" + "\\n".join(f"- {x}" for x in _chemo))
    if _targ:
        body.append("\\n## 💉 표적/면역(개인)\\n" + "\\n".join(f"- {x}" for x in _targ))
    if _abx:
        body.append("\\n## 🧫 항생제(개인)\\n" + "\\n".join(f"- {x}" for x in _abx))

    if ctx.get("diet_lines"):
        diet = [str(x) for x in ctx["diet_lines"] if x]
        if diet:
            body.append("\n## 🍽️ 식이가이드\n" + "\n".join(f"- {L}" for L in diet))
    if ctx.get("short_note"):
        body.append("\n## ℹ️ 짧은 해석\n- " + str(ctx["short_note"]))
    if ctx.get("mode") == "암":
        summary = _one_line_selection(ctx)
        if summary:
            body.append("\n## 🗂️ 선택 요약\n- " + summary)
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

    # (예시 섹션 완전 제거)

    st.markdown("### 2) 개인 선택")
    from drug_db import picklist, key_from_label
    rec_local = auto_recs_by_dx(group, dx, DRUG_DB, ONCO_MAP)  # 옵션 생성용
    chemo_opts    = picklist(rec_local.get("chemo", []))
    targeted_opts = picklist(rec_local.get("targeted", []))
    abx_defaults = [
        "Piperacillin/Tazobactam","Cefepime","Meropenem","Imipenem/Cilastatin","Aztreonam",
        "Amikacin","Vancomycin","Linezolid","Daptomycin","Ceftazidime","Levofloxacin","TMP-SMX",
        "Metronidazole","Amoxicillin/Clavulanate"
    ]
    abx_opts      = picklist(rec_local.get("abx") or abx_defaults)
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
        for p in preds:
            _n = disease_short_note(p['label'])
            extra = f" — {_n}" if _n else ""
            st.write(f"- **{p['label']}** · 신뢰도 {p['score']}점{extra}")
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
        for p in preds:
            _n = disease_short_note(p['label'])
            extra = f" — {_n}" if _n else ""
            st.write(f"- **{p['label']}** · 신뢰도 {p['score']}점{extra}")
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
    note = disease_short_note(disease)
    if note:
        st.caption(f"ℹ️ {note}")
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
            "mode":"소아", "disease": disease, "short_note": note,
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

        st.subheader("🗂️ 선택 요약")
        st.write(_one_line_selection(ctx))

        # 부작용
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
        _export_buttons(md, txt)

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
            for p in preds:
                _n = disease_short_note(p['label'])
                extra = f" — {_n}" if _n else ""
                st.write(f"- **{p['label']}** · 신뢰도 {p['score']}점{extra}")
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
        md, txt = _export_report(ctx, ctx.get("lines_blocks"))
        _export_buttons(md, txt)

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
        md, txt = _export_report(ctx, ctx.get("lines_blocks"))
        _export_buttons(md, txt)

    st.caption("본 도구는 참고용입니다. 의료진의 진단/치료를 대체하지 않습니다.")
    st.caption("문의/버그 제보: [피수치 가이드 공식카페](https://cafe.naver.com/bloodmap)")
    st.stop()

