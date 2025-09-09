
# -*- coding: utf-8 -*-
from datetime import datetime, date
import os
import streamlit as st
import importlib

# ---- Robust dynamic imports (package-aware) ----
PKG = os.path.basename(os.path.dirname(__file__))

def _load_mod(path_in_pkg):
    """
    Try to import a module inside the current package (PKG.path_in_pkg).
    If that fails, try importing as a top-level module (path_in_pkg).
    Return the imported module or None.
    """
    for modname in (f"{PKG}.{path_in_pkg}", path_in_pkg):
        try:
            return importlib.import_module(modname)
        except Exception:
            continue
    return None

# config
_cfg = _load_mod("config")
if _cfg is None:
    raise ImportError("Cannot import config module (tried both package and top-level).")
APP_TITLE = getattr(_cfg, "APP_TITLE", "BloodMap")
PAGE_TITLE = getattr(_cfg, "PAGE_TITLE", "BloodMap")
MADE_BY = getattr(_cfg, "MADE_BY", "")
CAFE_LINK_MD = getattr(_cfg, "CAFE_LINK_MD", "")
FOOTER_CAFE = getattr(_cfg, "FOOTER_CAFE", "")
DISCLAIMER = getattr(_cfg, "DISCLAIMER", "")
ORDER = getattr(_cfg, "ORDER", [])
FEVER_GUIDE = getattr(_cfg, "FEVER_GUIDE", "")
LBL_WBC = getattr(_cfg, "LBL_WBC", "WBC")
LBL_Hb = getattr(_cfg, "LBL_Hb", "Hb")
LBL_PLT = getattr(_cfg, "LBL_PLT", "PLT")
LBL_ANC = getattr(_cfg, "LBL_ANC", "ANC")
LBL_Ca = getattr(_cfg, "LBL_Ca", "Ca")
LBL_P = getattr(_cfg, "LBL_P", "P")
LBL_Na = getattr(_cfg, "LBL_Na", "Na")
LBL_K = getattr(_cfg, "LBL_K", "K")
LBL_Alb = getattr(_cfg, "LBL_Alb", "Alb")
LBL_Glu = getattr(_cfg, "LBL_Glu", "Glu")
LBL_TP = getattr(_cfg, "LBL_TP", "TP")
LBL_AST = getattr(_cfg, "LBL_AST", "AST")
LBL_ALT = getattr(_cfg, "LBL_ALT", "ALT")
LBL_LDH = getattr(_cfg, "LBL_LDH", "LDH")
LBL_CRP = getattr(_cfg, "LBL_CRP", "CRP")
LBL_Cr = getattr(_cfg, "LBL_Cr", "Cr")
LBL_UA = getattr(_cfg, "LBL_UA", "UA")
LBL_TB = getattr(_cfg, "LBL_TB", "TB")
LBL_BUN = getattr(_cfg, "LBL_BUN", "BUN")
LBL_BNP = getattr(_cfg, "LBL_BNP", "BNP")
FONT_PATH_REG = getattr(_cfg, "FONT_PATH_REG", None)

# data modules
_drugs = _load_mod("data.drugs")
_foods = _load_mod("data.foods")
_ped = _load_mod("data.ped")

ANTICANCER = getattr(_drugs, "ANTICANCER", {}) if _drugs else {}
ABX_GUIDE = getattr(_drugs, "ABX_GUIDE", {}) if _drugs else {}
FOODS = getattr(_foods, "FOODS", {}) if _foods else {}

PED_TOPICS = getattr(_ped, "PED_TOPICS", {})
PED_INPUTS_INFO = getattr(_ped, "PED_INPUTS_INFO", "")
PED_INFECT = getattr(_ped, "PED_INFECT", {})
PED_SYMPTOMS = getattr(_ped, "PED_SYMPTOMS", {})
PED_RED_FLAGS = getattr(_ped, "PED_RED_FLAGS", {})

