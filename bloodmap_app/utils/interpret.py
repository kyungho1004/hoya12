# -*- coding: utf-8 -*-
from typing import Dict, List
from ..config import (ORDER, LBL_WBC, LBL_Hb, LBL_PLT, LBL_ANC, LBL_Alb, LBL_CRP, LBL_Glu, LBL_Ca, LBL_Na, LBL_K)
from ..data.foods import FOODS
from ..data.drugs import ANTICANCER

def _fmt_pair(k, v):
    return f"- {k}: {v}"

def interpret_labs(vals: Dict, extras: Dict) -> List[str]:
    out = []
    WBC = vals.get(LBL_WBC); Hb = vals.get(LBL_Hb); PLT = vals.get(LBL_PLT); ANC = vals.get(LBL_ANC)
    Alb = vals.get(LBL_Alb); CRP = vals.get(LBL_CRP); Glu = vals.get(LBL_Glu)
    Ca = vals.get(LBL_Ca); Na = vals.get(LBL_Na); K = vals.get(LBL_K)

    if ANC is not None:
        if ANC < 500: out.append("🚨 ANC 500 미만: 감염 고위험 — **생야채 금지**, 조리식 권장, 외출 최소화")
        elif ANC < 1000: out.append("⚠️ ANC 1000 미만: 감염 주의 — 익힌 음식/잔반 2시간 이내 폐기")

    if Hb is not None and Hb < 9.0:
        out.append("🩸 Hb 낮음: 빈혈 증상(어지러움/피로) 관찰")

    if PLT is not None and PLT < 50:
        out.append("🛡️ 혈소판 낮음: 멍/코피, 넘어짐 주의")

    if CRP is not None and CRP > 0.5:
        out.append("🔥 CRP 상승: 염증/감염 의심 — 발열 가이드 참고")

    if Alb is not None and Alb < 3.5:
        out.append("🥛 알부민 낮음: 단백질 보충 식단 권장")

    if Glu is not None and Glu >= 200:
        out.append("🍬 혈당 높음: 저당 식이/수분 보충")

    if Na is not None and Na < 135:
        out.append("🧂 저나트륨: 전해질 음료 등으로 보충, 빠른 변동 시 병원 상담")
    if K is not None and K < 3.5:
        out.append("🥔 저칼륨: 칼륨 포함 식이 보충")
    if Ca is not None and Ca < 8.5:
        out.append("🦴 저칼슘: 칼슘 식이 보충(의사 지시에 따름)")

    # 특수검사(보체/요검 등) 해석
    spec = extras.get("special", {})
    if spec:
        C3 = spec.get("C3"); C4 = spec.get("C4")
        ProtU = spec.get("Proteinuria"); HemeU = spec.get("Hematuria"); GluU = spec.get("Glycosuria")
        if C3 is not None and C3 < 90: out.append("🧪 보체 C3 낮음: 보체 소모성 상태 가능 — 감염/면역질환 평가 필요")
        if C4 is not None and C4 < 10: out.append("🧪 보체 C4 낮음: 면역복합체 질환 가능성")
        if ProtU and ProtU >= 1: out.append("🫙 단백뇨 양성: 신장/단백 소실 의심 — 주치의 상담")
        if HemeU and HemeU >= 1: out.append("🫙 혈뇨 양성: 요로 감염/결석 등 평가 필요")
        if GluU and GluU >= 1: out.append("🫙 요당 양성: 혈당 이상/신세뇨관 문제 평가")

    return out if out else ["정상 범위 내 해석(입력값 기준)."]

def compare_with_previous(nickname_key: str, cur_vals: Dict) -> List[str]:
    import streamlit as st
    recs = st.session_state.get("records", {}).get(nickname_key, [])
    if not recs:
        return []
    prev = None
    # 마지막 저장 기록
    for r in reversed(recs):
        labs = r.get("labs") or {}
        if labs:
            prev = labs; break
    if not prev:
        return []
    out = ["최근 기록과 비교:"]
    for k, v in cur_vals.items():
        if v is None: 
            continue
        pv = prev.get(k)
        if pv is None: 
            continue
        diff = v - pv
        if abs(diff) > 0:
            sign = "↑" if diff > 0 else "↓"
            out.append(f"- {k}: {pv} → {v} ({sign}{abs(diff):.1f})")
    return out

def food_suggestions(vals: Dict, anc_place: str) -> List[str]:
    tips = []
    Alb = vals.get("Albumin(알부민)")
    K = vals.get("K(포타슘)")
    Hb = vals.get("Hb(혈색소)")
    Na = vals.get("Na(소디움)")
    Ca = vals.get("Ca(칼슘)")
    def row(title, key):
        foods = FOODS.get(key, [])
        if foods:
            tips.append(f"- **{title}**: " + ", ".join(foods))
    if Alb is not None and Alb < 3.5: row("알부민 낮음", "Albumin_low")
    if K is not None and K < 3.5: row("칼륨 낮음", "K_low")
    if Hb is not None and Hb < 10.0: row("Hb 낮음", "Hb_low")
    if Na is not None and Na < 135: row("나트륨 낮음", "Na_low")
    if Ca is not None and Ca < 8.5: row("칼슘 낮음", "Ca_low")

    # ANC 낮을 때 위생/조리 가이드
    ANC = vals.get("ANC(호중구)")
    if ANC is not None and ANC < 500:
        tips.append("- **ANC 저하 위생 가이드**: 생채소 금지, 익힌 음식/전자레인지 30초 이상, 멸균식품 권장, 조리 후 2시간 지나면 폐기, 껍질 있는 과일은 주치의와 상담")
    return tips

def summarize_meds(meds: Dict) -> List[str]:
    out = []
    for k, v in meds.items():
        alias = ANTICANCER.get(k, {}).get("alias", "")
        aes = ANTICANCER.get(k, {}).get("aes", [])
        if alias:
            out.append(f"- {k} ({alias}) 주의: " + (", ".join(aes) if aes else "—"))
        else:
            out.append(f"- {k} 주의: " + (", ".join(aes) if aes else "—"))
    # 특이: ATRA 분화증후군 경고 강조
    if "ATRA" in meds:
        out.append("⚠️ ATRA: **분화증후군(Differentiation Syndrome)** 주의 — 호흡곤란/부종/발열 발생 시 즉시 병원")
    return out

def abx_summary(extras_abx: Dict) -> List[str]:
    rows = []
    for cat, dose in extras_abx.items():
        if dose is None: 
            rows.append(f"- {cat}: 용량 미입력 — 일반 주의만 확인")
        else:
            rows.append(f"- {cat}: 입력 용량 {dose} — QT/상호작용 등 주의")
    return rows
