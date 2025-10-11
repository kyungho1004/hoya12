
# -*- coding: utf-8 -*-
import streamlit as st
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))

def kst_now():
    return datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S KST")

def wkey(s: str) -> str:
    return f"k_{s}"

# --------------------
# 피수치 입력창 (Labs)
# --------------------
LAB_FIELDS = [
    ("WBC", "x10^3/µL"),
    ("ANC", "/µL"),
    ("Hb", "g/dL"),
    ("Plt", "x10^3/µL"),
    ("Creatinine", "mg/dL"),
    ("eGFR", "mL/min/1.73m²"),
    ("AST", "U/L"),
    ("ALT", "U/L"),
    ("T.bil", "mg/dL"),
    ("Na", "mmol/L"),
    ("K", "mmol/L"),
    ("Cl", "mmol/L"),
    ("CRP", "mg/L"),
    ("ESR", "mm/hr"),
    ("Ferritin", "ng/mL"),
    ("Procalcitonin", "ng/mL"),
    ("UPCR", "mg/g"),
    ("ACR", "mg/g"),
]

def labs_input_ui():
    st.subheader("피수치 입력")
    labs = st.session_state.get("labs_dict", {}).copy()
    cols = st.columns(3)
    for i, (name, unit) in enumerate(LAB_FIELDS):
        with cols[i % 3]:
            val = st.text_input(f"{name} ({unit})", value=str(labs.get(name, "")), key=wkey(f"lab_{name}"))
            labs[name] = val.strip()
    st.session_state["labs_dict"] = labs
    # 결과 미리보기
    if labs:
        st.markdown("#### 입력 요약")
        for k, v in labs.items():
            if str(v).strip() != "":
                st.markdown(f"- **{k}**: {v}")
    return labs

# --------------------
# 압종분류 (혈압 분류: ACC/AHA 2017 기준 단순화)
# --------------------
def classify_bp(sbp, dbp):
    # Returns (category, note)
    if sbp is None or dbp is None:
        return ("측정값 없음", "SBP/DBP를 입력하세요.")
    if sbp >= 180 or dbp >= 120:
        return ("🚨 고혈압 위기", "즉시 의료기관 평가 권장")
    if sbp >= 140 or dbp >= 90:
        return ("2기 고혈압", "생활습관 + 약물치료 고려(의료진)")
    if 130 <= sbp <= 139 or 80 <= dbp <= 89:
        return ("1기 고혈압", "생활습관 교정 + 위험평가")
    if 120 <= sbp <= 129 and dbp < 80:
        return ("주의혈압(상승)", "염분 제한/운동/체중조절 권장")
    if sbp < 120 and dbp < 80:
        return ("정상혈압", "유지")
    return ("분류불가", "값을 확인하세요.")

def bp_ui():
    st.subheader("혈압 측정 및 분류(압종분류)")
    c1, c2, c3 = st.columns(3)
    with c1:
        sbp = st.text_input("수축기 혈압 SBP (mmHg)", key=wkey("sbp"))
    with c2:
        dbp = st.text_input("이완기 혈압 DBP (mmHg)", key=wkey("dbp"))
    with c3:
        st.caption("기준: ACC/AHA 2017 (단순화)")
    try:
        sbp_val = float(sbp) if sbp else None
        dbp_val = float(dbp) if dbp else None
    except Exception:
        sbp_val = None; dbp_val = None
    cat, note = classify_bp(sbp_val, dbp_val)
    st.info(f"분류: **{cat}** — {note}")
    st.session_state["bp_summary"] = f"{cat} (SBP {sbp or '?'} / DBP {dbp or '?'}) — {note}"
    return cat, note

