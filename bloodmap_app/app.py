# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import date, datetime

from core_utils import nickname_pin, clean_num, round_half, temp_band, rr_thr_by_age_m, schedule_block
from drug_db import DRUG_DB, ensure_onco_drug_db
from onco_map import build_onco_map, auto_recs_by_dx, dx_display
from ui_results import results_only_after_analyze, render_adverse_effects
from lab_diet import lab_diet_guides
from peds_profiles import get_symptom_options
from peds_dose import acetaminophen_ml, ibuprofen_ml

# Init
ensure_onco_drug_db(DRUG_DB)
ONCO_MAP = build_onco_map()

st.set_page_config(page_title="블러드맵 피수치가이드 (모듈화)", page_icon="🩸", layout="centered")
st.title("BloodMap — 모듈화 버전")

# 공통 고지
st.info(
    "본 수치는 참고용이며, 해석 결과는 개발자와 무관합니다.\n"
    "약 변경/복용 중단 등은 반드시 주치의와 상의하세요.\n"
    "이 앱은 개인정보를 수집하지 않으며, 어떠한 개인정보 입력도 요구하지 않습니다."
)

# ----------- 별명+PIN -----------
nick, pin, key = nickname_pin()
st.divider()

# ----------- 모드 선택 -----------
mode = st.radio("모드 선택", ["암", "소아"], horizontal=True)


report_sections = []

# ------------------ 암 모드 ------------------
if mode == "암":
    st.markdown("### 1) 암 선택")
    group = st.selectbox("암 카테고리", ["혈액암","림프종","고형암","육종","희귀암"])
    dx_options = list(ONCO_MAP.get(group, {}).keys())
    dx = st.selectbox("진단(영문)", dx_options or ["직접 입력"])
    if dx == "직접 입력":
        dx = st.text_input("진단(영문/축약 직접 입력)", value="")

    if group == "혈액암":
        msg = "혈액암 환자에서 **철분제 + 비타민 C** 복용은 흡수 촉진 가능성이 있어, **반드시 주치의와 상의 후** 복용 여부를 결정하세요."
        st.warning(msg); report_sections.append(("영양/보충제 주의", [msg]))

    st.markdown("### 2) 자동 예시(토글)")
    if st.toggle("자동 예시 보기", value=True):
        rec = auto_recs_by_dx(group, dx, DRUG_DB, ONCO_MAP)
        c = st.columns(3)
        with c[0]:
            st.markdown("**항암제(예시)**")
            for d in rec["chemo"]: st.write("- " + d)
        with c[1]:
            st.markdown("**표적/면역(예시)**")
            for d in rec["targeted"]: st.write("- " + d)
        with c[2]:
            st.markdown("**항생제(참고)**")
            for d in rec["abx"]: st.write("- " + d)

    st.markdown("### 3) 피수치 입력 (숫자만)")
    LABS_ORDER = [
        ("WBC","WBC(백혈구)"), ("Hb","Hb(혈색소)"), ("PLT","PLT(혈소판)"), ("ANC","ANC(절대호중구,면역력)"),
        ("Ca","Ca(칼슘)"), ("Na","Na(나트륨,소디움)"), ("K","K(칼륨)"), ("Alb","Alb(알부민)"), ("Glu","Glu(혈당)"),
        ("TP","TP(총단백)"), ("AST","AST(간수치)"), ("ALT","ALT(간세포)"), ("LD","LD(유산탈수효소)"),
        ("CRP","CRP(C-반응성단백,염증)"), ("Cr","Cr(크레아티닌,신장)"), ("BUN","BUN(요소질소)"), ("UA","UA(요산)"), ("Tbili","Tbili(총빌리루빈)")
    ]
    labs = {}
    for code, label in LABS_ORDER:
        v = st.text_input(label, placeholder="예: 4500")
        labs[code] = clean_num(v)


    st.markdown("### 3) 개인 선택 (영어 + 한글 병기)")
