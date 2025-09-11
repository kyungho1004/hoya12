# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
# --- Local Korean display (fallback; independent of onco_map import) ---
def _is_korean(s: str) -> bool:
    return any('\uac00' <= ch <= '\ud7a3' for ch in (s or ""))

def _norm(s: str) -> str:
    if not s:
        return ""
    s2 = (s or "").strip()
    return s2.upper().replace(" ", "") or s2

DX_KO_LOCAL = {
    # Hematology
    "APL": "급성 전골수구성 백혈병",
    "AML": "급성 골수성 백혈병",
    "ALL": "급성 림프모구 백혈병",
    "CML": "만성 골수성 백혈병",
    "CLL": "만성 림프구성 백혈병",
    "MDS": "골수형성이상증후군",
    "MPN": "골수증식성종양",
    "DLBCL": "미만성 거대 B세포 림프종",
    "HGBL": "고등급 B세포 림프종",
    "BL": "버킷 림프종",
    "FL": "여포성 림프종",
    "MZL": "변연부 림프종",
    "MALT LYMPHOMA": "점막연관 변연부 B세포 림프종",
    "MCL": "외투세포 림프종",
    "CHL": "고전적 호지킨 림프종",
    "NLPHL": "결절성 림프구우세 호지킨 림프종",
    "PTCL-NOS": "말초 T세포 림프종 (NOS)",
    "AITL": "혈관면역모세포성 T세포 림프종",
    "ALCL (ALK+)": "역형성 대세포 림프종 (ALK 양성)",
    "ALCL (ALK−)": "역형성 대세포 림프종 (ALK 음성)",
    # Sarcoma
    "OSTEOSARCOMA": "골육종",
    "EWS": "유잉육종",
    "LMS": "평활근육종",
    "LPS": "지방육종",
    "UPS": "분화불량 다형성 육종",
    "RMS": "횡문근육종",
    # Solid
    "NSCLC": "비소세포폐암",
    "SCLC": "소세포폐암",
    "LUAD": "폐선암",
    "LUSC": "편평상피세포 폐암",
    "BRCA": "유방암",
    "CRC": "대장암",
    "GC": "위암",
    "HCC": "간세포암",
    "CCA": "담관암",
    "PDAC": "췌장관선암",
    "RCC": "신장암",
    "HNSCC": "두경부 편평상피암",
    "BTC": "담도계 암",
    "PCA": "전립선암",
    # Korean names passthrough
    "폐선암": "폐선암",
    "비소세포폐암": "비소세포폐암",
    "소세포폐암": "소세포폐암",
    "유방암": "유방암",
    "대장암": "대장암",
    "위암": "위암",
    "간암": "간암",
    "담관암": "담관암",
    "췌장암": "췌장암",
    "난소암": "난소암",
    "자궁경부암": "자궁경부암",
    "방광암": "방광암",
    "식도암": "식도암",
    "GIST": "위장관기저종양",
    "NET": "신경내분비종양",
    "MTC": "수질성 갑상선암",
}

def local_dx_display(group: str, dx: str) -> str:
    dx = (dx or "").strip()
    if _is_korean(dx):
        return f"{group} - {dx}"
    key = _norm(dx)
    ko = DX_KO_LOCAL.get(key) or DX_KO_LOCAL.get(dx)
    return f"{group} - {dx} ({ko})" if ko else f"{group} - {dx}"

from datetime import date, datetime

from core_utils import nickname_pin, clean_num, round_half, temp_band, rr_thr_by_age_m, schedule_block
from drug_db import DRUG_DB, ensure_onco_drug_db
from onco_map import build_onco_map, auto_recs_by_dx, dx_display
from ui_results import results_only_after_analyze, render_adverse_effects
from lab_diet import lab_diet_guides
from peds_profiles import get_symptom_options
from peds_dose import acetaminophen_ml, ibuprofen_ml
from config import FEVER_GUIDE

# Init
ensure_onco_drug_db(DRUG_DB)
ONCO_MAP = build_onco_map()

st.set_page_config(page_title="블러드맵 피수치가이드 (모듈화)", page_icon="🩸", layout="centered")
st.title("BloodMap — 모듈화 버전")

# 0) 사용자 식별 (별명 + PIN)
st.markdown("#### 👤 사용자 식별 (별명 + 4자리 PIN)")
col = st.columns(3)
with col[0]: nick = st.text_input("별명", value="")
with col[1]: pin  = st.text_input("PIN(4자리)", value="", max_chars=4)
with col[2]:
    when = st.date_input("측정일", value=date.today())
key, has_key = nickname_pin(nick, pin)
st.session_state["key"] = key

# 1) 모드 선택
mode = st.radio("모드 선택", ["암", "소아"], horizontal=True)

