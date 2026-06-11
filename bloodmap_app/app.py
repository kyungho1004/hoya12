import streamlit as st
import datetime as _dt
from zoneinfo import ZoneInfo as _ZoneInfo
import os, sys, re, io, csv
import importlib, types
import json
from pathlib import Path
import importlib.util

# ---- HomeBlocker v1 ----
def _block_spurious_home():
    ss = st.session_state
    cur = ss.get("_route") or "home"
    last = ss.get("_route_last")
    intent_home = ss.get("_home_intent", False)
    if (cur == "home") and (last and last != "home") and (not intent_home):
        ss["_route"] = last
        try:
            if st.query_params.get("route") != last:
                st.query_params.update(route=last)
        except Exception:
            st.experimental_set_query_params(route=last)
    try:
        if ss.get("_route") and ss["_route"] != "home":
            ss["_route_last"] = ss["_route"]
    except Exception:
        pass
# ---- End HomeBlocker v1 ----


# ---- Hard redirect guard v2 ----
try:
    def __hr_qp(name: str) -> str:
        try:
            v = st.query_params.get(name)
            return v[0] if isinstance(v, list) else (v or "")
        except Exception:
            v = st.experimental_get_query_params().get(name, [""])
            return v[0]

    url_route = __hr_qp("route")
    ss = st.session_state
    cur = ss.get("_route")
    last = ss.get("_route_last")

    if not ss.get("_hrg_v2_done", False):
        ss["_hrg_v2_done"] = True
        if url_route:
            want = url_route
            if cur != want:
                ss["_route"] = want
                ss["_route_last"] = want
                try:
                    if st.query_params.get("route") != want:
                        st.query_params.update(route=want)
                except Exception:
                    st.experimental_set_query_params(route=want)
                st.rerun()
except Exception:
    pass
# ---- End hard redirect guard v2 ----


# ---- Initial route bootstrap ----
try:
    ss = st.session_state
    if not ss.get("_route"):
        try:
            url_r = st.query_params.get("route")
            url_r = url_r[0] if isinstance(url_r, list) else url_r
        except Exception:
            url_r = (st.experimental_get_query_params().get("route") or [""])[0]
        if not url_r:
            last = ss.get("_route_last")
            if last and last != "home":
                ss["_route"] = last
            else:
                ss["_route"] = "chemo"
                ss["_route_last"] = "chemo"
            try:
                if st.query_params.get("route") != ss["_route"]:
                    st.query_params.update(route=ss["_route"])
            except Exception:
                st.experimental_set_query_params(route=ss["_route"])
            st.rerun()
except Exception:
    pass
# ---- End initial route bootstrap ----


# ===== Robust import guard =====
def _safe_import(modname):
    try:
        return importlib.import_module(modname)
    except Exception:
        return None

# Utility: wkey (Syntax Error 완벽 수정 완료)
if "wkey" not in globals():
    def wkey(x): 
        try:
            return f"{x}_{st.session_state.get('_uid', '')}".strip('_')
        except Exception:
            return str(x)

# ===== End import guard =====

# ---- Onco import shim ----
try:
    from onco_map import ensure_onco_map, ONCO_REGIMENS, build_onco_map, auto_recs_by_dx  # type: ignore
except Exception:
    def _load_local_module_onco(mod_name: str, file_path: str):
        spec = importlib.util.spec_from_file_location(mod_name, file_path)
        m = importlib.util.module_from_spec(spec)
        sys.modules[mod_name] = m
        spec.loader.exec_module(m)
        return m

    _onco = None
    _candidates = [
        Path(__file__).parent / "onco_map.py",
        Path(__file__).parent / "modules" / "onco_map.py",
        Path("/mount/src/hoya12/bloodmap_app/onco_map.py"),
        Path("/mount/src/hoya12/bloodmap_app/modules/onco_map.py"),
        Path("/mnt/data/onco_map.py"),
    ]
    for _p in _candidates:
        try:
            if _p.is_file():
                _onco = _load_local_module_onco("onco_map", str(_p))
                break
        except Exception:
            pass

    if _onco is None:
        def ensure_onco_map(m): return m
        ONCO_REGIMENS = {}
        def build_onco_map(): return {}
        def auto_recs_by_dx(*args, **kwargs): return {"chemo": [], "targeted": [], "abx": []}
    else:
        ensure_onco_map = getattr(_onco, "ensure_onco_map", lambda m: m)
        ONCO_REGIMENS  = getattr(_onco, "ONCO_REGIMENS", {})
        build_onco_map = getattr(_onco, "build_onco_map", lambda: {})
        auto_recs_by_dx = getattr(_onco, "auto_recs_by_dx", lambda *a, **k: {"chemo": [], "targeted": [], "abx": []})
