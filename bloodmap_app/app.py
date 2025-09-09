# -*- coding: utf-8 -*-
# BloodMap — 통합판 (카테고리 풀셋 + 특수검사 확장 + 항암제 선택 + 저장/그래프 + 보고서)
# 면역/세포 치료 제외. 소아 해열제: 1회 권장량만 표기(일일 최대횟수 안내 제거).

import os, json
from datetime import datetime, date
from typing import Dict, Any, List
import streamlit as st
import pandas as pd

APP_TITLE  = "피수치 가이드 (BloodMap) — 통합 특수검사 확장판"
PAGE_TITLE = "BloodMap"
MADE_BY    = "제작: Hoya/GPT"
CAFE_LINK  = "https://cafe.naver.com/bloodmap"
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

# -----------------------------
# 저장/불러오기
# -----------------------------
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

# -----------------------------
# 유틸/계산
# -----------------------------
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

# -----------------------------
# 기본 해석
# -----------------------------
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

# -----------------------------
# 특수검사 해석(확장)
# -----------------------------
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

# -----------------------------
# 음식 가이드
# -----------------------------
def build_food_guide(labs: Dict[str, Any]) -> List[str]:
    out = []
    v = labs or {}
    def val(k):
        try:
            return float(v.get(k)) if v.get(k) is not None else None
        except:
            return None
    if (alb := val("Alb")) is not None and alb < 3.5:
        out.append("알부민 낮음: 달걀, 연두부, 흰살생선, 닭가슴살, 귀리죽")
    if (k := val("K")) is not None and k < 3.5:
        out.append("칼륨 낮음: 바나나, 감자, 호박죽, 고구마, 오렌지")
    if (hb := val("Hb")) is not None and hb < 10.0:
        out.append("Hb 낮음: 소고기, 시금치, 두부, 달걀 노른자, 렌틸콩 · 철분/비타민C 병용은 주치의와 상의")
    if (na := val("Na")) is not None and na < 135:
        out.append("나트륨 낮음: 전해질 음료, 미역국, 바나나, 오트밀죽, 삶은 감자")
    if (ca := val("Ca")) is not None and ca < 8.5:
        out.append("칼슘 낮음: 연어 통조림, 두부, 케일, 브로콜리(참깨 제외)")
    if (anc := val("ANC")) is not None:
        if anc < 500:
            out.append("ANC 매우 낮음: 생채소 금지 · 모든 음식 익혀 섭취 · 남은 음식 2시간 이후 비권장 · 껍질 과일은 상담")
        elif anc < 1000:
            out.append("ANC 낮음: 위생 철저 · 외식/뷔페 피하기 · 충분히 가열 조리")
    return out

# -----------------------------
# 보고서(Markdown)
# -----------------------------
def build_report_md(nick_pin: str, dt: date, mode: str, group: str, dx: str,
                    lab_values: Dict[str, Any], lab_notes: List[str],
                    spec_notes: List[str], tx_catalog: Dict[str, List[str]],
                    tx_phase: str, tx_selected: List[str], food_lines: List[str]) -> str:
    L = []
    L.append(f"# {APP_TITLE}\n")
    L.append(f"- 사용자: {nick_pin}  ")
    L.append(f"- 검사일: {dt.isoformat()}  ")
    L.append(f"- 모드: {mode}  ")
    if mode == "암 진단 모드":
        L.append(f"- 암 그룹/진단: {group} / {dx}  ")
        if tx_phase: L.append(f"- 치료 단계: {tx_phase}  ")
        if tx_selected: L.append(f"- 현재 치료 선택: {', '.join(tx_selected)}  ")
    L.append("")
    if lab_values:
        L.append("## 입력 수치")
        for abbr in ORDER:
            if abbr in lab_values and entered(lab_values[abbr]):
                L.append(f"- {label(abbr)}: {lab_values[abbr]}")
        L.append("")
    if lab_notes:
        L.append("## 해석 요약"); [L.append(f"- {m}") for m in lab_notes]; L.append("")
    if spec_notes:
        L.append("## 특수검사 해석"); [L.append(f"- {m}") for m in spec_notes]; L.append("")
    if mode == "암 진단 모드":
        L.append("## 치료 카탈로그(추천)")
        for sec in ["항암제","표적치료제"]:
            items = tx_catalog.get(sec, [])
            if not items: continue
            L.append(f"### {sec}")
            for d in items:
                L.append(f"- {d}")
        L.append("")
    if food_lines:
        L.append("## 음식/식이 가이드"); [L.append(f"- {t}") for t in food_lines]; L.append("")
    L.append("---")
    L.append("```")
    L.append(DISCLAIMER)
    L.append("```")
    return "\n".join(L)

