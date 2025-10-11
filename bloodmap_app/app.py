
# -*- coding: utf-8 -*-
# ---- Safe guards for autosave/restore (injected) ----
try:
    autosave_state
except NameError:
    def autosave_state():
        return None
try:
    restore_state
except NameError:
    def restore_state():
        return None

import streamlit as st
from datetime import datetime, timezone, timedelta
from pathlib import Path
import importlib.util, sys, csv, json

KST = timezone(timedelta(hours=9))
def kst_now() -> str:
    return datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S KST")
def wkey(s: str) -> str:
    return f"k_{s}"

CURRENT_USERS = 140
FEED_PATH = Path("/mnt/data/feedback.csv")
AUTOSAVE_PATH = Path("/mnt/data/autosave.json")

# ---------- Autosave / Restore (real implementations) ----------
ESSENTIAL_KEYS = [
    "labs_dict","bp_summary","onco_group","onco_dx","peds_notes",
    "special_interpretations","selected_agents","onco_warnings",
    "show_peds_on_home"
]
def restore_state():
    try:
        if AUTOSAVE_PATH.exists():
            data = json.loads(AUTOSAVE_PATH.read_text(encoding="utf-8"))
            for k,v in data.items():
                st.session_state[k] = v
            st.caption(f"자동 복원 완료: {AUTOSAVE_PATH}")
    except Exception as e:
        st.warning(f"자동 복원 실패: {e}")

def autosave_state():
    try:
        data = {k: st.session_state.get(k) for k in ESSENTIAL_KEYS}
        AUTOSAVE_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        st.warning(f"자동 저장 실패: {e}")

# ---------- onco_map loader ----------
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
    out, seen = [], set()
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
            omap = None
            if callable(build): omap = build()
            elif hasattr(mod, "OM"): omap = getattr(mod, "OM")
            elif hasattr(mod, "ONCO_MAP"): omap = getattr(mod, "ONCO_MAP")
            if isinstance(omap, dict) and omap:
                return omap, disp, p
        except Exception as e:
            last_err = e
    return None, None, last_err

def onco_select_ui():
    st.header("🧬 암종 선택")
    omap, dx_display, info = load_onco()
    if not isinstance(omap, dict) or not omap:
        st.error(f"onco_map.py에서 암 분류를 불러오지 못했습니다. {'에러: '+str(info) if info else ''}")
        g_manual = st.text_input("암 그룹(수동)", value=st.session_state.get("onco_group") or "", key=wkey("onco_g_manual"))
        d_manual = st.text_input("진단(암종, 수동)", value=st.session_state.get("onco_dx") or "", key=wkey("onco_d_manual"))
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
        idx_default = dx_keys.index(default_dx) if default_dx in dx_keys else 0
        idx = st.selectbox("진단(암종)", list(range(len(labels))), index=idx_default, format_func=lambda i: labels[i], key=wkey("onco_dx_idx"))
        dx = dx_keys[idx]
        st.session_state["onco_group"] = group
        st.session_state["onco_dx"] = dx
        dmap = omap.get(group, {}).get(dx, {})
        recs = []
        for sec in ["chemo","targeted","maintenance","support","abx"]:
            arr = dmap.get(sec, [])
            if arr: recs.append(f"{sec}: " + ", ".join(arr[:12]))
        if recs:
            st.markdown("#### onco_map 권장 약물")
            for r in recs: st.write("- " + r)
    else:
        st.warning("해당 그룹에 진단이 없습니다.")
        st.session_state["onco_group"] = group
        st.session_state["onco_dx"] = None
    return st.session_state.get("onco_group"), st.session_state.get("onco_dx")

# ---------- special_tests loader ----------
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
    out, seen = [], set()
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
    for fn in ["special_tests_ui", "render_special_tests_ui", "build_special_tests_ui", "ui"]:
        f = getattr(mod, fn, None)
        if callable(f): return f()
    for name in ["SPECIAL_TESTS","SPECIAL_RESULTS","DATA"]:
        if hasattr(mod, name):
            data = getattr(mod, name)
            if isinstance(data, (list, tuple)): return list(data)
            if isinstance(data, dict):
                out = []
                for k,v in data.items():
                    if isinstance(v,(list,tuple)):
                        for x in v: out.append(f"{k}: {x}")
                    else: out.append(f"{k}: {v}")
                return out
    return None

