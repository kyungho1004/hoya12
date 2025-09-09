# -*- coding: utf-8 -*-
# BloodMap — 소아 질환(크룹/모세기관지염) + 소아 증상 해석 + 피수치별 식이가이드 자동 생성
# 면역/세포치료 제외. 소아 해열제: 1회 권장량만 표기. 별명+PIN 저장/그래프, 특수검사 확장 유지.

import os, json
from datetime import datetime, date
from typing import Dict, Any, List, Optional, Tuple
import streamlit as st
import pandas as pd

APP_TITLE  = "피수치 가이드 (BloodMap) — 소아/암 통합"
PAGE_TITLE = "BloodMap"
MADE_BY    = "제작: Hoya/GPT"
DISCLAIMER = (
    "본 수치는 참고용이며, 해석 결과는 개발자와 무관합니다.  "
    "약 변경, 복용 중단 등은 반드시 주치의와 상의 후 결정하시기 바랍니다.  "
    "이 앱은 개인정보를 수집하지 않으며, 어떠한 개인정보 입력도 요구하지 않습니다."
)
FEVER_GUIDE = "38.0~38.5℃: 해열제/경과관찰 · 38.5~39.0℃: 해열제+병원 연락 고려 · 39.0℃ 이상: 즉시 병원"
RECORDS_PATH = "records.json"

ORDER = ["WBC","Hb","PLT","ANC","Ca","P","Na","K","Alb","Glu","TP",
         "AST","ALT","LDH","CRP","Cr","UA","TB","BUN","BNP"]

KR = {
    "WBC":"백혈구","Hb":"혈색소","PLT":"혈소판","ANC":"호중구",
    "Ca":"칼슘","P":"인","Na":"소디움","K":"포타슘",
    "Alb":"알부민","Glu":"혈당","TP":"총단백",
    "AST":"AST(간 효소)","ALT":"ALT(간세포)","LDH":"LDH",
    "CRP":"CRP(염증)","Cr":"크레아티닌","UA":"요산",
    "TB":"총빌리루빈","BUN":"BUN","BNP":"BNP",
}
def label(abbr: str) -> str:
    return f"{abbr} ({KR.get(abbr, abbr)})"

# ---------- 저장/불러오기 ----------
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

# ---------- 유틸/계산 ----------
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

# ---------- 해석 ----------
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

# ---------- 특수검사 해석(확장) ----------
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
            if t >= 160: out.append(f"TG {t} (소아 기준) 높음")
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

# ---------- 소아 질환/증상 ----------
PED_DISEASES = [
    "일반 감기(상기도감염)","RSV","Adenovirus(아데노)","Parainfluenza(파라인플루엔자)","Influenza(독감)",
    "COVID-19","Rotavirus(로타)","Norovirus(노로)","수족구(HFMD)","Mycoplasma(마이코플라즈마)",
    "중이염 의심","결막염 의심","크룹(Croup)","모세기관지염(Bronchiolitis)","폐렴 의심"
]
PED_SYMPTOMS = [
    "발열","기침","콧물","코막힘","인후통",
    "눈곱/결막충혈","구토","설사","복통","발진",
    "쌕쌕거림/호흡곤란","빠른호흡/흉곽함몰","거친쉰목소리/개짖는기침",
    "탈수 의심(소변↓/입마름)","음수량 감소","야간기침"
]

