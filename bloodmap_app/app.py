# -*- coding: utf-8 -*-
# BloodMap — Streamlit App (통합본)
# - 소아 모드: "증상 기반" vs "진단명 직접" 트랙 분리
# - 증상 기반 규칙: 38℃ 이상·2일 이상 + 설사 ≥4회 + 구토 → 장염/로타 의심
# - 진단명 직접 선택 시: 선택 진단 식이가이드 + 해열제 용량만 노출
# - 요검사(HPF) 평균 파싱 + 해석 / 보체(C3/C4/CH50) 해석
# - MD/TXT 보고서 저장, 선택 요약 중복 제거, 보체 위젯 key 충돌 해결

import re
from datetime import date
import pandas as pd
import streamlit as st

# -------------------- 공통 헬퍼 --------------------

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
    # Lymphoma (일부 동의어 포함)
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
    # Solid/Rare (한글 그대로 사용)
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

# -------------------- 모듈 임포트 --------------------
from core_utils import nickname_pin, clean_num, schedule_block
from drug_db import DRUG_DB, ensure_onco_drug_db
from onco_map import build_onco_map, auto_recs_by_dx, dx_display
from ui_results import results_only_after_analyze, render_adverse_effects
from lab_diet import lab_diet_guides
from peds_dose import acetaminophen_ml, ibuprofen_ml
import config as CFG

# ------------------ 소아 식이가이드 매핑 ------------------
PEDS_DIET_DB = {
    "로타/장염": [
        "수분/전해질 보충(ORS)을 우선하세요.",
        "튀김·기름진 음식은 피하고, 유제품은 일시 제한 고려.",
        "바나나·쌀죽·사과퓨레·토스트(BRAT)를 24–48시간, 이후 균형식으로 복귀.",
        "탈수 징후(소변 감소, 축 처짐, 입마름) 시 진료 권고.",
    ],
    "독감/코로나": [
        "수분 충분히(미지근한 물·국/수프).",
        "카페인·탄산음료는 피하기.",
        "식사량 떨어지면 소량씩 자주.",
    ],
    "RSV": [
        "따뜻한 수분, 묽은 미음·죽 위주.",
        "콧물 많으면 소량씩 자주.",
    ],
    "아데노": [
        "수분 보충, 자극적인 음식 피하기.",
    ],
    "마이코": [
        "연식(죽/수프)과 수분 위주.",
    ],
    "수족구": [
        "목 통증 고려해 차갑고 부드러운 음식. 맵고 신 음식은 피하기.",
    ],
    "편도염": [
        "부드러운 연식, 따뜻한 수분. 자극적/단단한 음식 피하기.",
    ],
    "중이염": [
        "특별한 제한 없음. 수분 충분히.",
    ],
}

def _diet_key_from_text(txt: str) -> str:
    s = (txt or "").upper()
    if "로타" in s or "장염" in s:
        return "로타/장염"
    if "독감" in s or "코로나" in s:
        return "독감/코로나"
    for k in ["RSV", "아데노", "마이코", "수족구", "편도염", "중이염"]:
        if k.upper() in s:
            return k
    return ""


def peds_diet_lines(name: str):
    return PEDS_DIET_DB.get(name, [])

# -------------------- 초기화 --------------------
ensure_onco_drug_db(DRUG_DB)
ONCO_MAP = build_onco_map()

st.set_page_config(page_title="블러드맵 피수치가이드 (통합)", page_icon="🩸", layout="centered")
st.title("BloodMap — 통합본")
st.info(CFG.DISCLAIMER)

# ID 키: 별명 + 4자리 PIN
nick, pin, key = nickname_pin()
st.divider()
has_key = bool(nick and pin and len(pin) == 4)

# -------------------- 요검사/보체 해석 유틸 --------------------

def parse_hpf_mean(text: str):
    """예: '6-10/HPF', '3~5/HPF', '5/HPF' → 평균 숫자(float)"""
    if not text:
        return None
    s = str(text).upper().replace("HPF", "").replace("/", "").strip()
    m = re.search(r"(\d+)\s*[-~]\s*(\d+)", s)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        return round((a + b) / 2, 1)
    m2 = re.search(r"(\d+)", s)
    if m2:
        return float(m2.group(1))
    return None