# --------------------
# Pediatric Guide (shortened: returns notes for report)
# --------------------
def render_caregiver_notes_peds(
    *, stool, fever, persistent_vomit, oliguria, cough, nasal, eye, abd_pain, ear_pain, rash, hives, migraine, hfmd, constipation=False, anc_low=False,
):
    st.markdown("---")
    st.subheader("보호자 설명 (증상별 + 식이가이드)")
    notes = []

    def bullet(title, body):
        st.markdown(f"**{title}**")
        st.markdown(body.strip())
        for ln in body.strip().splitlines():
            ln = ln.strip()
            if ln.startswith("-"):
                notes.append(f"{title}: {ln[1:].strip()}")

    if anc_low:
        bullet("🍽️ ANC 낮음 식이가이드", dedent("""- 생채소/날고기 금지, 모든 음식은 충분히 익혀 섭취
- 멸균 식품 권장, 남은 음식 2시간 이후 폐기
"""))

    if stool in ["3~4회", "5~6회", "7회 이상"]:
        bullet("💧 설사/장염", dedent("""- ORS 1시간 10–20 mL/kg, 이후 1회당 5–10 mL/kg 추가
- 피 섞인 변·고열·소변감소 시 즉시 진료
"""))

    if constipation:
        bullet("🚻 변비", dedent("""- 수분 50–60 mL/kg/일, 좌변 훈련
- 심한 복통/혈변/팽만 + 무배변 3–4일 → 진료
"""))

    if fever in ["38~38.5", "38.5~39", "39 이상"]:
        bullet("🌡️ 발열", dedent("""- 해열제 간격: APAP ≥4h / IBU ≥6h
- ≥38.5℃ 연락, ≥39.0℃ 또는 무기력/경련/호흡곤란/탈수 즉시 병원
"""))

    if persistent_vomit:
        bullet("🤢 구토 지속", dedent("""- 10~15분마다 소량씩 수분, 6h 이상 물도 못 마시면 진료
"""))

    if oliguria:
        bullet("🚨 탈수 의심", dedent("""- 6h 이상 무뇨(영아 4h), 축 늘어짐/차가운 피부 → 즉시 진료
"""))

    if cough in ["조금", "보통", "심함"] or nasal in ["진득", "누런"]:
        bullet("🤧 기침·콧물", dedent("""- 생리식염수로 콧물 제거, 숨차면 즉시 진료
"""))

    if eye in ["노랑-농성", "양쪽"]:
        bullet("👀 결막염", dedent("""- 분비물 닦기·손 위생, 통증/빛통증/고열은 진료
"""))

    if abd_pain in ["보통", "심함"]:
        bullet("🤕 복통", dedent("""- 우하복부 통증·보행시 악화면 충수염 고려 → 진료
"""))

    if ear_pain in ["보통", "심함"]:
        bullet("👂 귀 통증", dedent("""- 진통제 간격 준수, 분비물/안면마비/48h 지속 시 진료
"""))

    if rash or hives:
        bullet("🌱 발진/두드러기", dedent("""- 입술/혀 붓기·호흡곤란·어지러움은 아나필락시스 의심 → 즉시 진료
"""))

    if migraine:
        bullet("🤯 두통", dedent("""- 번개치는 두통·시야 이상/신경학 이상 즉시 진료
"""))

    if hfmd:
        bullet("✋👣 수족구", dedent("""- 손씻기/식기분리, 탈수·고열>3일·경련/무기력 → 진료
"""))

    st.session_state["peds_notes"] = notes
    return notes

# --------------------
# Special Tests (external)
# --------------------
def render_special_tests():
    try:
        import importlib.util, sys, pathlib
        p = pathlib.Path("/mnt/data/special_tests.py")
        if p.exists():
            spec = importlib.util.spec_from_file_location("special_tests", str(p))
            mod = importlib.util.module_from_spec(spec)
            sys.modules["special_tests"] = mod
            spec.loader.exec_module(mod)  # type: ignore
            if hasattr(mod, "special_tests_ui"):
                lines = mod.special_tests_ui()
                st.session_state["special_interpretations"] = lines
                if lines:
                    st.markdown("### 해석 라인")
                    for ln in lines:
                        st.markdown(f"- {ln}")
                return
        st.warning("특수검사 모듈을 찾지 못했거나 UI 함수가 없습니다.")
    except Exception as e:
        st.error(f"특수검사 로드 오류: {e}")

# --------------------
# Chemo AE (short; danger summary to report)
# --------------------
GOOD="🟢"; WARN="🟡"; DANGER="🚨"
def _b(txt: str) -> str:
    return txt.replace("{GOOD}", GOOD).replace("{WARN}", WARN).replace("{DANGER}", DANGER)

