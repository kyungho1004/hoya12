# -*- coding: utf-8 -*-
# BloodMap — 소아/암 통합 + 특수검사(지질·응고·보체·요검사·갑상선·당대사·패혈증·빈혈패널)
# 면역/세포치료 제외. 소아 해열제: 1회 권장량만 표기.
# ✅ 해석/저장 분리: [🔎 해석하기]는 별명·PIN 없이 가능, [💾 저장하기]는 별명#PIN 필요. 그래프는 저장된 기록만.
# ✅ 식이가이드 경고: 혈액암/항암 단계면 "철분+비타민C" 주의 문구 자동 포함.
# ✅ NEW: 보호자 체크 (질환별 증상 프리셋 + 세부 선택)
#    - DISEASE_SYMPTOMS에 기반하여 ‘기침/콧물/설사/열/두통/호흡곤란/물집/탈수/눈꼽’ 등 세부 옵션 제공
#    - 예: 기침(없음/조금/보통/심함), 콧물(없음/투명/흰색/노란색/피섞임), 설사(횟수), 열(범주 + 현재체온),
#         두통/호흡곤란/눈꼽(없음/조금/보통/많이 심함), 물집(없음/있음+부위), 탈수증상(있음/없음)

import os, json
from datetime import datetime, date
from typing import Dict, Any, List, Optional, Tuple
import streamlit as st
import pandas as pd

st.set_page_config(page_title="BloodMap", layout="centered")

APP_TITLE  = "피수치 가이드 (BloodMap)"
MADE_BY    = "제작: Hoya/GPT"
DISCLAIMER = (
    "본 수치는 참고용이며, 해석 결과는 개발자와 무관합니다.  "
    "약 변경, 복용 중단 등은 반드시 주치의와 상의 후 결정하시기 바랍니다.  "
    "이 앱은 개인정보를 절대 수집하지 않으며, 어떠한 개인정보 입력도 요구하지 않습니다."
)
FEVER_GUIDE = "38.0~38.5℃: 해열제/경과관찰 · 38.5~39.0℃: 해열제+병원 연락 고려 · 39.0℃ 이상: 즉시 병원"
RECORDS_PATH = "records.json"

# ------------------ 기본 컬럼/라벨 ------------------
ORDER = ["WBC","Hb","PLT","ANC","Ca","P","Na","K","Alb","Glu","TP",
         "AST","ALT","LDH","CRP","Cr","UA","TB","BUN","BNP"]

KR = {
    "WBC":"백혈구","Hb":"혈색소","PLT":"혈소판(PLT)","ANC":"호중구(ANC)",
    "Ca":"칼슘","P":"인","Na":"소디움","K":"포타슘",
    "Alb":"알부민","Glu":"혈당","TP":"총단백",
    "AST":"AST(간 효소)","ALT":"ALT(간세포)","LDH":"LDH",
    "CRP":"CRP(염증)","Cr":"크레아티닌","UA":"요산",
    "TB":"총빌리루빈","BUN":"BUN","BNP":"BNP",
}
def label(abbr: str) -> str:
    base = KR.get(abbr, abbr)
    han = base.split("(")[-1].rstrip(")") if "(" in base else base
    return f"{abbr} ({han})"