def render_special_tests():
    st.header("🔬 특수검사")
    try:
        mod, info = _load_special_module()
        if not mod:
            st.error(f"특수검사 모듈을 찾지 못했습니다. {'에러: '+str(info) if info else ''}"); return
        res = _call_special_ui(mod)
        if res is None:
            st.error("특수검사 UI 함수를 찾지 못했습니다. (허용: special_tests_ui/render_special_tests_ui/build_special_tests_ui/ui 또는 SPECIAL_TESTS 자료구조)"); return
        if isinstance(res,(list,tuple)):
            lines = [str(x) for x in res]
        else:
            lines = getattr(mod,"LATEST_LINES",[])
            if not isinstance(lines,list): lines = []
        st.session_state["special_interpretations"] = lines
        if lines:
            st.markdown("### 특수검사 해석")
            for ln in lines: st.markdown(f"- {ln}")
        st.caption(f"special_tests 연결: {info}")
    except Exception as e:
        st.error(f"특수검사 로드 오류: {e}")

# ---------- Labs (validation) ----------
LAB_FIELDS=[("WBC","x10^3/µL"),("ANC","/µL"),("Hb","g/dL"),("Plt","x10^3/µL"),
            ("Creatinine","mg/dL"),("eGFR","mL/min/1.73m²"),("AST","U/L"),
            ("ALT","U/L"),("T.bil","mg/dL"),("Na","mmol/L"),("K","mmol/L"),
            ("Cl","mmol/L"),("CRP","mg/L"),("ESR","mm/hr"),("Ferritin","ng/mL"),
            ("Procalcitonin","ng/mL"),("UPCR","mg/g"),("ACR","mg/g")]

REF_RANGE = {
    "WBC": (4.0, 10.0), "ANC": (1500, 8000), "Hb": (12.0, 16.0), "Plt": (150, 400),
    "Creatinine": (0.5, 1.2), "eGFR": (60, None), "AST": (0, 40), "ALT": (0, 40),
    "T.bil": (0.2, 1.2), "Na": (135, 145), "K": (3.5, 5.1), "Cl": (98, 107),
    "CRP": (0, 5), "ESR": (0, 20), "Ferritin": (15, 150), "Procalcitonin": (0, 0.5),
}

def _parse_float(x):
    if x is None: return None
    s = str(x).strip().replace(",", "")
    if s == "": return None
    try:
        return float(s)
    except Exception:
        return None

def labs_input_ui():
    st.header("🧪 피수치 입력 (유효성 검증)")
    labs = st.session_state.get("labs_dict", {}).copy()
    cols = st.columns(3)
    alerts = []
    for i,(name,unit) in enumerate(LAB_FIELDS):
        with cols[i%3]:
            val = st.text_input(f"{name} ({unit})", value=str(labs.get(name,"")), key=wkey(f"lab_{name}"))
            labs[name] = val.strip()
            v = _parse_float(val)
            if name in REF_RANGE and v is not None:
                lo, hi = REF_RANGE[name]
                ok = ((lo is None or v >= lo) and (hi is None or v <= hi))
                if ok:
                    st.caption("✅ 참고범위 내")
                else:
                    alerts.append(f"{name} 비정상: {v}")
                    st.caption("⚠️ 참고범위 벗어남")
            elif v is None and val.strip() != "":
                st.caption("❌ 숫자 인식 실패")
    st.session_state["labs_dict"]=labs
    if alerts:
        st.warning("이상치: " + ", ".join(alerts))
    st.markdown("#### 입력 요약")
    for k,v in labs.items():
        if str(v).strip()!="": st.markdown(f"- **{k}**: {v}")
    return labs

# ---------- Blood pressure ----------
def classify_bp(sbp, dbp):
    if sbp is None or dbp is None: return ("측정값 없음","SBP/DBP를 입력하세요.")
    if sbp>=180 or dbp>=120: return ("🚨 고혈압 위기","즉시 의료기관 평가 권장")
    if sbp>=140 or dbp>=90: return ("2기 고혈압","생활습관 + 약물치료 고려(의료진)")
    if 130<=sbp<=139 or 80<=dbp<=89: return ("1기 고혈압","생활습관 교정 + 위험평가")
    if 120<=sbp<=129 and dbp<80: return ("주의혈압(상승)","염분 제한/운동/체중조절 권장")
    if sbp<120 and dbp<80: return ("정상혈압","유지")
    return ("분류불가","값을 확인하세요.")

