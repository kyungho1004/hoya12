
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


def _parse_conc_to_mg_per_ml(conc_label: str) -> float | None:
    '''
    Parse labels like '160 mg/5 ml' into mg per ml (e.g., 32.0).
    '''
    try:
        # Normalize case/spaces
        c = conc_label.replace("mL","ml").replace("ML","ml")
        mg_part, ml_part = c.split("mg/")
        mg = float(mg_part.strip().split()[-1])
        ml = float(ml_part.strip().split()[0])
        if ml == 0:
            return None
        return mg / ml
    except Exception:
        return None

def _round_ml(x: float, step: float = 0.5) -> float:
    try:
        return round(round(x / step) * step, 2)  # keep one/two decimals
    except Exception:
        return None

def dose_ml_acetaminophen_central(weight_kg, conc_label: str, mg_per_kg: float = 12.5, step: float = 0.5):
    try:
        w = float(weight_kg)
        mg_per_ml = _parse_conc_to_mg_per_ml(conc_label)
        if mg_per_ml is None or w <= 0:
            return None
        ml = (w * mg_per_kg) / mg_per_ml
        return _round_ml(ml, step)
    except Exception:
        return None

def dose_ml_ibuprofen_central(weight_kg, conc_label: str, mg_per_kg: float = 7.5, step: float = 0.5):
    try:
        w = float(weight_kg)
        mg_per_ml = _parse_conc_to_mg_per_ml(conc_label)
        if mg_per_ml is None or w <= 0:
            return None
        ml = (w * mg_per_kg) / mg_per_ml
        return _round_ml(ml, step)
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
conc2 = st.selectbox("시럽 농도", ["160 mg/5 ml", "120 mg/5 ml"], key="antipy_conc_acet_gi")
ml_one = dose_ml_acetaminophen_central(wt2, conc2)
if ml_one is not None:
    st.info(f"권장 1회 용량: **{ml_one:.1f} ml**")
    st.caption(f"{conc2} 기준 · 4–6시간 간격 · 하루 최대 5회")
