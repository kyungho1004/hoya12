# app.py  — BloodMap 단일파일 버전
# 실행: streamlit run app.py

from __future__ import annotations
import streamlit as st
import pandas as pd
import numpy as np
import math, io, json, datetime as dt

# ===== 안전 기본값(외부 config 없이 동작) =====
PAGE_TITLE = "피수치 가이드 (BloodMap)"
APP_TITLE  = "피수치 가이드 (BloodMap)"
DISCLAIMER = (
    "본 수치는 참고용이며, 해석 결과는 개발자와 무관합니다.\n"
    "약 변경, 복용 중단 등은 반드시 주치의와 상의 후 결정하시기 바랍니다.\n"
    "이 앱은 개인정보를 절대 수집하지 않으며, 어떠한 개인정보 입력도 요구하지 않습니다."
)
MADE_BY = "🛠️ BloodMap 프로젝트 제작"
# ===========================================

st.set_page_config(page_title=PAGE_TITLE, layout="centered")

# ---------------- 공통 유틸 ----------------
def round_half_ml(x: float) -> float:
    """0.5 mL 단위 반올림(평균값), 2.0 mL 같은 정수/0.5는 그대로."""
    if x is None or x != x:  # NaN
        return 0.0
    return round(x * 2) / 2.0

def color_badge(label:str, level:str) -> str:
    m = {"정상":"🟢", "주의":"🟡", "위험":"🟥"}
    return f"{m.get(level,'⚪')} {label}"

def now_ts() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M")

def slug(s: str) -> str:
    return "".join(ch for ch in s if ch.isalnum() or ch in ("_","-"," ")).strip()

# ------------- 소아 질환/증상 사전 -------------
DISEASE_SYMPTOMS = {
    "RSV": ["기침", "콧물", "쌕쌕거림", "호흡곤란"],
    "Adenovirus(아데노)": ["열", "눈충혈", "기침", "설사"],
    "Parainfluenza(파라인플루엔자)": ["기침", "쉰목소리", "호흡곤란"],
    "Rotavirus(로타)": ["설사", "구토", "탈수"],
    "수족구(HFMD)": ["물집", "입안 통증", "열"],
    "COVID-19": ["열", "기침", "콧물", "무증상", "후각소실"],
    "크룹(Croup)": ["쉰목소리", "개짖는 기침", "호흡곤란"],
    "모세기관지염(Bronchiolitis)": ["쌕쌕거림", "호흡곤란", "기침"],
    "Mycoplasma(마이코플라즈마)": ["기침", "두통", "열", "피로감"],
}

# 증상 체크 옵션(보호자 입력 UI에 사용)
SYM_OPTIONS = {
    "기침":    ["없음","조금","보통","심함"],
    "콧물":    ["없음","투명","흰색","노란색","피섞임"],
    "설사":    ["횟수 직접입력"],
    "열":      ["직접입력(°C)"],
    "두통":    ["없음","조금","보통","많이","심함"],
    "호흡곤란":["없음","조금","보통","많이","심함"],
    "물집":    ["없음","있음(손/발/전신 체크)"],
    "탈수증상":["없음","있음"],
    "눈꼽":    ["없음","조금","보통","많이","심함"],
    "쌕쌕거림":["없음","조금","보통","심함"],
    "쉰목소리":["없음","조금","보통","심함"],
    "눈충혈":  ["없음","조금","보통","심함"],
    "구토":    ["없음","1-2회","3회 이상"],
    "무증상":  ["체크"],
    "후각소실":["없음","있음"],
    "개짖는 기침":["없음","있음"]
}

