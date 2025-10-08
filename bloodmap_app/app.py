# app.py
import datetime as _dt
import os, sys, re, io, csv
from pathlib import Path
import importlib.util
import streamlit as st

APP_VERSION = "In memory of Eunseo, a little star now shining in the sky. This app is made with the hope that she is no longer in pain, and resting peacefully in a world free from all hardships."

# ---------- Safe Import Helper ----------
def _load_local_module(mod_name: str, rel_paths):
    here = Path(__file__).resolve().parent
    for rel in rel_paths:
        cand = (here / rel).resolve()
        if cand.exists():
            spec = importlib.util.spec_from_file_location(mod_name, str(cand))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            sys.modules[mod_name] = mod
            return mod, str(cand)
    try:
        mod = __import__(mod_name)
        return mod, f"(sys.path)::{mod.__file__}"
    except Exception:
        return None, None

# ---------- Optional modules with graceful fallback ----------
_branding, BRANDING_PATH = _load_local_module("branding", ["branding.py", "modules/branding.py"])
if _branding and hasattr(_branding, "render_deploy_banner"):
    render_deploy_banner = _branding.render_deploy_banner
else:
    def render_deploy_banner(*a, **k): return None

_core, CORE_PATH = _load_local_module("core_utils", ["core_utils.py", "modules/core_utils.py"])
if _core and hasattr(_core, "ensure_unique_pin"):
    ensure_unique_pin = _core.ensure_unique_pin
else:
    def ensure_unique_pin(user_key: str, auto_suffix: bool=True):
        if not user_key: return "guest#PIN", False, "empty"
        if "#" not in user_key: user_key += "#0001"
        return user_key, False, "ok"

_pdf, PDF_PATH = _load_local_module("pdf_export", ["pdf_export.py", "modules/pdf_export.py"])
if _pdf and hasattr(_pdf, "export_md_to_pdf"):
    export_md_to_pdf = _pdf.export_md_to_pdf
else:
    def export_md_to_pdf(md_text: str) -> bytes:
        # 최소 폴백: PDF 엔진이 없으면 텍스트 바이트 반환(다운로드는 가능)
        return md_text.encode("utf-8")

_onco, ONCO_PATH = _load_local_module("onco_map", ["onco_map.py", "modules/onco_map.py"])
if _onco:
    build_onco_map = getattr(_onco, "build_onco_map", lambda: {})
    dx_display = getattr(_onco, "dx_display", lambda g,d: f"{g} - {d}")
    auto_recs_by_dx = getattr(_onco, "auto_recs_by_dx", lambda *a, **k: {"chemo": [], "targeted": [], "abx": []})
else:
    build_onco_map = lambda: {}
    dx_display = lambda g,d: f"{g} - {d}"
    def auto_recs_by_dx(*args, **kwargs): return {"chemo": [], "targeted": [], "abx": []}

_drugdb, DRUGDB_PATH = _load_local_module("drug_db", ["drug_db.py", "modules/drug_db.py"])
if _drugdb:
    DRUG_DB = getattr(_drugdb, "DRUG_DB", {})
    ensure_onco_drug_db = getattr(_drugdb, "ensure_onco_drug_db", lambda db: None)
    display_label = getattr(_drugdb, "display_label", lambda k, db=None: str(k))
else:
    DRUG_DB = {}
    def ensure_onco_drug_db(db): pass
    def display_label(k, db=None): return str(k)

_ld, LD_PATH = _load_local_module("lab_diet", ["lab_diet.py", "modules/lab_diet.py"])
if _ld and hasattr(_ld, "lab_diet_guides"):
    lab_diet_guides = _ld.lab_diet_guides
else:
    def lab_diet_guides(labs, heme_flag=False): return []

_pd, PD_PATH = _load_local_module("peds_dose", ["peds_dose.py", "modules/peds_dose.py"])
if _pd:
    acetaminophen_ml = getattr(_pd, "acetaminophen_ml", lambda wt: (0.0,0.0))
    ibuprofen_ml = getattr(_pd, "ibuprofen_ml", lambda wt: (0.0,0.0))
else:
    def acetaminophen_ml(w): return (0.0,0.0)
    def ibuprofen_ml(w): return (0.0,0.0)

_sp, SPECIAL_PATH = _load_local_module("special_tests", ["special_tests.py", "modules/special_tests.py"])
if _sp and hasattr(_sp, "special_tests_ui"):
    special_tests_ui = _sp.special_tests_ui
else:
    SPECIAL_PATH = None
    def special_tests_ui():
        st.warning("special_tests.py를 찾지 못해, 특수검사 UI는 더미로 표시됩니다.")
        return []

# --- optional plotting backend (matplotlib → st.line_chart → 표 폴백) ---
try:
    import matplotlib.pyplot as plt  # 있으면 사용
    _HAS_MPL = True
except Exception:
    plt = None
    _HAS_MPL = False

# ---------- Page & Banner ----------
st.set_page_config(page_title=f"Bloodmap {APP_VERSION}", layout="wide")
st.title(f"Bloodmap {APP_VERSION}")
st.markdown(
    """> In memory of Eunseo, a little star now shining in the sky.
> This app is made with the hope that she is no longer in pain,
> and resting peacefully in a world free from all hardships."""
)
st.markdown("---")
render_deploy_banner("https://bloodmap.streamlit.app/", "제작: Hoya/GPT · 자문: Hoya/GPT")
st.caption(f"모듈 경로 — special_tests: {SPECIAL_PATH or '(not found)'} | onco_map: {ONCO_PATH or '(not found)'} | drug_db: {DRUGDB_PATH or '(not found)'}")

from qr_patch import st_qr
st_qr("https://bloodmap.streamlit.app/", caption="공식 배포 링크 QR")

# ---------- Helpers ----------
def wkey(name:str)->str:
    who = st.session_state.get("key","guest#PIN")
    return f"{who}:{name}"

def _try_float(s):
    if s is None: return None
    if isinstance(s, (int,float)): return float(s)
    s = str(s)
    m = re.search(r'([-+]?[0-9]*[\\.,]?[0-9]+)', s)
    if not m: return None
    num = m.group(1).replace(",", ".")
    try: return float(num)
    except Exception: return None

def _safe_float(v, default=0.0):
    try:
        if v in (None, ""): return default
        if isinstance(v, (int, float)): return float(v)
        return float(str(v).strip())
    except Exception:
        return default

# ---------- Emergency scoring (Weights + Presets) ----------
DEFAULT_WEIGHTS = {
    "w_anc_lt500": 1.0, "w_anc_500_999": 1.0,
    "w_temp_38_0_38_4": 1.0, "w_temp_ge_38_5": 1.0,
    "w_plt_lt20k": 1.0, "w_hb_lt7": 1.0, "w_crp_ge10": 1.0, "w_hr_gt130": 1.0,
    "w_hematuria": 1.0, "w_melena": 1.0, "w_hematochezia": 1.0,
    "w_chest_pain": 1.0, "w_dyspnea": 1.0, "w_confusion": 1.0,
    "w_oliguria": 1.0, "w_persistent_vomit": 1.0, "w_petechiae": 1.0,
    "w_thunderclap": 1.0, "w_visual_change": 1.0,
}
PRESETS = {
    "기본(Default)": DEFAULT_WEIGHTS,
    "발열·감염 민감": {**DEFAULT_WEIGHTS, "w_temp_ge_38_5": 2.0, "w_temp_38_0_38_4": 1.5, "w_crp_ge10": 1.5, "w_anc_lt500": 2.0, "w_anc_500_999": 1.5},
    "출혈 위험 민감": {**DEFAULT_WEIGHTS, "w_plt_lt20k": 2.5, "w_petechiae": 2.0, "w_hematochezia": 2.0, "w_melena": 2.0},
    "신경계 위중 민감": {**DEFAULT_WEIGHTS, "w_thunderclap": 3.0, "w_visual_change": 2.5, "w_confusion": 2.5, "w_chest_pain": 1.2},
}