from drug_db import picklist, key_from_label

    # 분리된 키셋
    CHEMO_KEYS = [
        "ATRA","Arsenic Trioxide","Idarubicin","Daunorubicin","Ara-C","MTX","6-MP",
        "Vincristine","Cyclophosphamide","Prednisone",
        "Cisplatin","Carboplatin","Oxaliplatin","5-FU","Capecitabine","Irinotecan",
        "Docetaxel","Paclitaxel","Nab-Paclitaxel","Gemcitabine","Pemetrexed","Temozolomide",
        "Ifosfamide","Etoposide","Dactinomycin","Trabectedin","Topotecan"
    ]
    TARGETED_KEYS = [
        "Imatinib","Osimertinib","Alectinib","Crizotinib","Larotrectinib","Entrectinib","Capmatinib","Lorlatinib",
        "Selpercatinib","Pralsetinib","Sotorasib",
        "Trastuzumab","Pertuzumab","T-DM1","Trastuzumab deruxtecan","Lapatinib","Tucatinib",
        "Bevacizumab","Ramucirumab","Regorafenib","Ripretinib",
        "Cetuximab","Panitumumab",
        "Olaparib","Niraparib",
        "Palbociclib","Ribociclib","Abemaciclib",
        "Everolimus","Octreotide",
        "Pembrolizumab","Nivolumab","Atezolizumab","Durvalumab","Ipilimumab",
        "Brentuximab Vedotin","Polatuzumab Vedotin","Obinutuzumab","Rituximab"
    ]
    ABX_KEYS   = ["Piperacillin/Tazobactam","Cefepime","Meropenem","Imipenem/Cilastatin","Aztreonam","Amikacin",
                  "Vancomycin","Linezolid","Daptomycin","Ceftazidime","Levofloxacin","TMP-SMX","Metronidazole","Amoxicillin/Clavulanate"]

    # 암 진단에 맞는 치료 목록으로 동적 구성 (chemo 우선, 없으면 targeted 대체)
    rec_local = auto_recs_by_dx(group, dx, DRUG_DB, ONCO_MAP)
    CHEMO_KEYS = rec_local.get("chemo", []) or rec_local.get("targeted", [])
    chemo_opts    = picklist([k for k in CHEMO_KEYS if k in DRUG_DB])
    targeted_opts = picklist([k for k in TARGETED_KEYS if k in DRUG_DB])
    abx_opts      = picklist([k for k in ABX_KEYS if k in DRUG_DB])

    p1, p2, p3 = st.columns(3)
    with p1:
        user_chemo_labels = st.multiselect("항암제(세포독성) 선택", chemo_opts, default=[])
    with p2:
        user_abx_labels   = st.multiselect("항생제 선택", abx_opts, default=[])

    user_chemo    = [key_from_label(x) for x in user_chemo_labels]
    user_targeted = [key_from_label(x) for x in user_targeted_labels]
    user_abx      = [key_from_label(x) for x in user_abx_labels]
    
    st.markdown("#### 💾 저장/그래프")
    when = st.date_input("측정일", value=date.today())
    if st.button("📈 피수치 저장/추가"):
        st.session_state.setdefault("lab_hist", {}).setdefault(key, pd.DataFrame())
        df_prev = st.session_state["lab_hist"][key]
        row = {"Date": when.strftime("%Y-%m-%d")}
        labels = [label for _, label in LABS_ORDER]
        for code, label in LABS_ORDER:
            row[label] = labs.get(code)
        newdf = pd.DataFrame([row])
        if df_prev is None or df_prev.empty:
            df = newdf
        else:
            df = pd.concat([df_prev, newdf], ignore_index=True)
            df = df.drop_duplicates(subset=["Date"], keep="last").sort_values("Date")
        for col in (["Date"]+labels):
            if col not in df.columns: df[col] = pd.NA
        df = df.reindex(columns=(["Date"]+labels))
        st.session_state["lab_hist"][key] = df
        st.success("저장 완료!")

    dfh = st.session_state.get("lab_hist", {}).get(key)
    if not has_key:
        st.info("그래프는 별명 + PIN(4자리) 저장 시 표시됩니다.")
    elif isinstance(dfh, pd.DataFrame) and not dfh.empty:
        st.markdown("##### 📊 추이 그래프")
        nonnull_cols = [c for c in dfh.columns if (c!="Date" and dfh[c].notna().any())]
        default_pick = [c for c in ["WBC(백혈구)","Hb(혈색소)","PLT(혈소판)","CRP(C-반응성단백,염증)","ANC(절대호중구,면역력)"] if c in nonnull_cols]
        pick = st.multiselect("지표 선택", options=nonnull_cols, default=default_pick)
        if pick: st.line_chart(dfh.set_index("Date")[pick], use_container_width=True)
        st.dataframe(dfh[["Date"]+nonnull_cols], use_container_width=True, height=220)
    else:
        st.info("저장된 히스토리가 없습니다. 값을 입력하고 ‘피수치 저장/추가’를 눌러 보세요.")

    # 해석 버튼 → 결과만 하단에
    if st.button("🔎 해석하기", key="analyze_cancer"):
        st.session_state["analyzed"] = True
        st.session_state["analysis_ctx"] = {
            "mode":"암", "group":group, "dx":dx, "dx_label": dx_display(group, dx),
            "labs": labs,
            "user_chemo": user_chemo,
            "user_abx": user_abx
        }

    # 특수검사
    from special_tests import special_tests_ui
    sp_lines = special_tests_ui()
    if sp_lines:
        st.markdown("#### 🧬 특수검사 해석")
        for L in sp_lines: st.write("- "+L)
        report_sections.append(("특수검사 해석", sp_lines))

    # 스케줄
    schedule_block()