_URINE_FLAG = {"-": 0, "±": 1, "+": 1, "++": 2, "+++": 3}


def interpret_urinalysis(albumin_flag: str, glucose_flag: str, ob_flag: str, rbc_hpf, wbc_hpf):
    lines = []
    # 알부민뇨
    lvl = _URINE_FLAG.get((albumin_flag or "").strip(), None)
    if lvl is not None and lvl >= 1:
        if lvl >= 3:
            lines.append("알부민뇨 +++ → 🚨 신장 기능 이상 가능성, 정밀검사 권고")
        elif lvl == 2:
            lines.append("알부민뇨 ++ → 🟠 단백뇨, 신장질환/탈수 등 감별")
        else:
            lines.append("알부민뇨 + → 🟡 일시적 단백뇨 가능 (운동/발열/탈수 등)")
    # 잠혈
    lvl_ob = _URINE_FLAG.get((ob_flag or "").strip(), None)
    if lvl_ob is not None and lvl_ob >= 1:
        if lvl_ob >= 2:
            lines.append("잠혈 ++ 이상 → 🟠 요로 출혈/결석/염증 의심")
        else:
            lines.append("잠혈 + → 🟡 미세 혈뇨 가능")
    # 요당
    lvl_g = _URINE_FLAG.get((glucose_flag or "").strip(), None)
    if lvl_g is not None and lvl_g >= 1:
        lines.append("요당 양성 → 🟠 고혈당/당대사 이상 여부 확인 권고")
    # RBC/WBC per HPF
    if rbc_hpf is not None:
        if rbc_hpf > 10:
            lines.append(f"적혈구 {rbc_hpf}/HPF → 🚨 유의한 혈뇨")
        elif rbc_hpf > 5:
            lines.append(f"적혈구 {rbc_hpf}/HPF → 🟠 혈뇨 가능")
        elif rbc_hpf > 2:
            lines.append(f"적혈구 {rbc_hpf}/HPF → 🟡 경계")
    if wbc_hpf is not None:
        if wbc_hpf > 10:
            lines.append(f"백혈구 {wbc_hpf}/HPF → 🟠 요로감염 가능성")
        elif wbc_hpf > 5:
            lines.append(f"백혈구 {wbc_hpf}/HPF → 🟡 염증 소견 가능")
    return lines

_DEF_REF = {"C3": (90, 180), "C4": (10, 40), "CH50": (60, 144)}  # 일반 참고범위(기관마다 다름)


def interpret_complement(C3, C4, CH50):
    lines = []
    def _chk(name, v):
        if v is None:
            return
        lo, hi = _DEF_REF[name]
        if v < lo:
            lines.append(f"{name} 낮음 → 🟡 보체 소모/면역계 이상 가능")
        elif v > hi:
            lines.append(f"{name} 높음 → 참고치 상회 (염증/급성기 반응 등)")
    _chk("C3", C3)
    _chk("C4", C4)
    _chk("CH50", CH50)
    if not lines:
        lines.append("보체 수치 특이 소견 없음 (참고치 기준)")
    lines.append("※ 참고: 검사실 별 참고범위가 다를 수 있습니다.")
    return lines

# -------------------- 모드 선택 --------------------
mode = st.radio("모드 선택", ["암", "소아"], horizontal=True)
report_sections = []