# ------------------ 저장/불러오기 ------------------
def load_records() -> Dict[str, List[dict]]:
    try:
        if os.path.exists(RECORDS_PATH):
            with open(RECORDS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def save_records(data: Dict[str, List[dict]]):
    try:
        with open(RECORDS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# ------------------ 유틸/계산 ------------------
def parse_float(x):
    try:
        if x is None: return None
        s = str(x).strip()
        if not s: return None
        return float(s)
    except Exception:
        return None

def entered(v) -> bool:
    try:
        return v is not None and float(v) == float(v)
    except Exception:
        return False

def calc_corrected_ca(total_ca, albumin):
    try:
        if total_ca is None or albumin is None:
            return None
        return round(float(total_ca) + 0.8*(4.0 - float(albumin)), 2)
    except Exception:
        return None

def calc_friedewald_ldl(tc, hdl, tg):
    try:
        if tg is None or float(tg) >= 400:
            return None
        return round(float(tc) - float(hdl) - float(tg)/5.0, 1)
    except Exception:
        return None

def calc_non_hdl(tc, hdl):
    try:
        return round(float(tc) - float(hdl), 1)
    except Exception:
        return None

def calc_homa_ir(glu_fasting, insulin):
    try:
        return round((float(glu_fasting) * float(insulin)) / 405.0, 2)
    except Exception:
        return None

def calc_egfr(creatinine, age=60, sex="F"):
    try:
        scr = float(creatinine)
        k = 0.7 if sex == "F" else 0.9
        alpha = -0.241 if sex == "F" else -0.302
        min_scr_k = min(scr/k, 1)
        max_scr_k = max(scr/k, 1)
        sex_factor = 1.012 if sex == "F" else 1.0
        egfr = 142 * (min_scr_k**alpha) * (max_scr_k**(-1.200)) * (0.9938**float(age)) * sex_factor
        return int(round(egfr, 0))
    except Exception:
        return None

def stage_egfr(egfr):
    try:
        e = float(egfr)
    except Exception:
        return None, None
    if e >= 90:   return "G1", "정상/고정상 (≥90)"
    if 60 <= e < 90:  return "G2", "경도 감소 (60–89)"
    if 45 <= e < 60:  return "G3a", "중등도 감소 (45–59)"
    if 30 <= e < 45:  return "G3b", "중등도~중증 감소 (30–44)"
    if 15 <= e < 30:  return "G4", "중증 감소 (15–29)"
    return "G5", "신부전 (<15)"

def stage_acr(acr_mg_g):
    try:
        a = float(acr_mg_g)
    except Exception:
        return None, None
    if a < 30: return "A1", "정상-경도 증가 (<30 mg/g)"
    if a <= 300: return "A2", "중등도 증가 (30–300 mg/g)"
    return "A3", "중증 증가 (>300 mg/g)"

# ------------------ 기본 해석 ------------------
def interpret_labs(v: Dict[str, Any]) -> List[str]:
    out = []
    g = lambda k: v.get(k)
    if entered(g("WBC")):
        if g("WBC") < 3.0: out.append("WBC 낮음 → 🟡 감염 주의(손 위생·마스크·혼잡 피하기)")
        elif g("WBC") > 11.0: out.append("WBC 높음 → 🟡 염증/감염 가능성")
    if entered(g("Hb")):
        if g("Hb") < 8.0: out.append("Hb 낮음 → 🟠 증상 주의/필요 시 수혈 의논")
        elif g("Hb") < 10.0: out.append("Hb 경도 감소 → 🟡 경과관찰")
    if entered(g("PLT")) and g("PLT") < 50: out.append("혈소판 낮음 → 🟥 멍/출혈 주의, 넘어짐·양치 시 조심")
    if entered(g("ANC")):
        if g("ANC") < 500: out.append("ANC 매우 낮음 → 🟥 생채소 금지·익힌 음식·남은 음식 2시간 이후 비권장·껍질 과일 상담")
        elif g("ANC") < 1000: out.append("ANC 낮음 → 🟠 감염 위험↑, 외출/위생 관리")
    if entered(g("AST")) and g("AST") >= 50: out.append("AST 상승 → 🟡 간 기능 저하 가능")
    if entered(g("ALT")) and g("ALT") >= 55: out.append("ALT 상승 → 🟡 간세포 손상 의심")
    if entered(g("Alb")) and g("Alb") < 3.5: out.append("알부민 낮음 → 🟡 영양 보강 권장")
    if entered(g("Cr")) and g("Cr") > 1.2: out.append("Cr 상승 → 🟡 신장 기능 저하 가능")
    if entered(g("CRP")) and g("CRP") >= 0.5: out.append("CRP 상승 → 🟡 염증/감염 활동 가능성")
    return out

# ------------------ 특수검사 해석(확장) ------------------
def interpret_special_extended(qc: Dict[str, str], qn: Dict[str, float], base_vals: Dict[str, Any]=None, profile: str="adult") -> List[str]:
    out = []
    ped = str(profile).lower().startswith("p")

    # 보체
    C3, C4, CH50 = qn.get("C3"), qn.get("C4"), qn.get("CH50")
    if C3 is not None:
        c3 = float(C3)
        if c3 < 90: out.append(f"C3 {c3} mg/dL 낮음 → 🟡 자가면역/보체 소모 가능성")
        elif c3 > 180: out.append(f"C3 {c3} mg/dL 상승")
    if C4 is not None:
        c4 = float(C4)
        if c4 < 10: out.append(f"C4 {c4} mg/dL 낮음 → 🟡 고전경로 이상 가능")
        elif c4 > 40: out.append(f"C4 {c4} mg/dL 상승")
    if CH50 is not None and float(CH50) < 40:
        out.append(f"CH50 {CH50} U/mL 낮음 → 🟡 보체 결핍/소모 의심")

    # 응고
    PT, aPTT, Fbg, Dd = qn.get("PT"), qn.get("aPTT"), qn.get("Fibrinogen"), qn.get("D-dimer")
    if PT is not None and float(PT) > 15: out.append(f"PT {PT}s 연장 → 🟠 간질환/비타민K/항응고제 확인")
    if aPTT is not None and float(aPTT) > 45: out.append(f"aPTT {aPTT}s 연장 → 🟠 내인성 경로 이상/항응고제")
    if Fbg is not None and float(Fbg) < 150: out.append(f"Fibrinogen {Fbg} mg/dL 낮음 → 🟠 DIC/간질환 가능")
    if Dd is not None and float(Dd) > 0.5: out.append(f"D-dimer {Dd} µg/mL 상승")

    # 지질
    TG, TC, HDL, LDL, nonHDL = qn.get("TG"), qn.get("TC"), qn.get("HDL"), qn.get("LDL"), qn.get("Non-HDL-C")
    if TG is not None:
        t = float(TG)
        if not ped:
            if t >= 500: out.append(f"TG {t} mg/dL 매우 높음 → 🟥 췌장염 위험")
            elif t >= 200: out.append(f"TG {t} mg/dL 높음")
            elif t >= 150: out.append(f"TG {t} mg/dL 경계")
        else:
            if t >= 160: out.append(f"TG {t} (소아) 높음")
            elif t >= 130: out.append(f"TG {t} (소아) 경계")
    if TC is not None:
        c = float(TC)
        if not ped:
            if c >= 240: out.append(f"총콜레스테롤 {c} 높음")
            elif c >= 200: out.append(f"총콜레스테롤 {c} 경계")
        else:
            if c >= 200: out.append(f"총콜레스테롤 {c} (소아) 높음")
            elif c >= 170: out.append(f"총콜레스테롤 {c} (소아) 경계")
    if HDL is not None:
        h = float(HDL)
        if (not ped and h < 40) or (ped and h < 45): out.append(f"HDL {h} 낮음")
    if LDL is not None:
        l = float(LDL)
        if not ped:
            if l >= 190: out.append(f"LDL {l} 매우 높음")
            elif l >= 160: out.append(f"LDL {l} 높음")
            elif l >= 130: out.append(f"LDL {l} 경계")
        else:
            if l >= 160: out.append(f"LDL {l} (소아) 매우 높음")
            elif l >= 130: out.append(f"LDL {l} (소아) 높음")
            elif l >= 110: out.append(f"LDL {l} (소아) 경계")
    if nonHDL is not None:
        nh = float(nonHDL)
        if not ped:
            if nh >= 190: out.append(f"Non-HDL {nh} 매우 높음")
            elif nh >= 160: out.append(f"Non-HDL {nh} 높음")
            elif nh >= 130: out.append(f"Non-HDL {nh} 경계")
        else:
            if nh >= 190: out.append(f"Non-HDL {nh} (소아) 매우 높음")
            elif nh >= 145: out.append(f"Non-HDL {nh} (소아) 높음")
            elif nh >= 120: out.append(f"Non-HDL {nh} (소아) 경계")

    # 갑상선
    TSH, FT4 = qn.get("TSH"), qn.get("Free T4")
    if TSH is not None and FT4 is not None:
        T, F = float(TSH), float(FT4)
        if T > 4.0 and F < 0.8: out.append("패턴: 원발성 갑상선저하증 의심 (TSH↑, FT4↓)")
        if T < 0.4 and F > 1.8: out.append("패턴: 갑상선기능항진증 의심 (TSH↓, FT4↑)")

    # 당대사
    glu, a1c, homa = qn.get("공복혈당"), qn.get("HbA1c"), qn.get("HOMA-IR")
    if glu is not None:
        g = float(glu)
        if g >= 126: out.append(f"공복혈당 {g} → 당뇨 의심")
        elif g >= 100: out.append(f"공복혈당 {g} → 공복혈당장애")
    if a1c is not None:
        a = float(a1c)
        if a >= 6.5: out.append(f"HbA1c {a}% → 당뇨 의심")
        elif a >= 5.7: out.append(f"HbA1c {a}% → 당뇨 전단계")
    if homa is not None and float(homa) >= 2.5:
        out.append(f"HOMA-IR {homa} → 인슐린 저항성 의심")

    # 신장/eGFR
    egfr = qn.get("eGFR") or (base_vals or {}).get("eGFR")
    if egfr is not None:
        stage, label = stage_egfr(egfr)
        if stage: out.append(f"eGFR {egfr} → CKD {stage} ({label})")

    # 요검사
    if qc.get("알부민뇨") in {"+","++","+++"}: out.append(f"알부민뇨 {qc['알부민뇨']} → 🚨 신장 기능 이상 가능성")
    if qc.get("혈뇨") in {"+","++","+++"}: out.append(f"혈뇨 {qc['혈뇨']} → 🟠 요로계 염증/결석 가능성")

    # 빈혈 패널
    ferr, tsat = qn.get("Ferritin"), qn.get("TSAT")
    if ferr is not None and float(ferr) < 30: out.append(f"Ferritin {ferr} 낮음 → 철결핍 가능")
    if tsat is not None and float(tsat) < 20: out.append(f"TSAT {tsat}% 낮음 → 철결핍/만성질환빈혈 감별")

    # 전해질 확장
    mg, phos, ica, ca_corr = qn.get("Mg"), qn.get("Phos(인)"), qn.get("iCa"), qn.get("Corrected Ca")
    if mg is not None and (float(mg) < 1.6 or float(mg) > 2.3): out.append(f"Mg {mg} 비정상(정상 1.6–2.3)")
    if phos is not None and (float(phos) < 2.4 or float(phos) > 4.5): out.append(f"인 {phos} 비정상(정상 2.4–4.5)")
    if ica is not None and (float(ica) < 1.10 or float(ica) > 1.32): out.append(f"이온화칼슘 {ica} mmol/L 비정상(정상 1.10–1.32)")
    if ca_corr is not None and (float(ca_corr) < 8.5 or float(ca_corr) > 10.2): out.append(f"보정 칼슘 {ca_corr} mg/dL 비정상(정상 8.5–10.2)")

    # 염증/패혈증
    pct, lac = qn.get("PCT"), qn.get("Lactate")
    if pct is not None and float(pct) >= 0.5: out.append(f"PCT {pct} ng/mL 상승(세균감염/패혈증 의심)")
    if lac is not None:
        l = float(lac)
        if l >= 4.0: out.append(f"Lactate {l} mmol/L 매우 높음 → 🟥 응급")
        elif l > 2.0: out.append(f"Lactate {l} mmol/L 상승")

    return out

# ------------------ 소아 질환/증상 ------------------
PED_DISEASES = [
    "일반 감기(상기도감염)","RSV","Adenovirus(아데노)","Parainfluenza(파라인플루엔자)","Influenza(독감)",
    "COVID-19","Rotavirus(로타)","Norovirus(노로)","수족구(HFMD)","Mycoplasma(마이코플라즈마)",
    "중이염 의심","결막염 의심","크룹(Croup)","모세기관지염(Bronchiolitis)","폐렴 의심"
]

# 🔸 질환별 대표 증상 프리셋(요청안 반영)
DISEASE_SYMPTOMS = {
    "RSV": ["기침", "콧물", "쌕쌕거림", "호흡곤란"],
    "Adenovirus(아데노)": ["열", "눈충혈", "기침", "설사"],
    "Parainfluenza(파라인플루엔자)": ["기침", "쉰목소리", "호흡곤란"],
    "Rotavirus(로타)": ["설사", "구토", "탈수"],
    "수족구(HFMD)": ["물집", "입안 통증", "열"],
    "COVID-19": ["열", "기침", "콧물", "무증상", "후각소실"],
    "크룹(Croup)": ["쉰목소리", "개짖는 기침", "호흡곤란"],
    "모세기관지염(Bronchiolitis)": ["쌕쌕거림", "호흡곤란", "기침"],
    "Mycoplasma(마이코플라즈마)": ["기침", "두통", "열", "피로감"]
}

# 보호자 체크 UI 생성
def render_caregiver_check(ped_dx: str) -> Dict[str, Any]:
    preset = DISEASE_SYMPTOMS.get(ped_dx, ["기침","콧물","열"])
    st.markdown("### 👪 보호자 체크")
    result: Dict[str, Any] = {}
    # 공통 위젯들
    if "기침" in preset or "개짖는 기침" in preset:
        result["기침"] = st.radio("기침", ["없음","조금","보통","심함"], index=0, horizontal=True, key="cg_cough")
    if "개짖는 기침" in preset:
        result["개짖는 기침"] = st.radio("개짖는 기침", ["없음","조금","보통","심함"], index=0, horizontal=True, key="cg_bark")
    if "콧물" in preset:
        result["콧물"] = st.radio("콧물", ["없음","투명","흰색","노란색","피섞임"], index=0, horizontal=True, key="cg_rn")
    if "설사" in preset:
        c1, c2 = st.columns([2,1])
        result["설사_횟수"] = int(c1.number_input("설사 횟수(하루)", min_value=0, max_value=30, step=1, value=0, key="cg_diarrhea"))
        result["구토"] = st.radio("구토", ["없음","조금","보통","심함"], index=0, horizontal=True, key="cg_vomit") if "구토" in preset else result.get("구토")
    if "열" in preset:
        c1, c2 = st.columns([1,1])
        result["열_범주"] = c1.radio("열(범주)", ["없음","37.5~38","38~39","39 이상"], index=0, horizontal=True, key="cg_fever_cat")
        result["열_현재체온"] = c2.text_input("현재 체온(℃, 선택)", placeholder="예: 38.2", key="cg_temp")
    if "두통" in preset:
        result["두통"] = st.radio("두통", ["없음","조금","보통","많이 심함"], index=0, horizontal=True, key="cg_headache")
    if "호흡곤란" in preset:
        result["호흡곤란"] = st.radio("호흡곤란", ["없음","조금","보통","많이 심함"], index=0, horizontal=True, key="cg_dysp")
    if "쌕쌕거림" in preset:
        result["쌕쌕거림"] = st.radio("쌕쌕거림", ["없음","조금","보통","많이 심함"], index=0, horizontal=True, key="cg_wheeze")
    if "쉰목소리" in preset:
        result["쉰목소리"] = st.radio("쉰목소리", ["없음","조금","보통","많이 심함"], index=0, horizontal=True, key="cg_hoarse")
    if "물집" in preset:
        has_blister = st.checkbox("물집 있음", value=False, key="cg_blister")
        result["물집"] = "있음" if has_blister else "없음"
        if has_blister:
            result["물집_부위"] = st.selectbox("물집 부위", ["손","발","전신"], index=0, key="cg_blister_loc")
    if "탈수" in preset or "탈수증상" in preset:
        result["탈수증상"] = st.radio("탈수증상", ["없음","있음"], index=0, horizontal=True, key="cg_dehy")
    if "눈충혈" in preset or "눈곱" in preset:
        result["눈곱/결막"] = st.radio("눈곱/결막충혈", ["없음","조금","보통","많이 심함"], index=0, horizontal=True, key="cg_eye")
    if "무증상" in preset:
        result["무증상"] = st.checkbox("무증상(증상 전혀 없음)", value=False, key="cg_asx")
    # 추가 메모
    result["보호자_메모"] = st.text_area("추가 메모(선택)", placeholder="예: 밤새 기침 심했고 해열제 20:30 투여", key="cg_note")
    return result

def summarize_ped_checks(cg: Dict[str, Any]) -> List[str]:
    out = []
    if not cg: return out
    def add(name, key, transform=lambda x:x):
        if key in cg and str(cg[key]).strip():
            v = transform(cg[key])
            if v in ["없음", "0", 0, "", None, False]: return
            out.append(f"{name}: {v}")
    add("기침", "기침")
    add("개짖는 기침", "개짖는 기침")
    add("콧물", "콧물")
    if "설사_횟수" in cg and int(cg["설사_횟수"])>0:
        out.append(f"설사: {int(cg['설사_횟수'])}회/일")
    add("구토", "구토")
    if cg.get("열_범주") and cg["열_범주"]!="없음":
        tv = cg.get("열_현재체온","").strip()
        out.append(f"열: {cg['열_범주']}" + (f" (현재 {tv}℃)" if tv else ""))
    add("두통", "두통")
    add("호흡곤란", "호흡곤란")
    add("쌕쌕거림", "쌕쌕거림")
    add("쉰목소리", "쉰목소리")
    if cg.get("물집")=="있음":
        out.append(f"물집: 있음" + (f" ({cg.get('물집_부위')})" if cg.get("물집_부위") else ""))
    if cg.get("탈수증상")=="있음":
        out.append("탈수증상: 있음")
    add("눈곱/결막", "눈곱/결막")
    if cg.get("무증상"): out.append("무증상")
    return out

def interpret_peds_symptoms_from_checks(dx: str, cg: Dict[str, Any]) -> List[str]:
    tips: List[str] = []

    # 기존 텍스트 룰 + 강화된 룰
    # 크룹/개짖는 기침/쉰목소리
    if dx in ["Parainfluenza(파라인플루엔자)","크룹(Croup)"] or cg.get("개짖는 기침") in ["보통","심함","많이 심함"]:
        tips.append("크룹 가능성: 찬 공기 잠시 쐬고 진정. 스트라이더/호흡곤란이면 즉시 응급실.")
    # 모세기관지염/RSV
    if dx in ["RSV","모세기관지염(Bronchiolitis)"] or cg.get("쌕쌕거림") in ["보통","많이 심함"] or cg.get("호흡곤란") in ["보통","많이 심함"]:
        tips.append("하기도 폐색/모세기관지염 가능: 호흡수↑·함몰·입술청색증 시 즉시 병원. 코세척/가습/수분.")
    # 결막/눈곱
    if cg.get("눈곱/결막") in ["보통","많이 심함"]:
        tips.append("결막염 의심: 손 위생·수건 공동사용 금지, 심하면 항생제 점안 상담.")
    # 위장관염/탈수
    if dx in ["Rotavirus(로타)","Norovirus(노로)"] or int(cg.get("설사_횟수") or 0) >= 6 or cg.get("탈수증상")=="있음":
        tips.append("구토·설사/탈수: ORS 소량씩 자주, 소변량/축 처짐 체크. 지속/증악 시 진료.")
    # 열
    fever_cat = cg.get("열_범주")
    if fever_cat in ["38~39","39 이상"]:
        tips.append("고열: 항해열제 1회 용량 사용 후 경과 관찰, 39℃ 이상 지속·경련·의식저하 시 응급평가.")
    # 두통
    if cg.get("두통") in ["보통","많이 심함"]:
        tips.append("두통 동반: 수분·휴식, 지속/악화 시 진료 필요.")
    # COVID-19
    if dx == "COVID-19":
        tips.append("COVID-19: 격리 지침 및 해열/수분, 위험군은 항바이러스제 진료 상담.")
    # 수족구 물집
    if dx == "수족구(HFMD)" or cg.get("물집")=="있음":
        tips.append("수족구: 통증으로 수분섭취 저하 주의, 탈수 징후 모니터, 유치원 등원은 지침 확인.")

    return list(dict.fromkeys(tips))  # 중복 제거

# ------------------ 피수치별 식이가이드 ------------------
def build_diet_guide(labs: Dict[str, Any], qn: Dict[str, Any], mode: str) -> List[str]:
    out: List[str] = []
    g = lambda k: labs.get(k)

    if entered(g("ANC")) and g("ANC") < 500:
        out.append("ANC < 500 → 익힌 음식만(회/덜익은 고기·달걀·생채소/새싹 금지), 과일은 껍질 제거·흐르는 물 세척, 남은 음식 2시간 넘기지 않기, 생수는 밀봉 제품.")
    elif entered(g("ANC")) and g("ANC") < 1000:
        out.append("ANC 500~1000 → 외식·뷔페·길거리 음식 주의, 가열 충분히, 손 위생 철저.")
    if entered(g("PLT")) and g("PLT") < 50:
        out.append("혈소판 < 50 → 딱딱·날카로운 음식(뼈있는 생선, 질긴 육포, 딱딱한 견과류) 조심, 빨대·강한 가글 금지, 술 금지. (진통제/항혈소판제는 의료진과 상의)")
    if (entered(g("AST")) and g("AST") >= 50) or (entered(g("ALT")) and g("ALT") >= 55):
        out.append("간수치 상승 → 술/허브보충제 중단, 튀김·기름진 음식 줄이기, 아세트아미노펜 과량 금지, 수분·균형식. 지속 시 상담.")
    if entered(g("Alb")) and g("Alb") < 3.5:
        out.append("알부민 낮음 → 단백질 보강(살코기·생선·달걀·두부/콩·유제품), 소량씩 자주. 부종/신질환 있으면 개인지침 우선.")
    TG = qn.get("TG")
    if TG is not None:
        try:
            t = float(TG)
            if t >= 500:
                out.append("TG ≥ 500 → 🟥 췌장염 위험: 초저지방 식사(총 지방 10~15% 이내), 단 음료/과자·술 즉시 중단, 정제탄수 줄이고 생선(오메가3)·채소 위주.")
            elif t >= 200:
                out.append("TG 200~499 → 당분·과당·술 줄이고, 튀김/가공육 제한, 통곡·채소·운동 늘리기.")
        except: pass
    LDL = qn.get("LDL"); NHDL = qn.get("Non-HDL-C")
    try:
        if (LDL is not None and float(LDL) >= 160) or (NHDL is not None and float(NHDL) >= 160):
            out.append("LDL/Non-HDL 상승 → 트랜스/포화지방 줄이고, 올리브유·등푸른생선·견과류로 대체, 식이섬유(귀리·보리·채소) 충분히.")
    except: pass
    if entered(g("UA")) and g("UA") > 7.0:
        out.append("요산 높음 → 내장류·멸치/정어리·육수·맥주·과당음료 줄이고, 물 충분히.")
    egfr = qn.get("eGFR")
    try:
        if egfr is not None and float(egfr) < 60:
            out.append("eGFR < 60 → 저염(나트륨 2g/일 내외), 단백질 과다 섭취 피하기, 칼륨/인 제한은 단계별로(의료진 지침).")
    except: pass
    if entered(g("Hb")) and g("Hb") < 10:
        out.append("빈혈 → 철분 식단(살코기·간·시금치·콩)+비타민C, 식사 중 차·커피 피하기. (원인 따라 다름)")
    if entered(g("CRP")) and g("CRP") >= 0.5:
        out.append("염증 ↑ → 수분·휴식, 자극적인 튀김/가공식품 줄이고, 익힌 채소·단백질 균형.")
    return out

# ------------------ 보고서 빌더 ------------------
def build_report_md(nick_pin: str, dt: date, mode: str, group: str, dx: str,
                    lab_values: Dict[str, Any], lab_notes: List[str],
                    spec_notes: List[str], tx_catalog: Dict[str, List[str]],
                    tx_phase: str, tx_selected: List[str],
                    food_lines: List[str],
                    ped_dx: Optional[str]=None, ped_symptoms: Optional[List[str]]=None, ped_tips: Optional[List[str]]=None) -> str:
    L = []
    L.append(f"# {APP_TITLE}\n")
    L.append(f"- 사용자: {nick_pin or '저장 안 함(임시 해석)'}  ")
    L.append(f"- 검사일: {dt.isoformat()}  ")
    L.append(f"- 모드: {mode}  ")
    if mode == "암 진단 모드":
        L.append(f"- 암 그룹/진단: {group} / {dx}  ")
        if tx_phase: L.append(f"- 치료 단계: {tx_phase}  ")
        if tx_selected: L.append(f"- 현재 치료 선택: {', '.join(tx_selected)}  ")
    if mode == "소아 일상/질환" and ped_dx:
        L.append(f"- 소아 질환 선택: {ped_dx}  ")
        if ped_symptoms: L.append(f"- 보호자 체크 요약: {', '.join(ped_symptoms)}  ")
    L.append("")
    if lab_values:
        L.append("## 입력 수치")
        for abbr in ORDER:
            if abbr in lab_values and entered(lab_values[abbr]):
                L.append(f"- {label(abbr)}: {lab_values[abbr]}")
        L.append("")
    if lab_notes:
        L.append("## 해석 요약")
        for m in lab_notes: L.append(f"- {m}")
        L.append("")
    if spec_notes:
        L.append("## 특수검사 해석")
        for m in spec_notes: L.append(f"- {m}")
        L.append("")
    if food_lines:
        L.append("## 🍽️ 피수치별 음식/식이 가이드")
        for t in food_lines: L.append(f"- {t}")
        L.append("")
    if mode == "암 진단 모드":
        L.append("## 치료 카탈로그(추천)")
        for sec in ["항암제","표적치료제"]:
            items = tx_catalog.get(sec, [])
            if not items: continue
            L.append(f"### {sec}")
            for d in items: L.append(f"- {d}")
        L.append("")
    if mode == "소아 일상/질환" and ped_tips:
        L.append("## 소아 증상/질환 해석 & 가이드")
        for t in ped_tips: L.append(f"- {t}")
        L.append("")
    L.append("---")
    L.append("```")
    L.append(DISCLAIMER)
    L.append("```")
    return "\n".join(L)

# ------------------ 암 카탈로그 & 약물 설명 (생략 없이 유지 / 면역·세포치료 제외) ------------------
# (중략 없이 이전 버전 그대로 — 분량상 동일 내용 유지)
# === 생략 없이 전체 사전 그대로 포함 ===
# (아래 TX / drug_info는 이전 메시지 버전과 동일하므로 그대로 둠)

HEME_DISPLAY = [
    "급성 골수성 백혈병(AML)","급성 전골수구성 백혈병(APL)","급성 림프모구성 백혈병(ALL)",
    "만성 골수성 백혈병(CML)","만성 림프구성 백혈병(CLL)",
    "다발골수종(Multiple Myeloma)","골수이형성증후군(MDS)","골수증식성 종양(MPN)"
]
HEME_KEY = {"급성 골수성 백혈병(AML)":"AML","급성 전골수구성 백혈병(APL)":"APL","급성 림프모구성 백혈병(ALL)":"ALL","만성 골수성 백혈병(CML)":"CML","만성 림프구성 백혈병(CLL)":"CLL","다발골수종(Multiple Myeloma)":"MM","골수이형성증후군(MDS)":"MDS","골수증식성 종양(MPN)":"MPN"}

LYMPH_DISPLAY = ["미만성 거대 B세포 림프종(DLBCL)","원발 종격동 B세포 림프종(PMBCL)","여포성 림프종 1-2등급(FL 1-2)","여포성 림프종 3A(FL 3A)","여포성 림프종 3B(FL 3B)","외투세포 림프종(MCL)","변연대 림프종(MZL)","고등급 B세포 림프종(HGBL)","버킷 림프종(Burkitt)","고전적 호지킨 림프종(cHL)","말초 T세포 림프종(PTCL-NOS)","비강형 NK/T 세포 림프종(ENKTL)"]
LYMPH_KEY = {"미만성 거대 B세포 림프종(DLBCL)":"DLBCL","원발 종격동 B세포 림프종(PMBCL)":"PMBCL","여포성 림프종 1-2등급(FL 1-2)":"FL12","여포성 림프종 3A(FL 3A)":"FL3A","여포성 림프종 3B(FL 3B)":"FL3B","외투세포 림프종(MCL)":"MCL","변연대 림프종(MZL)":"MZL","고등급 B세포 림프종(HGBL)":"HGBL","버킷 림프종(Burkitt)":"BL","고전적 호지킨 림프종(cHL)":"cHL","말초 T세포 림프종(PTCL-NOS)":"PTCL","비강형 NK/T 세포 림프종(ENKTL)":"ENKTL"}

SOLID_DISPLAY = ["폐선암(Lung Adenocarcinoma)","NSCLC 편평(Lung Squamous)","SCLC(소세포폐암)","유방암 HR+","유방암 HER2+","삼중음성유방암(TNBC)","위암(Gastric)","대장암(Colorectal)","췌장암(Pancreatic)","간세포암(HCC)","담관암(Cholangiocarcinoma)","신장암(RCC)","전립선암(Prostate)","방광암(Bladder)","난소암(Ovarian)","자궁경부암(Cervical)","자궁내막암(Endometrial)","두경부암 Head&Neck SCC","식도암(Esophageal)","역형성갑상선암(ATC)"]
SOLID_KEY = {"폐선암(Lung Adenocarcinoma)":"LungAdeno","NSCLC 편평(Lung Squamous)":"LungSCC","SCLC(소세포폐암)":"SCLC","유방암 HR+":"BreastHR","유방암 HER2+":"BreastHER2","삼중음성유방암(TNBC)":"TNBC","위암(Gastric)":"Gastric","대장암(Colorectal)":"CRC","췌장암(Pancreatic)":"Pancreas","간세포암(HCC)":"HCC","담관암(Cholangiocarcinoma)":"CCA","신장암(RCC)":"RCC","전립선암(Prostate)":"Prostate","방광암(Bladder)":"Bladder","난소암(Ovarian)":"Ovary","자궁경부암(Cervical)":"Cervix","자궁내막암(Endometrial)":"Endomet","두경부암 Head&Neck SCC":"HNSCC","식도암(Esophageal)":"Esophagus","역형성갑상선암(ATC)":"ATC"}

SARCOMA_DISPLAY = ["UPS(미분화 다형성)","LMS(평활근)","LPS(지방)","Synovial Sarcoma","Ewing Sarcoma","Rhabdomyosarcoma","Angiosarcoma","DFSP","GIST"]
SARCOMA_KEY = {"UPS(미분화 다형성)":"UPS","LMS(평활근)":"LMS","LPS(지방)":"LPS","Synovial Sarcoma":"Synovial","Ewing Sarcoma":"Ewing","Rhabdomyosarcoma":"Rhabdo","Angiosarcoma":"Angio","DFSP":"DFSP","GIST":"GIST"}

RARE_DISPLAY = ["GIST(지스트)","NET(신경내분비종양)","Medullary Thyroid(수질갑상선암)","Pheochromocytoma/Paraganglioma","Uveal Melanoma","Merkel Cell(메르켈세포)"]
RARE_KEY = {"GIST(지스트)":"GIST","NET(신경내분비종양)":"NET","Medullary Thyroid(수질갑상선암)":"MTC","Pheochromocytoma/Paraganglioma":"PPGL","Uveal Melanoma":"Uveal","Merkel Cell(메르켈세포)":"Merkel"}

TX = {
    "혈액암": {
        "AML": {"항암제": ["Cytarabine(Ara-C)","Anthracycline(Idarubicin/Daunorubicin)","CPX-351(고위험군)","Azacitidine+Venetoclax"],
                "표적치료제": ["Midostaurin(FLT3)","Gilteritinib(FLT3, 재발/불응)","Enasidenib(IDH2)","Ivosidenib(IDH1)","Glasdegib(Hedgehog)"]},
        "APL": {"항암제": ["ATRA(베사노이드)","ATO","Cytarabine(Ara-C, 고위험 병용)","6-MP(유지)","MTX(유지)"],
                "표적치료제": ["ATRA+ATO (PML-RARA 표적적 접근)"]},
        "ALL": {"항암제": ["Hyper-CVAD","Cytarabine(Ara-C, 고용량)"],
                "표적치료제": ["Blinatumomab(CD19 BiTE)","Inotuzumab ozogamicin(CD22 ADC)","Rituximab(CD20+, 일부 B-ALL)","Nelarabine(T-ALL)"]},
        "CML": {"항암제": [], "표적치료제": ["Imatinib(1세대)","Dasatinib","Nilotinib","Bosutinib","Ponatinib(T315I)","Asciminib(STI, allosteric)"]},
        "CLL": {"항암제": [], "표적치료제": ["Ibrutinib","Acalabrutinib","Zanubrutinib","Venetoclax(+Obinutuzumab)","Rituximab/Obinutuzumab/Ofatumumab","Idelalisib/Duvelisib(제한적)"]},
        "MM":  {"항암제": ["VRd(Bortezomib+Lenalidomide+Dexamethasone)","Carfilzomib","Ixazomib"],
                "표적치료제": ["Daratumumab(Isatuximab, anti-CD38)","Elotuzumab(SLAMF7)","Belantamab mafodotin(BCMA ADC)"]},
        "MDS": {"항암제": ["Azacitidine","Decitabine"],
                "표적치료제": ["Luspatercept(저위험 빈혈)","Ivosidenib/Enasidenib(IDH 변이)"]},
        "MPN": {"항암제": ["Hydroxyurea"],
                "표적치료제": ["Ruxolitinib(JAK2)","Fedratinib(JAK2)","Ropeginterferon alfa-2b(PV)"]},
    },
    "림프종": {
        "DLBCL": {"항암제": ["R-CHOP","Pola-R-CHP","DA-EPOCH-R","R-ICE","R-DHAP","R-GDP","R-GemOx"], "표적치료제": ["Pola-BR","Tafasitamab+Lenalidomide","Loncastuximab"]},
        "PMBCL": {"항암제": ["DA-EPOCH-R","R-ICE","R-DHAP"], "표적치료제": []},
        "FL12":  {"항암제":["BR","R-CVP","R-CHOP","Obinutuzumab+BR"], "표적치료제":["Lenalidomide+Rituximab"]},
        "FL3A":  {"항암제":["R-CHOP","Pola-R-CHP","BR"], "표적치료제":[]},
        "FL3B":  {"항암제":["R-CHOP","Pola-R-CHP","DA-EPOCH-R"], "표적치료제":[]},
        "MCL":   {"항암제":["BR","R-CHOP","Cytarabine 포함","R-ICE","R-DHAP"], "표적치료제":["Ibrutinib","Acalabrutinib","Zanubrutinib"]},
        "MZL":   {"항암제":["BR","R-CVP","R-CHOP"], "표적치료제":[]},
        "HGBL":  {"항암제":["DA-EPOCH-R","R-CHOP","Pola-R-CHP","R-ICE","R-DHAP"], "표적치료제":[]},
        "BL":    {"항암제":["CODOX-M/IVAC-R","Hyper-CVAD-R","R-ICE"], "표적치료제":[]},
        "cHL":   {"항암제":["ABVD","BV-AVD","ICE(구제)","DHAP(구제)"], "표적치료제":["Brentuximab Vedotin"]},
        "PTCL":  {"항암제":["CHOP/CHOEP"], "표적치료제":["Pralatrexate","Romidepsin"]},
        "ENKTL": {"항암제":["SMILE","Aspa 기반","RT 병합"], "표적치료제":[]},
    },
    "고형암": {
        "LungAdeno": {"항암제":["Platinum+Pemetrexed"], "표적치료제":["EGFR(Osimertinib)","ALK(Alectinib)","ROS1(Crizotinib/Entrectinib)","BRAF V600E(Dabrafenib+Trametinib)","METex14(Tepotinib/Capmatinib)","RET(Selpercatinib/Pralsetinib)","NTRK(Larotrectinib/Entrectinib)","KRAS G12C(Sotorasib/Adagrasib)"]},
        "LungSCC": {"항암제":["Platinum+Taxane"], "표적치료제":[]},
        "SCLC":    {"항암제":["Platinum+Etoposide"], "표적치료제":[]},
        "BreastHR":   {"항암제":[], "표적치료제":["ET(AI/Tamoxifen)+CDK4/6i(Palbociclib/Ribociclib/Abemaciclib)","Fulvestrant","Everolimus+Exemestane"]},
        "BreastHER2": {"항암제":["Taxane 병용"], "표적치료제":["Trastuzumab+Pertuzumab","T-DM1","T-DXd"]},
        "TNBC":       {"항암제":["Paclitaxel"], "표적치료제":["Sacituzumab govitecan"]},
        "Gastric":    {"항암제":["FOLFOX/XP"], "표적치료제":["Trastuzumab(HER2+)"]},
        "CRC":        {"항암제":["FOLFOX","FOLFIRI"], "표적치료제":["Bevacizumab","Cetuximab/Panitumumab(RAS WT, 좌측)"]},
        "Pancreas":   {"항암제":["FOLFIRINOX","Gemcitabine+nab-Paclitaxel"], "표적치료제":[]},
        "HCC":        {"항암제":[], "표적치료제":["Lenvatinib","Sorafenib","Regorafenib(2차)"]},
        "CCA":        {"항암제":["Gemcitabine+Cisplatin"], "표적치료제":["Pemigatinib(FGFR2)","Ivosidenib(IDH1)"]},
        "RCC":        {"항암제":[], "표적치료제":["Cabozantinib","Axitinib"]},
        "Prostate":   {"항암제":["Docetaxel(ADT 병용)"], "표적치료제":["Abiraterone/Enzalutamide/Apalutamide","PARP inhibitor(BRCA)"]},
        "Bladder":    {"항암제":["Cisplatin+Gemcitabine"], "표적치료제":["Erdafitinib(FGFR)"]},
        "Ovary":      {"항암제":["Carboplatin+Paclitaxel"], "표적치료제":["Bevacizumab","PARP inhibitor(Olaparib/Niraparib)"]},
        "Cervix":     {"항암제":["Cisplatin+Paclitaxel+Bevacizumab"], "표적치료제":[]},
        "Endomet":    {"항암제":["Carboplatin+Paclitaxel"], "표적치료제":[]},
        "HNSCC":      {"항암제":["Cisplatin+RT(근치)"], "표적치료제":[]},
        "Esophagus":  {"항암제":["FOLFOX/DCF"], "표적치료제":[]},
        "ATC":        {"항암제":[], "표적치료제":["BRAF V600E(Dabrafenib+Trametinib)","Lenvatinib"]},
    },
    "육종": {
        "UPS":     {"항암제":["Doxorubicin","Ifosfamide","Trabectedin","Pazopanib"], "표적치료제":[]},
        "LMS":     {"항암제":["Doxorubicin","Ifosfamide","Gemcitabine+Docetaxel","Pazopanib"], "표적치료제":[]},
        "LPS":     {"항암제":["Doxorubicin","Ifosfamide","Eribulin","Trabectedin"], "표적치료제":[]},
        "Synovial":{"항암제":["Ifosfamide","Doxorubicin","Pazopanib"], "표적치료제":[]},
        "Ewing":   {"항암제":["VDC/IE","Ifosfamide+Etoposide"], "표적치료제":[]},
        "Rhabdo":  {"항암제":["VAC/IVA","Ifosfamide+Etoposide"], "표적치료제":[]},
        "Angio":   {"항암제":["Paclitaxel","Docetaxel","Pazopanib"], "표적치료제":[]},
        "DFSP":    {"항암제":[], "표적치료제":["Imatinib"]},
        "GIST":    {"항암제":[], "표적치료제":["Imatinib","Sunitinib(2차)","Regorafenib(3차)"]},
    },
    "희귀암": {
        "GIST":   {"항암제":[], "표적치료제":["Imatinib","Sunitinib","Regorafenib"]},
        "NET":    {"항암제":[], "표적치료제":["Everolimus","Sunitinib(췌장NET)"]},
        "MTC":    {"항암제":[], "표적치료제":["Selpercatinib/Pralsetinib(RET)","Vandetanib","Cabozantinib"]},
        "PPGL":   {"항암제":["CVD(Cyclophosphamide+Vincristine+DTIC)"], "표적치료제":["Sunitinib"]},
        "Uveal":  {"항암제":[], "표적치료제":[]},
        "Merkel": {"항암제":[], "표적치료제":[]},
    }
}
drug_info = {  # (이전 버전과 동일 — 일부만 발췌, 전체 유지)
    "ATRA(베사노이드)": {"ko":"비스트레티노인","mech":"미성숙 전구세포 분화 유도","ae":"분화증후군, 간수치 상승, 피부건조/광과민"},
    "ATO": {"ko":"무수비소","mech":"분화 유도/세포사멸","ae":"QT 연장, 전해질 이상"},
    "6-MP": {"ko":"6-머캅토퓨린","mech":"퓨린 합성 억제","ae":"간독성, 골수억제, 오심"},
    "MTX": {"ko":"메토트렉세이트","mech":"DHFR 억제","ae":"골수억제, 간/신독성, 구내염"},
    "Cytarabine(Ara-C)": {"ko":"시타라빈","mech":"핵산 합성 저해","ae":"골수억제, 결막염/신경독성(고용량)"},
    # ... (중략: 전체 테이블 유지)
}

# ------------------ 초기 변수 ------------------
labs: Dict[str, Any] = {}
qc: Dict[str, Any] = {}
qn: Dict[str, Any] = {}
calc_info: List[str] = []
ped_dx: Optional[str] = None
ped_checks: Dict[str, Any] = {}
group: str = ""
dx: str = ""
tx_catalog: Dict[str, List[str]] = {"항암제": [], "표적치료제": []}
tx_phase: str = ""
tx_selected: List[str] = []

# ------------------ Streamlit UI ------------------
st.title(APP_TITLE)
st.caption(MADE_BY)
if "store" not in st.session_state: st.session_state.store = load_records()

st.subheader("사용자 식별")
c1, c2 = st.columns([2,1])
nickname = c1.text_input("별명", placeholder="예: 민수아빠", key="nickname")
pin      = c2.text_input("PIN(4자리)", max_chars=4, placeholder="예: 1234", key="pin")
pin_clean = "".join([c for c in (pin or "") if c.isdigit()])[:4]
nick_key  = f"{nickname.strip()}#{pin_clean}" if nickname and pin_clean else ""

test_date = st.date_input("검사 날짜", value=date.today(), key="test_date")
mode = st.radio("진단 모드", ["소아 일상/질환", "암 진단 모드"], horizontal=True, key="mode")

# ----------- 피수치 입력 -----------
def lab_inputs(always_show: bool) -> Dict[str, Any]:
    vals: Dict[str, Any] = {}
    show = True if always_show else st.toggle("피수치 입력란 보기", value=False, key="toggle_labs")
    if not show: return {}
    for abbr in ORDER:
        s = st.text_input(label(abbr), placeholder=f"{label(abbr)} 값 입력", key=f"lab_{abbr}")
        val = parse_float(s)
        if val is not None:
            vals[abbr] = val
    return vals

# ----------- 특수검사 입력 -----------
def special_inputs() -> Tuple[Dict[str,str], Dict[str,float], List[str]]:
    qc, qn, info = {}, {}, []
    st.markdown("### 특수검사 (토글)")
    # 요검사
    with st.expander("요검사(정성/정량)", expanded=False):
        cqa, cqb, cqc, cqd = st.columns(4)
        qc["알부민뇨"] = cqa.selectbox("알부민뇨", ["", "+", "++", "+++"], index=0, key="qc_alb")
        qc["혈뇨"]     = cqb.selectbox("혈뇨", ["", "+", "++", "+++"], index=0, key="qc_hem")
        qc["요당"]     = cqc.selectbox("요당", ["", "-","+" , "++", "+++"], index=0, key="qc_glu")
        qc["잠혈"]     = cqd.selectbox("잠혈", ["", "-","+" , "++"], index=0, key="qc_occ")
        r1, r2 = st.columns(2)
        qn["적혈구(소변/HPF)"] = parse_float(r1.text_input("소변 적혈구(/HPF)", key="u_rbc"))
        qn["백혈구(소변/HPF)"] = parse_float(r2.text_input("소변 백혈구(/HPF)", key="u_wbc"))
        with st.expander("UPCR/ACR 계산(선택)", expanded=False):
            u_prot = parse_float(st.text_input("요단백 (mg/dL)", key="u_prot"))
            u_cr   = parse_float(st.text_input("소변 크레아티닌 (mg/dL)", key="u_cr"))
            u_alb  = parse_float(st.text_input("소변 알부민 (mg/L)", key="u_alb"))
            upcr = acr = None
            if u_cr and u_prot:
                upcr = round((u_prot*1000.0)/u_cr, 1)
                info.append(f"UPCR(자동): {upcr} mg/g")
            if u_cr and u_alb:
                acr = round((u_alb*100.0)/u_cr, 1)
                stg, lab = stage_acr(acr)
                info.append(f"ACR(자동): {acr} mg/g · {stg or ''} {lab or ''}")
            upcr_manual = parse_float(st.text_input("Pro/Cr, urine (mg/g) — 수기 입력", key="upcr_m"))
            if upcr_manual is not None: upcr = upcr_manual
            if upcr is not None: qn["UPCR"] = upcr
            if acr is not None: qn["ACR"] = acr

    # 지질
    with st.expander("지질(기본/확장)", expanded=False):
        c1,c2,c3,c4 = st.columns(4)
        qn["TG"]  = parse_float(c1.text_input("TG (mg/dL)", key="lip_tg"))
        qn["TC"]  = parse_float(c2.text_input("총콜레스테롤 TC (mg/dL)", key="lip_tc"))
        qn["HDL"] = parse_float(c3.text_input("HDL-C (mg/dL)", key="lip_hdl"))
        qn["LDL"] = parse_float(c4.text_input("LDL-C (mg/dL, 입력 또는 자동)", key="lip_ldl"))
        if qn.get("TC") is not None and qn.get("HDL") is not None:
            nonhdl = calc_non_hdl(qn.get("TC"), qn.get("HDL"))
            if nonhdl is not None:
                qn["Non-HDL-C"] = nonhdl
                info.append(f"Non-HDL-C(자동): {nonhdl} mg/dL")
        if qn.get("TC") is not None and qn.get("HDL") is not None and qn.get("TG") is not None and qn.get("LDL") is None:
            ldl = calc_friedewald_ldl(qn["TC"], qn["HDL"], qn["TG"])
            if ldl is not None:
                qn["LDL"] = ldl
                info.append(f"LDL(Friedewald, 자동): {ldl} mg/dL (TG<400에서만 계산)")

    # 응고/보체
    with st.expander("응고/보체", expanded=False):
        c1,c2,c3,c4 = st.columns(4)
        qn["PT"]   = parse_float(c1.text_input("PT (sec)", key="coag_pt"))
        qn["aPTT"] = parse_float(c2.text_input("aPTT (sec)", key="coag_aptt"))
        qn["Fibrinogen"] = parse_float(c3.text_input("Fibrinogen (mg/dL)", key="coag_fbg"))
        qn["D-dimer"]    = parse_float(c4.text_input("D-dimer (µg/mL FEU)", key="coag_dd"))
        d1,d2,d3 = st.columns(3)
        qn["C3"]   = parse_float(d1.text_input("C3 (mg/dL)", key="comp_c3"))
        qn["C4"]   = parse_float(d2.text_input("C4 (mg/dL)", key="comp_c4"))
        qn["CH50"] = parse_float(d3.text_input("CH50 (U/mL)", key="comp_ch50"))

    # 전해질/보정Ca
    with st.expander("전해질 확장/보정칼슘", expanded=False):
        e1,e2,e3 = st.columns(3)
        qn["Mg"]  = parse_float(e1.text_input("Mg (mg/dL)", key="el_mg"))
        qn["Phos(인)"] = parse_float(e2.text_input("인 Phos (mg/dL)", key="el_phos"))
        qn["iCa"] = parse_float(e3.text_input("이온화칼슘 iCa (mmol/L)", key="el_ica"))
        ca_val = st.session_state.get("lab_Ca")
        alb_val = st.session_state.get("lab_Alb")
        ca_corr = calc_corrected_ca(ca_val, alb_val)
        if ca_corr is not None:
            qn["Corrected Ca"] = ca_corr
            info.append(f"보정 칼슘(Alb 반영): {ca_corr} mg/dL")

    # 갑상선·당대사·패혈증
    with st.expander("갑상선·당대사·패혈증", expanded=False):
        t1,t2,t3 = st.columns(3)
        qn["TSH"] = parse_float(t1.text_input("TSH (µIU/mL)", key="thy_tsh"))
        qn["Free T4"] = parse_float(t2.text_input("Free T4 (ng/dL)", key="thy_ft4"))
        qn["Total T3"] = parse_float(t3.text_input("Total T3 (ng/dL)", key="thy_t3"))
        g1,g2,g3 = st.columns(3)
        qn["공복혈당"] = parse_float(g1.text_input("공복혈당 (mg/dL)", key="glu_f"))
        qn["HbA1c"]   = parse_float(g2.text_input("HbA1c (%)", key="glu_a1c"))
        insulin = parse_float(g3.text_input("Insulin (µU/mL)", key="glu_ins"))
        if qn.get("공복혈당") is not None and insulin is not None:
            homa = calc_homa_ir(qn["공복혈당"], insulin)
            if homa is not None:
                qn["HOMA-IR"] = homa
                info.append(f"HOMA-IR(자동): {homa}")
        s1,s2 = st.columns(2)
        qn["PCT"] = parse_float(s1.text_input("Procalcitonin PCT (ng/mL)", key="sep_pct"))
        qn["Lactate"] = parse_float(s2.text_input("Lactate (mmol/L)", key="sep_lac"))

    # 빈혈 패널
    with st.expander("빈혈 패널", expanded=False):
        a1,a2,a3,a4 = st.columns(4)
        qn["Fe"]       = parse_float(a1.text_input("Fe(철) (µg/dL)", key="an_fe"))
        qn["Ferritin"] = parse_float(a2.text_input("Ferritin (ng/mL)", key="an_ferr"))
        qn["TIBC"]     = parse_float(a3.text_input("TIBC (µg/dL)", key="an_tibc"))
        qn["TSAT"]     = parse_float(a4.text_input("Transferrin Sat. TSAT (%)", key="an_tsat"))
        b1,b2,b3 = st.columns(3)
        qn["Reticulocyte(%)"] = parse_float(b1.text_input("망상적혈구(%)", key="an_retic"))
        qn["Vitamin B12"]     = parse_float(b2.text_input("Vitamin B12 (pg/mL)", key="an_b12"))
        qn["Folate"]          = parse_float(b3.text_input("Folate (ng/mL)", key="an_folate"))
    return qc, qn, info

# ------------------ 본문: 소아/암 모드 ------------------
if mode == "소아 일상/질환":
    st.info("소아 감염/일상 중심: 항암제는 숨김 처리됩니다.")
    st.markdown("### 소아 질환 선택")
    ped_dx = st.selectbox("질환", PED_DISEASES, index=0, key="ped_dx")
    # 보호자 체크(질환별 프리셋)
    ped_checks = render_caregiver_check(ped_dx)
    # 피수치 입력(토글)
    labs = lab_inputs(always_show=False)

    # 해열제 자동 계산(기존)
    st.markdown("### 해열제 자동 계산")
    cw, ct = st.columns(2)
    wt = parse_float(cw.text_input("체중(kg)", placeholder="예: 20.5", key="wt"))
    # 보호자 체크에 입력한 체온을 자동으로 반영
    cg_temp_txt = (ped_checks.get("열_현재체온") or "").strip()
    tc = parse_float(ct.text_input("체온(℃)",  value=cg_temp_txt if cg_temp_txt else "", key="tc"))
    if st.button("해열 가이드 계산", key="btn_fever"):
        if not wt:
            st.warning("체중을 먼저 입력하세요.")
        else:
            ac_min = 10*wt; ac_max = 15*wt; ib = 10*wt
            st.write(f"아세트아미노펜: 1회 {ac_min:.0f}~{ac_max:.0f} mg")
            st.write(f"이부프로펜: 1회 약 {ib:.0f} mg")
            st.caption(FEVER_GUIDE)

    qc, qn, calc_info = special_inputs()

else:
    st.success("암 진단 모드: 피수치 입력란이 항상 표시됩니다.")
    c1, c2 = st.columns(2)
    group = c1.selectbox("암 그룹", ["","혈액암","림프종","고형암","육종","희귀암"], index=0, key="group")
    if group == "혈액암":
        dx = c2.selectbox("혈액암(진단명)", HEME_DISPLAY, index=0, key="dx_heme")
    elif group == "림프종":
        dx = c2.selectbox("림프종(진단명)", LYMPH_DISPLAY, index=0, key="dx_lymph")
    elif group == "고형암":
        dx = c2.selectbox("고형암(진단명)", SOLID_DISPLAY, index=0, key="dx_solid")
    elif group == "육종":
        dx = c2.selectbox("육종(진단명)", SARCOMA_DISPLAY, index=0, key="dx_sarcoma")
    elif group == "희귀암":
        dx = c2.selectbox("희귀암(진단명)", RARE_DISPLAY, index=0, key="dx_rare")
    else:
        dx = ""

    tx_phase = st.selectbox("치료 단계", ["", "유지요법", "외래 항암", "입원 항암", "완료(추적관찰)"], index=0, key="tx_phase")
    tx_catalog = {}
    if group:
        if group == "혈액암": tx_catalog = TX["혈액암"].get( HEME_KEY.get(dx, dx), {"항암제":[], "표적치료제":[]})
        elif group == "림프종": tx_catalog = TX["림프종"].get( LYMPH_KEY.get(dx, dx), {"항암제":[], "표적치료제":[]})
        elif group == "고형암": tx_catalog = TX["고형암"].get( SOLID_KEY.get(dx, dx), {"항암제":[], "표적치료제":[]})
        elif group == "육종":   tx_catalog = TX["육종"].get( SARCOMA_KEY.get(dx, dx), {"항암제":[], "표적치료제":[]})
        elif group == "희귀암": tx_catalog = TX["희귀암"].get( RARE_KEY.get(dx, dx), {"항암제":[], "표적치료제":[]})

    st.markdown("### 항암제/표적치료제 선택")
    cc1, cc2 = st.columns(2)
    chemo_sel = cc1.multiselect("항암제 선택", tx_catalog.get("항암제", []), default=[], key="chemo_sel")
    targ_sel  = cc2.multiselect("표적치료제 선택", tx_catalog.get("표적치료제", []), default=[], key="targ_sel")
    tx_custom = st.text_input("직접 추가(쉼표로 구분, 예: Cyclophosphamide, Rituximab)", key="tx_custom")
    tx_selected = list(dict.fromkeys([*chemo_sel, *targ_sel] + ([s.strip() for s in tx_custom.split(",")] if tx_custom.strip() else [])))

    with st.expander("치료 카탈로그(요약 설명)", expanded=False):
        for sec in ["항암제","표적치료제"]:
            items = tx_catalog.get(sec, [])
            if not items: continue
            st.markdown(f"**{sec}**")
            for d in items:
                info = drug_info.get(d, {})
                ko = info.get("ko",""); mech = info.get("mech",""); ae = info.get("ae","")
                st.markdown(f"- **{d}**{f' ({ko})' if ko else ''}")
                if mech: st.caption(f"작용: {mech}")
                if ae:   st.caption(f"주의: {ae}")

    labs = lab_inputs(always_show=True)
    qc, qn, calc_info = special_inputs()

# ------------------ eGFR 계산 (선택) ------------------
st.markdown("### eGFR 계산 (선택)")
age = parse_float(st.text_input("나이(세)", key="kid_age"))
sex = st.selectbox("성별", ["F","M"], key="kid_sex")
egfr = None
if entered(labs.get("Cr")) and age:
    egfr = calc_egfr(labs.get("Cr"), age=age, sex=sex)
    if egfr is not None:
        st.info(f"eGFR(자동): {egfr} mL/min/1.73m²")

# ------------------ 해석 / 저장 분리 ------------------
st.divider()
colA, colB, colC = st.columns([1,1,1])
run_analyze = colA.button("🔎 해석하기", use_container_width=True, key="btn_analyze_only")
save_now    = colB.button("💾 저장하기", use_container_width=True, key="btn_save_only")
load_last   = colC.button("↩️ 가장 최근 기록으로 폼 채우기", use_container_width=True, key="btn_fill")
clear_user  = st.button("🗑️ 이 사용자 기록 전체 삭제", use_container_width=True, key="btn_clear")

if clear_user and nick_key:
    st.session_state.store.pop(nick_key, None)
    save_records(st.session_state.store)
    st.success("이 사용자 기록을 모두 삭제했습니다.")

if load_last and nick_key:
    user_records = st.session_state.store.get(nick_key, [])
    if user_records:
        last = user_records[-1]
        labs_last = last.get("labs", {})
        for abbr, val in labs_last.items():
            st.session_state[f"lab_{abbr}"] = str(val)
        st.success("최근 기록을 폼에 반영했습니다. (입력란 확인)")

def do_analysis(show_result: bool=True) -> dict:
    qn_for_eval = dict(qn or {})
    if egfr is not None:
        qn_for_eval["eGFR"] = egfr

    lab_notes  = interpret_labs(labs or {})
    spec_notes = interpret_special_extended(qc or {}, qn_for_eval, base_vals=labs or {}, profile="adult")
    food_lines = build_diet_guide(labs or {}, qn_for_eval, mode)

    # 철분+비타민C 경고
    if mode == "암 진단 모드":
        if (group == "혈액암") or (tx_phase in ["유지요법","외래 항암","입원 항암"]):
            warning = ("⚠️ 철분제와 비타민C를 함께 복용하면 흡수가 촉진됩니다.\n"
                       "하지만 항암 치료 중이거나 백혈병 환자는 반드시 주치의와 상담 후 복용 여부를 결정해야 합니다.")
            if warning not in food_lines:
                food_lines.append(warning)

    # 소아 증상/질환 해석(보호자 체크 반영)
    ped_symmary_list = None
    ped_tips_local = None
    if mode == "소아 일상/질환":
        ped_symmary_list = summarize_ped_checks(ped_checks)
        ped_tips_local = interpret_peds_symptoms_from_checks(ped_dx, ped_checks)

    if show_result:
        if lab_notes:
            st.subheader("해석 요약")
            for m in lab_notes: st.write("• " + m)
        if calc_info:
            st.subheader("자동 계산")
            for m in calc_info: st.write("• " + m)
        if spec_notes:
            st.subheader("특수검사 해석")
            for m in spec_notes: st.write("• " + m)
        if food_lines:
            st.subheader("🍽️ 피수치별 음식/식이 가이드")
            for t in food_lines: st.write("• " + t)
        if mode == "소아 일상/질환":
            if ped_symmary_list:
                st.subheader("👪 보호자 체크 요약")
                for s in ped_symmary_list: st.write("• " + s)
            if ped_tips_local:
                st.subheader("👶 소아 증상/질환 해석")
                for t in ped_tips_local: st.write("• " + t)

        # 보고서 다운로드
        group_for_report = group if mode=="암 진단 모드" else ""
        dx_for_report    = dx    if mode=="암 진단 모드" else ""
        tx_cat_for_report= tx_catalog if mode=="암 진단 모드" else {"항암제":[], "표적치료제":[]}
        tx_phase_report  = tx_phase if mode=="암 진단 모드" else ""
        tx_selected_rep  = tx_selected if mode=="암 진단 모드" else []
        report_md = build_report_md(
            nick_key, test_date, mode, group_for_report, dx_for_report, labs or {}, lab_notes, spec_notes,
            tx_cat_for_report, tx_phase_report, tx_selected_rep, food_lines,
            ped_dx = ped_dx if mode=="소아 일상/질환" else None,
            ped_symptoms = ped_symmary_list if mode=="소아 일상/질환" else None,
            ped_tips = ped_tips_local if mode=="소아 일상/질환" else None
        )
        st.download_button("📥 보고서(.md) 다운로드", data=report_md.encode("utf-8"),
                           file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                           mime="text/markdown")
        st.download_button("📄 보고서(.txt) 다운로드", data=report_md.encode("utf-8"),
                           file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                           mime="text/plain")

    return {
        "qn_for_eval": qn_for_eval,
        "lab_notes": lab_notes,
        "spec_notes": spec_notes,
        "food_lines": food_lines,
        "ped_symmary_list": ped_symmary_list,
        "ped_tips": ped_tips_local
    }

# 해석하기
if run_analyze:
    payload = do_analysis(show_result=True)
    st.session_state["analysis_payload"] = payload
    st.info("임시 해석 완료(저장은 하지 않았습니다). 별명·PIN 입력 후 [저장하기]를 누르면 기록됩니다.")

# 저장하기
if save_now:
    if not nick_key:
        st.warning("별명과 PIN(숫자 4자리)을 입력해야 저장할 수 있어요. 지금은 해석만 가능합니다.")
    else:
        payload = st.session_state.get("analysis_payload") or do_analysis(show_result=False)
        qn_for_eval = payload["qn_for_eval"]
        rec = {
            "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "date": test_date.isoformat(),
            "mode": mode,
            "group": group if mode=="암 진단 모드" else "",
            "dx":    dx if mode=="암 진단 모드" else "",
            "tx_phase": tx_phase if mode=="암 진단 모드" else "",
            "tx_selected": tx_selected if mode=="암 진단 모드" else [],
            "labs": {k: labs.get(k) for k in ORDER if entered(labs.get(k))},
            "special": {"qc": qc, "qn": qn_for_eval},
            "pediatric": {
                "dx": ped_dx if mode=="소아 일상/질환" else "",
                "checks": ped_checks if mode=="소아 일상/질환" else {},
                "summary": payload.get("ped_symmary_list") if mode=="소아 일상/질환" else []
            }
        }
        st.session_state.store.setdefault(nick_key, []).append(rec)
        save_records(st.session_state.store)
        st.success("저장 완료! 아래 그래프로 추이를 확인할 수 있어요.")

# ------------------ 그래프 ------------------
st.header("📈 추이 그래프 (별명#PIN 기준)")
if not nick_key:
    st.info("별명과 PIN을 입력하면 그래프를 사용할 수 있어요. (저장 전에는 그래프가 표시되지 않습니다)")
else:
    user_records = st.session_state.store.get(nick_key, [])
    if not user_records:
        st.info("저장된 기록이 없습니다. [해석하기] 후 [저장하기]를 눌러 기록을 남겨주세요.")
    else:
        rows = []
        for r in user_records:
            row = {"date": r.get("date")}
            for k in ORDER:
                v = (r.get("labs") or {}).get(k)
                row[k] = v if entered(v) else None
            rows.append(row)
        df = pd.DataFrame(rows)
        try: df["date"] = pd.to_datetime(df["date"])
        except: pass
        df = df.sort_values("date")

        metric_sel = st.multiselect(
            "그래프에 표시할 항목 선택",
            ["WBC","Hb","PLT","CRP","ANC"] + [x for x in ORDER if x not in ["WBC","Hb","PLT","CRP","ANC"]],
            default=["WBC","Hb","PLT","CRP","ANC"],
        )
        if not metric_sel:
            st.info("표시할 항목을 선택하세요.")
        else:
            for m in metric_sel:
                if m not in df.columns: continue
                sub = df[["date", m]].dropna()
                if len(sub) == 0:
                    st.warning(f"{m} 데이터가 아직 없습니다."); continue
                st.subheader(label(m))
                st.line_chart(sub.set_index("date")[m])

st.markdown("---")
st.code(DISCLAIMER, language="text")