# utils modules
_utils_inputs = _load_mod("utils.inputs")
_utils_interpret = _load_mod("utils.interpret")
_utils_reports = _load_mod("utils.reports")
_utils_graphs = _load_mod("utils.graphs")
_utils_schedule = _load_mod("utils.schedule")

if not all([_utils_inputs, _utils_interpret, _utils_reports, _utils_graphs, _utils_schedule]):
    raise ImportError("Cannot import required utils modules under the package.")

num_input_generic = getattr(_utils_inputs, "num_input_generic")
entered = getattr(_utils_inputs, "entered")
_parse_numeric = getattr(_utils_inputs, "_parse_numeric")

interpret_labs = getattr(_utils_interpret, "interpret_labs")
compare_with_previous = getattr(_utils_interpret, "compare_with_previous")
food_suggestions = getattr(_utils_interpret, "food_suggestions")
summarize_meds = getattr(_utils_interpret, "summarize_meds")
abx_summary = getattr(_utils_interpret, "abx_summary")

build_report = getattr(_utils_reports, "build_report")
md_to_pdf_bytes_fontlocked = getattr(_utils_reports, "md_to_pdf_bytes_fontlocked")

render_graphs = getattr(_utils_graphs, "render_graphs")
render_schedule = getattr(_utils_schedule, "render_schedule")

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

def _load_css():
    try:
        st.markdown('<style>'+open(os.path.join(os.path.dirname(__file__), "style.css"), "r", encoding="utf-8").read()+'</style>', unsafe_allow_html=True)
    except Exception:
        pass

# === 계산 유틸 ===
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


def stage_egfr(egfr):
    """Return (stage, label) per KDIGO based on eGFR (mL/min/1.73m²)."""
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
    """Return (stage, label) A1/A2/A3 based on UACR mg/g."""
    try:
        a = float(acr_mg_g)
    except Exception:
        return None, None
    if a < 30: return "A1", "정상-경도 증가 (<30 mg/g)"
    if a <= 300: return "A2", "중등도 증가 (30–300 mg/g)"
    return "A3", "중증 증가 (>300 mg/g)"

def child_pugh_score(albumin, bilirubin, inr, ascites, enceph):
    """
    albumin g/dL, bilirubin mg/dL, inr float,
    ascites: '없음','경미','중증'
    enceph: '없음','경미','중증'
    Return (score, klass[A/B/C]).
    """
    def _alb(a):
        try:
            a=float(a)
        except Exception:
            return 0
        if a > 3.5: return 1
        if 2.8 <= a <= 3.5: return 2
        return 3
    def _tb(b):
        try:
            b=float(b)
        except Exception:
            return 0
        if b < 2: return 1
        if 2 <= b <= 3: return 2
        return 3
    def _inr(x):
        try:
            x=float(x)
        except Exception:
            return 0
        if x < 1.7: return 1
        if 1.7 <= x <= 2.3: return 2
        return 3
    def _cat(v):
        if v == "없음": return 1
        if v == "경미": return 2
        if v == "중증": return 3
        return 0
    s = _alb(albumin) + _tb(bilirubin) + _inr(inr) + _cat(ascites) + _cat(enceph)
    if s == 0:
        return 0, None
    if 5 <= s <= 6: k="A"
    elif 7 <= s <= 9: k="B"
    else: k="C"
    return s, k


def dose_acetaminophen(weight_kg):
    """Return (low_mg, high_mg) per dose using 10–15 mg/kg."""
    try:
        w = float(weight_kg)
        return round(w*10), round(w*15)
    except Exception:
        return None, None

