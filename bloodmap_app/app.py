
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

# utils modules
_utils_inputs = _load_mod("utils.inputs")
_utils_interpret = _load_mod("utils.interpret")
_utils_reports = _load_mod("utils.reports")
_utils_graphs = _load_mod("utils.graphs")
_utils_schedule = _load_mod("utils.schedule")

_FALLBACK_UTILS = not all([_utils_inputs, _utils_interpret, _utils_reports, _utils_graphs, _utils_schedule])

if not _FALLBACK_UTILS:
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
else:
    # ---- Minimal safe fallbacks so the app can run even without utils/ ----
    import streamlit as st

    def num_input_generic(label, key=None, unit="", min_value=None, max_value=None, step=None, help=None, format=None):
        lbl = label + (f" ({unit})" if unit else "")
        return st.number_input(lbl, key=key, min_value=min_value, max_value=max_value, step=step, help=help)

    def entered(v):
        return (v is not None) and (str(v).strip() != "")

    def _parse_numeric(x):
        try:
            return None if x is None or x=="" else float(x)
        except Exception:
            return None

    def interpret_labs(vals, extras):
        lines = []
        try:
            for k, v in (vals or {}).items():
                if entered(v):
                    lines.append(f"{k}: {v}")
        except Exception:
            pass
        if not lines:
            lines = ["입력된 수치가 없습니다."]
        # 간단한 특수 검사도 표시
        try:
            if extras:
                lines.append("— 특수검사 요약 —")
                for k, v in extras.items():
                    if entered(v):
                        lines.append(f"{k}: {v}")
        except Exception:
            pass
        return lines

    def compare_with_previous(*args, **kwargs):
        return []

    def food_suggestions(*args, **kwargs):
        return []

    def summarize_meds(*args, **kwargs):
        return []

    def abx_summary(*args, **kwargs):
        return []
    def build_report(nickname, pin, mode, lines, urine_lines, extra_sections, disclaimer):
        md = f"""# BloodMap 보고서

- 사용자: {nickname}#{pin or '----'}
- 모드: {mode}

## 해석 결과
"""
        for L in (lines or []):
            md += f"- {L}\n"
        if urine_lines:
            md += "\n## 요검사\n"
            for L in urine_lines:
                md += f"- {L}\n"
        for title, items in (extra_sections or []):
            md += f"\n## {title}\n"
            for L in (items or []):
                md += f"- {L}\n"
        if disclaimer:
            md += f"\n\n{disclaimer}\n"
        return md

    def md_to_pdf_bytes_fontlocked(md_text):
        # PDF 생성기를 사용할 수 없는 환경이므로, 상위 로직의 try/except에 맡긴다.
        raise RuntimeError("PDF generator unavailable in fallback mode.")

    def render_graphs(*args, **kwargs):
        st.info("그래프 기능은 준비 중입니다. (utils가 없어서 최소 모드로 실행 중)")

    def render_schedule(*args, **kwargs):
        # 요청에 따라 스케줄은 비활성화
        pass

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


# === 소아 해석 유틸 ===
def _peds_rr_tachypnea_threshold(age_months):
    """Return RR threshold above which tachypnea is likely for age (WHO-ish)."""
    try:
        m = float(age_months)
    except Exception:
        return None
    if m < 2:   return 60
    if m < 12:  return 50
    if m < 60:  return 40
    return 30  # ≥5y