def get_weights():
    key = st.session_state.get("key","guest#PIN")
    store = st.session_state.setdefault("weights", {})
    return store.setdefault(key, dict(DEFAULT_WEIGHTS))

def set_weights(new_w):
    key = st.session_state.get("key","guest#PIN")
    st.session_state.setdefault("weights", {})
    st.session_state["weights"][key] = dict(new_w)

def anc_band(anc: float) -> str:
    if anc is None: return "(미입력)"
    try: anc = float(anc)
    except Exception: return "(값 오류)"
    if anc < 500: return "🚨 중증 호중구감소(<500)"
    if anc < 1000: return "🟧 중등도 호중구감소(500~999)"
    if anc < 1500: return "🟡 경도 호중구감소(1000~1499)"
    return "🟢 정상(≥1500)"

def emergency_level(labs: dict, temp_c, hr, symptoms: dict):
    a = _try_float((labs or {}).get("ANC"))
    p = _try_float((labs or {}).get("PLT"))
    c = _try_float((labs or {}).get("CRP"))
    h = _try_float((labs or {}).get("Hb"))
    t = _try_float(temp_c)
    heart = _try_float(hr)

    W = get_weights()
    reasons = []; contrib = []
    def add(name, base, wkey):
        w = W.get(wkey, 1.0); s = base * w
        contrib.append({"factor": name, "base": base, "weight": w, "score": s})
        reasons.append(name)

    if a is not None and a < 500:      add("ANC<500", 3, "w_anc_lt500")
    elif a is not None and a < 1000:   add("ANC 500~999", 2, "w_anc_500_999")
    if t is not None and t >= 38.5:    add("고열 ≥38.5℃", 2, "w_temp_ge_38_5")
    elif t is not None and t >= 38.0:  add("발열 38.0~38.4℃", 1, "w_temp_38_0_38_4")
    if p is not None and p < 20000:    add("혈소판 <20k", 2, "w_plt_lt20k")
    if h is not None and h < 7.0:      add("중증 빈혈(Hb<7)", 1, "w_hb_lt7")
    if c is not None and c >= 10:      add("CRP ≥10", 1, "w_crp_ge10")
    if heart and heart > 130:          add("빈맥(HR>130)", 1, "w_hr_gt130")

    if symptoms.get("hematuria"):       add("혈뇨", 1, "w_hematuria")
    if symptoms.get("melena"):          add("흑색변", 2, "w_melena")
    if symptoms.get("hematochezia"):    add("혈변", 2, "w_hematochezia")
    if symptoms.get("chest_pain"):      add("흉통", 2, "w_chest_pain")
    if symptoms.get("dyspnea"):         add("호흡곤란", 2, "w_dyspnea")
    if symptoms.get("confusion"):       add("의식저하/혼돈", 3, "w_confusion")
    if symptoms.get("oliguria"):        add("소변량 급감", 2, "w_oliguria")
    if symptoms.get("persistent_vomit"):add("지속 구토", 2, "w_persistent_vomit")
    if symptoms.get("petechiae"):       add("점상출혈", 2, "w_petechiae")
    if symptoms.get("thunderclap"):     add("번개치는 듯한 두통(Thunderclap)", 3, "w_thunderclap")
    if symptoms.get("visual_change"):   add("시야 이상/복시/암점", 2, "w_visual_change")

    risk = sum(item["score"] for item in contrib)
    level = "🚨 응급" if risk >= 5 else ("🟧 주의" if risk >= 2 else "🟢 안심")
    return level, reasons, contrib

# ---------- Preload ----------
ensure_onco_drug_db(DRUG_DB)
ONCO = build_onco_map() or {}

# ---------- Sidebar (PIN • Vital • Age/Mode) ----------
with st.sidebar:
    st.header("프로필")
    raw_key = st.text_input("별명#PIN", value=st.session_state.get("key","guest#PIN"), key="user_key_raw")
    unique_key, was_modified, msg = ensure_unique_pin(raw_key, auto_suffix=True)
    st.session_state["key"] = unique_key
    if was_modified: st.warning(msg + f" → 현재 키: {unique_key}")
    else:            st.caption("PIN 확인됨")

    st.subheader("활력징후")
    temp = st.text_input("현재 체온(℃)", value=st.session_state.get(wkey("cur_temp"), ""), key=wkey("cur_temp"), placeholder="36.8")
    hr   = st.text_input("심박수(bpm)", value=st.session_state.get(wkey("cur_hr"), ""), key=wkey("cur_hr"), placeholder="0")

    st.subheader("연령/모드")
    age_years = st.number_input("나이(년)", min_value=0.0, max_value=120.0,
                                value=_safe_float(st.session_state.get(wkey("age_years"), 0.0), 0.0),
                                step=0.5, key=wkey("age_years_num"))
    st.session_state[wkey("age_years")] = age_years
    auto_peds = age_years < 18.0
    manual_override = st.checkbox("소아/성인 수동 선택", value=False, key=wkey("mode_override"))
    if manual_override:
        is_peds = st.toggle("소아 모드", value=bool(st.session_state.get(wkey("is_peds"), auto_peds)), key=wkey("is_peds_tgl"))
    else:
        is_peds = auto_peds
    st.session_state[wkey("is_peds")] = is_peds
    st.caption(("현재 모드: **소아**" if is_peds else "현재 모드: **성인**") + (" (자동)" if not manual_override else " (수동)"))

# ---------- Caregiver notes (소아 보호자 설명) ----------
def render_caregiver_notes_peds(*, stool, fever, persistent_vomit, oliguria,
                                cough, nasal, eye, abd_pain, ear_pain, rash,
                                hives, migraine, hfmd):
    st.markdown("---")
    st.subheader("보호자 설명 (증상별)")

    def bullet(title, body):
        st.markdown(f"**{title}**")
        st.markdown(body.strip())

    if stool in ["3~4회","5~6회","7회 이상"]:
        bullet("💧 설사/장염 의심",
        """
- 하루 **3회 이상 묽은 변** → 장염 가능성
- **노란/초록 변**, **거품 많고 냄새 심함** → 로타/노로바이러스 고려
- **대처**: ORS·미음/쌀죽 등 수분·전해질 보충
- **즉시 진료**: 피 섞인 변, 고열, 소변 거의 없음/축 늘어짐
        """)
    if fever in ["38~38.5","38.5~39","39 이상"]:
        bullet("🌡️ 발열 대처",
        """
- 옷은 가볍게, 실내 시원하게(과도한 땀내기 X)
- **미온수 마사지**는 잠깐만
- **해열제 간격**: 아세트아미노펜 ≥4h, 이부프로펜 ≥6h
        """)
    if persistent_vomit:
        bullet("🤢 구토 지속",
        """
- 10~15분마다 **소량씩 수분**(ORS/미지근한 물)
- 우유·기름진 음식 일시 회피
- **즉시 진료**: 6시간 이상 물도 못 마심 / 초록·커피색 토물 / 혈토
        """)
    if oliguria:
        bullet("🚨 탈수 의심(소변량 급감)",
        """
- 입술 마름, 눈물 없음, 피부 탄력 저하, 축 늘어짐 동반 시 **중등~중증** 가능
- **ORS 빠르게 보충**, 호전 없으면 진료
        """)
    if cough in ["조금","보통","심함"] or nasal in ["진득","누런"]:
        bullet("🤧 기침·콧물(상기도감염)",
        """
- **생리식염수/흡인기**로 콧물 제거, 수면 시 머리 높이기
- **즉시 진료**: 숨차함/청색증/가슴함몰
        """)
    if eye in ["노랑-농성","양쪽"]:
        bullet("👀 결막염 의심",
        """
- 손 위생 철저, 분비물은 깨끗이 닦기
- **양쪽·고열·눈 통증/빛 통증** → 진료 권장
        """)
    if abd_pain:
        bullet("😣 복통/배 마사지 거부",
        """
- 우하복부 통증·보행 악화·구토/발열 동반 → **충수염 평가**
- 혈변/흑변 동반 → **즉시 진료**
        """)
    if ear_pain:
        bullet("👂 귀 통증(중이염 의심)",
        """
- 눕기 불편 시 **머리 살짝 높이기**
- 38.5℃↑, 지속 통증, **귀 분비물** → 진료 필요
        """)
    if rash:
        bullet("🩹 발진/두드러기(가벼움)",
        """
- **미온 샤워**, 면 소재 옷, 시원한 로션
- 새로운 음식/약 후 시작했는지 확인
        """)
    if hives:
        bullet("⚠️ 두드러기/알레르기(주의)",
        """
- 전신 두드러기/입술·눈 주위 부종/구토·복통 동반 시 알레르기 가능
- **호흡곤란/쌕쌕/목 조임** → **즉시 응급실**
        """)
    if migraine:
        bullet("🧠 편두통 의심",
        """
- **한쪽·박동성 두통**, **빛/소리 민감**, **구역감**
- 어두운 곳 휴식, 수분 보충
- **번개치듯 새로 시작한 극심한 두통**/신경학적 이상 → 응급평가
        """)
    if hfmd:
        bullet("✋👣 수족구 의심(HFMD)",
        """
- **손·발·입 안** 물집/궤양 + 발열
- 전염성: 손 씻기/식기 구분
- **탈수(소변 감소·축 늘어짐)**, **고열 >3일**, **경련/무기력** → 진료 필요
        """)
    st.info("❗ 즉시 병원 평가: 번개치는 두통 · 시야 이상/복시/암점 · 경련 · 의식저하 · 심한 목 통증 · 호흡곤란/입술부종")

