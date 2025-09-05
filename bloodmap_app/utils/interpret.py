
# -*- coding: utf-8 -*-
from .inputs import entered
from ..config import (LBL_WBC, LBL_Hb, LBL_PLT, LBL_ANC, LBL_Alb, LBL_Na, LBL_K, LBL_Ca, LBL_CRP, LBL_Glu, ORDER)
from ..data.foods import FOODS
from ..data.drugs import ANTICANCER

def _fmt(name, v):
    return f"{name}: {v}"

def interpret_labs(vals, extras):
    out = []
    WBC = vals.get(LBL_WBC); Hb = vals.get(LBL_Hb); PLT = vals.get(LBL_PLT); ANC = vals.get(LBL_ANC)
    Alb = vals.get(LBL_Alb); Na = vals.get(LBL_Na); K = vals.get(LBL_K); Ca = vals.get(LBL_Ca)
    CRP = vals.get(LBL_CRP); Glu = vals.get(LBL_Glu)
    diur = extras.get("diuretic_amt")

    if entered(ANC) and ANC < 500:
        out.append("🚨 **중증 호중구감소(ANC<500)** — 생채소 금지, 모든 음식은 완전 가열/전자레인지 ≥30초, 남은 음식 2시간 이후 섭취 금지, 껍질 과일은 주치의와 상의.")
    if entered(WBC): out.append(_fmt(LBL_WBC, WBC))
    if entered(Hb) and Hb < 8.0: out.append("⚠️ 빈혈 의심(Hb<8). 피로/어지럼 주의.")
    if entered(PLT) and PLT < 50: out.append("⚠️ 혈소판 감소(PLT<50k) — 멍/출혈 주의.")
    if entered(CRP) and CRP > 0.5: out.append("⚠️ 염증 상승(CRP>0.5). 발열 모니터.")
    if entered(Alb) and Alb < 3.3: out.append("⚠️ 저알부민 — 단백질 섭취 필요.")
    if entered(Na) and Na < 135: out.append("⚠️ 저나트륨 — 수분/전해질 관리.")
    if entered(K) and K < 3.5: out.append("⚠️ 저칼륨 — 근력 저하/부정맥 주의.")
    if entered(Ca) and Ca < 8.5: out.append("⚠️ 저칼슘 — 근경련/저림 가능.")
    if entered(Glu) and Glu >= 200: out.append("⚠️ 고혈당(혈당 ≥200). 저당 식이 권장.")
    if entered(diur) and diur>0:
        out.append("💊 이뇨제 복용 중 — 탈수 및 전해질 이상(저K/저Na/저Ca) 모니터.")
    return out

def compare_with_previous(nickname_key, current_vals):
    if not current_vals: 
        return []
    return [f"- {k}: 이번 입력값 {v}" for k,v in current_vals.items()]

def food_suggestions(vals, anc_place):
    out = []
    Alb = vals.get(LBL_Alb); Na = vals.get(LBL_Na); K = vals.get(LBL_K); Ca = vals.get(LBL_Ca); Hb = vals.get(LBL_Hb)
    def _mk(title, key):
        foods = FOODS.get(key, [])
        if foods:
            out.append(f"**{title}** → " + ", ".join(foods))
    if Alb is not None and Alb < 3.3: _mk("알부민 낮음", "albumin_low")
    if K is not None and K < 3.5: _mk("칼륨 낮음", "k_low")
    if Hb is not None and Hb < 10.0: _mk("Hb 낮음", "hb_low")
    if Na is not None and Na < 135: _mk("나트륨 낮음", "na_low")
    if Ca is not None and Ca < 8.5: _mk("칼슘 낮음", "ca_low")
    if anc_place=="가정":
        out.append("가정관리 시 **멸균식품 권장**. 상온 보관식은 피하고, 익혀서 드세요.")
    return out

def summarize_meds(meds):
    lines = []
    for k, v in meds.items():
        alias = ANTICANCER.get(k, {}).get("alias","")
        aes = ", ".join(ANTICANCER.get(k, {}).get("aes", []))
        core = f"- {k} ({alias})"
        if "dose" in v or "dose_or_tabs" in v:
            core += f" — 용량/탭: {v.get('dose', v.get('dose_or_tabs'))}"
        if "form" in v:
            core += f" — 제형: {v['form']}"
        lines.append(core + (f" · 부작용: {aes}" if aes else ""))
    return lines

def abx_summary(abx_dict):
    lines = []
    for cat, amt in abx_dict.items():
        amt_s = f"{amt}" if amt is not None and amt != 0 else "—"
        lines.append(f"- {cat} — 투여량: {amt_s}")
    return lines
