
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

# --- [PATCH 2025-10-23 KST] Contextual keyword explainers (patch-only, no removals) ---
# 목적: 부작용/설명 문자열 안에 특정 키워드가 '실제로 등장할 때만' 짧은 설명 배지를 자동 표기.
# 사용 예:
#   render_keyword_explainers(st, source_text)
#   -> source_text 안에 'QT', 'torsades', 'QT 연장' 등이 있으면 심전도/QT 가이드만 출력.
#
# 기존 기능은 삭제하지 않고, 이 함수는 선택적으로 호출할 수 있도록 별도 공개 API로 추가한다.
_KEYWORD_RULES: List[Dict[str, Any]] = [
    {
        "name": "QTc500",
        "patterns": [
            "(?-i)QTc\\s*(>=|≥|>|≧)\\s*500\\s*ms?",
            "(?-i)QTc\\s*500\\s*ms",
            "(?-i)QTc\\s*≥\\s*500",
            "(?-i)QTc\\s*>\\s*500"
        ],
        "html": (
            "<div class='explain-chip'>"
            "<b>QTc ≥ 500ms</b> — 위험수준: ECG/전해질(K≥4, Mg≥2) 확인, "
            "어지럼/실신 시 즉시 연락"
            "</div>"
        ),
    },
    {
        "name": "ILD_G2PLUS",
        "patterns": [
            "(?i)(grade|g)\\s*[2-4]\\s*(ild|pneumonitis)",
            "(?i)g[2-4]\\s*(ild|pneumonitis)",
            "등급\\s*[2-4]\\s*(폐렴|간질성\\s*폐질환)"
        ],
        "html": (
            "<div class='explain-chip'>"
            "<b>ILD G2+</b> — 휴약/스테로이드 고려, 흉부영상·산소포화도 추적 필요"
            "</div>"
        ),
    },
    {
        "name": "ILD_DIFF",
        "patterns": [
            "(?i)ild\\s*vs\\s*infection",
            "(?i)differential\\s*(pneumonitis|ild)",
            "폐렴\\s*감별",
            "감염\\s*감별"
        ],
        "html": (
            "<div class='explain-chip'>"
            "<b>ILD vs 감염 감별</b> — 발열/백혈구/CRP, HRCT/균배양 등 고려하여 "
            "감염·약물성 감별"
            "</div>"
        ),
    },
    {
        "name": "TE",
        "patterns": [
            "(?i)thromboembolism|vte",
            "(?i)deep\\s*vein\\s*thrombosis|dvt",
            "(?i)pulmonary\\s*embolism|pe",
            "혈전",
            "색전",
            "혈전색전증",
            "폐색전"
        ],
        "html": (
            "<div class='explain-chip'>"
            "<b>혈전/색전</b> — 종아리 부종·통증/호흡곤란·흉통 시 즉시 평가, "
            "활동·수분, 위험요인 있으면 추가 주의"
            "</div>"
        ),
    },
    {
        "name": "NEPHROTOX",
        "patterns": [
            "(?i)nephrotoxi(c|city)",
            "(?i)aki\\b|acute\\s*kidney\\s*injury",
            "크레아티닌\\s*상승",
            "Cr\\s*상승",
            "eGFR\\s*저하",
            "사구체여과\\s*감소"
        ],
        "html": (
            "<div class='explain-chip'>"
            "<b>신독성/AKI</b> — Cr/eGFR 추적, 수분 유지, NSAID/조영제 등 신독성 약물 주의"
            "</div>"
        ),
    },
    {
        "name": "DIARRHEA_DEHYD",
        "patterns": [
            "(?i)severe\\s*diarrhea",
            "(?i)grade\\s*[3-4]\\s*diarrhea",
            "물설사",
            ">=\\s*4\\s*회",
            "4\\s*회/일\\s*이상",
            "탈수"
        ],
        "html": (
            "<div class='explain-chip'>"
            "<b>설사/탈수</b> — ≥4회/일·혈변/고열 시 연락, ORS로 수분·전해질 보충, "
            "수액 필요 여부 평가"
            "</div>"
        ),
    },
    {
        "name": "ILD",
        "patterns": [
            "(?i)interstitial\\s+lung\\s+disease",
            "(?i)pneumonitis",
            "간질성\\s*폐질환",
            "약물성\\s*폐렴",
            "폐렴\\s*의심"
        ],
        "html": (
            "<div class='explain-chip'>"
            "<b>ILD/약물성 폐렴</b> — 기침·호흡곤란·산소포화도 저하 시 <i>즉시 연락</i>, "
            "휴약/스테로이드 필요할 수 있음"
            "</div>"
        ),
    },
    {
        "name": "TLS",
        "patterns": [
            "(?i)tumou?r\\s+lysis\\s+syndrome",
            "종양\\s*용해\\s*증후군",
            "요산\\s*상승",
            "칼륨\\s*상승",
            "인\\s*상승",
            "칼슘\\s*저하"
        ],
        "html": (
            "<div class='explain-chip'>"
            "<b>TLS(종양용해)</b> — 수분·소변량 체크, 오심·부정맥·경련 시 <i>즉시 연락</i>, "
            "요산·K·P·Ca 추적"
            "</div>"
        ),
    },
    {
        "name": "HSR",
        "patterns": [
            "(?i)hypersensitivity",
            "(?i)infusion\\s*reaction",
            "과민반응",
            "주입\\s*반응",
            "아나필락시스"
        ],
        "html": (
            "<div class='explain-chip'>"
            "<b>주입/과민반응</b> — 발진·숨참·쌕쌕/저혈압 시 <i>즉시 중단·의료진 연락</i>"
            "</div>"
        ),
    },
    {
        "name": "FN",
        "patterns": [
            "(?i)febrile\\s*neutropenia",
            "호중구감소성\\s*발열",
            "호중구\\s*감소\\s*발열",
            "발열\\s*\\(anc\\s*<\\s*500\\)"
        ],
        "html": (
            "<div class='explain-chip'>"
            "<b>호중구감소성 발열(FN)</b> — 38.0–38.5℃ 해열제/경과, ≥38.5℃ <i>즉시 연락</i>, "
            "혈액배양·항생제 평가"
            "</div>"
        ),
    },
    {
        "name": "HEPATOX",
        "patterns": [
            "(?i)hepatotoxi(c|city)",
            "(?i)transaminitis",
            "간효소\\s*상승",
            "ast\\s*상승",
            "alt\\s*상승"
        ],
        "html": (
            "<div class='explain-chip'>"
            "<b>간효소 상승</b> — AST/ALT 추적, 황달·가려움·오심 시 연락, "
            "알코올·간독성 약물 피하기"
            "</div>"
        ),
    },
    {
        "name": "PROTEINURIA",
        "patterns": [
            "(?i)proteinuria",
            "단백뇨",
            "미세알부민",
            "요단백"
        ],
        "html": (
            "<div class='explain-chip'>"
            "<b>단백뇨</b> — 소변 단백 정기 추적, 부종/혈압 상승 시 연락, "
            "Anti‑VEGF 계열은 추가 주의"
            "</div>"
        ),
    },
    {
        "name": "MUCOSITIS",
        "patterns": [
            "(?i)mucositis",
            "(?i)stomatitis",
            "구내염",
            "구강\\s*궤양",
            "입통증"
        ],
        "html": (
            "<div class='explain-chip'>"
            "<b>구내염</b> — 처방 가글/통증조절, 산·매운 음식·자극 피하기, "
            "수분 유지·구강위생"
            "</div>"
        ),
    },
    {
        "name": "HFS",
        "patterns": [
            "(?i)hand[- ]?foot\\s*syndrome",
            "(?i)palmar[- ]?plantar\\s*erythrodysesthesia",
            "(?i)ppe",
            "손발증후군",
            "손발\\s*피부반응",
            "손발\\s*홍반",
            "손발\\s*통증",
            "손바닥\\s*발바닥\\s*통증"
        ],
        "html": (
            "<div class='explain-chip'>"
            "<b>손발증후군(HFS)</b> — 손·발 붉어짐/통증/벗겨짐 → 마찰·열 피하고, 보습·냉각. "
            "파임/수포·보행 어려우면 의사 상담"
            "</div>"
        ),
    },
    {
        "name": "RA_syndrome",
        "patterns": [
            "(?i)atra\\s*syndrome",
            "(?i)retinoic\\s*acid\\s*syndrome",
            "(?i)differentiation\\s*syndrome",
            "(?i)ras\\b",
            "RA\\s*증후군",
            "레티노산\\s*증후군",
            "레티노이드\\s*증후군",
            "분화\\s*증후군"
        ],
        "html": (
            "<div class='explain-chip'>"
            "<b>RA(ATRA) 증후군</b> — 숨참/부종/저혈압/발열 가능 → "
            "증상 시 즉시 연락, 의료진 지시 따라 스테로이드 가능"
            "</div>"
        ),
    },
    {
        "name": "QT",
        "patterns": ["(?-i)(?<![A-Za-z0-9])QT(?![A-Za-z0-9])", "(?-i)QT\s*연장", "(?i)torsades", "(?i)long\s*qt", "(?i)롱\s*qt"],
        "html": (
            "<div class='explain-chip'>"
            "<b>QT 연장</b> — ECG 추적, K≥4.0 / Mg≥2.0 유지, "
            "실신·심계항진·어지럼 시 즉시 연락"
            "</div>"
        ),
    },
    {
        "name": "Anthracycline",
        "patterns": [r"anthracycline", r"안트라사이클린", r"도?옥?소루비신", r"다우노루비신", r"이다루비신"],
        "html": (
            "<div class='explain-chip'>"
            "<b>안트라사이클린 심독성</b> — 누적용량 추적, 주기적 <i>Echo/LVEF</i> 권고"
            "</div>"
        ),
    },
    {
        "name": "VEGF",
        "patterns": [r"vegf", r"bevacizumab", r"ramucirumab", r"lenvatinib", r"sorafenib", r"단백뇨", r"고혈압", r"sunitinib",r"수니티닙", ],
        "html": (
            "<div class='explain-chip'>"
            "<b>Anti‑VEGF 계열</b> — 혈압·소변단백 정기 체크, 수술 전후 주의"
            "</div>"
        ),
    },
]