# ---------- Tabs ----------
tab_labels = ["🏠 홈","🧪 피수치 입력","🧬 암 선택","💊 항암제(진단 기반)","👶 소아 증상","🔬 특수검사","📄 보고서"]
t_home, t_labs, t_dx, t_chemo, t_peds, t_special, t_report = st.tabs(tab_labels)

# HOME
with t_home:
    st.subheader("응급도 요약")
    labs = st.session_state.get("labs_dict", {})
    level_tmp, reasons_tmp, contrib_tmp = emergency_level(
        labs, st.session_state.get(wkey("cur_temp")), st.session_state.get(wkey("cur_hr")), {}
    )
    if level_tmp.startswith("🚨"): st.error("현재 상태: " + level_tmp)
    elif level_tmp.startswith("🟧"): st.warning("현재 상태: " + level_tmp)
    else: st.info("현재 상태: " + level_tmp)

    st.markdown("---")
    st.subheader("응급도 체크(증상 기반)")
    c1,c2,c3,c4,c5,c6 = st.columns(6)
    with c1: hematuria = st.checkbox("혈뇨", key=wkey("sym_hematuria"))
    with c2: melena = st.checkbox("흑색변", key=wkey("sym_melena"))
    with c3: hematochezia = st.checkbox("혈변", key=wkey("sym_hematochezia"))
    with c4: chest_pain = st.checkbox("흉통", key=wkey("sym_chest"))
    with c5: dyspnea = st.checkbox("호흡곤란", key=wkey("sym_dyspnea"))
    with c6: confusion = st.checkbox("의식저하", key=wkey("sym_confusion"))
    d1,d2,d3 = st.columns(3)
    with d1: oliguria = st.checkbox("소변량 급감", key=wkey("sym_oliguria"))
    with d2: persistent_vomit = st.checkbox("지속 구토(>6시간)", key=wkey("sym_pvomit"))
    with d3: petechiae = st.checkbox("점상출혈", key=wkey("sym_petechiae"))
    e1,e2 = st.columns(2)
    with e1: thunderclap = st.checkbox("번개치는 듯한 두통(Thunderclap)", key=wkey("sym_thunderclap"))
    with e2: visual_change = st.checkbox("시야 이상/복시/암점", key=wkey("sym_visual_change"))

    sym = dict(
        hematuria=hematuria, melena=melena, hematochezia=hematochezia,
        chest_pain=chest_pain, dyspnea=dyspnea, confusion=confusion,
        oliguria=oliguria, persistent_vomit=persistent_vomit, petechiae=petechiae,
        thunderclap=thunderclap, visual_change=visual_change,
    )

    alerts = []
    a = _try_float((labs or {}).get("ANC"))
    p = _try_float((labs or {}).get("PLT"))
    if thunderclap or (visual_change and (confusion or chest_pain or dyspnea)):
        alerts.append("🧠 **신경계 위중 의심** — 번개치듯 두통/시야 이상/의식장애 → 즉시 응급평가")
    if (a is not None and a < 500) and (_try_float(st.session_state.get(wkey("cur_temp"))) and _try_float(st.session_state.get(wkey("cur_temp"))) >= 38.0):
        alerts.append("🔥 **발열성 호중구감소증 의심** — ANC<500 + 발열 → 즉시 항생제 평가")
    if (p is not None and p < 20000) and (melena or hematochezia or petechiae):
        alerts.append("🩸 **출혈 고위험** — 혈소판<20k + 출혈징후 → 즉시 병원")
    if oliguria and persistent_vomit:
        alerts.append("💧 **중등~중증 탈수 가능** — 소변 급감 + 지속 구토 → 수액 고려")
    if chest_pain and dyspnea:
        alerts.append("❤️ **흉통+호흡곤란** — 응급평가 권장")
    if alerts:
        for msg in alerts: st.error(msg)
    else:
        st.info("위험 조합 경고 없음")

    level, reasons, contrib = emergency_level(
        labs, st.session_state.get(wkey("cur_temp")), st.session_state.get(wkey("cur_hr")), sym
    )
    if level.startswith("🚨"): st.error("응급도: " + level + " — " + " · ".join(reasons))
    elif level.startswith("🟧"): st.warning("응급도: " + level + " — " + " · ".join(reasons))
    else: st.info("응급도: " + level + (" — " + " · ".join(reasons) if reasons else ""))

    st.markdown("---")
    st.subheader("응급도 가중치 (편집 + 프리셋)")
    colp = st.columns(3)
    with colp[0]:
        preset_name = st.selectbox("프리셋 선택", list(PRESETS.keys()), key=wkey("preset_sel"))
    with colp[1]:
        if st.button("프리셋 적용", key=wkey("preset_apply")):
            set_weights(PRESETS[preset_name]); st.success(f"'{preset_name}' 가중치를 적용했습니다.")
    with colp[2]:
        if st.button("기본값으로 초기화", key=wkey("preset_reset")):
            set_weights(DEFAULT_WEIGHTS); st.info("가중치를 기본값으로 되돌렸습니다.")
    W = get_weights()
    grid = [
        ("ANC<500","w_anc_lt500"), ("ANC 500~999","w_anc_500_999"),
        ("발열 38.0~38.4","w_temp_38_0_38_4"), ("고열 ≥38.5","w_temp_ge_38_5"),
        ("혈소판 <20k","w_plt_lt20k"), ("중증빈혈 Hb<7","w_hb_lt7"),
        ("CRP ≥10","w_crp_ge10"), ("HR>130","w_hr_gt130"),
        ("혈뇨","w_hematuria"), ("흑색변","w_melena"), ("혈변","w_hematochezia"),
        ("흉통","w_chest_pain"), ("호흡곤란","w_dyspnea"), ("의식저하","w_confusion"),
        ("소변량 급감","w_oliguria"), ("지속 구토","w_persistent_vomit"), ("점상출혈","w_petechiae"),
        ("번개두통","w_thunderclap"), ("시야 이상","w_visual_change"),
    ]
    cols = st.columns(3); newW = dict(W)
    for i,(label,keyid) in enumerate(grid):
        with cols[i%3]:
            newW[keyid] = st.slider(label, 0.0, 3.0, float(W.get(keyid,1.0)), 0.1, key=wkey(f"w_{keyid}"))
    if newW != W:
        set_weights(newW); st.success("가중치 변경 사항 저장됨.")