# ------------------ 소아 모드 ------------------
else:
    ctop = st.columns(3)
    with ctop[0]:
        disease = st.selectbox("소아 질환", ["로타","독감","RSV","아데노","마이코","수족구","편도염","코로나","중이염"], index=0)
    with ctop[1]:
        temp = st.number_input("체온(℃)", min_value=0.0, step=0.1)
    with ctop[2]:
        pass

    # 증상 옵션 로딩
    opts = get_symptom_options(disease)
    st.markdown("### 증상 체크")
    c1,c2,c3,c4 = st.columns(4)
    with c1: nasal = st.selectbox("콧물", opts["콧물"])
    with c2: cough = st.selectbox("기침", opts["기침"])
    with c3: diarrhea = st.selectbox("설사(횟수/일)", opts["설사"])
    with c4: fever = st.selectbox("발열", opts["발열"])

    st.markdown("#### 🔥 해열제 (1회 평균 용량 기준, mL)")
    from peds_dose import acetaminophen_ml, ibuprofen_ml
    apap_ml, apap_w = acetaminophen_ml(age_m, weight or None)
    ibu_ml,  ibu_w  = ibuprofen_ml(age_m, weight or None)
    dc = st.columns(2)
    with dc[0]: st.metric("아세트아미노펜 시럽", f"{apap_ml} mL", help=f"계산 체중 {apap_w} kg · 160 mg/5 mL, 12.5 mg/kg")
    with dc[1]: st.metric("이부프로펜 시럽", f"{ibu_ml} mL", help=f"계산 체중 {ibu_w} kg · 100 mg/5 mL, 7.5 mg/kg")

    if st.button("🔎 해석하기", key="analyze_peds"):
        st.session_state["analyzed"] = True
        st.session_state["analysis_ctx"] = {
            "mode":"소아", "disease": disease,
            "symptoms": {"콧물": nasal, "기침": cough, "설사": diarrhea, "발열": fever},
            "temp": temp, "age_m": age_m, "weight": weight or None,
            "apap_ml": apap_ml, "ibu_ml": ibu_ml,
            "vals": {}
        }