def render_keyword_explainers(st, text: str|None):
    """주어진 텍스트(text)에 포함된 키워드에만 반응해서 짧은 설명 배지를 출력.
    - 삭제/치환 없이, 매칭된 항목만 누적 출력.
    - 동일 규칙은 1회만 표시.
    - HTML 안전출력(unsafe_allow_html=True).
    - 과다 트리거 방지: URL/코드 블록 제거, 대소문자 민감도 패턴별 제어, 최대 4칩.
    """
    raw = (text or "")
    if not raw.strip():
        return

    # --- pre-clean: URL, 코드블록/인라인 코드 제거
    s = re.sub(r"`{3}.*?`{3}", " ", raw, flags=re.DOTALL)       # ``` code ```
    s = re.sub(r"`[^`]*`", " ", s)                              # `inline`
    s = re.sub(r"https?://\S+|www\.\S+", " ", s)                # URLs
    s = re.sub(r"\s+", " ", s).strip()

    matched_html: List[str] = []
    for rule in _KEYWORD_RULES:
        try:
            pats = rule.get("patterns", [])
            hit = False
            for ptn in pats:
                # inline flags support: (?i) case-insensitive, (?-i) sensitive
                flags = 0
                if isinstance(ptn, str) and ptn.startswith("(?i)"):
                    flags = re.IGNORECASE
                if re.search(ptn, s, flags=flags):
                    hit = True
                    break
            if hit:
                matched_html.append(rule.get("html", ""))
            if len(matched_html) >= 4:  # chip cap
                break
        except re.error:
            continue
    if not matched_html:
        return
    container = (
        "<div class='keyword-explainers'>"
        + "".join(matched_html)
        + "</div>"
    )
    st.markdown(container, unsafe_allow_html=True)

