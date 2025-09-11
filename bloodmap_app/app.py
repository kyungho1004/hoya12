# -*- coding: utf-8 -*-
"""
BloodMap / 피수치 해석기 - 단일파일 버전(app.py)
- 한국시간(KST) 기준
- 소아 일상/질환 모드: 증상 → 간단 예측병명 + 해열제 1회분(mL) 자동계산(1일 최대표기 없음)
- 암 진단 모드: [혈액암/고형암/육종/희귀암/림프종] + 진단 → 항암제/표적치료제/항생제 & 부작용 '강조' 표기
- 피수치 입력: 암 모드에서 항상 노출(소아는 토글로 노출)
- 특수검사(정성/정량) 토글 + 색상 해석
- 결과 저장: .md, .txt
- 별명+PIN(4자리) 중복 방지(세션 범위)
- '세포·면역 치료(예: CAR-T 등)'는 혼돈 방지를 위해 화면에 표기하지 않음(고정 안내)
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
from io import StringIO

# =========================
# 전역 상수/문구
# =========================
APP_VERSION = "v3.0-mini"
KST = timezone(timedelta(hours=9))
MADE_BY = "제작: Hoya/GPT  ·  자문: Hoya/GPT"
DISCLAIMER = (
    "본 수치는 참고용이며, 해석 결과는 개발자와 무관합니다.\n"
    "약 변경, 복용 중단 등은 반드시 주치의와 상의 후 결정하시기 바랍니다.\n"
    "이 앱은 개인정보를 절대 수집하지 않으며, 어떠한 개인정보 입력도 요구하지 않습니다."
)
CAFE_LINK_MD = "[피수치 가이드 공식카페](https://naver.me/xxxxxx)  ·  [웹앱 QR/블로그 안내](https://naver.me/yyyyyy)"

# 세포치료 고정 안내 (모든 화면에 노출)
IMMUNO_BANNER = "혼돈 방지 및 범위 밖 안내: 저희는 **세포·면역 치료(CAR-T, TCR-T, NK, HSCT 등)** 는 표기하지 않습니다."

# =========================
# 유틸
# =========================
def now_kst_str():
    return datetime.now(KST).strftime("%Y-%m-%d %H:%M (KST)")

def clean_num(x):
    try:
        if x is None or x == "":
            return None
        return float(str(x).replace(",", "").strip())
    except Exception:
        return None

def round_step(x: float, step: float = 0.5):
    if x is None:
        return None
    return round(x / step) * step

def nickname_pin_key(nick: str, pin: str) -> str:
    n = (nick or "").strip()
    p = (pin or "").strip()
    return f"{n}#{p}"

# 온도 구간 표기
def temp_band(temp_c: float) -> str:
    if temp_c is None:
        return "입력없음"
    if temp_c < 38.0:
        return "38.0도 미만"
    if 38.0 <= temp_c < 38.5:
        return "38.0~38.5도"
    if 38.5 <= temp_c < 39.0:
        return "38.5~39.0도"
    return "39.0도 이상"

# =========================
# 소아 증상 옵션(안전 기본값)
# =========================
PEDS_SYMPTOMS_DEFAULT = {
    "콧물": ["없음", "투명", "흰색", "누런", "피섞임"],
    "기침": ["없음", "조금", "보통", "심함"],
    "설사": ["없음", "1~2회", "3~4회", "5~6회"],
    "발열": ["없음", "37~37.5 (미열)", "37.5~38 (병원 내원 권장)", "38.5~39 (병원/응급실)"],
}

PEDS_DISEASES = [
    "일상 감기/상기도염", "RSV", "아데노", "로타", "노로", "장염",
    "독감", "편도염", "코로나", "중이염"
]

def get_symptom_options_safe(disease: str):
    # (간단 맵 – 실제 프로필이 깨져있어도 안전동작)
    d = (disease or "").strip()
    base = PEDS_SYMPTOMS_DEFAULT.copy()
    if d in {"로타","노로","장염"}:
        base["설사"] = ["1~2회", "3~4회", "5~6회"]
    if d in {"RSV","아데노","중이염"}:
        base["콧물"] = ["투명","흰색","누런"]
    if d in {"독감","편도염","코로나"}:
        base["발열"] = ["37~37.5 (미열)", "37.5~38 (병원 내원 권장)", "38.5~39 (병원/응급실)"]
    return base

# =========================
# 소아 해열제 1회분(mL) 계산
# =========================
# - 아세트아미노펜: 10~15 mg/kg → 12.5 mg/kg 기준, 시럽 160mg/5mL → 32 mg/mL
# - 이부프로펜: 10 mg/kg, 시럽 100mg/5mL → 20 mg/mL
def acetaminophen_ml(weight_kg: float) -> float:
    if not weight_kg or weight_kg <= 0:
        return 0.0
    mg = 12.5 * weight_kg
    ml = mg / 32.0
    return round_step(ml, 0.5)

def ibuprofen_ml(weight_kg: float) -> float:
    if not weight_kg or weight_kg <= 0:
        return 0.0
    mg = 10.0 * weight_kg
    ml = mg / 20.0
    return round_step(ml, 0.5)

# =========================
# DRUG DB (요약 – 한글 병기/기전/부작용)
# =========================
DRUG_DB = {}
def _upsert(db, key, alias, moa, ae):
    keyn = (key or "").strip()
    db.setdefault(keyn, {})
    db[keyn].update({"alias": alias, "moa": moa, "ae": ae})
    # 쉬운 조회용 별칭키도 등록
    for alt in {keyn, keyn.lower(), alias, alias.lower()}:
        db.setdefault(alt, {"alias": alias, "moa": moa, "ae": ae})

# 핵심(요구사항 커버 중심)
_upsert(DRUG_DB, "ATRA", "트레티노인(베사노이드, ATRA)",
        "분화유도(RAR) → APL 치료 핵심",
        "분화증후군(발열·호흡곤란·부종), 간효소 상승, 두통/피부증상")
_upsert(DRUG_DB, "Arsenic Trioxide", "아르세닉 트리옥사이드(ATO)",
        "분화유도/세포사멸",
        "QT 연장, 전해질 이상, 간효소 상승")
_upsert(DRUG_DB, "Idarubicin", "이다루비신(안트라사이클린)",
        "Topoisomerase II 억제",
        "골수억제, 구내염, 심장독성(누적용량)")
_upsert(DRUG_DB, "MTX", "메토트렉세이트(MTX)",
        "엽산경로 억제",
        "간효소 상승, 점막염/구내염, 골수억제, 신독성(고용량), 광과민성")
_upsert(DRUG_DB, "6-MP", "6-머캅토퓨린(6-MP)",
        "푸린 대사 억제",
        "골수억제, 간독성, 발열/피로")
_upsert(DRUG_DB, "Ara-C", "시타라빈(Ara-C)",
        "핵산합성 억제",
        "골수억제, 발열반응, 결막염/피부발진(고용량), 신경독성(HDAC)")
_upsert(DRUG_DB, "G-CSF", "그라신(G-CSF)",
        "호중구 증식 촉진",
        "골/근육통, 주사부위 반응, 드물게 비장비대/파열")

_upsert(DRUG_DB, "Vincristine", "빈크리스틴(VCR)", "미세소관 억제", "말초신경병증, 변비")
_upsert(DRUG_DB, "Cyclophosphamide", "사이클로포스파마이드", "알킬화제", "골수억제, 출혈성 방광염(수분/메스나)")
_upsert(DRUG_DB, "Daunorubicin", "다우노루비신", "Topo-II 억제", "골수억제, 심독성")
_upsert(DRUG_DB, "Doxorubicin", "독소루비신", "Topo-II 억제", "골수억제, 심독성, 탈모")
_upsert(DRUG_DB, "Prednisone", "프레드니손", "스테로이드", "고혈당/불면/기분변화, 위장관 증상")
_upsert(DRUG_DB, "Rituximab", "리툭시맙(CD20)", "CD20 단일클론항체", "주입반응, HBV 재활성화")
_upsert(DRUG_DB, "Imatinib", "이매티닙(BCR-ABL/c-KIT)", "TKI", "부종/발진, 간효소 상승, 골수억제")
_upsert(DRUG_DB, "Trastuzumab", "트라스투주맙(HER2)", "HER2 항체", "심기능저하(LVEF 감소), 주입반응")
_upsert(DRUG_DB, "Bevacizumab", "베바시주맙(VEGF)", "VEGF 억제", "고혈압, 단백뇨, 상처치유 지연/출혈")
_upsert(DRUG_DB, "Paclitaxel", "파클리탁셀", "미세소관 안정화", "말초신경병증, 과민반응(전처치), 골수억제")
_upsert(DRUG_DB, "Gemcitabine", "젬시타빈", "핵산합성 억제", "골수억제, 발열, 피로")
_upsert(DRUG_DB, "Pemetrexed", "페메트렉시드", "엽산경로 억제", "골수억제, 발진 · 엽산/B12 보충 필요")
_upsert(DRUG_DB, "Everolimus", "에버롤리무스(mTOR)", "mTOR 억제", "구내염, 고혈당/고지혈, 감염")
_upsert(DRUG_DB, "Octreotide", "옥트레오타이드", "소마토스타틴 유사체", "위장관 증상, 담석, 혈당변동")
_upsert(DRUG_DB, "Sunitinib", "수니티닙", "멀티 TKI", "고혈압, 수족증후군, 갑상선기능저하")

# 감염/발열 항생제(일반인 설명용)
_upsert(DRUG_DB, "Cefepime", "세페핌(주사)", "광범위 세팔로스포린", "설사/발진, 드물게 신경증상")
_upsert(DRUG_DB, "Piperacillin/Tazobactam", "타조신(주사)", "항녹농균 β-락탐+억제제", "설사/발진, 간효소 상승")
_upsert(DRUG_DB, "Meropenem", "메로페넴(주사)", "카바페넴", "구역/설사, 드물게 경련")
_upsert(DRUG_DB, "Vancomycin", "반코마이신(주사)", "글라이코펩티드", "주입반응, 신독성(농도모니터링)")

# =========================
# 진단 → 자동 예시 레지멘
# =========================
ONCO_MAP = {
    "혈액암": {
        "APL": {"chemo": ["ATRA","Arsenic Trioxide","Idarubicin","MTX","6-MP"], "targeted": [], "abx": []},
        "AML": {"chemo": ["Ara-C","Daunorubicin","Idarubicin"], "targeted": [], "abx": []},
        "ALL": {"chemo": ["Vincristine","Ara-C","MTX","6-MP","Cyclophosphamide","Prednisone"], "targeted": [], "abx": []},
        "CML": {"chemo": [], "targeted": ["Imatinib"], "abx": []},
        "CLL": {"chemo": ["Cyclophosphamide","Prednisone"], "targeted": ["Rituximab"], "abx": []},
        "PCNSL": {"chemo": ["MTX","Ara-C"], "targeted": ["Rituximab"], "abx": []},
    },
    "림프종": {
        "DLBCL": {"chemo": ["Cyclophosphamide","Doxorubicin","Vincristine","Prednisone"], "targeted": ["Rituximab"], "abx": []},
        "BL": {"chemo": ["Cyclophosphamide","Doxorubicin","Vincristine","MTX","Ara-C"], "targeted": ["Rituximab"], "abx": []},
        "FL": {"chemo": ["Cyclophosphamide","Doxorubicin","Vincristine","Prednisone"], "targeted": ["Rituximab"], "abx": []},
        "cHL": {"chemo": ["Doxorubicin","Vinblastine","Dacarbazine","Bleomycin"], "targeted": [], "abx": []},
    },
    "고형암": {
        "폐선암": {"chemo": ["Pemetrexed","Carboplatin","Paclitaxel"], "targeted": ["Bevacizumab","Trastuzumab"], "abx": []},
        "유방암": {"chemo": ["Doxorubicin","Cyclophosphamide","Paclitaxel"], "targeted": ["Trastuzumab"], "abx": []},
        "위암": {"chemo": ["Cisplatin","Fluorouracil","Paclitaxel"], "targeted": ["Trastuzumab"], "abx": []},
        "대장암": {"chemo": ["Oxaliplatin","Fluorouracil"], "targeted": ["Bevacizumab"], "abx": []},
        "간세포암": {"chemo": [], "targeted": ["Everolimus"], "abx": []},
        "담도암": {"chemo": ["Gemcitabine","Cisplatin"], "targeted": [], "abx": []},
        "췌장암": {"chemo": ["Gemcitabine"], "targeted": [], "abx": []},
        "난소암": {"chemo": ["Carboplatin","Paclitaxel"], "targeted": [], "abx": []},
    },
    "육종": {
        "골육종(OS)": {"chemo": ["Doxorubicin","Cisplatin","High-dose MTX"], "targeted": [], "abx": []},
        "유잉육종(ES)": {"chemo": ["Vincristine","Doxorubicin","Cyclophosphamide"], "targeted": [], "abx": []},
        "평활근육종(LMS)": {"chemo": ["Doxorubicin","Ifosfamide"], "targeted": [], "abx": []},
        "지방육종(LPS)": {"chemo": ["Doxorubicin","Ifosfamide"], "targeted": [], "abx": []},
    },
    "희귀암": {
        "GIST": {"chemo": [], "targeted": ["Imatinib"], "abx": []},
        "NET": {"chemo": [], "targeted": ["Everolimus","Octreotide"], "abx": []},
        "MTC": {"chemo": [], "targeted": ["Sunitinib"], "abx": []},
    }
}

def auto_recs_by_dx(group: str, dx: str):
    g = (group or "").strip()
    d = (dx or "").strip()
    data = (ONCO_MAP.get(g) or {}).get(d) or {}
    return {
        "chemo": data.get("chemo", []),
        "targeted": data.get("targeted", []),
        "abx": data.get("abx", []),
    }

# =========================
# 결과 게이트 & 부작용 렌더러
# =========================
def results_only_after_analyze(st) -> bool:
    if st.session_state.get("analyzed"):
        st.divider()
        st.markdown("## 결과")
        st.caption("아래에는 피수치 해석과 식이가이드, 약물 부작용만 표시합니다.")
        return True
    return False

def render_adverse_effects(st, regimen, db):
    if not regimen:
        st.write("- (선택된 약물이 없습니다)")
        return
    st.markdown("#### 💊 약물 부작용(요약)")
    for key in regimen:
        info = (db or {}).get(key) or (db or {}).get(str(key).lower()) or (db or {}).get(str(key).strip())
        if not info:
            st.write(f"- {key}: 데이터 없음")
            continue
        alias, moa, ae = info.get("alias", key), info.get("moa", ""), info.get("ae", "")
        st.write(f"- **{key} ({alias})**")
        if moa: st.caption(f"  · 기전/특징: {moa}")
        if ae:  st.caption(f"  · 주의/부작용: {ae}")

# =========================
# 피수치 입력/해석
# =========================
LABS_ORDER = [
    ("WBC","WBC(백혈구)"), ("Hb","Hb(혈색소)"), ("PLT","혈소판"), ("ANC","ANC(절대호중구,면역력)"),
    ("Ca","Ca(칼슘)"), ("P","P(인)"), ("Na","Na(나트륨,소디움)"), ("K","K(칼륨)"), ("Alb","Albumin(알부민)"),
    ("Glu","Glucose(혈당)"), ("TP","Total Protein(총단백)"), ("AST","AST(간수치)"), ("ALT","ALT(간세포)"),
    ("LDH","LDH"), ("CRP","CRP(C-반응성단백,염증)"), ("Cr","Cr(크레아티닌,신장)"),
    ("UA","UA(요산)"), ("TB","TB(총빌리루빈)"), ("BUN","BUN(요소질소)")
]

# 간단 정상범위(참고치) – 병원마다 다를 수 있음(안전한 폭으로 제시)
RANGE = {
    "WBC": (4.0, 10.0), "Hb": (12.0, 16.0), "PLT": (150, 450), "ANC": (1.5, 8.0),
    "Na": (135, 145), "K": (3.5, 5.1), "Ca": (8.6, 10.2), "P": (2.5, 4.5), "Alb": (3.5, 5.2),
    "Glu": (70, 140), "TP": (6.0, 8.3), "AST": (0, 40), "ALT": (0, 55), "LDH": (0, 250),
    "CRP": (0, 0.5), "Cr": (0.5, 1.2), "UA": (3.5, 7.2), "TB": (0.2, 1.2), "BUN": (7, 20)
}

def lab_flag(name, val):
    if val is None: return ("⚪", "입력없음")
    lo, hi = RANGE.get(name, (None, None))
    if lo is None: return ("⚪", "기준없음")
    if val < lo: return ("🟡", "낮음")
    if val > hi: return ("🟡", "높음")
    return ("🟢", "정상")

def interpret_labs(labs: dict):
    out = []
    for k, _label in LABS_ORDER:
        v = labs.get(k)
        if v is None: continue  # 입력한 수치만 결과에 표시
        flag, msg = lab_flag(k, v)
        tips = []
        # 간단 원인/가이드
        if k == "ANC":
            if v < 0.5: tips.append("🚨 매우 낮음: 생채소 금지, 모든 음식 익혀 먹기(전자레인지 30초 이상), 살균식품 권장, 남은 음식 2시간 후 섭취 금지, 껍질 과일은 주치의와 상담")
            elif v < 1.0: tips.append("🟠 낮음: 외출/감염원 주의, 조리 음식 위주")
        if k == "Hb" and v < 10: tips.append("빈혈 증상 주의(어지럼/피로). **철분제는 혈액암 환자에게 해로울 수 있어 임의복용 금지**")
        if k == "AST" and v >= 40: tips.append("간수치 상승: 간보호 식단 및 약물 검토")
        if k == "ALT" and v >= 55: tips.append("간세포 손상 의심: 약물/감염 등 원인 확인")
        if k == "CRP" and v > 0.5: tips.append("염증 상승: 발열/통증 동반 시 의료진 상담")
        out.append((k, v, flag, msg, tips))
    return out

# =========================
# 식이가이드 (요구된 5개 추천 예시 포함)
# =========================
def lab_diet_guides(labs: dict, heme_flag=False):
    recs = []

    # 82/74 항목 반영 예시
    if labs.get("Alb") is not None and labs["Alb"] < 3.5:
        recs.append("알부민 낮음: 달걀, 연두부, 흰살 생선, 닭가슴살, 귀리죽")
    if labs.get("K") is not None and labs["K"] < 3.5:
        recs.append("칼륨 낮음: 바나나, 감자, 호박죽, 고구마, 오렌지")
    if labs.get("Hb") is not None and labs["Hb"] < 12:
        recs.append("Hb 낮음: 소고기, 시금치, 두부, 달걀 노른자, 렌틸콩")
    # 나트륨/칼슘도 예시
    if labs.get("Na") is not None and labs["Na"] < 135:
        recs.append("나트륨 낮음: 전해질 음료, 미역국, 바나나, 오트밀죽, 삶은 감자")
    if labs.get("Ca") is not None and labs["Ca"] < 8.6:
        recs.append("칼슘 낮음: 연어통조림, 두부, 케일, 브로콜리, (참깨 제외)")

    # 혈액암 공통 경고
    if heme_flag:
        recs.append("철분제+비타민C: 흡수 촉진되지만 **항암/혈액암 환자는 반드시 주치의와 상담 후** 복용 결정")
    return recs

# =========================
# 로컬 표시(그룹-진단 한글 병기)
# =========================
def _is_korean(s: str) -> bool:
    return any('\uac00' <= ch <= '\ud7a3' for ch in (s or ""))

DX_KO_LOCAL = {
    "APL": "급성 전골수구성 백혈병",
    "AML": "급성 골수성 백혈병",
    "ALL": "급성 림프모구성 백혈병",
    "CML": "만성 골수성 백혈병",
    "CLL": "만성 림프구성 백혈병",
    "PCNSL": "일차성 중추신경계 림프종",
    "DLBCL": "미만성 거대 B세포 림프종",
    "BL": "버킷 림프종",
    "FL": "여포성 림프종",
    "cHL": "고전적 호지킨 림프종",
    "폐선암": "폐선암",
    "유방암": "유방암",
    "위암": "위암",
    "대장암": "대장암",
    "간세포암": "간세포암",
    "담도암": "담도암",
    "췌장암": "췌장암",
    "난소암": "난소암",
    "골육종(OS)": "골육종",
    "유잉육종(ES)": "유잉육종",
    "평활근육종(LMS)": "평활근육종",
    "지방육종(LPS)": "지방육종",
    "GIST": "위장관기저종양",
    "NET": "신경내분비종양",
    "MTC": "수질성 갑상선암",
}

def local_dx_display(group: str, dx: str) -> str:
    dx = (dx or "").strip()
    ko = DX_KO_LOCAL.get(dx)
    return f"{group} - {dx} ({ko})" if ko else f"{group} - {dx}"

# =========================
# 보고서 생성(.md / .txt)
# =========================
def build_report_md(ctx: dict) -> str:
    lines = [f"# BloodMap 보고서  ·  {APP_VERSION}",
             f"- 생성시각: {now_kst_str()}",
             f"- {MADE_BY}",
             ""]
    mode = ctx.get("mode")
    if mode == "암":
        lines += ["## 진단", f"- {ctx.get('group','')} - {ctx.get('dx','')}", ""]
        lines += ["## 피수치 요약(입력값)"]
        labs = ctx.get("labs", {}) or {}
        for k, v in labs.items():
            if v is not None:
                lines.append(f"- {k}: {v}")
        lines += ["", "## 식이가이드(요약)"]
        for d in (ctx.get("diet") or []):
            lines.append(f"- {d}")
        lines += ["", "## 약물 부작용(개인 선택)"]
        for k in (ctx.get("user_chemo") or []):
            info = DRUG_DB.get(k, {})
            lines.append(f"- **{k} ({info.get('alias',k)})**  ·  {info.get('ae','')}")
        for k in (ctx.get("user_abx") or []):
            info = DRUG_DB.get(k, {})
            lines.append(f"- **{k} ({info.get('alias',k)})**  ·  {info.get('ae','')}")
        lines += ["", "## 약물 부작용(자동 예시)"]
        for k in (ctx.get("auto_chemo") or []) + (ctx.get("auto_tgt") or []):
            info = DRUG_DB.get(k, {})
            lines.append(f"- **{k} ({info.get('alias',k)})**  ·  {info.get('ae','')}")
    else:
        lines += ["## 소아 증상 요약"]
        for k, v in (ctx.get("symptoms") or {}).items():
            lines.append(f"- {k}: {v}")
        lines += ["", "## 해열제 1회 평균 용량"]
        lines.append(f"- 아세트아미노펜 시럽: {ctx.get('apap_ml')} mL")
        lines.append(f"- 이부프로펜 시럽: {ctx.get('ibu_ml')} mL")
        # 선택 시 소아 피수치 요약
        labs = ctx.get("labs", {}) or {}
        if labs:
            lines += ["", "## 소아 입력 피수치(선택)"]
            for k, v in labs.items():
                if v is not None:
                    lines.append(f"- {k}: {v}")
    lines += ["", "## 고지(중요)", DISCLAIMER, "", CAFE_LINK_MD]
    return "\n".join(lines)

# =========================
# Streamlit UI
# =========================
st.set_page_config(page_title="BloodMap 피수치 해석기", page_icon="🩸", layout="centered")
st.title(f"🩸 BloodMap 피수치 해석기 {APP_VERSION}")
st.caption(MADE_BY)
st.info(IMMUNO_BANNER, icon="ℹ️")

# 별명 + PIN (4자리) - 중복 방지
st.markdown("### 0) 사용자 식별")
col_id1, col_id2 = st.columns([2,1])
with col_id1:
    nickname = st.text_input("별명", value="", placeholder="예: 하늘맘")
with col_id2:
    pin = st.text_input("PIN (4자리 숫자)", value="", max_chars=4, help="동일 조합은 중복 저장 불가")

if "id_registry" not in st.session_state:
    st.session_state["id_registry"] = set()
idkey = nickname_pin_key(nickname, pin) if nickname and pin else None

if idkey:
    if idkey in st.session_state["id_registry"]:
        st.error("이미 등록된 별명+PIN 조합입니다. 다른 조합을 사용해주세요.")
    else:
        st.success("사용 가능한 조합입니다.")
else:
    st.warning("별명과 4자리 PIN을 입력하면 결과 저장/그래프 기능을 사용할 수 있어요.")

# 모드 선택
mode = st.radio("모드 선택", ["소아 일상/질환", "암 진단"], horizontal=True)

# =========================
# 소아 모드
# =========================
if mode == "소아 일상/질환":
    st.markdown("### 1) 증상/체중")
    disease = st.selectbox("질환(참고용)", PEDS_DISEASES, index=0)
    opts = get_symptom_options_safe(disease)

    c1,c2,c3,c4 = st.columns(4)
    with c1: nasal = st.selectbox("콧물", opts.get("콧물", PEDS_SYMPTOMS_DEFAULT["콧물"]))
    with c2: cough = st.selectbox("기침", opts.get("기침", PEDS_SYMPTOMS_DEFAULT["기침"]))
    with c3: diarrhea = st.selectbox("설사(횟수/일)", opts.get("설사", PEDS_SYMPTOMS_DEFAULT["설사"]))
    with c4: fever = st.selectbox("발열", opts.get("발열", PEDS_SYMPTOMS_DEFAULT["발열"]))

    ckg, ct = st.columns([1,1])
    with ckg:
        weight_kg = clean_num(st.number_input("체중(kg)", min_value=0.0, step=0.5, value=0.0))
    with ct:
        temp_input = clean_num(st.number_input("현재 체온(°C)", min_value=34.0, step=0.1, value=36.5))

    apap_ml = acetaminophen_ml(weight_kg)
    ibu_ml = ibuprofen_ml(weight_kg)

    st.markdown("### 2) 해열제 1회분(평균) · 1일 최대값은 따로 표기하지 않습니다")
    dcols = st.columns(2)
    with dcols[0]:
        st.metric("아세트아미노펜 시럽", f"{apap_ml} mL")
    with dcols[1]:
        st.metric("이부프로펜 시럽", f"{ibu_ml} mL")

    st.caption("온도 구간 가이드: 38.0~38.5도: 해열제/경과관찰 · 38.5도 이상: 병원 연락 · 39.0도 이상: 즉시 병원")

    # 피수치 입력 토글
    st.markdown("### 3) (선택) 피수치 입력")
    show_labs = st.toggle("피수치 입력란 보이기", value=False)
    labs = {}
    if show_labs:
        for k, label in [("WBC","WBC(백혈구)"), ("Hb","Hb(혈색소)"), ("PLT","혈소판"), ("CRP","CRP"), ("ANC","ANC")]:
            labs[k] = clean_num(st.text_input(label, value=""))

    # 증상 기반 간단 예측(룰)
    def predict_peds(sym):
        score = {}
        def add(items, w=1):
            for d in items:
                score[d] = score.get(d, 0) + w
        if sym.get("설사") in {"3~4회","5~6회"}:
            add(["로타","노로","장염"], 2)
        if "누런" in sym.get("콧물","") or sym.get("기침") in {"보통","심함"}:
            add(["RSV","아데노","중이염"], 1)
        if "38.5" in sym.get("발열","") or temp_input and temp_input >= 38.5:
            add(["독감","편도염","코로나"], 2)
        return sorted(score.items(), key=lambda x: x[1], reverse=True)[:2]

    # 해석 버튼
    if st.button("해석하기", type="primary"):
        st.session_state["analyzed"] = True
        if idkey: st.session_state["id_registry"].add(idkey)
        st.session_state["ctx"] = {
            "mode": "소아",
            "symptoms": {"콧물":nasal,"기침":cough,"설사":diarrhea,"발열":fever, "체온대": temp_band(temp_input)},
            "apap_ml": apap_ml, "ibu_ml": ibu_ml,
            "labs": labs
        }

    if results_only_after_analyze(st):
        ctx = st.session_state.get("ctx", {})
        st.markdown("#### 🤔 예측 진단(참고)")
        preds = predict_peds({"콧물":nasal,"기침":cough,"설사":diarrhea,"발열":fever})
        if preds:
            for d, s in preds: st.write(f"- {d} (점수 {s})")
        else:
            st.write("- 입력된 증상이 적어 예측이 어렵습니다.")

        # 소아 피수치 간단 해석
        if ctx.get("labs"):
            st.subheader("🧪 소아 피수치 간단 해석")
            rows = []
            for k, v in ctx["labs"].items():
                if v is None: continue
                flag, msg = lab_flag(k, v)
                rows.append({"항목": k, "값": v, "해석": f"{flag} {msg}"})
            if rows:
                df = pd.DataFrame(rows)
                st.dataframe(df, use_container_width=True)

        # 보고서
        md = build_report_md(ctx)
        txt = md.replace("#","").replace("*","")
        st.download_button("⬇️ 보고서(.md)", md, file_name="bloodmap_report.md")
        st.download_button("⬇️ 보고서(.txt)", txt, file_name="bloodmap_report.txt")
        st.markdown("—")
        st.markdown(DISCLAIMER)

# =========================
# 암 진단 모드
# =========================
else:
    st.markdown("### 1) 암 카테고리/진단")
    group = st.selectbox("암 카테고리", ["혈액암","고형암","육종","희귀암","림프종"])
    dx_list = ["직접 입력"] + sorted(list((ONCO_MAP.get(group) or {}).keys()))
    dx = st.selectbox("진단명(영/약어)", dx_list, index=1 if len(dx_list)>1 else 0)

    if dx == "직접 입력":
        dx = st.text_input("진단(영문/축약 직접 입력)", value="").strip()

    if dx:
        st.markdown(f"**진단:** {local_dx_display(group, dx)}")

    st.markdown("### 2) 피수치 입력 (항상 표시)")
    labs = {}
    lcols = st.columns(3)
    for i, (k, label) in enumerate(LABS_ORDER):
        with lcols[i % 3]:
            labs[k] = clean_num(st.text_input(label, value=""))

    # 개인 선택 약물
    st.markdown("### 3) (선택) 현재 복용/투여 중인 약물")
    cA, cB = st.columns(2)
    with cA:
        user_chemo = st.multiselect("항암제", ["ATRA","Arsenic Trioxide","Idarubicin","MTX","6-MP","Ara-C","Vincristine","Cyclophosphamide","Daunorubicin","Doxorubicin","Paclitaxel","Gemcitabine","Pemetrexed"])
    with cB:
        user_abx = st.multiselect("항생제(발열/감염)", ["Cefepime","Piperacillin/Tazobactam","Meropenem","Vancomycin","G-CSF"])

    # 해석 버튼
    if st.button("해석하기", type="primary"):
        st.session_state["analyzed"] = True
        if idkey: st.session_state["id_registry"].add(idkey)
        auto = auto_recs_by_dx(group, dx)
        heme_flag = (group == "혈액암")
        diet = lab_diet_guides(labs, heme_flag=heme_flag)
        st.session_state["ctx"] = {
            "mode": "암", "group": group, "dx": dx,
            "labs": labs,
            "user_chemo": user_chemo, "user_abx": user_abx,
            "auto_chemo": auto.get("chemo", []), "auto_tgt": auto.get("targeted", []),
            "diet": diet
        }

    if results_only_after_analyze(st):
        ctx = st.session_state.get("ctx", {})
        heme_flag = (ctx.get("group") == "혈액암")

        # 피수치 해석
        st.subheader("🧪 피수치 해석(입력한 항목만)")
        rows = []
        for k, v, flag, msg, tips in interpret_labs(ctx.get("labs", {})):
            rows.append({"항목": k, "값": v, "해석": f"{flag} {msg}", "메모": "; ".join(tips)})
        if rows:
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True)

        # 식이가이드
        st.subheader("🥗 식이가이드")
        for d in ctx.get("diet", []):
            st.write(f"- {d}")
        if heme_flag:
            st.warning("혈액암 환자: **철분제 + 비타민 C** 병용은 흡수 촉진 → 반드시 주치의와 상의 후 복용 결정", icon="⚠️")

        # 부작용 '강조'
        st.warning("아래 **약물 부작용**을 반드시 확인하세요. 증상 발생 시 즉시 의료진과 상의하세요.", icon="⚠️")

        st.subheader("💊 (개인 선택) 약물 부작용")
        render_adverse_effects(st, ctx.get("user_chemo") or [], DRUG_DB)
        render_adverse_effects(st, ctx.get("user_abx") or [], DRUG_DB)

        st.subheader("💊 (자동 예시) 약물 부작용")
        render_adverse_effects(st, (ctx.get("auto_chemo") or []) + (ctx.get("auto_tgt") or []), DRUG_DB)

        # 특수검사(토글)
        st.markdown("### ➃ (선택) 특수검사 해석")
        if st.toggle("특수검사 입력 열기", value=False):
            st.caption("정성: '+/++/+++', 정량: 숫자 입력")
            # 정성
            q1, q2, q3, q4 = st.columns(4)
            with q1: albuminuria = st.selectbox("알부민뇨", ["", "+", "++", "+++"], index=0)
            with q2: hematuria = st.selectbox("혈뇨", ["", "+", "++", "+++"], index=0)
            with q3: glycosuria = st.selectbox("요당", ["", "+", "++", "+++"], index=0)
            with q4: occult = st.selectbox("잠혈", ["", "+", "++", "+++"], index=0)
            # 정량
            r1, r2, r3, r4 = st.columns(4)
            with r1: c3 = clean_num(st.text_input("C3", value=""))
            with r2: c4 = clean_num(st.text_input("C4", value=""))
            with r3: tg = clean_num(st.text_input("TG", value=""))
            with r4: hdl = clean_num(st.text_input("HDL", value=""))
            r5, r6, r7, r8 = st.columns(4)
            with r5: ldl = clean_num(st.text_input("LDL", value=""))
            with r6: rbc = clean_num(st.text_input("적혈구 수", value=""))
            with r7: wbc = clean_num(st.text_input("백혈구 수", value=""))
            with r8: plt = clean_num(st.text_input("혈소판 수", value=""))
            # 해석
            st.subheader("🧠 특수검사 해석")
            if albuminuria == "+++":
                st.error("알부민뇨 +++ → 🚨 신장 기능 이상 가능성")
            if c3 is not None and c3 < 90:
                st.warning("C3 수치 낮음 → 🟡 면역계 이상 가능성")
            if tg is not None and tg >= 200:
                st.warning("TG 200 이상 → 고지혈증 가능성")
            if plt is not None and plt < 100:
                st.warning("혈소판 낮음 → 출혈 주의")

        # 보고서
        md = build_report_md(ctx)
        txt = md.replace("#","").replace("*","")
        st.download_button("⬇️ 보고서(.md)", md, file_name="bloodmap_report.md")
        st.download_button("⬇️ 보고서(.txt)", txt, file_name="bloodmap_report.txt")
        st.markdown("—")
        st.markdown(DISCLAIMER)
