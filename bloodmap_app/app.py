# app.py — BloodMap (통합/안정화 버전)
# - utils/* 모듈이 없어도 최소기능 폴백으로 동작
# - _get_drug_list() 클로저 의존 제거 → get_drug_list(mode, group, cancer, ...)
# - 림프종 매핑 선선언, 프리셋/선택 상태키 안정화
# - 소변 정성(+/++/+++)만 사용, PLT 기본 라벨을 '혈소판'로
# - 보고서 .md/.txt/.pdf(미설치 시 안내) 저장, 그래프/스케줄 모듈 없을 때도 안전 동작

from datetime import datetime, date
import os
import importlib
import streamlit as st

# -----------------------------------------------------------------------------
# 동적 로더 (패키지/탑레벨 모두 시도)
# -----------------------------------------------------------------------------
PKG = os.path.basename(os.path.dirname(__file__)) or "bloodmap_app"

def _load_mod(path_in_pkg: str):
    """Try import: {PKG}.{path} → {path}."""
    for modname in (f"{PKG}.{path_in_pkg}", path_in_pkg):
        try:
            return importlib.import_module(modname)
        except Exception:
            continue
    return None

# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------
_cfg = _load_mod("config")
if _cfg is None:
    # 최소 기본값 (config 없어도 구동)
    class _C:
        APP_TITLE = "BloodMap"
        PAGE_TITLE = "BloodMap"
        MADE_BY = "제작: Hoya/GPT · 자문: Hoya/GPT"
        CAFE_LINK_MD = "[피수치 가이드 공식카페](https://cafe.naver.com/bloodmap)"
        FOOTER_CAFE = "공식 카페: cafe.naver.com/bloodmap"
        DISCLAIMER = ("본 수치는 참고용이며, 해석 결과는 개발자와 무관합니다. "
                      "약 변경, 복용 중단 등은 반드시 주치의와 상의 후 결정하시기 바랍니다. "
                      "이 앱은 개인정보를 절대 수집하지 않으며, 어떠한 개인정보 입력도 요구하지 않습니다.")
        FEVER_GUIDE = (
            "- 38.0~38.5℃: 해열제 복용/경과 관찰\n"
            "- ≥38.5℃: 병원에 연락 권고\n"
            "- ≥39.0℃: 즉시 병원 방문 고려"
        )
        ORDER = ["WBC", "Hb", "혈소판", "ANC", "Ca", "P", "Na", "K", "Albumin",
                 "Glucose", "Total Protein", "AST", "ALT", "LDH", "CRP",
                 "Creatinine", "Uric Acid", "Total Bilirubin", "BUN", "BNP"]
        LBL_WBC="WBC"; LBL_Hb="Hb"; LBL_PLT="혈소판"; LBL_ANC="ANC"
        LBL_Ca="Ca"; LBL_P="P"; LBL_Na="Na"; LBL_K="K"; LBL_Alb="Albumin"
        LBL_Glu="Glucose"; LBL_TP="Total Protein"; LBL_AST="AST"; LBL_ALT="ALT"
        LBL_LDH="LDH"; LBL_CRP="CRP"; LBL_Cr="Creatinine"; LBL_UA="Uric Acid"
        LBL_TB="Total Bilirubin"; LBL_BUN="BUN"; LBL_BNP="BNP"
    _cfg = _C()

APP_TITLE = getattr(_cfg, "APP_TITLE")
PAGE_TITLE = getattr(_cfg, "PAGE_TITLE")
MADE_BY = getattr(_cfg, "MADE_BY")
CAFE_LINK_MD = getattr(_cfg, "CAFE_LINK_MD")
FOOTER_CAFE = getattr(_cfg, "FOOTER_CAFE")
DISCLAIMER = getattr(_cfg, "DISCLAIMER")
ORDER = getattr(_cfg, "ORDER")
FEVER_GUIDE = getattr(_cfg, "FEVER_GUIDE")

# 라벨 (PLT 기본 한글)
LBL_WBC = getattr(_cfg, "LBL_WBC", "WBC")
LBL_Hb  = getattr(_cfg, "LBL_Hb", "Hb")
LBL_PLT = getattr(_cfg, "LBL_PLT", "혈소판")
LBL_ANC = getattr(_cfg, "LBL_ANC", "ANC")
LBL_Ca  = getattr(_cfg, "LBL_Ca", "Ca")
LBL_P   = getattr(_cfg, "LBL_P", "P")
LBL_Na  = getattr(_cfg, "LBL_Na", "Na")
LBL_K   = getattr(_cfg, "LBL_K", "K")
LBL_Alb = getattr(_cfg, "LBL_Alb", "Albumin")
LBL_Glu = getattr(_cfg, "LBL_Glu", "Glucose")
LBL_TP  = getattr(_cfg, "LBL_TP", "Total Protein")
LBL_AST = getattr(_cfg, "LBL_AST", "AST")
LBL_ALT = getattr(_cfg, "LBL_ALT", "ALT")
LBL_LDH = getattr(_cfg, "LBL_LDH", "LDH")
LBL_CRP = getattr(_cfg, "LBL_CRP", "CRP")
LBL_Cr  = getattr(_cfg, "LBL_Cr", "Creatinine")
LBL_UA  = getattr(_cfg, "LBL_UA", "Uric Acid")
LBL_TB  = getattr(_cfg, "LBL_TB", "Total Bilirubin")
LBL_BUN = getattr(_cfg, "LBL_BUN", "BUN")
LBL_BNP = getattr(_cfg, "LBL_BNP", "BNP")

# -----------------------------------------------------------------------------
# Data modules
# -----------------------------------------------------------------------------
_drugs = _load_mod("data.drugs")
_foods = _load_mod("data.foods")
_ped   = _load_mod("data.ped")

ANTICANCER = getattr(_drugs, "ANTICANCER", {}) if _drugs else {}
ABX_GUIDE  = getattr(_drugs, "ABX_GUIDE", {}) if _drugs else {}
FOODS      = getattr(_foods, "FOODS", {}) if _foods else {}

PED_TOPICS      = getattr(_ped, "PED_TOPICS", {})
PED_INPUTS_INFO = getattr(_ped, "PED_INPUTS_INFO", "")
PED_INFECT      = getattr(_ped, "PED_INFECT", {})
PED_SYMPTOMS    = getattr(_ped, "PED_SYMPTOMS", {})
PED_RED_FLAGS   = getattr(_ped, "PED_RED_FLAGS", {})

# -----------------------------------------------------------------------------
# Utils modules + 함수 바인딩 (없으면 폴백)
# -----------------------------------------------------------------------------
_utils_inputs   = _load_mod("utils.inputs")
_utils_interpret= _load_mod("utils.interpret")
_utils_reports  = _load_mod("utils.reports")
_utils_graphs   = _load_mod("utils.graphs")
_utils_schedule = _load_mod("utils.schedule")

# 기본: None으로 받고, 아래 폴백에서 채움
num_input_generic     = getattr(_utils_inputs, "num_input_generic", None)
entered               = getattr(_utils_inputs, "entered", None)
_parse_numeric        = getattr(_utils_inputs, "_parse_numeric", None)

interpret_labs        = getattr(_utils_interpret, "interpret_labs", None)
compare_with_previous = getattr(_utils_interpret, "compare_with_previous", None)
food_suggestions      = getattr(_utils_interpret, "food_suggestions", None)
summarize_meds        = getattr(_utils_interpret, "summarize_meds", None)
abx_summary           = getattr(_utils_interpret, "abx_summary", None)
interpret_specials    = getattr(_utils_interpret, "_interpret_specials", None) or getattr(_utils_interpret, "interpret_specials", None)

build_report          = getattr(_utils_reports, "build_report", None)
md_to_pdf_bytes_fontlocked = getattr(_utils_reports, "md_to_pdf_bytes_fontlocked", None)

render_graphs         = getattr(_utils_graphs, "render_graphs", None)
render_schedule       = getattr(_utils_schedule, "render_schedule", None)