# 2) 기본 랩 입력
from config import (
    LBL_WBC, LBL_Hb, LBL_PLT, LBL_ANC,
    LBL_Ca, LBL_P, LBL_Na, LBL_K,
    LBL_Alb, LBL_Glu, LBL_TP, LBL_AST, LBL_ALT, LBL_LDH,
    LBL_CRP, LBL_Cr, LBL_UA, LBL_TB, LBL_BUN, LBL_BNP, ORDER
)

labs = {}
st.markdown("### 기본 수치 입력")
cols = st.columns(4)
labels = ORDER
for i, lbl in enumerate(labels):
    with cols[i % 4]:
        labs[lbl] = st.text_input(lbl, value="")

# 3) 모드별 UI
if mode == "암":
    st.markdown("### 1) 암 진단 선택")
    g1, g2 = st.columns(2)
    with g1:
        group = st.selectbox("암 카테고리", ["혈액암", "고형암", "육종", "림프종"], index=0)
    dx_list = sorted({ # display purpose only
        "APL","AML","ALL","CML","CLL","MDS","MPN",
        "DLBCL","HGBL","BL","FL","MZL","MALT lymphoma","MCL","cHL","NLPHL","PTCL-NOS","AITL","ALCL (ALK+)","ALCL (ALK−)",
        "OSTEOSARCOMA","EWS","LMS","LPS","UPS","RMS",
        "NSCLC","SCLC","LUAD","LUSC","BRCA","CRC","GC","HCC","CCA","PDAC","RCC","HNSCC","BTC","PCA",
        "폐선암","비소세포폐암","소세포폐암","유방암","대장암","위암","간암","담관암","췌장암","난소암","자궁경부암","방광암","식도암","GIST","NET","MTC",
        "직접 입력"
    })
    with g2:
        dx = st.selectbox("진단명(영문/한글)", dx_list, index=0)

    # ▼ 강제 한글 병기 라벨 출력
    if dx and dx != "직접 입력":
        st.markdown(f"**진단:** {local_dx_display(group, dx)}")
    if dx == "직접 입력":
        dx = st.text_input("진단(영문/축약 직접 입력)", value="")
        if dx:
            st.markdown(f"**진단:** {local_dx_display(group, dx)}")

    if group == "혈액암":
        msg = "혈액암 환자에서 **철분제 + 비타민 C** 복용은 흡수 촉진 가능성이 있어, **반드시 주치의와 상의 후** 복용 여부를 결정하세요."
        st.warning(msg); report_sections = [("영양/보충제 주의", [msg])]
    else:
        report_sections = []

    st.markdown("### 2) 자동 예시(토글)")
    if st.toggle("자동 예시 보기", value=True, key="auto_example_main"):
        rec = auto_recs_by_dx(group, dx, DRUG_DB, ONCO_MAP)
        c = st.columns(3)
        with c[0]:
            st.markdown("**항암제(예시)**")
            from drug_db import display_label
            for d in rec["chemo"]:
                st.write("- " + display_label(d))
        with c[1]:
            st.markdown("**표적/면역(예시)**")
            from drug_db import display_label
            for d in rec["targeted"]:
                st.write("- " + display_label(d))
        with c[2]:
            st.markdown("**항생제(참고)**")
            for d in rec["abx"]: st.write("- " + d)

    # 4) 수동 선택 (항암제/항생제)
    st.markdown("### 3) 약물 선택(선택)")
    from drug_db import list_labels_by_group
    user_chemo = st.multiselect("항암제(세포독성)", options=list_labels_by_group("chemo"))
    user_abx   = st.multiselect("항생제", options=list_labels_by_group("abx"))

    # 5) 결과 요약(선행 표시)
    st.markdown("### 4) 결과 요약(간단)")
    results_only_after_analyze(st, labs)

    # 6) 저장/그래프
    st.markdown("#### 💾 저장/그래프")
    when = st.date_input("측정일", value=date.today())
    if st.button("📈 피수치 저장/추가", key="save_labs"):
        st.session_state.setdefault("lab_hist", {}).setdefault(key, pd.DataFrame())
        df_prev = st.session_state["lab_hist"][key]
        row = {"Date": when.strftime("%Y-%m-%d")}
        for L in labels:
            row[L] = labs.get(L)
        df = pd.concat([df_prev, pd.DataFrame([row])], ignore_index=True)
        if "Date" in df:
            try:
                df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.date
            except: pass
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

    # 7) 해석하기 → 결과 게이트로 전달
    if st.button("🔎 해석하기", key="analyze_cancer"):
        st.session_state["analyzed"] = True
        st.session_state["analysis_ctx"] = {
            "mode":"암", "group":group, "dx":dx, "dx_label": dx_display(group, dx),
            "labs": labs,
            "user_chemo": user_chemo,
            "user_abx": user_abx
        }

    # 스케줄
    schedule_block()

