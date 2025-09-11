# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
# --- Pediatric predictor & daily guide utils ---
from typing import Dict, Tuple

def predict_peds_disease(sym_sel: Dict[str, object]) -> Tuple[str, str]:
    """
    아주 단순 룰 기반 예측 (참고용):
    - 다중 선택값(예: '부위')은 리스트로 들어올 수 있음
    - 반환: (예상 병명, 근거 요약)
    """
    nasal = str(sym_sel.get("콧물", ""))
    cough = str(sym_sel.get("기침", ""))
    diarrhea = str(sym_sel.get("설사", ""))
    fever = str(sym_sel.get("발열", ""))
    site = sym_sel.get("부위", [])
    if isinstance(site, str):
        site = [site] if site else []
    pain = str(sym_sel.get("통증", ""))

    # 수족구: 부위에 손/발/입안 포함
    if any(x in site for x in ["입안","손바닥","발바닥","둔부","체간"]):
        return ("수족구", "손·발·입 부위 병변 선택")

    # 독감: 고열 + 기침
    if ("38.5" in fever or "병원/응급실" in fever) and cough in ("보통","심함"):
        return ("독감", "고열과 기침 동반")

    # RSV: 콧물(투명/흰/누런) + 기침(조금~심함), 발열 낮거나 없음
    if nasal in ("투명","흰색","누런") and cough in ("조금","보통","심함") and ("없음" in fever or "37~37.5" in fever):
        return ("RSV", "상기도 점액 + 저열/무열")

    # 중이염: 통증 존재 + 발열 저~중등도, 설사 없음
    if pain in ("약간","보통","심함") and ("없음" in diarrhea or not diarrhea):
        return ("중이염", "귀 통증 호소")

    # 로타/노로/장염: 설사 다회
    if diarrhea in ("3~4회","5~6회"):
        # 고열이면 로타 쪽 가중
        if "37.5~38" in fever or "38.5" in fever:
            return ("로타", "다회 설사 + 발열")
        return ("노로", "다회 설사")

    # 아데노: 콧물 누런 + 보통 기침 + 중간 발열
    if nasal in ("누런",) and cough in ("조금","보통") and "37.5~38" in fever:
        return ("아데노", "점액성 콧물 + 중등도 발열")

    # 기본
    return ("감기/상기도감염", "특이 소견 없음 또는 비특이적 조합")

def peds_daily_tips(pred_dx: str) -> list:
    tips = [
        "충분한 수분 섭취(소량씩 자주)",
        "휴식과 수면 확보",
        "손위생·기침예절, 일시적 등원/등교 제한 고려",
        "40도 미만 열은 미온수 마사지, 해열제는 체중 기반 용량 준수",
    ]
    if pred_dx == "수족구":
        tips += ["입안 통증 시 차가운 부드러운 음식 권장", "수포 부위 긁지 않도록 손톱 짧게 유지"]
    elif pred_dx == "독감":
        tips += ["고위험군·증상 초기엔 항바이러스제 여부 진료상담", "호흡곤란/탈수·의식저하 시 즉시 진료"]
    elif pred_dx == "RSV":
        tips += ["비강 생리식염수 세척/흡인", "영유아는 호흡곤란·무호흡 주의"]
    elif pred_dx == "중이염":
        tips += ["진통제 적절 사용(의료진 안내)", "코 세척·상기도 케어"]
    elif pred_dx in ("로타","노로","장염"):
        tips += ["경구 수분보충액(ORS)", "기름진/자극 음식 피하기"]
    return tips

# --- 별명+PIN 입력 유틸 ---
def nickname_pin_local():
    pass
#     c1, c2 = st.columns([2,1])
#     with c1:
#         nick = st.text_input("별명", value=st.session_state.get("nick",""), placeholder="예: 토끼맘")
#     with c2:
#         pin = st.text_input("PIN (4자리)", value=st.session_state.get("pin",""), max_chars=4, placeholder="예: 0427")
#     # sanitize
#     pin = "".join([ch for ch in pin if ch.isdigit()])[:4]
#     st.session_state["nick"] = nick
#     st.session_state["pin"]  = pin
#     key = f"{nick}#{pin}" if nick and pin else ""
#     if not nick or len(pin)!=4:
#         st.caption("그래프/저장은 별명+PIN(4자리) 등록 시 사용 가능해요.")
#     else:
#         st.success(f"별명+PIN 등록됨: {nick}#{pin}")
#     return nick, pin, key