# LABS
def _normalize_abbr(k: str) -> str:
    k = (k or "").strip().upper().replace(" ", "")
    alias = {"TP":"T.P", "TB":"T.B", "WBC":"WBC","HB":"Hb","PLT":"PLT","ANC":"ANC",
             "CRP":"CRP","NA":"Na","CR":"Cr","GLU":"Glu","CA":"Ca","P":"P",
             "AST":"AST","ALT":"ALT","TBIL":"T.B","ALB":"Alb","BUN":"BUN"}
    return alias.get(k, k)

LAB_REF_ADULT = {"WBC": (4.0, 10.0), "Hb": (12.0, 16.0), "PLT": (150, 400),
    "ANC": (1500, 8000), "CRP": (0.0, 5.0), "Na": (135, 145),
    "Cr": (0.5, 1.2), "Glu": (70, 140), "Ca": (8.6, 10.2),
    "P": (2.5, 4.5), "T.P": (6.4, 8.3), "AST": (0, 40), "ALT": (0, 41),
    "T.B": (0.2, 1.2), "Alb": (3.5, 5.0), "BUN": (7, 20)}
LAB_REF_PEDS = {"WBC": (5.0, 14.0), "Hb": (11.0, 15.0), "PLT": (150, 450),
    "ANC": (1500, 8000), "CRP": (0.0, 5.0), "Na": (135, 145),
    "Cr": (0.2, 0.8), "Glu": (70, 140), "Ca": (8.8, 10.8),
    "P": (4.0, 6.5), "T.P": (6.0, 8.0), "AST": (0, 50), "ALT": (0, 40),
    "T.B": (0.2, 1.2), "Alb": (3.8, 5.4), "BUN": (5, 18)}
def lab_ref(is_peds: bool): return LAB_REF_PEDS if is_peds else LAB_REF_ADULT
def lab_validate(abbr: str, val, is_peds: bool):
    rng = lab_ref(is_peds).get(abbr)
    if rng is None or val in (None, ""): return None
    try: v = float(val)
    except Exception: return "형식 오류"
    lo, hi = rng
    if v < lo: return f"⬇️ 기준치 미만({lo}~{hi})"
    if v > hi: return f"⬆️ 기준치 초과({lo}~{hi})"
    return "정상범위"

with t_labs:
    st.subheader("피수치 입력 — 붙여넣기 지원 (견고)")
    st.caption("예: 'WBC: 4.5', 'Hb 12.3', 'PLT, 200', 'Na 140 mmol/L'…")

    auto_is_peds = bool(st.session_state.get(wkey("is_peds"), False))
    st.toggle("소아 기준 자동 적용(나이 기반)", value=True, key=wkey("labs_auto_mode"))
    if st.session_state.get(wkey("labs_auto_mode")):
        use_peds = auto_is_peds
    else:
        use_peds = st.checkbox("소아 기준(참조범위/검증)", value=auto_is_peds, key=wkey("labs_use_peds_manual"))

    order = [("WBC","백혈구"), ("Ca","칼슘"), ("Glu","혈당"), ("CRP","CRP"),
             ("Hb","혈색소"), ("P","인(Phosphorus)"), ("T.P","총단백"), ("Cr","크레아티닌"),
             ("PLT","혈소판"), ("Na","나트륨"), ("AST","AST"), ("T.B","총빌리루빈"),
             ("ANC","절대호중구"), ("Alb","알부민"), ("ALT","ALT"), ("BUN","BUN")]
    with st.expander("📋 검사값 붙여넣기(자동 인식)", expanded=False):
        pasted = st.text_area("예: WBC: 4.5\nHb 12.3\nPLT, 200\nNa 140 mmol/L", height=120, key=wkey("labs_paste"))
        if st.button("붙여넣기 파싱 → 적용", key=wkey("parse_paste")):
            parsed = {}
            try:
                if pasted:
                    for line in str(pasted).splitlines():
                        s = line.strip()
                        if not s: continue
                        parts = re.split(r'[:;,\t\-=\u00b7\u2022]| {2,}', s)
                        parts = [p for p in parts if p.strip()]
                        if len(parts) >= 2:
                            k = _normalize_abbr(parts[0]); v = _try_float(parts[1])
                            if k and (v is not None): parsed[k] = v; continue
                        toks = s.split()
                        if len(toks) >= 2:
                            k = _normalize_abbr(toks[0]); v = _try_float(" ".join(toks[1:]))
                            if k and (v is not None): parsed[k] = v
                if parsed:
                    for abbr,_ in order:
                        if abbr in parsed: st.session_state[wkey(abbr)] = parsed[abbr]
                    st.success(f"적용됨: {', '.join(list(parsed.keys())[:12])} ...")
                else:
                    st.info("인식 가능한 수치를 찾지 못했습니다. 줄마다 '항목 값' 형태인지 확인해주세요.")
            except Exception:
                st.error("파싱 중 예외가 발생했지만 앱은 계속 동작합니다. 입력 형식을 다시 확인하세요.")

    cols = st.columns(4); values = {}
    for i,(abbr,kor) in enumerate(order):
        with cols[i%4]:
            val = st.text_input(f"{abbr} — {kor}", value=str(st.session_state.get(wkey(abbr), "")), key=wkey(abbr))
            values[abbr] = _try_float(val)
            msg = lab_validate(abbr, values[abbr], use_peds)
            if msg: st.caption(("✅ " if msg=="정상범위" else "⚠️ ")+msg)
    labs_dict = st.session_state.get("labs_dict", {}); labs_dict.update(values)
    st.session_state["labs_dict"] = labs_dict
    st.markdown(f"**참조범위 기준:** {'소아' if use_peds else '성인'} / **ANC 분류:** {anc_band(values.get('ANC'))}")

# DX
with t_dx:
    st.subheader("암 선택")
    if not ONCO:
        st.warning("onco_map 이 로드되지 않아 기본 목록이 비어있습니다. onco_map.py를 같은 폴더나 modules/ 에 두세요.")
    groups = sorted(ONCO.keys()) if ONCO else ["혈액암","고형암"]
    group = st.selectbox("암 그룹", options=groups, index=0, key=wkey("onco_group_sel"))
    diseases = sorted(ONCO.get(group, {}).keys()) if ONCO else ["ALL","AML","Lymphoma","Breast","Colon","Lung"]
    disease = st.selectbox("의심/진단명", options=diseases, index=0, key=wkey("onco_disease_sel"))
    disp = dx_display(group, disease)
    st.session_state["onco_group"] = group
    st.session_state["onco_disease"] = disease
    st.session_state["dx_disp"] = disp
    st.info(f"선택: {disp}")

    recs = auto_recs_by_dx(group, disease, DRUG_DB) or {}
    if any(recs.values()):
        st.markdown("**자동 추천 요약**")
        for cat, arr in recs.items():
            if not arr: continue
            st.write(f"- {cat}: " + ", ".join(arr))
    st.session_state["recs_by_dx"] = recs

# ---------- Chemo interactions ----------
def _to_set_or_empty(x):
    s = set()
    if not x: return s
    if isinstance(x, str):
        for p in re.split(r"[;,/]|\\s+", x):
            p = p.strip().lower()
            if p: s.add(p)
    elif isinstance(x, (list, tuple, set)):
        for p in x:
            p = str(p).strip().lower()
            if p: s.add(p)
    elif isinstance(x, dict):
        for k,v in x.items():
            s.add(str(k).strip().lower())
            if isinstance(v, (list,tuple,set)): s |= {str(t).strip().lower() for t in v}
    return s