else:
mg_low, mg_high = dose_ibuprofen(wt2)
conc2 = st.selectbox("시럽 농도", ["100 mg/5 ml"], key="antipy_conc_ibu_gi")
ml_one = dose_ml_ibuprofen_central(wt2, conc2)
if ml_one is not None:
    st.info(f"권장 1회 용량: **{ml_one:.1f} ml**")
    st.caption("간격: 6–8시간 · 생후 6개월 미만은 의료진과 상담 필요")
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

    # 항암제 입력
    def _get_drug_list():
        if not (mode == "일반/암" and group and group != "미선택/일반" and cancer):
            return []
        heme_by_cancer = {
            "AML": ["ARA-C","Daunorubicin","Idarubicin","Cyclophosphamide",
                    "Etoposide","Fludarabine","Hydroxyurea","MTX","ATRA","G-CSF"],
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
        key = heme_key_map.get(cancer, cancer)
        default_drugs_by_group = {
            "혈액암": heme_by_cancer.get(key, []),
            "고형암": solid_by_cancer.get(cancer, []),
            "육종": sarcoma_by_dx.get(cancer, []),
            "희귀암": rare_by_cancer.get(cancer, []),
        }
        return list(dict.fromkeys(default_drugs_by_group.get(group, [])))

    drug_list = _get_drug_list()

    if mode == "일반/암":
        st.markdown("### 💊 항암제 선택 및 입력")
        # Regimen presets
        preset = st.selectbox("레짐 프리셋", ["없음","APL(ATRA+ATO)","유방 AC-T","대장 FOLFOX","대장 FOLFIRI","림프종 CHOP"], index=0, help="선택 후 '프리셋 적용'을 누르면 아래 항암제 선택에 반영됩니다.")
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
        drug_search = st.text_input("🔍 항암제 검색", key="drug_search")
        drug_choices = [d for d in drug_list if not drug_search or drug_search.lower() in d.lower() or drug_search.lower() in ANTICANCER.get(d,{}).get("alias","").lower()]
        selected_drugs = st.multiselect("항암제 선택", drug_choices, default=st.session_state.get("selected_drugs", []), key="selected_drugs")

        for d in selected_drugs:
            alias = ANTICANCER.get(d,{}).get("alias","")
            if d == "ATRA":
                amt = num_input_generic(f"{d} ({alias}) - 캡슐 개수", key=f"med_{d}", as_int=True, placeholder="예: 2")
            elif d == "ARA-C":
                ara_form = st.selectbox(f"{d} ({alias}) - 제형", ["정맥(IV)","피하(SC)","고용량(HDAC)"], key=f"ara_form_{d}")
                amt = num_input_generic(f"{d} ({alias}) - 용량/일", key=f"med_{d}", decimals=1, placeholder="예: 100")
                if amt and float(amt)>0:
                    meds[d] = {"form": ara_form, "dose": amt}
                continue
            else:
                amt = num_input_generic(f"{d} ({alias}) - 용량/알약", key=f"med_{d}", decimals=1, placeholder="예: 1.5")
            if amt and float(amt)>0:
                meds[d] = {"dose_or_tabs": amt}

    st.markdown("### 🧪 항생제 선택 및 입력")
    extras["abx"] = {}
    abx_search = st.text_input("🔍 항생제 검색", key="abx_search")
    abx_choices = [a for a in ABX_GUIDE.keys() if not abx_search or abx_search.lower() in a.lower() or any(abx_search.lower() in tip.lower() for tip in ABX_GUIDE[a])]
    selected_abx = st.multiselect("항생제 계열 선택", abx_choices, default=[])
    for abx in selected_abx:
        extras["abx"][abx] = num_input_generic(f"{abx} - 복용/주입량", key=f"abx_{abx}", decimals=1, placeholder="예: 1")

    st.markdown("### 💧 동반 약물/상태")
    extras["diuretic_amt"] = num_input_generic("이뇨제(복용량/회/일)", key="diuretic_amt", decimals=1, placeholder="예: 1")

    st.divider()
    if mode == "일반/암":
        st.header("2️⃣ 기본 혈액 검사 수치 (입력한 값만 해석)")
    elif mode == "소아(일상/호흡기)":
        st.header("2️⃣ 소아 공통 입력")
    else:
        st.header("2️⃣ (감염질환은 별도 수치 입력 없음)")

    vals = {}

    def render_inputs_vertical():
        st.markdown("**기본 패널**")
        for name in ORDER:
            if name == LBL_CRP:
                vals[name] = num_input_generic(f"{name}", key=f"v_{name}", decimals=2, placeholder="예: 0.12")
            elif name in (LBL_WBC, LBL_ANC, LBL_AST, LBL_ALT, LBL_LDH, LBL_BNP, LBL_Glu):
                vals[name] = num_input_generic(f"{name}", key=f"v_{name}", decimals=1, placeholder="예: 1200")
            else:
                vals[name] = num_input_generic(f"{name}", key=f"v_{name}", decimals=1, placeholder="예: 3.5")

    def render_inputs_table():
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
        if table_mode:
            render_inputs_table()
        else:
            render_inputs_vertical()
        # 이전 기록 불러오기
        if nickname_key and st.session_state.records.get(nickname_key):
            if st.button("↩️ 이전 기록 불러오기", help="같은 별명#PIN의 가장 최근 수치를 현재 폼에 채웁니다."):
                last = st.session_state.records[nickname_key][-1]
                labs = last.get("labs", {})
                # 채울 수 있는 현재 입력 key를 찾아 값 넣기
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
        if not spo2_unknown:
            spo2 = _parse_num_ped("산소포화도(%)", key="ped_spo2", decimals=0, placeholder="예: 96")
        else:
            spo2 = None
        urine_24h    = _parse_num_ped("24시간 소변 횟수", key="ped_u", decimals=0, placeholder="예: 6")
        retraction   = _parse_num_ped("흉곽 함몰(0/1)", key="ped_ret", decimals=0, placeholder="0 또는 1")
        nasal_flaring= _parse_num_ped("콧벌렁임(0/1)", key="ped_nf", decimals=0, placeholder="0 또는 1")
        apnea        = _parse_num_ped("무호흡(0/1)", key="ped_ap", decimals=0, placeholder="0 또는 1")

        # 👶 간단 증상 입력(보호자 친화)
        with st.expander("👶 증상(간단 선택)", expanded=True):
            runny = st.selectbox("콧물", ["없음","흰색","노란색","피섞임"], key="ped_runny")
            cough_sev = st.selectbox("기침", ["없음","조금","보통","심함"], key="ped_cough_sev")
            st.session_state["ped_simple_sym"] = {"콧물": runny, "기침": cough_sev}

        with st.expander("👀 보호자 관찰 체크리스트", expanded=False):
            obs = {}
            obs["숨 가빠보임(호흡곤란)"] = st.checkbox("숨 가빠보임(호흡곤란)", key="obs1")
            obs["청색증 의심(입술/손발)"] = st.checkbox("청색증 의심(입술/손발)", key="obs2")
            obs["말수 감소·축 늘어짐"]   = st.checkbox("말수 감소·축 늘어짐/보챔", key="obs3")
            obs["탈수 의심(마른입/눈물↓/소변↓)"] = st.checkbox("탈수 의심(마른 입술/눈물 적음/소변 감소)", key="obs4")
            obs["고열(≥40.0℃)"] = st.checkbox("고열(≥40.0℃)", key="obs5")
            obs["3개월 미만 발열(≥38.0℃)"] = st.checkbox("3개월 미만 발열(≥38.0℃)", key="obs6")
            obs["경련(열성경련 포함)"] = st.checkbox("경련(열성경련 포함)", key="obs7")
            st.session_state["ped_obs"] = {k:v for k,v in obs.items() if v}

        with st.expander("🧮 해열제 용량 계산기", expanded=False):
            wt = st.text_input("체중(kg)", key="antipy_wt", placeholder="예: 10.5")
            med = st.selectbox("해열제", ["아세트아미노펜(acetaminophen)", "이부프로펜(ibuprofen)"], key="antipy_med")
            if med.startswith("아세트"):
mg_low, mg_high = dose_acetaminophen(wt)
conc = st.selectbox("시럽 농도", ["160 mg/5 ml", "120 mg/5 ml"], key="antipy_conc_acet")
ml_one = dose_ml_acetaminophen_central(wt, conc)
if ml_one is not None:
    st.info(f"권장 1회 용량: **{ml_one:.1f} ml**")
    st.caption(f"{conc} 기준 · 4–6시간 간격 · 하루 최대 5회")
else:
mg_low, mg_high = dose_ibuprofen(wt)
conc = st.selectbox("시럽 농도", ["100 mg/5 ml"], key="antipy_conc_ibu")
ml_one = dose_ml_ibuprofen_central(wt, conc)
if ml_one is not None:
    st.info(f"권장 1회 용량: **{ml_one:.1f} ml**")
    st.caption("간격: 6–8시간 · 생후 6개월 미만은 의료진과 상담 필요")
# ===== 특수검사(기본) + TOP8 확장 =====
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
            t_urine_basic = st.checkbox("요검사(단백/잠혈/요당/요Cr)")
        with col[3]:
            t_lipid_basic = st.checkbox("지질 기본(TG/TC)")

        if t_coag:
            st.markdown("**응고패널**")
            extra_vals["PT"] = num_input_generic("PT (sec)", key="ex_pt", decimals=1, placeholder="예: 12.0")
            extra_vals["aPTT"] = num_input_generic("aPTT (sec)", key="ex_aptt", decimals=1, placeholder="예: 32.0")
            extra_vals["Fibrinogen"] = num_input_generic("Fibrinogen (Fbg, mg/dL)", key="ex_fbg", decimals=1, placeholder="예: 250")
            extra_vals["D-dimer"] = num_input_generic("D-dimer (DD, µg/mL FEU)", key="ex_dd", decimals=2, placeholder="예: 0.50")

        if t_comp:
            st.markdown("**보체(C3/C4/CH50)**")
            extra_vals["C3"] = num_input_generic("C3 (mg/dL)", key="ex_c3", decimals=1, placeholder="예: 90")
            extra_vals["C4"] = num_input_generic("C4 (mg/dL)", key="ex_c4", decimals=1, placeholder="예: 20")
            extra_vals["CH50"] = num_input_generic("CH50 (U/mL)", key="ex_ch50", decimals=1, placeholder="예: 50")

        if t_urine_basic:
            st.markdown("**요검사(기본)** — 정성 + 정량(선택)")
            # 정성(스트립) 결과
            cq = st.columns(4)
            with cq[0]:
                hematuria_q = st.selectbox("혈뇨(정성)", ["", "+", "++", "+++"], index=0)
            with cq[1]:
                proteinuria_q = st.selectbox("단백뇨(정성)", ["", "-", "+", "++"], index=0)
            with cq[2]:
                wbc_q = st.selectbox("백혈구(정성)", ["", "-", "+", "++"], index=0)
            with cq[3]:
                gly_q = st.selectbox("요당(정성)", ["", "-", "+++"], index=0)

            # 설명 매핑
            _desc_hema = {"+":"소량 검출","++":"중등도 검출","+++":"고농도 검출"}
            _desc_prot = {"-":"음성","+":"경도 검출","++":"중등도 검출"}
            _desc_wbc  = {"-":"음성","+":"의심 수준","++":"양성"}
            _desc_gly  = {"-":"음성","+++":"고농도 검출"}

            if hematuria_q:
                extra_vals["혈뇨(정성)"] = f"{hematuria_q} ({_desc_hema.get(hematuria_q,'')})"
            if proteinuria_q:
                extra_vals["단백뇨(정성)"] = f"{proteinuria_q} ({_desc_prot.get(proteinuria_q,'')})"
            if wbc_q:
                extra_vals["백혈구뇨(정성)"] = f"{wbc_q} ({_desc_wbc.get(wbc_q,'')})"
            if gly_q:
                extra_vals["요당(정성)"] = f"{gly_q} ({_desc_gly.get(gly_q,'')})"

            # 정량(선택): UPCR/ACR 계산용
            with st.expander("정량(선택) — UPCR/ACR 계산", expanded=False):
                u_prot = num_input_generic("요단백 (mg/dL)", key="ex_upr", decimals=1, placeholder="예: 30")
                u_cr   = num_input_generic("소변 Cr (mg/dL)", key="ex_ucr", decimals=1, placeholder="예: 100")
                u_alb  = num_input_generic("소변 알부민 (mg/L)", key="ex_ualb", decimals=1, placeholder="예: 30")
                upcr = acr = None
                if u_cr and u_prot:
                    upcr = round((u_prot * 1000.0) / float(u_cr), 1)
                    st.info(f"UPCR(요단백/Cr): **{upcr} mg/g** (≈ 1000×[mg/dL]/[mg/dL])")
                if u_cr and u_alb:
                    acr = round((u_alb * 100.0) / float(u_cr), 1)
                    st.info(f"ACR(소변 알부민/Cr): **{acr} mg/g** (≈ 100×[mg/L]/[mg/dL])")
                if acr is not None:
                    extra_vals["ACR(mg/g)"] = acr
                    a, a_label = stage_acr(acr)
                    if a:
                        st.caption(f"Albuminuria A-stage: **{a}** · {a_label}")
                        extra_vals["Albuminuria stage"] = f"{a} ({a_label})"
                if upcr is not None:
                    extra_vals["UPCR(mg/g)"] = upcr
                extra_vals["Urine Cr"] = u_cr
                extra_vals["Urine albumin"] = u_alb
        if t_lipid_basic:
            st.markdown("**지질(기본)**")
            extra_vals["TG"] = num_input_generic("Triglyceride (TG, mg/dL)", key="ex_tg", decimals=0, placeholder="예: 150")
            extra_vals["TC"] = num_input_generic("Total Cholesterol (TC, mg/dL)", key="ex_tc", decimals=0, placeholder="예: 180")

        # --- TOP8 확장 토글 ---
        st.subheader("➕ 확장 패널")

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            t_anemia = st.checkbox("빈혈 패널")
            t_elect  = st.checkbox("전해질 확장")
        with c2:
            t_kidney = st.checkbox("신장/단백뇨")
            t_thy    = st.checkbox("갑상선")
        with c3:
            t_sepsis = st.checkbox("염증/패혈증")
            t_glu    = st.checkbox("당대사/대사증후군")
        with c4:
            t_lipidx = st.checkbox("지질 확장")
            t_biomkr = st.checkbox("암별 분자/표지자")

        if t_anemia:
            st.markdown("**빈혈 패널**")
            extra_vals["Fe(철)"] = num_input_generic("Fe (µg/dL)", key="an_fe", decimals=0, placeholder="예: 60")
            extra_vals["Ferritin"] = num_input_generic("Ferritin (Fer, ng/mL)", key="an_ferr", decimals=1, placeholder="예: 80")
            extra_vals["TIBC"] = num_input_generic("TIBC (Total Iron Binding Capacity, µg/dL)", key="an_tibc", decimals=0, placeholder="예: 330")
            extra_vals["Transferrin sat.(%)"] = num_input_generic("Transferrin Sat. (TSAT, %)", key="an_tsat", decimals=1, placeholder="예: 18.0")
            extra_vals["Reticulocyte(%)"] = num_input_generic("망상적혈구(%) (Retic %)", key="an_retic", decimals=1, placeholder="예: 1.2")
            extra_vals["Vitamin B12"] = num_input_generic("비타민 B12 (Vit B12, pg/mL)", key="an_b12", decimals=0, placeholder="예: 400")
            extra_vals["Folate"] = num_input_generic("엽산(Folate, ng/mL)", key="an_folate", decimals=1, placeholder="예: 6.0")

        if t_elect:
            st.markdown("**전해질 확장**")
            extra_vals["Mg"] = num_input_generic("Mg (mg/dL)", key="el_mg", decimals=2, placeholder="예: 2.0")
            extra_vals["Phos(인)"] = num_input_generic("Phosphate (Phos/P, mg/dL)", key="el_phos", decimals=2, placeholder="예: 3.5")
            extra_vals["iCa(이온화칼슘)"] = num_input_generic("이온화칼슘 iCa (iCa, mmol/L)", key="el_ica", decimals=2, placeholder="예: 1.15")
            ca_corr = calc_corrected_ca(vals.get(LBL_Ca), vals.get(LBL_Alb))
            if ca_corr is not None:
                st.info(f"보정 칼슘(Alb 반영): **{ca_corr} mg/dL**")
                st.caption("공식: Ca + 0.8×(4.0 - Alb), mg/dL 기준")
                extra_vals["Corrected Ca"] = ca_corr

        if t_kidney:
            st.markdown("**신장/단백뇨**")
            age = num_input_generic("나이(추정, eGFR 계산용)", key="kid_age", decimals=0, placeholder="예: 40")
            sex = st.selectbox("성별", ["F","M"], key="kid_sex")
            egfr = calc_egfr(vals.get(LBL_Cr), age=age or 60, sex=sex)
            if egfr is not None:
                st.info(f"eGFR(자동계산): **{egfr} mL/min/1.73m²**")
                extra_vals["eGFR"] = egfr
                g, g_label = stage_egfr(egfr)
                if g:
                    st.caption(f"CKD G-stage: **{g}** · {g_label}")
                    extra_vals["CKD G-stage"] = f"{g} ({g_label})"

            # UACR/UPCR는 위 '요검사(기본)'에 포함

        if t_thy:
            st.markdown("**갑상선 패널**")
            extra_vals["TSH"] = num_input_generic("TSH (Thyroid Stimulating Hormone, µIU/mL)", key="thy_tsh", decimals=2, placeholder="예: 1.50")
            extra_vals["Free T4"] = num_input_generic("Free T4 (FT4, ng/dL)", key="thy_ft4", decimals=2, placeholder="예: 1.2")
            if st.checkbox("Total T3 입력", key="thy_t3_on"):
                extra_vals["Total T3"] = num_input_generic("Total T3 (TT3, ng/dL)", key="thy_t3", decimals=0, placeholder="예: 110")

        if t_sepsis:
            st.markdown("**염증/패혈증 패널**")
            extra_vals["Procalcitonin"] = num_input_generic("Procalcitonin (PCT, ng/mL)", key="sep_pct", decimals=2, placeholder="예: 0.12")
            extra_vals["Lactate"] = num_input_generic("Lactate (Lac, mmol/L)", key="sep_lac", decimals=1, placeholder="예: 1.8")
            # CRP는 기본 유지

        if t_glu:
            st.markdown("**당대사/대사증후군**")
            glu_f = num_input_generic("공복혈당( mg/dL )", key="glu_f", decimals=0, placeholder="예: 95")
            extra_vals["HbA1c"] = num_input_generic("HbA1c( % )", key="glu_a1c", decimals=2, placeholder="예: 5.6")
            if st.checkbox("인슐린 입력(선택, HOMA-IR 계산)", key="glu_ins_on"):
                insulin = num_input_generic("Insulin (µU/mL)", key="glu_ins", decimals=1, placeholder="예: 8.5")
                homa = calc_homa_ir(glu_f, insulin) if glu_f and insulin else None
                if homa is not None:
                    st.info(f"HOMA-IR: **{homa}**")
                    st.caption("HOMA-IR = (공복혈당×인슐린)/405")
                    extra_vals["HOMA-IR"] = homa

        if t_lipidx:
            st.markdown("**지질 확장**")
            tc  = extra_vals.get("TC") or num_input_generic("Total Cholesterol (TC, mg/dL)", key="lx_tc", decimals=0, placeholder="예: 180")
            hdl = num_input_generic("HDL-C (HDL, mg/dL)", key="lx_hdl", decimals=0, placeholder="예: 50")
            tg  = extra_vals.get("TG") or num_input_generic("Triglyceride (mg/dL)", key="lx_tg", decimals=0, placeholder="예: 120")
            ldl_fw = calc_friedewald_ldl(tc, hdl, tg)
            try:
                if tg is not None and float(tg) >= 400:
                    st.warning("TG ≥ 400 mg/dL: Friedewald LDL 계산이 비활성화됩니다.")
            except Exception:
                pass
            non_hdl = calc_non_hdl(tc, hdl) if tc and hdl else None
            if non_hdl is not None:
                st.info(f"Non-HDL-C: **{non_hdl} mg/dL**")
                extra_vals["Non-HDL-C"] = non_hdl
            if ldl_fw is not None:
                st.info(f"Friedewald LDL(자동): **{ldl_fw} mg/dL** (TG<400에서만 계산)")
                extra_vals["LDL(Friedewald)"] = ldl_fw
            extra_vals["ApoB"] = num_input_generic("ApoB (Apolipoprotein B, mg/dL)", key="lx_apob", decimals=0, placeholder="예: 90")

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

    # === 암별 디테일(토글) ===
    if mode == "일반/암" and group and group != "미선택/일반" and cancer:
        st.divider()
        if st.checkbox("4️⃣ 암별 디테일(토글)", value=False, help="자주 나가지 않아 기본은 숨김"):
            st.header("암별 디테일 수치")
            if group == "혈액암":
                key = heme_key_map.get(cancer, cancer)
                if key in ["AML","APL"]:
                    extra_vals["DIC Score"] = num_input_generic("DIC Score (pt)", key="ex_dic", decimals=0, placeholder="예: 3")
            elif group == "육종":
                extra_vals["ALP"] = num_input_generic("ALP(U/L)", key="ex_alp", decimals=0, placeholder="예: 100")
                extra_vals["CK"] = num_input_generic("CK(U/L)", key="ex_ck", decimals=0, placeholder="예: 150")

    # 스케줄/그래프
    render_schedule(nickname_key)

    st.divider()
    run = st.button("🔎 해석하기", use_container_width=True)

    if run:
        st.subheader(f"📋 해석 결과 — {nickname}#{pin if pin else '----'}")

        if mode == "일반/암":
            lines = interpret_labs(vals, extras)
            for line in lines:
                st.write(line)

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
        report_md = build_report(mode, meta, {k: v for k, v in vals.items() if entered(v)}, cmp_lines, extra_vals, meds_lines, food_lines, abx_lines)
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
