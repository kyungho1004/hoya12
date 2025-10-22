# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import List, Dict, Tuple, Iterable
import re

# === [PATCH 2025-10-22 KST] ❤️ Cardio-Guard renderer ===
def _render_cardio_guard(st, rec: Dict):
    name = (rec.get("alias") or "").lower()
    moa  = (rec.get("moa") or "").lower()
    def any_in(s, kws): 
        return any(k in s for k in kws)
    show_anthr = any_in(name, ["doxorubicin","daunorubicin","idarubicin"]) or "anthracycline" in moa
    show_her2  = any_in(name, ["trastuzumab","pertuzumab","t-dm1","deruxtecan"]) or "her2" in moa
    show_qt    = any_in(name, ["vandetanib","selpercatinib","pralsetinib","osimertinib","lapatinib","entrectinib"]) or ("qt" in (rec.get("ae","").lower()))
    show_arac = ('ara-c hdac' in name) or ('cytarabine hdac' in name)

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
    if show_arac:
        bullets += [
            'Ara-C 고용량(HDAC)에서 드문 심낭염/심낭삼출 보고: 흉통·호흡곤란 시 즉시 보고',
            '증상 시 ECG/심장효소(Troponin) 평가 고려'
        ]
    if show_qt:
        bullets += [
            "QT 연장 위험: 기저 ECG ± 추적, K≥4.0 / Mg≥2.0 유지",
            "동시 QT 연장 약물·저칼륨혈증·저마그네슘혈증 교정",
            "실신·심계항진·어지럼 발생 시 즉시 연락"
        ]

    html = "<ul>" + "".join(f"<li>{b}</li>" for b in bullets) + "</ul>"
    block = "<div class='cardio-guard'><div class='title'>❤️ Cardio‑Guard</div>" + html + "</div>"
    st.markdown(block, unsafe_allow_html=True)



# === [PATCH 2025-10-22 KST] AE detail expander ===
def _render_ae_detail(st, rec: Dict):
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
        html += bullet("참고", det.get("notes"))
        if html:
            st.markdown(f"<div class='ae-detail'>{html}</div>", unsafe_allow_html=True)



# === [PATCH 2025-10-22 KST] Monitoring checklist renderer ===

def _render_monitoring_chips(st, rec: Dict):
    mons = rec.get("monitor") if isinstance(rec, dict) else None
    if not mons:
        return

    ICONS = [
        ("CBC", "🩸 CBC"),
        ("LFT", "🧪 LFT"),
        ("Renal", "🧪 Renal(eGFR)"),
        ("Electrolytes", "⚡ Electrolytes"),
        ("Fever/Sepsis", "🌡️ Fever/Sepsis"),
        ("Mucositis", "💊 Mucositis"),
        ("N/V", "🤢 N/V"),
        ("Diarrhea", "💩 Diarrhea"),
        ("Cerebellar", "🧠 Cerebellar exam"),
        ("Conjunctivitis", "👁️ Conjunctivitis"),
        ("Ototoxicity", "👂 Ototoxicity"),
        ("Neuropathy", "🧠 Neuropathy"),
        ("Cold-induced neuropathy", "🧊 Cold neuropathy"),
        ("Allergy", "🤧 Allergy"),
        ("Hypersensitivity", "🤧 Hypersensitivity"),
        ("Edema", "💧 Edema"),
        ("Echo/LVEF", "❤️ Echo/LVEF"),
        ("BNP", "❤️ BNP/NT-proBNP"),
        ("BP", "📈 BP"),
        ("Proteinuria", "🧪 Proteinuria(UPCR)"),
        ("Wound healing/bleeding", "🩹 Wound/bleeding"),
        ("ILD", "🫁 ILD"),
        ("QT", "🫀 QT(ECG)"),
        ("Lipids", "🧪 Lipids"),
        ("Glucose", "🧪 Glucose"),
        ("TFT", "🧪 TFT"),
        ("Cortisol", "🧪 Cortisol±ACTH"),
        ("iRAE", "⚠️ iRAE screening"),
        ("SpO2", "🌬️ SpO₂"),
        ("Rash", "🧴 Rash"),
    ]

    def prettify(x: str) -> str:
        s = str(x)
        for key, label in ICONS:
            if key.lower() in s.lower():
                return label
        return s

    chips_html = "".join([f"<span class='chip'>{prettify(x)}</span>" for x in mons])
    st.markdown(f"<div class='monitor-chips'>🩺 {chips_html}</div>", unsafe_allow_html=True)


# 심각도 규칙 (키워드 기반 하이라이트)
AE_RULES: List[Tuple[str, List[str]]] = [
    ("🚨 위중", [
        "분화증후군","QT","심근독성","폐섬유화","아나필락시","아나필락시스","SJS","스티븐스","독성표피괴사","TEN",
        "혈구감소","범혈구감소","무과립구증","심부전","폐렴","C.? difficile","혈전","출혈","췌장염","간부전",
        "신부전","신부전증","소뇌독성","경련","뇌병증","GI 천공","심실성 부정맥","HBV 재활성화","헤모글로빈 급감"
    ]),
    ("🟧 주의", [
        "신장독성","간독성","고칼륨","저칼륨","저나트륨","저칼슘","고혈압","담즙정체","담즙정체성 간염",
        "적색인자","레드맨","주입반응","말초신경병증","CPK 상승","시신경염","시야","과민반응","감염위험",
        "장천공","당뇨악화","갑상선","혈당상승","탈수","용량 의존"
    ]),
    ("🟡 흔함/경미", [
        "오심","구토","설사","변비","탈모","피로","발진","가려움","미각","두통","현기증","어지러움",
        "점막염","주사부위","홍반"
    ]),
]

