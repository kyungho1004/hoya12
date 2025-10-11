
# -*- coding: utf-8 -*-
import streamlit as st
from datetime import datetime, timezone, timedelta
from pathlib import Path
import importlib.util, sys

KST = timezone(timedelta(hours=9))

def kst_now():
    return datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S KST")

def wkey(s: str) -> str:
    return f"k_{s}"

# --------------------
# onco_map MULTI-SCAN loader (same as previous build)
# --------------------
def _candidate_onco_paths():
    cands = []
    try:
        here = Path(__file__).resolve().parent
        cands += [here / "onco_map.py"]
    except Exception:
        pass
    cands += [
        Path.cwd() / "onco_map.py",
        Path("onco_map.py"),
        Path("/mnt/data/onco_map.py"),
        Path("/mount/src/hoya12/bloodmap_app/onco_map.py"),
    ]
    seen = set(); out = []
    for p in cands:
        s = str(p.resolve()) if p.exists() else str(p)
        if s not in seen:
            seen.add(s); out.append(p)
    return out

def load_onco():
    last_err = None
    for p in _candidate_onco_paths():
        try:
            if not p.exists(): continue
            spec = importlib.util.spec_from_file_location("onco_map", str(p))
            mod = importlib.util.module_from_spec(spec)
            sys.modules["onco_map"] = mod
            spec.loader.exec_module(mod)  # type: ignore
            build = getattr(mod, "build_onco_map", None)
            disp = getattr(mod, "dx_display", None)
            if callable(build):
                omap = build()
                if isinstance(omap, dict) and omap:
                    return omap, disp, p
        except Exception as e:
            last_err = e
    return None, None, last_err

def onco_select_ui():
    st.subheader("암종류 선택 (onco_map 연동)")
    omap, dx_display, info = load_onco()
    if not isinstance(omap, dict) or not omap:
        st.error(f"onco_map.py에서 암 분류를 불러오지 못했습니다. {'에러: '+str(info) if info else ''}")
        g_manual = st.text_input("암 그룹(수동)", value=st.session_state.get("onco_group") or "")
        d_manual = st.text_input("진단(암종, 수동)", value=st.session_state.get("onco_dx") or "")
        if g_manual or d_manual:
            st.session_state["onco_group"] = g_manual.strip() or None
            st.session_state["onco_dx"] = d_manual.strip() or None
            st.success("수동 입력값을 사용합니다.")
        return st.session_state.get("onco_group"), st.session_state.get("onco_dx")

    st.caption(f"onco_map 연결: {info}")
    groups = sorted(list(omap.keys()))
    group = st.selectbox("암 그룹", groups, key=wkey("onco_group"))
    dx_keys = sorted(list(omap.get(group, {}).keys()))
    labels = [(dx_display(group, dx) if dx_display else f"{group} - {dx}") for dx in dx_keys]
    if dx_keys:
        default_dx = st.session_state.get("onco_dx")
        idx = dx_keys.index(default_dx) if default_dx in dx_keys else 0
        idx = st.selectbox("진단(암종)", list(range(len(labels))), index=idx, format_func=lambda i: labels[i], key=wkey("onco_dx_idx"))
        dx = dx_keys[idx]
        st.session_state["onco_group"] = group
        st.session_state["onco_dx"] = dx
        dmap = omap.get(group, {}).get(dx, {})
        recs = []
        for sec in ["chemo","targeted","maintenance","support","abx"]:
            arr = dmap.get(sec, [])
            if arr:
                recs.append(f"{sec}: " + ", ".join(arr[:12]))
        if recs:
            st.markdown("#### onco_map 권장 약물")
            for r in recs:
                st.write("- " + r)
    else:
        st.warning("해당 그룹에 진단이 없습니다.")
        st.session_state["onco_group"] = group
        st.session_state["onco_dx"] = None
    return st.session_state.get("onco_group"), st.session_state.get("onco_dx")

# --------------------
# Labs
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
    if labs:
        st.markdown("#### 입력 요약")
        for k, v in labs.items():
            if str(v).strip() != "":
                st.markdown(f"- **{k}**: {v}")
    return labs

