# -*- coding: utf-8 -*-
# BloodMap — heme/lymph 한글진단명 + 별명#PIN 저장 + 그래프 확장판 (단일 파일)
# ⓐ 소아모드: 토글 입력 + 해열제 자동계산(1회 용량만 표기) ⓑ 암모드: 피수치 항상표시 + 한국어 병기
# ⓒ 암 카테고리 전부 포함(혈액암/림프종/고형암/육종/희귀암) ⓓ 보고서 md/txt ⓔ 별명#PIN 저장/불러오기/그래프

import os, json
from datetime import datetime, date
from typing import Dict, Any, List
import streamlit as st
import pandas as pd

# -----------------------------
# 기본 설정
# -----------------------------
APP_TITLE  = "피수치 가이드 (BloodMap)"
PAGE_TITLE = "BloodMap"
MADE_BY    = "제작: Hoya/GPT · 자문: Hoya/GPT"
CAFE_LINK  = "[피수치 가이드 공식카페](https://cafe.naver.com/bloodmap)"
DISCLAIMER = (
    "본 수치는 참고용이며, 해석 결과는 개발자와 무관합니다.  "
    "약 변경, 복용 중단 등은 반드시 주치의와 상의 후 결정하시기 바랍니다.  "
    "이 앱은 개인정보를 수집하지 않으며, 어떠한 개인정보 입력도 요구하지 않습니다."
)
FEVER_GUIDE = "38.0~38.5℃: 해열제/경과관찰 · 38.5~39.0℃: 해열제+병원 연락 고려 · 39.0℃ 이상: 즉시 병원"

RECORDS_PATH = "records.json"   # 간단 보관(로컬). 배포 환경에서는 재시작 시 초기화될 수 있음.

# 피수치 표시 순서(약어 기준)
ORDER = ["WBC","Hb","PLT","ANC","Ca","P","Na","K","Alb","Glu","TP",
         "AST","ALT","LDH","CRP","Cr","UA","TB","BUN","BNP"]

# 약어→한글 병기
KR = {
    "WBC":"백혈구", "Hb":"혈색소", "PLT":"혈소판", "ANC":"호중구",
    "Ca":"칼슘", "P":"인", "Na":"소디움", "K":"포타슘",
    "Alb":"알부민", "Glu":"혈당", "TP":"총단백",
    "AST":"AST(간 효소)", "ALT":"ALT(간세포)", "LDH":"LDH",
    "CRP":"CRP(염증)", "Cr":"크레아티닌", "UA":"요산",
    "TB":"총빌리루빈", "BUN":"BUN", "BNP":"BNP",
}
def label(abbr: str) -> str:
    return f"{abbr} ({KR.get(abbr, abbr)})"