def _peds_interpret_common(age_m=None, temp_c=None, rr=None, spo2=None, urine_24h=None,
                           retraction=None, nasal_flaring=None, apnea=None, redflags=None):
    lines = []
    risk = "🟢 낮음"
    def _num(x):
        try: return float(x)
        except Exception: return None

    a = _num(age_m); t = _num(temp_c); r = _num(rr); s = _num(spo2); u = _num(urine_24h)
    retr = (str(retraction).strip() == "1")
    nfl  = (str(nasal_flaring).strip() == "1")
    ap   = (str(apnea).strip() == "1")
    reds = set([k for k,v in (redflags or {}).items() if v])

    # 온도
    if t is not None:
        if t >= 39.0:
            lines.append("🌡️ 고열(≥39.0℃): 해열제 용법 준수, 미온수 닦기, 수분 보충 권장.")
        elif t >= 38.0:
            lines.append("🌡️ 발열(38.0–38.9℃): 경과 관찰 + 해열제 고려.")
        else:
            lines.append(f"🌡️ 체온 {t}℃: 발열은 뚜렷하지 않습니다.")

    # 호흡수
    thr = _peds_rr_tachypnea_threshold(a) if a is not None else None
    if r is not None and thr is not None:
        if r > thr:
            lines.append(f"🫁 빠른 호흡(RR {int(r)}>{thr}/분): 상기도/하기도 감염 가능성, 흉곽 함몰/쌕쌕 동반 시 진료 권고.")
        else:
            lines.append(f"🫁 호흡수(RR {int(r)}/분): 연령 기준 내로 보입니다(기준 {thr}/분).")

    # SpO2
    if s is not None:
        if s < 92:
            lines.append(f"🧯 산소포화도 {int(s)}%: 저산소 범위, 즉시 진료/응급실 고려.")
            risk = "🔴 높음"
        elif s < 95:
            lines.append(f"⚠️ 산소포화도 {int(s)}%: 경계 범위, 증상 악화 시 진료 권고.")
            risk = "🟠 중간"
        else:
            lines.append(f"🫧 산소포화도 {int(s)}%: 안정적입니다.")

    # 탈수 추정 (간단)
    if u is not None:
        if u <= 2:
            lines.append("🥤 소변 횟수 ≤2회/일: 탈수 고위험, 수분 보충 + 진료 고려.")
            risk = "🟠 중간" if risk == "🟢 낮음" else risk
        elif u < 6:
            lines.append("🥤 소변 횟수 <6회/일: 가벼운 탈수 가능성, 수분 보충 권장.")
        else:
            lines.append("🥤 소변 횟수 양호(≥6회/일).")

    # 관찰 소견
    if retr or nfl or ap:
        flags = []
        if retr: flags.append("흉곽 함몰")
        if nfl:  flags.append("콧벌렁임")
        if ap:   flags.append("무호흡")
        lines.append("🚨 호흡곤란 징후: " + ", ".join(flags) + " → 진료/응급 권고.")
        risk = "🔴 높음"

    # 체크박스 레드플래그
    if reds:
        lines.append("🚨 레드 플래그: " + ", ".join(sorted(reds)) + " → 즉시 진료/응급실 고려.")
        risk = "🔴 높음"

    # 3개월 미만 발열
    if a is not None and t is not None and a < 3 and t >= 38.0:
        lines.append("👶 3개월 미만 + 발열(≥38.0℃): **반드시 의료진 상담/진료**.")
        risk = "🔴 높음"

    return risk, lines

def _peds_care_advice():
    return [
        "🧼 손위생·기침 예절, 코세척(생리식염수)으로 분비물 관리",
        "🍚 소량씩 자주 수분·식사 제공, 수프/미음/부드러운 식감 권장",
        "🛌 충분한 휴식, 과한 활동은 피하기",
        "🧯 증상 급격 악화·호흡곤란·탈수 소견 시 즉시 진료",
    ]