# --------------------
# Blood pressure
# --------------------
def classify_bp(sbp, dbp):
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
# Pediatric caregiver guide
# --------------------
def render_caregiver_notes_peds(
    *, stool, fever, persistent_vomit, oliguria, cough, nasal, eye, abd_pain, ear_pain, rash, hives, migraine, hfmd, constipation=False, anc_low=None,
):
    if anc_low is None:
        try:
            anc_val = float(st.session_state.get("labs_dict", {}).get("ANC"))
            anc_low = anc_val < 500
        except Exception:
            anc_low = False

    st.markdown("---")
    st.subheader("보호자 설명 (증상별 + 식이가이드)")

    def bullet(title, body):
        st.markdown(f"**{title}**")
        st.markdown(body.strip())

    if anc_low:
        bullet("🍽️ ANC 낮음(호중구 감소) 식이가이드", """
- **생야채/날고기·생선 금지**, 모든 음식은 **충분히 익혀서**
- **멸균/살균 제품** 위주 섭취, 유통기한·보관 온도 준수
- 과일은 **껍질 제거 후** 섭취(가능하면 데친 뒤 식혀서)
- **조리 후 2시간이 지나면 폐기**, **뷔페/회/초밥/생채소 샐러드 금지**
""")

    if stool in ["3~4회", "5~6회", "7회 이상"]:
        bullet("💧 설사/장염 의심", """
- 하루 **3회 이상 묽은 변**이면 장염 가능성, **노란/초록·거품 많은 변**이면 로타/노로 의심
- **ORS**: 처음 1시간 **10–20 mL/kg**(5~10분마다 소량), 이후 설사 1회당 **5–10 mL/kg**
- **즉시 진료**: 피 섞인 변, **고열 ≥39℃**, **소변 거의 없음/축 늘어짐**
""")
        bullet("🍽️ 식이가이드(설사)", """
- 초기 24시간: **바나나·쌀죽·사과퓨레·토스트(BRAT 변형)** 참고
- **자주·소량**의 미지근한 수분, 탄산/아이스는 피하기
""")

    if constipation:
        bullet("🚻 변비 대처", """
- **수분**: 대략 체중 **50–60 mL/kg/일**(질환/의사 지시에 맞춰 조정)
- **좌변 습관**: 식후 10–15분, 하루 1회 **편안한 자세**로 5–10분
- **운동**: 가벼운 걷기·스트레칭
- **즉시/조속 진료**: 심한 복통, **구토**, **혈변**, **3–4일 무배변 + 복부팽만**
""")
        if not anc_low:
            bullet("🍽️ 식이가이드(변비)", """
- **수용성 섬유**: 귀리·보리·사과/배(껍질), 키위, 자두·프룬
- **불용성 섬유**: 고구마, 통곡물빵, 현미, 채소(가능하면 익혀서)
- **프룬/배 주스**: **1–3 mL/kg/회**, 하루 1–2회(과하면 설사)
""")
        else:
            bullet("🍽️ 식이가이드(변비 + ANC 낮음)", """
- 생야채 대신 **익힌 채소**(당근찜·브로콜리·호박)
- 통곡물빵/오트밀/귀리죽 등 **가열 조리된 곡류**
- 과일은 **껍질 제거** 후 섭취, 프룬/배 주스는 **끓여 식힌 물 1:1 희석**
""")

    if fever in ["38~38.5", "38.5~39", "39 이상"]:
        bullet("🌡️ 발열 대처", """
- 옷은 가볍게, 실내 시원하게(과도한 땀내기 X)
- **해열제 간격**: 아세트아미노펜 ≥4h, 이부프로펜 ≥6h
- **연락 기준(KST)**: **≥38.5℃** 연락, **내원 기준**: **≥39.0℃** 또는 무기력/경련/탈수/호흡곤란
""")

    if persistent_vomit:
        bullet("🤢 구토 지속", """
- 10~15분마다 **소량씩 수분**(ORS/미지근한 물)
- **즉시 진료**: 6시간 이상 물도 못 마심 / 초록·커피색 토물 / 혈토
""")

    if oliguria:
        bullet("🚨 탈수 의심(소변량 급감)", """
- 입술 마름·눈물 없음·피부 탄력 저하·축 늘어짐 동반 시 **중등~중증**
- **즉시 진료**: **6h 이상 무뇨(영아 4h)**, 매우 축 늘어짐/무기력
""")

    if cough in ["조금", "보통", "심함"] or nasal in ["진득", "누런"]:
        bullet("🤧 기침·콧물(상기도)", """
- **생리식염수/흡인기**로 콧물 제거, 수면 시 **머리 높이기**
- **즉시 진료**: 숨차함/청색증/가슴함몰
""")

    if eye in ["노랑-농성", "양쪽"]:
        bullet("👀 결막염 의심", """
- 손 위생 철저, 분비물은 깨끗이 닦기
- **양쪽·고열·눈 통증/빛 통증** → 진료 권장
""")

    if abd_pain:
        bullet("🤕 복통", """
- **쥐어짜는 통증/우하복부 통증/보행 시 악화**면 충수염 고려
- **즉시 진료**: 지속적 심한 통증·국소 압통/반발통·구토 동반
""")

    if ear_pain:
        bullet("👂 귀 통증", """
- 해열제·진통제 간격 준수, 코막힘 관리
- **즉시 진료**: 고막 분비물, 안면 마비, 48h 이상 지속
""")

    if rash or hives:
        bullet("🌱 피부 발진/두드러기", """
- 가려움 완화: 시원한 찜질, 필요 시 항히스타민(지시에 따름)
- **즉시 진료**: **입술/혀 붓기, 호흡곤란, 어지러움** → 아나필락시스 의심
""")

    if migraine:
        bullet("🤯 두통/편두통", """
- 조용하고 어두운 곳에서 휴식, 수분 보충
- **즉시 진료**: **번개치는 두통**, **시야 이상/복시/암점**, **신경학적 이상**
""")

    if hfmd:
        bullet("✋👣 수족구 의심(HFMD)", """
- **손·발·입 안** 물집/궤양 + 발열
- 전염성: 손 씻기/식기 구분
- **탈수(소변 감소·축 늘어짐)**, **고열 >3일**, **경련/무기력** → 진료 필요
""")