def _meta_for_drug(key):
    rec = DRUG_DB.get(key, {}) if isinstance(DRUG_DB, dict) else {}
    klass = str(rec.get("class","")).strip().lower()
    tags  = _to_set_or_empty(rec.get("tags")) | _to_set_or_empty(rec.get("tag")) | _to_set_or_empty(rec.get("properties"))
    if "qt" in tags or "qt_prolong" in tags or "qt-prolong" in tags: tags.add("qt_prolong")
    if "myelo" in tags or "myelosuppression" in tags: tags.add("myelosuppression")
    if "io" in tags or "immunotherapy" in tags or "pd-1" in tags or "pd-l1" in tags or "ctla-4" in tags:
        tags.add("immunotherapy")
    if "steroid" in tags or "corticosteroid" in tags: tags.add("steroid")
    inter = rec.get("interactions") or rec.get("ddi") or rec.get("drug_interactions")
    inter_list = []
    if isinstance(inter, str):
        inter_list = [s.strip() for s in re.split(r"[\\n;,]", inter) if s.strip()]
    elif isinstance(inter, (list, tuple)):
        inter_list = [str(s).strip() for s in inter if str(s).strip()]
    warning = rec.get("warnings") or rec.get("warning") or rec.get("boxed_warning") or ""
    return {"class": klass, "tags": tags, "interactions": inter_list, "warning": warning, "raw": rec}

def check_chemo_interactions(keys):
    warns = []; notes = []
    if not keys: return warns, notes
    metas = {k: _meta_for_drug(k) for k in keys}
    classes = {}
    for k, m in metas.items():
        if not m["class"]: continue
        classes.setdefault(m["class"], []).append(k)
    for klass, arr in classes.items():
        if len(arr) >= 2 and klass not in ("antiemetic","hydration"):
            warns.append(f"동일 계열 **{klass}** 약물 중복({', '.join(arr)}) — 누적 독성 주의")
    qt_list = [k for k,m in metas.items() if "qt_prolong" in m["tags"]]
    if len(qt_list) >= 2:
        warns.append(f"**QT 연장 위험** 약물 다수 병용({', '.join(qt_list)}) — EKG/전해질 모니터링")
    myelo_list = [k for k,m in metas.items() if "myelosuppression" in m["tags"]]
    if len(myelo_list) >= 2:
        warns.append(f"**강한 골수억제 병용**({', '.join(myelo_list)}) — 감염/출혈 위험 ↑")
    if any("immunotherapy" in m["tags"] for m in metas.values()) and any("steroid" in m["tags"] for m in metas.values()):
        warns.append("**면역항암제 + 스테로이드** 병용 — 면역반응 저하 가능 (임상적 필요 시 예외)")
    for k, m in metas.items():
        for it in m["interactions"]:
            notes.append(f"- {k}: {it}")
        if m["warning"]:
            notes.append(f"- {k} [경고]: {m['warning']}")
    return warns, notes

# CHEMO
def _aggregate_all_aes(meds, db):
    result = {}
    if not isinstance(meds, (list, tuple)) or not meds:
        return result
    ae_fields = ["ae","ae_ko","adverse_effects","adverse","side_effects","side_effect",
                 "warnings","warning","black_box","boxed_warning","toxicity","precautions",
                 "safety","safety_profile","notes"]
    for k in meds:
        rec = db.get(k) if isinstance(db, dict) else None
        lines = []
        if isinstance(rec, dict):
            for field in ae_fields:
                v = rec.get(field)
                if not v: continue
                if isinstance(v, str):
                    parts = []
                    for chunk in v.split("\n"):
                        for semi in chunk.split(";"):
                            parts.extend([p.strip() for p in semi.split(",")])
                    lines += [p for p in parts if p]
                elif isinstance(v, (list, tuple)):
                    tmp = []
                    for s in v:
                        for p in str(s).split(","):
                            q = p.strip()
                            if q: tmp.append(q)
                    lines += tmp
        seen = set(); uniq = []
        for s in lines:
            if s not in seen:
                uniq.append(s); seen.add(s)
        if uniq:
            result[k] = uniq
    return result

with t_chemo:
    st.subheader("항암제(진단 기반)")
    group = st.session_state.get("onco_group")
    disease = st.session_state.get("onco_disease")
    recs = st.session_state.get("recs_by_dx", {}) or {}

    rec_chemo = list(dict.fromkeys(recs.get("chemo", []))) if recs else []
    rec_target = list(dict.fromkeys(recs.get("targeted", []))) if recs else []
    recommended = rec_chemo + [x for x in rec_target if x not in rec_chemo]

    def _indicates(rec: dict, disease: str):
        if not isinstance(rec, dict) or not disease: return False
        keys = ["indications","indication","for","dx","uses"]
        s = " ".join([str(rec.get(k,"")) for k in keys])
        return (disease.lower() in s.lower()) if s else False

    if (not recommended) and DRUG_DB and disease:
        for k, rec in DRUG_DB.items():
            try:
                if _indicates(rec, disease): recommended.append(k)
            except Exception:
                pass

    label_map = {k: display_label(k, DRUG_DB) for k in DRUG_DB.keys()} if DRUG_DB else {}

    show_all = st.toggle("전체 보기(추천 외 약물 포함)", value=False, key=wkey("chemo_show_all"))
    if show_all or not recommended:
        pool_keys = sorted(label_map.keys()); st.caption("현재: 전체 약물 목록에서 선택")
    else:
        pool_keys = recommended; st.caption("현재: 진단 기반 추천 목록에서 선택")

    pool_labels = [label_map.get(k, str(k)) for k in pool_keys]
    unique_pairs = sorted(set(zip(pool_labels, pool_keys)), key=lambda x: x[0].lower())
    pool_labels_sorted = [p[0] for p in unique_pairs]
    picked_labels = st.multiselect("투여/계획 약물 선택", options=pool_labels_sorted, key=wkey("drug_pick"))
    label_to_key = {lbl: key for lbl, key in unique_pairs}
    picked_keys = [label_to_key.get(lbl) for lbl in picked_labels if lbl in label_to_key]
    st.session_state["chemo_keys"] = picked_keys

    if picked_keys:
        st.markdown("### 선택 약물")
        for k in picked_keys:
            st.write("- " + label_map.get(k, str(k)))

        warns, notes = check_chemo_interactions(picked_keys)
        if warns:
            st.markdown("### ⚠️ 병용 주의/경고")
            for w in warns: st.error(w)
        if notes:
            st.markdown("### ℹ️ 참고(데이터베이스 기재)")
            for n in notes: st.info(n)

        ae_map = _aggregate_all_aes(picked_keys, DRUG_DB)
        st.markdown("### 항암제 부작용(전체)")
        if ae_map:
            for k, arr in ae_map.items():
                st.write(f"- **{label_map.get(k, str(k))}**")
                for ln in arr:
                    st.write(f"  - {ln}")
        else:
            st.write("- (DB에 상세 부작용 없음)")