# ------------- 항암제 한글 병기 사전 -------------
DRUG_NAME_KR = {
    # Leukemia / Hematology
    "Cytarabine(Ara-C)": "사이타라빈",
    "Anthracycline(Idarubicin/Daunorubicin)": "안트라사이클린(이다루비신/다우노루비신)",
    "Azacitidine+Venetoclax": "아자시티딘+베네토클락스",
    "Azacitidine": "아자시티딘",
    "Decitabine": "데시타빈",
    "Hydroxyurea": "하이드록시우레아",
    "6-MP(유지)": "메르캅토퓨린",
    "MTX(유지)": "메토트렉세이트",
    "HiDAC": "고용량 사이타라빈",
    "ATRA(베사노이드)": "ATRA(베사노이드)",
    "ATO": "산화비소(ATO)",
    "Hyper-CVAD": "하이퍼-CVAD",
    # Targeted / TKIs
    "Midostaurin(FLT3)": "미도스타우린",
    "Gilteritinib(FLT3, 재발/불응)": "길테리티닙",
    "Enasidenib(IDH2)": "에나시데닙",
    "Ivosidenib(IDH1)": "이보시데닙",
    "Glasdegib(Hedgehog)": "글라스데깁",
    "Imatinib(1세대)": "이미티닙",
    "Dasatinib": "다사티닙",
    "Nilotinib": "닐로티닙",
    "Bosutinib": "보수티닙",
    "Ponatinib(T315I)": "포나티닙",
    "Asciminib(STI, allosteric)": "아시미닙",
    # Lymphoma
    "R-CHOP": "리툭시맙+사이클로포스파마이드+독소루비신+빈크리스틴+프레드니손",
    "Pola-R-CHP": "폴라투주맙 포함 R-CHP",
    "R-ICE": "리툭시맙+이포스파마이드+카보플라틴+에토포시드",
    "R-DHAP": "리툭시맙+데사메타손+시타라빈+시스플라틴",
    "R-GDP": "리툭시맙+젬시타빈+덱사메타손+시스플라틴",
    "R-GemOx": "리툭시맙+젬시타빈+옥살리플라틴",
    "BR": "벤다무스틴+리툭시맙",
    "Pola-BR": "폴라투주맙+벤다무스틴+리툭시맙",
    "Lenalidomide+Rituximab": "레날리도마이드+리툭시맙",
    "ABVD": "독소루비신+블레오마이신+빈블라스틴+다카르바진",
    "BV-AVD": "브렌툭시맙+독소루비신+빈블라스틴+다카르바진",
    "Tafasitamab+Lenalidomide": "타파시타맙+레날리도마이드",
    "Loncastuximab": "론카스투시맙",
    # Myeloma
    "VRd(Bortezomib+Lenalidomide+Dexamethasone)": "보르테조밉+레날리도마이드+덱사메타손",
    "Bortezomib": "보르테조밉",
    "Lenalidomide": "레날리도마이드",
    "Dexamethasone": "덱사메타손",
    "Carfilzomib": "카필조밉",
    "Ixazomib": "익사조밉",
    "Daratumumab(Isatuximab)": "다라투무맙/이사툭시맙",
    "Elotuzumab": "엘로투주맙",
    "Belantamab mafodotin": "벨란타맙 마포도틴",
    # MPN
    "Ruxolitinib(JAK2)": "룩소리티닙",
    "Fedratinib(JAK2)": "페드라티닙",
    "Ropeginterferon alfa-2b(PV)": "로페그인터페론 알파-2b",
    # Solid — Lung
    "Platinum+Pemetrexed": "백금계+페메트렉시드",
    "Platinum+Taxane": "백금계+탁산",
    "Platinum+Etoposide": "백금계+에토포시드",
    "EGFR(Osimertinib)": "오시머티닙",
    "ALK(Alectinib)": "알렉티닙",
    "ROS1(Crizotinib/Entrectinib)": "크리조티닙/엔트렉티닙",
    "BRAF V600E(Dabrafenib+Trametinib)": "다브라페닙+트라메티닙",
    "METex14(Tepotinib/Capmatinib)": "테포티닙/카프마티닙",
    "RET(Selpercatinib/Pralsetinib)": "셀퍼카티닙/프랄세티닙",
    "KRAS G12C(Sotorasib/Adagrasib)": "소토라십/아다가라십",
    # GI / Breast / GU / 기타
    "FOLFOX": "옥살리플라틴+5-FU+류코보린",
    "FOLFIRI": "이리노테칸+5-FU+류코보린",
    "FOLFIRINOX": "이리노테칸+옥살리플라틴+5-FU+류코보린",
    "Gemcitabine+nab-Paclitaxel": "젬시타빈+나노-파클리탁셀",
    "Gemcitabine+Cisplatin": "젬시타빈+시스플라틴",
    "Carboplatin+Paclitaxel": "카보플라틴+파클리탁셀",
    "Cetuximab": "세툭시맙",
    "Panitumumab": "파니투무맙",
    "Bevacizumab": "베바시주맙",
    "Trastuzumab+Pertuzumab": "트라스투주맙+퍼투주맙",
    "T-DM1": "트라스투주맙 엠탄신(T-DM1)",
    "T-DXd": "트라스투주맙 데룩스테칸(T-DXd)",
    "ET(AI/Tamoxifen)+CDK4/6i": "내분비치료+CDK4/6 억제제",
    "Abiraterone/Enzalutamide/Apalutamide": "아비라테론/엔잘루타마이드/아팔루타마이드",
    "PARP inhibitor(Olaparib/Niraparib)": "PARP 억제제(올라파립/니라파립)",
    "Cabozantinib": "카보잔티닙",
    "Axitinib": "악시티닙",
    "Lenvatinib": "렌바티닙",
    "Sorafenib": "소라페닙",
    "Regorafenib(2차)": "레고라페닙",
    "Erdafitinib(FGFR)": "에르다피티닙",
    "Everolimus": "에베로리무스",
    "Sunitinib(2차)": "수니티닙(2차)",
}