# ---- End Onco import shim ----

KST = _ZoneInfo("Asia/Seoul")

def now_kst():
    return _dt.datetime.now(tz=KST)

st.markdown("""
<style>
html { scroll-behavior: smooth; }
.peds-nav-md{display:grid;grid-template-columns:repeat(3,1fr);gap:.5rem;margin:.25rem 0 .5rem;}
.peds-nav-md a{display:block;text-align:center;padding:.6rem .8rem;border-radius:12px;border:1px solid #ddd;text-decoration:none;color:inherit;background:#fff}
.peds-nav-md a:active{transform:scale(.98)}
</style>
""", unsafe_allow_html=True)

def render_peds_nav_md():
    st.markdown("""
    <div class="peds-nav-md">
      <a href="#peds_constipation">🧻 변비</a>
      <a href="#peds_diarrhea">💦 설사</a>
      <a href="#peds_vomit">🤢 구토</a>
      <a href="#peds_antipyretic">🌡️ 해열제</a>
      <a href="#peds_ors">🥤 ORS·탈수</a>
      <a href="#peds_respiratory">🫁 가래·쌕쌕</a>
    </div>
    """, unsafe_allow_html=True)

if 'peds_notes' not in st.session_state:
    st.session_state['peds_notes'] = ''
if 'peds_actions' not in st.session_state:
    st.session_state['peds_actions'] = []

APP_VERSION = "항상 여러분들의 힘이 되도록 노력하겠습니다. 여러분들의 피드백이 업데이트에 많은 도움이 됩니다"

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

_branding, BRANDING_PATH = _load_local_module("branding", ["branding.py", "modules/branding.py"])
if _branding and hasattr(_branding, "render_deploy_banner"):
    render_deploy_banner = _branding.render_deploy_banner
else:
    def render_deploy_banner(*a, **k): return None

_core, CORE_PATH = _load_local_module("core_utils", ["core_utils.py", "modules/core_utils.py"])
if _core and hasattr(_core, "ensure_unique_pin"):
    ensure_unique_pin = _core.ensure_unique_pin
else:
    def ensure_unique_pin(user_key: str, auto_suffix: bool = True):
        if not user_key: return "guest#PIN", False, "empty"
        if "#" not in user_key: user_key += "#0001"
        return user_key, False, "ok"

_pdf, PDF_PATH = _load_local_module("pdf_export", ["pdf_export.py", "modules/pdf_export.py"])
if _pdf and hasattr(_pdf, "export_md_to_pdf"):
    export_md_to_pdf = _pdf.export_md_to_pdf
else:
    def export_md_to_pdf(md_text: str) -> bytes: return md_text.encode("utf-8")

_drugdb, DRUGDB_PATH = _load_local_module("drug_db", ["drug_db.py", "modules/drug_db.py"])
if _drugdb:
    DRUG_DB = getattr(_drugdb, "DRUG_DB", {})
    ensure_onco_drug_db = getattr(_drugdb, "ensure_onco_drug_db", lambda db: None)
else:
    DRUG_DB = {}
    def ensure_onco_drug_db(db): pass

_ld, LD_PATH = _load_local_module("lab_diet", ["lab_diet.py", "modules/lab_diet.py"])
if _ld and hasattr(_ld, "lab_diet_guides"):
    lab_diet_guides = _ld.lab_diet_guides
else:
    def lab_diet_guides(labs, heme_flag=False): return []

_pd, PD_PATH = _load_local_module("peds_dose", ["peds_dose.py", "modules/peds_dose.py"])
if _pd:
    acetaminophen_ml = getattr(_pd, "acetaminophen_ml", lambda wt: (0.0, 0.0))
    ibuprofen_ml = getattr(_pd, "ibuprofen_ml", lambda wt: (0.0, 0.0))
