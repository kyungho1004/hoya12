
# -*- coding: utf-8 -*-
import streamlit as st
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))

def kst_now():
    return datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S KST")

def wkey(s: str) -> str:
    return f"k_{s}"

# --------------------
# Pediatric Caregiver Guide (collect notes for report)
# --------------------
def render_caregiver_notes_peds(
    *,
    stool,
    fever,
    persistent_vomit,
    oliguria,
    cough,
    nasal,
    eye,
    abd_pain,
    ear_pain,
    rash,
    hives,
    migraine,
    hfmd,
    constipation=False,
    anc_low=False,
):
    st.markdown("---")
    st.subheader("보호자 설명 (증상별 + 식이가이드)")

    notes = []  # collect for report

    def bullet(title, body):
        st.markdown(f"**{title}**")
        st.markdown(body.strip())
        # also collect first-level bullets (lines starting with - )
        for ln in body.strip().splitlines():
            ln = ln.strip()
            if ln.startswith("-"):
                notes.append(f"{title}: {ln[1:].strip()}")

    # 공통 식이가이드 — ANC 저하 시 최우선
    if anc_low:
        bullet(
            "🍽️ ANC 낮음(호중구 감소) 식이 가이드",
            """
- 생채소/날고기·생선 금지, 모든 음식은 충분히 익혀서 섭취
- 전자레인지 30초 이상 재가열(속까지 뜨겁게)
- 멸균/살균 식품 권장, 유통기한·보관 온도 준수
- 껍질 있는 과일은 주치의와 상담 후 섭취 결정(가능하면 껍질 제거)
- 조리 후 남은 음식은 2시간 이후 섭취 비권장(상온 방치 금지)
- 외식·뷔페·생야채 샐러드·회/초밥은 피하기
            """,
        )

    # 설사/장염
    if stool in ["3~4회", "5~6회", "7회 이상"]:
        bullet(
            "💧 설사/장염 의심",
            """
- 하루 3회 이상 묽은 변 → 장염 가능성
- 노란/초록 변, 거품 많고 냄새 심함 → 로타/노로바이러스 고려
- 대처: ORS·미음/쌀죽 등 수분·전해질 보충
- ORS 권장량(참고): 처음 1시간 10–20 mL/kg(5~10분마다 소량씩), 이후 설사 1회당 5–10 mL/kg 추가
- 즉시 진료: 피 섞인 변, 고열, 소변 거의 없음/축 늘어짐
            """,
        )
        bullet(
            "🍽️ 식이 가이드(설사 시)",
            """
- 기름진 음식·유가공 과다 섭취는 일시 피하기
- 바나나·쌀죽·사과퓨레·토스트(BRAT 변형)를 초기 24시간 참고
- 수분은 자주·소량씩, 찬 음료/탄산은 피하기
            """,
        )

    # 변비
    if constipation:
        bullet(
            "🚻 변비 대처",
            """
- 수분 보충: 체중 50–60 mL/kg/일 범위에서 충분히 마시기(연령·질환에 따라 조정)
- 규칙적인 좌변 시간: 식후 10–15분, 1일 1회 편안한 자세로 5–10분
- 운동: 가벼운 걷기/스트레칭
- 즉시/조속 진료: 심한 복통, 구토, 혈변, 체중 감소, 3–4일 이상 무배변 + 복부팽만
            """,
        )
        if not anc_low:
            bullet(
                "🍽️ 식이 가이드(변비)",
                """
- 수용성 식이섬유: 귀리, 보리, 사과·배(껍질), 키위, 자두·프룬
- 불용성 섬유: 고구마, 통곡물빵, 현미, 채소(익혀서 섭취 권장)
- 프룬/배 주스: 1–3 mL/kg/회, 하루 1–2회(과다 섭취 시 설사 주의)
- 칼슘제·철분제 복용 중이면 변비 악화 가능 → 의사와 용량/대체 논의
                """,
            )
        else:
            bullet(
                "🍽️ 식이 가이드(변비 + ANC 낮음)",
                """
- 생야채 대신 익힌 채소(당근찜, 브로콜리·호박 충분히 익혀서)
- 통곡물빵/귀리죽/오트밀 등 가열 조리된 곡류
- 과일은 껍질 제거 후 섭취, 프룬/배 주스는 끓여 식힌 물로 희석(1:1)하여 1–3 mL/kg/회
- 요구르트·발효유는 살균 제품만 선택
                """,
            )

    # 발열
    if fever in ["38~38.5", "38.5~39", "39 이상"]:
        bullet(
            "🌡️ 발열 대처",
            """
- 옷은 가볍게, 실내 시원하게(과도한 땀내기 X)
- 미온수 마사지는 잠깐만
- 해열제 간격: 아세트아미노펜 ≥4h, 이부프로펜 ≥6h
- 연락 기준(KST): ≥38.5℃면 주치의/병원에 전화 상담 권장
- 내원 기준(KST): ≥39.0℃이거나 무기력/경련/탈수/호흡곤란 동반 시 즉시 병원
            """,
        )

    if persistent_vomit:
        bullet(
            "🤢 구토 지속",
            """
- 10~15분마다 소량씩 수분(ORS/미지근한 물)
- 우유·기름진 음식 일시 회피
- 즉시 진료: 6시간 이상 물도 못 마심 / 초록·커피색 토물 / 혈토
            """,
        )

    if oliguria:
        bullet(
            "🚨 탈수 의심(소변량 급감)",
            """
- 입술 마름, 눈물 없음, 피부 탄력 저하, 축 늘어짐 동반 시 중등~중증 가능
- 즉시 진료: 6시간 이상 소변 없음(영아 4시간), 매우 축 늘어짐/무기력, 차고 얼룩덜룩한 피부
            """,
        )

    if cough in ["조금", "보통", "심함"] or nasal in ["진득", "누런"]:
        bullet(
            "🤧 기침·콧물(상기도감염)",
            """
- 생리식염수/흡인기로 콧물 제거, 수면 시 머리 높이기
- 즉시 진료: 숨차함/청색증/가슴함몰
            """,
        )

    if eye in ["노랑-농성", "양쪽"]:
        bullet(
            "👀 결막염 의심",
            """
- 손 위생 철저, 분비물은 깨끗이 닦기
- 양쪽·고열·눈 통증/빛 통증 → 진료 권장
            """,
        )

    if abd_pain in ["보통", "심함"]:
        bullet(
            "🤕 복통",
            """
- 쥐어짜는 통증·우측 아랫배·보행 시 악화면 충수염 고려
- 즉시 진료: 지속적 심한 통증, 국소 압통/반발통, 구토 동반
            """,
        )

    if ear_pain in ["보통", "심함"]:
        bullet(
            "👂 귀 통증",
            """
- 해열제·진통제 간격 준수, 코막힘 관리
- 즉시 진료: 고막 분비물, 안면 마비, 48시간 이상 지속
            """,
        )

    if rash or hives:
        bullet(
            "🌱 피부 발진/두드러기",
            """
- 가려움 완화: 시원한 찜질, 필요 시 항히스타민(지시에 따름)
- 즉시 진료: 입술/혀 붓기, 호흡곤란, 어지러움 → 아나필락시스 의심
            """,
        )

    if migraine:
        bullet(
            "🤯 두통/편두통",
            """
- 조용하고 어두운 곳에서 휴식, 수분 보충
- 즉시 진료: 번개치는 두통, 시야 이상/복시/암점, 신경학적 이상
            """,
        )

    if hfmd:
        bullet(
            "✋👣 수족구 의심(HFMD)",
            """
- 손·발·입 안 물집/궤양 + 발열
- 전염성: 손 씻기/식기 구분
- 탈수(소변 감소·축 늘어짐), 고열 >3일, 경련/무기력 → 진료 필요
            """,
        )

    st.info("❗ 즉시 병원 평가: 번개치는 두통 · 시야 이상/복시/암점 · 경련 · 의식저하 · 심한 목 통증 · 호흡곤란/입술부종")

    # Save for report
    st.session_state["peds_notes"] = notes
    return notes