# ------------------ 결과 전용 게이트 ------------------
if results_only_after_analyze(st):
    ctx = st.session_state.get("analysis_ctx", {})
    if ctx.get("mode") == "암":
        labs = ctx.get("labs", {})
        st.subheader("🧪 피수치 요약")
        if labs:
            rcols = st.columns(len(labs))
            for i, (k, v) in enumerate(labs.items()):
                with rcols[i]:
                    st.metric(k, v)
        if ctx.get("dx_label"):
            st.caption(f"진단: **{ctx['dx_label']}**")


        st.subheader("🗂️ 선택 요약")
        s1, s2, s3 = st.columns(3)
        with s1:
            st.markdown("**항암제(세포독성, 개인 선택)**")
            for k in (ctx.get("user_chemo") or []):
                from drug_db import display_label
                st.write("- " + display_label(k))
        with s2:
            st.markdown("**표적/면역(개인 선택)**")
            for k in (ctx.get("user_targeted") or []):
                from drug_db import display_label
                st.write("- " + display_label(k))
        with s3:
            st.markdown("**항생제(개인 선택)**")
            for k in (ctx.get("user_abx") or []):
                from drug_db import display_label
                st.write("- " + display_label(k))
    
        s1, s2 = st.columns(2)
        with s1:
            st.markdown("**항암제(개인 선택)**")
            for lbl in (ctx.get("user_chemo") or []):
                from drug_db import display_label
                st.write("- " + display_label(lbl))
        with s2:
            st.markdown("**항생제(개인 선택)**")
            for lbl in (ctx.get("user_abx") or []):
                from drug_db import display_label
                st.write("- " + display_label(lbl))

        st.subheader("💊 항암제(세포독성) 부작용")
        render_adverse_effects(st, ctx.get("user_chemo") or [], DRUG_DB)

        st.subheader("🧫 항생제 부작용")
        render_adverse_effects(st, ctx.get("user_abx") or [], DRUG_DB)

        st.markdown("---")
        st.markdown("**참고: 맵 기반 추천 레지멘 요약**")
        rec = auto_recs_by_dx(ctx.get("group"), ctx.get("dx"), DRUG_DB, ONCO_MAP)
        regimen_auto = (rec.get("chemo") or []) + (rec.get("targeted") or [])
        render_adverse_effects(st, regimen_auto, DRUG_DB)

        # 식이가이드
        st.subheader("🥗 피수치 기반 식이가이드 (예시)")
        lines = lab_diet_guides(labs, heme_flag=(ctx.get("group")=="혈액암"))
        for L in lines: st.write("- " + L)

        # 약물 부작용 (자동 추천만 우선 표시)
        st.subheader("💊 약물 부작용")
        rec = auto_recs_by_dx(ctx.get("group"), ctx.get("dx"), DRUG_DB, ONCO_MAP)
        regimen = (rec.get("chemo") or []) + (rec.get("targeted") or [])
        render_adverse_effects(st, regimen, DRUG_DB)

    elif ctx.get("mode") == "소아":
        st.subheader("👶 증상 요약")
        sy = ctx.get("symptoms", {})
        sy_cols = st.columns(4)
        keys = list(sy.keys())
        for i, key in enumerate(keys):
            with sy_cols[i % 4]:
                st.metric(key, sy[key])

        st.subheader("🥗 식이가이드")
        from ui_results import results_only_after_analyze as _dummy  # to keep imports coherent
        from ui_results import render_adverse_effects as _dummy2
        # 기존 peds_diet_guide는 별도 모듈에 있었지만, 원본의 가이드가 충분하여 lab_diet는 암에 한정.
        # 필요 시 별도 모듈로 확장 가능.

        st.subheader("🌡️ 해열제 1회분(평균)")
        dcols = st.columns(2)
        with dcols[0]:
            st.metric("아세트아미노펜 시럽", f"{ctx.get('apap_ml')} mL")
        with dcols[1]:
            st.metric("이부프로펜 시럽", f"{ctx.get('ibu_ml')} mL")

    st.stop()