else:
    def acetaminophen_ml(w): return (0.0, 0.0)
    def ibuprofen_ml(w): return (0.0, 0.0)

def _load_local_module2(mod_name: str, candidates):
    import importlib.util, sys
    from pathlib import Path
    def _try(fp: Path):
        try:
            spec = importlib.util.spec_from_file_location(mod_name, str(fp))
            if not spec or not spec.loader: return None, None
            m = importlib.util.module_from_spec(spec)
            sys.modules[mod_name] = m
            spec.loader.exec_module(m)
            return m, str(fp)
        except Exception:
            return None, None
    base_candidates = []
    seq = candidates if isinstance(candidates, (list, tuple)) else [candidates]
    for c in seq:
        c = str(c)
        if c.startswith("/"):
            fps = [Path(c)]
        else:
            fps = [
                Path(__file__).parent / c,
                Path(__file__).parent / "modules" / c,
                Path("/mount/src/hoya12/bloodmap_app") / c,
                Path("/mount/src/hoya12/bloodmap_app/modules") / c,
                Path("/mnt/data") / c,
            ]
        for fp in fps: base_candidates.append(fp)
    for fp in base_candidates:
        if fp.exists():
            m, used = _try(fp)
            if m: return m, used
    return None, None

_sp, SPECIAL_PATH = _load_local_module2("special_tests", ["special_tests.py", "modules/special_tests.py", "/mnt/data/special_tests.py"])
if _sp and hasattr(_sp, "special_tests_ui"):
    special_tests_ui = _sp.special_tests_ui
else:
    SPECIAL_PATH = None
    def special_tests_ui():
        st.warning("special_tests.py를 찾지 못해, 특수검사 UI는 더미로 표시됩니다.")
        return []

try:
    import matplotlib.pyplot as plt
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

# ---------- Helpers ----------
def _try_float(s):
    if s is None: return None
    if isinstance(s, (int, float)): return float(s)
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
    except Exception: return default

# ---------- Emergency scoring ----------
DEFAULT_WEIGHTS = {
    "w_anc_lt500": 1.0, "w_anc_500_999": 1.0, "w_temp_38_0_38_4": 1.0, "w_temp_ge_38_5": 1.0,
    "w_plt_lt20k": 1.0, "w_hb_lt7": 1.0, "w_crp_ge10": 1.0, "w_hr_gt130": 1.0, "w_hematuria": 1.0,
    "w_melena": 1.0, "w_hematochezia": 1.0, "w_chest_pain": 1.0, "w_dyspnea": 1.0, "w_confusion": 1.0,
    "w_oliguria": 1.0, "w_persistent_vomit": 1.0, "w_petechiae": 1.0, "w_thunderclap": 1.0, "w_visual_change": 1.0,
}

def get_weights():
    key = st.session_state.get("key", "guest#PIN")
    store = st.session_state.setdefault("weights", {})
    return store.setdefault(key, dict(DEFAULT_WEIGHTS))

def emergency_level(labs: dict, temp_c, hr, symptoms: dict):
    a = _try_float((labs or {}).get("ANC"))
    p = _try_float((labs or {}).get("PLT"))
    c = _try_float((labs or {}).get("CRP"))
    h = _try_float((labs or {}).get("Hb"))
    t = _try_float(temp_c)
    heart = _try_float(hr)

    W = get_weights()
    contrib = []

    def add(name, base, wkey_name):
        w = W.get(wkey_name, 1.0)
        contrib.append({"score": base * w})

    if a is not None and a < 500: add("ANC<500", 3, "w_anc_lt500")
    if t is not None and t >= 38.5: add("고열 ≥38.5℃", 2, "w_temp_ge_38_5")
    if p is not None and p < 20000: add("혈소판 <20k", 2, "w_plt_lt20k")
    if h is not None and h < 7.0: add("중증 빈혈(Hb<7)", 1, "w_hb_lt7")
    if c is not None and c >= 10: add("CRP ≥10", 1, "w_crp_ge10")
    if heart and heart > 130: add("빈맥(HR>130)", 1, "w_hr_gt130")

    risk = sum(item["score"] for item in contrib)
    return "🚨 응급" if risk >= 5 else ("🟧 주의" if risk >= 2 else "🟢 안심"), [], contrib

