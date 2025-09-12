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

st.set_page_config(page_title="BloodMap 피수치 해석", page_icon="🩸", layout="centered")

# 세션 초기화
if "nick" not in st.session_state:
    st.session_state["nick"] = nickname_pin()
if "lab_hist" not in st.session_state:
    st.session_state["lab_hist"] = {}

# ---------------- 유틸 ----------------
def _fmt_drug_label(k: str) -> str:
    # 약물 표시는 '영문,한글' 기본
    return display_label(k, DRUG_DB, style="comma")

def _pill(text: str, color: str = "blue"):
    st.markdown(f"<span style='background:{color};color:white;padding:2px 8px;border-radius:12px'>{text}</span>", unsafe_allow_html=True)

def _fever_bucket_from_temp(temp: float|None) -> str:
    if temp is None: return ""
    if temp < 37.5: return "정상"
    if temp < 38.0: return "37.5~38"
    if temp < 38.5: return "38.0~38.5"
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

    # 공통 요약
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

    # 특수검사/기타 블록
    if lines_blocks:
        for title2, lines in lines_blocks:
            if lines:
                body.append(f"\n## {title2}\n" + "\n".join(f"- {L}" for L in lines))

    # 약물 요약(암 모드 전용) — 영문,한글 병기
    if ctx.get("mode") == "암":
        _chemo = [display_label(x) for x in (ctx.get("user_chemo") or []) if x]
        _targ  = [display_label(x) for x in (ctx.get("user_targeted") or []) if x]
        _abx   = [display_label(x) for x in (ctx.get("user_abx") or []) if x]
        if _chemo:
            body.append("\n## 🧪 항암제(개인)\n" + "\n".join(f"- {x}" for x in _chemo))
        if _targ:
            body.append("\n## 💉 표적/면역(개인)\n" + "\n".join(f"- {x}" for x in _targ))
        if _abx:
            body.append("\n## 🧫 항생제(개인)\n" + "\n".join(f"- {x}" for x in _abx))

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
        ("WBC","WBC,백혈구"), ("Hb","Hb,혈색소"), ("PLT","PLT,혈소판"), ("ANC","ANC,호중구"),
        ("Ca","Ca,칼슘"), ("Na","Na,소디움"), ("K","K,칼륨"),
        ("Alb","Alb,알부민"), ("Glu","Glu,혈당"), ("TP","TP,총단백"),
        ("AST","AST"), ("ALT","ALT"), ("LDH","LDH"),
        ("CRP","CRP"), ("Cr","Cr,크레아티닌"), ("UA","UA,요산"), ("TB","TB,총빌리루빈"), ("BUN","BUN")
    ]
    labs = {code: clean_num(st.text_input(label, placeholder="예: 4500")) for code, label in LABS_ORDER}

    # 특수검사
    from special_tests import special_tests_ui
    sp_lines = special_tests_ui()
    lines_blocks = []
    if sp_lines: lines_blocks.append(("특수검사 해석", sp_lines))

    # 저장/그래프
    st.markdown("#### 💾 저장/그래프")
    key = st.session_state["nick"]
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
    has_key = bool(key)
    if has_key and isinstance(dfh, pd.DataFrame) and not dfh.empty:
        st.markdown("##### 📊 추이 그래프")
        nonnull = [c for c in dfh.columns if (c!="Date" and dfh[c].notna().any())]
        default_pick = [c for c in ["WBC,백혈구","Hb,혈색소","PLT,혈소판","CRP","ANC,호중구"] if c in nonnull]
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

# ---------------- 일상 모드 ----------------
elif mode == "일상":
    st.markdown("### 🏠 일상 관리")
    st.info("일상 모드는 간단한 수치 입력과 식이 가이드를 제공합니다.", icon="ℹ️")

    LABS_ORDER = [
        ("WBC","WBC,백혈구"), ("Hb","Hb,혈색소"), ("PLT","PLT,혈소판"),
        ("CRP","CRP"), ("Glu","Glu,혈당")
    ]
    labs = {code: clean_num(st.text_input(label, placeholder="예: 4500")) for code, label in LABS_ORDER}

    # 식이 가이드
    st.markdown("### 🍽️ 맞춤 식이 가이드")
    diet_lines = lab_diet_guides(labs, context="adult")
    for line in diet_lines:
        st.write("- " + line)

    if st.button("🔎 해석하기", key="analyze_daily_adult"):
        st.session_state["analyzed"] = True
        st.session_state["analysis_ctx"] = {
            "mode":"일상", "labs": labs, "who":"성인"
        }