def interpret_peds_symptoms(sx: List[str], temp: Optional[float]) -> List[str]:
    out: List[str] = []
    if "거친쉰목소리/개짖는기침" in sx:
        out.append("크룹 양상: 찬 공기 잠시 쐬고 진정. 스트라이더/호흡곤란 시 응급실(스테로이드/네불 가능).")
    if "쌕쌕거림/호흡곤란" in sx or "빠른호흡/흉곽함몰" in sx:
        out.append("하기도 폐색/모세기관지염 가능: 숨 가쁘면 즉시 진료. 코막힘 완화·수분공급.")
    if "야간기침" in sx:
        out.append("야간기침: 크룹/아데노/알레르기/기침천식 증후군 감별 필요.")
    if "눈곱/결막충혈" in sx:
        out.append("결막염 소견: 수건 공동사용 금지, 분비물 심하면 항생제 점안제 평가.")
    if ("구토" in sx or "설사" in sx) and "탈수 의심(소변↓/입마름)" in sx:
        out.append("구토·설사 + 탈수: ORS 소량씩 자주, 지속 시 수액 고려.")
    if "음수량 감소" in sx:
        out.append("수분섭취 감소: 젤리/미온수/전해질 음료 소량씩 권장.")
    if temp is not None:
        if temp >= 39: out.append("고열 지속 시 세균성 감염·폐렴 감별 필요.")
        elif temp >= 38: out.append("38도 이상: 해열제 1회 권장량 사용 후 경과 관찰.")
    return out

def build_ped_tips(dx: str, sx: List[str], temp: Optional[float]) -> List[str]:
    tips = interpret_peds_symptoms(sx, temp)
    if dx in ["RSV","모세기관지염(Bronchiolitis)"]:
        tips.append("모세기관지염: 코흡인/가습/수분. 호흡수↑·함몰 시 즉시 병원.")
    if dx in ["Parainfluenza(파라인플루엔자)","크룹(Croup)"]:
        tips.append("크룹: 울음 달래고 찬 공기. 호흡곤란·청색증 시 응급실.")
    if dx in ["Influenza(독감)"]:
        tips.append("독감: 48시간 내 진료 시 항바이러스제 고려(연령·위험군).")
    if dx in ["Rotavirus(로타)","Norovirus(노로)"]:
        tips.append("위장관염: ORS 소량씩, 기름진 음식/우유 일시 제한.")
    if dx in ["중이염 의심"]:
        tips.append("귀통증·야간발열 반복 시 진료. 진통제는 지시대로.")
    if dx in ["폐렴 의심"]:
        tips.append("호흡수 상승/함몰/식욕저하 심하면 영상·혈액검사 평가.")
    if dx in ["결막염 의심"]:
        tips.append("결막염: 손 위생 철저, 등원은 증상/전파력 고려해 상담.")
    if dx in ["일반 감기(상기도감염)","Adenovirus(아데노)","Mycoplasma(마이코플라즈마)","COVID-19"]:
        tips.append("호흡기 감염 공통: 손 위생, 실내 환기, 수분/휴식.")
    return tips