# 스타일(간단 배지) — 기존 style.css를 침범하지 않도록 클래스만 추가
_EXPLAINER_STYLE = """
<style>
.keyword-explainers{display:flex;flex-wrap:wrap;gap:.5rem;margin:.5rem 0;}
.keyword-explainers .explain-chip{
  padding:.35rem .6rem;border-radius:1rem;background:#f6f7fb;border:1px solid #e7e9f3;
  font-size:.85rem;line-height:1.2;
}
.keyword-explainers .explain-chip b{margin-right:.25rem}
</style>
"""

def ensure_keyword_explainer_style(st):
    """한 번만 삽입되더라도 안전. 호출부가 여러 곳이어도 중복 삽입 무해."""
    try:
        st.markdown(_EXPLAINER_STYLE, unsafe_allow_html=True)
    except Exception:
        pass
# --- [/PATCH] ---



# =============================
# Chemo summary example (영/한 + 부작용) — patch-safe helper
# =============================
def render_chemo_summary_example(st):
    """
    Render a compact example block under the 항암제 섹션:
    - Title: '## 항암제 요약 (영/한 + 부작용)'
    - Example: Sunitinib (수니티닙) with common/severe/call-warning cues
    This does not depend on app state and can be called anywhere.
    """
    st.markdown("## 항암제 요약 (영/한 + 부작용)")
    st.markdown(
        """
### Sunitinib (수니티닙)
- **일반**: 피로 — 자주 쉬어 주세요 · 설사 — 탈수 위험 → ORS · 구내염 — 입통증/궤양 → 자극 피하고 가글 · 손발증후군 — 손발 붉어짐·벗겨짐 → 보습 · 고혈압 — 혈압 체크·약 조절
- **중증**: QT 연장 — 실신·돌연사 위험 ↑ → ECG 추적 · 출혈 — 잇몸/코피·멍↑ → 외상 주의
- **연락 필요**: 흉통/실신/심한 어지러움

### 용어 풀이(요약)
- **QT 연장**: 실신·돌연사 위험 ↑ → ECG 추적.
- **손발증후군**: 손발 붉어짐·벗겨짐 → 보습·마찰 줄이기.
        """.strip()
    )