# -----------------------------
# 데이터 저장/불러오기
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
# 암종/치료 매핑 (요약)
# -----------------------------
# 혈액암: 한글 병기 표기 → 내부 키로 매핑
HEME_DISPLAY = [
    "급성 골수성 백혈병(AML)", "급성 전골수구성 백혈병(APL)", "급성 림프모구성 백혈병(ALL)",
    "만성 골수성 백혈병(CML)", "만성 림프구성 백혈병(CLL)", "다발골수종(Multiple Myeloma)",
    "골수이형성증후군(MDS)", "골수증식성 종양(MPN)"
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

HEME_DRUGS = {
    "AML": ["7+3(Cytarabine+Anthracycline)","Azacitidine+Venetoclax","Midostaurin(FLT3)","Gilteritinib(FLT3, R/R)"],
    "APL": ["ATRA(베사노이드)","ATO","6-MP","MTX"],
    "ALL": ["Hyper-CVAD","Blinatumomab(CD19)","Inotuzumab(CD22)"],
    "CML": ["Imatinib","Dasatinib","Nilotinib","Bosutinib","Ponatinib"],
    "CLL": ["Ibrutinib","Acalabrutinib","Venetoclax+Obinutuzumab"],
    "MM":  ["VRd(보르테조밉+레날리도마이드+덱사)","Daratumumab+VRd","Carfilzomib+Dexamethasone"],
    "MDS": ["Azacitidine","Decitabine","Luspatercept(저위험 빈혈)"],
    "MPN": ["Hydroxyurea","Ruxolitinib","Ropeginterferon alfa-2b(PV)"],
}

# 림프종: 한글 병기 표기 → 내부 키로 매핑
LYMPH_DISPLAY = [
    "미만성 거대 B세포 림프종(DLBCL)",
    "원발 종격동 B세포 림프종(PMBCL)",
    "여포성 림프종 1-2등급(FL 1-2)",
    "여포성 림프종 3A(FL 3A)",
    "여포성 림프종 3B(FL 3B)",
    "외투세포 림프종(MCL)",
    "변연대 림프종(MZL)",
    "고등급 B세포 림프종(HGBL)",
    "버킷 림프종(Burkitt)",
    "고전적 호지킨 림프종(cHL)",
    "말초 T세포 림프종(PTCL-NOS)",
    "비강형 NK/T 세포 림프종(ENKTL)"
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
LYMPH_DRUGS = {
    "DLBCL": ["R-CHOP","Pola-R-CHP","DA-EPOCH-R","R-ICE","R-DHAP","R-GDP","R-GemOx"],
    "PMBCL": ["DA-EPOCH-R","R-ICE","R-DHAP","Pembrolizumab"],
    "FL12":  ["BR","R-CVP","R-CHOP","Obinutuzumab+BR","Lenalidomide+Rituximab"],
    "FL3A":  ["R-CHOP","Pola-R-CHP","BR"],
    "FL3B":  ["R-CHOP","Pola-R-CHP","DA-EPOCH-R"],
    "MCL":   ["BR","R-CHOP","Ibrutinib","Acalabrutinib","Zanubrutinib","R-ICE","R-DHAP"],
    "MZL":   ["BR","R-CVP","R-CHOP"],
    "HGBL":  ["DA-EPOCH-R","R-CHOP","Pola-R-CHP","R-ICE","R-DHAP"],
    "BL":    ["CODOX-M/IVAC-R","Hyper-CVAD-R","R-ICE"],
    "cHL":   ["ABVD","BV-AVD","ICE(구제)","DHAP(구제)","Nivolumab/Pembrolizumab(R/R)"],
    "PTCL":  ["CHOP/CHOEP","Pralatrexate(R/R)","Romidepsin(R/R)"],
    "ENKTL": ["SMILE","Aspa 기반 요법","RT 병합"],
}

# 고형암/육종/희귀암은 생략 없이 카테고리 유지(간단 셀렉트만. 필요 시 확장 가능)
SOLID_DISPLAY = [
    "폐선암(Lung Adenocarcinoma)","NSCLC 편평(Lung Squamous)","SCLC(소세포폐암)",
    "유방암 HR+","유방암 HER2+","삼중음성유방암(TNBC)",
    "위암(Gastric)","대장암(Colorectal)","췌장암(Pancreatic)",
    "간세포암(HCC)","담관암(Cholangiocarcinoma)","신장암(RCC)",
    "난소암(Ovarian)","자궁경부암(Cervical)","자궁내막암(Endometrial)",
    "두경부암 Head&Neck SCC","식도암(Esophageal)","역형성갑상선암(ATC)"
]
SARCOMA_DISPLAY = [
    "UPS(미분화 다형성)","LMS(평활근)","LPS(지방)","Synovial Sarcoma","Ewing Sarcoma","Rhabdomyosarcoma","Angiosarcoma","DFSP","GIST"
]
RARE_DISPLAY = [
    "GIST(지스트)","NET(신경내분비종양)","Medullary Thyroid(수질갑상선암)","Pheochromocytoma/Paraganglioma",
    "Uveal Melanoma","Merkel Cell(메르켈세포)"
]

def get_drug_list(group: str, dx_label: str) -> List[str]:
    if not group or not dx_label: return []
    if group == "혈액암":
        return HEME_DRUGS.get(HEME_KEY.get(dx_label, dx_label), [])
    if group == "림프종":
        return LYMPH_DRUGS.get(LYMPH_KEY.get(dx_label, dx_label), [])
    # 고형암/육종/희귀암 — 요약(필요 시 확장)
    if group == "고형암" and dx_label:
        if dx_label.startswith("폐선암"): return ["Platinum+Pemetrexed","Osimertinib(EGFR)","Alectinib(ALK)"]
        if "NSCLC 편평" in dx_label: return ["Platinum+Taxane","Pembrolizumab(PD-L1)"]
        if "SCLC" in dx_label: return ["Platinum+Etoposide","Atezolizumab 병용"]
        if "유방암 HR+" in dx_label: return ["AI/Tamoxifen + CDK4/6i","Fulvestrant"]
        if "유방암 HER2+" in dx_label: return ["Trastuzumab+Pertuzumab+Taxane","T-DM1","T-DXd"]
        if "TNBC" in dx_label: return ["Paclitaxel","Pembrolizumab(PD-L1+)","Sacituzumab govitecan"]
        if "대장암" in dx_label: return ["FOLFOX","FOLFIRI","Bevacizumab","Cetuximab(RAS WT)"]
        if "위암" in dx_label: return ["FOLFOX/XP","Trastuzumab(HER2+)","Nivolumab/Pembrolizumab"]
        if "췌장암" in dx_label: return ["FOLFIRINOX","Gemcitabine+nab-Paclitaxel"]
        if "HCC" in dx_label: return ["Atezolizumab+Bevacizumab","Lenvatinib","Sorafenib"]
        if "담관암" in dx_label: return ["Gemcitabine+Cisplatin","Pemigatinib(FGFR2)","Ivosidenib(IDH1)"]
        if "RCC" in dx_label: return ["Pembrolizumab+Axitinib","Nivolumab+Ipilimumab","Cabozantinib"]
    if group == "육종" and dx_label:
        if "UPS" in dx_label: return ["Doxorubicin","Ifosfamide","Trabectedin","Pazopanib"]
        if "LMS" in dx_label: return ["Doxorubicin","Ifosfamide","Gemcitabine+Docetaxel","Pazopanib"]
        if "LPS" in dx_label: return ["Doxorubicin","Ifosfamide","Eribulin","Trabectedin"]
        if "Synovial" in dx_label: return ["Ifosfamide","Doxorubicin","Pazopanib"]
        if "Ewing" in dx_label: return ["VDC/IE","Ifosfamide+Etoposide"]
        if "Rhabdo" in dx_label: return ["VAC/IVA","Ifosfamide+Etoposide"]
        if "DFSP" in dx_label: return ["Imatinib"]
        if "GIST" in dx_label: return ["Imatinib","Sunitinib(2차)","Regorafenib(3차)"]
    if group == "희귀암" and dx_label:
        if dx_label.startswith("GIST"): return ["Imatinib","Sunitinib","Regorafenib"]
        if dx_label.startswith("NET"): return ["Octreotide/Lanreotide","Everolimus","Sunitinib(췌장NET)"]
        if "Medullary" in dx_label: return ["Selpercatinib/Pralsetinib(RET)","Vandetanib","Cabozantinib"]
        if "Merkel" in dx_label: return ["Avelumab","Pembrolizumab"]
    return []

# -----------------------------
# 유틸
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

# 간단 해석(보호자용 톤)
def interpret_labs(v: Dict[str, Any]) -> List[str]:
    out = []
    g = lambda k: v.get(k)
    if entered(g("WBC")):
        if g("WBC") < 3.0: out.append("WBC 낮음 → 🟡 감염 주의(손 위생·마스크·혼잡 피하기)")
        elif g("WBC") > 11.0: out.append("WBC 높음 → 🟡 염증/감염 가능성")
    if entered(g("Hb")):
        if g("Hb") < 8.0: out.append("Hb 낮음 → 🟠 증상 주의/필요 시 수혈 의논")
        elif g("Hb") < 10.0: out.append("Hb 경도 감소 → 🟡 경과관찰")
    if entered(g("PLT")) and g("PLT") < 50:
        out.append("혈소판 낮음 → 🟥 멍/출혈 주의, 넘어짐·양치 시 조심(필요 시 수혈 의논)")
    if entered(g("ANC")):
        if g("ANC") < 500:
            out.append("ANC 매우 낮음 → 🟥 생채소 금지·익힌 음식·남은 음식 2시간 지나면 비권장·껍질 과일 상담")
        elif g("ANC") < 1000:
            out.append("ANC 낮음 → 🟠 감염 위험↑, 외출/위생 관리")
    if entered(g("AST")) and g("AST") >= 50: out.append("AST 상승 → 🟡 간 기능 저하 가능")
    if entered(g("ALT")) and g("ALT") >= 55: out.append("ALT 상승 → 🟡 간세포 손상 의심")
    if entered(g("Alb")) and g("Alb") < 3.5: out.append("알부민 낮음 → 🟡 영양 보강 권장")
    if entered(g("Cr")) and g("Cr") > 1.2: out.append("Cr 상승 → 🟡 신장 기능 저하 가능")
    if entered(g("CRP")) and g("CRP") >= 0.5: out.append("CRP 상승 → 🟡 염증/감염 활동 가능성")
    return out

# 소아 해열제 1회 용량
def pediatric_antipyretic(weight_kg: float, temp_c: float) -> List[str]:
    if not weight_kg or weight_kg <= 0:
        return ["체중을 먼저 입력하세요."]
    ac_min = 10 * weight_kg
    ac_max = 15 * weight_kg
    ib = 10 * weight_kg
    zone = "체온 미입력"
    if temp_c:
        if 38.0 <= temp_c < 38.5: zone = "38.0~38.5℃: 해열제 고려/경과관찰"
        elif 38.5 <= temp_c < 39.0: zone = "38.5~39.0℃: 해열제 + 병원 연락 고려"
        elif temp_c >= 39.0: zone = "39.0℃ 이상: 즉시 병원 권고"
    return [
        f"[해열 가이드] {zone}",
        f"아세트아미노펜: 1회 {ac_min:.0f}~{ac_max:.0f} mg (4~6시간 간격, 최대 5회/일)",
        f"이부프로펜: 1회 약 {ib:.0f} mg (6~8시간 간격, 최대 4회/일)",
        FEVER_GUIDE
    ]

# 보고서(Markdown)
def build_report_md(nick_pin: str, dt: date, mode: str, group: str, dx: str,
                    lab_values: Dict[str, Any], lab_notes: List[str], drug_list: List[str]) -> str:
    L = []
    L.append(f"# {APP_TITLE}\n")
    L.append(f"- 사용자: {nick_pin}  ")
    L.append(f"- 검사일: {dt.isoformat()}  ")
    L.append(f"- 모드: {mode}  ")
    if mode == "암 진단 모드":
        L.append(f"- 암 그룹/진단: {group} / {dx}  ")
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
    if drug_list and mode == "암 진단 모드":
        L.append("## 관련 항암제/치료 (요약)")
        for d in drug_list: L.append(f"- {d}")
        L.append("")
    L.append("---")
    L.append(MADE_BY)
    L.append(CAFE_LINK)
    L.append("")
    L.append("```")
    L.append(DISCLAIMER)
    L.append("```")
    return "\n".join(L)

# -----------------------------
# UI 시작
# -----------------------------
st.set_page_config(page_title=PAGE_TITLE, layout="centered")
st.title(APP_TITLE)
st.caption(MADE_BY)
st.markdown(CAFE_LINK)

# 세션 상태 준비
if "used_keys" not in st.session_state: st.session_state.used_keys = set()
if "store" not in st.session_state:     st.session_state.store = load_records()

# 사용자 식별
st.subheader("사용자 식별")
c1, c2 = st.columns([2,1])
nickname = c1.text_input("별명", placeholder="예: 민수아빠")
pin      = c2.text_input("PIN(4자리)", max_chars=4, placeholder="예: 1234")
pin_clean = "".join([c for c in (pin or "") if c.isdigit()])[:4]
nick_key  = f"{nickname.strip()}#{pin_clean}" if nickname and pin_clean else ""
if nick_key:
    if nick_key in st.session_state.used_keys:
        st.warning("이미 사용 중인 별명+PIN 조합입니다. (동일 세션 내 중복 방지)")
    else:
        st.session_state.used_keys.add(nick_key)

test_date = st.date_input("검사 날짜", value=date.today())

# 모드
mode = st.radio("진단 모드", ["소아 일상/질환", "암 진단 모드"], horizontal=True)

# 피수치 입력
def lab_inputs(always_show: bool) -> Dict[str, Any]:
    vals: Dict[str, Any] = {}
    show = True if always_show else st.toggle("피수치 입력란 보기", value=False)
    if not show: return {}
    for abbr in ORDER:
        raw = st.text_input(label(abbr), placeholder=f"{label(abbr)} 값 입력")
        val = parse_float(raw)
        if val is not None:
            vals[abbr] = val
    return vals

drug_list = []
group = ""; dx = ""
labs: Dict[str, Any] = {}

if mode == "소아 일상/질환":
    st.info("소아 감염/일상 중심: 항암제는 숨김 처리됩니다.")
    labs = lab_inputs(always_show=False)
    st.markdown("### 해열제 자동 계산")
    cw, ct = st.columns(2)
    wt = parse_float(cw.text_input("체중(kg)", placeholder="예: 20.5"))
    tc = parse_float(ct.text_input("체온(℃)",  placeholder="예: 38.2"))
    if st.button("해열 가이드 계산"):
        for m in pediatric_antipyretic(wt or 0.0, tc or 0.0):
            st.write("• " + m)

else:
    st.success("암 진단 모드: 피수치 입력란이 항상 표시됩니다.")
    c1, c2 = st.columns(2)
    group = c1.selectbox("암 그룹", ["","혈액암","림프종","고형암","육종","희귀암"], index=0)
    if group == "혈액암":
        dx = c2.selectbox("혈액암(진단명)", HEME_DISPLAY, index=0)
    elif group == "림프종":
        dx = c2.selectbox("림프종(진단명)", LYMPH_DISPLAY, index=0)
    elif group == "고형암":
        dx = c2.selectbox("고형암(진단명)", SOLID_DISPLAY, index=0)
    elif group == "육종":
        dx = c2.selectbox("육종(진단명)", SARCOMA_DISPLAY, index=0)
    elif group == "희귀암":
        dx = c2.selectbox("희귀암(진단명)", RARE_DISPLAY, index=0)
    else:
        dx = ""
    labs = lab_inputs(always_show=True)
    drug_list = get_drug_list(group, dx)
    if drug_list:
        st.markdown("### 관련 항암제/치료 (요약)")
        for d in drug_list: st.markdown(f"- {d}")

st.divider()

# 저장/해석
colA, colB = st.columns([1,1])
run_analyze = colA.button("🔎 해석하기 & 저장", use_container_width=True)
clear_user  = colB.button("🗑️ 이 사용자 기록 전체 삭제", use_container_width=True)

# 사용자 전체 삭제
if clear_user and nick_key:
    st.session_state.store.pop(nick_key, None)
    save_records(st.session_state.store)
    st.success("이 사용자 기록을 모두 삭제했습니다.")

if run_analyze:
    if not nick_key:
        st.warning("별명과 PIN(숫자 4자리)을 먼저 입력해주세요.")
    else:
        notes = interpret_labs(labs)
        if notes:
            st.subheader("해석 요약")
            for m in notes: st.write("• " + m)
        # 보고서
        report_md = build_report_md(nick_key, test_date, mode, group, dx, labs, notes, drug_list)
        st.download_button("📥 보고서(.md) 다운로드", data=report_md.encode("utf-8"),
                           file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                           mime="text/markdown")
        st.download_button("📄 보고서(.txt) 다운로드", data=report_md.encode("utf-8"),
                           file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                           mime="text/plain")

        # 저장(세션+파일)
        rec = {
            "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "date": test_date.isoformat(),
            "mode": mode,
            "group": group,
            "dx": dx,
            "labs": {k: labs.get(k) for k in ORDER if entered(labs.get(k))}
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
        # DataFrame 구성
        df_rows = []
        for r in user_records:
            row = {"date": r.get("date")}
            for k in ORDER:
                v = (r.get("labs") or {}).get(k)
                row[k] = v if entered(v) else None
            df_rows.append(row)
        df = pd.DataFrame(df_rows)
        try:
            df["date"] = pd.to_datetime(df["date"])
        except Exception:
            pass
        df = df.sort_values("date")

        st.caption("기본 지표: WBC, Hb, PLT, CRP, ANC")
        metric_sel = st.multiselect(
            "그래프에 표시할 항목 선택",
            ["WBC","Hb","PLT","CRP","ANC"] + [x for x in ORDER if x not in ["WBC","Hb","PLT","CRP","ANC"]],
            default=["WBC","Hb","PLT","CRP","ANC"]
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

        # 이전 기록 불러오기(폼 채우기)
        if st.button("↩️ 가장 최근 기록으로 폼 채우기"):
            last = user_records[-1]
            labs_last = last.get("labs", {})
            for abbr, val in labs_last.items():
                # 텍스트 입력값은 세션 상태 키가 label()이 아니라 약어 그대로로 구성돼 있어 아래처럼 접근
                for prefix in ("",):  # 단일 입력
                    key = f"{abbr}"
                    if key in st.session_state:
                        st.session_state[key] = str(val)
            st.success("최근 기록을 폼에 반영했습니다. (입력란 확인)")

st.markdown("---")
st.markdown(f"_{MADE_BY}_")
st.markdown(CAFE_LINK)
st.code(DISCLAIMER, language="text")