# ==================== 암 모드 ====================
if mode == "암":
    st.markdown("### 1) 암 선택")
    group = st.selectbox("암 카테고리", ["혈액암", "림프종", "고형암", "육종", "희귀암"])
    dx_options = list(ONCO_MAP.get(group, {}).keys())
    dx = st.selectbox("진단(영문)", dx_options or ["직접 입력"])

    if dx and dx != "직접 입력":
        st.markdown(f"**진단:** {local_dx_display(group, dx)}")
    if dx == "직접 입력":
        dx = st.text_input("진단(영문/축약 직접 입력)", value="")
        if dx:
            st.markdown(f"**진단:** {local_dx_display(group, dx)}")

    if group == "혈액암":
        msg = "혈액암 환자에서 **철분제 + 비타민 C** 병용은 흡수 촉진 가능성이 있어, **반드시 주치의와 상의 후** 결정하세요."
        st.warning(msg)
        report_sections.append(("영양/보충제 주의", [msg]))

    st.markdown("### 2) 자동 예시(토글)")
    if st.toggle("자동 예시 보기", value=True):
        rec = auto_recs_by_dx(group, dx, DRUG_DB, ONCO_MAP)
        c = st.columns(3)
        from drug_db import display_label
        with c[0]:
            st.markdown("**항암제(예시)**")
            for d in rec.get("chemo", []):
                st.write("- " + display_label(d))
        with c[1]:
            st.markdown("**표적/면역(예시)**")
            for d in rec.get("targeted", []):
                st.write("- " + display_label(d))
        with c[2]:
            st.markdown("**항생제(참고)**")
            for d in rec.get("abx", []):
                st.write("- " + d)

    # 3) 개인 선택
    st.markdown("### 3) 개인 선택 (영어 + 한글 병기)")
    from drug_db import picklist, key_from_label
    rec_local = auto_recs_by_dx(group, dx, DRUG_DB, ONCO_MAP)
    chemo_keys = rec_local.get("chemo", []) or rec_local.get("targeted", [])
    abx_keys = [
        "Piperacillin/Tazobactam", "Cefepime", "Meropenem", "Imipenem/Cilastatin", "Aztreonam", "Amikacin",
        "Vancomycin", "Linezolid", "Daptomycin", "Ceftazidime", "Levofloxacin", "TMP-SMX", "Metronidazole", "Amoxicillin/Clavulanate",
    ]
    chemo_opts = picklist([k for k in chemo_keys if k in DRUG_DB])
    abx_opts = picklist([k for k in abx_keys if k in DRUG_DB]) or abx_keys

    c1, c2 = st.columns(2)
    with c1:
        user_chemo_labels = st.multiselect("항암제(개인)", chemo_opts, default=[])
    with c2:
        user_abx_labels = st.multiselect("항생제(개인)", abx_opts, default=[], placeholder="복용 중인 항생제를 선택")

    user_chemo = [key_from_label(x) for x in user_chemo_labels]
    user_abx = [key_from_label(x) for x in user_abx_labels]

    # 4) 피수치 입력
    st.markdown("### 4) 피수치 입력 (숫자만)")
    LABS_ORDER = [
        ("WBC", "WBC(백혈구)"), ("Hb", "Hb(혈색소)"), ("PLT", "PLT(혈소판)"), ("ANC", "ANC(절대호중구,면역력)"),
        ("Ca", "Ca(칼슘)"), ("Na", "Na(나트륨,소디움)"), ("K", "K(칼륨)"), ("Alb", "Alb(알부민)"), ("Glu", "Glu(혈당)"),
        ("TP", "TP(총단백)"), ("AST", "AST(간수치)"), ("ALT", "ALT(간세포)"), ("LD", "LD(유산탈수효소)"),
        ("CRP", "CRP(C-반응성단백,염증)"), ("Cr", "Cr(크레아티닌,신장)"), ("UA", "UA(요산)"), ("Tbili", "Tbili(총빌리루빈)"),
    ]
    labs = {}
    for code, label in LABS_ORDER:
        v = st.text_input(label, placeholder="예: 4500")
        labs[code] = clean_num(v)

    # 5) 🚽 소변 검사(요검사)
    st.markdown("#### 🚽 소변 검사(요검사)")
    u1, u2, u3 = st.columns(3)
    with u1:
        u_albumin = st.selectbox("알부민뇨", ["-", "+", "++", "+++"])
    with u2:
        u_glucose = st.selectbox("요당", ["-", "+", "++", "+++"])
    with u3:
        u_ob = st.selectbox("잠혈(OB)", ["-", "+", "++", "+++"])
    u4, u5 = st.columns(2)
    with u4:
        u_rbc_txt = st.text_input("적혈구(HPF)", placeholder="예: 6-10/HPF")
    with u5:
        u_wbc_txt = st.text_input("백혈구(HPF)", placeholder="예: 3-5/HPF")

    u_rbc = parse_hpf_mean(u_rbc_txt)
    u_wbc = parse_hpf_mean(u_wbc_txt)
    u_lines = interpret_urinalysis(u_albumin, u_glucose, u_ob, u_rbc, u_wbc)
    if u_lines:
        st.markdown("#### 🚽 소변검사 해석")
        for L in u_lines:
            st.write("- " + L)
        report_sections.append(("소변검사 해석", u_lines))

    # 5-c) 🧪 보체 검사 (key 지정으로 충돌 방지)
    st.markdown("#### 🧪 보체 검사 (C3/C4/CH50)")
    cC3, cC4, cCH = st.columns(3)
    with cC3:
        C3_txt = st.text_input("C3 (mg/dL)", key="main_c3")
    with cC4:
        C4_txt = st.text_input("C4 (mg/dL)", key="main_c4")
    with cCH:
        CH50_txt = st.text_input("CH50 (U/mL)", key="main_ch50")
    C3 = clean_num(C3_txt)
    C4 = clean_num(C4_txt)
    CH50 = clean_num(CH50_txt)
    comp_lines = interpret_complement(C3, C4, CH50)
    if any(x is not None for x in [C3, C4, CH50]):
        st.markdown("#### 🧪 보체검사 해석")
        for L in comp_lines:
            st.write("- " + L)
        report_sections.append(("보체검사 해석", comp_lines))

    # 6) 저장/그래프
    st.markdown("#### 💾 저장/그래프")
    when = st.date_input("측정일", value=date.today())
    if st.button("📈 피수치 저장/추가"):
        st.session_state.setdefault("lab_hist", {}).setdefault(key, pd.DataFrame())
        df_prev = st.session_state["lab_hist"][key]
        row = {"Date": when.strftime("%Y-%m-%d")}
        labels = [label for _, label in LABS_ORDER]
        for code, label in LABS_ORDER:
            row[label] = labs.get(code)
        # 요검사/보체 요약 저장
        row["U-RBC(/HPF)"] = u_rbc
        row["U-WBC(/HPF)"] = u_wbc
        row["U-Albumin"] = u_albumin
        row["U-OB"] = u_ob
        row["U-Glucose"] = u_glucose
        row["C3(mg/dL)"] = C3
        row["C4(mg/dL)"] = C4
        row["CH50(U/mL)"] = CH50
        newdf = pd.DataFrame([row])
        if df_prev is None or df_prev.empty:
            df = newdf
        else:
            df = pd.concat([df_prev, newdf], ignore_index=True)
            df = df.drop_duplicates(subset=["Date"], keep="last").sort_values("Date")
        for col in (["Date"] + labels):
            if col not in df.columns:
                df[col] = pd.NA
        df = df.reindex(columns=(["Date"] + labels + [
            "U-RBC(/HPF)", "U-WBC(/HPF)", "U-Albumin", "U-OB", "U-Glucose",
            "C3(mg/dL)", "C4(mg/dL)", "CH50(U/mL)"
        ]))
        st.session_state["lab_hist"][key] = df
        st.success("저장 완료!")

    dfh = st.session_state.get("lab_hist", {}).get(key)
    if not has_key:
        st.info("그래프는 별명 + PIN(4자리) 저장 시 표시됩니다.")
    elif isinstance(dfh, pd.DataFrame) and not dfh.empty:
        st.markdown("##### 📊 추이 그래프")
        nonnull_cols = [c for c in dfh.columns if (c != "Date" and dfh[c].notna().any())]
        default_pick = [c for c in ["WBC(백혈구)", "Hb(혈색소)", "PLT(혈소판)", "CRP(C-반응성단백,염증)", "ANC(절대호중구,면역력)"] if c in nonnull_cols]
        pick = st.multiselect("지표 선택", options=nonnull_cols, default=default_pick)
        if pick:
            st.line_chart(dfh.set_index("Date")[pick], use_container_width=True)
        st.dataframe(dfh[["Date"] + nonnull_cols], use_container_width=True, height=240)
    else:
        st.info("저장된 히스토리가 없습니다. 값을 입력하고 ‘피수치 저장/추가’를 눌러 보세요.")

    # 7) 해석하기
    if st.button("🔎 해석하기", key="analyze_cancer"):
        st.session_state["analyzed"] = True
        st.session_state["analysis_ctx"] = {
            "mode": "암",
            "group": group,
            "dx": dx,
            "dx_label": dx_display(group, dx),
            "labs": labs,
            "user_chemo": user_chemo,
            "user_abx": user_abx,
            "urinalysis": {
                "albumin": u_albumin, "glucose": u_glucose, "ob": u_ob,
                "rbc_hpf": u_rbc, "wbc_hpf": u_wbc,
                "lines": u_lines,
            },
            "complement": {"C3": C3, "C4": C4, "CH50": CH50, "lines": comp_lines},
        }

    schedule_block()