# ---- 폴백 구현 (누락된 모듈이 있어도 동작) ----
missing = []
if num_input_generic is None or entered is None or _parse_numeric is None:
    missing.append("utils.inputs")
    def _parse_numeric(raw, decimals=1):
        if raw is None: return None
        s = str(raw).strip().replace(",", "")
        if s == "": return None
        try:
            return int(float(s)) if decimals == 0 else round(float(s), decimals)
        except Exception:
            return None
    def num_input_generic(label, key=None, decimals=1, placeholder="", as_int=False):
        raw = st.text_input(label, key=key, placeholder=placeholder)
        return _parse_numeric(raw, 0 if as_int else decimals)
    def entered(v):
        try:
            if v is None: return False
            if isinstance(v, str): return v.strip() != ""
            return True
        except Exception:
            return False

if interpret_labs is None or compare_with_previous is None or food_suggestions is None or summarize_meds is None or abx_summary is None or interpret_specials is None:
    missing.append("utils.interpret")
    def interpret_labs(vals, extras):
        out=[]
        for k,v in (vals or {}).items():
            if entered(v): out.append(f"- {k}: {v}")
        return out
    def compare_with_previous(nickname_key, current_vals): return []
    def food_suggestions(vals, anc_place): return []
    def summarize_meds(meds: dict):
        if not meds: return []
        lines = ["입력된 항암제 요약"]
        for k,v in meds.items():
            if isinstance(v, dict):
                if "form" in v and "dose" in v:
                    lines.append(f"- {k} ({v['form']}) · {v['dose']}")
                elif "dose_or_tabs" in v:
                    lines.append(f"- {k} · {v['dose_or_tabs']}")
                else:
                    lines.append(f"- {k}")
            else:
                lines.append(f"- {k}")
        return lines
    def abx_summary(abx_dict: dict):
        if not abx_dict: return []
        return ["입력된 항생제 요약"] + [f"- {k}: {v}" for k,v in abx_dict.items()]
    def interpret_specials(extra_vals, vals, profile="adult"): return []

if build_report is None or md_to_pdf_bytes_fontlocked is None:
    missing.append("utils.reports")
    def build_report(mode, meta, labs, cmp_lines, extra_vals, meds_lines, food_lines, abx_lines):
        parts = ["# BloodMap 간이 보고서",
                 f"- 모드: {mode}",
                 f"- 메타: {meta}",
                 "## 입력 수치"]
        for k,v in (labs or {}).items(): parts.append(f"- {k}: {v}")
        if cmp_lines:  parts += ["## 변화 비교", *[f"- {x}" for x in cmp_lines]]
        if meds_lines: parts += ["## 항암제 요약", *meds_lines]
        if abx_lines:  parts += ["## 항생제 요약", *abx_lines]
        if food_lines: parts += ["## 음식 가이드", *food_lines]
        return "\n".join(parts)
    def md_to_pdf_bytes_fontlocked(_):
        raise FileNotFoundError("reportlab 미설치: PDF 변환은 환경에 설치 후 이용하세요.")

if render_graphs is None:
    missing.append("utils.graphs")
    def render_graphs():
        st.caption("그래프 모듈 없음: `utils/graphs.py` 추가 시 자동 활성화됩니다.")

if render_schedule is None:
    missing.append("utils.schedule")
    def render_schedule(nickname_key):
        st.caption("항암 스케줄 모듈 없음: `utils/schedule.py` 추가 시 자동 활성화됩니다.")

# -----------------------------------------------------------------------------
# 스타일
# -----------------------------------------------------------------------------
def _load_css():
    try:
        path = os.path.join(os.path.dirname(__file__), "style.css")
        with open(path, "r", encoding="utf-8") as f:
            st.markdown('<style>'+f.read()+'</style>', unsafe_allow_html=True)
    except Exception:
        pass

# -----------------------------------------------------------------------------
# 입력 유틸/계산
# -----------------------------------------------------------------------------
def calc_corrected_ca(total_ca, albumin):
    try:
        if total_ca is None or albumin is None: return None
        return round(float(total_ca) + 0.8*(4.0 - float(albumin)), 2)
    except Exception:
        return None

def calc_friedewald_ldl(tc, hdl, tg):
    try:
        if tg is None or float(tg) >= 400: return None
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
    try: e=float(egfr)
    except Exception: return None, None
    if e >= 90:   return "G1", "정상/고정상 (≥90)"
    if 60 <= e < 90:  return "G2", "경도 감소 (60–89)"
    if 45 <= e < 60:  return "G3a", "중등도 감소 (45–59)"
    if 30 <= e < 45:  return "G3b", "중등도~중증 감소 (30–44)"
    if 15 <= e < 30:  return "G4", "중증 감소 (15–29)"
    return "G5", "신부전 (<15)"

def stage_acr(acr_mg_g):
    try: a=float(acr_mg_g)
    except Exception: return None, None
    if a < 30: return "A1", "정상-경도 증가 (<30 mg/g)"
    if a <= 300: return "A2", "중등도 증가 (30–300 mg/g)"
    return "A3", "중증 증가 (>300 mg/g)"

def dose_acetaminophen(weight_kg):
    try: w=float(weight_kg); return round(w*10), round(w*15)
    except Exception: return None, None

def dose_ibuprofen(weight_kg):
    try: w=float(weight_kg); return round(w*5), round(w*10)
    except Exception: return None, None

def _badge(txt, level="info"):
    colors = {"ok":"#16a34a","mild":"#f59e0b","mod":"#fb923c","high":"#dc2626","info":"#2563eb","dim":"#6b7280"}
    col = colors.get(level, "#2563eb")
    return f'<span style="display:inline-block;padding:2px 8px;border-radius:9999px;background:rgba(0,0,0,0.04);color:{col};border:1px solid {col};font-size:12px;margin-right:6px;">{txt}</span>'

def _strip_html(s: str) -> str:
    import re
    return re.sub(r'<[^>]+>', '', s or '')

# -----------------------------------------------------------------------------
# 닉네임+PIN
# -----------------------------------------------------------------------------
def _nickname_with_pin():
    col1, col2 = st.columns([2,1])
    with col1:
        nickname = st.text_input("별명", placeholder="예: 홍길동")
    with col2:
        pin = st.text_input("PIN(4자리 숫자)", max_chars=4, help="중복 방지용 4자리 숫자", key="pin", placeholder="0000")
    pin_clean = "".join([c for c in (pin or "") if c.isdigit()])[:4]
    if pin and pin != pin_clean:
        st.warning("PIN은 숫자 4자리만 허용됩니다.")
    if pin_clean and len(pin_clean)!=4:
        st.info("PIN 4자리를 입력해주세요.")
    k = (nickname.strip() + "#" + pin_clean) if nickname and pin_clean else nickname.strip()
    return nickname, pin_clean, k

# -----------------------------------------------------------------------------
# 소변 해석(기본)
# -----------------------------------------------------------------------------
def _interpret_urine(extras: dict):
    lines = []
    def _isnum(x):
        try:
            return x is not None and float(x) == float(x)
        except Exception:
            return False
    rbc = extras.get("적혈구(소변, /HPF)")
    wbc = extras.get("백혈구(소변, /HPF)")
    upcr = extras.get("UPCR(mg/g)")
    acr  = extras.get("ACR(mg/g)")

    if _isnum(rbc):
        r=float(rbc)
        if r <= 2: lines.append(f"소변 적혈구(/HPF): {int(r)} — 정상(0–2).")
        elif 3 <= r <= 5: lines.append(f"소변 적혈구(/HPF): {int(r)} — 경미 혈뇨 가능(운동/생리/채뇨오염 확인).")
        else: lines.append(f"소변 적혈구(/HPF): {int(r)} — 유의한 혈뇨 가능(UTI/결석 등 평가).")
    if _isnum(wbc):
        w=float(wbc)
        if w <= 5: lines.append(f"소변 백혈구(/HPF): {int(w)} — 정상(≤5).")
        elif 6 <= w <= 9: lines.append(f"소변 백혈구(/HPF): {int(w)} — 경미 백혈구뇨 가능.")
        else: lines.append(f"소변 백혈구(/HPF): {int(w)} — 유의한 백혈구뇨(UTI 의심) 가능.")
    if _isnum(upcr):
        u=float(upcr)
        if u < 150: lines.append(f"UPCR: {u:.1f} mg/g — 정상~경미(<150).")
        elif u < 300: lines.append(f"UPCR: {u:.1f} mg/g — 경도 단백뇨(150–300).")
        elif u < 1000: lines.append(f"UPCR: {u:.1f} mg/g — 중등도 단백뇨(300–1000).")
        else: lines.append(f"UPCR: {u:.1f} mg/g — 중증 단백뇨(>1000).")
    if _isnum(acr):
        a=float(acr)
        if a < 30: lines.append(f"ACR: {a:.1f} mg/g — A1(정상-경도).")
        elif a <= 300: lines.append(f"ACR: {a:.1f} mg/g — A2(중등도).")
        else: lines.append(f"ACR: {a:.1f} mg/g — A3(중증).")
    if lines:
        lines.append("※ 해석은 참고용입니다. 증상·반복 상승 시 의료진과 상담하세요.")
    return lines