def with_korean_drug(name: str) -> str:
    """영문 (한글) 표시"""
    name = (name or "").strip()
    if not name:
        return name
    kr = DRUG_NAME_KR.get(name)
    # 괄호 내 이미 한글이 있으면 그대로 두고 뒤에 한글 병기만 추가
    if kr:
        return f"{name} ({kr})"
    # 괄호 안 한글 추출
    if "(" in name and ")" in name:
        inner = name[name.find("(")+1:name.rfind(")")]
        if any("가" <= ch <= "힣" for ch in inner):
            return name  # 이미 한글 포함
    return name

# ----------- 암 카테고리/진단/단계/옵션 -----------
CANCER_GROUPS = ["혈액암","림프종","고형암","육종","희귀암"]

DX = {
    "혈액암": [
        "AML(급성 골수성 백혈병)",
        "APL(급성 전골수구성 백혈병)",
        "ALL(급성 림프모구 백혈병)",
        "CML(만성 골수성 백혈병)",
        "CLL(만성 림프구성 백혈병)",
        "MM(다발골수종)",
        "MDS(골수형성이상증후군)",
        "MPN(골수증식성 종양)",
    ],
    "림프종": [
        "DLBCL(미만성 B거대세포)",
        "FL(여포성)",
        "MCL(외투세포)",
        "MZL(변연부)",
        "HL(호지킨)",
        "PTCL(말초 T세포)",
        "ENKTL(NK/T)",
    ],
    "고형암": [
        "폐선암",
        "폐편평암",
        "소세포폐암",
        "유방암-HR+",
        "유방암-HER2+",
        "삼중음성유방암",
        "대장암",
        "위암",
        "췌장암",
        "담도암",
        "간세포암(HCC)",
        "신장암(RCC)",
        "방광암",
        "전립선암",
        "난소암",
        "자궁경부암",
        "자궁내막암",
        "갑상선암",
    ],
    "육종": [
        "연부조직육종",
        "골육종",
        "유잉육종",
        "지방육종",
    ],
    "희귀암": [
        "GIST",
        "담낭암",
        "담관내유두상종양",
    ]
}

PHASES = ["진단/초기", "유도", "공고/강화", "유지", "재발/구제", "수술전/후", "병합방사선"]

