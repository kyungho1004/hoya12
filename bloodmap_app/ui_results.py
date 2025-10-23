
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
            try:
                aug = _augment_terms_with_explain(items)
            except Exception:
                aug = items
            lis = "".join([f"<li>{x}</li>" for x in aug])
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

# === [PATCH:AE_GLOSSARY_KO+NORMALIZE] BEGIN ===
import re as _re_gls

_AE_GLOSSARY_KO = {
    "QT 연장": "QT 간격이 연장되면 심장 리듬 이상이 발생할 수 있어요. 실신이나 돌연사 위험이 있으니 ECG(심전도) 추적 검사가 권장돼요.",
    "RA 증후군": "베사노이드(트레티노인) 사용 시 고열·호흡곤란·체중 증가가 동반되면 RA 증후군일 수 있어요. 스테로이드 치료가 필요할 수 있으니 즉시 병원에 알려야 해요.",
    "고삼투증후군": "탈수나 전해질 이상으로 의식 저하·구토가 나타날 수 있어요. 충분한 수분 섭취가 필요하며 증상 시 즉시 내원하세요.",
    "신경독성": "손발 저림, 시야 흔들림, 보행 불안정 등이 나타나면 신경계 이상일 수 있어요. 심해지기 전 주치의에게 알려야 해요.",
    "손발증후군": "손바닥·발바닥이 붉어지고 벗겨질 수 있어요. 미지근한 물로 씻고, 보습제를 자주 바르며 마찰을 줄이세요.",
    "골수억제": "백혈구·혈소판이 감소해 감염/출혈 위험이 증가해요. 발열(≥38.5℃)·쉽게 멍/코피가 나면 바로 연락하세요.",
    "간독성": "AST/ALT 상승, 황달·암색 소변이 생기면 간 이상 신호예요. 약 중단·검사 조정이 필요할 수 있어요.",
    "신장독성": "부종·소변 줄어듦·거품뇨가 있으면 신장 이상 신호예요. 수분 관리와 혈액/소변검사가 필요해요.",
    "광과민": "햇빛에 노출되면 쉽게 빨개지거나 발진이 생길 수 있어요. SPF, 긴옷, 자외선 차단이 중요해요.",
    "구내염": "입안 통증/궤양으로 식사가 어려울 수 있어요. 부드러운 음식, 자극 피하기, 얼음조각·가글이 도움돼요.",
    "설사": "수양성 설사·탈수 위험이 있어요. 보충수분(ORS)와 필요 시 지사제, 심하면 병원에 연락하세요.",
    "변비": "수분·식이섬유·가벼운 운동이 도움돼요. 3일 이상 변이 없거나 복통·구토 동반 시 의사와 상의하세요.",
    "오심/구토": "소량씩 자주 섭취하고, 처방된 항구토제를 규칙적으로 드세요. 탈수/구토 지속 시 연락하세요.",
    "탈수": "입 마름, 소변량 감소, 어지러움은 탈수 신호예요. 수분 보충이 필요하고 심하면 병원으로.",
    "저나트륨혈증": "두통·구역·혼동이 생길 수 있어요. 급격한 체중 증가(부종) 시 즉시 연락하세요.",
    "고칼륨혈증": "심장 두근거림·근력 저하가 나타날 수 있어요. ECG·혈액검사가 필요해요.",
    "출혈": "잇몸/코피·멍이 쉽게 생기면 혈소판 저하 가능성이 있어요. 넘어짐·상처를 주의하고 바로 연락하세요.",
    "혈전": "한쪽 다리 붓고 통증·호흡곤란·흉통은 혈전 신호예요. 즉시 응급평가가 필요해요.",
    "단백뇨": "거품뇨·부종이 있으면 신장 손상 신호예요. 소변검사 추적이 필요해요.",
    "고혈압": "두통·어지러움이 있으면 혈압을 확인하세요. 목표치를 넘어가면 약 조절이 필요할 수 있어요.",
    "상처치유 지연": "수술/상처가 잘 낫지 않을 수 있어요. 치료 전후 일정 조정이 필요하니 의료진과 상의하세요.",
    "폐독성": "기침·호흡곤란 악화는 폐 이상 신호예요. 흉부 영상·호흡기 평가가 필요해요.",
    "간질성 폐질환": "호흡곤란/건성 기침·발열이 동반되면 의심돼요. 약 중단과 스테로이드가 필요할 수 있어요.",
}