# --------------------
# Special Tests
# --------------------
def render_special_tests():
    try:
        import importlib.util, sys, types, pathlib
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
# Chemo AE (store danger-summary for report)
# --------------------
GOOD = "🟢"; WARN = "🟡"; DANGER = "🚨"
def _b(txt: str) -> str:
    return txt.replace("{GOOD}", GOOD).replace("{WARN}", WARN).replace("{DANGER}", DANGER)

CHEMO_DB = {
    "ATRA (Tretinoin, Vesanoid) / 베사노이드": {
        "aka": ["ATRA", "Tretinoin", "Vesanoid", "베사노이드"],
        "effects": {"common": ["{WARN} 두통/피부건조/지질상승"]},
        "ra_syndrome": {
            "name": "RA-분화증후군",
            "window": "2일~2주",
            "symptoms": ["{DANGER} 발열", "{DANGER} 호흡곤란/저산소", "{DANGER} 저혈압", "{DANGER} 전신부종/체중 급증"],
        },
        "monitor": ["CBC, SpO₂, 체중/부종, 지질"],
        "when_to_call": ["😮‍💨 숨참/호흡곤란", "🧊 급격한 부종/체중 증가", "🌡️ 고열 지속"],
    },
    "Cytarabine (Ara-C) / 시타라빈(아라씨)": {
        "routes": {
            "IV/SC(표준용량)": ["{WARN} 발열/구토/설사/구내염", "{DANGER} 골수억제", "{WARN} 결막염"],
            "HDAC(고용량)": ["{DANGER} 소뇌독성(보행/말/글씨체 변화)", "{WARN} 각결막염 — 스테로이드 점안"],
        },
        "monitor": ["CBC, 간기능, 신경학적 징후"],
        "when_to_call": ["🚶 보행 흔들림/말 더듬", "👁️ 심한 충혈/통증", "🌡️ 발열"],
    },
    "MTX (Methotrexate) / 메토트렉세이트": {
        "effects": {"blood": ["{DANGER} 골수억제"], "renal": ["{DANGER} HD-MTX 신독성/결정뇨"], "pulmonary": ["{WARN} MTX 폐렴"]},
        "monitor": ["CBC, AST/ALT, Cr/eGFR", "HD-MTX: MTX 농도 + 류코보린 + 요알칼리화"],
        "when_to_call": ["🌡️ 발열", "💧 소변 급감/부종", "😮‍💨 호흡곤란"],
    },
    "Doxorubicin / 도소루비신(아드리아마이신)": {
        "effects": {"cardiac": ["{DANGER} 누적 심근병증/심부전"], "derm": ["{WARN} 혈관외유출 조직괴사"]},
        "monitor": ["심초음파(EF), ECG, CBC"],
        "when_to_call": ["💓 흉통/숨참/부종", "🛑 주사 부위 통증/발적"],
    },
    "Vincristine / 빈크리스틴": {
        "effects": {"neuro": ["{DANGER} 말초신경병증", "{WARN} 자율신경: 변비/장마비"]},
        "monitor": ["신경 증상, 변비/장음"],
        "when_to_call": ["🚶 보행 악화/넘어짐", "🚻 심한 변비/복부팽만"],
    },
    "Cisplatin / 시스플라틴": {
        "effects": {"renal": ["{DANGER} 신독성 — Cr↑, Mg/K↓"], "neuro": ["{WARN} 청력독성/말초신경병증"]},
        "monitor": ["Cr/eGFR, 전해질(Mg/K/Ca), 오디오그램"],
        "when_to_call": ["👂 이명/청력저하", "💧 소변 감소/부종"],
    },
    "6-MP (Mercaptopurine) / 6-머캅토퓨린": {
        "effects": {"blood": ["{DANGER} 골수억제"], "hepatic": ["{WARN} 간수치상승"], "rare": ["{WARN} 췌장염 드묾"]},
        "monitor": ["CBC, 간기능"],
        "when_to_call": ["🌡️ ≥38.5℃ 연락/≥39.0℃ 즉시 병원", "🩸 출혈·멍 지속", "💛 황달/소변 진해짐"],
    },
}