# ---------------- 소아 모드 ----------------
else:
    st.markdown("### 🧒 소아 증상/수치")
    who = st.selectbox("대상", ["소아"])
    age_m = clean_num(st.text_input("나이(개월)", placeholder="예: 18"))
    weight = clean_num(st.text_input("체중(kg)", placeholder="예: 11.2"))

    # 증상 입력
    st.markdown("#### 1) 증상 입력")
    opts = get_symptom_options()
    col1, col2, col3, col4 = st.columns(4)
    symptoms = {}
    with col1:
        symptoms["콧물"] = st.selectbox("콧물", opts["콧물"])
        symptoms["기침"] = st.selectbox("기침", opts["기침"])
        symptoms["설사"] = st.selectbox("설사", opts["설사"])
    with col2:
        symptoms["구토"] = st.selectbox("구토", opts["구토"])
        symptoms["인후통"] = st.selectbox("인후통", opts["인후통"])
        symptoms["복통"] = st.selectbox("복통", opts["복통"])
    with col3:
        symptoms["피부발진"] = st.selectbox("피부발진", opts["피부발진"])
        symptoms["호흡곤란"] = st.selectbox("호흡곤란", opts["호흡곤란"])
        symptoms["무기력"] = st.selectbox("무기력", opts["무기력"])
    with col4:
        symptoms["증상일수"] = st.selectbox("지속일수", ["0일","1일","2일","3일 이상"])
        temp = clean_num(st.text_input("체온(℃)", placeholder="예: 38.2"))
        symptoms["체온"] = temp

    # 자동 추정/트리아지(간단)
    preds = [{"label": "바이럴 상기도감염", "score": 0.6}]
    triage = "가정 경과관찰" if (temp or 0) < 38.5 else "해열제 + 경과관찰"

    # 검사 수치 (옵션)
    st.markdown("#### 2) 선택 수치")
    LABS_ORDER = [
        ("WBC","WBC,백혈구"), ("Hb","Hb,혈색소"), ("PLT","PLT,혈소판"), ("CRP","CRP")
    ]
    labs = {code: clean_num(st.text_input(label, placeholder="예: 4500")) for code, label in LABS_ORDER}

    # 식이 가이드 (fallback + 조건)
    st.markdown("### 🍽️ 식이 가이드")
    diet_lines = lab_diet_guides(labs, context="peds")
    diet_lines += _peds_diet_fallback(symptoms)
    for line in diet_lines:
        st.write("- " + line)

    # 해열제 1회분 계산 (평균)
    st.markdown("### 🌡️ 해열제 1회분(평균)")
    d1, d2 = st.columns(2)
    with d1:
        st.metric("아세트아미노펜 시럽", f"{acetaminophen_ml(weight)} ml")
    with d2:
        st.metric("이부프로펜 시럽", f"{ibuprofen_ml(weight)} ml")

    if st.button("🔎 해석하기", key="analyze_peds"):
        st.session_state["analyzed"] = True
        st.session_state["analysis_ctx"] = {
            "mode":"소아", "who":who, "age_m":age_m, "weight":weight,
            "symptoms": symptoms, "temp": temp, "preds": preds, "triage": triage, "labs": labs
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
                with rcols[i]:
                    st.metric(k, v)
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
        n1 = _render_selected("항암제(개인)", ctx.get("user_chemo"))
        n2 = _render_selected("표적/면역(개인)", ctx.get("user_targeted"))
        n3 = _render_selected("항생제(개인)", ctx.get("user_abx"))
        if (n1+n2+n3)==0:
            st.info("선택된 항암/표적/항생제가 없습니다.")

        st.subheader("📌 부작용 상세")
        st.markdown(render_adverse_effects(ctx.get("user_chemo"), ctx.get("user_targeted"), ctx.get("user_abx"), DRUG_DB), unsafe_allow_html=True)

        st.subheader("🥗 식이가이드")
        tips = lab_diet_guides(labs, context="adult")
        for L in tips: st.write("- " + L)

        # 보고서 저장
        st.subheader("📝 보고서 저장")
        md, txt = _export_report(ctx, None)
        st.download_button("⬇️ Markdown (.md)", data=md, file_name="BloodMap_Report.md")
        st.download_button("⬇️ 텍스트 (.txt)", data=txt, file_name="BloodMap_Report.txt")

    elif m == "일상":
        labs = ctx.get("labs", {})
        st.subheader("🧪 피수치 요약")
        if labs:
            rcols = st.columns(len(labs))
            for i, (k, v) in enumerate(labs.items()):
                with rcols[i]:
                    st.metric(k, v)

        st.subheader("🥗 식이가이드")
        tips = lab_diet_guides(labs, context="adult")
        for L in tips: st.write("- " + L)

        # 보고서 저장
        st.subheader("📝 보고서 저장")
        md, txt = _export_report(ctx, None)
        st.download_button("⬇️ Markdown (.md)", data=md, file_name="BloodMap_Report.md")
        st.download_button("⬇️ 텍스트 (.txt)", data=txt, file_name="BloodMap_Report.txt")

    else:  # 소아
        labs = ctx.get("labs", {})
        st.subheader("🧪 피수치 요약")
        if labs:
            rcols = st.columns(len(labs))
            for i, (k, v) in enumerate(labs.items()):
                with rcols[i]:
                    st.metric(k, v)

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