def dose_ibuprofen(weight_kg):
    """Return (low_mg, high_mg) per dose using 5–10 mg/kg."""
    try:
        w = float(weight_kg)
        return round(w*5), round(w*10)
    except Exception:
        return None, None

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
        r = float(rbc)
        if r <= 2:
            lines.append(f"소변 적혈구(/HPF): {int(r)} — **정상범위(0–2)**로 보입니다.")
        elif 3 <= r <= 5:
            lines.append(f"소변 적혈구(/HPF): {int(r)} — **경미한 혈뇨 가능**(운동/생리/채뇨오염 확인 후 추적).")
        else:
            lines.append(f"소변 적혈구(/HPF): {int(r)} — **유의한 혈뇨** 가능. 반복 검사·원인 평가(UTI/결석 등) 고려.")
    if _isnum(wbc):
        w = float(wbc)
        if w <= 5:
            lines.append(f"소변 백혈구(/HPF): {int(w)} — **정상(≤5)**.")
        elif 6 <= w <= 9:
            lines.append(f"소변 백혈구(/HPF): {int(w)} — **경미한 백혈구뇨** 가능. 증상 동반 시 추적.")
        else:
            lines.append(f"소변 백혈구(/HPF): {int(w)} — **유의한 백혈구뇨(UTI 의심)** 가능. 증상·배양 고려.")
    if _isnum(upcr):
        u = float(upcr)
        if u < 150:
            lines.append(f"UPCR: {u:.1f} mg/g — **정상~경미**(<150).")
        elif u < 300:
            lines.append(f"UPCR: {u:.1f} mg/g — **경도 단백뇨**(150–300).")
        elif u < 1000:
            lines.append(f"UPCR: {u:.1f} mg/g — **중등도 단백뇨**(300–1000).")
        else:
            lines.append(f"UPCR: {u:.1f} mg/g — **중증 단백뇨**(>1000).")
    if _isnum(acr):
        a = float(acr)
        if a < 30:
            lines.append(f"ACR: {a:.1f} mg/g — **A1(정상-경도)**.")
        elif a <= 300:
            lines.append(f"ACR: {a:.1f} mg/g — **A2(중등도 증가)**.")
        else:
            lines.append(f"ACR: {a:.1f} mg/g — **A3(중증 증가)**.")
    if lines:
        lines.append("※ 해석은 참고용입니다. 증상이 있거나 수치가 반복 상승하면 의료진과 상담하세요.")
    return lines