# -----------------------------
# 진단 카탈로그 (항암/표적만, 면역/세포 제외)
# -----------------------------
# 혈액암
HEME_DISPLAY = [
    "급성 골수성 백혈병(AML)","급성 전골수구성 백혈병(APL)","급성 림프모구성 백혈병(ALL)",
    "만성 골수성 백혈병(CML)","만성 림프구성 백혈병(CLL)","다발골수종(Multiple Myeloma)",
    "골수이형성증후군(MDS)","골수증식성 종양(MPN)"
]
HEME_KEY = {
    "급성 골수성 백혈병(AML)":"AML",
    "급성 전골수구성 백혈병(APL)":"APL",
    "급성 림프모구성 백혈병(ALL)":"ALL",
    "만성 골수성 백혈병(CML)":"CML",
    "만성 림프구성 백혈병(CLL)":"CLL",
    "다발골수종(Multiple Myeloma)":"MM",
    "골수이형성증후군(MDS)":"MDS",
    "골수증식성 종양(MPN)":"MPN",
}

# 림프종
LYMPH_DISPLAY = [
    "미만성 거대 B세포 림프종(DLBCL)","원발 종격동 B세포 림프종(PMBCL)",
    "여포성 림프종 1-2등급(FL 1-2)","여포성 림프종 3A(FL 3A)","여포성 림프종 3B(FL 3B)",
    "외투세포 림프종(MCL)","변연대 림프종(MZL)","고등급 B세포 림프종(HGBL)","버킷 림프종(Burkitt)",
    "고전적 호지킨 림프종(cHL)","말초 T세포 림프종(PTCL-NOS)","비강형 NK/T 세포 림프종(ENKTL)"
]
LYMPH_KEY = {
    "미만성 거대 B세포 림프종(DLBCL)":"DLBCL",
    "원발 종격동 B세포 림프종(PMBCL)":"PMBCL",
    "여포성 림프종 1-2등급(FL 1-2)":"FL12",
    "여포성 림프종 3A(FL 3A)":"FL3A",
    "여포성 림프종 3B(FL 3B)":"FL3B",
    "외투세포 림프종(MCL)":"MCL",
    "변연대 림프종(MZL)":"MZL",
    "고등급 B세포 림프종(HGBL)":"HGBL",
    "버킷 림프종(Burkitt)":"BL",
    "고전적 호지킨 림프종(cHL)":"cHL",
    "말초 T세포 림프종(PTCL-NOS)":"PTCL",
    "비강형 NK/T 세포 림프종(ENKTL)":"ENKTL",
}