def bp_ui():
    st.header("🩺 혈압 체크 (압종분류)")
    c1,c2,c3 = st.columns(3)
    with c1: sbp = st.text_input("수축기 혈압 SBP (mmHg)", key=wkey("sbp"))
    with c2: dbp = st.text_input("이완기 혈압 DBP (mmHg)", key=wkey("dbp"))
    with c3: st.caption("기준: ACC/AHA 2017 (단순화)")
    sbp_val = _parse_float(sbp); dbp_val = _parse_float(dbp)
    cat,note = classify_bp(sbp_val, dbp_val)
    st.info(f"분류: **{cat}** — {note}")
    st.session_state["bp_summary"] = f"{cat} (SBP {sbp or '?'} / DBP {dbp or '?'}) — {note}"
    return cat,note

# ---------- Pediatric guide ----------
def render_caregiver_notes_peds(*, stool, fever, persistent_vomit, oliguria, cough, nasal, eye, abd_pain, ear_pain, rash, hives, migraine, hfmd, constipation=False, anc_low=None):
    st.header("🧒 소아가이드")
    if anc_low is None:
        try:
            anc_val = _parse_float(st.session_state.get("labs_dict", {}).get("ANC")); anc_low = (anc_val is not None and anc_val<500)
        except Exception: anc_low=False
    notes=[]
    def bullet(title, body):
        st.markdown(f"**{title}**"); st.markdown(body.strip())
        first = body.strip().splitlines()[0].strip("- ").strip()
        if first: notes.append(f"{title} — {first}")
    if anc_low:
        bullet("🍽️ ANC 낮음(호중구 감소) 식이가이드","""
- **생야채/날고기·생선 금지**, 모든 음식은 **충분히 익혀서**
- **멸균/살균 제품** 위주 섭취, 유통기한·보관 온도 준수
- 과일은 **껍질 제거 후** 섭취(가능하면 데친 뒤 식혀서)
- **조리 후 2시간 지나면 폐기**, **뷔페/회/초밥/생채소 샐러드 금지**
""")
    if stool in ["3~4회","5~6회","7회 이상"]:
        bullet("💧 설사/장염 의심","""
- 하루 **3회 이상 묽은 변**이면 장염 가능성, **노란/초록·거품 많은 변**이면 로타/노로 의심
- **ORS**: 처음 1시간 **10–20 mL/kg**, 이후 설사 1회당 **5–10 mL/kg**
- **즉시 진료**: 피 섞인 변, **고열 ≥39℃**, **소변 거의 없음/축 늘어짐**
"""); bullet("🍽️ 식이가이드(설사)","""
- 초기 24시간: **바나나·쌀죽·사과퓨레·토스트(BRAT 변형)** 참고
- **자주·소량**의 미지근한 수분, 탄산/아이스는 피하기
""")
    if constipation:
        bullet("🚻 변비 대처","""
- **수분**: 대략 체중 **50–60 mL/kg/일**(지시 맞춰 조정)
- **좌변 습관**: 식후 10–15분, 하루 1회 5–10분
- **운동**: 가벼운 걷기·스트레칭
- **즉시/조속 진료**: 심한 복통/구토/혈변/3–4일 무배변+팽만
""")
        bullet("🍽️ 식이가이드(변비{ANC})".format(ANC=" + ANC 낮음" if anc_low else ""),"""
- (ANC 정상) **수용성/불용성 섬유**: 귀리·보리·사과/배, 키위, 자두·프룬, 고구마, 통곡물빵, 현미, 익힌 채소
- (ANC 낮음) 생야채 대신 **익힌 채소**, 통곡·오트밀·귀리죽 등 **가열 곡류**, 과일은 **껍질 제거**
- 프룬/배 주스: **1–3 mL/kg/회**, 하루 1–2회(과하면 설사) — ANC 낮으면 **끓여 식힌 물 1:1 희석**
""")
    if fever in ["38~38.5","38.5~39","39 이상"]:
        bullet("🌡️ 발열 대처","""
- 옷 가볍게, 실내 시원하게
- **해열제 간격**: 아세트아미노펜 ≥4h, 이부프로펜 ≥6h
- **연락 기준**: **≥38.5℃**, **내원 기준**: **≥39.0℃** 또는 무기력/경련/탈수/호흡곤란
""")
    if persistent_vomit:
        bullet("🤢 구토 지속","""
- 10~15분마다 **소량**의 수분(ORS/미지근한 물)
- **즉시 진료**: 6h 이상 물도 못 마심 / 초록·커피색 토물 / 혈토
""")
    if oliguria:
        bullet("🚨 탈수 의심(소변량 급감)","""
- 입술 마름·눈물 없음·피부 탄력 저하·축 늘어짐
- **즉시 진료**: **6h 이상 무뇨(영아 4h)**, 매우 축 늘어짐/무기력
""")
    if cough in ["조금","보통","심함"] or nasal in ["진득","누런"]:
        bullet("🤧 기침·콧물(상기도)","""
- **생리식염수/흡인기**로 콧물 제거, 수면 시 머리 높이기
- **즉시 진료**: 숨차함/청색증/가슴함몰
""")
    if eye in ["노랑-농성","양쪽"]:
        bullet("👀 결막염 의심","""
- 손 위생 철저, 분비물 닦기
- **양쪽·고열·눈 통증/빛 통증** → 진료 권장
""")
    if abd_pain:
        bullet("🤕 복통","""
- **쥐어짜는 통증/우하복부 통증/보행 시 악화**면 충수염 고려
- **즉시 진료**: 지속적 심한 통증·국소 압통/반발통·구토 동반
""")
    if ear_pain:
        bullet("👂 귀 통증","""
- 해열제·진통제 간격 준수, 코막힘 관리
- **즉시 진료**: 고막 분비물, 안면 마비, 48h 이상 지속
""")
    if rash or hives:
        bullet("🌱 피부 발진/두드러기","""
- 시원한 찜질, 필요 시 항히스타민
- **즉시 진료**: **입술/혀 붓기, 호흡곤란, 어지러움**
""")
    if migraine:
        bullet("🤯 두통/편두통","""
- 조용하고 어두운 곳에서 휴식, 수분 보충
- **즉시 진료**: **번개치는 두통**, **시야 이상/복시/암점**, **신경학적 이상**
""")
    if hfmd:
        bullet("✋👣 수족구 의심(HFMD)","""
- **손·발·입 안** 물집/궤양 + 발열
- 전염성: 손 씻기/식기 구분
- **탈수**, **고열 >3일**, **경련/무기력** → 진료 필요
""")
    st.session_state["peds_notes"]=notes