# PEDS
with t_peds:
    st.subheader("소아 증상 기반 점수 + 보호자 설명 + 해열제 계산")
    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: nasal = st.selectbox("콧물", ["없음","투명","진득","누런"], key=wkey("p_nasal"))
    with c2: cough = st.selectbox("기침", ["없음","조금","보통","심함"], key=wkey("p_cough"))
    with c3: stool = st.selectbox("설사", ["없음","1~2회","3~4회","5~6회","7회 이상"], key=wkey("p_stool"))
    with c4: fever = st.selectbox("발열", ["없음","37~37.5 (미열)","37.5~38","38~38.5","38.5~39","39 이상"], key=wkey("p_fever"))
    with c5: eye   = st.selectbox("눈꼽/결막", ["없음","맑음","노랑-농성","양쪽"], key=wkey("p_eye"))

    d1,d2,d3 = st.columns(3)
    with d1: oliguria = st.checkbox("소변량 급감", key=wkey("p_oliguria"))
    with d2: persistent_vomit = st.checkbox("지속 구토(>6시간)", key=wkey("p_pvomit"))
    with d3: petechiae = st.checkbox("점상출혈", key=wkey("p_petechiae"))

    e1,e2,e3 = st.columns(3)
    with e1: abd_pain = st.checkbox("복통/배마사지 거부", key=wkey("p_abd_pain"))
    with e2: ear_pain = st.checkbox("귀 통증/만지면 울음", key=wkey("p_ear_pain"))
    with e3: rash     = st.checkbox("가벼운 발진/두드러기", key=wkey("p_rash"))

    f1,f2,f3 = st.columns(3)
    with f1: hives    = st.checkbox("두드러기·알레르기 의심(전신/입술부종 등)", key=wkey("p_hives"))
    with f2: migraine = st.checkbox("편두통 의심(한쪽·박동성·빛/소리 민감)", key=wkey("p_migraine"))
    with f3: hfmd     = st.checkbox("수족구 의심(손발·입 병변)", key=wkey("p_hfmd"))

    score = {"장염 의심":0, "상기도/독감 계열":0, "결막염 의심":0, "탈수/신장 문제":0,
             "출혈성 경향":0, "중이염/귀질환":0, "피부발진/경미한 알레르기":0,
             "복통 평가":0, "알레르기 주의":0, "편두통 의심":0, "수족구 의심":0}
    if stool in ["3~4회","5~6회","7회 이상"]:
        score["장염 의심"] += {"3~4회":40,"5~6회":55,"7회 이상":70}[stool]
    if fever in ["38~38.5","38.5~39","39 이상"]: score["상기도/독감 계열"] += 25
    if cough in ["조금","보통","심함"]: score["상기도/독감 계열"] += 20
    if eye in ["노랑-농성","양쪽"]: score["결막염 의심"] += 30
    if oliguria: score["탈수/신장 문제"] += 40; score["장염 의심"] += 10
    if persistent_vomit: score["장염 의심"] += 25; score["탈수/신장 문제"] += 15; score["복통 평가"] += 10
    if petechiae: score["출혈성 경향"] += 60
    if ear_pain: score["중이염/귀질환"] += 35
    if rash: score["피부발진/경미한 알레르기"] += 25
    if abd_pain: score["복통 평가"] += 25
    if hives: score["알레르기 주의"] += 60
    if migraine: score["편두통 의심"] += 35
    if hfmd: score["수족구 의심"] += 40

    ordered = sorted(score.items(), key=lambda x: x[1], reverse=True)
    st.write("• " + " / ".join([f"{k}: {v}" for k,v in ordered if v>0]) if any(v>0 for _,v in ordered) else "• 특이 점수 없음")

    st.markdown("---")
    st.subheader("해열제 계산기")
    prev_wt = st.session_state.get(wkey("wt_peds"), 0.0)
    default_wt = _safe_float(prev_wt, 0.0)
    wt = st.number_input("체중(kg)", min_value=0.0, max_value=200.0, value=default_wt, step=0.1, key=wkey("wt_peds_num"))
    st.session_state[wkey("wt_peds")] = wt
    try:
        ap_ml_1, ap_ml_max = acetaminophen_ml(wt)
        ib_ml_1, ib_ml_max = ibuprofen_ml(wt)
    except Exception:
        ap_ml_1, ap_ml_max, ib_ml_1, ib_ml_max = (0.0,0.0,0.0,0.0)
    colA, colB = st.columns(2)
    with colA: st.write(f"아세트아미노펜 1회 권장량: **{ap_ml_1:.1f} mL** (최대 {ap_ml_max:.1f} mL)")
    with colB: st.write(f"이부프로펜 1회 권장량: **{ib_ml_1:.1f} mL** (최대 {ib_ml_max:.1f} mL)")
    st.caption("쿨다운: APAP ≥4h, IBU ≥6h. 중복 복용 주의.")
    st.markdown("---")
    st.subheader("보호자 설명")
    render_caregiver_notes_peds(
        stool=stool, fever=fever, persistent_vomit=persistent_vomit, oliguria=oliguria,
        cough=cough, nasal=nasal, eye=eye, abd_pain=abd_pain, ear_pain=ear_pain, rash=rash,
        hives=hives, migraine=migraine, hfmd=hfmd
    )

# SPECIAL (간단 각주 매핑)
def _annotate_special_notes(lines):
    if not lines: return []
    notes_map = {
        r"procalcitonin|pct": "세균성 감염 지표로 사용 — 해석은 임상 맥락 필수",
        r"d[- ]?dimer": "혈전/색전 의심 시 상승 — 비특이적",
        r"ferritin": "염증/HLH/철대사 이상 평가에 참고",
        r"troponin": "심근 손상 지표 — 신장기능/수술 등도 영향",
        r"bnp|nt[- ]?pro[- ]?bnp": "심부전 가능성 평가 — 연령/신장기능 고려",
        r"crp": "염증 비특이 지표 — 추세로 평가",
    }
    out = []
    for ln in lines:
        added = False
        for pat, note in notes_map.items():
            if re.search(pat, ln, flags=re.I):
                out.append(f"{ln} — [참고] {note}")
                added = True
                break
        if not added:
            out.append(ln)
    return out

with t_special:
    st.subheader("특수검사 해석")
    if SPECIAL_PATH: st.caption(f"special_tests 로드: {SPECIAL_PATH}")
    lines = special_tests_ui()
    lines = _annotate_special_notes(lines or [])
    st.session_state['special_interpretations'] = lines
    if lines:
        for ln in lines: st.write("- " + ln)
    else:
        st.info("아직 입력/선택이 없습니다.")

# ---------- QR helper ----------
def _build_hospital_summary():
    key_id   = st.session_state.get("key","(미설정)")
    labs     = st.session_state.get("labs_dict", {}) or {}
    temp     = st.session_state.get(wkey("cur_temp")) or "—"
    hr       = st.session_state.get(wkey("cur_hr")) or "—"
    group    = st.session_state.get("onco_group","") or "—"
    disease  = st.session_state.get("onco_disease","") or "—"
    meds     = st.session_state.get("chemo_keys", []) or []
    sym_keys = ["sym_hematuria","sym_melena","sym_hematochezia","sym_chest","sym_dyspnea",
                "sym_confusion","sym_oliguria","sym_pvomit","sym_petechiae","sym_thunderclap","sym_visual_change"]
    sym_kor  = ["혈뇨","흑색변","혈변","흉통","호흡곤란","의식저하","소변량 급감","지속 구토","점상출혈","번개두통","시야 이상"]
    sym_line = ", ".join([nm for nm, kk in zip(sym_kor, sym_keys) if st.session_state.get(wkey(kk), False)]) or "해당 없음"
    pick = ["WBC","Hb","PLT","ANC","CRP","Na","K","Ca","Cr","BUN","AST","ALT","T.B","Alb","Glu"]
    lab_parts = []
    for k in pick:
        v = labs.get(k)
        if v not in (None, ""):
            lab_parts.append(f"{k}:{v}")
    labs_line = ", ".join(lab_parts) if lab_parts else "—"
    meds_line = ", ".join(meds) if meds else "—"
    return f"[PIN]{key_id} | T:{temp}℃ HR:{hr} | Dx:{group}/{disease} | Sx:{sym_line} | Labs:{labs_line} | Chemo:{meds_line}"

def _qr_image_bytes(text: str) -> bytes:
    try:
        import qrcode
        img = qrcode.make(text)
        buf = io.BytesIO(); img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception:
        return b""  # 라이브러리 없으면 빈 바이트 반환