# ==================== 소아 모드 ====================
else:
    # 공통 기본 입력(두 트랙 공용)
    ctop = st.columns(3)
    with ctop[0]:
        input_mode = st.radio("입력 방식", ["증상 기반", "진단명 직접"], horizontal=True)
    with ctop[1]:
        age_m = st.number_input("나이(개월)", min_value=0, step=1)
    with ctop[2]:
        weight = st.number_input("체중(kg)", min_value=0.0, step=0.1)

    # 해열제(1회 평균) — 두 트랙 모두 표시
    apap_ml, apap_w = acetaminophen_ml(age_m, weight or None)
    ibu_ml, ibu_w = ibuprofen_ml(age_m, weight or None)
    dc = st.columns(2)
    with dc[0]:
        st.metric("아세트아미노펜 시럽", f"{apap_ml} mL", help=f"계산 체중 {apap_w} kg · 160 mg/5 mL, 12.5 mg/kg")
    with dc[1]:
        st.metric("이부프로펜 시럽", f"{ibu_ml} mL", help=f"계산 체중 {ibu_w} kg · 100 mg/5 mL, 7.5 mg/kg")

    # ------- 트랙 A: 증상 기반 -------
    if input_mode == "증상 기반":
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            nasal = st.selectbox("콧물", ["없음", "투명", "흰색", "누런", "피섞임"])
        with c2:
            cough = st.selectbox("기침", ["없음", "조금", "보통", "심함"])
        with c3:
            diarrhea = st.selectbox("설사(횟수/일)", ["없음", "1~2회", "3~4회", "5~6회"])
        with c4:
            fever = st.selectbox("발열", ["없음", "37~37.5", "37.5~38", "38.5~39", "39+"])
        c5, c6 = st.columns(2)
        with c5:
            temp = st.number_input("체온(℃)", min_value=0.0, step=0.1)
        with c6:
            fever_days = st.number_input("발열 지속(일)", min_value=0, step=1)
        vomit = st.selectbox("구토", ["없음", "1~2회", "3회 이상"])  

        # 예측 로직
        def _predict_disease(nasal: str, cough: str, diarrhea: str, fever_text: str, temp_val: float, fever_days: int, vomit: str) -> str:
            ft = fever_text or ""
            high_fever = (temp_val and temp_val >= 38.0) or ("38.5" in ft or "39" in ft)
            diarrhea_heavy = any(s in diarrhea for s in ["3~4", "5~6"])
            vomit_present = vomit != "없음"
            # 🔴 규칙: 38℃ 이상 + 2일 이상 + 설사 4회 이상 + 구토 동반 → 장염/로타 의심
            if high_fever and fever_days >= 2 and diarrhea_heavy and vomit_present:
                return "장염/로타 의심"
            if diarrhea_heavy:
                return "로타/장염 가능"
            if high_fever:
                if cough in {"보통", "심함"}:
                    return "독감/코로나 가능"
                return "편도염/고열성 바이러스 감염 가능"
            if cough == "심함" and nasal in {"흰색", "누런"}:
                return "RSV/상기도염 가능"
            if nasal in {"투명"} and cough in {"조금", "보통"}:
                return "아데노/상기도염 가능"
            return "경미한 감기/회복기 가능"

        pred = _predict_disease(nasal, cough, diarrhea, fever, temp, fever_days, vomit)
        st.caption(f"🤖 증상 기반 추정: **{pred}** (참고용)")

        if st.button("🔎 해석하기", key="analyze_peds_sx"):
            st.session_state["analyzed"] = True
            st.session_state["analysis_ctx"] = {
                "mode": "소아",
                "input_mode": "증상 기반",
                "disease": None,
                "pred": pred,
                "symptoms": {"콧물": nasal, "기침": cough, "설사": diarrhea, "발열": fever, "구토": vomit, "발열지속(일)": fever_days},
                "temp": temp,
                "age_m": age_m,
                "weight": weight or None,
                "apap_ml": apap_ml,
                "ibu_ml": ibu_ml,
            }

    # ------- 트랙 B: 진단명 직접 -------
    else:
        dx_manual = st.selectbox("진단명(직접 선택)", ["로타/장염", "독감/코로나", "RSV", "아데노", "마이코", "수족구", "편도염", "코로나", "중이염"], index=0)
        if st.button("🔎 해석하기", key="analyze_peds_dx"):
            st.session_state["analyzed"] = True
            st.session_state["analysis_ctx"] = {
                "mode": "소아",
                "input_mode": "진단명 직접",
                "disease": dx_manual,
                "pred": None,
                "symptoms": {},
                "age_m": age_m,
                "weight": weight or None,
                "apap_ml": apap_ml,
                "ibu_ml": ibu_ml,
            }