def render_chemo_adverse_effects(agents, route_map=None):
    st.markdown("## 항암제 부작용 가이드(확장판)")
    st.caption("KST 기준. 참고용이며 최종 판단은 의료진의 진료에 따릅니다.")

    summary = []  # for report

    if not agents:
        st.info("항암제를 선택하면 상세 부작용/모니터링 지침이 표시됩니다.")
        st.session_state['onco_warnings'] = []
        return

    for agent in agents:
        data = CHEMO_DB.get(agent, {})
        st.markdown(f"### {agent}")

        # UI rendering
        if "routes" in data:
            route = (route_map or {}).get(agent) or "IV/SC(표준용량)"
            st.markdown(f"**투여 경로/용량:** {route}")
            for line in data["routes"].get(route, []):
                st.markdown(f"- {_b(line)}")
                if "{DANGER}" in line or "소뇌독성" in line:
                    summary.append(f"{agent} [{route}]: " + _b(line).replace('🟡 ','').replace('🟢 ','').replace('🚨 ',''))
        else:
            effects = data.get("effects", {})
            for k, arr in effects.items():
                with st.expander(k):
                    for ln in arr:
                        st.markdown(f"- {_b(ln)}")
                        if "{DANGER}" in ln or "심근병증" in ln or "신독성" in ln or "폐렴" in ln:
                            summary.append(f"{agent}: " + _b(ln).replace('🟡 ','').replace('🟢 ','').replace('🚨 ',''))

        # RA-syndrome
        if agent.startswith("ATRA") and data.get("ra_syndrome"):
            ra = data["ra_syndrome"]
            with st.expander(f"⚠️ {ra['name']}"):
                st.markdown(f"- 발현 창: {ra['window']}")
                st.markdown("**증상 핵심:**")
                for s in ra["symptoms"]:
                    st.markdown(f"  - {_b(s)}")
                    if "{DANGER}" in s:
                        summary.append(f"ATRA/RA-증후군: " + _b(s).replace('🚨 ',''))

        # Monitoring/When to call
        for title, key in [("🧪 모니터링", "monitor"), ("🚩 즉시 연락/내원 기준", "when_to_call")]:
            if data.get(key):
                with st.expander(title):
                    for x in data[key]:
                        st.markdown(f"- {x}")

    # Save summary (de-duplicate and cap length)
    seen = set()
    uniq = []
    for s in summary:
        if s not in seen:
            seen.add(s)
            uniq.append(s)
    st.session_state["onco_warnings"] = uniq[:60]

    st.markdown("---")
    st.subheader("공통 요약")
    st.markdown("- 발열: **≥38.5℃ 연락**, **≥39.0℃ 또는 무기력/경련/호흡곤란/탈수 즉시 병원**")
    st.markdown("- 해열제 간격: 아세트아미노펜 **≥4h**, 이부프로펜 **≥6h** (24h 총량 초과 금지)")
    st.markdown("- **ANC<500/µL + 발열 = FN 의심** — 지체 없이 병원")