# --------------------
# SPECIAL TESTS — robust loader
# --------------------
def _candidate_special_paths():
    cands = []
    try:
        here = Path(__file__).resolve().parent
        cands += [here / "special_tests.py"]
    except Exception:
        pass
    cands += [
        Path.cwd() / "special_tests.py",
        Path("special_tests.py"),
        Path("/mnt/data/special_tests.py"),
        Path("/mount/src/hoya12/bloodmap_app/special_tests.py"),
    ]
    seen = set(); out = []
    for p in cands:
        s = str(p.resolve()) if p.exists() else str(p)
        if s not in seen:
            seen.add(s); out.append(p)
    return out

def _load_special_module():
    last_err = None
    for p in _candidate_special_paths():
        try:
            if not p.exists(): continue
            spec = importlib.util.spec_from_file_location("special_tests", str(p))
            mod = importlib.util.module_from_spec(spec)
            sys.modules["special_tests"] = mod
            spec.loader.exec_module(mod)  # type: ignore
            return mod, p
        except Exception as e:
            last_err = e
    return None, last_err

def _call_special_ui(mod):
    # 허용되는 함수 이름들
    for fn in ["special_tests_ui", "render_special_tests_ui", "build_special_tests_ui", "ui"]:
        f = getattr(mod, fn, None)
        if callable(f):
            return f()
    # 딕셔너리/리스트를 반환하는 정적 데이터도 허용
    for name in ["SPECIAL_TESTS", "SPECIAL_RESULTS", "DATA"]:
        if hasattr(mod, name):
            data = getattr(mod, name)
            if isinstance(data, (list, tuple)):
                return list(data)
            if isinstance(data, dict):
                # dict → "key: value" 라인 리스트로 변환
                out = []
                for k, v in data.items():
                    if isinstance(v, (list, tuple)):
                        for x in v:
                            out.append(f"{k}: {x}")
                    else:
                        out.append(f"{k}: {v}")
                return out
    return None