# --- Safe defaults to avoid NameError in any mode ---
user_chemo = []
user_targeted = []  # safe default
user_abx = []

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
    "ALL": "급성 림프구성 백혈병",
    "CML": "만성 골수성 백혈병",
    "CLL": "만성 림프구성 백혈병",
    "PCNSL": "원발성 중추신경계 림프종",
    # Lymphoma + common synonyms
    "DLBCL": "미만성 거대 B세포 림프종",
    "B거대세포종": "미만성 거대 B세포 림프종",
    "B 거대세포종": "미만성 거대 B세포 림프종",
    "B거대세포 림프종": "미만성 거대 B세포 림프종",
    "b거대세포종": "미만성 거대 B세포 림프종",
    "PMBCL": "원발성 종격동 B세포 림프종",
    "HGBL": "고등급 B세포 림프종",
    "BL": "버킷 림프종",
    "FL": "여포성 림프종",
    "MZL": "변연부 림프종",
    "MALT lymphoma": "점막연관 변연부 B세포 림프종",
    "MCL": "외투세포 림프종",
    "cHL": "고전적 호지킨 림프종",
    "NLPHL": "결절성 림프구우세 호지킨 림프종",
    "PTCL-NOS": "말초 T세포 림프종 (NOS)",
    "AITL": "혈관면역모세포성 T세포 림프종",
    "ALCL (ALK+)": "역형성 대세포 림프종 (ALK 양성)",
    "ALCL (ALK−)": "역형성 대세포 림프종 (ALK 음성)",
    # Sarcoma
    "OSTEOSARCOMA": "골육종",
    "EWING SARCOMA": "유잉육종",
    "RHABDOMYOSARCOMA": "횡문근육종",
    "SYNOVIAL SARCOMA": "활막육종",
    "LEIOMYOSARCOMA": "평활근육종",
    "LIPOSARCOMA": "지방육종",
    "UPS": "미분화 다형성 육종",
    "ANGIOSARCOMA": "혈관육종",
    "MPNST": "악성 말초신경초종",
    "DFSP": "피부섬유종증성 육종(DFSP)",
    "CLEAR CELL SARCOMA": "투명세포 육종",
    "EPITHELIOID SARCOMA": "상피양 육종",
    # Solid & Rare (keys already Korean or short)
    "폐선암": "폐선암",
    "유방암": "유방암",
    "대장암": "결장/직장 선암",
    "위암": "위선암",
    "간세포암": "간세포암(HCC)",
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

# Init
ensure_onco_drug_db(DRUG_DB)
ONCO_MAP = build_onco_map()

st.set_page_config(page_title="블러드맵 피수치가이드 (모듈화)", page_icon="🩸", layout="centered")
st.title("BloodMap — 모듈화 버전")


# --- 별명+PIN 입력 (상단) ---
# 공통 고지
st.info(
    "본 수치는 참고용이며, 해석 결과는 개발자와 무관합니다.\n"
    "약 변경/복용 중단 등은 반드시 주치의와 상의하세요.\n"
    "이 앱은 개인정보를 수집하지 않으며, 어떠한 개인정보 입력도 요구하지 않습니다."
)
nick, pin, key = nickname_pin(key_prefix="top1_")

# ----------- 별명+PIN -----------
# (removed duplicate)  nick, pin, key = nickname_pin(key_prefix="top_")
st.divider()
# 그래프/저장은 별명+PIN 기반 게이트
has_key = bool(nick and pin and len(pin) == 4)

# ----------- 모드 선택 -----------
mode = st.radio("모드 선택", ["암", "소아"], horizontal=True)


report_sections = []

