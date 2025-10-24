"""
eGFR utilities and a minimal Streamlit UI (beta).
- Adult (>=18y): CKD-EPI 2021 creatinine-only (race-free)
- Pediatric (<18y): Schwartz (k=0.413)
Returns ml/min/1.73m^2 with KDIGO staging and safety notes.
"""
from __future__ import annotations
from typing import Optional, Tuple, Dict

def _ckdepi_2021_creatinine(age: float, sex: str, scr_mg_dl: float) -> float:
    sex = (sex or "").lower()
    kappa = 0.7 if sex.startswith("f") else 0.9
    alpha = -0.241 if sex.startswith("f") else -0.302
    scr_k = scr_mg_dl / kappa
    import math
    egfr = 142.0 * (min(scr_k, 1.0) ** alpha) * (max(scr_k, 1.0) ** -1.200) * (0.9938 ** age)
    if sex.startswith("f"):
        egfr *= 1.012
    return float(max(0.0, egfr))

def _schwartz_2009(height_cm: float, scr_mg_dl: float, k: float = 0.413) -> float:
    if not height_cm or height_cm <= 0:
        return 0.0
    if scr_mg_dl <= 0:
        return 0.0
    return float((k * height_cm) / scr_mg_dl)

def calc_egfr(age: float, sex: str, scr_mg_dl: float, height_cm: Optional[float] = None) -> Tuple[float, str]:
    """
    Returns (egfr, stage) where stage is KDIGO G1..G5.
    """
    try:
        age_f = float(age)
        scr = float(scr_mg_dl)
    except Exception:
        return 0.0, "NA"
    if age_f >= 18:
        egfr = _ckdepi_2021_creatinine(age_f, sex, scr)
    else:
        egfr = _schwartz_2009(float(height_cm or 0.0), scr)
    stage = stage_egfr(egfr)
    return round(egfr, 1), stage

def stage_egfr(egfr: float) -> str:
    if egfr >= 90: return "G1"
    if egfr >= 60: return "G2"
    if egfr >= 45: return "G3a"
    if egfr >= 30: return "G3b"
    if egfr >= 15: return "G4"
    return "G5"

def safety_notes(egfr: float) -> str:
    notes = []
    if egfr < 60:
        notes.append("신독성 약물·조영제 주의")
    if egfr < 45:
        notes.append("용량 조절 고려")
    if egfr < 30:
        notes.append("강력 금기/대체 약 검토")
    return " · ".join(notes) or "특이 위험 없음"

# ---- Minimal Streamlit UI (beta) ----
def render_egfr_tool(st) -> None:
    """Compact UI inside an expander. Safe to call multiple times."""
    try:
        with st.expander("eGFR 계산 (β)", expanded=False):
            col1, col2, col3, col4 = st.columns([1,1,1,1])
            with col1:
                age = st.number_input("나이(세)", min_value=0, max_value=120, value=40, step=1)
            with col2:
                sex = st.selectbox("성별", ["남", "여"])
                sex_en = "female" if sex == "여" else "male"
            with col3:
                scr = st.number_input("크레아티닌 (mg/dL)", min_value=0.0, max_value=20.0, value=1.0, step=0.1, format="%.2f")
            with col4:
                height = st.number_input("키 (cm, 소아만)", min_value=0.0, max_value=220.0, value=120.0, step=1.0)
            egfr, stage = calc_egfr(age, sex_en, scr, height_cm=height)
            st.markdown(f"**eGFR:** {egfr} mL/min/1.73㎡  •  **Stage:** {stage}")
            st.caption(safety_notes(egfr))
    except Exception:
        pass