def main():
    st.set_page_config(page_title=PAGE_TITLE, layout="centered")
    _load_css()
    st.title(APP_TITLE)
    st.markdown(MADE_BY)
    st.markdown(CAFE_LINK_MD)

    st.markdown("### 🔗 공유하기")
    c1, c2, c3 = st.columns([1,1,2])
    with c1:
        st.link_button("📱 카카오톡/메신저", "https://hdzwo5ginueir7hknzzfg4.streamlit.app/")
    with c2:
        st.link_button("📝 카페/블로그", "https://cafe.naver.com/bloodmap")
    with c3:
        st.code("https://hdzwo5ginueir7hknzzfg4.streamlit.app/", language="text")
    st.caption("✅ 모바일 줄꼬임 방지 · 별명+PIN 저장/그래프 · 암별/소아/희귀암/육종 패널 · PDF 한글 폰트 고정 · 수치 변화 비교 · 항암 스케줄표 · ANC 가이드")

    # 조회수
    try:
        from .utils import counter as _bm_counter
        _bm_counter.bump()
        st.caption(f"👀 조회수(방문): {_bm_counter.count()}")
    except Exception:
        pass

    if "records" not in st.session_state:
        st.session_state.records = {}
    if "schedules" not in st.session_state:
        st.session_state.schedules = {}

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

    if mode == "일반/암":
        group = st.selectbox("암 그룹 선택", ["미선택/일반", "혈액암", "고형암", "육종", "희귀암"])
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
        else:
            st.info("암 그룹을 선택하면 해당 암종에 맞는 **항암제 목록과 추가 수치 패널**이 자동 노출됩니다.")
    elif mode == "소아(일상/호흡기)":
        st.markdown("### 🧒 소아 일상 주제 선택")
        st.caption(PED_INPUTS_INFO)
        ped_topic = st.selectbox("소아 주제", ["일상 케어","수분 섭취","해열제 사용","기침/콧물 관리"])
    else:
        st.markdown("### 🧫 소아·영유아 감염질환")
        infect_sel = st.selectbox("질환 선택", list(PED_INFECT.keys()))
        info = PED_INFECT.get(infect_sel, {})
        st.info(f"핵심: {info.get('핵심','')} · 진단: {info.get('진단','')} · 특징: {info.get('특징','')}")
        with st.expander("🧒 기본 활력/계측 입력", expanded=False):
            age_m_gi = st.text_input("나이(개월)", key="pedinf_age_m", placeholder="예: 18")
            temp_c_gi = st.text_input("체온(℃)", key="pedinf_temp_c", placeholder="예: 38.2")
            rr_gi = st.text_input("호흡수(/분)", key="pedinf_rr", placeholder="예: 42")
            spo2_na_gi = st.checkbox("산소포화도 측정기 없음/측정 불가", key="pedinf_spo2_na", value=True)
        if not spo2_na_gi:
            spo2_gi = st.text_input("산소포화도(%)", key="pedinf_spo2", placeholder="예: 96")
        else:
            spo2_gi = ""
            hr_gi = st.text_input("심박수(/분)", key="pedinf_hr", placeholder="예: 120")
            wt_kg_gi = st.text_input("체중(kg)", key="pedinf_wt", placeholder="예: 10.5")

        with st.expander("👀 보호자 관찰 체크리스트", expanded=False):
            obs2 = {}
            obs2["숨 가빠보임(호흡곤란)"] = st.checkbox("숨 가빠보임(호흡곤란)", key="gi_obs1")
            obs2["청색증 의심(입술/손발)"] = st.checkbox("청색증 의심(입술/손발)", key="gi_obs2")
            obs2["말수 감소·축 늘어짐"]   = st.checkbox("말수 감소·축 늘어짐/보챔", key="gi_obs3")
            obs2["탈수 의심(마른입/눈물↓/소변↓)"] = st.checkbox("탈수 의심(마른 입술/눈물 적음/소변 감소)", key="gi_obs4")
            obs2["고열(≥40.0℃)"] = st.checkbox("고열(≥40.0℃)", key="gi_obs5")
            obs2["3개월 미만 발열(≥38.0℃)"] = st.checkbox("3개월 미만 발열(≥38.0℃)", key="gi_obs6")
            obs2["경련(열성경련 포함)"] = st.checkbox("경련(열성경련 포함)", key="gi_obs7")
            st.session_state["ped_obs_gi"] = {k:v for k,v in obs2.items() if v}

        # 👶 질환별 핵심 입력(간단)
        with st.expander("👶 질환별 핵심 입력(간단)", expanded=True):
            core = {}
            name = (infect_sel or "").lower()

            # 아데노바이러스(PCF) — 눈곱/결막충혈
            if ("아데노" in name) or ("adeno" in name) or ("pcf" in name):
                eye_opt = st.selectbox("눈곱(eye discharge)", ["없음", "있음"], key="gi_adeno_eye")
                core["눈곱"] = eye_opt
                core["결막충혈"] = st.checkbox("결막 충혈/충혈성 눈", key="gi_adeno_conj")

            # 파라인플루엔자 — 설사 횟수(간단)
            if ("파라" in name) or ("parainfluenza" in name):
                core["설사 횟수(회/일)"] = st.number_input("설사 횟수(회/일)", min_value=0, max_value=50, step=1, key="gi_para_stool")

            # 로타/노로 — 설사/구토 횟수
            if ("로타" in name) or ("rotavirus" in name) or ("노로" in name) or ("norovirus" in name):
                core["설사 횟수(회/일)"] = st.number_input("설사 횟수(회/일)", min_value=0, max_value=50, step=1, key="gi_rota_stool")
                core["구토 횟수(회/일)"] = st.number_input("구토 횟수(회/일)", min_value=0, max_value=50, step=1, key="gi_rota_vomit")

            # RSV — 쌕쌕거림/흉곽함몰
            if ("rsv" in name):
                core["쌕쌕거림(천명)"] = st.checkbox("쌕쌕거림(천명)", key="gi_rsv_wheeze")
                core["흉곽 함몰"] = st.checkbox("흉곽 함몰", key="gi_rsv_retract")

            # 인플루엔자 — 근육통/두통/기침 심함
            if ("인플루엔자" in name) or ("influenza" in name) or ("독감" in name):
                core["근육통/전신통"] = st.checkbox("근육통/전신통", key="gi_flu_myalgia")
                core["기침 심함"] = st.checkbox("기침 심함", key="gi_flu_cough")

            st.session_state["ped_infect_core"] = {k:v for k,v in core.items() if (isinstance(v, bool) and v) or (isinstance(v, str) and v) or (isinstance(v, (int,float)) and v>0)}

        with st.expander("🧮 해열제 용량 계산기", expanded=False):
            wt2 = st.text_input("체중(kg)", key="antipy_wt_gi", placeholder="예: 10.5")
            med2 = st.selectbox("해열제", ["아세트아미노펜(acetaminophen)", "이부프로펜(ibuprofen)"], key="antipy_med_gi")
            if med2.startswith("아세트"):
                mg_low, mg_high = dose_acetaminophen(wt2)
                conc2 = st.selectbox("시럽 농도", ["160 mg/5 mL", "120 mg/5 mL"], key="antipy_conc_acet_gi")
                if mg_low and mg_high:
                    try:
                        mg_num = int(conc2.split("mg/")[0])
                    except Exception:
                        mg_num = 160
                    try:
                        ml_denom = int(conc2.split("mg/")[1].split()[0].replace("mL",""))
                    except Exception:
                        ml_denom = 5
                    ml_low  = round(mg_low  * ml_denom / mg_num, 1)
                    ml_high = round(mg_high * ml_denom / mg_num, 1)
                    st.info(f"권장 1회 용량: **{mg_low}–{mg_high} mg** ≈ **{ml_low}–{ml_high} mL** ({conc2})")
                    st.caption("간격: 4–6시간, 최대 5회/일. 복용 전 제품 라벨·의료진 지침을 확인하세요.")
            else:
                mg_low, mg_high = dose_ibuprofen(wt2)
                conc2 = st.selectbox("시럽 농도", ["100 mg/5 mL"], key="antipy_conc_ibu_gi")
                if mg_low and mg_high:
                    try:
                        mg_num = int(conc2.split("mg/")[0])
                    except Exception:
                        mg_num = 100
                    try:
                        ml_denom = int(conc2.split("mg/")[1].split()[0].replace("mL",""))
                    except Exception:
                        ml_denom = 5
                    ml_low  = round(mg_low  * ml_denom / mg_num, 1)
                    ml_high = round(mg_high * ml_denom / mg_num, 1)
                    st.info(f"권장 1회 용량: **{mg_low}–{mg_high} mg** ≈ **{ml_low}–{ml_high} mL** ({conc2})")
                    st.caption("간격: 6–8시간, 생후 6개월 미만은 의료진과 상담 필요. 최대 일일 용량 준수.")

        with st.expander("🧒 증상 체크리스트", expanded=True):
            sel_sym = []
            name_l = (infect_sel or "").lower()
            # 질환별 간단 체크리스트 (없으면 공통 기본)
            base_sym = None
            if ("아데노" in name_l) or ("adeno" in name_l) or ("pcf" in name_l):
                base_sym = ["발열","결막 충혈","눈곱","인후통"]
            elif ("파라" in name_l) or ("parainfluenza" in name_l):
                base_sym = ["발열","기침","콧물"]
            elif ("로타" in name_l) or ("rotavirus" in name_l) or ("노로" in name_l) or ("norovirus" in name_l):
                base_sym = ["설사","구토","탈수 의심"]
            elif ("rsv" in name_l):
                base_sym = ["쌕쌕거림(천명)","흉곽 함몰","무호흡"]
            elif ("인플루엔자" in name_l) or ("influenza" in name_l) or ("독감" in name_l):
                base_sym = ["고열(≥38.5℃)","근육통/전신통","기침"]
            if not base_sym:
                base_sym = PED_SYMPTOMS.get(infect_sel) or PED_SYMPTOMS.get("공통") or ["발열","기침","콧물"]
            for i, s in enumerate(base_sym):
                if st.checkbox(s, key=f"sym_{infect_sel}_{i}"):
                    sel_sym.append(s)
            reds = list(set(PED_RED_FLAGS.get("공통", []) + PED_RED_FLAGS.get(infect_sel, [])))
            if reds:
                st.markdown("**🚨 레드 플래그(아래 항목이 하나라도 해당되면 진료/응급실 고려)**")
                for i, r in enumerate(reds):
                    st.checkbox(r, key=f"red_{infect_sel}_{i}")
        st.session_state["infect_symptoms"] = sel_sym



    table_mode = st.checkbox("⚙️ PC용 표 모드(가로형)", help="모바일은 세로형 고정 → 줄꼬임 없음.")

    meds = {}
    extras = {}