ensure_onco_drug_db(DRUG_DB)
ONCO = build_onco_map() or {}

# ---------- Sidebar ----------
with st.sidebar:
    st.header("프로필")
    raw_key = st.text_input("별명#PIN", value=st.session_state.get("key", "guest#PIN"), key="user_key_raw")
    st.session_state["key"] = raw_key
    
    st.subheader("활력징후")
    temp = st.text_input("현재 체온(℃)", value=st.session_state.get(wkey("cur_temp"), ""), key=wkey("cur_temp"))
    hr = st.text_input("심박수(bpm)", value=st.session_state.get(wkey("cur_hr"), ""), key=wkey("cur_hr"))

    st.subheader("연령")
    age_years = st.number_input("나이(년)", min_value=0.0, max_value=120.0, value=_safe_float(st.session_state.get(wkey("age_years"), 0.0)), key=wkey("age_years_num"))
    st.session_state[wkey("age_years")] = age_years

# ---------- Caregiver notes ----------
def render_caregiver_notes_peds(*, stool, fever, persistent_vomit, oliguria, cough, nasal, eye, abd_pain, ear_pain, rash, hives, migraine, hfmd):
    st.markdown("---")
    st.subheader("보호자 설명 (증상별)")
    if stool != "없음": st.markdown("- **설사/장염**: 수분 공급(ORS)에 신경 써 주시고 피가 섞이거나 처지면 바로 진료를 받으세요.")
    if fever != "없음": st.markdown("- **발열**: 해열제 간격을 준수하고 수분을 충분히 섭취하게 해 주세요.")

def build_peds_notes(*, stool, fever, persistent_vomit, oliguria, cough, nasal, eye, abd_pain, ear_pain, rash, hives, migraine, hfmd, max_temp=None) -> str:
    lines = []
    if fever != "없음": lines.append(f"[발열] {fever} (최고 {max_temp}℃)")
    if cough != "없음": lines.append(f"[기침] {cough}")
    return "\n".join(lines) if lines else "특이 증상 없음"

# ---------- Tabs Layout ----------
tab_labels = ["🏠 홈", "👶 소아 증상", "🧬 암 선택", "💊 항암제", "🧪 피수치 입력", "🔬 특수검사", "📄 보고서", "📊 기록/그래프"]
t_home, t_peds, t_dx, t_chemo, t_labs, t_special, t_report, t_graph = st.tabs(tab_labels)

# HOME
with t_home:
    st.subheader("응급도 요약")
    level_tmp, _, _ = emergency_level({}, st.session_state.get(wkey("cur_temp")), st.session_state.get(wkey("cur_hr")), {})
    st.info(f"현재 상태: {level_tmp}")
    
    with st.expander("💬 피드백(앱 개선 제안)", expanded=False):
        fb_store_key = wkey("home_feedback_store")
        fb_widget_key = wkey("home_feedback_input")
        st.text_area("피드백을 남겨주세요", value=st.session_state.get(fb_store_key, ""), key=fb_widget_key)
        
        if st.button("피드백 저장(세션)", key=wkey("btn_fb_save")):
            st.session_state[fb_store_key] = st.session_state.get(fb_widget_key, "")
            st.success("세션에 저장되었습니다.")

with t_peds:
    st.subheader("👶 소아 증상 상세 관리")
    render_peds_nav_md()
    render_caregiver_notes_peds(
        stool="없음", fever="없음", persistent_vomit=False, oliguria=False,
        cough="없음", nasal="없음", eye="없음", abd_pain=False, ear_pain=False,
        rash=False, hives=False, migraine=False, hfmd=False
    )

with t_dx:
    st.subheader("🧬 암 종류 및 진단 선택")

with t_chemo:
    st.subheader("💊 항암제 프로토콜 가이드")
    st.write(f"로드된 프로토콜 개수: {len(ONCO)}")

with t_labs:
    st.subheader("🧪 피수치(Lab) 데이터 입력 및 분석")

with t_special:
    st.subheader("🔬 특수검사 결과 요약")
    if SPECIAL_PATH: special_tests_ui()

with t_report:
    st.subheader("📄 통합 환자 보고서 출력")

with t_graph:
    st.subheader("📊 활력징후 및 피수치 트렌드 그래프")