# 단계별 대표 옵션(참고용; 자동 적용 X)
PHASED_TX = {
    "혈액암": {
        "AML(급성 골수성 백혈병)": {
            "유도": {"레지멘":["Anthracycline(Idarubicin/Daunorubicin)+Cytarabine(Ara-C)"],
                    "항암제":["Cytarabine(Ara-C)","Anthracycline(Idarubicin/Daunorubicin)"],
                    "표적치료제":["Midostaurin(FLT3)","Gilteritinib(FLT3, 재발/불응)","Enasidenib(IDH2)","Ivosidenib(IDH1)","Glasdegib(Hedgehog)"]},
            "유지": {"레지멘":[], "항암제":["Azacitidine+Venetoclax"], "표적치료제":[]},
        },
        "APL(급성 전골수구성 백혈병)": {
            "유도":{"레지멘":["ATRA(베사노이드)+ATO"],"항암제":["ATRA(베사노이드)","ATO"],"표적치료제":[]},
            "유지":{"레지멘":["6-MP(유지)+MTX(유지)"],"항암제":["6-MP(유지)","MTX(유지)"],"표적치료제":[]}
        },
        "ALL(급성 림프모구 백혈병)": {
            "유도":{"레지멘":["Hyper-CVAD"],"항암제":["Hyper-CVAD","HiDAC"],"표적치료제":[]},
        },
        "CML(만성 골수성 백혈병)": {
            "유지":{"레지멘":[],"항암제":[],"표적치료제":["Imatinib(1세대)","Dasatinib","Nilotinib","Bosutinib","Ponatinib(T315I)","Asciminib(STI, allosteric)"]}
        },
        "CLL(만성 림프구성 백혈병)": {
            "유지":{"레지멘":[],"항암제":[],"표적치료제":["Ibrutinib","Acalabrutinib","Zanubrutinib","Venetoclax(+Obinutuzumab)","Rituximab/Obinutuzumab/Ofatumumab","Idelalisib/Duvelisib(제한적)"]}
        },
        "MM(다발골수종)": {
            "유도":{"레지멘":["VRd(Bortezomib+Lenalidomide+Dexamethasone)"],
                    "항암제":["Bortezomib","Lenalidomide","Dexamethasone","Carfilzomib","Ixazomib"],
                    "표적치료제":["Daratumumab(Isatuximab)","Elotuzumab","Belantamab mafodotin"]},
        },
        "MDS(골수형성이상증후군)": {
            "유지":{"레지멘":[],"항암제":["Azacitidine","Decitabine"],"표적치료제":["Ivosidenib(IDH1)","Enasidenib(IDH2)"]}
        },
        "MPN(골수증식성 종양)": {
            "유지":{"레지멘":[],"항암제":["Hydroxyurea"],"표적치료제":["Ruxolitinib(JAK2)","Fedratinib(JAK2)","Ropeginterferon alfa-2b(PV)"]}
        },
    },
    "림프종": {
        "DLBCL(미만성 B거대세포)": {
            "유도":{"레지멘":["R-CHOP","Pola-R-CHP"],"항암제":["R-CHOP","Pola-R-CHP"],"표적치료제":["Tafasitamab+Lenalidomide","Loncastuximab"]},
            "재발/구제":{"레지멘":["R-ICE","R-DHAP","R-GDP","R-GemOx"],"항암제":["R-ICE","R-DHAP","R-GDP","R-GemOx"],"표적치료제":[]}
        },
        "FL(여포성)": {"유도":{"레지멘":["BR","Lenalidomide+Rituximab"],"항암제":["BR"],"표적치료제":["Lenalidomide+Rituximab"]}},
        "HL(호지킨)": {"유도":{"레지멘":["ABVD","BV-AVD"],"항암제":["ABVD","BV-AVD"],"표적치료제":[]}},
    },
    "고형암": {
        "폐선암": {
            "유도":{"레지멘":["Platinum+Pemetrexed"],"항암제":["Platinum+Pemetrexed"],"표적치료제":["EGFR(Osimertinib)","ALK(Alectinib)","ROS1(Crizotinib/Entrectinib)","BRAF V600E(Dabrafenib+Trametinib)","METex14(Tepotinib/Capmatinib)","RET(Selpercatinib/Pralsetinib)","KRAS G12C(Sotorasib/Adagrasib)"]}
        },
        "폐편평암": {"유도":{"레지멘":["Platinum+Taxane"],"항암제":["Platinum+Taxane"],"표적치료제":[]}},
        "소세포폐암": {"유도":{"레지멘":["Platinum+Etoposide"],"항암제":["Platinum+Etoposide"],"표적치료제":[]}},
        "대장암": {"유도":{"레지멘":["FOLFOX","FOLFIRI"],"항암제":["FOLFOX","FOLFIRI"],"표적치료제":["Bevacizumab","Cetuximab","Panitumumab"]}},
        "위암": {"유도":{"레지멘":["FOLFOX"],"항암제":["FOLFOX"],"표적치료제":["Trastuzumab+Pertuzumab","T-DM1","T-DXd"]}},
        "췌장암": {"유도":{"레지멘":["FOLFIRINOX","Gemcitabine+nab-Paclitaxel"],"항암제":["FOLFIRINOX","Gemcitabine+nab-Paclitaxel"],"표적치료제":[]}},
        "담도암": {"유도":{"레지멘":["Gemcitabine+Cisplatin"],"항암제":["Gemcitabine+Cisplatin"],"표적치료제":["Pemigatinib(FGFR2)","Ivosidenib(IDH1)"]}},
        "간세포암(HCC)": {"유지":{"레지멘":[], "항암제":[], "표적치료제":["Lenvatinib","Sorafenib","Regorafenib(2차)"]}},
        "신장암(RCC)": {"유지":{"레지멘":[], "항암제":[], "표적치료제":["Cabozantinib","Axitinib","Everolimus"]}},
        "유방암-HR+": {"유지":{"레지멘":[], "항암제":[], "표적치료제":["ET(AI/Tamoxifen)+CDK4/6i"]}},
        "유방암-HER2+": {"유지":{"레지멘":[], "항암제":[], "표적치료제":["Trastuzumab+Pertuzumab","T-DM1","T-DXd"]}},
        "전립선암": {"유지":{"레지멘":[], "항암제":[], "표적치료제":["Abiraterone/Enzalutamide/Apalutamide","PARP inhibitor(Olaparib/Niraparib)"]}},
        "방광암": {"유지":{"레지멘":[], "항암제":[], "표적치료제":["Erdafitinib(FGFR)"]}},
        "갑상선암": {"유지":{"레지멘":[], "항암제":[], "표적치료제":["Selpercatinib/Pralsetinib(RET)","Vandetanib"]}},
    },
    "육종": {
        "연부조직육종": {"유도":{"레지멘":["Ifosfamide+Etoposide","Gemcitabine+Docetaxel"],"항암제":["Ifosfamide","Trabectedin","Eribulin"],"표적치료제":["Pazopanib"]}},
        "골육종": {"유도":{"레지멘":["MAP(표준)"],"항암제":["Doxorubicin","Ifosfamide"],"표적치료제":[]}},
    }
}