# 고형암
SOLID_DISPLAY = [
    "폐선암(Lung Adenocarcinoma)","NSCLC 편평(Lung Squamous)","SCLC(소세포폐암)",
    "유방암 HR+","유방암 HER2+","삼중음성유방암(TNBC)",
    "위암(Gastric)","대장암(Colorectal)","췌장암(Pancreatic)",
    "간세포암(HCC)","담관암(Cholangiocarcinoma)","신장암(RCC)",
    "전립선암(Prostate)","방광암(Bladder)","난소암(Ovarian)",
    "자궁경부암(Cervical)","자궁내막암(Endometrial)",
    "두경부암 Head&Neck SCC","식도암(Esophageal)","역형성갑상선암(ATC)"
]
SOLID_KEY = {
    "폐선암(Lung Adenocarcinoma)":"LungAdeno",
    "NSCLC 편평(Lung Squamous)":"LungSCC",
    "SCLC(소세포폐암)":"SCLC",
    "유방암 HR+":"BreastHR",
    "유방암 HER2+":"BreastHER2",
    "삼중음성유방암(TNBC)":"TNBC",
    "위암(Gastric)":"Gastric",
    "대장암(Colorectal)":"CRC",
    "췌장암(Pancreatic)":"Pancreas",
    "간세포암(HCC)":"HCC",
    "담관암(Cholangiocarcinoma)":"CCA",
    "신장암(RCC)":"RCC",
    "전립선암(Prostate)":"Prostate",
    "방광암(Bladder)":"Bladder",
    "난소암(Ovarian)":"Ovary",
    "자궁경부암(Cervical)":"Cervix",
    "자궁내막암(Endometrial)":"Endomet",
    "두경부암 Head&Neck SCC":"HNSCC",
    "식도암(Esophageal)":"Esophagus",
    "역형성갑상선암(ATC)":"ATC"
}

# 육종 / 희귀
SARCOMA_DISPLAY = ["UPS(미분화 다형성)","LMS(평활근)","LPS(지방)","Synovial Sarcoma","Ewing Sarcoma",
                   "Rhabdomyosarcoma","Angiosarcoma","DFSP","GIST"]
SARCOMA_KEY = {
    "UPS(미분화 다형성)":"UPS","LMS(평활근)":"LMS","LPS(지방)":"LPS",
    "Synovial Sarcoma":"Synovial","Ewing Sarcoma":"Ewing","Rhabdomyosarcoma":"Rhabdo",
    "Angiosarcoma":"Angio","DFSP":"DFSP","GIST":"GIST",
}

RARE_DISPLAY = ["GIST(지스트)","NET(신경내분비종양)","Medullary Thyroid(수질갑상선암)","Pheochromocytoma/Paraganglioma","Uveal Melanoma","Merkel Cell(메르켈세포)"]
RARE_KEY = {"GIST(지스트)":"GIST","NET(신경내분비종양)":"NET","Medullary Thyroid(수질갑상선암)":"MTC","Pheochromocytoma/Paraganglioma":"PPGL","Uveal Melanoma":"Uveal","Merkel Cell(메르켈세포)":"Merkel"}