def render_special_tests():
    try:
        mod, info = _load_special_module()
        if not mod:
            st.error(f"특수검사 모듈을 찾지 못했습니다. {'에러: '+str(info) if info else ''}")
            return
        res = _call_special_ui(mod)
        if res is None:
            st.error("특수검사 UI 함수를 찾지 못했습니다. (허용: special_tests_ui/render_special_tests_ui/build_special_tests_ui/ui 또는 SPECIAL_TESTS 자료구조)")
            return
        # 결과 렌더 및 세션 저장
        if isinstance(res, (list, tuple)):
            lines = [str(x) for x in res]
        else:
            # 함수가 Streamlit 내부 렌더만 하고 리스트를 반환 안 할 수 있음
            lines = getattr(mod, "LATEST_LINES", [])
            if not isinstance(lines, list):
                lines = []
        st.session_state["special_interpretations"] = lines
        if lines:
            st.markdown("### 특수검사 해석")
            for ln in lines:
                st.markdown(f"- {ln}")
        st.caption(f"special_tests 연결: {info}")
    except Exception as e:
        st.error(f"특수검사 로드 오류: {e}")

# --------------------
# Chemo adverse effects (concise)
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
    st.session_state["onco_warnings"] = list(dict.fromkeys(summary))[:60]

# --------------------
# Report
# --------------------
def build_report():
    parts = []
    parts.append(f"# 피수치/가이드 요약\n- 생성시각: {kst_now()}\n- 제작/자문: Hoya/GPT")

    labs = st.session_state.get("labs_dict", {})
    if labs and any(str(v).strip() for v in labs.values()):
        parts.append("## 피수치")
        for k, v in labs.items():
            if str(v).strip() != "":
                parts.append(f"- {k}: {v}")

    bp = st.session_state.get("bp_summary")
    if bp:
        parts.append("## 혈압 분류(압종분류)")
        parts.append(f"- {bp}")

    g = st.session_state.get("onco_group")
    d = st.session_state.get("onco_dx")
    if g or d:
        parts.append("## 암종 선택")
        parts.append(f"- 그룹: {g or '-'} / 진단: {d or '-'}")

    peds = st.session_state.get("peds_notes", [])
    if peds:
        parts.append("## 소아 보호자가이드")
        parts.extend([f"- {x}" for x in peds])

    lines = st.session_state.get("special_interpretations", [])
    if lines:
        parts.append("## 특수검사 해석")
        parts.extend([f"- {ln}" for ln in lines])

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
st.set_page_config(page_title="피수치 가이드(special_tests 고정판)", layout="wide")
st.title("피수치 가이드 — special_tests 연동 강화판")
st.caption("암종 선택/피수치/소아가이드/특수검사/항암제/보고서 통합. special_tests 경로·함수명 자동 인식.")

tabs = st.tabs(["🏠 홈", "🧪 피수치 입력", "🩺 혈압체크", "🧒 소아 가이드", "🔬 특수검사", "🧬 암종 선택", "💊 항암제", "📄 보고서"])

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
    render_caregiver_notes_peds(
        stool=stool, fever=fever, persistent_vomit=persistent_vomit, oliguria=oliguria,
        cough=cough, nasal=nasal, eye=eye, abd_pain=abd_pain, ear_pain=ear_pain,
        rash=rash, hives=hives, migraine=migraine, hfmd=hfmd,
        constipation=constipation,
    )

with tabs[4]:
    render_special_tests()

with tabs[5]:
    onco_select_ui()

with tabs[6]:
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

with tabs[7]:
    st.subheader("보고서")
    md = build_report()
    st.code(md, language="markdown")
    st.download_button("📥 보고서(.md) 다운로드", data=md.encode("utf-8"), file_name="report.md", mime="text/markdown")