# -----------------------------------------------------------------------------
# 항암제 기본 목록 (순수 함수)
# -----------------------------------------------------------------------------
def get_drug_list(mode, group, cancer, heme_key_map, lymphoma_key_map):
    if not (mode == "일반/암" and group and group != "미선택/일반" and cancer):
        return []

    heme_by_cancer = {
        "AML": ["ARA-C","Daunorubicin","Idarubicin","Cyclophosphamide","Etoposide","Fludarabine","Hydroxyurea","MTX","ATRA","G-CSF"],
        "APL": ["ATRA","Idarubicin","Daunorubicin","ARA-C","MTX","6-MP","G-CSF"],
        "ALL": ["Vincristine","Asparaginase","Daunorubicin","Cyclophosphamide","MTX","ARA-C","Topotecan","Etoposide"],
        "CML": ["Imatinib","Dasatinib","Nilotinib","Hydroxyurea"],
        "CLL": ["Fludarabine","Cyclophosphamide"],
    }
    solid_by_cancer = {
        "폐암(Lung cancer)": ["Cisplatin","Carboplatin","Paclitaxel","Docetaxel","Gemcitabine","Pemetrexed",
                              "Gefitinib","Erlotinib","Osimertinib","Alectinib","Bevacizumab","Pembrolizumab","Nivolumab"],
        "유방암(Breast cancer)": ["Doxorubicin","Cyclophosphamide","Paclitaxel","Docetaxel","Trastuzumab","Bevacizumab"],
        "위암(Gastric cancer)": ["Cisplatin","Oxaliplatin","5-FU","Capecitabine","Paclitaxel","Trastuzumab","Pembrolizumab"],
        "대장암(Cololoractal cancer)": ["5-FU","Capecitabine","Oxaliplatin","Irinotecan","Bevacizumab"],
        "간암(HCC)": ["Sorafenib","Lenvatinib","Bevacizumab","Pembrolizumab","Nivolumab"],
        "췌장암(Pancreatic cancer)": ["Gemcitabine","Oxaliplatin","Irinotecan","5-FU"],
        "담도암(Cholangiocarcinoma)": ["Gemcitabine","Cisplatin","Bevacizumab"],
        "자궁내막암(Endometrial cancer)": ["Carboplatin","Paclitaxel"],
        "구강암/후두암": ["Cisplatin","5-FU","Docetaxel"],
        "피부암(흑색종)": ["Dacarbazine","Paclitaxel","Nivolumab","Pembrolizumab"],
        "신장암(RCC)": ["Sunitinib","Pazopanib","Bevacizumab","Nivolumab","Pembrolizumab"],
        "갑상선암": ["Lenvatinib","Sorafenib"],
        "난소암": ["Carboplatin","Paclitaxel","Bevacizumab"],
        "자궁경부암": ["Cisplatin","Paclitaxel","Bevacizumab"],
        "전립선암": ["Docetaxel","Cabazitaxel"],
        "뇌종양(Glioma)": ["Temozolomide","Bevacizumab"],
        "식도암": ["Cisplatin","5-FU","Paclitaxel","Nivolumab","Pembrolizumab"],
        "방광암": ["Cisplatin","Gemcitabine","Bevacizumab","Pembrolizumab","Nivolumab"],
    }
    sarcoma_by_dx = {
        "연부조직육종(Soft tissue sarcoma)": ["Doxorubicin","Ifosfamide","Pazopanib","Gemcitabine","Docetaxel"],
        "골육종(Osteosarcoma)": ["Doxorubicin","Cisplatin","Ifosfamide","High-dose MTX"],
        "유잉육종(Ewing sarcoma)": ["Vincristine","Doxorubicin","Cyclophosphamide","Ifosfamide","Etoposide"],
        "평활근육종(Leiomyosarcoma)": ["Doxorubicin","Ifosfamide","Gemcitabine","Docetaxel","Pazopanib"],
        "지방육종(Liposarcoma)": ["Doxorubicin","Ifosfamide","Trabectedin"],
        "악성 섬유성 조직구종(UPS/MFH)": ["Doxorubicin","Ifosfamide","Gemcitabine","Docetaxel"],
    }
    rare_by_cancer = {
        "담낭암(Gallbladder cancer)": ["Gemcitabine","Cisplatin"],
        "부신암(Adrenal cancer)": ["Mitotane","Etoposide","Doxorubicin","Cisplatin"],
        "망막모세포종(Retinoblastoma)": ["Vincristine","Etoposide","Carboplatin"],
        "흉선종/흉선암(Thymoma/Thymic carcinoma)": ["Cyclophosphamide","Doxorubicin","Cisplatin"],
        "신경내분비종양(NET)": ["Etoposide","Cisplatin","Sunitinib"],
        "간모세포종(Hepatoblastoma)": ["Cisplatin","Doxorubicin"],
        "비인두암(NPC)": ["Cisplatin","5-FU","Gemcitabine","Bevacizumab","Nivolumab","Pembrolizumab"],
        "GIST": ["Imatinib","Sunitinib","Regorafenib"],
    }
    lymphoma_by_dx = {
        "DLBCL": ["R-CHOP","Pola-R-CHP","DA-EPOCH-R","R-ICE","R-DHAP","R-GDP","R-GemOx","R-ESHAP","Pola-BR","Tafasitamab + Lenalidomide","Loncastuximab","Glofitamab","Epcoritamab","Selinexor"],
        "PMBCL": ["DA-EPOCH-R","R-ICE","R-DHAP","R-GDP","R-GemOx","Pembrolizumab (PMBCL; 해외 활발 사용, 국내 미승인)","Glofitamab","Epcoritamab"],
        "FL12":  ["BR","R-CVP","R-CHOP","Obinutuzumab + BR","Lenalidomide + Rituximab"],
        "FL3A":  ["R-CHOP","Pola-R-CHP","BR"],
        "FL3B":  ["R-CHOP","Pola-R-CHP","DA-EPOCH-R"],
        "MCL":   ["BR","R-CHOP","Ibrutinib (R/R)","Acalabrutinib (R/R)","Zanubrutinib (R/R)","R-ICE","R-DHAP"],
        "MZL":   ["BR","R-CVP","R-CHOP"],
        "HGBL":  ["R-CHOP","Pola-R-CHP","DA-EPOCH-R","R-ICE","R-DHAP","R-GDP"],
        "BL":    ["CODOX-M/IVAC-R","Hyper-CVAD-R","R-ICE"],
    }

    key = heme_key_map.get(cancer, cancer)
    per_group = {
        "혈액암": heme_by_cancer.get(key, []),
        "고형암": solid_by_cancer.get(cancer, []),
        "육종":   sarcoma_by_dx.get(cancer, []),
        "희귀암": rare_by_cancer.get(cancer, []),
        "림프종": lymphoma_by_dx.get(lymphoma_key_map.get(cancer, cancer), []),
    }
    return list(dict.fromkeys(per_group.get(group, [])))