# ------------------ 소아 모드 ------------------
else:
    ctop = st.columns(3)
    with ctop[0]:
        disease = st.selectbox("소아 질환", ["로타","독감","RSV","아데노","마이코","수족구","편도염","코로나","중이염"], index=0)
    with ctop[1]:
        temp = st.number_input("체온(℃)", min_value=0.0, step=0.1)
        st.caption(FEVER_GUIDE)
    with ctop[2]:
        age_m = st.number_input("나이(개월)", min_value=0, step=1)
        weight = st.number_input("체중(kg)", min_value=0.0, step=0.1)

    # 증상 옵션 로딩
    opts = get_symptom_options(disease)
    st.markdown("### 증상 체크")
    c1,c2,c3,c4 = st.columns(4)
    with c1: nasal = st.selectbox("콧물", opts["콧물"])
    with c2: cough = st.selectbox("기침", opts["기침"])
    with c3: diarrhea = st.selectbox("설사(횟수/일)", opts["설사"])
    with c4: fever = st.selectbox("발열", opts["발열"])

    st.markdown("#### 🔥 해열제 (1회 평균 용량 기준, mL)")
    apap_ml, apap_w = acetaminophen_ml(age_m, weight or None)
    ibu_ml,  ibu_w  = ibuprofen_ml(age_m, weight or None)
    dc = st.columns(2)
    with dc[0]: st.metric("아세트아미노펜 시럽", f"{apap_ml} mL", help=f"계산 체중 {apap_w} kg · 160 mg/5 mL, 12.5 mg/kg")
    with dc[1]: st.metric("이부프로펜 시럽", f"{ibu_ml} mL", help=f"계산 체중 {ibu_w} kg · 100 mg/5 mL, 7.5 mg/kg")

    if st.button("🔎 해석하기", key="analyze_peds"):
        st.session_state["analyzed"] = True
        st.session_state["analysis_ctx"] = {
            "mode":"소아", "disease": disease,
            "symptoms": {
                "콧물": nasal, "기침": cough, "설사": diarrhea, "발열": fever
            },
            "apap_ml": apap_ml, "ibu_ml": ibu_ml
        }

# ------------------ 결과 게이트 ------------------
if st.session_state.get("analyzed"):
    ctx = st.session_state.get("analysis_ctx") or {}
    st.header("📘 해석 결과")
    st.caption("본 수치는 참고용이며, 해석 결과는 개발자와 무관합니다. 약 변경/중단은 반드시 주치의와 상의하세요. 개인정보는 수집하지 않습니다.")

    # 공통: 수치 요약
    results_only_after_analyze(st, labs)

    if ctx.get("mode") == "암":
        st.subheader("🧬 진단")
        st.write(ctx.get("dx_label") or "-")

        st.subheader("🧪 약물(자동 예시)")
        rec = auto_recs_by_dx(ctx.get("group"), ctx.get("dx"), DRUG_DB, ONCO_MAP)
        c = st.columns(3)
        with c[0]:
            st.markdown("**항암제(예시)**")
            from drug_db import display_label
            for d in rec["chemo"]:
                st.write("- " + display_label(d))
        with c[1]:
            st.markdown("**표적/면역(예시)**")
            from drug_db import display_label
            for d in rec["targeted"]:
                st.write("- " + display_label(d))
        with c[2]:
            st.markdown("**항생제(참고)**")
            for d in rec["abx"]: st.write("- " + d)

        st.subheader("💊 항암제(세포독성) 부작용")
        render_adverse_effects(st, rec.get("chemo") or [], DRUG_DB)

        st.subheader("🧫 항생제 부작용")
        render_adverse_effects(st, rec.get("abx") or [], DRUG_DB)

        # 식이가이드
        st.subheader("🥗 피수치 기반 식이가이드 (예시)")
        lines = lab_diet_guides(labs, heme_flag=(ctx.get("group")=="혈액암"))
        for L in lines: st.write("- " + L)

        # 약물 부작용 (자동 추천만 우선 표시)
        st.subheader("💊 약물 부작용")
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
        from ui_results import results_only_after_analyze as _dummy  # keep imports coherent
        from ui_results import render_adverse_effects as _dummy2
        # (소아용 식이가이드는 필요 시 확장)

        st.subheader("🌡️ 해열제 1회분(평균)")
        dcols = st.columns(2)
        with dcols[0]:
            st.metric("아세트아미노펜 시럽", f"{ctx.get('apap_ml')} mL")
        with dcols[1]:
            st.metric("이부프로펜 시럽", f"{ctx.get('ibu_ml')} mL")

    st.stop()
