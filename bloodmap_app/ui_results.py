
from typing import Dict, Any, List
import re

# Public API
def render_adverse_effects(st, drug_keys: List[str], db: Dict[str, Dict[str, Any]]):
    try:
        st.session_state["_aes_rendered_once"] = True
    except Exception:
        pass

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
        # 보강: DB에 없는 약물 키는 즉석 자리표시 등록(패치 방식)
        if k not in db:
            try:
                from drug_db import ALIAS_FALLBACK
            except Exception:
                ALIAS_FALLBACK = {}
            _alias = ALIAS_FALLBACK.get(k, k)
            db[k] = {"alias": _alias, "moa": "", "ae": "부작용 정보 필요", "monitor": []}
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

        _render_term_glossary(st, rec)

        # 모니터링 칩
        _render_monitoring_chips(st, rec)
        _render_monitoring_checklist(st, k, rec)

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




def _render_monitoring_checklist(st, drug_key: str, rec: Dict[str, Any]):
    """
    아이콘 + 체크리스트 UI
    - rec["monitor"] 리스트를 기반으로 렌더
    - 각 체크 상태는 세션 스코프 key로 유지(st.session_state)
    - 진행률 바 표시
    """
    items = rec.get("monitor") if isinstance(rec, dict) else None
    if not isinstance(items, (list, tuple)) or not items:
        return

    # 아이콘 매핑(가벼운 이모지, 접근성 고려하여 라벨 유지)
    ICONS = {
        "CBC": "🩸",
        "CBC(Platelet)": "🩸",
        "Platelet(T-DM1)": "🩸",
        "LFT": "🧪",
        "Renal(eGFR)": "🧪",
        "Electrolytes": "🧂",
        "Mg/K": "🧂",
        "BP": "🩺",
        "Proteinuria(UPCR)": "💧",
        "Echo/LVEF": "❤️",
        "BNP/NT-proBNP": "❤️",
        "ECG": "📈",
        "QT(ECG)": "📈",
        "Rash/Diarrhea": "💢",
        "ILD": "🫁",
        "SpO2(if respiratory)": "🫁",
        "Glucose": "🍬",
        "Lipids": "🧴",
        "TFT": "🦋",
        "Cortisol±ACTH": "🧬",
        "Allergy": "🤧",
        "Hypersensitivity": "🤧",
        "Edema(Doce)": "💧",
        "Ototoxicity": "🎧",
        "Neuropathy": "🔔",
        "Cold-induced neuropathy": "🧊",
        "Cerebellar exam": "🧠",
        "Conjunctivitis(스테로이드 점안)": "👁️",
        "iRAE screening": "🛡️",
        "Wound healing/bleeding": "🩹",
        "Rash/Nausea": "😖",
        "Mucositis": "💊",
        "N/V": "🤢",
        "Diarrhea": "💩",
        "Fever/Sepsis": "🔥",
        "Edema": "💧",
        "LFT/AST/ALT": "🧪",
        "Platelet": "🩸",
    }

    # 중복/정렬 정리
    norm = []
    seen = set()
    for it in items:
        s = str(it).strip()
        if not s: 
            continue
        if s not in seen:
            norm.append(s)
            seen.add(s)

    # 체크 상태 키
    base_key = f"monchk::{drug_key}::"
    done = 0
    total = len(norm)

    st.markdown("<div class='checklist-row'>", unsafe_allow_html=True)
    for s in norm:
        ico = ICONS.get(s) or ICONS.get(s.split("(")[0]) or "✅"
        key = base_key + s
        # 세션 상태 기본 False 보장
        if key not in st.session_state:
            st.session_state[key] = False
        checked = st.checkbox(f"{s}", value=bool(st.session_state[key]), key=key)
        if checked:
            done += 1
        # 옆에 아이콘 라벨을 꾸며서 보여주자
        st.markdown(f"<span class='checkitem'><span class='icon'>{ico}</span><span class='label'>{s}</span></span>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # 진행률
    pct = int(round((done/total)*100)) if total else 0
    st.markdown(f"<div class='checklist-progress'><div style='width:{pct}%;'></div></div>", unsafe_allow_html=True)
    st.caption(f"모니터링 진행률: {done}/{total} ({pct}%) — 약: {rec.get('alias') or drug_key}")


# --- 쉬운말 용어 풀이 (패치: 삭제 금지, 확장만) ---
GLOSSARY_TERMS = {
    "골수억제": "골수에서 피를 만드는 기능이 줄어들어 백혈구·혈색소·혈소판이 같이 떨어지는 상태예요. 감염/빈혈/출혈에 주의가 필요해요.",
    "호중구감소": "감염에 맞서는 백혈구(호중구)가 줄어든 상태예요. 38.0°C 이상 발열 시 즉시 병원 연락이 필요해요.",
    "손발증후군": "손·발 바닥이 붉고 따갑고 벗겨지는 증상이에요. 뜨거운 물/마찰을 피하고 보습제를 자주 발라주세요.",
    "구내염": "입안이 헐고 아픈 상태예요. 자극적 음식은 피하고, 처방받은 가글을 규칙적으로 사용하면 도움돼요.",
    "고혈압": "혈압이 높아지는 부작용이에요. 집에서 혈압을 주기적으로 재고, 두통/흉통/호흡곤란에 유의하세요.",
    "단백뇨": "소변에 단백질이 새는 상태예요. 소변거품이 많아질 수 있어요. 필요 시 UPCR 같은 검사를 해요.",
    "간효소상승": "AST/ALT 같은 간수치가 올라간 상태예요. 무증상일 수 있고, 수치 추적과 약 조절이 필요할 수 있어요.",
    "신독성": "콩팥(신장)에 무리가 가는 상태예요. Cr/eGFR로 신기능을 추적하고 수분보충이 중요해요.",
    "말초신경병증": "손발 저림/감각저하 등의 증상이에요. 일상생활에서 뜨거운 것/날카로운 것에 특히 주의하세요.",
    "QT 연장": "심전도에서 심장 재분극 간격(QTc)이 길어지는 상태예요. 실신/두근거림이 있으면 즉시 진료가 필요해요.",
    "탈모": "치료 중 일시적으로 머리카락이 빠질 수 있어요. 대부분 치료 종료 후 서서히 회복돼요.",
    "피로": "전신 피로감이 생길 수 있어요. 규칙적인 가벼운 활동과 수면 위생이 도움이 돼요.",
    "부종": "손발·다리 등이 붓는 증상이에요. 다리 올려 쉬기, 염분 조절이 도움이 될 수 있어요.",
    "속쓰림": "위장 자극으로 속이 쓰릴 수 있어요. 자극적 음식 피하고, 의사가 처방한 위보호제를 복용해요.",
    "오심": "메스꺼움이 느껴질 수 있어요. 소량씩 자주 먹고, 수분을 충분히 섭취하세요.",
    "구토": "토할 수 있어요. 탈수에 주의하고 필요 시 항구토제를 사용해요.",
    "설사": "묽은 변이 잦아질 수 있어요. 수분·전해질 보충과 지사제 사용을 의료진과 상의하세요.",
    "갑상선기능저하": "피로·추위 민감·체중 증가 등이 나타날 수 있어요. 혈액검사(TSH/FT4)로 확인해요.",
    "주입반응": "주사 중 알레르기 같은 반응(발열/오한/발진/호흡곤란)이 생길 수 있어요. 대부분 병원에서 대처가 진행돼요.",
    "분화증후군": "일부 백혈병 치료에서 발생할 수 있는 염증 반응이에요. 호흡곤란·부종·발열 시 즉시 병원 연락이 필요해요.",
}

# 용어 키 매핑(다국어/축약 포함)
GLOSSARY_ALIASES = {
    "구역": "오심", "속쓰림": "속쓰림",
    "QT": "QT 연장", "QTc": "QT 연장", "QT prolongation": "QT 연장",
    "HFS": "손발증후군", "hand-foot": "손발증후군",
    "mucositis": "구내염", "stomatitis": "구내염",
    "proteinuria": "단백뇨", "hypertension": "고혈압",
    "neuropathy": "말초신경병증", "PNP": "말초신경병증",
    "nephrotoxicity": "신독성", "hepatotoxicity": "간효소상승",
    "fatigue": "피로", "nausea": "오심", "vomiting": "구토", "diarrhea": "설사",
    "hypothyroidism": "갑상선기능저하", "infusion reaction": "주입반응",
    "differentiation syndrome": "분화증후군",
}

def _clean_text_for_glossary(s: str) -> str:
    if not isinstance(s, str):
        return ""
    # remove common emoji ranges + variation selector + bullets
    s = re.sub(r"[\u2600-\u27BF\u1F300-\u1F9FF\uFE0F]", " ", s)
    # unify separators
    s = s.replace("·", " ").replace("•", " ").replace("/", " ").replace("|", " ")
    # collapse whitespace
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _normalize_glossary_token(tok: str) -> str:
    s = tok.strip().lower()
    # normalize punctuation
    s = re.sub(r"[·,;/]+", " ", s)
    s = s.replace("(", " ").replace(")", " ")
    return s

def _extract_glossary_terms(*texts) -> list:
    found = []
    bag = " ".join([t for t in texts if isinstance(t, str)]).strip()
    bag_clean = _clean_text_for_glossary(bag)
    if not bag:
        return found
    # direct Korean terms
    for k in GLOSSARY_TERMS.keys():
        if k in bag_clean and k not in found:
            found.append(k)
    # aliases (English/abbr)
    low = bag_clean.lower()
    for a, canon in GLOSSARY_ALIASES.items():
        if a.lower() in low and canon not in found:
            found.append(canon)
    return found

def _render_term_glossary(st, rec):
    # 대상 텍스트: 부작용, MOA, 모니터링 레이블 일부
    ae = rec.get("ae", "")
    moa = rec.get("moa", "")
    monitor_items = rec.get("monitor", []) if isinstance(rec.get("monitor"), (list, tuple)) else []
    monitor_txt = " ".join(map(str, monitor_items))

    terms = _extract_glossary_terms(ae, moa, monitor_txt)
    if not terms:
        return

    try:
        if '_glossary_rendered_once' not in st.session_state:
            st.session_state['_glossary_rendered_once'] = True
        else:
            st.session_state['_glossary_rendered_once'] = True
    except Exception:
        pass

    st.markdown("**📚 어려운 용어 풀이**")
    for t in terms:
        desc = GLOSSARY_TERMS.get(t)
        if not desc:
            continue
        st.markdown(f"- **{t}** — {desc}")


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
