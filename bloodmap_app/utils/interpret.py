
# -*- coding: utf-8 -*-
import streamlit as st

def interpret_labs(vals, extras):
    lines = []
    # 간단한 예시: CRP/LDH/UA/BNP 중심으로 몇 줄 생성
    try:
        crp = vals.get("CRP")
        if crp is not None:
            if float(crp) <= 3: lines.append("CRP: 낮거나 정상 — 저등급 염증 가능.")
            elif float(crp) <= 10: lines.append("CRP: 상승 — 감염/염증 가능.")
            else: lines.append("CRP: 높은 편 — 임상 맥락 고려하여 평가.")
    except Exception:
        pass
    try:
        ldh = vals.get("LDH")
        if ldh and float(ldh) > 480:
            lines.append("LDH 상승 — 용혈/조직손상/종양활성 가능성.")
    except Exception:
        pass
    try:
        ua = vals.get("Uric Acid(UA)") or vals.get("UA") or vals.get("Uric Acid")
        if ua and float(ua) > 7.0:
            lines.append("요산 상승 — TLS/통풍 위험 평가.")
    except Exception:
        pass
    return lines

def compare_with_previous(nickname_key, cur_vals):
    S = st.session_state
    prevs = S.get("records", {}).get(nickname_key, [])
    if not prevs: return []
    last = prevs[-1].get("labs", {})
    out = []
    for k, v in (cur_vals or {}).items():
        try:
            pv = last.get(k)
            if pv is None or v is None: 
                continue
            dv = float(v) - float(pv)
            if abs(dv) >= 0.1:
                out.append(f"{k}: 이전 대비 {dv:+.1f} 변화")
        except Exception:
            continue
    return out

def food_suggestions(vals, anc_place):
    tips = []
    anc = vals.get("ANC(호중구)") or vals.get("ANC")
    try:
        anc = float(anc) if anc is not None else None
    except Exception:
        anc = None
    if anc is not None and anc < 1000:
        tips += ["익힌 음식 위주", "조리 후 2시간 지난 음식 금지", "껍질 과일/생채소는 담당의 지침 확인"]
    else:
        tips += ["균형 잡힌 식단", "수분 충분히(하루 1.5~2L)", "단백질과 채소 적절히"]
    if anc_place == "가정":
        tips.append("가정: 냉장/가열 위생 관리")
    else:
        tips.append("병원: 면회·공용물품 접촉 주의")
    return [f"- {t}" for t in tips]

def summarize_meds(meds: dict):
    out = []
    for k, v in (meds or {}).items():
        dose = v.get("dose_or_tabs") or v.get("dose") or ""
        out.append(f"{k}: 투여량 {dose}")
    return out

def abx_summary(abx_dict: dict):
    out = []
    for k, v in (abx_dict or {}).items():
        out.append(f"{k}: 입력한 용량 {v}")
    return out