# ---------- 피수치별 식이가이드 ----------
def build_diet_guide(labs: Dict[str, Any], qn: Dict[str, Any], mode: str) -> List[str]:
    out: List[str] = []
    g = lambda k: labs.get(k)

    # 백혈구/ANC
    if entered(g("ANC")) and g("ANC") < 500:
        out.append("ANC < 500 → 익힌 음식만(회/덜익은 고기·달걀·생채소/새싹 금지), 과일은 껍질 제거·흐르는 물 세척, 남은 음식 2시간 넘기지 않기, 생수는 밀봉 제품.")
    elif entered(g("ANC")) and g("ANC") < 1000:
        out.append("ANC 500~1000 → 외식·뷔페·길거리 음식 주의, 가열 충분히, 손 위생 철저.")

    # 혈소판
    if entered(g("PLT")) and g("PLT") < 50:
        out.append("혈소판 < 50 → 딱딱·날카로운 음식(뼈있는 생선, 질긴 육포, 딱딱한 견과류) 조심, 빨대·가글 강하게 사용 금지, 술 금지. (약물: 아스피린/이부프로펜류는 의료진과 상의)")

    # 간수치
    if entered(g("AST")) and g("AST") >= 50 or (entered(g("ALT")) and g("ALT") >= 55):
        out.append("간수치 상승 → 술/허브보충제 중단, 기름진·튀김 줄이기, 아세트아미노펜 과량 금지, 수분·균형식. 장기 지속 시 의사 상담.")

    # 알부민
    if entered(g("Alb")) and g("Alb") < 3.5:
        out.append("알부민 낮음 → 단백질 보강(살코기·생선·달걀·두부/콩·유제품), 소량씩 자주 먹기. 부종·신장질환 있으면 의료진 권고에 따름.")

    # 지질
    TG = qn.get("TG")
    if TG is not None:
        try:
            t = float(TG)
            if t >= 500:
                out.append("TG ≥ 500 → 🟥 췌장염 위험: 초저지방 식사(총 지방 10~15% 이내), 단 음료/과자·술 즉시 중단, 정제탄수 줄이고 생선(오메가3)·채소 위주.")
            elif t >= 200:
                out.append("TG 200~499 → 당분·과당·술 줄이고, 튀김/가공육 제한, 통곡/채소·운동 늘리기.")
        except:
            pass
    LDL = qn.get("LDL"); NHDL = qn.get("Non-HDL-C")
    try:
        if LDL is not None and float(LDL) >= 160 or (NHDL is not None and float(NHDL) >= 160):
            out.append("LDL/Non-HDL 상승 → 트랜스지방·포화지방 줄이고, 올리브유/등푸른생선/견과류로 대체, 식이섬유(귀리·보리·채소) 충분히.")
    except:
        pass

    # 요산
    if entered(g("UA")) and g("UA") > 7.0:
        out.append("요산 높음 → 내장류·멸치/정어리·육수/맥주·과당음료 줄이고, 물 충분히 섭취.")

    # 신장/나트륨·칼륨
    egfr = qn.get("eGFR")
    try:
        if egfr is not None and float(egfr) < 60:
            out.append("eGFR < 60 → 저염(나트륨 2g/일 내외), 단백질 과다 섭취 피하기, 칼륨/인 많은 음식은 단계에 따라 제한(의료진 지침 우선).")
    except:
        pass

    # 빈혈
    if entered(g("Hb")) and g("Hb") < 10:
        out.append("빈혈 → 풍부한 식단(살코기·간·시금치·콩),식사 중 차/커피는 피하기. (원인에 따라 달라질 수 있음)")

    # CRP 높음(염증)
    if entered(g("CRP")) and g("CRP") >= 0.5:
        out.append("염증 ↑ → 수분·휴식, 자극적인 튀김/가공식품 줄이고, 익힌 채소·단백질 균형 있게.")

    return out

# ---------- 보고서(Markdown) ----------
def build_report_md(nick_pin: str, dt: date, mode: str, group: str, dx: str,
                    lab_values: Dict[str, Any], lab_notes: List[str],
                    spec_notes: List[str], tx_catalog: Dict[str, List[str]],
                    tx_phase: str, tx_selected: List[str],
                    food_lines: List[str],
                    ped_dx: Optional[str]=None, ped_symptoms: Optional[List[str]]=None, ped_tips: Optional[List[str]]=None) -> str:
    L = []
    L.append(f"# {APP_TITLE}\n")
    L.append(f"- 사용자: {nick_pin}  ")
    L.append(f"- 검사일: {dt.isoformat()}  ")
    L.append(f"- 모드: {mode}  ")
    if mode == "암 진단 모드":
        L.append(f"- 암 그룹/진단: {group} / {dx}  ")
        if tx_phase: L.append(f"- 치료 단계: {tx_phase}  ")
        if tx_selected: L.append(f"- 현재 치료 선택: {', '.join(tx_selected)}  ")
    if mode == "소아 일상/질환" and ped_dx:
        L.append(f"- 소아 질환 선택: {ped_dx}  ")
        if ped_symptoms: L.append(f"- 증상: {', '.join(ped_symptoms)}  ")
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

# ---------- 암 카탈로그 (생략: 이전과 동일) ----------
# ... [여기부터는 이전에 드린 암종/림프종/고형암/육종/희귀암 TX 딕셔너리와 drug_info 그대로 사용하세요]
# 공간을 위해 코드 블록에서는 생략했지만, 현재 사용 중이던 그대로 붙여넣으면 됩니다.
# === 실제 사용시엔 아래 줄을 지우고, 이전 버전의 TX/drug_info 블록을 그대로 유지하세요. ===
from math import inf
TX, drug_info = {}, {}