# 치료 카탈로그(항암제/표적치료제만)
TX: Dict[str, Dict[str, Dict[str, List[str]]]] = {
    "혈액암": {
        "AML": {
            "항암제": ["Cytarabine(Ara-C)","Anthracycline(Idarubicin/Daunorubicin)","CPX-351(고위험군)","Azacitidine+Venetoclax"],
            "표적치료제": ["Midostaurin(FLT3)","Gilteritinib(FLT3, 재발/불응)","Enasidenib(IDH2)","Ivosidenib(IDH1)","Glasdegib(Hedgehog)"]
        },
        "APL": {
            "항암제": ["ATRA(베사노이드)","ATO","Cytarabine(Ara-C, 고위험 병용)","6-MP(유지)","MTX(유지)"],
            "표적치료제": ["ATRA+ATO (PML-RARA 표적적 접근)"]
        },
        "ALL": {
            "항암제": ["Hyper-CVAD","Cytarabine(Ara-C, 고용량)"],
            "표적치료제": ["Blinatumomab(CD19 BiTE)","Inotuzumab ozogamicin(CD22 ADC)","Rituximab(CD20+, 일부 B-ALL)","Nelarabine(T-ALL)"]
        },
        "CML": {
            "항암제": [],
            "표적치료제": ["Imatinib(1세대)","Dasatinib","Nilotinib","Bosutinib","Ponatinib(T315I)","Asciminib(STI, allosteric)"]
        },
        "CLL": {
            "항암제": [],
            "표적치료제": ["Ibrutinib","Acalabrutinib","Zanubrutinib","Venetoclax(+Obinutuzumab)","Rituximab/Obinutuzumab/Ofatumumab","Idelalisib/Duvelisib(제한적)"]
        },
        "MM": {
            "항암제": ["VRd(Bortezomib+Lenalidomide+Dexamethasone)","Carfilzomib","Ixazomib"],
            "표적치료제": ["Daratumumab(Isatuximab, anti-CD38)","Elotuzumab(SLAMF7)","Belantamab mafodotin(BCMA ADC)"]
        },
        "MDS": {
            "항암제": ["Azacitidine","Decitabine"],
            "표적치료제": ["Luspatercept(저위험 빈혈)","Ivosidenib/Enasidenib(IDH 변이 일부)"]
        },
        "MPN": {
            "항암제": ["Hydroxyurea"],
            "표적치료제": ["Ruxolitinib(JAK2)","Fedratinib(JAK2)","Ropeginterferon alfa-2b(PV)"]
        },
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

# 약물 요약(한글/작용/주의) — 일부 대표 약 (발췌)
drug_info = {
    "ATRA(베사노이드)": {"ko":"비스트레티노인","mech":"미성숙 전구세포 분화 유도","ae":"분화증후군, 간수치 상승, 피부건조/광과민"},
    "ATO": {"ko":"무수비소","mech":"분화 유도/세포사멸","ae":"QT 연장, 전해질 이상"},
    "6-MP": {"ko":"6-머캅토퓨린","mech":"퓨린 합성 억제","ae":"간독성, 골수억제, 오심"},
    "MTX": {"ko":"메토트렉세이트","mech":"DHFR 억제","ae":"골수억제, 간/신독성, 구내염"},
    "Cytarabine(Ara-C)": {"ko":"시타라빈","mech":"핵산 합성 저해","ae":"골수억제, 결막염/신경독성(고용량)"},
    "Anthracycline(Idarubicin/Daunorubicin)": {"ko":"안트라사이클린","mech":"Topo II 억제","ae":"심독성, 골수억제"},
    "Azacitidine": {"ko":"아자시티딘","mech":"DNA 메틸화 억제","ae":"골수억제, 오심"},
    "Decitabine": {"ko":"데시타빈","mech":"DNA 메틸화 억제","ae":"골수억제"},
    "Venetoclax": {"ko":"베네토클락스","mech":"BCL-2 억제","ae":"종양융해증후군, 골수억제"},
    "Midostaurin(FLT3)": {"ko":"미도스터린","mech":"FLT3 억제","ae":"오심, QT 연장 가능"},
    "Gilteritinib(FLT3, 재발/불응)": {"ko":"길테리티닙","mech":"FLT3 억제","ae":"간수치 상승, 피로"},
    "Enasidenib(IDH2)": {"ko":"에나시데닙","mech":"IDH2 억제","ae":"분화증후군, 고빌리루빈혈증"},
    "Ivosidenib(IDH1)": {"ko":"이보시데닙","mech":"IDH1 억제","ae":"분화증후군, 간독성"},
    "Glasdegib(Hedgehog)": {"ko":"글라스데깁","mech":"Hedgehog 경로 억제","ae":"미각저하, 근육경련"},
    "Imatinib": {"ko":"이마티닙","mech":"BCR-ABL/KIT 등 억제","ae":"부종, 피로"},
    "Dasatinib": {"ko":"다사티닙","mech":"BCR-ABL 억제","ae":"흉막/심낭 삼출"},
    "Nilotinib": {"ko":"닐로티닙","mech":"BCR-ABL 억제","ae":"QT 연장, 대사이상"},
    "Bosutinib": {"ko":"보수티닙","mech":"BCR-ABL 억제","ae":"설사, 간수치 상승"},
    "Ponatinib(T315I)": {"ko":"포나티닙","mech":"BCR-ABL(T315I) 억제","ae":"혈전/혈관 이상"},
    "Asciminib": {"ko":"아시미닙","mech":"BCR-ABL allosteric","ae":"췌장염, 근골격통"},
    "Ibrutinib": {"ko":"이브루티닙","mech":"BTK 억제","ae":"출혈/AFib 위험"},
    "Acalabrutinib": {"ko":"아칼라브루티닙","mech":"BTK 억제","ae":"두통, 혈소판감소"},
    "Zanubrutinib": {"ko":"자누브루티닙","mech":"BTK 억제","ae":"호중구감소, 출혈"},
    "Obinutuzumab": {"ko":"오비누투주맙","mech":"anti-CD20","ae":"주입반응"},
    "Rituximab": {"ko":"리툭시맙","mech":"anti-CD20","ae":"주입반응, HBV reactivation"},
    "Blinatumomab(CD19 BiTE)": {"ko":"블리나투모맙","mech":"CD19×CD3 BiTE","ae":"CRS, 신경독성"},
    "Inotuzumab ozogamicin(CD22 ADC)": {"ko":"이노투주맙 오조가마이신","mech":"CD22 ADC","ae":"간정맥폐쇄병증"},
    "Daratumumab": {"ko":"다라투무맙","mech":"anti-CD38","ae":"주입반응"},
    "Isatuximab": {"ko":"이사툭시맙","mech":"anti-CD38","ae":"주입반응"},
    "Elotuzumab": {"ko":"엘로투주맙","mech":"anti-SLAMF7","ae":"피로, 감염"},
    "Belantamab mafodotin": {"ko":"벨란타맵 마포도틴","mech":"BCMA ADC","ae":"각막독성"},
    "EGFR(Osimertinib)": {"ko":"오시머티닙","mech":"EGFR TKI","ae":"발진, 설사"},
    "ALK(Alectinib)": {"ko":"알렉티닙","mech":"ALK TKI","ae":"간수치 상승, 변비"},
    "Bevacizumab": {"ko":"베바시주맙","mech":"VEGF 억제","ae":"출혈/혈전, 단백뇨"},
    "T-DM1": {"ko":"트라스투주맙 엠탄신","mech":"HER2 ADC","ae":"혈소판감소, 간독성"},
    "T-DXd": {"ko":"트라스투주맙 데룩스테칸","mech":"HER2 ADC","ae":"간질성폐질환 주의"},
    "Lenvatinib": {"ko":"렌바티닙","mech":"다중 TKI","ae":"고혈압, 단백뇨"},
    "Sorafenib": {"ko":"소라페닙","mech":"다중 TKI","ae":"손발증후군"},
    "Regorafenib": {"ko":"레고라페닙","mech":"다중 TKI","ae":"피로, 손발증"},
    "Cabozantinib": {"ko":"카보잔티닙","mech":"RET/MET/VEGFR TKI","ae":"손발증, 고혈압"},
    "Axitinib": {"ko":"액시티닙","mech":"VEGFR TKI","ae":"고혈압, 단백뇨"},
    "Erdafitinib(FGFR)": {"ko":"에르다피티닙","mech":"FGFR 억제","ae":"고인산혈증, 시야변화"},
    "Olaparib": {"ko":"올라파립","mech":"PARP 억제","ae":"빈혈, 오심"},
    "Niraparib": {"ko":"니라파립","mech":"PARP 억제","ae":"혈소판감소"},
    "Selpercatinib": {"ko":"셀퍼카티닙","mech":"RET 억제","ae":"고혈압, 간수치 상승"},
    "Pralsetinib": {"ko":"프랄세티닙","mech":"RET 억제","ae":"간수치 상승"},
    "Sunitinib": {"ko":"수니티닙","mech":"VEGFR/PDGFR/KIT 억제","ae":"고혈압, 피로"},
    "Vandetanib": {"ko":"반데타닙","mech":"RET/EGFR/VEGFR 억제","ae":"QT 연장"},
}

# -----------------------------
# 카탈로그 유틸
# -----------------------------
def get_tx_catalog(group: str, dx_label: str) -> Dict[str, List[str]]:
    if not group or not dx_label: return {"항암제":[], "표적치료제":[]}
    if group == "혈액암":
        key = HEME_KEY.get(dx_label, dx_label)
        return TX["혈액암"].get(key, {"항암제":[], "표적치료제":[]})
    if group == "림프종":
        key = LYMPH_KEY.get(dx_label, dx_label)
        return TX["림프종"].get(key, {"항암제":[], "표적치료제":[]})
    if group == "고형암":
        key = SOLID_KEY.get(dx_label, dx_label)
        return TX["고형암"].get(key, {"항암제":[], "표적치료제":[]})
    if group == "육종":
        key = SARCOMA_KEY.get(dx_label, dx_label)
        return TX["육종"].get(key, {"항암제":[], "표적치료제":[]})
    if group == "희귀암":
        key = RARE_KEY.get(dx_label, dx_label)
        return TX["희귀암"].get(key, {"항암제":[], "표적치료제":[]})
    return {"항암제":[], "표적치료제":[]}

def flatten_tx(cat: Dict[str, List[str]]) -> List[str]:
    out: List[str] = []
    for k in ["항암제","표적치료제"]:
        out.extend(cat.get(k, []))
    return list(dict.fromkeys(out))

# -----------------------------
# UI 시작
# -----------------------------
st.set_page_config(page_title=PAGE_TITLE, layout="centered")
st.title(APP_TITLE)
st.caption(MADE_BY)
st.markdown(f"[공식 카페로 이동]({CAFE_LINK})")

if "used_keys" not in st.session_state: st.session_state.used_keys = set()
if "store" not in st.session_state:     st.session_state.store = load_records()

st.subheader("사용자 식별")
c1, c2 = st.columns([2,1])
nickname = c1.text_input("별명", placeholder="예: 민수아빠", key="nickname")
pin      = c2.text_input("PIN(4자리)", max_chars=4, placeholder="예: 1234", key="pin")
pin_clean = "".join([c for c in (pin or "") if c.isdigit()])[:4]
nick_key  = f"{nickname.strip()}#{pin_clean}" if nickname and pin_clean else ""
if nick_key:
    if nick_key in st.session_state.used_keys:
        st.warning("이미 사용 중인 별명+PIN 조합입니다. (동일 세션 내 중복 방지)")
    else:
        st.session_state.used_keys.add(nick_key)

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

# --- 특수검사 입력
def special_inputs() -> (Dict[str,str], Dict[str,float], List[str]):
    qc, qn, info = {}, {}, []
    st.markdown("### 특수검사 (토글)")
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
                stage, lab = stage_acr(acr)
                info.append(f"ACR(자동): {acr} mg/g · {stage or ''} {lab or ''}")
            upcr_manual = parse_float(st.text_input("Pro/Cr, urine (mg/g) — 수기 입력", key="upcr_m"))
            if upcr_manual is not None: upcr = upcr_manual
            if upcr is not None: qn["UPCR"] = upcr
            if acr is not None: qn["ACR"] = acr

    with st.expander("지질(기본/확장)", expanded=False):
        c1,c2,c3,c4 = st.columns(4)
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

    with st.expander("전해질 확장/보정Ca", expanded=False):
        e1,e2,e3 = st.columns(3)
        qn["Mg"]  = parse_float(e1.text_input("Mg (mg/dL)", key="el_mg"))
        qn["Phos(인)"] = parse_float(e2.text_input("인 Phos (mg/dL)", key="el_phos"))
        qn["iCa"] = parse_float(e3.text_input("이온화칼슘 iCa (mmol/L)", key="el_ica"))
        ca_corr = calc_corrected_ca(st.session_state.get("lab_Ca"), st.session_state.get("lab_Alb"))
        if ca_corr is not None:
            qn["Corrected Ca"] = ca_corr
            info.append(f"보정 칼슘(Alb 반영): {ca_corr} mg/dL")

    with st.expander("갑상선/당대사/패혈증", expanded=False):
        t1,t2,t3 = st.columns(3)
        qn["TSH"] = parse_float(t1.text_input("TSH (µIU/mL)", key="thy_tsh"))
        qn["Free T4"] = parse_float(t2.text_input("Free T4 (ng/dL)", key="thy_ft4"))
        qn["Total T3"] = parse_float(t3.text_input("Total T3 (ng/dL)", key="thy_t3"))
        g1,g2,g3 = st.columns(3)
        qn["공복혈당"] = parse_float(g1.text_input("공복혈당 (mg/dL)", key="glu_f"))
        qn["HbA1c"]   = parse_float(g2.text_input("HbA1c (%)", key="glu_a1c"))
        ins = parse_float(g3.text_input("Insulin (µU/mL)", key="glu_ins"))
        if qn.get("공복혈당") is not None and ins is not None:
            homa = calc_homa_ir(qn["공복혈당"], ins)
            if homa is not None:
                qn["HOMA-IR"] = homa
                info.append(f"HOMA-IR(자동): {homa}")
        s1,s2 = st.columns(2)
        qn["PCT"] = parse_float(s1.text_input("Procalcitonin PCT (ng/mL)", key="sep_pct"))
        qn["Lactate"] = parse_float(s2.text_input("Lactate (mmol/L)", key="sep_lac"))

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

# -----------------------------
# 본문
# -----------------------------
if mode == "소아 일상/질환":
    st.info("소아 감염/일상 중심: 항암제는 숨김 처리됩니다.")
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

    labs = lab_inputs(always_show=True)

    # 진단별 카탈로그 불러오기 + 기본 리스트(평면)
    tx_catalog = get_tx_catalog(group, dx)
    flat = flatten_tx(tx_catalog)

    # 치료 단계 + 현재 치료 선택
    st.markdown("### 치료 단계 / 현재 치료 선택")
    tx_phase = st.selectbox("치료 단계", ["", "유지요법", "외래 항암", "입원 항암", "완료(추적관찰)"], index=0, key="tx_phase")
    tx_selected = st.multiselect("현재 항암제/치료 선택 (복수 선택 가능)", flat, default=[], key="tx_sel")
    tx_custom = st.text_input("직접 추가(쉼표로 구분, 예: Cyclophosphamide, Rituximab)", key="tx_custom")
    if tx_custom.strip():
        extra = [x.strip() for x in tx_custom.split(",") if x.strip()]
        for e in extra:
            if e not in tx_selected:
                tx_selected.append(e)

    # 카테고리별 추천 목록(요약 설명)
    st.markdown("### 치료 카탈로그(추천·설명)")
    for sec in ["항암제","표적치료제"]:
        items = tx_catalog.get(sec, [])
        if not items: continue
        with st.expander(sec, expanded=(sec=="항암제")):
            for d in items:
                info = drug_info.get(d, {})
                ko = info.get("ko",""); mech = info.get("mech",""); ae = info.get("ae","")
                st.markdown(f"- **{d}**{f' ({ko})' if ko else ''}")
                if mech: st.caption(f"작용: {mech}")
                if ae:   st.caption(f"주의: {ae}")

    qc, qn, calc_info = special_inputs()

st.divider()

# eGFR 계산(기본 Cr, 나이/성별 받아서)
st.markdown("### eGFR 계산 (선택)")
age = parse_float(st.text_input("나이(세)", key="kid_age"))
sex = st.selectbox("성별", ["F","M"], key="kid_sex")
egfr = None
if entered(st.session_state.get("lab_Cr")) and age:
    egfr = calc_egfr(st.session_state.get("lab_Cr"), age=age, sex=sex)
    if egfr is not None:
        st.info(f"eGFR(자동): {egfr} mL/min/1.73m²")
        # qn dict는 special_inputs() 내부 로컬이므로 추가 반영
        # 간단히 아래처럼 저장: (보고서/해석 시 qn 활용)
        st.session_state["calc_egfr_value"] = egfr

# 해석/저장
colA, colB, colC = st.columns([1,1,1])
run_analyze = colA.button("🔎 해석하기 & 저장", use_container_width=True, key="btn_analyze")
clear_user  = colB.button("🗑️ 이 사용자 기록 전체 삭제", use_container_width=True, key="btn_clear")
load_last   = colC.button("↩️ 가장 최근 기록으로 폼 채우기", use_container_width=True, key="btn_fill")

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
        # egfr 반영
        if st.session_state.get("calc_egfr_value") is not None:
            # special 입력 로컬 qn에 직접 넣기 어려우므로, 아래에서 report/저장 시 병합
            pass

        lab_notes  = interpret_labs(labs)
        # special notes
        qn_for_eval = {**locals().get("qn", {}), **({"eGFR": st.session_state.get("calc_egfr_value")} if st.session_state.get("calc_egfr_value") is not None else {})}
        spec_notes = interpret_special_extended(locals().get("qc", {}), qn_for_eval, base_vals=labs, profile="adult")
        food_lines = build_food_guide(labs)

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
            st.subheader("🥗 음식 가이드")
            for t in food_lines: st.write("• " + t)

        group = locals().get("group","") if mode=="암 진단 모드" else ""
        dx    = locals().get("dx","")    if mode=="암 진단 모드" else ""
        tx_catalog = locals().get("tx_catalog", {"항암제":[], "표적치료제":[]}) if mode=="암 진단 모드" else {}
        tx_phase   = locals().get("tx_phase","") if mode=="암 진단 모드" else ""
        tx_selected= locals().get("tx_selected", []) if mode=="암 진단 모드" else []

        report_md = build_report_md(
            nick_key, test_date, mode, group, dx, labs, lab_notes, spec_notes,
            tx_catalog, tx_phase, tx_selected, food_lines
        )
        st.download_button("📥 보고서(.md) 다운로드", data=report_md.encode("utf-8"),
                           file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                           mime="text/markdown")
        st.download_button("📄 보고서(.txt) 다운로드", data=report_md.encode("utf-8"),
                           file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                           mime="text/plain")

        # 저장 레코드
        rec = {
            "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "date": test_date.isoformat(),
            "mode": mode, "group": group, "dx": dx,
            "tx_phase": tx_phase, "tx_selected": tx_selected,
            "labs": {k: labs.get(k) for k in ORDER if entered(labs.get(k))},
            "special": {"qc": locals().get("qc", {}), "qn": qn_for_eval},
        }
        st.session_state.store.setdefault(nick_key, []).append(rec)
        save_records(st.session_state.store)
        st.success("저장 완료! 아래 그래프로 추이를 확인하세요.")

st.divider()
# -----------------------------
# 그래프 (별명#PIN 기준)
# -----------------------------
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

        st.caption("기본 지표: WBC, Hb, PLT, CRP, ANC")
        metric_sel = st.multiselect(
            "그래프에 표시할 항목 선택",
            ["WBC","Hb","PLT","CRP","ANC"] + [x for x in ORDER if x not in ["WBC","Hb","PLT","CRP","ANC"]],
            default=["WBC","Hb","PLT","CRP","ANC"],
            key="metric_sel"
        )
        if not metric_sel:
            st.info("표시할 항목을 선택하세요.")
        else:
            for m in metric_sel:
                if m not in df.columns:
                    continue
                sub = df[["date", m]].dropna()
                if len(sub) == 0:
                    st.warning(f"{m} 데이터가 아직 없습니다.")
                    continue
                st.subheader(label(m))
                st.line_chart(sub.set_index("date")[m])

st.markdown("---")
st.markdown(f"_{MADE_BY}_")
st.markdown(f"[공식 카페]({CAFE_LINK})")
st.code(DISCLAIMER, language="text")