# ---------- Chemo AEs (concise) ----------
GOOD,WARN,DANGER="🟢","🟡","🚨"
def _b(txt:str)->str: return txt.replace("{GOOD}",GOOD).replace("{WARN}",WARN).replace("{DANGER}",DANGER)
CHEMO_DB={
 "ATRA (Tretinoin, Vesanoid) / 베사노이드":{
  "effects":{"common":["{WARN} 두통/피부건조/지질상승"]},
  "ra_syndrome":{"name":"RA-분화증후군","symptoms":["{DANGER} 발열","{DANGER} 호흡곤란/저산소","{DANGER} 저혈압","{DANGER} 전신부종/체중 급증"]},
  "monitor":["CBC, SpO₂, 체중/부종, 지질"],
 },
 "Cytarabine (Ara-C) / 시타라빈(아라씨)":{
  "routes":{"IV/SC(표준용량)":["{WARN} 발열/구토/설사/구내염","{DANGER} 골수억제","{WARN} 결막염"],
            "HDAC(고용량)":["{DANGER} 소뇌독성(보행/말/글씨체 변화)","{WARN} 각결막염 — 스테로이드 점안"]},
  "monitor":["CBC, 간기능, 신경학적 징후"],
 },
 "MTX (Methotrexate) / 메토트렉세이트":{
  "effects":{"blood":["{DANGER} 골수억제"],"renal":["{DANGER} HD-MTX 신독성/결정뇨"],"pulmonary":["{WARN} MTX 폐렴"]},
  "monitor":["CBC, AST/ALT, Cr/eGFR","HD-MTX: MTX 농도 + 류코보린 + 요알칼리화"],
 },
}
def render_chemo_adverse_effects(agents, route_map=None):
    st.header("💊 항암제")
    summary=[]
    if not agents:
        st.info("항암제를 선택하면 상세 부작용/모니터링 지침이 표시됩니다."); st.session_state['onco_warnings']=[]; return
    for agent in agents:
        data = CHEMO_DB.get(agent, {}); st.markdown(f"### {agent}")
        if "routes" in data:
            route = (route_map or {}).get(agent) or "IV/SC(표준용량)"
            st.markdown(f"**투여 경로/용량:** {route}")
            for line in data["routes"].get(route, []):
                st.markdown(f"- {_b(line)}")
                if "{DANGER}" in line or "소뇌독성" in line:
                    summary.append(f"{agent} [{route}]: " + _b(line).replace('🟡 ','').replace('🟢 ','').replace('🚨 ',''))
        else:
            effects=data.get("effects",{})
            for section,arr in effects.items():
                with st.expander(section):
                    for ln in arr:
                        st.markdown(f"- {_b(ln)}")
                        if "{DANGER}" in ln:
                            summary.append(f"{agent}: " + _b(ln).replace('🟡 ','').replace('🟢 ','').replace('🚨 ',''))
        if agent.startswith("ATRA") and data.get("ra_syndrome"):
            rs=data["ra_syndrome"]
            with st.expander("⚠️ RA-분화증후군"):
                for s in rs["symptoms"]:
                    st.markdown(f"- {_b(s)}")
                    if "{DANGER}" in s: summary.append("ATRA/RA-증후군: " + _b(s).replace('🚨 ',''))
    st.session_state["onco_warnings"]=list(dict.fromkeys(summary))[:60]