CHEMO_DB = {
    "ATRA (Tretinoin, Vesanoid) / 베사노이드": {
        "effects": {"common": ["{WARN} 두통/피부건조/지질상승"]},
        "ra_syndrome": {"name":"RA-분화증후군","symptoms":["{DANGER} 발열","{DANGER} 호흡곤란/저산소","{DANGER} 저혈압","{DANGER} 전신부종/체중 급증"]},
        "monitor": ["CBC, SpO₂, 체중/부종, 지질"],
    },
    "Cytarabine (Ara-C) / 시타라빈(아라씨)": {
        "routes": {"IV/SC(표준용량)":["{WARN} 발열/구토/설사/구내염","{DANGER} 골수억제","{WARN} 결막염"],
                   "HDAC(고용량)":["{DANGER} 소뇌독성(보행/말/글씨체 변화)","{WARN} 각결막염 — 스테로이드 점안"]},
        "monitor": ["CBC, 간기능, 신경학적 징후"],
    },
    "MTX (Methotrexate) / 메토트렉세이트": {
        "effects":{"blood":["{DANGER} 골수억제"],"renal":["{DANGER} HD-MTX 신독성/결정뇨"],"pulmonary":["{WARN} MTX 폐렴"]},
        "monitor":["CBC, AST/ALT, Cr/eGFR", "HD-MTX: MTX 농도 + 류코보린 + 요알칼리화"],
    },
}

def render_chemo_adverse_effects(agents, route_map=None):
    st.subheader("항암제 부작용(요약)")
    summary = []
    if not agents:
        st.info("항암제를 선택하면 상세 부작용/모니터링 지침이 표시됩니다.")
        st.session_state['onco_warnings'] = []
        return
    for agent in agents:
        data = CHEMO_DB.get(agent, {})
        st.markdown(f"### {agent}")
        if "routes" in data:
            route = (route_map or {}).get(agent) or "IV/SC(표준용량)"
            st.markdown(f"**투여 경로/용량:** {route}")
            for line in data["routes"].get(route, []):
                st.markdown(f"- {_b(line)}")
                if "{DANGER}" in line or "소뇌독성" in line:
                    summary.append(f"{agent} [{route}]: " + _b(line).replace('🟡 ','').replace('🟢 ','').replace('🚨 ',''))
        else:
            effects = data.get("effects", {})
            for section, arr in effects.items():
                with st.expander(section):
                    for ln in arr:
                        st.markdown(f"- {_b(ln)}")
                        if "{DANGER}" in ln:
                            summary.append(f"{agent}: " + _b(ln).replace('🟡 ','').replace('🟢 ','').replace('🚨 ',''))
        if agent.startswith("ATRA") and data.get("ra_syndrome"):
            rs = data["ra_syndrome"]
            with st.expander("⚠️ RA-분화증후군"):
                for s in rs["symptoms"]:
                    st.markdown(f"- {_b(s)}")
                    if "{DANGER}" in s:
                        summary.append(f"ATRA/RA-증후군: " + _b(s).replace('🚨 ',''))
    # Save summary
    st.session_state["onco_warnings"] = list(dict.fromkeys(summary))[:60]

# --------------------
# Report Builder
# --------------------
def build_report():
    parts = []
    parts.append(f"# 피수치/가이드 요약\n- 생성시각: {kst_now()}\n- 제작/자문: Hoya/GPT")

    # Labs
    labs = st.session_state.get("labs_dict", {})
    if labs and any(str(v).strip() for v in labs.values()):
        parts.append("## 피수치")
        for k, v in labs.items():
            if str(v).strip() != "":
                parts.append(f"- {k}: {v}")

    # BP
    bp = st.session_state.get("bp_summary")
    if bp:
        parts.append("## 혈압 분류(압종분류)")
        parts.append(f"- {bp}")

    # Pediatric notes
    peds = st.session_state.get("peds_notes", [])
    if peds:
        parts.append("## 소아 보호자가이드")
        parts.extend([f"- {x}" for x in peds])

    # Special tests
    lines = st.session_state.get("special_interpretations", [])
    if lines:
        parts.append("## 특수검사 해석")
        parts.extend([f"- {ln}" for ln in lines])

    # Chemo warnings
    agents = st.session_state.get("selected_agents", [])
    warns = st.session_state.get("onco_warnings", [])
    if agents:
        parts.append("## 항암제(선택)")
        parts.extend([f"- {a}" for a in agents])
    if warns:
        parts.append("## 항암제 부작용 요약(위험)")
        parts.extend([f"- {w}" for w in warns])

    if not any(sec.startswith("##") for sec in parts[1:]):
        parts.append("## 입력된 데이터가 없어 기본 안내만 표시됩니다.")
    return "\n\n".join(parts)