# ---------- Streamlit UI ----------
st.set_page_config(page_title=PAGE_TITLE, layout="centered")
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

# --- 특수검사 입력 (이전과 동일) ---
# ... [생략 없이 기존 코드 사용 가능. LDL/Non-HDL 자동계산 포함]
# === 실제 사용시엔 기존 special_inputs() 함수를 그대로 넣어주세요. ===
def special_inputs():
    qc, qn, info = {}, {}, []
    st.markdown("### 특수검사 (토글)")
    with st.expander("지질(기본/확장)", expanded=False):
        c1,c2,c3 = st.columns(3)
        qn["TG"]  = parse_float(c1.text_input("TG (mg/dL)", key="lip_tg"))
        qn["TC"]  = parse_float(c2.text_input("총콜레스테롤 TC (mg/dL)", key="lip_tc"))
        qn["HDL"] = parse_float(c3.text_input("HDL-C (mg/dL)", key="lip_hdl"))
        if qn.get("TC") is not None and qn.get("HDL") is not None:
            nonhdl = calc_non_hdl(qn.get("TC"), qn.get("HDL"))
            if nonhdl is not None:
                qn["Non-HDL-C"] = nonhdl
                info.append(f"Non-HDL-C(자동): {nonhdl} mg/dL")
        if qn.get("TC") is not None and qn.get("HDL") is not None and qn.get("TG") is not None:
            ldl = calc_friedewald_ldl(qn["TC"], qn["HDL"], qn["TG"])
            if ldl is not None:
                qn["LDL"] = ldl
                info.append(f"LDL(Friedewald, 자동): {ldl} mg/dL (TG<400에서만 계산)")
    return qc, qn, info

# --- 본문 ---
if mode == "소아 일상/질환":
    st.info("소아 감염/일상 중심: 항암제는 숨김 처리됩니다.")
    st.markdown("### 소아 질환 선택")
    ped_dx = st.selectbox("질환", PED_DISEASES, index=0, key="ped_dx")
    st.markdown("### 증상 체크")
    ped_sx = st.multiselect("해당되는 증상을 모두 선택하세요", PED_SYMPTOMS, default=[], key="ped_sx")
    ped_note = st.text_area("증상 메모(선택)", placeholder="예: 새벽에 기침 심함, 해열제 먹은 시간 등", key="ped_note")

    labs = lab_inputs(always_show=False)

    st.markdown("### 해열제 자동 계산")
    cw, ct = st.columns(2)
    wt = parse_float(cw.text_input("체중(kg)", placeholder="예: 20.5", key="wt"))
    tc = parse_float(ct.text_input("체온(℃)",  placeholder="예: 38.2", key="tc"))
    if st.button("해열 가이드 계산", key="btn_fever"):
        if not wt:
            st.warning("체중을 먼저 입력하세요.")
        else:
            ac_min = 10*wt; ac_max = 15*wt; ib = 10*wt
            st.write(f"아세트아미노펜: 1회 {ac_min:.0f}~{ac_max:.0f} mg")
            st.write(f"이부프로펜: 1회 약 {ib:.0f} mg")
            st.caption(FEVER_GUIDE)
    ped_tips = build_ped_tips(ped_dx, ped_sx, tc)
    qc, qn, calc_info = special_inputs()

else:
    st.success("암 진단 모드: 피수치 입력란이 항상 표시됩니다.")
    labs = lab_inputs(always_show=True)
    qc, qn, calc_info = special_inputs()
    ped_dx = ped_sx = None

# eGFR 계산(선택)
st.markdown("### eGFR 계산 (선택)")
age = parse_float(st.text_input("나이(세)", key="kid_age"))
sex = st.selectbox("성별", ["F","M"], key="kid_sex")
egfr = None
if entered(labs.get("Cr")) and age:
    egfr = calc_egfr(labs.get("Cr"), age=age, sex=sex)
    if egfr is not None:
        st.info(f"eGFR(자동): {egfr} mL/min/1.73m²")

