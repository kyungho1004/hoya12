
# -*- coding: utf-8 -*-
from typing import Dict, Any, List
from ..data.foods import FOODS

def interpret_labs(vals: Dict[str, Any], extras: Dict[str, Any]) -> List[str]:
    lines = []
    for k, v in (vals or {}).items():
        if v is None: 
            continue
        if "혈소판" in k and v < 100:
            lines.append(f"{k}: {v} → 🟠 감소(출혈 주의)")
        elif "WBC" in k and v < 3:
            lines.append(f"{k}: {v} → 🟡 백혈구 감소")
        elif "Hb" in k and v < 10:
            lines.append(f"{k}: {v} → 🟡 빈혈 가능")
        elif "CRP" in k and v >= 3:
            lines.append(f"{k}: {v} → 🔴 염증 상승")
        else:
            lines.append(f"{k}: {v}")
    return lines

def compare_with_previous(nickname_key: str, current: Dict[str, Any]) -> List[str]:
    # Streamlit session_state 접근은 app에서 처리하므로 여기는 포맷만
    out = []
    # App에서 직접 records를 넘겨주지는 않지만, 인터페이스만 유지
    for k, v in current.items():
        out.append(f"{k}: 최근값 {v} (이전 대비 비교는 별명 기록이 있을 때 표시)")
    return out

def food_suggestions(vals: Dict[str, Any], anc_place: str) -> List[str]:
    tips = []
    alb = None
    k = None
    hb = None
    for key, v in (vals or {}).items():
        if "알부민" in key: alb = v
        if "칼륨" in key: k = v
        if "Hb(" in key: hb = v
    if alb is not None and alb < 3.5:
        tips.append("**알부민 낮음** → 추천: " + ", ".join(FOODS.get("Albumin_low", [])))
    if k is not None and k < 3.5:
        tips.append("**칼륨 낮음** → 추천: " + ", ".join(FOODS.get("Potassium_low", [])))
    if hb is not None and hb < 10:
        tips.append("**Hb 낮음** → 추천: " + ", ".join(FOODS.get("Hb_low", [])))
    if anc_place == "가정":
        tips.append("**호중구 감소 시** 생채소 금지 · 익힌 음식/멸균식품 권장 · 조리 후 2시간 지난 음식은 피하세요.")
    return tips

def summarize_meds(meds: Dict[str, Any]) -> List[str]:
    out = []
    for name, info in (meds or {}).items():
        if name == "MTX":
            out.append("MTX: 간수치 상승/구내염/골수억제 주의. 엽산제 복용 지침 확인.")
        elif name == "6-MP":
            out.append("6-MP: 간독성/골수억제 가능. 복용량 과다 주의.")
        elif name == "ATRA":
            out.append("ATRA: 분화증후군(호흡곤란/발열/부종) 경고, 즉시 의료진 연락.")
        elif name == "G-CSF":
            out.append("G-CSF: 뼈통증/발열 반응 가능. 주사 부위 통증 관찰.")
        elif name == "ARA-C":
            f = info.get("form","")
            out.append(f"ARA-C({f}): 용량의존 골수억제/점막염/고용량 시 신경독성·결막염 주의.")
        else:
            out.append(f"{name}: 일반적 부작용 모니터링.")
    return out

def abx_summary(abx_dict: Dict[str, Any]) -> List[str]:
    out = []
    for k in (abx_dict or {}).keys():
        out.append(f"{k}: 과민반응/약물상호작용 주의. 신기능/간기능에 따라 용량조절 필요.")
    return out