# -----------------------------------------------------------------------------
# 메인
# -----------------------------------------------------------------------------
def main():
    st.set_page_config(page_title=PAGE_TITLE, layout="centered")
    _load_css()

    st.title(APP_TITLE)
    st.markdown(MADE_BY)
    if CAFE_LINK_MD: st.markdown(CAFE_LINK_MD)
    if missing:
        st.info("개발 모드: 일부 유틸 모듈이 없어 간이 기능으로 동작 중 → " + ", ".join(sorted(set(missing))))

    st.markdown("### 공유하기")
    c1, c2, c3 = st.columns([1,1,2])
    with c1:
        st.link_button("카카오톡/메신저", "https://hdzwo5ginueir7hknzzfg4.streamlit.app/")
    with c2:
        st.link_button("카페/블로그", "https://cafe.naver.com/bloodmap")
    with c3:
        st.code("https://hdzwo5ginueir7hknzzfg4.streamlit.app/", language="text")
    st.caption("모바일 줄꼬임 방지 · 별명+PIN 저장/그래프 · 암별/소아/희귀암/육종 · PDF 한글 고정 · 수치 비교 · ANC 가이드")

    if "records" not in st.session_state: st.session_state.records = {}
    if "schedules" not in st.session_state: st.session_state.schedules = {}

    st.divider()
    st.header("1️⃣ 환자/암·소아 정보")

    nickname, pin, nickname_key = _nickname_with_pin()
    test_date = st.date_input("검사 날짜", value=date.today())
    anc_place = st.radio("현재 식사 장소(ANC 가이드용)", ["가정", "병원"], horizontal=True)

    mode = st.selectbox("모드 선택", ["일반/암", "소아(일상/호흡기)", "소아(감염질환)"])

    group = None
    cancer = None
    infect_sel = None
    ped_topic = None

    # 혈액암/림프종 라벨 매핑
    heme_key_map = {
        'AML(급성 골수성 백혈병)': 'AML',
        'APL(급성 전골수구성백혈병)': 'APL',
        'ALL(급성 림프모구성 백혈병)': 'ALL',
        'CML(만성 골수성백혈병)': 'CML',
        'CLL(만성 림프구성백혈병)': 'CLL',
        '급성 골수성 백혈병(AML)': 'AML',
        '급성 전골수구성 백혈병(APL)': 'APL',
        '급성 림프모구성 백혈병(ALL)': 'ALL',
        '만성 골수성 백혈병(CML)': 'CML',
        '만성 림프구성 백혈병(CLL)': 'CLL',
    }
    lymphoma_key_map = {
        "미만성 거대 B세포 림프종(DLBCL)": "DLBCL",
        "원발 종격동 B세포 림프종(PMBCL)": "PMBCL",
        "여포성 림프종 1-2등급(FL 1-2)": "FL12",
        "여포성 림프종 3A(FL 3A)": "FL3A",
        "여포성 림프종 3B(FL 3B)": "FL3B",
        "외투세포 림프종(MCL)": "MCL",
        "변연대 림프종(MZL)": "MZL",
        "고등급 B세포 림프종(HGBL)": "HGBL",
        "버킷 림프종(Burkitt)": "BL",
    }

    if mode == "일반/암":
        group = st.selectbox("암 그룹 선택", ["미선택/일반", "혈액암", "고형암", "육종", "희귀암", "림프종"])

        if group == "혈액암":
            heme_display = [
                "급성 골수성 백혈병(AML)",
                "급성 전골수구성 백혈병(APL)",
                "급성 림프모구성 백혈병(ALL)",
                "만성 골수성 백혈병(CML)",
                "만성 림프구성 백혈병(CLL)",
            ]
            cancer = st.selectbox("혈액암(진단명)", heme_display)

        elif group == "고형암":
            cancer = st.selectbox("고형암(진단명)", [
                "폐암(Lung cancer)","유방암(Breast cancer)","위암(Gastric cancer)",
                "대장암(Cololoractal cancer)","간암(HCC)","췌장암(Pancreatic cancer)",
                "담도암(Cholangiocarcinoma)","자궁내막암(Endometrial cancer)",
                "구강암/후두암","피부암(흑색종)","신장암(RCC)",
                "갑상선암","난소암","자궁경부암","전립선암","뇌종양(Glioma)","식도암","방광암"
            ])

        elif group == "육종":
            cancer = st.selectbox("육종(진단명)", [
                "연부조직육종(Soft tissue sarcoma)","골육종(Osteosarcoma)","유잉육종(Ewing sarcoma)",
                "평활근육종(Leiomyosarcoma)","지방육종(Liposarcoma)","악성 섬유성 조직구종(UPS/MFH)"
            ])

        elif group == "희귀암":
            cancer = st.selectbox("희귀암(진단명)", [
                "담낭암(Gallbladder cancer)","부신암(Adrenal cancer)","망막모세포종(Retinoblastoma)",
                "흉선종/흉선암(Thymoma/Thymic carcinoma)","신경내분비종양(NET)",
                "간모세포종(Hepatoblastoma)","비인두암(NPC)","GIST"
            ])

        elif group == "림프종":
            st.subheader("림프종 진단 / 약물 선택")
            lymph_display = list(lymphoma_key_map.keys())
            cancer = st.selectbox("림프종(진단명)", lymph_display)
            st.session_state["dx_label"] = cancer
            st.session_state["dx_slug"]  = lymphoma_key_map.get(cancer, cancer)

        # 진단 변경 시 그룹별 선택 상태 초기화
        if group:
            dx_key = f"{group}:{cancer}"
            if st.session_state.get("dx_key") != dx_key:
                st.session_state["dx_key"] = dx_key
                st.session_state[f"selected_drugs_{group}"] = []

    elif mode == "소아(일상/호흡기)":
        st.markdown("### 소아 일상 주제 선택")
        if PED_INPUTS_INFO: st.caption(PED_INPUTS_INFO)
        ped_topic = st.selectbox("소아 주제", ["일상 케어","수분 섭취","해열제 사용","기침/콧물 관리"])

    else:
        st.markdown("### 소아·영유아 감염질환")
        infect_sel = st.selectbox("질환 선택", list(PED_INFECT.keys()) or ["RSV","아데노","로타"])
        info = PED_INFECT.get(infect_sel, {})
        st.info(f"핵심: {info.get('핵심','')} · 진단: {info.get('진단','')} · 특징: {info.get('특징','')}")

    table_mode = st.checkbox("PC용 표 모드(가로형)", help="모바일은 세로형 권장")

    meds = {}
    extras = {}

    # -------------------- 항암제 입력 --------------------
    if mode == "일반/암":
        st.markdown("### 💊 항암제 선택 및 입력")

        preset = st.selectbox("레짐 프리셋", ["없음","APL(ATRA+ATO)","유방 AC-T","대장 FOLFOX","대장 FOLFIRI","림프종 CHOP"], index=0)
        if st.button("프리셋 적용"):
            preset_map = {
                "없음": [],
                "APL(ATRA+ATO)": ["ATRA","Arsenic trioxide","Idarubicin"],
                "유방 AC-T": ["Doxorubicin","Cyclophosphamide","Paclitaxel"],
                "대장 FOLFOX": ["Oxaliplatin","5-FU","Leucovorin"],
                "대장 FOLFIRI": ["Irinotecan","5-FU","Leucovorin"],
                "림프종 CHOP": ["Cyclophosphamide","Doxorubicin","Vincristine","Prednisolone"],
            }
            cur = st.session_state.get("selected_drugs", [])
            st.session_state["selected_drugs"] = list(dict.fromkeys(cur + preset_map.get(preset, [])))

        base_list = get_drug_list(mode, group, cancer, heme_key_map, lymphoma_key_map)
        drug_search = st.text_input("항암제 검색", key="drug_search")
        drug_choices = [d for d in base_list if not drug_search or drug_search.lower() in d.lower() or drug_search.lower() in ANTICANCER.get(d,{}).get("alias","").lower()]

        drug_key = f"selected_drugs_{group}" if group else "selected_drugs"
        default_sel = st.session_state.get(drug_key, [])
        if isinstance(default_sel, str): default_sel = [default_sel]
        default_sel = [x for x in default_sel if x in drug_choices]
        selected_drugs = st.multiselect("항암제 선택", drug_choices, default=default_sel, key=drug_key)

        for d in selected_drugs:
            alias = ANTICANCER.get(d,{}).get("alias","")
            if d == "ATRA":
                amt = num_input_generic(f"{d} ({alias}) - 캡슐 개수", key=f"med_{d}", as_int=True, placeholder="예: 2")
            elif d == "ARA-C":
                ara_form = st.selectbox(f"{d} ({alias}) - 제형", ["정맥(IV)","피하(SC)","고용량(HDAC)"], key=f"ara_form_{d}")
                amt = num_input_generic(f"{d} ({alias}) - 용량/일", key=f"med_{d}", decimals=1, placeholder="예: 100")
                if entered(amt):
                    meds[d] = {"form": ara_form, "dose": amt}
                continue
            else:
                amt = num_input_generic(f"{d} ({alias}) - 용량/알약", key=f"med_{d}", decimals=1, placeholder="예: 1.5")
            if entered(amt):
                meds[d] = {"dose_or_tabs": amt}

    # -------------------- 항생제 입력 --------------------
    st.markdown("### 🧪 항생제 선택 및 입력")
    extras["abx"] = {}
    abx_search = st.text_input("항생제 검색", key="abx_search")
    abx_choices = [a for a in ABX_GUIDE.keys() if not abx_search or abx_search.lower() in a.lower() or any(abx_search.lower() in tip.lower() for tip in ABX_GUIDE[a])]
    selected_abx = st.multiselect("항생제 계열 선택", abx_choices, default=[])
    for abx in selected_abx:
        extras["abx"][abx] = num_input_generic(f"{abx} - 복용/주입량", key=f"abx_{abx}", decimals=1, placeholder="예: 1")

    st.markdown("### 💧 동반 약물/상태")
    extras["diuretic_amt"] = num_input_generic("이뇨제(복용량/회/일)", key="diuretic_amt", decimals=1, placeholder="예: 1")

    # -------------------- 기본 검사 입력 --------------------
    st.divider()
    if mode == "일반/암":
        st.header("2️⃣ 기본 혈액 검사 수치 (입력한 값만 해석)")
    elif mode == "소아(일상/호흡기)":
        st.header("2️⃣ 소아 공통 입력")
    else:
        st.header("2️⃣ (감염질환은 별도 수치 입력 없음)")

    vals = {}

    def render_inputs_vertical(vals):
        st.markdown("**기본 패널**")
        for name in ORDER:
            if name == LBL_CRP:
                vals[name] = num_input_generic(f"{name}", key=f"v_{name}", decimals=2, placeholder="예: 0.12")
            elif name in (LBL_WBC, LBL_ANC, LBL_AST, LBL_ALT, LBL_LDH, LBL_BNP, LBL_Glu):
                vals[name] = num_input_generic(f"{name}", key=f"v_{name}", decimals=1, placeholder="예: 1200")
            else:
                vals[name] = num_input_generic(f"{name}", key=f"v_{name}", decimals=1, placeholder="예: 3.5")

    def render_inputs_table(vals):
        st.markdown("**기본 패널 (표 모드)**")
        left, right = st.columns(2)
        half = (len(ORDER)+1)//2
        with left:
            for name in ORDER[:half]:
                if name == LBL_CRP:
                    vals[name] = num_input_generic(f"{name}", key=f"l_{name}", decimals=2, placeholder="예: 0.12")
                elif name in (LBL_WBC, LBL_ANC, LBL_AST, LBL_ALT, LBL_LDH, LBL_BNP, LBL_Glu):
                    vals[name] = num_input_generic(f"{name}", key=f"l_{name}", decimals=1, placeholder="예: 1200")
                else:
                    vals[name] = num_input_generic(f"{name}", key=f"l_{name}", decimals=1, placeholder="예: 3.5")
        with right:
            for name in ORDER[half:]:
                if name == LBL_CRP:
                    vals[name] = num_input_generic(f"{name}", key=f"r_{name}", decimals=2, placeholder="예: 0.12")
                elif name in (LBL_WBC, LBL_ANC, LBL_AST, LBL_ALT, LBL_LDH, LBL_BNP, LBL_Glu):
                    vals[name] = num_input_generic(f"{name}", key=f"r_{name}", decimals=1, placeholder="예: 1200")
                else:
                    vals[name] = num_input_generic(f"{name}", key=f"r_{name}", decimals=1, placeholder="예: 3.5")

    if mode == "일반/암":
        if table_mode: render_inputs_table(vals)
        else:          render_inputs_vertical(vals)
        if nickname_key and st.session_state.records.get(nickname_key):
            if st.button("↩️ 이전 기록 불러오기", help="같은 별명#PIN의 가장 최근 수치를 현재 폼에 채움"):
                last = st.session_state.records[nickname_key][-1]
                labs = last.get("labs", {})
                for lab, val in labs.items():
                    for pref in ("v_", "l_", "r_"):
                        k = f"{pref}{lab}"
                        if k in st.session_state:
                            st.session_state[k] = val
                st.success("이전 기록을 폼에 채웠습니다.")
    elif mode == "소아(일상/호흡기)":
        def _parse_num_ped(label, key, decimals=1, placeholder=""):
            raw = st.text_input(label, key=key, placeholder=placeholder)
            return _parse_numeric(raw, decimals=decimals)
        age_m        = _parse_num_ped("나이(개월)", key="ped_age", decimals=0, placeholder="예: 18")
        temp_c       = _parse_num_ped("체온(℃)", key="ped_temp", decimals=1, placeholder="예: 38.2")
        rr           = _parse_num_ped("호흡수(/분)", key="ped_rr", decimals=0, placeholder="예: 42")
        spo2_unknown = st.checkbox("산소포화도 측정기 없음/측정 불가", key="ped_spo2_na", value=True)
        spo2         = None if spo2_unknown else _parse_num_ped("산소포화도(%)", key="ped_spo2", decimals=0, placeholder="예: 96")
        urine_24h    = _parse_num_ped("24시간 소변 횟수", key="ped_u", decimals=0, placeholder="예: 6")
        retraction   = _parse_num_ped("흉곽 함몰(0/1)", key="ped_ret", decimals=0, placeholder="0 또는 1")
        nasal_flaring= _parse_num_ped("콧벌렁임(0/1)", key="ped_nf", decimals=0, placeholder="0 또는 1")
        apnea        = _parse_num_ped("무호흡(0/1)", key="ped_ap", decimals=0, placeholder="0 또는 1")

        with st.expander("증상(간단 선택)", expanded=True):
            runny = st.selectbox("콧물", ["없음","흰색","노란색","피섞임"], key="ped_runny")
            cough_sev = st.selectbox("기침", ["없음","조금","보통","심함"], key="ped_cough_sev")
            st.session_state["ped_simple_sym"] = {"콧물": runny, "기침": cough_sev}

        with st.expander("보호자 관찰 체크리스트", expanded=False):
            obs = {}
            obs["숨 가빠보임(호흡곤란)"] = st.checkbox("숨 가빠보임(호흡곤란)", key="obs1")
            obs["청색증 의심(입술/손발)"] = st.checkbox("청색증 의심(입술/손발)", key="obs2")
            obs["말수 감소·축 늘어짐"]   = st.checkbox("말수 감소·축 늘어짐/보챔", key="obs3")
            obs["탈수 의심(마른 입술/눈물 적음/소변 감소)"] = st.checkbox("탈수 의심(마른 입술/눈물 적음/소변 감소)", key="obs4")
            obs["고열(≥40.0℃)"] = st.checkbox("고열(≥40.0℃)", key="obs5")
            obs["3개월 미만 발열(≥38.0℃)"] = st.checkbox("3개월 미만 발열(≥38.0℃)", key="obs6")
            obs["경련(열성경련 포함)"] = st.checkbox("경련(열성경련 포함)", key="obs7")
            st.session_state["ped_obs"] = {k:v for k,v in obs.items() if v}

        with st.expander("해열제 용량 계산기", expanded=False):
            wt = st.text_input("체중(kg)", key="antipy_wt", placeholder="예: 10.5")
            med = st.selectbox("해열제", ["아세트아미노펜(acetaminophen)", "이부프로펜(ibuprofen)"], key="antipy_med")
            if med.startswith("아세트"):
                mg_low, mg_high = dose_acetaminophen(wt)
                conc = st.selectbox("시럽 농도", ["160 mg/5 mL", "120 mg/5 mL"], key="antipy_conc_acet")
                if mg_low and mg_high:
                    try:
                        mg_num = int(conc.split("mg/")[0])
                        ml_denom = int(conc.split("mg/")[1].split()[0].replace("mL",""))
                    except Exception:
                        mg_num, ml_denom = 160, 5
                    ml_low  = round(mg_low  * ml_denom / mg_num, 1)
                    ml_high = round(mg_high * ml_denom / mg_num, 1)
                    st.info(f"권장 1회: {mg_low}–{mg_high} mg ≈ {ml_low}–{ml_high} mL ({conc})")
                    st.caption("간격 4–6시간, 최대 5회/일")
            else:
                mg_low, mg_high = dose_ibuprofen(wt)
                conc = st.selectbox("시럽 농도", ["100 mg/5 mL"], key="antipy_conc_ibu")
                if mg_low and mg_high:
                    mg_num, ml_denom = 100, 5
                    ml_low  = round(mg_low  * ml_denom / mg_num, 1)
                    ml_high = round(mg_high * ml_denom / mg_num, 1)
                    st.info(f"권장 1회: {mg_low}–{mg_high} mg ≈ {ml_low}–{ml_high} mL ({conc})")
                    st.caption("간격 6–8시간, 생후 6개월 미만은 의료진 상담")

    # -------------------- 특수검사/확장 --------------------
    extra_vals = {}

    if mode == "일반/암":
        st.divider()
        st.header("3️⃣ 특수 검사(토글)")

        col = st.columns(4)
        with col[0]:
            t_coag = st.checkbox("응고패널(PT/aPTT 등)")
        with col[1]:
            t_comp = st.checkbox("보체 검사(C3/C4/CH50)")
        with col[2]:
            t_urine_basic = st.checkbox("요검사(알부민/잠혈/요당/요Cr)")
        with col[3]:
            t_lipid_basic = st.checkbox("지질 기본(TG/TC)")

        if t_coag:
            st.markdown("**응고패널**")
            extra_vals["PT"] = num_input_generic("PT (sec)", key="ex_pt", decimals=1, placeholder="예: 12.0")
            extra_vals["aPTT"] = num_input_generic("aPTT (sec)", key="ex_aptt", decimals=1, placeholder="예: 32.0")
            extra_vals["Fibrinogen"] = num_input_generic("Fibrinogen (mg/dL)", key="ex_fbg", decimals=1, placeholder="예: 250")
            extra_vals["D-dimer"] = num_input_generic("D-dimer (µg/mL FEU)", key="ex_dd", decimals=2, placeholder="예: 0.50")

        if t_comp:
            st.markdown("**보체(C3/C4/CH50)**")
            extra_vals["C3"] = num_input_generic("C3 (mg/dL)", key="ex_c3", decimals=1, placeholder="예: 90")
            extra_vals["C4"] = num_input_generic("C4 (mg/dL)", key="ex_c4", decimals=1, placeholder="예: 20")
            extra_vals["CH50"] = num_input_generic("CH50 (U/mL)", key="ex_ch50", decimals=1, placeholder="예: 50")

        if t_urine_basic:
            st.markdown("**요검사(기본)** — 정성 + 정량(선택)")
            cq = st.columns(4)
            with cq[0]:
                hematuria_q = st.selectbox("혈뇨(정성)", ["", "+", "++", "+++"], index=0)
            with cq[1]:
                proteinuria_q = st.selectbox("알부민 소변(정성)", ["", "+", "++", "+++"], index=0)
            with cq[2]:
                wbc_q = st.selectbox("백혈구(정성)", ["", "+", "++", "+++"], index=0)
            with cq[3]:
                gly_q = st.selectbox("요당(정성)", ["", "+", "++", "+++"], index=0)

            u_rbc_hpf = num_input_generic("적혈구(소변, /HPF)", key="u_rbc_hpf", decimals=0, placeholder="예: 3")
            u_wbc_hpf = num_input_generic("백혈구(소변, /HPF)", key="u_wbc_hpf", decimals=0, placeholder="예: 10")
            if entered(u_rbc_hpf): extra_vals["적혈구(소변, /HPF)"] = u_rbc_hpf
            if entered(u_wbc_hpf): extra_vals["백혈구(소변, /HPF)"] = u_wbc_hpf

            _desc_hema = {"+":"소량","++":"중등도","+++":"고농도"}
            _desc_prot = {"+":"경도","++":"중등도","+++":"고농도"}
            _desc_wbc  = {"+":"의심","++":"양성","+++":"고농도"}
            _desc_gly  = {"+":"경도","++":"중등도","+++":"고농도"}

            if hematuria_q:   extra_vals["혈뇨(정성)"] = f"{hematuria_q} ({_desc_hema.get(hematuria_q,'')})"
            if proteinuria_q: extra_vals["알부민 소변(정성)"] = f"{proteinuria_q} ({_desc_prot.get(proteinuria_q,'')})"
            if wbc_q:         extra_vals["백혈구뇨(정성)"] = f"{wbc_q} ({_desc_wbc.get(wbc_q,'')})"
            if gly_q:         extra_vals["요당(정성)"] = f"{gly_q} ({_desc_gly.get(gly_q,'')})"

            with st.expander("정량(선택) — UPCR/ACR 계산", expanded=False):
                u_prot = num_input_generic("요단백 (mg/dL)", key="ex_upr", decimals=1, placeholder="예: 30")
                u_cr   = num_input_generic("소변 Cr (mg/dL)", key="ex_ucr", decimals=1, placeholder="예: 100")
                u_alb  = num_input_generic("소변 알부민 (mg/L)", key="ex_ualb", decimals=1, placeholder="예: 30")
                upcr = acr = None
                if entered(u_cr) and entered(u_prot):
                    upcr = round((u_prot * 1000.0) / float(u_cr), 1)
                    st.info(f"UPCR(요단백/Cr): {upcr} mg/g")
                if entered(u_cr) and entered(u_alb):
                    acr = round((u_alb * 100.0) / float(u_cr), 1)
                    st.info(f"ACR(소변 알부민/Cr): {acr} mg/g")
                upcr_manual = num_input_generic("Pro/Cr, urine (mg/g)", key="ex_upcr_manual", decimals=1, placeholder="예: 350.0")
                if entered(upcr_manual): upcr = upcr_manual
                if entered(acr):
                    extra_vals["ACR(mg/g)"] = acr
                    a, a_label = stage_acr(acr)
                    if a: st.caption(f"Albuminuria stage: {a} · {a_label}"); extra_vals["Albuminuria stage"] = f"{a} ({a_label})"
                if entered(upcr): extra_vals["UPCR(mg/g)"] = upcr
                extra_vals["Urine Cr"] = u_cr; extra_vals["Urine albumin"] = u_alb

        if t_lipid_basic:
            st.markdown("**지질(기본)**")
            extra_vals["TG"] = num_input_generic("Triglyceride (TG, mg/dL)", key="ex_tg", decimals=0, placeholder="예: 150")
            extra_vals["TC"] = num_input_generic("Total Cholesterol (TC, mg/dL)", key="ex_tc", decimals=0, placeholder="예: 180")

        # 확장 패널
        st.subheader("➕ 확장 패널")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            t_anemia = st.checkbox("빈혈 패널"); t_elect  = st.checkbox("전해질 확장")
        with c2:
            t_kidney = st.checkbox("신장/단백뇨"); t_thy    = st.checkbox("갑상선")
        with c3:
            t_sepsis = st.checkbox("염증/패혈증"); t_glu    = st.checkbox("당대사/대사증후군")
        with c4:
            t_lipidx = st.checkbox("지질 확장");  t_biomkr = st.checkbox("암별 분자/표지자")

        if t_anemia:
            st.markdown("**빈혈 패널**")
            extra_vals["Fe(철)"] = num_input_generic("Fe (µg/dL)", key="an_fe", decimals=0, placeholder="예: 60")
            extra_vals["Ferritin"] = num_input_generic("Ferritin (ng/mL)", key="an_ferr", decimals=1, placeholder="예: 80")
            extra_vals["TIBC"] = num_input_generic("TIBC (µg/dL)", key="an_tibc", decimals=0, placeholder="예: 330")
            extra_vals["Transferrin sat.(%)"] = num_input_generic("Transferrin Sat. (TSAT, %)", key="an_tsat", decimals=1, placeholder="예: 18.0")
            extra_vals["Reticulocyte(%)"] = num_input_generic("망상적혈구(%) (Retic %)", key="an_retic", decimals=1, placeholder="예: 1.2")
            extra_vals["Vitamin B12"] = num_input_generic("비타민 B12 (pg/mL)", key="an_b12", decimals=0, placeholder="예: 400")
            extra_vals["Folate"] = num_input_generic("엽산(Folate, ng/mL)", key="an_folate", decimals=1, placeholder="예: 6.0")

        if t_elect:
            st.markdown("**전해질 확장**")
            extra_vals["Mg"] = num_input_generic("Mg (mg/dL)", key="el_mg", decimals=2, placeholder="예: 2.0")
            extra_vals["Phos(인)"] = num_input_generic("Phosphate (mg/dL)", key="el_phos", decimals=2, placeholder="예: 3.5")
            extra_vals["iCa(이온화칼슘)"] = num_input_generic("이온화칼슘 iCa (mmol/L)", key="el_ica", decimals=2, placeholder="예: 1.15")
            ca_corr = calc_corrected_ca(vals.get(LBL_Ca), vals.get(LBL_Alb))
            if ca_corr is not None:
                st.info(f"보정 칼슘(Alb 반영): {ca_corr} mg/dL")
                st.caption("공식: Ca + 0.8×(4.0 - Alb)")
                extra_vals["Corrected Ca"] = ca_corr

        if t_kidney:
            st.markdown("**신장/단백뇨**")
            age = num_input_generic("나이(추정, eGFR 계산용)", key="kid_age", decimals=0, placeholder="예: 40")
            sex = st.selectbox("성별", ["F","M"], key="kid_sex")
            egfr = calc_egfr(vals.get(LBL_Cr), age=age or 60, sex=sex)
            if egfr is not None:
                st.info(f"eGFR(자동): {egfr} mL/min/1.73m²")
                extra_vals["eGFR"] = egfr
                g, g_label = stage_egfr(egfr)
                if g: st.caption(f"CKD G-stage: {g} · {g_label}"); extra_vals["CKD G-stage"] = f"{g} ({g_label})"

        if t_thy:
            st.markdown("**갑상선 패널**")
            extra_vals["TSH"] = num_input_generic("TSH (µIU/mL)", key="thy_tsh", decimals=2, placeholder="예: 1.50")
            extra_vals["Free T4"] = num_input_generic("Free T4 (ng/dL)", key="thy_ft4", decimals=2, placeholder="예: 1.2")
            if st.checkbox("Total T3 입력", key="thy_t3_on"):
                extra_vals["Total T3"] = num_input_generic("Total T3 (ng/dL)", key="thy_t3", decimals=0, placeholder="예: 110")

        if t_sepsis:
            st.markdown("**염증/패혈증 패널**")
            extra_vals["Procalcitonin"] = num_input_generic("Procalcitonin (ng/mL)", key="sep_pct", decimals=2, placeholder="예: 0.12")
            extra_vals["Lactate"] = num_input_generic("Lactate (mmol/L)", key="sep_lac", decimals=1, placeholder="예: 1.8")

        if t_glu:
            st.markdown("**당대사/대사증후군**")
            glu_f = num_input_generic("공복혈당( mg/dL )", key="glu_f", decimals=0, placeholder="예: 95")
            extra_vals["HbA1c"] = num_input_generic("HbA1c( % )", key="glu_a1c", decimals=2, placeholder="예: 5.6")
            if st.checkbox("인슐린 입력(선택, HOMA-IR 계산)", key="glu_ins_on"):
                insulin = num_input_generic("Insulin (µU/mL)", key="glu_ins", decimals=1, placeholder="예: 8.5")
                homa = calc_homa_ir(glu_f, insulin) if entered(glu_f) and entered(insulin) else None
                if homa is not None:
                    st.info(f"HOMA-IR: {homa}")
                    st.caption("HOMA-IR = (공복혈당×인슐린)/405")
                    extra_vals["HOMA-IR"] = homa

        if t_lipidx:
            st.markdown("**지질 확장**")
            tc  = extra_vals.get("TC") or num_input_generic("Total Cholesterol (mg/dL)", key="lx_tc", decimals=0, placeholder="예: 180")
            hdl = num_input_generic("HDL-C (mg/dL)", key="lx_hdl", decimals=0, placeholder="예: 50")
            tg  = extra_vals.get("TG") or num_input_generic("Triglyceride (mg/dL)", key="lx_tg", decimals=0, placeholder="예: 120")
            ldl_fw = calc_friedewald_ldl(tc, hdl, tg)
            try:
                if entered(tg) and float(tg) >= 400:
                    st.warning("TG ≥ 400 mg/dL: Friedewald LDL 계산 비활성화.")
            except Exception:
                pass
            non_hdl = calc_non_hdl(tc, hdl) if entered(tc) and entered(hdl) else None
            if non_hdl is not None:
                st.info(f"Non-HDL-C: {non_hdl} mg/dL"); extra_vals["Non-HDL-C"] = non_hdl
            if ldl_fw is not None:
                st.info(f"Friedewald LDL(자동): {ldl_fw} mg/dL (TG<400에서만)"); extra_vals["LDL(Friedewald)"] = ldl_fw
            extra_vals["ApoB"] = num_input_generic("ApoB (mg/dL)", key="lx_apob", decimals=0, placeholder="예: 90")

        if t_biomkr and group and cancer:
            st.markdown("**암별 분자/표지자 (조건부 노출)**")
            if group == "고형암":
                if "폐암" in cancer:
                    st.caption("폐암: EGFR/ALK/ROS1/RET/NTRK, PD-L1(CPS)")
                    extra_vals["EGFR"] = st.text_input("EGFR 변이", key="bio_egfr")
                    extra_vals["ALK"] = st.text_input("ALK 재배열", key="bio_alk")
                    extra_vals["ROS1"] = st.text_input("ROS1 재배열", key="bio_ros1")
                    extra_vals["RET"] = st.text_input("RET 재배열", key="bio_ret")
                    extra_vals["NTRK"] = st.text_input("NTRK 융합", key="bio_ntrk")
                    extra_vals["PD-L1(CPS)"] = num_input_generic("PD-L1 CPS(%)", key="bio_pdl1", decimals=0, placeholder="예: 50")
                elif "위암" in cancer or "대장암" in cancer:
                    st.caption("위/대장: MSI-H/dMMR")
                    extra_vals["MSI/MMR"] = st.text_input("MSI-H/dMMR 여부", key="bio_msi")
                elif "난소암" in cancer or "유방암" in cancer:
                    st.caption("난소/유방: BRCA1/2")
                    extra_vals["BRCA1/2"] = st.text_input("BRCA1/2 변이", key="bio_brca")
                elif "간암" in cancer:
                    st.caption("간암(HCC): 필요 시 Child-Pugh와 함께 기록")
            elif group == "혈액암":
                key = heme_key_map.get(cancer, cancer)
                if key == "AML":
                    st.caption("AML: FLT3-ITD / NPM1 등")
                    extra_vals["FLT3-ITD"] = st.text_input("FLT3-ITD", key="bio_flt3")
                    extra_vals["NPM1"] = st.text_input("NPM1", key="bio_npm1")
                elif key == "CLL":
                    st.caption("CLL: IGHV / TP53")
                    extra_vals["IGHV"] = st.text_input("IGHV", key="bio_ighv")
                    extra_vals["TP53"] = st.text_input("TP53", key="bio_tp53")
                elif key == "CML":
                    st.caption("CML: BCR-ABL(IS)")
                    extra_vals["BCR-ABL(IS)"] = num_input_generic("BCR-ABL(IS, %)", key="bio_bcrabl", decimals=2, placeholder="예: 0.12")

    # -------------------- 암별 디테일(토글) --------------------
    if mode == "일반/암" and group and group != "미선택/일반" and cancer:
        st.divider()
        if st.checkbox("4️⃣ 암별 디테일(토글)", value=False, help="자주 나가지 않아 기본은 숨김"):
            st.header("암별 디테일 수치")
            if group == "혈액암":
                key = heme_key_map.get(cancer, cancer)
                if key in ["AML","APL"]:
                    extra_vals["DIC Score"] = num_input_generic("DIC Score (pt)", key="ex_dic", decimals=0, placeholder="예: 3")
            elif group == "육종":
                extra_vals["CK"] = num_input_generic("CK(U/L)", key="ex_ck", decimals=0, placeholder="예: 150")

    # 스케줄/그래프 (있으면 렌더)
    try: render_schedule(nickname_key)
    except Exception: pass

    st.divider()
    _prof = "adult"  # 안전 기본값 (분기 미도달 대비)
    run = st.button("🔎 해석하기", use_container_width=True)

    if run:
        st.subheader(f"📋 해석 결과 — {nickname}#{pin if pin else '----'}")

        if mode == "일반/암":
            lines = interpret_labs(vals, extras)
            for line in lines: st.write(line)

            urine_lines = _interpret_urine(extra_vals)
            if urine_lines:
                st.markdown("### 🧪 요검사 해석")
                for ul in urine_lines: st.write(ul)

            ref_profile = st.radio("컷오프 기준", ["성인(기본)", "소아"], index=0, horizontal=True, help="지질/일부 항목은 소아 기준이 다릅니다")
            _prof = "peds" if ref_profile == "소아" else "adult"
            spec_lines = interpret_specials(extra_vals, vals, profile=_prof)
            if spec_lines:
                st.markdown("### 🧬 특수검사 해석")
                for sl in spec_lines: st.markdown(sl, unsafe_allow_html=True)

            if nickname_key and st.session_state.records.get(nickname_key):
                st.markdown("### 🔍 수치 변화 비교 (이전 기록 대비)")
                cmp_lines = compare_with_previous(nickname_key, {k: vals.get(k) for k in ORDER if entered(vals.get(k))})
                if cmp_lines:
                    for l in cmp_lines: st.write(l)
                else:
                    st.info("비교할 이전 기록이 없거나 값이 부족합니다.")

            shown = [(k, v) for k, v in (extra_vals or {}).items() if entered(v) or isinstance(v, dict)]
            if shown:
                st.markdown("### 🧬 특수/확장/암별 디테일 수치")
                for k, v in shown: st.write(f"- {k}: {v}")

            fs = food_suggestions(vals, anc_place)
            if fs:
                st.markdown("### 🥗 음식 가이드 (계절/레시피 포함)")
                for f in fs: st.markdown(f)

        elif mode == "소아(일상/호흡기)":
            st.info("위 위험도 배너를 참고하세요.")
        else:
            st.success("선택한 감염질환 요약을 보고서에 포함했습니다.")

        if meds:
            st.markdown("### 💊 항암제 부작용·상호작용 요약")
            for line in summarize_meds(meds): st.write(line)

        if extras.get("abx"):
            abx_lines = abx_summary(extras["abx"])
            if abx_lines:
                st.markdown("### 🧪 항생제 주의 요약")
                for l in abx_lines: st.write(l)

        st.markdown("### 🌡️ 발열 가이드")
        st.write(FEVER_GUIDE)

        # 메타/보고서
        meta = {"group": group, "cancer": cancer, "infect_sel": infect_sel, "anc_place": anc_place, "ped_topic": ped_topic}
        if mode == "소아(일상/호흡기)":
            def _ent(x):
                try: return x is not None and float(x) != 0
                except Exception: return False
            meta["ped_inputs"] = {}
            for k, lab in [("나이(개월)", "ped_age"), ("체온(℃)", "ped_temp"), ("호흡수(/분)", "ped_rr"), ("SpO₂(%)", "ped_spo2"), ("24시간 소변 횟수", "ped_u"),
                           ("흉곽 함몰", "ped_ret"), ("콧벌렁임", "ped_nf"), ("무호흡", "ped_ap")]:
                v = st.session_state.get(lab)
                if _ent(v): meta["ped_inputs"][k] = v
        elif mode == "소아(감염질환)":
            info = PED_INFECT.get(infect_sel, {})
            meta["infect_info"] = {"핵심": info.get("핵심",""), "진단": info.get("진단",""), "특징": info.get("특징","")}
            meta["infect_symptoms"] = st.session_state.get("infect_symptoms", [])
            core = st.session_state.get("ped_infect_core", {})
            if core: meta["infect_core"] = core

        meds_lines = summarize_meds(meds) if meds else []
        abx_lines = abx_summary(extras.get("abx", {})) if extras.get("abx") else []
        cmp_lines = compare_with_previous(nickname_key, {k: vals.get(k) for k in ORDER if entered(vals.get(k))}) if (mode=="일반/암") else []
        food_lines = food_suggestions(vals, anc_place) if (mode=="일반/암") else []

        a4_opt = st.checkbox("A4 프린트 최적화(섹션 구분선 추가)", value=True)
        urine_lines_for_report = _interpret_urine(extra_vals)
        spec_lines_for_report = interpret_specials(extra_vals, vals, profile=_prof)
        report_md = build_report(mode, meta, {k: vals.get(k) for k in ORDER if entered(vals.get(k))}, cmp_lines, extra_vals, meds_lines, food_lines, abx_lines)
        if urine_lines_for_report:
            report_md += "\n\n---\n\n### 🧪 요검사 해석\n" + "\n".join(["- " + _strip_html(l) for l in urine_lines_for_report])
        if spec_lines_for_report:
            report_md += "\n\n### 🧬 특수검사 해석\n" + "\n".join(["- " + _strip_html(l) for l in spec_lines_for_report])
        report_md += "\n\n---\n\n### 🌡️ 발열 가이드\n" + FEVER_GUIDE + "\n\n> " + DISCLAIMER
        if a4_opt:
            report_md = report_md.replace("### ", "\n\n---\n\n### ")

        st.download_button("📥 보고서(.md) 다운로드", data=report_md.encode("utf-8"),
                           file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                           mime="text/markdown")
        st.download_button("📄 보고서(.txt) 다운로드", data=report_md.encode("utf-8"),
                           file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                           mime="text/plain")

        try:
            pdf_bytes = md_to_pdf_bytes_fontlocked(report_md)
            st.info("PDF 생성 시 사용 폰트: NanumGothic(제목 Bold/ExtraBold 있으면 자동 적용)")
            st.download_button("🖨️ 보고서(.pdf) 다운로드", data=pdf_bytes,
                               file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                               mime="application/pdf")
        except FileNotFoundError as e:
            st.warning(str(e))
        except Exception:
            st.info("PDF 모듈이 없거나 오류가 발생했습니다. (pip install reportlab)")

        if nickname_key and nickname_key.strip():
            rec = {
                "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "mode": mode, "group": group, "cancer": cancer, "infect": infect_sel,
                "labs": {k: vals.get(k) for k in ORDER if entered(vals.get(k))},
                "extra": {k: v for k, v in (locals().get('extra_vals') or {}).items() if entered(v) or isinstance(v, dict)},
                "meds": meds, "extras": extras,
            }
            st.session_state.records.setdefault(nickname_key, []).append(rec)
            st.success("저장되었습니다. 아래 그래프에서 추이를 확인하세요.")
        else:
            st.info("별명과 PIN을 입력하면 추이 그래프를 사용할 수 있어요.")

    try: render_graphs()
    except Exception: pass

    st.caption(FOOTER_CAFE)
    st.markdown("> " + DISCLAIMER)
    try: st.caption(f"🧩 패키지: {PKG} · 모듈 로딩 정상(폴백 포함)")
    except Exception: pass

if __name__ == "__main__":
    main()

