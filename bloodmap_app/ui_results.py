
from typing import Dict, Any, List
import re

# Public API
def render_adverse_effects(st, drug_keys: List[str], db: Dict[str, Dict[str, Any]]):
    if not drug_keys:
        st.caption("선택된 항암제가 없습니다.")
        return

    # 1) 라벨/키 정리
    label_map = {k: db.get(k, {}).get("alias", k) for k in drug_keys}

    # 2) Ara-C 제형 라디오 (혼합 표기 모두 감지)
    def _is_arac_like(name: str) -> bool:
        s = (name or "").lower()
        return ("ara-c" in s) or ("cytarabine" in s) or ("시타라빈" in s)

    def _arac_formulation_picker(st, db: Dict[str, Dict[str, Any]]):
        opts = []
        label_map2 = {"Ara-C IV":"정맥(IV)","Ara-C SC":"피하(SC)","Ara-C HDAC":"고용량(HDAC)"}
        for key in ["Ara-C IV","Ara-C SC","Ara-C HDAC","Cytarabine IV","Cytarabine SC","Cytarabine HDAC"]:
            if key in db:
                opts.append(key if key.startswith("Ara-C") else key.replace("Cytarabine","Ara-C"))
        opts = sorted(set(opts))
        if not opts:
            return None
        return st.radio("Ara-C 제형 선택", opts, format_func=lambda k: label_map2.get(k, k), key="arac_form_pick")

    # 3) 렌더 루프
    for k in drug_keys:
        if _is_arac_like(k):
            pick = _arac_formulation_picker(st, db)
            if pick:
                k = pick

        rec = db.get(k, {})
        alias = rec.get("alias", k)
        st.write(f"- **{alias}**")

        # 요약 AE
        ae = rec.get("ae", "")
        if ae and "부작용 정보 필요" not in ae:
            st.caption(ae)
        else:
            st.caption("요약 부작용 정보가 부족합니다.")

        # 모니터링 칩
        _render_monitoring_chips(st, rec)

        # 쉬운말 상세
        _render_ae_detail(st, rec)

        # Cardio-Guard
        _render_cardio_guard(st, rec)

        st.divider()


def _render_monitoring_chips(st, rec: Dict[str, Any]):
    chips = []
    ae = rec.get("ae","")
    if any(x in ae for x in ["골수억제","호중구","혈소판"]):
        chips.append("🩸 CBC 주기 체크")
    if any(x in ae for x in ["고혈압","단백뇨"]):
        chips.append("🩺 혈압/소변 단백 모니터")
    if any(x in ae for x in ["간효소","간독성","황달"]):
        chips.append("🧪 간기능(LFT) 추적")
    if any(x in ae for x in ["신독성","크레아티닌","혈뇨"]):
        chips.append("🧪 신기능(Cr/eGFR) 추적")
    if any(x in ae for x in ["설사","오심","구토"]):
        chips.append("💧 탈수 주의")
    if "QT" in ae or "QT " in ae:
        chips.append("📈 ECG/QT 체크")

    if chips:
        st.markdown(" ".join([f"<span class='chip'>{c}</span>" for c in chips]), unsafe_allow_html=True)


def _render_ae_detail(st, rec: Dict[str, Any]):
    det = rec.get("ae_detail") if isinstance(rec, dict) else None
    if not isinstance(det, dict) or not det:
        return
    with st.expander("🔎 자세히 보기 (쉽게 설명)", expanded=False):
        def bullet(title, items):
            if not items: return ""
            lis = "".join([f"<li>{x}</li>" for x in items])
            return f"<p><b>{title}</b></p><ul>{lis}</ul>"
        html = ""
        html += bullet("자주 나타나는 증상", det.get("common"))
        html += bullet("중요한 경고 신호", det.get("serious"))
        html += bullet("관리 팁", det.get("tips"))
        html += bullet("바로 연락해야 할 때", det.get("call"))
        if html:
            st.markdown(f"<div class='ae-detail'>{html}</div>", unsafe_allow_html=True)


def _render_cardio_guard(st, rec: Dict[str, Any]):
    name = (rec.get("alias") or "").lower()
    moa  = (rec.get("moa") or "").lower()
    def any_in(s, kws): 
        return any(k in s for k in kws)
    show_anthr = any_in(name, ["doxorubicin","daunorubicin","idarubicin"]) or "anthracycline" in moa
    show_her2  = any_in(name, ["trastuzumab","pertuzumab","t-dm1","deruxtecan"]) or "her2" in moa
    show_qt    = any_in(name, ["vandetanib","selpercatinib","pralsetinib","osimertinib","lapatinib","entrectinib"]) or ("qt" in (rec.get("ae","").lower()))
    show_arac  = any_in(name, ["ara-c hdac","cytarabine hdac"])

    if not (show_anthr or show_her2 or show_qt or show_arac):
        return

    bullets = []
    if show_anthr:
        bullets += [
            "누적 용량 추적(도옥소루비신 환산) — 250–300mg/m²: 경계, 400–450mg/m²: 고위험",
            "LVEF: 기저 및 3개월 간격(센터 프로토콜 우선)",
            "LVEF <50% & 10%p 감소 또는 증상성: 일시중단·평가",
            "증상: 숨가쁨·정좌호흡·야간호흡곤란·말초부종·갑작스런 체중↑ → 즉시 상담",
            "고위험군(이전 흉부방사선, 심질환 등): Dexrazoxane 고려"
        ]
    if show_her2:
        bullets += [
            "Trastuzumab 계열: LVEF 기저 및 주기적(보통 q3mo)",
            "LVEF 저하 또는 심부전 증상 시 보류·심장평가"
        ]
    if show_qt:
        bullets += [
            "QT 연장 위험: 기저 ECG ± 추적, K≥4.0 / Mg≥2.0 유지",
            "동시 QT 연장 약물·저칼륨혈증·저마그네슘혈증 교정",
            "실신·심계항진·어지럼 발생 시 즉시 연락"
        ]
    if show_arac:
        bullets += [
            "Ara-C 고용량(HDAC) 드문 심낭염/심낭삼출: 흉통·호흡곤란 시 즉시 보고",
            "증상 시 ECG/심장효소(Troponin) 평가 고려"
        ]
    html = "<ul>" + "".join(f"<li>{b}</li>" for b in bullets) + "</ul>"
    st.markdown("<div class='cardio-guard'><div class='title'>❤️ Cardio-Guard</div>"+html+"</div>", unsafe_allow_html=True)



