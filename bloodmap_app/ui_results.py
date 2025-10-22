
from typing import Dict, Any, List
import re

def render_adverse_effects(st, drug_keys: List[str], db: Dict[str, Dict[str, Any]]):
    """
    Shared renderer: shows (in order)
      1) AE summary
      2) Monitoring chips
      3) Easy-detail expander
      4) ❤️ Cardio-Guard when relevant
    Includes Ara-C formulation picker (IV/SC/HDAC) up front when any Ara-C-like key is present.
    """
    if not drug_keys:
        st.caption("선택된 항암제가 없습니다.")
        return

    for k in drug_keys:
        # --- Ara-C formulation override (robust) ---
        if _is_arac_like(k):
            pick = _arac_formulation_picker(st, db)
            if pick:
                k = pick

        rec = db.get(k, {})
        alias = rec.get("alias", k)
        st.write(f"- **{alias}**")

        # 1) AE summary
        ae = rec.get("ae", "")
        if ae and "부작용 정보 필요" not in ae:
            st.caption(ae)
        else:
            st.caption("요약 부작용 정보가 부족합니다.")

        # 2) Monitoring chips
        _render_monitoring_chips(st, rec)

        # 3) Easy-detail
        _render_ae_detail(st, rec)

        # 4) Cardio-Guard
        _render_cardio_guard(st, rec)

        st.divider()


# ---------- Helpers ----------
def _is_arac_like(name: str) -> bool:
    s = (name or "").lower()
    return ("ara-c" in s) or ("cytarabine" in s) or ("시타라빈" in s)

def _arac_formulation_picker(st, db: Dict[str, Dict[str, Any]]):
    opts = []
    label_map = {"Ara-C IV":"정맥(IV)","Ara-C SC":"피하(SC)","Ara-C HDAC":"고용량(HDAC)"}
    for key in ["Ara-C IV","Ara-C SC","Ara-C HDAC","Cytarabine IV","Cytarabine SC","Cytarabine HDAC"]:
        if key in db:
            # Normalize Cytarabine* label to Ara-C for consistency in UI
            opts.append(key if key.startswith("Ara-C") else key.replace("Cytarabine","Ara-C"))
    opts = sorted(set(opts))
    if not opts:
        return None
    return st.radio("Ara-C 제형 선택", opts, format_func=lambda k: label_map.get(k,k), key="arac_form_pick")

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