# === 암 모드: 항암제/항생제 입력 통합 UI ===
if False:  # disabled stray top-level block; real UI handled inside main()
    st.markdown("### 💊 항암제 선택 및 입력")
    try:
        base_list = _get_drug_list() or []
    except Exception:
        base_list = []
    drug_search = st.text_input("🔍 항암제 검색", key="drug_search")
    try:
        all_drugs = sorted(set(list(base_list) + list(ANTICANCER.keys())))
    except Exception:
        all_drugs = base_list
    drug_choices = [d for d in all_drugs if not drug_search or drug_search.lower() in d.lower() or drug_search.lower() in ANTICANCER.get(d,{}).get("alias","").lower()]
    drug_key = f"selected_drugs_{group}"
    _def = st.session_state.get(drug_key, [])
    if isinstance(_def, str):
        _def = [_def]
    _def = [x for x in _def if x in drug_choices]
    selected_drugs = st.multiselect("항암제 선택", drug_choices, default=_def, key=drug_key)
    meds = {}
    for d in selected_drugs:
        amt = num_input_generic(f"{d} - 용량/회수", key=f"med_{d}", decimals=1, placeholder="예: 1")
        if entered(amt):
            meds[d] = {"dose_or_tabs": amt}
    extras["anticancer"] = meds

    st.markdown("### 🧪 항생제 선택 및 입력")
    extras["abx"] = {}
    abx_search = st.text_input("🔍 항생제 검색", key="abx_search")
    try:
        abx_pool = list(ABX_GUIDE.keys())
    except Exception:
        abx_pool = [k for k in globals().get("ABX", {}).keys()]
    def _hit(a):
        q = (abx_search or "").lower().strip()
        if not q:
            return True
        tips = ABX_GUIDE.get(a, [])
        return (q in a.lower()) or any(q in str(t).lower() for t in tips)
    abx_choices = [a for a in abx_pool if _hit(a)]
    selected_abx = st.multiselect("항생제 계열 선택", abx_choices, default=[])
    for abx in selected_abx:
        extras["abx"][abx] = num_input_generic(f"{abx} - 복용/주입량", key=f"abx_{abx}", decimals=1, placeholder="예: 1")