# 해석/저장
st.divider()
colA, colB, colC = st.columns([1,1,1])
run_analyze = colA.button("🔎 해석하기 & 저장", use_container_width=True, key="btn_analyze")
clear_user  = colB.button("🗑️ 이 사용자 기록 전체 삭제", use_container_width=True, key="btn_clear")
load_last   = colC.button("↩️ 가장 최근 기록으로 폼 채우기", use_container_width=True, key="btn_fill")

pin_clean = "".join([c for c in (pin or "") if c.isdigit()])[:4]
nick_key  = f"{nickname.strip()}#{pin_clean}" if nickname and pin_clean else ""

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

if run_analyze:
    if not nick_key:
        st.warning("별명과 PIN(숫자 4자리)을 먼저 입력해주세요.")
    else:
        qn_for_eval = {**qn, **({"eGFR": egfr} if egfr is not None else {})}
        lab_notes  = interpret_labs(labs)
        spec_notes = interpret_special_extended(qc, qn_for_eval, base_vals=labs, profile="adult")
        food_lines = build_diet_guide(labs, qn_for_eval, mode)

        if lab_notes:
            st.subheader("해석 요약")
            for m in lab_notes:
                st.write("• " + m)
        if calc_info:
            st.subheader("자동 계산")
            for m in calc_info:
                st.write("• " + m)
        if spec_notes:
            st.subheader("특수검사 해석")
            for m in spec_notes:
                st.write("• " + m)
        if food_lines:
            st.subheader("🍽️ 피수치별 음식/식이 가이드")
            for t in food_lines:
                st.write("• " + t)
        if mode == "소아 일상/질환" and ped_dx:
            st.subheader("👶 소아 증상/질환 해석")
            for t in ped_tips:
                st.write("• " + t)

        report_md = build_report_md(
            nick_key, test_date, mode,
            group="", dx="",  # (간단 버전: 현재 답변에선 암 파트 UI 생략)
            lab_values=labs, lab_notes=lab_notes, spec_notes=spec_notes,
            tx_catalog={}, tx_phase="", tx_selected=[],
            food_lines=food_lines,
            ped_dx=ped_dx if mode=="소아 일상/질환" else None,
            ped_symptoms=ped_sx if mode=="소아 일상/질환" else None,
            ped_tips=ped_tips if mode=="소아 일상/질환" else None
        )
        st.download_button("📥 보고서(.md) 다운로드", data=report_md.encode("utf-8"),
                           file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                           mime="text/markdown")

        rec = {
            "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "date": test_date.isoformat(),
            "mode": mode,
            "labs": {k: labs.get(k) for k in ORDER if entered(labs.get(k))},
            "special": {"qc": qc, "qn": qn_for_eval},
            "pediatric": {"dx": ped_dx if mode=="소아 일상/질환" else "", "symptoms": ped_sx if mode=="소아 일상/질환" else []}
        }
        st.session_state.store.setdefault(nick_key, []).append(rec)
        save_records(st.session_state.store)
        st.success("저장 완료! 아래 그래프로 추이를 확인하세요.")

# 그래프
st.header("📈 추이 그래프 (별명#PIN 기준)")
if not nick_key:
    st.info("별명과 PIN을 입력하면 그래프를 사용할 수 있어요.")
else:
    user_records = st.session_state.store.get(nick_key, [])
    if not user_records:
        st.info("저장된 기록이 없습니다. '해석하기 & 저장'을 먼저 눌러주세요.")
    else:
        rows = []
        for r in user_records:
            row = {"date": r.get("date")}
            for k in ORDER:
                v = (r.get("labs") or {}).get(k)
                row[k] = v if entered(v) else None
            rows.append(row)
        df = pd.DataFrame(rows)
        try:
            df["date"] = pd.to_datetime(df["date"])
        except Exception:
            pass
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