# ------------------ 암 모드 ------------------
if mode == "암":
    st.markdown("### 1) 암 선택")
    group = st.selectbox("암 카테고리", ["혈액암","림프종","고형암","육종","희귀암"])
    dx_options = list(ONCO_MAP.get(group, {}).keys())
    dx = st.selectbox("진단(영문)", dx_options or ["직접 입력"])
    # ▼ 강제 한글 병기 라벨 출력
    if dx and dx != "직접 입력":
        st.markdown(f"**진단:** {local_dx_display(group, dx)}")
    if dx == "직접 입력":
        dx = st.text_input("진단(영문/축약 직접 입력)", value="")
        if dx:
            st.markdown(f"**진단:** {local_dx_display(group, dx)}")

    if group == "혈액암":
        msg = "혈액암 환자에서 **철분제 + 비타민 C** 복용은 흡수 촉진 가능성이 있어, **반드시 주치의와 상의 후** 복용 여부를 결정하세요."
        st.warning(msg); report_sections.append(("영양/보충제 주의", [msg]))

    st.markdown("### 2) 자동 예시(토글)")
    if st.toggle("자동 예시 보기", value=True):
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

    # 3) 개인 선택 (암 진단별 동적 리스트)
    st.markdown("### 3) 개인 선택 (영어 + 한글 병기)")
    from drug_db import picklist, key_from_label
    rec_local = auto_recs_by_dx(group, dx, DRUG_DB, ONCO_MAP)
    chemo_keys = rec_local.get("chemo", []) or rec_local.get("targeted", [])
    abx_keys = [
        "Piperacillin/Tazobactam","Cefepime","Meropenem","Imipenem/Cilastatin","Aztreonam","Amikacin",
        "Vancomycin","Linezolid","Daptomycin","Ceftazidime","Levofloxacin","TMP-SMX","Metronidazole","Amoxicillin/Clavulanate"
    ]
    chemo_opts = picklist([k for k in chemo_keys if k in DRUG_DB])
    abx_opts   = picklist([k for k in abx_keys if k in DRUG_DB])
    if not abx_opts:
        abx_opts = abx_keys  # DB 비어도 선택 가능하도록 폴백
    if not abx_opts:
        abx_opts = abx_keys  # DRUG_DB에 없더라도 키 자체로 선택 가능하게
    c1, c2 = st.columns(2)
    with c1:
        user_chemo_labels = st.multiselect("항암제(개인)", chemo_opts, default=[])
    with c2:
        user_abx_labels   = st.multiselect("항생제(개인)", abx_opts, default=[], placeholder="복용 중인 항생제를 선택")
    user_chemo = [key_from_label(x) for x in user_chemo_labels]
    user_abx   = [key_from_label(x) for x in user_abx_labels]

    # 4) 피수치 입력
    st.markdown("### 4) 피수치 입력 (숫자만)")
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

    # 5) 특수검사
    from special_tests import special_tests_ui
    sp_lines = special_tests_ui()
    if sp_lines:
        st.markdown("#### 🧬 특수검사 해석")
        def _badge(text, color):
            st.markdown(f"<span style=\"padding:2px 8px;border-radius:12px;background:{color};color:white;font-size:12px\">{text}</span>", unsafe_allow_html=True)
        colored = []
        for L in sp_lines:
            if any(x in L for x in ["정상"]):
                _badge("정상", "#6b7280"); st.write("- "+L)
            elif any(x in L for x in ["주의","낮음"]):
                _badge("주의", "#f59e0b"); st.write("- "+L)
            elif any(x in L for x in ["위험","+++"]):
                _badge("위험", "#ef4444"); st.write("- "+L)
            else:
                st.write("- "+L)
        report_sections.append(("특수검사 해석", sp_lines))

    # 6) 저장/그래프
    st.markdown("#### 💾 저장/그래프")
    when = st.date_input("측정일", value=date.today())
    if st.button("📈 피수치 저장/추가", disabled=not has_key):
        if not has_key:
            st.warning("별명+PIN(4자리) 등록 후 저장할 수 있습니다.")
        else:
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

    # 7) 해석하기 → 결과 게이트로 전달
    if st.button("🔎 해석하기", key="analyze_cancer"):
        st.session_state["analyzed"] = True
        st.session_state["analysis_ctx"] = {
            "mode":"암", "group":group, "dx":dx, "dx_label": local_dx_display(group, dx),
            "labs": labs,
            "user_chemo": user_chemo,
            "user_targeted": (user_targeted if isinstance(user_targeted, list) else []),
            "user_abx": user_abx
        }

    # 스케줄
    schedule_block("📋 사용 가이드", [
        "별명+PIN(4자리) 등록 시 그래프/저장 활성화",
        "암 모드에서는 해열제 UI가 보이지 않습니다",
        "자동 예시(토글)는 예시용이며, 실제 분석은 개인 선택 약 기준",
    ])

# ------------------ 소아 모드 ------------------
else:
    ctop = st.columns(3)
    with ctop[0]:
        disease = st.selectbox("소아 질환", ["일상","로타","독감","RSV","아데노","마이코","수족구","편도염","코로나","중이염"], index=0)
    with ctop[1]:
        temp = st.number_input("체온(℃)", min_value=0.0, step=0.1)
    with ctop[2]:
        age_m = st.number_input("나이(개월)", min_value=0, step=1)
        weight = st.number_input("체중(kg)", min_value=0.0, step=0.1)

    # 증상 옵션 로딩 (안전 가드)
    opts = {}
    try:
        opts = get_symptom_options(disease) or {}
    except Exception:
        opts = {}
    
    # 🏠 일상 (미리보기): 증상 체크 상단
    try:
        _pred_preview, _pred_why = predict_peds_disease({})
    except Exception:
        _pred_preview, _pred_why = "감기/상기도감염", "초기값"
    st.subheader("🏠 일상")
    st.caption("증상 입력 후 더 정확해져요")
    st.info(f"예상 병명(참고): **{_pred_preview}** — {_pred_why}")