# -------------------- 보고서 빌더 --------------------

def _build_report_md(ctx: dict, sections: list) -> str:
    lines = []
    lines.append(f"# BloodMap 결과\n")
    lines.append(f"- 모드: {ctx.get('mode')}\n")
    if ctx.get("mode") == "암":
        lines.append(f"- 진단: {ctx.get('dx_label') or ctx.get('dx')}\n")
        labs = ctx.get("labs", {})
        if labs:
            lines.append("\n## 피수치 요약\n")
            for k, v in labs.items():
                if v is not None:
                    lines.append(f"- {k}: {v}")
        lines.append("\n## 선택 약물\n")
        for k in (ctx.get("user_chemo") or []):
            lines.append(f"- 항암제: {k}")
        for k in (ctx.get("user_abx") or []):
            lines.append(f"- 항생제: {k}")
        ua = ctx.get("urinalysis") or {}
        if ua:
            lines.append("\n## 요검사 요약\n")
            lines.append(f"- 알부민뇨: {ua.get('albumin')}")
            lines.append(f"- 잠혈: {ua.get('ob')}")
            lines.append(f"- 요당: {ua.get('glucose')}")
            if ua.get('rbc_hpf') is not None:
                lines.append(f"- 적혈구: {ua.get('rbc_hpf')}/HPF")
            if ua.get('wbc_hpf') is not None:
                lines.append(f"- 백혈구: {ua.get('wbc_hpf')}/HPF")
        comp = ctx.get("complement") or {}
        if comp:
            lines.append("\n## 보체검사 요약\n")
            for n in ["C3", "C4", "CH50"]:
                v = comp.get(n)
                if v is not None:
                    lines.append(f"- {n}: {v}")
    else:
        im = ctx.get("input_mode")
        if im == "증상 기반":
            if ctx.get("pred"):
                lines.append(f"- 증상 기반 추정: {ctx.get('pred')}\n")
                dk = _diet_key_from_text(ctx.get("pred"))
                if dk:
                    for r in peds_diet_lines(dk):
                        sections.append(("소아 식이가이드", [r]))
        else:
            lines.append(f"- 진단: {ctx.get('disease')}\n")
            dk = _diet_key_from_text(ctx.get("disease"))
            if dk:
                for r in peds_diet_lines(dk):
                    sections.append(("소아 식이가이드", [r]))
        lines.append("\n## 해열제 1회 평균\n")
        lines.append(f"- 아세트아미노펜: {ctx.get('apap_ml')} mL")
        lines.append(f"- 이부프로펜: {ctx.get('ibu_ml')} mL")

    for title, rows in sections:
        lines.append(f"\n## {title}\n")
        for r in rows:
            lines.append(f"- {r}")

    lines.append("\n---\n")
    lines.append(CFG.DISCLAIMER)
    return "\n".join(lines)