def render_terms_glossary_min(st, *, show_qt=True, show_hfs=True):
    """
    Very small glossary chips. Optional; can be used if you want separate chips
    right below the '항암제' block rather than a full example.
    """
    chips = []
    if show_qt:
        chips.append("**QT 연장**: 실신·돌연사 위험 ↑ → ECG 추적")
    if show_hfs:
        chips.append("**손발증후군**: 손발 붉어짐·벗겨짐 → 보습·마찰 줄이기")
    if chips:
        st.markdown("### 용어 풀이(요약)")
        st.write(" · ".join(chips))



def get_chemo_summary_example_md() -> str:
    """Return the chemo summary example as Markdown string (for .md report / PDF export)."""
    return (
        "## 항암제 요약 (영/한 + 부작용)\n\n"
        "### Sunitinib (수니티닙)\n"
        "- **일반**: 피로 — 자주 쉬어 주세요 · 설사 — 탈수 위험 → ORS · 구내염 — 입통증/궤양 → 자극 피하고 가글 · 손발증후군 — 손발 붉어짐·벗겨짐 → 보습 · 고혈압 — 혈압 체크·약 조절\n"
        "- **중증**: QT 연장 — 실신·돌연사 위험 ↑ → ECG 추적 · 출혈 — 잇몸/코피·멍↑ → 외상 주의\n"
        "- **연락 필요**: 흉통/실신/심한 어지러움\n\n"
        "### 용어 풀이(요약)\n"
        "- **QT 연장**: 실신·돌연사 위험 ↑ → ECG 추적.\n"
        "- **손발증후군**: 손발 붉어짐·벗겨짐 → 보습·마찰 줄이기.\n"
    )