# --------------- 소아 해열제 계산 ---------------
def calc_antipyretic_ml(weight_kg: float, temp_c: float) -> dict:
    """
    평균 1회 용량 기준으로 밀리리터 출력(0.5 mL 반올림)
      - 아세트아미노펜: 12.5 mg/kg, 시럽 160 mg/5mL (32 mg/mL)
      - 이부프로펜: 10 mg/kg, 시럽 100 mg/5mL (20 mg/mL)
    """
    dose_acet_mg = 12.5 * weight_kg
    ml_acet = round_half_ml(dose_acet_mg / 32.0)

    dose_ibu_mg = 10.0 * weight_kg
    ml_ibu  = round_half_ml(dose_ibu_mg / 20.0)

    # 온도 구간 가이드
    if temp_c < 38.0:
        guide = "대개 해열제 불필요, 수분보충/관찰"
    elif temp_c < 38.5:
        guide = "38.0~38.5℃: 컨디션 나쁘면 투여 고려"
    elif temp_c < 39.0:
        guide = "38.5~39.0℃: 증상 따라 투여 권장"
    else:
        guide = "39.0℃ 이상: 투여 권장, 탈수 주의"

    return {"acet_ml": ml_acet, "ibu_ml": ml_ibu, "guide": guide}

# ----------- 피수치 입력 및 기본 해석 ----------
LAB_FIELDS = ["WBC","Hb","PLT","CRP","ANC","AST","ALT","Alb","Ca","P","Na","K","Cr","Glu","LDH","TB"]

def interpret_basic(lab: dict) -> list[str]:
    out = []
    wbc = lab.get("WBC"); plt = lab.get("PLT"); anc = lab.get("ANC")
    ast = lab.get("AST"); alt = lab.get("ALT"); alb = lab.get("Alb")
    if wbc is not None and wbc < 4:
        out.append("WBC 낮음 → 🟡 감염 주의(손 위생·마스크·혼잡 피하기)")
    if plt is not None and plt < 100:
        out.append("혈소판 낮음 → 🟥 멍/출혈 주의, 넘어짐·양치 시 조심")
    if anc is not None and anc < 0.5:
        out.append("ANC 매우 낮음 → 🟥 생채소 금지·익힌 음식·남은 음식 2시간 이후 비권장·껍질 과일 상담")
    if ast is not None and ast >= 50:
        out.append("AST 상승 → 🟡 간 기능 저하 가능")
    if alt is not None and alt >= 55:
        out.append("ALT 상승 → 🟡 간세포 손상 의심")
    if alb is not None and alb < 3.3:
        out.append("알부민 낮음 → 🟡 영양 보강 권장")
    return out