def _peds_disease_tips(name_lc, core_flags):
    tips = []
    nl = (name_lc or "").lower()
    cf = core_flags or {}
    def on(k): 
        v = cf.get(k)
        return (v is True) or (isinstance(v, str) and v and v != "없음") or (isinstance(v, (int,float)) and v>0)

    if "rsv" in nl:
        flags = []
        if on("쌕쌕거림(천명)"): flags.append("쌕쌕거림")
        if on("흉곽 함몰"): flags.append("흉곽 함몰")
        if flags:
            tips.append("🫁 RSV 의심: " + ", ".join(flags) + " → 흡입 가습·상체 올려 수면, 호흡곤란 시 진료.")
        else:
            tips.append("🫁 RSV 의심: 영아에서 심해질 수 있어 야간 악화 주의.")
    if ("로타" in nl) or ("노로" in nl):
        if on("설사 횟수(회/일)") or on("구토 횟수(회/일)"):
            tips.append("🚰 구토/설사: ORS(경구수분보충용액) 소량씩 자주, 탈수 소견 시 진료.")
        else:
            tips.append("🚰 구토/설사 가능성: 우유 일시 희석·담백한 식단, 지사제는 임의 복용 지양.")
    if ("아데노" in nl) or ("adeno" in nl) or ("pcf" in nl):
        if on("눈곱") or on("결막충혈"):
            tips.append("👁️ 결막염 동반 가능: 손위생·수건 개별 사용, 안약/가글은 처방에 따르기.")
    if ("인플루엔자" in nl) or ("influenza" in nl) or ("독감" in nl):
        if on("근육통/전신통") or on("기침 심함"):
            tips.append("🦠 인플루엔자 의심: 해열제 적절 사용, 기저질환/영유아면 항바이러스제 상담.")
    if ("파라" in nl) or ("parainfluenza" in nl):
        tips.append("🗣️ 파라인플루엔자: 후두염/크룹 주의, 밤에 기침 악화시 찬 공기 노출·가습 도움.")

    return tips


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
    st.caption("✅ 모바일 줄꼬임 방지 · 별명+PIN 저장/그래프 · 암별/소아/희귀암/육종 패널 · PDF 한글 폰트 고정 · 수치 변화 비교 · ANC 가이드")

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
        drug_list = _get_drug_list()
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
            "림프종": lymphoma_by_dx.get(lymphoma_key_map.get(cancer, cancer), []),
        }
        return list(dict.fromkeys(default_drugs_by_group.get(group, [])))


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
        if table_mode:
            render_inputs_table(vals)
        else:
            render_inputs_vertical(vals)
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
                conc = st.selectbox("시럽 농도", ["160 mg/5 mL", "120 mg/5 mL"], key="antipy_conc_acet")
                if mg_low and mg_high:
                    num, denom = map(int, conc.split()[0].split("mg/")[0]), int(conc.split("/")[1].split()[0])
                    # safer parse
                    try:
                        mg_num = int(conc.split("mg/")[0])
                    except Exception:
                        mg_num = 160
                    try:
                        ml_denom = int(conc.split("mg/")[1].split()[0].replace("mL",""))
                    except Exception:
                        ml_denom = 5
                    ml_low  = round(mg_low  * ml_denom / mg_num, 1)
                    ml_high = round(mg_high * ml_denom / mg_num, 1)
                    st.info(f"권장 1회 용량: **{mg_low}–{mg_high} mg** ≈ **{ml_low}–{ml_high} mL** ({conc})")
                    st.caption("간격: 4–6시간, 최대 5회/일. 복용 전 제품 라벨·의료진 지침을 확인하세요.")
            else:
                mg_low, mg_high = dose_ibuprofen(wt)
                conc = st.selectbox("시럽 농도", ["100 mg/5 mL"], key="antipy_conc_ibu")
                if mg_low and mg_high:
                    try:
                        mg_num = int(conc.split("mg/")[0])
                    except Exception:
                        mg_num = 100
                    try:
                        ml_denom = int(conc.split("mg/")[1].split()[0].replace("mL",""))
                    except Exception:
                        ml_denom = 5
                    ml_low  = round(mg_low  * ml_denom / mg_num, 1)
                    ml_high = round(mg_high * ml_denom / mg_num, 1)
                    st.info(f"권장 1회 용량: **{mg_low}–{mg_high} mg** ≈ **{ml_low}–{ml_high} mL** ({conc})")
                    st.caption("간격: 6–8시간, 생후 6개월 미만은 의료진과 상담 필요. 최대 일일 용량 준수.")

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
            t_urine_basic = st.checkbox("요검사(알부민/잠혈/요당/요Cr)")
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
                proteinuria_q = st.selectbox("알부민 소변(정성)", ["", "-", "+", "++"], index=0)
            with cq[2]:
                wbc_q = st.selectbox("백혈구(정성)", ["", "-", "+", "++"], index=0)
            with cq[3]:
                gly_q = st.selectbox("요당(정성)", ["", "-", "+++"], index=0)


            # 👇 정량(/HPF) 수치 입력
            u_rbc_hpf = num_input_generic("적혈구(소변, /HPF)", key="u_rbc_hpf", decimals=0, placeholder="예: 3")
            u_wbc_hpf = num_input_generic("백혈구(소변, /HPF)", key="u_wbc_hpf", decimals=0, placeholder="예: 10")
            if u_rbc_hpf is not None:
                extra_vals["적혈구(소변, /HPF)"] = u_rbc_hpf
            if u_wbc_hpf is not None:
                extra_vals["백혈구(소변, /HPF)"] = u_wbc_hpf

            # 설명 매핑
            _desc_hema = {"+":"소량 검출","++":"중등도 검출","+++":"고농도 검출"}
            _desc_prot = {"-":"음성","+":"경도 검출","++":"중등도 검출"}
            _desc_wbc  = {"-":"음성","+":"의심 수준","++":"양성"}
            _desc_gly  = {"-":"음성","+++":"고농도 검출"}

            if hematuria_q:
                extra_vals["혈뇨(정성)"] = f"{hematuria_q} ({_desc_hema.get(hematuria_q,'')})"
            if proteinuria_q:
                extra_vals["알부민 소변(정성)"] = f"{proteinuria_q} ({_desc_prot.get(proteinuria_q,'')})"
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
                # 수기 입력: Pro/Cr, urine (mg/g)
                upcr_manual = num_input_generic("Pro/Cr, urine (mg/g)", key="ex_upcr_manual", decimals=1, placeholder="예: 350.0")
                if upcr_manual is not None:
                    upcr = upcr_manual
    
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
    # [removed by request] render_schedule(nickname_key)  # 치료 단계/스케줄 표시는 혼동 방지를 위해 비활성화
    _prof = 'adult'
    

    st.divider()
    run = st.button("🔎 해석하기", use_container_width=True)

    if run:
        st.subheader(f"📋 해석 결과 — {nickname}#{pin if pin else '----'}")

        if mode == "일반/암":
            lines = interpret_labs(vals, extras)
            for line in lines:
                st.write(line)

            # 요검사 해석
            
            # 요검사 해석
            urine_lines = _interpret_urine(extra_vals)
            if urine_lines:
                st.markdown("### 🧪 요검사 해석")
                for ul in urine_lines:
                    st.write(ul)

            # 특수검사 해석 (색 배지)
            ref_profile = st.radio("컷오프 기준", ["성인(기본)", "소아"], index=0, horizontal=True, help="지질/일부 항목은 소아 기준이 다릅니다")
            _prof = "peds" if ref_profile == "소아" else "adult"
            spec_lines = _interpret_specials(extra_vals, vals, profile=_prof)

            if spec_lines:
                st.markdown("### 🧬 특수검사 해석")
                for sl in spec_lines:
                    st.markdown(sl, unsafe_allow_html=True)

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
            # Pull pediatric inputs
            age_m  = st.session_state.get("ped_age")
            temp_c = st.session_state.get("ped_temp")
            rr     = st.session_state.get("ped_rr")
            spo2   = st.session_state.get("ped_spo2")
            urine  = st.session_state.get("ped_u")
            ret    = st.session_state.get("ped_ret")
            nf     = st.session_state.get("ped_nf")
            ap     = st.session_state.get("ped_ap")
            redset = st.session_state.get("ped_obs", {})

            risk, plines = _peds_interpret_common(age_m, temp_c, rr, spo2, urine, ret, nf, ap, redset)
            st.markdown(f"### 🧠 종합 위험도: **{risk}**")
            for L in plines:
                st.write(L)

            # 해열제 안내(가볍게 리마인드)
            wt = st.session_state.get("antipy_wt")
            med = st.session_state.get("antipy_med", "")
            if wt:
                if med and str(med).startswith("아세트"):
                    lo, hi = dose_acetaminophen(wt)
                    if lo and hi: st.caption(f"아세트아미노펜 1회 **{lo}–{hi} mg** (4–6시간 간격, 최대 5회/일).")
                else:
                    lo, hi = dose_ibuprofen(wt)
                    if lo and hi: st.caption(f"이부프로펜 1회 **{lo}–{hi} mg** (6–8시간 간격).")

            st.markdown("### 🏠 가정 관리 팁")
            for t in _peds_care_advice():
                st.write("- " + t)

        else:
            # 소아 감염질환: vital/관찰 + 질환별 핵심 플래그를 기반으로 간단 해석
            name = infect_sel or ""
            age_m  = st.session_state.get("pedinf_age_m")
            temp_c = st.session_state.get("pedinf_temp_c")
            rr     = st.session_state.get("pedinf_rr")
            spo2   = None if st.session_state.get("pedinf_spo2_na") else st.session_state.get("pedinf_spo2")
            urine  = None
            redset = st.session_state.get("ped_obs_gi", {})
            core   = st.session_state.get("ped_infect_core", {})

            risk, plines = _peds_interpret_common(age_m, temp_c, rr, spo2, urine, None, None, None, redset)
            st.markdown(f"### 🧠 종합 위험도: **{risk}**")
            for L in plines:
                st.write(L)

            tips = _peds_disease_tips(name, core)
            if tips:
                st.markdown("### 🦠 질환별 포인트")
                for t in tips:
                    st.write("- " + t)

            # 해열제 리마인드 (감염질환 입력 쪽)
            wt2 = st.session_state.get("antipy_wt_gi")
            med2 = st.session_state.get("antipy_med_gi", "")
            if wt2:
                if med2 and str(med2).startswith("아세트"):
                    lo, hi = dose_acetaminophen(wt2)
                    if lo and hi: st.caption(f"아세트아미노펜 1회 **{lo}–{hi} mg** (4–6시간 간격, 최대 5회/일).")
                else:
                    lo, hi = dose_ibuprofen(wt2)
                    if lo and hi: st.caption(f"이부프로펜 1회 **{lo}–{hi} mg** (6–8시간 간격).")

            st.markdown("### 🏠 가정 관리 팁")
            for t in _peds_care_advice():
                st.write("- " + t)
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
        spec_lines_for_report = _interpret_specials(extra_vals, vals, profile=_prof)
        report_md = build_report(mode, meta, {k: v for k, v in vals.items() if entered(v)}, cmp_lines, extra_vals, meds_lines, food_lines, abx_lines)
        # 요검사 해석을 보고서에도 추가
        if urine_lines_for_report:
            report_md += "\n\n---\n\n### 🧪 요검사 해석\n" + "\n".join(["- " + _strip_html(l) for l in urine_lines_for_report])
        # 발열 가이드 + 면책 문구를 하단에 항상 추가
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