if "opts" not in locals():
    try:
        opts = get_symptom_options(disease) or {}
    except Exception:
        opts = {}

st.markdown("### 증상 체크")
_base = ["콧물","기침","설사","발열"]
_extra = [k for k in (opts.keys() if opts else []) if k not in _base]
sym_order = _base + _extra
sym_sel = {}
cols = st.columns(4)
for i, k in enumerate(sym_order):
    with cols[i % 4]:
        if k == "부위":
            sym_sel[k] = st.multiselect(k, opts[k], key=f"sym_{k}")
        else:
            sym_sel[k] = st.selectbox(k, opts[k], key=f"sym_{k}")

st.markdown("#### 🔥 해열제 (1회 평균 용량 기준, mL)")
from peds_dose import acetaminophen_ml, ibuprofen_ml
apap_ml, apap_w = acetaminophen_ml(age_m, weight or None)
ibu_ml,  ibu_w  = ibuprofen_ml(age_m, weight or None)
dc = st.columns(2)
with dc[0]: st.metric("아세트아미노펜 시럽 (mL)", f"{apap_ml:.1f}", help=f"계산 체중 {apap_w} kg · 160 mg/5 mL, 12.5 mg/kg")
with dc[1]: st.metric("이부프로펜 시럽 (mL)",  f"{ibu_ml:.1f}",  help=f"계산 체중 {ibu_w} kg · 100 mg/5 mL, 7.5 mg/kg")

if st.button("🔎 해석하기", key="analyze_peds"):
    st.session_state["analyzed"] = True
    st.session_state["analysis_ctx"] = {
        "mode":"소아", "disease": disease,
        "symptoms": sym_sel,
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

        st.subheader("💉 표적/면역 부작용")
        render_adverse_effects(st, ctx.get("user_targeted") or [], DRUG_DB)

        st.subheader("🧫 항생제 부작용")
        render_adverse_effects(st, ctx.get("user_abx") or [], DRUG_DB)
# 식이가이드
        st.subheader("🥗 피수치 기반 식이가이드 (예시)")
        lines = lab_diet_guides(labs, heme_flag=(ctx.get("group")=="혈액암"))
        for L in lines: st.write("- " + L)

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
            st.metric("아세트아미노펜 시럽 (mL)", f"{float(ctx.get('apap_ml', 0)):.1f}")
        with dcols[1]:
            st.metric("이부프로펜 시럽 (mL)", f"{float(ctx.get('ibu_ml', 0)):.1f}")

    
    # ---- 결과 다운로드 ----
    _ctx = st.session_state.get("analysis_ctx", {})
    _lines = []
    if _ctx.get("mode") == "암":
        _lines.append(f"진단: { _ctx.get('dx_label', '') }")
    elif _ctx.get("mode") == "소아":
        # 🏠 일상가이드: 증상 + 예측 병명 + 생활 팁
        st.subheader("🏠 일상가이드")
        _pred, _why = predict_peds_disease(_ctx.get("symptoms", {}))
        st.markdown(f"**예상 병명:** {_pred}  \n이유: {_why}")
        _tips = peds_daily_tips(_pred)
        for t in _tips:
            st.write("- " + t)
        report_sections.append(("일상가이드", [f"예상 병명: {_pred} (이유: {_why})"] + _tips))

        _sy = _ctx.get("symptoms", {})
        _lines.append("증상 요약:")
        for k,v in _sy.items():
            _v = ", ".join(v) if isinstance(v, list) else v
            _lines.append(f"- {k}: {_v}")
        _lines.append(f"해열제 1회분: APAP { _ctx.get('apap_ml') } mL / IBU { _ctx.get('ibu_ml') } mL")
    _md = "\n".join(_lines) + "\n\n---\n본 수치는 참고용이며, 해석 결과는 개발자와 무관합니다.\n약 변경, 복용 중단 등은 반드시 주치의와 상의 후 결정하시기 바랍니다.\n이 앱은 개인정보를 절대 수집하지 않으며, 어떠한 개인정보 입력도 요구하지 않습니다."
    _txt = _md
    st.download_button("⬇️ 결과 저장(.md)", _md, file_name="bloodmap_result.md")
    st.download_button("⬇️ 결과 저장(.txt)", _txt, file_name="bloodmap_result.txt")
st.stop()