# --------------- 특수검사 입력/계산 ---------------
def calc_corrected_ca(total_ca: float, albumin: float) -> float|None:
    if total_ca is None or albumin is None: return None
    # 보정 Ca (mg/dL) = 측정 Ca + 0.8*(4.0 - Alb)
    return round(total_ca + 0.8*(4.0 - albumin), 2)

def calc_friedewald_ldl(tc, hdl, tg):
    if None in (tc,hdl,tg): return None
    if tg >= 400: return None
    return round(tc - hdl - (tg/5.0), 1)

def calc_non_hdl(tc, hdl):
    if None in (tc,hdl): return None
    return round(tc - hdl, 1)

def calc_egfr(creat, age=40, sex="M"):
    if creat is None: return None
    # CKD-EPI(간략형, 대략값)
    k = 0.7 if sex=="F" else 0.9
    a = -0.329 if sex=="F" else -0.411
    min_cre = min(creat/k, 1.0)
    max_cre = max(creat/k, 1.0)
    egfr = 141*(min_cre**a)*(max_cre**(-1.209))*(0.993**age)*(1.018 if sex=="F" else 1)
    return round(egfr)

def calc_homa_ir(glu_mg_dl, insulin_u):
    if None in (glu_mg_dl, insulin_u): return None
    glu_mmol = glu_mg_dl / 18.0
    return round((glu_mmol*insulin_u)/22.5, 2)

# ---------------- 저장/그래프 ----------------
if "records" not in st.session_state:
    st.session_state["records"] = {}  # key: f"{nick}-{pin}" → list of dict

def save_record(nick_pin: str, payload: dict):
    recs = st.session_state["records"].setdefault(nick_pin, [])
    recs.append(payload)

def get_series(nick_pin: str, field: str):
    rows = st.session_state["records"].get(nick_pin, [])
    xs = [r.get("time") for r in rows if r.get(field) is not None]
    ys = [r.get(field) for r in rows if r.get(field) is not None]
    return xs, ys

# ================== UI 시작 ==================
st.title(APP_TITLE)
st.caption(MADE_BY)

mode = st.radio("진단 모드", ["소아 일상/질환", "암 진단 모드"], horizontal=True)

nick = st.text_input("별명(선택)", value="")
pin  = st.text_input("PIN 4자리(선택)", value="", max_chars=4)

# 저장/그래프 키
nick_pin = f"{slug(nick)}-{slug(pin)}" if nick and pin else None

# ---------- 소아 모드 ----------
if mode == "소아 일상/질환":
    st.info("소아 감염/일상 중심: 항암제는 숨김 처리됩니다.")
    # 보호자 체크(질환 & 증상)
    st.subheader("보호자 체크")
    col1, col2 = st.columns(2)
    disease = col1.selectbox("질환/의심질환", list(DISEASE_SYMPTOMS.keys()))
    temp_now = col2.text_input("현재 체온(°C, 선택)", value="")
    memo = st.text_input("추가 메모(선택)", placeholder="예: 밤새 기침 심했고 해열제 20:30 투여")

    st.markdown("##### 증상 체크")
    picked = {}
    for s in DISEASE_SYMPTOMS[disease]:
        opts = SYM_OPTIONS.get(s, ["없음","조금","보통","심함"])
        if "직접입력" in " ".join(opts):
            val = st.text_input(f"{s} (값 입력)", value="")
        else:
            val = st.select_slider(s, options=opts, value=opts[0])
        picked[s] = val

    with st.expander("피수치 입력란 보기", expanded=False):
        lab_vals = {}
        colA, colB, colC = st.columns(3)
        for i, f in enumerate(LAB_FIELDS):
            c = [colA, colB, colC][i%3]
            v = c.number_input(f, value=0.0, step=0.1, format="%.2f")
            lab_vals[f] = None if v==0 else v

    st.subheader("해열제 자동 계산")
    cw1, cw2 = st.columns(2)
    w_kg = cw1.number_input("체중(kg)", value=10.0, step=0.5)
    t_c  = cw2.number_input("체온(°C)", value=38.3, step=0.1, format="%.1f")
    if st.button("해열 가이드 계산"):
        rr = calc_antipyretic_ml(w_kg, t_c)
        st.write(f"아세트아미노펜: **{rr['acet_ml']} mL** / 이부프로펜: **{rr['ibu_ml']} mL**")
        st.caption(rr["guide"])

    # 해석하기 (저장 없이도 가능)
    if st.button("해석하기"):
        msgs = interpret_basic(lab_vals)
        if msgs:
            st.markdown("**기본 해석**")
            for m in msgs: st.write("• " + m)
        else:
            st.write("입력된 피수치 기준 특이 소견이 없습니다.")

        # 특수검사/자동계산 예시
        c_ca = calc_corrected_ca(lab_vals.get("Ca"), lab_vals.get("Alb"))
        if c_ca:
            st.write(f"• 보정 칼슘(Alb 반영): **{c_ca} mg/dL**")

    st.divider()
    st.markdown(DISCLAIMER.replace("\n","  \n"))