SEV_ORDER = ["🚨 위중", "🟧 주의", "🟡 흔함/경미"]

def _scan_hits(text: str) -> Dict[str, List[str]]:
    hits: Dict[str, List[str]] = {k: [] for k, _ in AE_RULES}
    if not text:
        return hits
    for tag, kws in AE_RULES:
        for kw in kws:
            if re.search(kw, text, flags=re.I):
                if kw not in hits[tag]:
                    hits[tag].append(kw)
    return hits

def _get_entry(db: Dict, key: str) -> Dict:
    if not key:
        return {}
    return db.get(key) or db.get(key.strip("'\"")) or {}

def collect_top_ae_alerts(drug_keys: Iterable[str], db: Dict | None = None) -> List[str]:
    """선택된 약물들 중 중요 경고만 모아 Top 리스트를 반환"""
    from drug_db import DRUG_DB as _DB
    ref = db if isinstance(db, dict) else _DB
    alerts = []
    for k in (drug_keys or []):
        e = _get_entry(ref, k)
        name = e.get("alias") or k
        ae   = e.get("ae","")
        hits = _scan_hits(ae).get("🚨 위중", [])
        if hits:
            alerts.append(f"🚨 {name}: " + ", ".join(hits))
    # 중복 제거, 상위 8개까지만
    seen = set(); out = []
    for a in alerts:
        if a not in seen:
            out.append(a); seen.add(a)
    return out[:8]

def _emit_box(st, severity: str, header: str, body: str):
    msg = f"{header}\n\n{body}" if header else body
    if severity == "🚨 위중":
        st.error(msg)
    elif severity == "🟧 주의":
        st.warning(msg)
    else:
        st.info(msg)

def render_adverse_effects(st, drug_keys: List[str], db: Dict):
    """약물별 부작용을 '색상 박스 안에 본문까지' 넣어서 보여줍니다."""
    if not drug_keys:
        st.caption("선택된 약물이 없습니다.")
        return
    for k in drug_keys:
        # Ara-C formulation override (robust)
        if _is_arac_like(k):
            pick = _arac_formulation_picker(st, db)
            if pick:
                k = pick
        e = _get_entry(db, k)
        if not isinstance(e, dict) or not e:
            st.write(f"- {k}")
            continue
        name = e.get("alias") or k
        moa  = e.get("moa") or ""
        ae   = e.get("ae") or ""

        # 헤더 (약명/기전)
        st.markdown(f"**{name}**")
        if moa:
            st.caption(moa)

        # 하이라이트 스캔
        hits = _scan_hits(ae)
        # 최상위 심각도 선택
        top_sev = next((s for s in SEV_ORDER if hits.get(s)), None)

        if top_sev:
            # 박스 헤더: "🚨 분화증후군 • 🟡 두통" 형태로 전 심각도 요약
            chips = []
            for sev in SEV_ORDER:
                kws = hits.get(sev) or []
                if not kws:
                    continue
                icon = sev.split()[0]  # 이모지
                chips.append(icon + " " + " · ".join(kws))
            header = " / ".join(chips)
            _emit_box(st, top_sev, header, ae)   # ✅ 본문을 박스 안에 넣음
        else:
            # 키워드 매치가 없으면 일반 정보 박스로 통째로 출력
            st.info(ae or "부작용 정보가 등록되어 있지 않습니다.")

        st.divider()

def results_only_after_analyze(st) -> bool:
    """원래 함수 유지 가정: 버튼 클릭 후 결과 섹션만 보여주기 위한 게이트"""
    return bool(st.session_state.get("analyzed"))

# === [PATCH 2025-10-22 KST] Robust Ara-C helpers (appended at EOF) ===
def _is_arac_like(name: str) -> bool:
    s = (name or "").lower()
    return ("ara-c" in s) or ("cytarabine" in s) or ("시타라빈" in s)

def _arac_formulation_picker(st, db: Dict):
    opts = []
    label_map = {"Ara-C IV":"정맥(IV)","Ara-C SC":"피하(SC)","Ara-C HDAC":"고용량(HDAC)"}
    for key in ["Ara-C IV","Ara-C SC","Ara-C HDAC","Cytarabine IV","Cytarabine SC","Cytarabine HDAC"]:
        if key in db:
            opts.append(key if key.startswith("Ara-C") else key.replace("Cytarabine","Ara-C"))
    if not opts:
        return None
    opts = sorted(set(opts))
    choice = st.radio("Ara-C 제형 선택", opts, format_func=lambda k: label_map.get(k,k), key="arac_form_pick")
    return choice

