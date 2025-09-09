
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



def _badge(txt, level="info"):
    colors = {"ok":"#16a34a","mild":"#f59e0b","mod":"#fb923c","high":"#dc2626","info":"#2563eb","dim":"#6b7280"}
    col = colors.get(level, "#2563eb")
    return f'<span style="display:inline-block;padding:2px 8px;border-radius:9999px;background:rgba(0,0,0,0.04);color:{col};border:1px solid {col};font-size:12px;margin-right:6px;">{txt}</span>'

def _strip_html(s: str) -> str:
    import re
    return re.sub(r'<[^>]+>', '', s or '')


def _interpret_specials(extras: dict, base_vals: dict = None, profile: str = 'adult'):
    out = []
    def _num(x):
        try: return float(x)
        except Exception: return None
    def _rng(x, bounds):
        v = _num(x)
        if v is None: return None, None
        for up, lvl, lab in bounds:
            if v <= up: return lvl, lab
        return bounds[-1][1], bounds[-1][2]

    # Complements
    c3, c4, ch50 = extras.get("C3"), extras.get("C4"), extras.get("CH50")
    if c3 is not None:
        lvl, lab = _rng(c3, [(89.9,"mild","낮음(소모/결핍 가능)"),(180,"ok","정상"),(9999,"mild","상승")])
        out.append(_badge("C3", lvl or "dim")+f"C3: {c3} mg/dL — {lab}")
    if c4 is not None:
        lvl, lab = _rng(c4, [(9.9,"mild","낮음(자가면역/고전경로 가능)"),(40,"ok","정상"),(9999,"mild","상승")])
        out.append(_badge("C4", lvl or "dim")+f"C4: {c4} mg/dL — {lab}")
    if ch50 is not None:
        lvl, lab = _rng(ch50, [(40,"mild","낮음(결핍/소모)"),(90,"ok","정상"),(9999,"mild","상승")])
        out.append(_badge("CH50", lvl or "dim")+f"CH50: {ch50} U/mL — {lab}")

    # Coag
    pt, inr, aptt = extras.get("PT"), extras.get("INR") or extras.get("PT(INR)") or extras.get("PT-INR"), extras.get("aPTT")
    fbg = extras.get("Fibrinogen")
    dd  = extras.get("D-dimer")
    if pt is not None:
        lvl, lab = _rng(pt, [(13.5,"ok","정상"),(15,"mild","약간 지연"),(20,"mod","지연"),(9999,"high","현저히 지연")])
        out.append(_badge("PT", lvl or "dim")+f"PT: {pt} sec — {lab}")
    if inr is not None:
        lvl, lab = _rng(inr, [(1.1,"ok","정상"),(1.5,"mild","연장"),(2.5,"mod","의미있는 연장"),(9999,"high","고위험")])
        out.append(_badge("INR", lvl or "dim")+f"INR: {inr} — {lab}")
    if aptt is not None:
        lvl, lab = _rng(aptt, [(35,"ok","정상"),(45,"mild","연장"),(60,"mod","의미있는 연장"),(9999,"high","현저히 연장")])
        out.append(_badge("aPTT", lvl or "dim")+f"aPTT: {aptt} sec — {lab}")
    if fbg is not None:
        lvl, lab = _rng(fbg, [(150,"mild","낮음(DIC/간질환)"),(400,"ok","정상(150–400)"),(9999,"mild","상승")])
        out.append(_badge("Fbg", lvl or "dim")+f"Fibrinogen: {fbg} mg/dL — {lab}")
    if dd is not None:
        lvl, lab = _rng(dd, [(0.49,"ok","정상"),(2.0,"mild","상승"),(5.0,"mod","높음"),(9999,"high","매우 높음")])
        out.append(_badge("D-dimer", lvl or "dim")+f"D-dimer: {dd} µg/mL FEU — {lab}")

    # Lipids
    ped = (str(profile).lower().startswith('p'))
    tg  = extras.get("TG") or extras.get("Triglyceride (TG, mg/dL)")
    tc  = extras.get("TC") or extras.get("Total Cholesterol (TC, mg/dL)")
    hdl = extras.get("HDL") or extras.get("HDL-C (HDL, mg/dL)")
    ldl = extras.get("LDL(Friedewald)") or extras.get("LDL")
    non_hdl = extras.get("Non-HDL-C")
    if tg is not None:
        lvl, lab = _rng(tg, ([(149,"ok","정상"),(199,"mild","경계"),(499,"mod","높음"),(9999,"high","매우 높음")] if not ped else [(89,"ok","정상(<90)"),(129,"mild","경계(90–129)"),(499,"mod","높음(≥130)"),(9999,"high","매우 높음(≥500)")] ))
        out.append(_badge("TG", lvl or "dim")+f"TG: {tg} mg/dL — {lab}")
    if tc is not None:
        lvl, lab = _rng(tc, ([(199,"ok","정상"),(239,"mild","경계"),(9999,"mod","높음")] if not ped else [(169,"ok","정상(<170)"),(199,"mild","경계(170–199)"),(9999,"mod","높음(≥200)")] ))
        out.append(_badge("TC", lvl or "dim")+f"TC: {tc} mg/dL — {lab}")
    if hdl is not None:
        h = _num(hdl)
        if h is not None:
            if not ped:
                if h < 40: out.append(_badge("HDL","high")+f"HDL-C: {h} — 낮음(<40)")
                elif h < 60: out.append(_badge("HDL","mild")+f"HDL-C: {h} — 보통(40–59)")
                else: out.append(_badge("HDL","ok")+f"HDL-C: {h} — 높음(≥60)")
            else:
                if h < 40: out.append(_badge("HDL","high")+f"HDL-C: {h} — 낮음(<40)")
                elif h < 45: out.append(_badge("HDL","mild")+f"HDL-C: {h} — 보통(40–44)")
                else: out.append(_badge("HDL","ok")+f"HDL-C: {h} — 높음(≥45)")
    if ldl is not None:
        lvl, lab = _rng(ldl, ([(99,"ok","최적"),(129,"mild","양호"),(159,"mild","경계"),(189,"mod","높음"),(9999,"high","매우 높음")] if not ped else [(109,"ok","정상(<110)"),(129,"mild","경계(110–129)"),(159,"mod","높음(≥130)"),(9999,"high","매우 높음(≥160)")] ))
        out.append(_badge("LDL", lvl or "dim")+f"LDL-C: {ldl} mg/dL — {lab}")
    if non_hdl is not None:
        lvl, lab = _rng(non_hdl, ([(129,"ok","표준 위험"),(159,"mild","경계"),(189,"mod","높음"),(9999,"high","매우 높음")] if not ped else [(119,"ok","정상(<120)"),(144,"mild","경계(120–144)"),(189,"mod","높음(≥145)"),(9999,"high","매우 높음(≥190)")] ))
        out.append(_badge("Non-HDL", lvl or "dim")+f"Non-HDL-C: {non_hdl} mg/dL — {lab}")

    # Kidney
    e = extras.get("eGFR") or ((base_vals or {}).get("eGFR") if isinstance(base_vals, dict) else None)
    if e is not None:
        g = _num(e)
        if g is not None:
            if g >= 90:   out.append(_badge("eGFR","ok")+f"eGFR: {g} — G1")
            elif g >= 60: out.append(_badge("eGFR","ok")+f"eGFR: {g} — G2")
            elif g >= 45: out.append(_badge("eGFR","mild")+f"eGFR: {g} — G3a")
            elif g >= 30: out.append(_badge("eGFR","mod")+f"eGFR: {g} — G3b")
            elif g >= 15: out.append(_badge("eGFR","high")+f"eGFR: {g} — G4")
            else:         out.append(_badge("eGFR","high")+f"eGFR: {g} — G5")

    # Electrolytes (extended)
    mg, phos, ica, ca_corr = extras.get("Mg"), extras.get("Phos(인)"), extras.get("iCa(이온화칼슘)"), extras.get("Corrected Ca")
    if mg is not None:
        lvl, lab = _rng(mg, [(1.6,"mild","낮음"),(2.3,"ok","정상"),(9999,"mild","상승")])
        out.append(_badge("Mg", lvl or "dim")+f"Mg: {mg} mg/dL — {lab}")
    if phos is not None:
        lvl, lab = _rng(phos, [(2.4,"mild","낮음"),(4.5,"ok","정상"),(9999,"mild","상승")])
        out.append(_badge("P", lvl or "dim")+f"Phosphate: {phos} mg/dL — {lab}")
    if ica is not None:
        lvl, lab = _rng(ica, [(1.10,"mild","낮음"),(1.32,"ok","정상"),(9999,"mild","상승")])
        out.append(_badge("iCa", lvl or "dim")+f"이온화Ca: {ica} mmol/L — {lab}")
    if ca_corr is not None:
        lvl, lab = _rng(ca_corr, [(8.5,"mild","낮음"),(10.2,"ok","정상"),(9999,"mild","상승")])
        out.append(_badge("Ca(corr)", lvl or "dim")+f"보정 Ca: {ca_corr} mg/dL — {lab}")

    # Inflammation / Sepsis
    crp = extras.get("CRP") or ((base_vals or {}).get("CRP") if isinstance(base_vals, dict) else None)
    pct = extras.get("Procalcitonin"); lac = extras.get("Lactate")
    if crp is not None:
        lvl, lab = _rng(crp, [(3,"ok","정상/저등급"),(10,"mild","상승"),(100,"mod","높음"),(9999,"high","매우 높음")])
        out.append(_badge("CRP", lvl or "dim")+f"CRP: {crp} mg/L — {lab}")
    if pct is not None:
        lvl, lab = _rng(pct, [(0.1,"ok","정상"),(0.25,"mild","경계"),(0.5,"mod","상승"),(2,"mod","높음"),(9999,"high","매우 높음")])
        out.append(_badge("PCT", lvl or "dim")+f"PCT: {pct} ng/mL — {lab}")
    if lac is not None:
        lvl, lab = _rng(lac, [(2.0,"ok","정상"),(4.0,"mod","상승"),(9999,"high","매우 높음")])
        out.append(_badge("Lactate", lvl or "dim")+f"Lactate: {lac} mmol/L — {lab}")

    # Thyroid
    tsh, ft4, tt3 = extras.get("TSH"), extras.get("Free T4"), extras.get("Total T3")
    if tsh is not None:
        lvl, lab = _rng(tsh, [(0.39,"mild","낮음"),(4.0,"ok","정상"),(10,"mild","상승"),(9999,"mod","현저히 상승")])
        out.append(_badge("TSH", lvl or "dim")+f"TSH: {tsh} µIU/mL — {lab}")
    if ft4 is not None:
        lvl, lab = _rng(ft4, [(0.79,"mild","낮음"),(1.8,"ok","정상"),(9999,"mild","상승")])
        out.append(_badge("FT4", lvl or "dim")+f"Free T4: {ft4} ng/dL — {lab}")
    if tt3 is not None:
        lvl, lab = _rng(tt3, [(79,"mild","낮음"),(200,"ok","정상"),(9999,"mild","상승")])
        out.append(_badge("T3", lvl or "dim")+f"Total T3: {tt3} ng/dL — {lab}")
    if _num(tsh) is not None and _num(ft4) is not None:
        T, F = _num(tsh), _num(ft4)
        if T > 4.0 and F < 0.8:
            out.append(_badge("THY","mod")+"패턴: **원발성 갑상선기능저하증**(TSH↑, FT4↓) 의심.")
        if T < 0.4 and F > 1.8:
            out.append(_badge("THY","mod")+"패턴: **갑상선기능항진증**(TSH↓, FT4↑) 의심.")

    # Glucose / Metabolic
    glu, a1c, homa = extras.get("공복혈당( mg/dL )"), extras.get("HbA1c"), extras.get("HOMA-IR")
    if glu is not None:
        lvl, lab = _rng(glu, [(99,"ok","정상"),(125,"mild","공복혈당장애"),(9999,"mod","당뇨 의심")])
        out.append(_badge("Glu", lvl or "dim")+f"공복혈당: {glu} mg/dL — {lab}")
    if a1c is not None:
        lvl, lab = _rng(a1c, [(5.6,"ok","정상"),(6.4,"mild","당뇨 전단계"),(9999,"mod","당뇨 의심")])
        out.append(_badge("A1c", lvl or "dim")+f"HbA1c: {a1c}% — {lab}")
    if homa is not None:
        lvl, lab = _rng(homa, [(2.5,"ok","정상"),(4.0,"mild","저항성 의심"),(9999,"mod","인슐린 저항성")])
        out.append(_badge("HOMA-IR", lvl or "dim")+f"HOMA-IR: {homa} — {lab}")

    # Anemia
    fe, ferr, tibc = extras.get("Fe(철)"), extras.get("Ferritin"), extras.get("TIBC")
    tsat = extras.get("Transferrin sat.(%)") or extras.get("TSAT")
    retic, b12, fol = extras.get("Reticulocyte(%)"), extras.get("Vitamin B12"), extras.get("Folate")
    if fe is not None:
        lvl, lab = _rng(fe, [(59,"mild","낮음(철결핍)"),(180,"ok","정상"),(9999,"mild","상승")])
        out.append(_badge("Fe", lvl or "dim")+f"Fe: {fe} µg/dL — {lab}")
    if ferr is not None:
        lvl, lab = _rng(ferr, [(14,"mild","낮음"),(30,"mild","경계"),(400,"ok","정상"),(9999,"mild","상승(염증/저장)")])
        out.append(_badge("Ferritin", lvl or "dim")+f"Ferritin: {ferr} ng/mL — {lab}")
    if tibc is not None:
        lvl, lab = _rng(tibc, [(250,"mild","낮음"),(360,"ok","정상"),(9999,"mild","상승(철결핍 시 ↑)")])
        out.append(_badge("TIBC", lvl or "dim")+f"TIBC: {tibc} µg/dL — {lab}")
    if tsat is not None:
        lvl, lab = _rng(tsat, [(19.9,"mild","낮음(<20%)"),(50,"ok","정상(20–50%)"),(9999,"mild","상승")])
        out.append(_badge("TSAT", lvl or "dim")+f"TSAT: {tsat}% — {lab}")
    if retic is not None:
        lvl, lab = _rng(retic, [(0.5,"mild","낮음"),(2.0,"ok","정상"),(9999,"mild","상승")])
        out.append(_badge("Retic", lvl or "dim")+f"Reticulocyte: {retic}% — {lab}")
    if b12 is not None:
        lvl, lab = _rng(b12, [(199,"mild","낮음"),(900,"ok","정상"),(9999,"mild","상승")])
        out.append(_badge("B12", lvl or "dim")+f"Vitamin B12: {b12} pg/mL — {lab}")
    if fol is not None:
        lvl, lab = _rng(fol, [(3.9,"mild","낮음(<4)"),(20,"ok","정상"),(9999,"mild","상승")])
        out.append(_badge("Folate", lvl or "dim")+f"Folate: {fol} ng/mL — {lab}")

    return [x for x in out if x]


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

            # 진단 변경 시 현재 그룹 키의 선택 초기화
            try:
                dx_key = f"{group}:{cancer}"
                if st.session_state.get("dx_key") != dx_key:
                    st.session_state["dx_key"] = dx_key
                    drug_key = f"selected_drugs_{group}"
                    st.session_state[drug_key] = []
            except Exception:
                pass
        elif group == "고형암":
            cancer = st.selectbox("고형암(진단명)", [

                "폐암(Lung cancer)","유방암(Breast cancer)","위암(Gastric cancer)",
                "대장암(Cololoractal cancer)","간암(HCC)","췌장암(Pancreatic cancer)",
                "담도암(Cholangiocarcinoma)","자궁내막암(Endometrial cancer)",
                "구강암/후두암","피부암(흑색종)","신장암(RCC)",
                "갑상선암","난소암","자궁경부암","전립선암","뇌종양(Glioma)","식도암","방광암"
            ])
            # 진단 변경 시 현재 그룹 키의 선택 초기화
            try:
                dx_key = f"{group}:{cancer}"
                if st.session_state.get("dx_key") != dx_key:
                    st.session_state["dx_key"] = dx_key
                    drug_key = f"selected_drugs_{group}"
                    st.session_state[drug_key] = []
            except Exception:
                pass

        elif group == "육종":
            cancer = st.selectbox("육종(진단명)", [

                "연부조직육종(Soft tissue sarcoma)","골육종(Osteosarcoma)","유잉육종(Ewing sarcoma)",
                "평활근육종(Leiomyosarcoma)","지방육종(Liposarcoma)","악성 섬유성 조직구종(UPS/MFH)"
            ])
            # 진단 변경 시 현재 그룹 키의 선택 초기화
            try:
                dx_key = f"{group}:{cancer}"
                if st.session_state.get("dx_key") != dx_key:
                    st.session_state["dx_key"] = dx_key
                    drug_key = f"selected_drugs_{group}"
                    st.session_state[drug_key] = []
            except Exception:
                pass

        elif group == "희귀암":
            cancer = st.selectbox("희귀암(진단명)", [

                "담낭암(Gallbladder cancer)","부신암(Adrenal cancer)","망막모세포종(Retinoblastoma)",
                "흉선종/흉선암(Thymoma/Thymic carcinoma)","신경내분비종양(NET)",
                "간모세포종(Hepatoblastoma)","비인두암(NPC)","GIST"
            ])
            # 진단 변경 시 현재 그룹 키의 선택 초기화
            try:
                dx_key = f"{group}:{cancer}"
                if st.session_state.get("dx_key") != dx_key:
                    st.session_state["dx_key"] = dx_key
                    drug_key = f"selected_drugs_{group}"
                    st.session_state[drug_key] = []
            except Exception:
                pass

        
        elif group == "림프종":
            st.subheader("림프종 진단 / 약물 선택")
            lymph_display = [
                "미만성 거대 B세포 림프종(DLBCL)",
                "원발 종격동 B세포 림프종(PMBCL)",
                "여포성 림프종 1-2등급(FL 1-2)",
                "여포성 림프종 3A(FL 3A)",
                "여포성 림프종 3B(FL 3B)",
                "외투세포 림프종(MCL)",
                "변연대 림프종(MZL)",
                "고등급 B세포 림프종(HGBL)",
                "버킷 림프종(Burkitt)",
            ]
            cancer = st.selectbox("림프종(진단명)", lymph_display)

            # 내부 저장: 코드 슬러그 + 한글 라벨
            st.session_state["dx_label"] = cancer
            st.session_state["dx_slug"] = lymphoma_key_map.get(cancer, cancer)

            # 진단 변경 시 현재 그룹 키의 선택 초기화
            try:
                dx_key = f"{group}:{cancer}"
                if st.session_state.get("dx_key") != dx_key:
                    st.session_state["dx_key"] = dx_key
                    drug_key = f"selected_drugs_{group}"
                    st.session_state[drug_key] = []
            except Exception:
                pass

            base_choices = [
                "R-CHOP","Pola-R-CHP","DA-EPOCH-R",
                "R-ICE","R-DHAP","R-GDP","R-GemOx","R-ESHAP",
                "Pola-BR","Tafasitamab + Lenalidomide","Loncastuximab",
                "Glofitamab","Epcoritamab","Selinexor",
            ]
            pmbcl_only = ["Pembrolizumab (PMBCL; 해외 활발 사용, 국내 미승인)"]

            if "PMBCL" in cancer:
                drug_choices = ["DA-EPOCH-R"] + base_choices + pmbcl_only
            elif "DLBCL" in cancer or "HGBL" in cancer or "3B" in cancer:
                drug_choices = ["R-CHOP","Pola-R-CHP","DA-EPOCH-R"] + base_choices
            elif "3A" in cancer:
                drug_choices = ["R-CHOP","Pola-R-CHP"] + [x for x in base_choices if x not in ["DA-EPOCH-R"]]
            elif "FL 1-2" in cancer or "1-2" in cancer:
                drug_choices = ["BR","R-CVP"] + base_choices
            elif "MCL" in cancer:
                drug_choices = ["BR","R-CHOP"] + base_choices + ["Ibrutinib (R/R)", "Acalabrutinib (R/R)", "Zanubrutinib (R/R)"]
            elif "MZL" in cancer:
                drug_choices = ["BR","R-CVP"] + base_choices
            elif "Burkitt" in cancer:
                drug_choices = ["CODOX-M/IVAC-R","Hyper-CVAD-R"] + base_choices
            else:
                drug_choices = base_choices

            # 그룹별 동적 키로 충돌 방지
            drug_key = f"selected_drugs_{group}"
            _def = st.session_state.get(drug_key, [])
            if isinstance(_def, str):
                _def = [_def]
            _def = [x for x in _def if x in drug_choices]
            selected_drugs = st.multiselect("항암제 선택", drug_choices, default=_def, key=drug_key)
            st.caption("세포/자가세포치료는 제외됩니다. 국내 미승인이더라도 해외에서 활발히 쓰이는 일부는 참고용으로 회색 표시될 수 있습니다.")

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

    # 항암제 입력
    
def _get_drug_list():
    try:
        return sorted(list(ANTICANCER.keys()))
    except Exception:
        return []