st.divider()
run = st.button("🔎 해석하기", use_container_width=True)
if run:
    st.success("입력값을 분석했습니다. (보고서/해석 섹션은 아래에서 이어집니다)")

    # 항암제 입력
    
def _get_drug_list():
    # Return recommended drug list presets based on current group & cancer selection
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
        "폐암(Lung cancer)": ["Cisplatin","Carboplatin","Paclitaxel","Docetaxel","Gemcitabine","Pemetrexed","Gefitinib","Erlotinib","Osimertinib","Alectinib","Bevacizumab","Pembrolizumab","Nivolumab"],
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
    default_drugs_by_group = {
        "혈액암": heme_by_cancer.get(key, []),
        "고형암": solid_by_cancer.get(cancer, []),
        "육종": sarcoma_by_dx.get(cancer, []),
        "희귀암": rare_by_cancer.get(cancer, []),
        "림프종": lymphoma_by_dx.get(lymphoma_key_map.get(cancer, cancer), []),
    }
    return list(dict.fromkeys(default_drugs_by_group.get(group, [])))

    if mode == "일반/암":
        st.markdown("### 💊 항암제 선택 및 입력")
        try:
            base_list = _get_drug_list() or []
        except Exception:
            base_list = []
        drug_search = st.text_input("🔍 항암제 검색", key="drug_search")
        # 전체 목록: 프리셋 + 모든 항암제 키
        try:
            all_drugs = sorted(set(list(base_list) + list(ANTICANCER.keys())))
        except Exception:
            all_drugs = base_list
        drug_choices = [d for d in all_drugs if not drug_search or drug_search.lower() in d.lower() or drug_search.lower() in ANTICANCER.get(d,{}).get("alias","").lower()]
        drug_key = f"selected_drugs_{group}"
        _def = st.session_state.get(drug_key, [])
        if isinstance(_def, str):
            _def = [_def]
        _def = [x for x in _def if x in drug_choices]
        selected_drugs = st.multiselect("항암제 선택", drug_choices, default=_def, key=drug_key)
        meds = {}
        for d in selected_drugs:
            amt = num_input_generic(f"{d} - 용량/회수", key=f"med_{d}", decimals=1, placeholder="예: 1")
            if entered(amt):
                meds[d] = {"dose_or_tabs": amt}
        extras["anticancer"] = meds
    
        st.markdown("### 🧪 항생제 선택 및 입력")
        extras["abx"] = {}
        abx_search = st.text_input("🔍 항생제 검색", key="abx_search")
        try:
            abx_pool = list(ABX_GUIDE.keys())
        except Exception:
            abx_pool = [k for k in globals().get("ABX", {}).keys()]
        def _hit(a):
            q = (abx_search or "").lower().strip()
            if not q:
                return True
            tips = ABX_GUIDE.get(a, [])
            return (q in a.lower()) or any(q in str(t).lower() for t in tips)
        abx_choices = [a for a in abx_pool if _hit(a)]
        selected_abx = st.multiselect("항생제 계열 선택", abx_choices, default=[])
        for abx in selected_abx:
            extras["abx"][abx] = num_input_generic(f"{abx} - 복용/주입량", key=f"abx_{abx}", decimals=1, placeholder="예: 1")
    
    st.divider()
    run = st.button("🔎 해석하기", use_container_width=True)

    if run:
        st.subheader(f"📋 해석 결과 — {nickname}#{pin if pin else '----'}")

        if mode == "일반/암":
            lines = interpret_labs(vals, extras)
            for line in lines:
                st.write(line)

            # 요검사 해석
            urine_lines = _interpret_urine(extra_vals)
            if urine_lines:
                st.markdown("### 🧪 요검사 해석")
                for ul in urine_lines:
                    st.write(ul)

            if nickname_key and "records" in st.session_state and st.session_state.records.get(nickname_key):
                st.markdown("### 🔍 수치 변화 비교 (이전 기록 대비)")
                cmp_lines = compare_with_previous(nickname_key, {k: vals.get(k) for k in ORDER if entered(vals.get(k))})
                if cmp_lines:
                    for l in cmp_lines:
                        st.write(l)
                else:
                    st.info("비교할 이전 기록이 없거나 값이 부족합니다.")

            shown = [(k, v) for k, v in (extra_vals or {}).items() if entered(v) or isinstance(v, dict)]
            if shown:
                st.markdown("### 🧬 특수/확장/암별 디테일 수치")
                for k, v in shown:
                    st.write(f"- {k}: {v}")

            fs = food_suggestions(vals, anc_place)
            if fs:
                st.markdown("### 🥗 음식 가이드 (계절/레시피 포함)")
                for f in fs:
                    st.markdown(f)
        elif mode == "소아(일상/호흡기)":
            st.info("위 위험도 배너를 참고하세요.")
        else:
            st.success("선택한 감염질환 요약을 보고서에 포함했습니다.")

        if meds:
            st.markdown("### 💊 항암제 부작용·상호작용 요약")
            for line in summarize_meds(meds):
                st.write(line)

        if extras.get("abx"):
            abx_lines = abx_summary(extras["abx"])
            if abx_lines:
                st.markdown("### 🧪 항생제 주의 요약")
                for l in abx_lines:
                    st.write(l)

        st.markdown("### 🌡️ 발열 가이드")
        st.write(FEVER_GUIDE)

        meta = {"group": group, "cancer": cancer, "infect_sel": infect_sel, "anc_place": anc_place, "ped_topic": ped_topic}
        if mode == "소아(일상/호흡기)":
            def _ent(x):
                try:
                    return x is not None and float(x) != 0
                except Exception:
                    return False
            meta["ped_inputs"] = {}
            for k, lab in [("나이(개월)", "ped_age"), ("체온(℃)", "ped_temp"), ("호흡수(/분)", "ped_rr"), ("SpO₂(%)", "ped_spo2"), ("24시간 소변 횟수", "ped_u"),
                           ("흉곽 함몰", "ped_ret"), ("콧벌렁임", "ped_nf"), ("무호흡", "ped_ap")]:
                v = st.session_state.get(lab)
                if _ent(v):
                    meta["ped_inputs"][k] = v
        elif mode == "소아(감염질환)":
            info = PED_INFECT.get(infect_sel, {})
            meta["infect_info"] = {"핵심": info.get("핵심",""), "진단": info.get("진단",""), "특징": info.get("특징","")}
            meta["infect_symptoms"] = st.session_state.get("infect_symptoms", [])
            core = st.session_state.get("ped_infect_core", {})
            if core:
                meta["infect_core"] = core

        meds_lines = summarize_meds(meds) if meds else []
        abx_lines = abx_summary(extras.get("abx", {})) if extras.get("abx") else []
        cmp_lines = compare_with_previous(nickname_key, {k: vals.get(k) for k in ORDER if entered(vals.get(k))}) if (mode=="일반/암") else []
        food_lines = food_suggestions(vals, anc_place) if (mode=="일반/암") else []

        a4_opt = st.checkbox("🖨️ A4 프린트 최적화(섹션 구분선 추가)", value=True)
        urine_lines_for_report = _interpret_urine(extra_vals)
        report_md = build_report(mode, meta, {k: v for k, v in vals.items() if entered(v)}, cmp_lines, extra_vals, meds_lines, food_lines, abx_lines)
        # 요검사 해석을 보고서에도 추가
        if urine_lines_for_report:
            report_md += "\n\n---\n\n### 🧪 요검사 해석\n" + "\n".join(["- " + l for l in urine_lines_for_report])
        # 발열 가이드 + 면책 문구를 하단에 항상 추가
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
                "mode": mode,
                "group": group,
                "cancer": cancer,
                "infect": infect_sel,
                "labs": {k: vals.get(k) for k in ORDER if entered(vals.get(k))},
                "extra": {k: v for k, v in (locals().get('extra_vals') or {}).items() if entered(v) or isinstance(v, dict)},
                "meds": meds,
                "extras": extras,
            }
            st.session_state.records.setdefault(nickname_key, []).append(rec)
            st.success("저장되었습니다. 아래 그래프에서 추이를 확인하세요.")
        else:
            st.info("별명과 PIN을 입력하면 추이 그래프를 사용할 수 있어요.")

    render_graphs()

    st.caption(FOOTER_CAFE)
    st.markdown("> " + DISCLAIMER)
    try:
        st.caption(f"🧩 패키지: {PKG} · 모듈 로딩 정상")
    except Exception:
        pass

if __name__ == "__main__":
    main()