# ---------- Report / Export ----------
def build_report():
    parts=[f"# 피수치/가이드 요약\n- 생성시각: {kst_now()}\n- 제작/자문: Hoya/GPT"]
    labs=st.session_state.get("labs_dict",{})
    if labs and any(str(v).strip() for v in labs.values()):
        parts.append("## 피수치")
        for k,v in labs.items():
            if str(v).strip()!="": parts.append(f"- {k}: {v}")
    bp=st.session_state.get("bp_summary")
    if bp: parts.append("## 혈압 분류(압종분류)"); parts.append(f"- {bp}")
    g=st.session_state.get("onco_group"); d=st.session_state.get("onco_dx")
    if g or d: parts.append("## 암종 선택"); parts.append(f"- 그룹: {g or '-'} / 진단: {d or '-'}")
    peds=st.session_state.get("peds_notes",[])
    if peds: parts.append("## 소아가이드"); parts.extend([f"- {x}" for x in peds])
    lines=st.session_state.get("special_interpretations",[])
    if lines: parts.append("## 특수검사 해석"); parts.extend([f"- {ln}" for ln in lines])
    agents=st.session_state.get("selected_agents",[]); warns=st.session_state.get("onco_warnings",[])
    if agents: parts.append("## 항암제(선택)"); parts.extend([f"- {a}" for a in agents])
    if warns: parts.append("## 항암제 부작용 요약(위험)"); parts.extend([f"- {w}" for w in warns])
    if not any(sec.startswith("##") for sec in parts[1:]): parts.append("## 입력된 데이터가 없어 기본 안내만 표시됩니다.")
    return "\n\n".join(parts)

