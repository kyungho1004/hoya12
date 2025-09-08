# -*- coding: utf-8 -*-
from .inputs import entered
try:
    from ..config import (ORDER, LBL_Hb, LBL_ANC, LBL_Alb, LBL_CRP, LBL_Glu)
except Exception:
    from config import (ORDER, LBL_Hb, LBL_ANC, LBL_Alb, LBL_CRP, LBL_Glu)
from ..data.foods import FOODS, ANC_FOOD_RULES
from ..data.drugs import ANTICANCER, ABX_GUIDE

def _fmt(k, v):
    try: return f"{k}: {float(v):g}"
    except: return f"{k}: {v}"

def interpret_labs(vals, extras):
    lines = []
    shown = [(k, vals.get(k)) for k in ORDER if entered(vals.get(k))]
    if not shown:
        return ["입력된 수치가 없습니다."]
    lines.append("**입력 수치 요약**")
    for k, v in shown: lines.append(f"- {_fmt(k, v)}")

    anc = vals.get(LBL_ANC); hb = vals.get(LBL_Hb)
    alb = vals.get(LBL_Alb); crp = vals.get(LBL_CRP); glu = vals.get(LBL_Glu)

    if anc and anc < 500:
        lines.append("⚠️ ANC 500 미만: 생채소 금지, 익힌 음식만 섭취. 남은 음식 2시간 이후 섭취 금지.")
    if hb and hb < 8.0:
        lines.append("⚠️ Hb 낮음: 빈혈 증상 관찰. 철분제는 혈액질환 환자에서 주치의 상의 필수.")
    if alb and alb < 3.0:
        lines.append("ℹ️ 알부민 낮음: 고단백 식사 권고.")
    if crp and crp >= 1.0:
        lines.append("⚠️ CRP 상승: 감염/염증 의심, 발열/호흡 증상 확인.")
    if glu and glu >= 200:
        lines.append("ℹ️ 혈당 높음: 저당 식이/수분 보충.")
    return lines

def compare_with_previous(patient_id, current_vals):
    from streamlit import session_state as S
    prev = (S.records.get(patient_id) or [])[-1] if (getattr(S, "records", None) and S.records.get(patient_id)) else None
    if not prev or not prev.get("labs"): return []
    lines = ["**이전 기록과 비교**"]
    for k, v in current_vals.items():
        if v is None: continue
        pv = prev["labs"].get(k); 
        if pv is None: continue
        try:
            diff = float(v) - float(pv)
            arrow = "↑" if diff > 0 else ("↓" if diff < 0 else "→")
            lines.append(f"- {k}: {pv} → {v} ({arrow} {diff:+g})")
        except: pass
    return lines

def food_suggestions(vals, anc_place):
    out = []
    alb = vals.get("Albumin(알부민)"); k = vals.get("K(포타슘)")
    hb = vals.get("Hb(혈색소)"); na = vals.get("Na(소디움)"); ca = vals.get("Ca(칼슘)")
    if alb is not None and alb < 3.0: out.append("**알부민 낮음 추천:** " + ", ".join(FOODS["Albumin_low"]))
    if k   is not None and k   < 3.5: out.append("**칼륨 낮음 추천:** " + ", ".join(FOODS["K_low"]))
    if hb  is not None and hb  < 9.0: out.append("**Hb 낮음 추천:** " + ", ".join(FOODS["Hb_low"]) + "  \n⚠️ 항암·혈액질환 환자 **철분제 비권장**(주치의와 상의).")
    if na  is not None and na  < 135: out.append("**나트륨 낮음 추천:** " + ", ".join(FOODS["Na_low"]))
    if ca  is not None and ca  < 8.5: out.append("**칼슘 낮음 추천:** " + ", ".join(FOODS["Ca_low"]))
    out.extend(ANC_FOOD_RULES)
    return out

def summarize_meds(meds: dict):
    lines = []
    for d, info in meds.items():
        meta = ANTICANCER.get(d, {})
        alias = meta.get("alias", ""); aes = meta.get("aes", [])
        base = f"- {d}" + (f" ({alias})" if alias else "")
        if "form" in info: base += f" · 제형: {info['form']}"
        if "dose" in info: base += f" · 용량: {info['dose']}"
        if "dose_or_tabs" in info: base += f" · 알약/용량: {info['dose_or_tabs']}"
        lines.append(base)
        if aes: lines.append("  · 주의: " + ", ".join(aes))
        if d == "ATRA": lines.append("  · 분화증후군 의심: 발열/호흡곤란/부종/저혈압 → 즉시 의료진 연락.")
        if d == "MTX":  lines.append("  · MTX: 간독성/점막염 주의, 엽산 보충 논의.")
    return lines

def abx_summary(abx_dict: dict):
    lines = []
    for cat, dose in abx_dict.items():
        tips = ABX_GUIDE.get(cat, [])
        base = f"- {cat}" + (f" · 용량: {dose}" if dose else "")
        lines.append(base)
        if tips: lines.append("  · 주의: " + ", ".join(tips))
    return lines