# --------------------
# Report Builder (now includes pediatric notes + chemo warnings)
# --------------------
def build_report():
    parts = []
    parts.append(f"# 피수치/가이드 요약\n- 생성시각: {kst_now()}\n- 제작/자문: Hoya/GPT")

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
st.set_page_config(page_title="피수치 가이드(리포트 보강판)", layout="wide")
st.title("피수치 가이드 — 리포트 보강판")
st.caption("한국시간 기준(KST).")

tabs = st.tabs(["🏠 홈", "🧒 소아 가이드", "🔬 특수검사", "💊 항암제 부작용", "📄 보고서"])

with tabs[1]:
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

    # ANC flag (optional labs)
    anc_low = False
    try:
        anc_val = float(st.session_state.get("labs_dict", {}).get("ANC"))
        anc_low = (anc_val < 500)
    except Exception:
        pass

    render_caregiver_notes_peds(
        stool=stool,
        fever=fever,
        persistent_vomit=persistent_vomit,
        oliguria=oliguria,
        cough=cough,
        nasal=nasal,
        eye=eye,
        abd_pain=abd_pain,
        ear_pain=ear_pain,
        rash=rash,
        hives=hives,
        migraine=migraine,
        hfmd=hfmd,
        constipation=constipation,
        anc_low=anc_low,
    )

with tabs[2]:
    render_special_tests()

with tabs[3]:
    st.subheader("항암제 선택")
    all_agents = list(CHEMO_DB.keys())
    selected_agents = st.multiselect("항암제", all_agents, key=wkey("agents"))
    st.session_state["selected_agents"] = selected_agents
    route_map = {}
    if "Cytarabine (Ara-C) / 시타라빈(아라씨)" in selected_agents:
        route_map["Cytarabine (Ara-C) / 시타라빈(아라씨)"] = st.selectbox(
            "아라씨 제형/용량", ["IV/SC(표준용량)", "HDAC(고용량)"], key=wkey("ara_route")
        )
    render_chemo_adverse_effects(selected_agents, route_map=route_map)

with tabs[4]:
    st.subheader("보고서")
    md = build_report()
    st.code(md, language="markdown")
    st.download_button("📥 보고서(.md) 다운로드", data=md.encode("utf-8"), file_name="report.md", mime="text/markdown")