# REPORT with side panel (기록/그래프)
with t_report:
    st.subheader("보고서 (.md/.txt/.pdf) — 모든 항목 포함")

    # 공통 데이터
    key_id   = st.session_state.get("key","(미설정)")
    labs     = st.session_state.get("labs_dict", {}) or {}
    group    = st.session_state.get("onco_group","")
    disease  = st.session_state.get("onco_disease","")
    meds     = st.session_state.get("chemo_keys", [])
    diets    = lab_diet_guides(labs, heme_flag=(group=="혈액암"))
    temp = st.session_state.get(wkey("cur_temp"))
    hr   = st.session_state.get(wkey("cur_hr"))
    age_years = _safe_float(st.session_state.get(wkey("age_years")), 0.0)
    is_peds   = bool(st.session_state.get(wkey("is_peds"), False))

    sym_map = {
        "혈뇨": st.session_state.get(wkey("sym_hematuria"), False),
        "흑색변": st.session_state.get(wkey("sym_melena"), False),
        "혈변": st.session_state.get(wkey("sym_hematochezia"), False),
        "흉통": st.session_state.get(wkey("sym_chest"), False),
        "호흡곤란": st.session_state.get(wkey("sym_dyspnea"), False),
        "의식저하": st.session_state.get(wkey("sym_confusion"), False),
        "소변량 급감": st.session_state.get(wkey("sym_oliguria"), False),
        "지속 구토": st.session_state.get(wkey("sym_pvomit"), False),
        "점상출혈": st.session_state.get(wkey("sym_petechiae"), False),
        "번개치는 듯한 두통": st.session_state.get(wkey("sym_thunderclap"), False),
        "시야 이상/복시/암점": st.session_state.get(wkey("sym_visual_change"), False),
    }
    level, reasons, contrib = emergency_level(labs or {}, temp, hr, {
        "hematuria": sym_map["혈뇨"], "melena": sym_map["흑색변"], "hematochezia": sym_map["혈변"],
        "chest_pain": sym_map["흉통"], "dyspnea": sym_map["호흡곤란"], "confusion": sym_map["의식저하"],
        "oliguria": sym_map["소변량 급감"], "persistent_vomit": sym_map["지속 구토"], "petechiae": sym_map["점상출혈"],
        "thunderclap": sym_map["번개치는 듯한 두통"], "visual_change": sym_map["시야 이상/복시/암점"],
    })

    # 레이아웃: 왼쪽(보고서) · 오른쪽(기록/그래프)
    col_report, col_side = st.columns([2, 1])

    # ---------- 오른쪽: 기록/그래프 ----------
