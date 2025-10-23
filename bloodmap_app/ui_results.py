
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
        "name": "QT",
        "patterns": [r"\bqt\b", r"qt\s*연장", r"torsades", r"롱\s*qt", r"long\s*qt"],
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
        "patterns": [r"vegf", r"bevacizumab", r"ramucirumab", r"lenvatinib", r"sorafenib", r"단백뇨", r"고혈압"],
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
    """
    s = (text or "").lower()
    if not s.strip():
        return
    matched_html: List[str] = []
    for rule in _KEYWORD_RULES:
        try:
            pats = rule.get("patterns", [])
            if any(re.search(p, s) for p in pats):
                matched_html.append(rule.get("html", ""))
        except re.error:
            # 정규식 오류가 있더라도 다른 규칙은 계속
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