def _build_report_txt(md: str) -> str:
    txt = md.replace("**", "").replace("# ", "").replace("## ", "").replace("---", "-")
    return txt

# -------------------- 결과 게이트 --------------------
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

        ua = ctx.get("urinalysis") or {}
        if ua:
            st.subheader("🚽 요검사 요약")
            y1, y2, y3, y4 = st.columns(4)
            with y1:
                st.metric("알부민뇨", ua.get("albumin"))
            with y2:
                st.metric("잠혈", ua.get("ob"))
            with y3:
                st.metric("RBC/HPF", ua.get("rbc_hpf"))
            with y4:
                st.metric("WBC/HPF", ua.get("wbc_hpf"))
            for L in (ua.get("lines") or []):
                st.write("- " + L)

        comp = ctx.get("complement") or {}
        if comp:
            st.subheader("🧪 보체검사 요약")
            z1, z2, z3 = st.columns(3)
            with z1:
                st.metric("C3", comp.get("C3"))
            with z2:
                st.metric("C4", comp.get("C4"))
            with z3:
                st.metric("CH50", comp.get("CH50"))
            for L in (comp.get("lines") or []):
                st.write("- " + L)

        st.subheader("💊 항암제(세포독성) 부작용")
        render_adverse_effects(st, ctx.get("user_chemo") or [], DRUG_DB)

        st.subheader("🧫 항생제 부작용")
        render_adverse_effects(st, ctx.get("user_abx") or [], DRUG_DB)

        st.subheader("🥗 피수치 기반 식이가이드 (예시)")
        lines = lab_diet_guides(labs, heme_flag=(ctx.get("group") == "혈액암"))
        for L in lines:
            st.write("- " + L)
        if lines:
            report_sections.append(("피수치 식이가이드", lines))

        st.subheader("💊 (자동 추천) 약물 부작용")
        rec = auto_recs_by_dx(ctx.get("group"), ctx.get("dx"), DRUG_DB, ONCO_MAP)
        regimen = (rec.get("chemo") or []) + (rec.get("targeted") or [])
        render_adverse_effects(st, regimen, DRUG_DB)

    elif ctx.get("mode") == "소아":
        im = ctx.get("input_mode", "증상 기반")

        # 공통: 해열제 용량
        st.subheader("🌡️ 해열제 1회분(평균)")
        dcols = st.columns(2)
        with dcols[0]:
            st.metric("아세트아미노펜 시럽", f"{ctx.get('apap_ml')} mL")
        with dcols[1]:
            st.metric("이부프로펜 시럽", f"{ctx.get('ibu_ml')} mL")

        # 트랙 A: 증상 기반 → 증상 요약 + 예측명 식이가이드
        if im == "증상 기반":
            st.subheader("👶 증상 요약")
            sy = ctx.get("symptoms", {})
            sy_cols = st.columns(4)
            keys = list(sy.keys())
            for i, key in enumerate(keys):
                with sy_cols[i % 4]:
                    st.metric(key, sy[key])
            if ctx.get("pred"):
                st.caption(f"🤖 증상 기반 추정: **{ctx['pred']}** (참고용)")
                dk = _diet_key_from_text(ctx["pred"]) 
                if dk:
                    lines = peds_diet_lines(dk)
                    st.subheader("🍽 식이가이드 (예측)")
                    for L in lines:
                        st.write("- " + L)
                    report_sections.append(("소아 식이가이드", lines))
        # 트랙 B: 진단명 직접 → 진단 + 해당 식이가이드만
        else:
            st.subheader("🧾 진단")
            st.write(ctx.get("disease"))
            dk = _diet_key_from_text(ctx.get("disease"))
            lines = peds_diet_lines(dk)
            st.subheader("🍽 식이가이드 (선택 질환)")
            for L in lines:
                st.write("- " + L)
            report_sections.append(("소아 식이가이드", lines))

    # 저장/다운로드
    st.markdown("---")
    st.markdown("### ⤵️ 보고서 저장 (.md / .txt)")
    md = _build_report_md(ctx, report_sections)
    txt = _build_report_txt(md)
    st.download_button("📥 Markdown(.md)", data=md, file_name="bloodmap_report.md", mime="text/markdown")
    st.download_button("📥 Text(.txt)", data=txt, file_name="bloodmap_report.txt", mime="text/plain")

    st.stop()