def export_report_pdf(md_text: str) -> bytes:
    try:
        spec = importlib.util.spec_from_file_location("pdf_export", "/mnt/data/pdf_export.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore
        if hasattr(mod, "export_md_to_pdf"):
            return mod.export_md_to_pdf(md_text)  # returns bytes
    except Exception as e:
        st.error(f"PDF 내보내기 오류: {e}")
    return b""

# ---------- Feedback ----------
def feedback_form():
    st.subheader("🗣️ 피드백 보내기")
    col1,col2 = st.columns([2,1])
    with col1:
        comment = st.text_area("피드백 내용", placeholder="개선 요청, 버그 제보, 추가 기능 등 자유롭게 적어주세요.", key=wkey("fb_comment"))
    with col2:
        rating = st.selectbox("만족도(1~5)", [5,4,3,2,1], index=0, key=wkey("fb_rating"))
        name = st.text_input("이름(선택)", key=wkey("fb_name"))
        email = st.text_input("이메일(선택)", key=wkey("fb_email"))
    if st.button("✉️ 피드백 제출", key=wkey("fb_submit")):
        row = [kst_now(), rating, name, email, comment.replace("\n"," ").strip()]
        try:
            newfile = not FEED_PATH.exists()
            with FEED_PATH.open("a", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                if newfile:
                    w.writerow(["timestamp_kst","rating","name","email","comment"])
                w.writerow(row)
            st.success("피드백이 저장되었습니다. 감사합니다!")
            st.caption(f"저장 경로: {FEED_PATH}")
        except Exception as e:
            st.error(f"피드백 저장 실패: {e}")

def feedback_stats():
    cnt = 0; avg = None
    try:
        if FEED_PATH.exists():
            import pandas as pd
            df = pd.read_csv(FEED_PATH)
            cnt = len(df.index)
            if "rating" in df.columns:
                try:
                    avg = float(df["rating"].astype(float).mean())
                except Exception:
                    avg = None
    except Exception:
        pass
    cols = st.columns(3)
    with cols[0]: st.metric("현재 사용자 수", f"{CURRENT_USERS} 명")
    with cols[1]: st.metric("누적 피드백", f"{cnt} 건")
    with cols[2]: st.metric("평균 만족도", f"{avg:.1f}" if avg is not None else "-")

# ---------- Diagnostics ----------
def diagnostics_panel():
    st.markdown("### 🔧 진단 패널 (경로/모듈 상태)")
    # onco_map
    omap, dx_display, onco_info = load_onco()
    status = "✅ 로드됨" if isinstance(omap, dict) and omap else "❌ 실패"
    st.write(f"- onco_map: **{status}** — 경로: `{onco_info}`")
    # special_tests
    try:
        mod, sp_info = _load_special_module()
        st.write(f"- special_tests: **{'✅ 로드됨' if mod else '❌ 실패'}** — 경로: `{sp_info}`")
    except Exception as e:
        st.write(f"- special_tests: ❌ 오류 — {e}")
    # pdf_export
    try:
        spec = importlib.util.spec_from_file_location("pdf_export", "/mnt/data/pdf_export.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore
        ok = hasattr(mod, "export_md_to_pdf")
        st.write(f"- pdf_export: **{'✅ 사용 가능' if ok else '❌ 함수 없음'}** — 경로: `/mnt/data/pdf_export.py`")
    except Exception as e:
        st.write(f"- pdf_export: ❌ 오류 — {e}")

# ---------- App Layout (requested order) ----------
st.set_page_config(page_title="피수치 가이드 — 최종 통합판", layout="wide")
restore_state()

st.title("피수치 가이드 — 최종 통합판")
st.caption("순서: 홈 → 암종 → 항암제 → 피수치 → 특수검사 → 혈압 체크 → 소아가이드 → 보고서")

tabs = st.tabs(["🏠 홈", "🧬 암종", "💊 항암제", "🧪 피수치", "🔬 특수검사", "🩺 혈압 체크", "🧒 소아가이드", "📄 보고서"])

with tabs[0]:
    st.subheader("홈")
    feedback_stats()
    st.markdown("---")
    diagnostics_panel()
    st.markdown("---")
    st.markdown("### 소아 가이드 바로가기")
    if st.button("🧒 홈에서 소아 가이드 열기", key=wkey("open_peds_on_home")):
        st.session_state["show_peds_on_home"] = True
    if st.session_state.get("show_peds_on_home"):
        st.info("홈에서 간편하게 소아 가이드를 바로 볼 수 있습니다. (탭 전환 없이)")
        c1,c2,c3 = st.columns(3)
        with c1:
            stool = st.selectbox("설사 횟수", ["0~2회","3~4회","5~6회","7회 이상"], key=wkey("home_stool"))
            fever = st.selectbox("최고 체온", ["37.x","38~38.5","38.5~39","39 이상"], key=wkey("home_fever"))
            constipation = st.checkbox("변비", key=wkey("home_constipation"))
        with c2:
            persistent_vomit = st.checkbox("지속 구토", key=wkey("home_vomit"))
            oliguria = st.checkbox("소변량 급감", key=wkey("home_oligo"))
            cough = st.selectbox("기침 정도", ["없음","조금","보통","심함"], key=wkey("home_cough"))
            nasal = st.selectbox("콧물 상태", ["맑음","진득","누런"], key=wkey("home_nasal"))
        with c3:
            eye = st.selectbox("눈 분비물", ["없음","맑음","노랑-농성","양쪽"], key=wkey("home_eye"))
            abd_pain = st.selectbox("복통", ["없음","조금","보통","심함"], key=wkey("home_abd"))
            ear_pain = st.selectbox("귀 통증", ["없음","조금","보통","심함"], key=wkey("home_ear"))
            rash = st.checkbox("피부 발진", key=wkey("home_rash"))
            hives = st.checkbox("두드러기", key=wkey("home_hives"))
            migraine = st.checkbox("두통/편두통", key=wkey("home_migraine"))
            hfmd = st.checkbox("수족구 의심", key=wkey("home_hfmd"))
        render_caregiver_notes_peds(stool=stool, fever=fever, persistent_vomit=persistent_vomit, oliguria=oliguria,
                                    cough=cough, nasal=nasal, eye=eye, abd_pain=abd_pain, ear_pain=ear_pain,
                                    rash=rash, hives=hives, migraine=migraine, hfmd=hfmd, constipation=constipation)
    st.markdown("---")
    feedback_form()

with tabs[1]:
    onco_select_ui(); autosave_state()

with tabs[2]:
    all_agents = list(CHEMO_DB.keys())
    selected_agents = st.multiselect("항암제", all_agents, key=wkey("agents"))
    st.session_state["selected_agents"]=selected_agents
    route_map={}
    if "Cytarabine (Ara-C) / 시타라빈(아라씨)" in selected_agents:
        route_map["Cytarabine (Ara-C) / 시타라빈(아라씨)"] = st.selectbox("아라씨 제형/용량", ["IV/SC(표준용량)","HDAC(고용량)"], key=wkey("ara_route"))
    render_chemo_adverse_effects(selected_agents, route_map=route_map); autosave_state()

with tabs[3]:
    labs_input_ui(); autosave_state()

with tabs[4]:
    render_special_tests(); autosave_state()

with tabs[5]:
    bp_ui(); autosave_state()

with tabs[6]:
    # Full pediatric guide tab
    c1,c2,c3 = st.columns(3)
    with c1:
        stool = st.selectbox("설사 횟수", ["0~2회","3~4회","5~6회","7회 이상"], key=wkey("stool"))
        fever = st.selectbox("최고 체온", ["37.x","38~38.5","38.5~39","39 이상"], key=wkey("fever"))
        constipation = st.checkbox("변비", key=wkey("constipation"))
    with c2:
        persistent_vomit = st.checkbox("지속 구토", key=wkey("vomit"))
        oliguria = st.checkbox("소변량 급감", key=wkey("oligo"))
        cough = st.selectbox("기침 정도", ["없음","조금","보통","심함"], key=wkey("cough"))
        nasal = st.selectbox("콧물 상태", ["맑음","진득","누런"], key=wkey("nasal"))
    with c3:
        eye = st.selectbox("눈 분비물", ["없음","맑음","노랑-농성","양쪽"], key=wkey("eye"))
        abd_pain = st.selectbox("복통", ["없음","조금","보통","심함"], key=wkey("abd"))
        ear_pain = st.selectbox("귀 통증", ["없음","조금","보통","심함"], key=wkey("ear"))
        rash = st.checkbox("피부 발진", key=wkey("rash"))
        hives = st.checkbox("두드러기", key=wkey("hives"))
        migraine = st.checkbox("두통/편두통", key=wkey("migraine"))
        hfmd = st.checkbox("수족구 의심", key=wkey("hfmd"))
    render_caregiver_notes_peds(stool=stool, fever=fever, persistent_vomit=persistent_vomit, oliguria=oliguria,
                                cough=cough, nasal=nasal, eye=eye, abd_pain=abd_pain, ear_pain=ear_pain,
                                rash=rash, hives=hives, migraine=migraine, hfmd=hfmd, constipation=constipation)
    autosave_state()

with tabs[7]:
    st.header("📄 보고서")
    md = build_report()
    st.code(md, language="markdown")
    st.download_button("📥 보고서(.txt) 다운로드", data=md.encode("utf-8"), file_name="report.txt", mime="text/plain")
    pdf_bytes = export_report_pdf(md)
    if pdf_bytes:
        st.download_button("🖨️ 보고서(.pdf) 다운로드", data=pdf_bytes, file_name="report.pdf", mime="application/pdf")
    else:
        st.warning("PDF 변환 모듈(reportlab 또는 제공된 pdf_export.py)이 동작하지 않아 TXT로만 내보낼 수 있습니다.")
    autosave_state()