_AE_SYNONYMS = {
    "qt prolongation": "QT 연장",
    "qt interval prolongation": "QT 연장",
    "torsades": "QT 연장",
    "ra syndrome": "RA 증후군",
    "retinoic acid syndrome": "RA 증후군",
    "hand-foot syndrome": "손발증후군",
    "palmar-plantar erythrodysesthesia": "손발증후군",
    "neurotoxicity": "신경독성",
    "peripheral neuropathy": "신경독성",
    "stomatitis": "구내염",
    "mucositis": "구내염",
    "hepatic toxicity": "간독성",
    "renal toxicity": "신장독성",
    "photosensitivity": "광과민",
}

def _norm_ae_term(s: str) -> str:
    if not s:
        return ""
    x = s.strip()
    x = _re_gls.sub(r"\(.*?\)|\[.*?\]", "", x)
    x = _re_gls.sub(r"[·,:;/]+", " ", x)
    x = _re_gls.sub(r"\s+", " ", x).strip()
    return x

def _to_glossary_key(term: str):
    if not term:
        return None
    t = _norm_ae_term(term)
    if t in _AE_GLOSSARY_KO:
        return t
    low = t.lower()
    if low in _AE_SYNONYMS:
        k = _AE_SYNONYMS[low]
        if k in _AE_GLOSSARY_KO:
            return k
    for k in _AE_GLOSSARY_KO.keys():
        if k in t:
            return k
    return None

def _ae_explain(term: str):
    key = _to_glossary_key(term)
    return _AE_GLOSSARY_KO.get(key) if key else None

def _augment_terms_with_explain(terms):
    out = []
    for t in terms or []:
        exp = _ae_explain(t)
        label = _norm_ae_term(t)
        out.append(f"{label} — {exp}" if exp else label)
    return out
# === [PATCH:AE_GLOSSARY_KO+NORMALIZE] END ===

# === [PATCH:AE_GLOSSARY_OVERRIDE_BUILD] BEGIN ===
def build_ae_summary_md(drug_list, formulation_map=None):
    try:
        ae = _bm_get_ae_detail_map()
    except Exception:
        ae = {}
    lines = ["## 항암제 요약 (영/한 + 부작용)"]
    if not drug_list:
        lines.append("- (선택된 항암제가 없습니다)")
        return "\n".join(lines)
    for d in drug_list:
        info = (ae or {}).get(d)
        if not info:
            lines.append(f"### {d}")
            lines.append("- 상세 정보 준비 중")
            lines.append("")
            continue
        title = info.get("title", d)
        lines.append(f"### {title}")
        forms = info.get("formulations") or {}
        sel_form = (formulation_map or {}).get(d) if formulation_map else None
        if forms:
            if sel_form and sel_form in forms:
                lines.append(f"- **제형({sel_form})**: " + " · ".join(_augment_terms_with_explain(forms[sel_form])))
            else:
                for fk, fv in forms.items():
                    lines.append(f"- **제형({fk})**: " + " · ".join(_augment_terms_with_explain(fv)))
        common  = info.get("common") or []
        serious = info.get("serious") or []
        call    = info.get("call") or []
        if common:
            lines.append("- **일반**: " + " · ".join(_augment_terms_with_explain(common)))
        if serious:
            lines.append("- **중증**: " + " · ".join(_augment_terms_with_explain(serious)))
        if call:
            lines.append("- **연락 필요**: " + " · ".join(_augment_terms_with_explain(call)))
        lines.append("")
    return "\n".join(lines)
# === [PATCH:AE_GLOSSARY_OVERRIDE_BUILD] END ===