# --------------------
# App Layout
# --------------------
st.set_page_config(page_title="피수치 가이드(완전 복구판)", layout="wide")
st.title("피수치 가이드 — 완전 복구판")
st.caption("한국시간 기준(KST). 특수검사/소아가이드/항암제/보고서 전부 통합.")

tabs = st.tabs(["🏠 홈", "🧪 피수치 입력", "🩺 압종분류", "🧒 소아 가이드", "🔬 특수검사", "💊 항암제", "📄 보고서"])

with tabs[1]:
    labs_input_ui()

with tabs[2]:
    bp_ui()

with tabs[3]:
    st.subheader("증상 입력")
    col1, col2, col3 = st.columns(3)
    with col1:
        stool = st.selectbox("설사 횟수", ["0~2회", "3~4회", "5~6회", "7회 이상"], key=wkey("stool"))
        fever = st.selectbox("최고 체온", ["37.x", "38~38.5", "38.5~39", "39 이상"], key=wkey("fever"))
        constipation = st.checkbox("변비", key=wkey("constipation"))
    with col2:
        persistent_vomit = st.checkbox("지속 구토", key=wkey("vomit"))
        oliguria = st.checkbox("소변량 급감", key=wkey("oligo"))
        cough = st.selectbox("기침 정도", ["없음", "조금", "보통", "심함"], key=wkey("cough"))
        nasal = st.selectbox("콧물 상태", ["맑음", "진득", "누런"], key=wkey("nasal"))
    with col3:
        eye = st.selectbox("눈 분비물", ["없음", "맑음", "노랑-농성", "양쪽"], key=wkey("eye"))
        abd_pain = st.selectbox("복통", ["없음", "조금", "보통", "심함"], key=wkey("abd"))
        ear_pain = st.selectbox("귀 통증", ["없음", "조금", "보통", "심함"], key=wkey("ear"))
        rash = st.checkbox("피부 발진", key=wkey("rash"))
        hives = st.checkbox("두드러기", key=wkey("hives"))
        migraine = st.checkbox("두통/편두통", key=wkey("migraine"))
        hfmd = st.checkbox("수족구 의심", key=wkey("hfmd"))
    # ANC flag (optional)
    anc_low = False
    try:
        anc_val = float(st.session_state.get("labs_dict", {}).get("ANC"))
        anc_low = (anc_val < 500)
    except Exception:
        pass
    render_caregiver_notes_peds(
        stool=stool, fever=fever, persistent_vomit=persistent_vomit, oliguria=oliguria,
        cough=cough, nasal=nasal, eye=eye, abd_pain=abd_pain, ear_pain=ear_pain,
        rash=rash, hives=hives, migraine=migraine, hfmd=hfmd,
        constipation=constipation, anc_low=anc_low,
    )

with tabs[4]:
    render_special_tests()

with tabs[5]:
    all_agents = list(CHEMO_DB.keys())
    selected_agents = st.multiselect("항암제", all_agents, key=wkey("agents"))
    st.session_state["selected_agents"] = selected_agents
    route_map = {}
    if "Cytarabine (Ara-C) / 시타라빈(아라씨)" in selected_agents:
        route_map["Cytarabine (Ara-C) / 시타라빈(아라씨)"] = st.selectbox(
            "아라씨 제형/용량", ["IV/SC(표준용량)", "HDAC(고용량)"], key=wkey("ara_route")
        )
    render_chemo_adverse_effects(selected_agents, route_map=route_map)

with tabs[6]:
    st.subheader("보고서")
    md = build_report()
    st.code(md, language="markdown")
    st.download_button("📥 보고서(.md) 다운로드", data=md.encode("utf-8"), file_name="report.md", mime="text/markdown")