# ---------- 암 진단 모드 ----------
else:
    st.subheader("암 카테고리 / 진단 / 단계")
    g1, g2, g3 = st.columns(3)
    grp = g1.selectbox("암 카테고리", CANCER_GROUPS)
    dx  = g2.selectbox("암 진단명", DX[grp])
    ph  = g3.selectbox("치료 단계(Phase)", PHASES)

    # 단계별 참고 목록 표시
    step = PHASED_TX.get(grp, {}).get(dx, {}).get(ph, {})
    step_regs = step.get("레지멘", [])
    step_chemo = step.get("항암제", [])
    step_targ  = step.get("표적치료제", [])
    if step_regs:
        st.caption("• 단계별 대표 레지멘: " + ", ".join([with_korean_drug(x) for x in step_regs]))

    st.markdown("### 항암제/표적치료제 선택")
    cc1, cc2 = st.columns(2)
    chemo_opts = [with_korean_drug(x) for x in step_chemo] or []
    targ_opts  = [with_korean_drug(x) for x in step_targ] or []
    chemo_sel = cc1.multiselect("항암제 (단계필터 적용)", chemo_opts, default=[])
    targ_sel  = cc2.multiselect("표적치료제 (단계필터 적용)", targ_opts,  default=[])

    st.markdown("**선택한 약의 용량·경로·주기는 반드시 직접 입력하세요.** (자동계산/권장치 없음)")
    inputs = []
    for label in chemo_sel + targ_sel:
        st.write(f"— {label}")
        colx, coly, colz = st.columns(3)
        dose = colx.text_input(f"용량 (예: 100 mg/m², mg 등) — {label}", key=f"dose_{label}")
        route = coly.text_input(f"투여경로 (예: IV/PO/SC) — {label}", key=f"route_{label}")
        cyc   = colz.text_input(f"주기 (예: q3w, 매주 등) — {label}", key=f"cycle_{label}")
        inputs.append({"drug":label, "dose":dose, "route":route, "cycle":cyc})

    with st.expander("암환자 흔용 항생제/주의 (참고)", expanded=False):
        st.write("• 발열성 호중구감소증 시 병원 지침에 따름(광범위 β-lactam 등).")
        st.write("• 신장/간 기능에 따른 용량 조절 및 상호작용 주의.")

    st.markdown("### 피수치 입력 (항상 표시)")
    lab_vals = {}
    colA, colB, colC = st.columns(3)
    for i, f in enumerate(LAB_FIELDS):
        c = [colA, colB, colC][i%3]
        v = c.number_input(f, value=0.0, step=0.1, format="%.2f", key=f"c_{f}")
        lab_vals[f] = None if v==0 else v

    # 특수검사(토글)
    with st.expander("특수검사 입력/자동계산", expanded=False):
        st.markdown("**지질**")
        l1,l2,l3,l4 = st.columns(4)
        tc  = l1.number_input("TC", 0.0, step=1.0)
        hdl = l2.number_input("HDL",0.0, step=1.0)
        tg  = l3.number_input("TG", 0.0, step=1.0)
        ldl = l4.number_input("LDL(직접, 선택)", 0.0, step=1.0)
        calc_ldl = calc_friedewald_ldl(tc, hdl, tg)
        non_hdl  = calc_non_hdl(tc, hdl)
        if calc_ldl: st.caption(f"Friedewald LDL ≈ **{calc_ldl} mg/dL**")
        if non_hdl:  st.caption(f"Non-HDL = **{non_hdl} mg/dL**")

        st.markdown("**응고/보체/갑상선/당대사**")
        c1,c2,c3,c4 = st.columns(4)
        inr = c1.number_input("INR", 0.0, step=0.1)
        aptt= c2.number_input("aPTT",0.0, step=0.1)
        c3v = c3.number_input("C3", 0.0, step=1.0)
        c4v = c4.number_input("C4", 0.0, step=1.0)
        c5,c6,c7,c8 = st.columns(4)
        tsh = c5.number_input("TSH", 0.0, step=0.1)
        ft4 = c6.number_input("FT4", 0.0, step=0.1)
        hba1c = c7.number_input("HbA1c(%)",0.0, step=0.1)
        insulin= c8.number_input("Insulin(μU/mL)",0.0, step=0.1)
        if lab_vals.get("Glu") and insulin:
            homa = calc_homa_ir(lab_vals["Glu"], insulin)
            if homa: st.caption(f"HOMA-IR ≈ **{homa}**")

        st.markdown("**신장/전해질 보정**")
        e1,e2,e3 = st.columns(3)
        egfr = calc_egfr(lab_vals.get("Cr"))
        cCa  = calc_corrected_ca(lab_vals.get("Ca"), lab_vals.get("Alb"))
        if egfr: e1.caption(f"eGFR ≈ **{egfr} mL/min/1.73m²**")
        if cCa:  e2.caption(f"보정 Ca ≈ **{cCa} mg/dL**")

        st.markdown("**요검사(정성)**")
        y1,y2,y3,y4 = st.columns(4)
        alb_u = y1.selectbox("알부민뇨","- + ++ +++".split(), index=0)
        hema_u= y2.selectbox("혈뇨","- + ++ +++".split(), index=0)
        glu_u = y3.selectbox("요당","- + ++ +++".split(), index=0)
        occult= y4.selectbox("잠혈","- + ++ +++".split(), index=0)

    # 해석하기(저장 불필요)
    st.markdown("### 해석하기")
    if st.button("결과 해석 생성"):
        msgs = interpret_basic(lab_vals)
        if msgs:
            for m in msgs: st.write("• " + m)
        # 지질/신장 등 특수 해석 예시
        if tg and tg >= 500:
            st.write(color_badge(f"TG {tg} mg/dL 매우 높음 → 췌장염 위험", "위험"))
        if egfr:
            stage = "G1 (정상/고정상)" if egfr >= 90 else ("G2" if egfr>=60 else ("G3" if egfr>=30 else "G4/5"))
            st.write(f"eGFR {egfr} → CKD {stage}")
        if cCa:
            st.write(f"보정 Ca {cCa} mg/dL")

        st.markdown("#### 식이가이드(요약)")
        st.write("• 단백질/열량 충분히, 위생 조리(특히 ANC 낮을 때).")
        st.write("• 철분 보충 필요 시 **비타민 C**와 함께 섭취하면 흡수 ↑.")
        st.warning("⚠️ 철분제와 비타민C를 함께 복용하면 흡수가 촉진됩니다.\n하지만 **항암 치료 중이거나 백혈병 환자**는 반드시 주치의와 상담 후 복용 여부를 결정해야 합니다.")

    # 저장/그래프
    st.markdown("### 저장/그래프")
    if nick_pin:
        if st.button("현재 입력 저장"):
            payload = {"time": now_ts()}
            payload.update({k:lab_vals.get(k) for k in LAB_FIELDS})
            payload["dx"]=dx; payload["phase"]=ph; payload["drugs"]=inputs
            save_record(nick_pin, payload)
            st.success("저장되었습니다.")
        if st.session_state["records"].get(nick_pin):
            st.line_chart(pd.DataFrame({
                "WBC": get_series(nick_pin,"WBC")[1],
                "Hb":  get_series(nick_pin,"Hb")[1],
                "PLT": get_series(nick_pin,"PLT")[1],
                "CRP": get_series(nick_pin,"CRP")[1],
                "ANC": get_series(nick_pin,"ANC")[1],
            }))
        else:
            st.caption("저장된 데이터가 없어요. (별명+PIN으로 저장 시 그래프 표시)")

    st.divider()
    st.markdown(DISCLAIMER.replace("\n","  \n"))