# ---------- 오른쪽: 기록/그래프(탭 분리) ----------
with col_side:
    st.markdown("### 📊 기록/그래프 패널")

    # 공용 상태
    st.session_state.setdefault("lab_history", [])
    hist = st.session_state["lab_history"]

    tab_log, tab_plot, tab_export = st.tabs(["📝 기록", "📈 그래프", "⬇️ 내보내기"])

    # -------------------- 📝 기록 탭 --------------------
    with tab_log:
        cols_btn = st.columns([1,1,1])
        with cols_btn[0]:
            if st.button("➕ 현재 값을 기록에 추가", key=wkey("add_history_tab")):
                snap = {
                    "ts": _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "temp": temp or "",
                    "hr": hr or "",
                    "labs": {k: ("" if labs.get(k) in (None,"") else labs.get(k)) for k in labs.keys()}
                }
                hist.append(snap)
                st.success("현재 값이 기록에 추가되었습니다.")
        with cols_btn[1]:
            if st.button("🗑️ 기록 비우기", key=wkey("clear_history")) and hist:
                st.session_state["lab_history"] = []
                hist = st.session_state["lab_history"]
                st.warning("기록을 모두 비웠습니다.")
        with cols_btn[2]:
            st.caption(f"총 {len(hist)}건")

        # 최근 10건 표시
        if not hist:
            st.info("기록이 없습니다.")
        else:
            try:
                import pandas as pd
                # 넓게 보이도록 핵심 항목만 요약표
                rows = []
                for h in hist[-10:]:
                    row = {
                        "시각": h.get("ts",""),
                        "T(℃)": h.get("temp",""),
                        "HR": h.get("hr",""),
                        "WBC": (h.get("labs",{}) or {}).get("WBC",""),
                        "Hb":  (h.get("labs",{}) or {}).get("Hb",""),
                        "PLT": (h.get("labs",{}) or {}).get("PLT",""),
                        "ANC": (h.get("labs",{}) or {}).get("ANC",""),
                        "CRP": (h.get("labs",{}) or {}).get("CRP",""),
                    }
                    rows.append(row)
                df = pd.DataFrame(rows)
                st.dataframe(df, use_container_width=True, height=280)
            except Exception:
                # pandas 없어도 동작
                st.write(hist[-5:])

    # -------------------- 📈 그래프 탭 --------------------
    with tab_plot:
        default_metrics = ["WBC","Hb","PLT","ANC","CRP","Na","Cr","BUN","AST","ALT","Glu"]
        all_metrics = sorted({*default_metrics, *list(labs.keys())})
        pick = st.multiselect("그래프 항목 선택", options=all_metrics,
                              default=default_metrics[:4], key=wkey("chart_metrics_tab"))

        if not hist:
            st.info("기록이 없습니다. 먼저 '기록' 탭에서 추가하세요.")
        elif not pick:
            st.info("표시할 항목을 선택하세요.")
        else:
            x = [h.get("ts","") for h in hist]

            if _HAS_MPL:
                import math
                # 항목별 단일 플롯(지시사항: 색/스타일 지정 안 함)
                for m in pick:
                    y = []
                    for h in hist:
                        v = (h.get("labs",{}) or {}).get(m, "")
                        try: v = float(str(v).replace(",", "."))
                        except Exception: v = None
                        y.append(v)
                    if all(v is None for v in y):  # 전부 결측이면 스킵
                        continue
                    fig = plt.figure()
                    plt.plot(x, [vv if vv is not None else float("nan") for vv in y], marker="o")
                    plt.title(m)
                    plt.xlabel("기록 시각")
                    plt.ylabel(m)
                    plt.xticks(rotation=45, ha="right")
                    plt.tight_layout()
                    st.pyplot(fig)
            else:
                # 폴백: Streamlit 내장 차트
                try:
                    import pandas as pd
                    df_rows = []
                    for i, h in enumerate(hist):
                        row = {"ts": x[i]}
                        for m in pick:
                            v = (h.get("labs",{}) or {}).get(m, None)
                            try: v = float(str(v).replace(",", "."))
                            except Exception: v = None
                            row[m] = v
                        df_rows.append(row)
                    if df_rows:
                        df = pd.DataFrame(df_rows).set_index("ts")
                        for m in pick:
                            st.line_chart(df[[m]])
                    else:
                        st.info("표시할 데이터가 없습니다.")
                except Exception:
                    st.warning("matplotlib/pandas 미설치 → 간단 표로 폴백합니다.")
                    for m in pick:
                        st.write(m, [ (x[i], (hist[i].get('labs',{}) or {}).get(m, None)) for i in range(len(hist)) ])

    # -------------------- ⬇️ 내보내기 탭 --------------------
    with tab_export:
        if not hist:
            st.info("기록이 없습니다.")
        else:
            output = io.StringIO()
            writer = csv.writer(output)
            # 가능한 모든 항목 헤더화
            all_keys = set()
            for h in hist:
                all_keys |= set((h.get("labs",{}) or {}).keys())
            all_keys = sorted(all_keys)
            headers = ["ts","temp","hr"] + all_keys
            writer.writerow(headers)
            for h in hist:
                row = [h.get("ts",""), h.get("temp",""), h.get("hr","")]
                for m in all_keys:
                    row.append((h.get("labs",{}) or {}).get(m, ""))
                writer.writerow(row)
            st.download_button("CSV 다운로드", data=output.getvalue().encode("utf-8"),
                               file_name="bloodmap_history.csv", mime="text/csv")
            st.caption("팁: 기록을 정리해서 외래/응급실에 공유할 때 CSV가 편합니다.")
    # ---------- 왼쪽: 보고서 본문 ----------
    with col_report:
        use_dflt = st.checkbox("기본(모두 포함)", True, key=wkey("rep_all"))
        colp1,colp2 = st.columns(2)
        with colp1:
            sec_profile = st.checkbox("프로필/활력/모드", True if use_dflt else False, key=wkey("sec_profile"))
            sec_symptom = st.checkbox("증상 체크(홈)", True if use_dflt else False, key=wkey("sec_symptom"))
            sec_emerg   = st.checkbox("응급도 평가(기여도/가중치 포함)", True if use_dflt else False, key=wkey("sec_emerg"))
            sec_dx      = st.checkbox("진단명(암 선택)", True if use_dflt else False, key=wkey("sec_dx"))
        with colp2:
            sec_meds    = st.checkbox("항암제 요약/부작용/병용경고", True if use_dflt else False, key=wkey("sec_meds"))
            sec_labs    = st.checkbox("피수치 전항목", True if use_dflt else False, key=wkey("sec_labs"))
            sec_diet    = st.checkbox("식이가이드", True if use_dflt else False, key=wkey("sec_diet"))
            sec_special = st.checkbox("특수검사 해석(각주)", True if use_dflt else False, key=wkey("sec_special"))

        # 병원 전달 요약 + QR
        st.markdown("### 🏥 병원 전달용 요약 + QR")
        qr_text = _build_hospital_summary()
        st.code(qr_text, language="text")
        qr_png = _qr_image_bytes(qr_text)
        if qr_png:
            st.image(qr_png, caption="이 QR을 스캔하면 위 요약 텍스트가 표시됩니다.", use_column_width=False)
            st.download_button("QR 이미지(.png) 다운로드", data=qr_png, file_name="bloodmap_hospital_qr.png", mime="image/png")
        else:
            st.info("QR 라이브러리를 찾지 못했습니다. 위 텍스트를 그대로 공유하세요. (선택: requirements에 `qrcode` 추가)")

        # 보고서 본문 생성
        lines = []
        lines.append("# Bloodmap Report (Full)")
        lines.append(f"_생성 시각(KST): {_dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_")
        lines.append("")
        lines.append("> In memory of Eunseo, a little star now shining in the sky.")
        lines.append("> This app is made with the hope that she is no longer in pain,")
        lines.append("> and resting peacefully in a world free from all hardships.")
        lines.append("")
        lines.append("---")
        lines.append("")

        if sec_profile:
            lines.append("## 프로필/활력/모드")
            lines.append(f"- 키(별명#PIN): {key_id}")
            lines.append(f"- 나이(년): {age_years}")
            lines.append(f"- 모드: {'소아' if is_peds else '성인'}")
            lines.append(f"- 체온(℃): {temp if temp not in (None, '') else '—'}")
            lines.append(f"- 심박수(bpm): {hr if hr not in (None, '') else '—'}")
            lines.append("")

        if sec_symptom:
            lines.append("## 증상 체크(홈)")
            for k,v in sym_map.items():
                lines.append(f"- {k}: {'예' if v else '아니오'}")
            lines.append("")

        if sec_emerg:
            lines.append("## 응급도 평가")
            lines.append(f"- 현재 응급도: {level}")
            if reasons:
                for r in reasons: lines.append(f"  - {r}")
            if contrib:
                lines.append("### 응급도 기여도(Why)")
                total = sum(x["score"] for x in contrib) or 1.0
                for it in sorted(contrib, key=lambda x:-x["score"]):
                    pct = round(100.0*it["score"]/total,1)
                    lines.append(f"- {it['factor']}: 점수 {round(it['score'],2)} (기본{it['base']}×가중치{it['weight']}, {pct}%)")
            lines.append("")
            lines.append("### 사용한 가중치")
            for k,v in get_weights().items():
                lines.append(f"- {k}: {v}")
            lines.append("")

        if sec_dx:
            lines.append("## 진단명(암)")
            lines.append(f"- 그룹: {group or '(미선택)'}")
            lines.append(f"- 질환: {disease or '(미선택)'}")
            lines.append("")

        if sec_meds:
            lines.append("## 항암제 요약")
            if meds:
                for m in meds:
                    try: lines.append(f"- {display_label(m, DRUG_DB)}")
                    except Exception: lines.append(f"- {m}")
            else:
                lines.append("- (없음)")
            lines.append("")

            warns, notes = check_chemo_interactions(meds)
            if warns:
                lines.append("### ⚠️ 병용 주의/경고")
                for w in warns: lines.append(f"- {w}")
                lines.append("")
            if notes:
                lines.append("### ℹ️ 참고(데이터베이스 기재)")
                for n in notes: lines.append(n)
                lines.append("")

            if meds:
                ae_map = _aggregate_all_aes(meds, DRUG_DB)
                if ae_map:
                    lines.append("## 항암제 부작용(전체)")
                    for k, arr in ae_map.items():
                        try: nm = display_label(k, DRUG_DB)
                        except Exception: nm = k
                        lines.append(f"- {nm}")
                        for ln in arr: lines.append(f"  - {ln}")
                    lines.append("")

        if sec_labs:
            lines.append("## 피수치 (모든 항목)")
            all_labs = [("WBC","백혈구"),("Ca","칼슘"),("Glu","혈당"),("CRP","CRP"),
                        ("Hb","혈색소"),("P","인(Phosphorus)"),("T.P","총단백"),("Cr","크레아티닌"),
                        ("PLT","혈소판"),("Na","나트륨"),("AST","AST"),("T.B","총빌리루빈"),
                        ("ANC","절대호중구"),("Alb","알부민"),("ALT","ALT"),("BUN","BUN")]
            for abbr, kor in all_labs:
                v = labs.get(abbr) if isinstance(labs, dict) else None
                lines.append(f"- {abbr} ({kor}): {v if v not in (None, '') else '—'}")
            lines.append(f"- ANC 분류: {anc_band(labs.get('ANC') if isinstance(labs, dict) else None)}")
            lines.append("")

        if sec_diet:
            dlist = diets or []
            if dlist:
                lines.append("## 식이가이드(자동)")
                for d in dlist: lines.append(f"- {d}")
                lines.append("")

        if sec_special:
            spec_lines = st.session_state.get('special_interpretations', [])
            if spec_lines:
                lines.append("## 특수검사 해석(각주 포함)")
                for ln in spec_lines: lines.append(f"- {ln}")
                lines.append("")

        lines.append("---")
        lines.append("### 🏥 병원 전달용 텍스트 (QR 동일 내용)")
        lines.append(_build_hospital_summary())
        lines.append("")

        md = "\n".join(lines)
        st.code(md, language="markdown")
        st.download_button("💾 보고서 .md 다운로드", data=md.encode("utf-8"),
                           file_name="bloodmap_report.md", mime="text/markdown")
        txt_data = md.replace('**','')
        st.download_button("📝 보고서 .txt 다운로드", data=txt_data.encode("utf-8"),
                           file_name="bloodmap_report.txt", mime="text/plain")
        try:
            pdf_bytes = export_md_to_pdf(md)
            st.download_button("📄 보고서 .pdf 다운로드", data=pdf_bytes,
                               file_name="bloodmap_report.pdf", mime="application/pdf")
        except Exception:
            st.caption("PDF 변환 모듈을 불러오지 못했습니다. .md 또는 .txt를 사용해주세요.")