# === [PATCH:P1_UI_AE_RENDER] BEGIN ===
def _bm_get_ae_detail_map():
    """
    Returns a dict of AE details keyed by canonical drug name.
    Non-destructive: only used if app chooses to render detailed AE.
    """
    return {
        "5-FU": {
            "title": "5‑Fluorouracil (5‑FU) / 5‑플루오로우라실",
            "common": ["골수억제", "오심/구토", "설사", "구내염", "손발증후군"],
            "serious": ["심근허혈/경련", "중증 설사·탈수", "중증 골수억제", "드문 뇌병증"],
            "call": ["38.5℃ 이상 발열", "수양성 설사 ≥4회/일", "출혈 경향", "섭취 불가 수준의 구내염"]
        },
        "Alectinib": {
            "title": "Alectinib (알렉티닙)",
            "common": ["근육통/CK 상승", "변비", "피로", "광과민", "부종"],
            "serious": ["간독성", "근병증", "서맥", "간질성 폐질환(희귀)"],
            "call": ["황달/암색 소변", "심한 근육통/무력감", "호흡곤란/기침 악화"]
        },
        "Ara-C": {
            "title": "Cytarabine (Ara‑C) / 시타라빈",
            "formulations": {
                "IV": ["발열 반응", "고용량 시 각막염 예방 위해 점안제 병용 고려"],
                "SC": ["주사부위 반응", "국소 통증/홍반"],
                "HDAC": ["각막염", "신경독성(소뇌 실조/언어장애)", "고열"]
            },
            "common": ["골수억제", "발열·오한", "오심/구토", "간효소 상승", "발진"],
            "serious": ["각막염(HDAC)", "소뇌 증상(HDAC)", "중증 감염"],
            "call": ["38.5℃ 이상 발열", "시야 흐림/안통", "보행 실조/말어눌", "비정상 출혈"]
        },
        "Bendamustine": {
            "title": "Bendamustine",
            "common": ["골수억제", "피로", "오심", "발진/가려움"],
            "serious": ["중증 감염", "심각한 피부반응(SJS/TEN)"],
            "call": ["고열", "점상출혈/멍", "광범위 발진", "호흡곤란"]
        },
        "Bevacizumab": {
            "title": "Bevacizumab (베바시주맙)",
            "common": ["고혈압", "단백뇨", "출혈 경향"],
            "serious": ["혈전증", "상처치유 지연", "GI 천공(희귀)"],
            "call": ["심한 두통/시야 변화", "혈뇨/거품뇨", "복부 극심한 통증", "급성 신경학 증상"]
        },
        "Bleomycin": {
            "title": "Bleomycin",
            "common": ["발열/오한", "피부 색소침착/경화", "손발톱 변화"],
            "serious": ["폐독성(간질성)", "호흡부전"],
            "call": ["진행성 호흡곤란", "고열", "흉통"]
        }
    }

def build_ae_summary_md(drug_list, formulation_map=None):
    """
    drug_list: iterable of canonical names (e.g., ["5-FU","Alectinib","Ara-C"])
    formulation_map: optional dict like {"Ara-C":"HDAC"} to fine-tune per-formulation notes.
    Returns markdown string for inclusion in .md/.pdf reports.
    """
    ae = _bm_get_ae_detail_map()
    lines = ["## 항암제 요약 (영/한 + 부작용)"]
    if not drug_list:
        lines.append("- (선택된 항암제가 없습니다)")
        return "\n".join(lines)
    for d in drug_list:
        info = ae.get(d)
        if not info:
            lines.append(f"- **{d}**: 상세 정보 준비 중")
            continue
        title = info.get("title", d)
        lines.append(f"### {title}")
        forms = info.get("formulations") or {}
        sel_form = None
        if formulation_map and d in formulation_map:
            sel_form = formulation_map.get(d)
        if forms:
            if sel_form and sel_form in forms:
                lines.append(f"- **제형({sel_form})**: " + " · ".join(forms[sel_form]))
            else:
                for fk, fv in forms.items():
                    lines.append(f"- **제형({fk})**: " + " · ".join(fv))
        common = info.get("common") or []
        serious = info.get("serious") or []
        call = info.get("call") or []
        if common:  lines.append("- **일반**: " + " · ".join(common))
        if serious: lines.append("- **중증**: " + " · ".join(serious))
        if call:    lines.append("- **연락 필요**: " + " · ".join(call))
        lines.append("")
    return "\n".own_join(lines) if hasattr(str, "own_join") else "\n".join(lines)

def render_ae_detail(drug_list, formulation_map=None):
    """
    Streamlit-safe renderer for AE summary in UI.
    If streamlit isn't available, returns markdown string.
    """
    try:
        import streamlit as st
        md = build_ae_summary_md(drug_list, formulation_map=formulation_map)
        st.markdown(md)
        return md
    except Exception:
        return build_ae_summary_md(drug_list, formulation_map=formulation_map)
# === [PATCH:P1_UI_AE_RENDER] END ===

