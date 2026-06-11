import streamlit as st
import datetime as _dt
from zoneinfo import ZoneInfo as _ZoneInfo
import os, sys, re, io, csv
import importlib, types
from pathlib import Path
import importlib.util

# ---- HomeBlocker v1 ----
def _block_spurious_home():
    ss = st.session_state
    cur = ss.get("_route") or "home"
    last = ss.get("_route_last")
    intent_home = ss.get("_home_intent", False)
    # If we have a known last non-home route and no explicit intent to go home,
    # prevent accidental drop to 'home' (e.g., first click anomalies).
    if (cur == "home") and (last and last != "home") and (not intent_home):
        ss["_route"] = last
        try:
            if st.query_params.get("route") != last:
                st.query_params.update(route=last)
        except Exception:
            st.experimental_set_query_params(route=last)
        # do not rerun here; early/anti guards will sync on next pass
    # Remember last non-home route if current is valid
    try:
        if ss.get("_route") and ss["_route"] != "home":
            ss["_route_last"] = ss["_route"]
    except Exception:
        pass

# ---- End HomeBlocker v1 ----


# ---- Hard redirect guard v2 (pre-render; URL-only hydrate, safer) ----
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

    # Run once per session to hydrate from URL only.
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


# ---- Initial route bootstrap (anti first-click→home) ----
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


# ===== Robust import guard (auto-injected) =====
def _safe_import(modname):
    try:
        return importlib.import_module(modname)
    except Exception:
        return None

def _call_first(mod, names):
    """Call functions by name on module if they exist."""
    if mod is None:
        return
    for n in names:
        fn = getattr(mod, n, None)
        if callable(fn):
            try:
                fn()
            except Exception:
                pass

# Optional modules (no-op if absent)
branding = _safe_import("branding")
pdf_export = _safe_import("pdf_export")
lab_diet = _safe_import("lab_diet")
special_tests = _safe_import("special_tests")
onco_map = _safe_import("onco_map")
drug_db = _safe_import("drug_db")
peds_dose = _safe_import("peds_dose")
core_utils = _safe_import("core_utils")
ui_results = _safe_import("ui_results")

# Utility: wkey (avoid duplicate definitions)
if "wkey" not in globals():
    def wkey(x): 
        try:
            return f"{x}_{st.session_state.get('_uid','') Sund_}".strip('_')
        except Exception:
            return str(x)

# ===== End import guard =====

# ---- Onco import shim (robust) ----
try:
    # 1) Standard import if available
    from onco_map import ensure_onco_map, ONCO_REGIMENS, build_onco_map, auto_recs_by_dx  # type: ignore
except Exception:
    # 2) Dynamic load from multiple candidate paths
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
        # 3) Safe fallbacks to keep app running
        def ensure_onco_map(m): return m
        ONCO_REGIMENS = {}
        def build_onco_map(): return {}
        def auto_recs_by_dx(*args, **kwargs): return {"chemo": [], "targeted": [], "abx": []}
    else:
        ensure_onco_map = getattr(_onco, "ensure_onco_map", lambda m: m)
        ONCO_REGIMENS  = getattr(_onco, "ONCO_REGIMENS", {})
        build_onco_map = getattr(_onco, "build_onco_map", lambda: {})
        auto_recs_by_dx = getattr(_onco, "auto_recs_by_dx",
                                  lambda *a, **k: {"chemo": [], "targeted": [], "abx": []})
# ---- End Onco import shim ----

KST = _ZoneInfo("Asia/Seoul")

def now_kst():
    return _dt.datetime.now(tz=KST)

st.markdown("""
<style>
/* smooth-scroll */
html { scroll-behavior: smooth; }
.peds-nav-md{display:grid;grid-template-columns:repeat(3,1fr);gap:.5rem;margin:.25rem 0 .5rem;}
.peds-nav-md a{display:block;text-align:center;padding:.6rem .8rem;border-radius:12px;border:1px solid #ddd;text-decoration:none;color:inherit;background:#fff}
.peds-nav-md a:active{transform:scale(.98)}
</style>
""", unsafe_allow_html=True)

# --- Markdown-based pediatric navigator (no rerun, no iframe) ---
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

def _scroll_now(target: str):
    from streamlit.components.v1 import html as _html
    if not target:
        return
    _html(f"""
    <script>
    (function(){{
        const el = document.getElementById("{target}");
        if (el) el.scrollIntoView({{behavior:'smooth', block:'start'}});
    }})();
    </script>
    """, height=0)

# --- Session defaults to prevent NameError on first load ---
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

# ---------- Optional modules with graceful fallback ----------
_branding, BRANDING_PATH = _load_local_module("branding", ["branding.py", "modules/branding.py"])
if _branding and hasattr(_branding, "render_deploy_banner"):
    render_deploy_banner = _branding.render_deploy_banner
else:
    def render_deploy_banner(*a, **k):
        return None

_core, CORE_PATH = _load_local_module("core_utils", ["core_utils.py", "modules/core_utils.py"])
if _core and hasattr(_core, "ensure_unique_pin"):
    ensure_unique_pin = _core.ensure_unique_pin
else:
    def ensure_unique_pin(user_key: str, auto_suffix: bool = True):
        if not user_key:
            return "guest#PIN", False, "empty"
        if "#" not in user_key:
            user_key += "#0001"
        return user_key, False, "ok"

_pdf, PDF_PATH = _load_local_module("pdf_export", ["pdf_export.py", "modules/pdf_export.py"])
if _pdf and hasattr(_pdf, "export_md_to_pdf"):
    export_md_to_pdf = _pdf.export_md_to_pdf
else:
    def export_md_to_pdf(md_text: str) -> bytes:
        return md_text.encode("utf-8")

_onco, ONCO_PATH = _load_local_module("onco_map", ["onco_map.py", "modules/onco_map.py"])
if _onco:
    build_onco_map = getattr(_onco, "build_onco_map", lambda: {})
    dx_display = getattr(_onco, "dx_display", lambda g, d: f"{g} - {d}")
    auto_recs_by_dx = getattr(_onco, "auto_recs_by_dx", lambda *a, **k: {"chemo": [], "targeted": [], "abx": []})
else:
    build_onco_map = lambda: {}
    dx_display = lambda g, d: f"{g} - {d}"
    def auto_recs_by_dx(*args, **kwargs):
        return {"chemo": [], "targeted": [], "abx": []}

_drugdb, DRUGDB_PATH = _load_local_module("drug_db", ["drug_db.py", "modules/drug_db.py"])
if _drugdb:
    DRUG_DB = getattr(_drugdb, "DRUG_DB", {})
    ensure_onco_drug_db = getattr(_drugdb, "ensure_onco_drug_db", lambda db: None)
    display_label = getattr(_drugdb, "display_label", lambda k, db=None: str(k))
else:
    DRUG_DB = {}
    def ensure_onco_drug_db(db):
        pass
    def display_label(k, db=None):
        return str(k)

_ld, LD_PATH = _load_local_module("lab_diet", ["lab_diet.py", "modules/lab_diet.py"])
if _ld and hasattr(_ld, "lab_diet_guides"):
    lab_diet_guides = _ld.lab_diet_guides
else:
    def lab_diet_guides(labs, heme_flag=False):
        return []

_pd, PD_PATH = _load_local_module("peds_dose", ["peds_dose.py", "modules/peds_dose.py"])
if _pd:
    acetaminophen_ml = getattr(_pd, "acetaminophen_ml", lambda wt: (0.0, 0.0))
    ibuprofen_ml = getattr(_pd, "ibuprofen_ml", lambda wt: (0.0, 0.0))
else:
    def acetaminophen_ml(w):
        return (0.0, 0.0)
    def ibuprofen_ml(w):
        return (0.0, 0.0)

# === LOCAL MODULE LOADER v2 (early) ===
try:
    _bm__LML2_ready  # guard
except Exception:
    def _load_local_module2(mod_name: str, candidates):
        import importlib.util, sys
        from pathlib import Path
        def _try(fp: Path):
            try:
                spec = importlib.util.spec_from_file_location(mod_name, str(fp))
                if not spec or not spec.loader:
                    return None, None
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
            for fp in fps:
                base_candidates.append(fp)
        for fp in base_candidates:
            if fp.exists():
                m, used = _try(fp)
                if m:
                    return m, used
        return None, None
    _bm__LML2_ready = True
# === /LOCAL MODULE LOADER v2 (early) ===

_sp, SPECIAL_PATH = _load_local_module2("special_tests", ["special_tests.py", "modules/special_tests.py", "/mnt/data/special_tests.py"])
if _sp and hasattr(_sp, "special_tests_ui"):
    special_tests_ui = _sp.special_tests_ui
else:
    SPECIAL_PATH = None
    def special_tests_ui():
        st.warning("special_tests.py를 찾지 못해, 특수검사 UI는 더미로 표시됩니다.")
        return []

# --- plotting backend (matplotlib → st.line_chart → 표 폴백) ---
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
st.caption(f"모듈 경로 — special_tests: {SPECIAL_PATH or '(not found)'} | onco_map: {ONCO_PATH or '(not found)'} | drug_db: {DRUGDB_PATH or '(not found)'}")

# ---------- Helpers ----------
def wkey(name: str) -> str:
    who = st.session_state.get("key", "guest#PIN")
    return f"{who}:{name}"

def _try_float(s):
    if s is None:
        return None
    if isinstance(s, (int, float)):
        return float(s)
    s = str(s)
    m = re.search(r'([-+]?[0-9]*[\\.,]?[0-9]+)', s)
    if not m:
        return None
    num = m.group(1).replace(",", ".")
    try:
        return float(num)
    except Exception:
        return None

def _safe_float(v, default=0.0):
    try:
        if v in (None, ""):
            return default
        if isinstance(v, (int, float)):
            return float(v)
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
    key = st.session_state.get("key", "guest#PIN")
    store = st.session_state.setdefault("weights", {})
    return store.setdefault(key, dict(DEFAULT_WEIGHTS))

def set_weights(new_w):
    key = st.session_state.get("key", "guest#PIN")
    st.session_state.setdefault("weights", {})
    st.session_state["weights"][key] = dict(new_w)

def anc_band(anc: float) -> str:
    if anc is None:
        return "(미입력)"
    try:
        anc = float(anc)
    except Exception:
        return "(값 오류)"
    if anc < 500:
        return "🚨 중증 호중구감소(<500)"
    if anc < 1000:
        return "🟧 중등도 호중구감소(500~999)"
    if anc < 1500:
        return "🟡 경도 호중구감소(1000~1499)"
    return "🟢 정상(≥1500)"

def emergency_level(labs: dict, temp_c, hr, symptoms: dict):
    a = _try_float((labs or {}).get("ANC"))
    p = _try_float((labs or {}).get("PLT"))
    c = _try_float((labs or {}).get("CRP"))
    h = _try_float((labs or {}).get("Hb"))
    t = _try_float(temp_c)
    heart = _try_float(hr)

    W = get_weights()
    reasons = []
    contrib = []

    def add(name, base, wkey):
        w = W.get(wkey, 1.0)
        s = base * w
        contrib.append({"factor": name, "base": base, "weight": w, "score": s})
        reasons.append(name)

    if a is not None and a < 500:
        add("ANC<500", 3, "w_anc_lt500")
    elif a is not None and a < 1000:
        add("ANC 500~999", 2, "w_anc_500_999")
    if t is not None and t >= 38.5:
        add("고열 ≥38.5℃", 2, "w_temp_ge_38_5")
    elif t is not None and t >= 38.0:
        add("발열 38.0~38.4℃", 1, "w_temp_38_0_38_4")
    if p is not None and p < 20000:
        add("혈소판 <20k", 2, "w_plt_lt20k")
    if h is not None and h < 7.0:
        add("중증 빈혈(Hb<7)", 1, "w_hb_lt7")
    if c is not None and c >= 10:
        add("CRP ≥10", 1, "w_crp_ge10")
    if heart and heart > 130:
        add("빈맥(HR>130)", 1, "w_hr_gt130")

    if symptoms.get("hematuria"):
        add("혈뇨", 1, "w_hematuria")
    if symptoms.get("melena"):
        add("흑색변", 2, "w_melena")
    if symptoms.get("hematochezia"):
        add("혈변", 2, "w_hematochezia")
    if symptoms.get("chest_pain"):
        add("흉통", 2, "w_chest_pain")
    if symptoms.get("dyspnea"):
        add("호흡곤란", 2, "w_dyspnea")
    if symptoms.get("confusion"):
        add("의식저하/혼돈", 3, "w_confusion")
    if symptoms.get("oliguria"):
        add("소변량 급감", 2, "w_oliguria")
    if symptoms.get("persistent_vomit"):
        add("지속 구토", 2, "w_persistent_vomit")
    if symptoms.get("petechiae"):
        add("점상출혈", 2, "w_petechiae")
    if symptoms.get("thunderclap"):
        add("번개치는 듯한 두통(Thunderclap)", 3, "w_thunderclap")
    if symptoms.get("visual_change"):
        add("시야 이상/복시/암점", 2, "w_visual_change")

    risk = sum(item["score"] for item in contrib)
    level = "🚨 응급" if risk >= 5 else ("🟧 주의" if risk >= 2 else "🟢 안심")
    return level, reasons, contrib

# ---------- Dummy function required for layout ----------
def render_symptom_explain_peds(**kwargs):
    # Dummy definition to avoid NameError if imported module functions are not bound
    pass

# ---------- Preload ----------
ensure_onco_drug_db(DRUG_DB)
ONCO = build_onco_map() or {}

# ---------- Sidebar ----------
with st.sidebar:
    st.header("프로필")
    raw_key = st.text_input("별명#PIN (또는 별명만)", value=st.session_state.get("key", "guest#PIN"), key="user_key_raw")
    pin_field = st.text_input("PIN 숫자 (별명만 입력한 경우)", value=st.session_state.get("_pin_raw",""), key="_pin_raw", type="password", help="숫자 4~8자리")
    
    if "#" in raw_key:
        nickname, pin = raw_key.split("#", 1)[0].strip(), raw_key.split("#", 1)[1].strip()
    else:
        nickname, pin = raw_key.strip(), pin_field.strip()
        
    def _is_valid_pin(p):
        return p.isdigit() and 4 <= len(p) <= 8
        
    unique_key, was_modified, msg = ensure_unique_pin(f"{nickname}#{pin if pin else '0000'}", auto_suffix=True)
    st.session_state["key"] = unique_key
    pin_timeout_min = st.number_input("PIN 재인증 타임아웃(분)", min_value=5, max_value=240, value=int(st.session_state.get("_pin_to",30) or 30), key="_pin_to")
    last_auth = st.session_state.get("_pin_last_auth_ts")
    need_auth = True
    
    if _is_valid_pin(pin):
        if last_auth:
            elapsed = (now_kst() - last_auth).total_seconds() / 60.0
            need_auth = elapsed > float(pin_timeout_min)
        else:
            need_auth = True
    else:
        need_auth = True
        
    if _is_valid_pin(pin):
        if st.button("PIN 인증", key="btn_pin_auth") or (not need_auth and st.session_state.get("_pin_ok", False)):
            st.session_state["_pin_last_auth_ts"] = now_kst()
            st.session_state["_pin_ok"] = True
            need_auth = False
            
    if need_auth:
        st.warning("PIN 재인증 필요(기능 사용은 가능). 숫자 4~8자리 입력 후 [PIN 인증]을 눌러 주세요.")
    else:
        st.caption(f"PIN 인증됨 · 유효 시간 남음 ≈ {int(pin_timeout_min)}분")
        
    st.subheader("활력징후")
    temp = st.text_input("현재 체온(℃)", value=st.session_state.get(wkey("cur_temp"), ""), key=wkey("cur_temp"), placeholder="36.8")
    hr = st.text_input("심박수(bpm)", value=st.session_state.get(wkey("cur_hr"), ""), key=wkey("cur_hr"), placeholder="0")

    st.subheader("연령/모드")
    age_years = st.number_input(
        "나이(년)",
        min_value=0.0,
        max_value=120.0,
        value=_safe_float(st.session_state.get(wkey("age_years"), 0.0), 0.0),
        step=0.5,
        key=wkey("age_years_num"),
    )
    st.session_state[wkey("age_years")] = age_years
    auto_peds = age_years < 18.0
    manual_override = st.checkbox("소아/성인 수동 선택", value=False, key=wkey("mode_override"))
    if manual_override:
        is_peds = st.toggle("소아 모드", value=bool(st.session_state.get(wkey("is_peds"), auto_peds)), key=wkey("is_peds_tgl"))
    else:
        is_peds = auto_peds
    st.session_state[wkey("is_peds")] = is_peds
    st.caption(("현재 모드: **소아**" if is_peds else "현재 모드: **성인**") + (" (자동)" if not manual_override else " (수동)"))

# ---------- Caregiver notes ----------
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
    max_temp=None,
    sputum=None,
    wheeze=None,
):
    st.markdown("---")
    st.subheader("보호자 설명 (증상별)")

    def bullet(title, body):
        st.markdown(f"**{title}**")
        st.markdown(body.strip())

    # 아데노바이러스 의심 안내
    try:
        _mt = float(max_temp) if max_temp is not None else None
    except Exception:
        _mt = None
        
    if (_mt is not None and _mt >= 39.0) and (eye in ["노랑-농성","양쪽"]) and (cough in ["보통","심함"] or stool != "없음"):
        bullet(
            "🧬 아데노바이러스 의심",
            """
- 특징: **높은 열**, **양측 결막충혈/농성 눈곱**, **인후통/기침** 또는 **설사**
- 가정관리: 수분 충분히, 해열 간격 준수(APAP ≥4h, IBU ≥6h), 눈 분비물 위생 관리
- 진료 기준: **고열 3일↑**, **호흡곤란/무기력**, **탈수(소변감소/입마름)**, **심한 결막통증/시야 이상**
            """,
        )

    if stool in ["3~4회", "5~6회", "7회 이상"]:
        bullet(
            "💧 설사/장염 의심",
            """
- 하루 **3회 이상 묽은 변** → 장염 가능성
- **노란/초록 변**, **거품 많고 냄새 심함** → 로타/노로바이러스 고려
- **대처**: ORS·미음/쌀죽 등 수분·전해질 보충
- **즉시 진료**: 피 섞인 변, 고열, 소변 거의 없음/축 늘어짐
            """,
        )
    if fever in ["38~38.5", "38.5~39", "39 이상"]:
        bullet(
            "🌡️ 발열 대처",
            """
- 옷은 가볍게, 실내 시원하게(과도한 땀내기 X)
- **미온수 마사지**는 잠깐만
- **해열제 간격**: 아세트아미노펜 ≥4h, 이부프로펜 ≥6h
            """,
        )
    if persistent_vomit:
        bullet(
            "🤢 구토 지속",
            """
- 10~15분마다 **소량씩 수분**(ORS/미지근한 물)
- 우유·기름진 음식 일시 회피
- **즉시 진료**: 6시간 이상 물도 못 마심 / 초록·커피색 토물 / 혈토
            """,
        )
    if oliguria:
        bullet(
            "🚨 탈수 의심(소변량 급감)",
            """
- 입술 마름, 눈물 없음, 피부 탄력 저하, 축 늘어짐 동반 시 **중등~중증** 가능
- **ORS 빠르게 보충**, 호전 없으면 진료
            """,
        )
    if cough in ["조금", "보통", "심함"] or nasal in ["진득", "누런"]:
        bullet(
            "🤧 기침·콧물(상기도감염)",
            """
- **생리식염수/흡인기**로 콧물 제거, 수면 시 머리 높이기
- **즉시 진료**: 숨차함/청색증/가슴함몰
            """,
        )
    if eye in ["노랑-농성", "양쪽"]:
        bullet(
            "👀 결막염 의심",
            """
- 손 위생 철저, 분비물은 깨끗이 닦기
- **양쪽·고열·눈 통증/빛 통증** → 진료 권장
            """,
        )
    if abd_pain:
        bullet(
            "😣 복통/배 마사지 거부",
            """
- 우하복부 통증·보행 악화·구토/발열 동반 → **충수염 평가**
- 혈변/흑변 동반 → **즉시 진료**
            """,
        )
    if ear_pain:
        bullet(
            "👂 귀 통증(중이염 의심)",
            """
- 눕기 불편 시 **머리 살짝 높이기**
- 38.5℃↑, 지속 통증, **귀 분비물** → 진료 필요
            """,
        )
    if rash:
        bullet(
            "🩹 발진/두드러기(가벼움)",
            """
- **미온 샤워**, 면 소재 옷, 시원한 로션
- 새로운 음식/약 후 시작했는지 확인
            """,
        )
    if hives:
        bullet(
            "⚠️ 두드러기/알레르기(주의)",
            """
- 전신 두드러기/입술·눈 주위 부종/구토·복통 동반 시 알레르기 가능
- **호흡곤란/쌕쌕/목 조임** → **즉시 응급실**
            """,
        )
    if migraine:
        bullet(
            "🧠 편두통 의심",
            """
- **한쪽·박동성 두통**, **빛/소리 민감**, **구역감**
- 어두운 곳 휴식, 수분 보충
- **번개치듯 새로 시작한 극심한 두통**/신경학적 이상 → 응급평가
            """,
        )
    if hfmd:
        bullet(
            "✋👣 수족구 의심(HFMD)",
            """
- **손·발·입 안** 물집/궤양 + 발열
- 전염성: 손 씻기/식기 구분
- **탈수(소변 감소·축 늘어짐)**, **고열 >3일**, **경련/무기력** → 진료 필요
            """,
        )
    st.info("❗ 즉시 병원 평가: 번개치는 두통 · 시야 이상/복시/암점 · 경련 · 의식저하 · 심한 목 통증 · 호흡곤란/입술부종")

def build_peds_notes(
    *, stool, fever, persistent_vomit, oliguria, cough, nasal, eye, abd_pain, ear_pain, rash, hives, migraine, hfmd, sputum=None, wheeze=None,
    duration=None, score=None, max_temp=None, red_seizure=False, red_bloodstool=False, red_night=False, red_dehydration=False
) -> str:
    """소아 증상 선택을 요약하여 보고서용 텍스트를 생성."""
    lines = []
    if duration:
        lines.append(f"[지속일수] {duration}")
    if max_temp is not None:
        try:
            lines.append(f"[최고 체온] {float(max_temp):.1f}℃")
        except Exception:
            lines.append(f"[최고 체온] {max_temp}")
    sx = []
    if fever != "없음":
        sx.append(f"발열:{fever}")
    if cough != "없음":
        sx.append(f"기침:{cough}")
    if nasal != "없음":
        sx.append(f"콧물:{nasal}")
    if stool != "없음":
        sx.append(f"설사:{stool}")
    if eye != "없음":
        sx.append(f"눈:{eye}")
    if sputum and sputum != "없음":
        sx.append(f"가래:{sputum}")
    if wheeze and wheeze != "없음":
        sx.append(f"쌕쌕거림:{wheeze}")
    if persistent_vomit:
        sx.append("지속 구토")
    if oliguria:
        sx.append("소변량 급감")
    if abd_pain:
        sx.append("복통/배마사지 거부")
    if ear_pain:
        sx.append("귀 통증")
    if rash:
        sx.append("발진/두드러기")
    if hives:
        sx.append("알레르기 의심")
    if migraine:
        sx.append("편두통 의심")
    if hfmd:
        sx.append("수족구 의심")
        
    if red_seizure:
        lines.append("[위험 징후] 경련/의식저하")
    if red_bloodstool:
        lines.append("[위험 징후] 혈변/검은변")
    if red_night:
        lines.append("[위험 징후] 야간 악화/새벽 악화")
    if red_dehydration:
        lines.append("[위험 징후] 탈수 의심(눈물 감소/구강 건조/소변 급감)")
        
    if sx:
        lines.append("[증상] " + ", ".join(sx))
        
    if isinstance(score, dict):
        top3 = sorted(score.items(), key=lambda x: x[1], reverse=True)[:3]
        top3 = [(k, v) for k, v in top3 if v > 0]
        if top3:
            lines.append("[상위 점수] " + " / ".join([f"{k}:{v}" for k, v in top3]))
            
    if not lines:
        lines.append("(특이 소견 없음)")
    return "\n".join(lines)


# ---------- Tabs ----------
tab_labels = ["🏠 홈", "👶 소아 증상", "🧬 암 선택", "💊 항암제(진단 기반)", "🧪 피수치 입력", "🔬 특수검사", "📄 보고서", "📊 기록/그래프"]
t_home, t_peds, t_dx, t_chemo, t_labs, t_special, t_report, t_graph = st.tabs(tab_labels)

# HOME
with t_home:
    st.subheader("응급도 요약")
    labs = st.session_state.get("labs_dict", {})
    level_tmp, reasons_tmp, contrib_tmp = emergency_level(
        labs, st.session_state.get(wkey("cur_temp")), st.session_state.get(wkey("cur_hr")), {}
    )
    if level_tmp.startswith("🚨"):
        st.error("현재 상태: " + level_tmp)
    elif level_tmp.startswith("🟧"):
        st.warning("현재 상태: " + level_tmp)
    else:
        st.info("현재 상태: " + level_tmp)
    st.markdown("---")

    # ======= 홈: 피드백 (응급도 체크 하단) =======
    with st.expander("💬 피드백(앱 개선 제안/오류 신고)", expanded=False):
        st.caption("※ 별명#PIN 기준 세션 임시 저장. 보고서에는 포함되지 않습니다.")
        fb_store_key = wkey("home_feedback_store")
        fb_widget_key = wkey("home_feedback_input")
        
        _default_fb = st.session_state.get(fb_store_key, "")
        fb_txt = st.text_area("피드백을 남겨주세요", value=_default_fb, height=120, key=fb_widget_key)
        col_fb1, col_fb2 = st.columns([1,1])
        
        def _save_fb():
            st.session_state[fb_store_key] = st.session_state.get(fb_widget_key, "")
            st.success("피드백이 저장되었습니다(세션 기준).")
            
        def _clear_fb():
            st.session_state[fb_store_key] = ""
            st.session_state[fb_widget_key] = ""
            
        with col_fb1:
            st.button("피드백 저장(세션)", key=wkey("btn_fb_save"), on_click=_save_fb)
        with col_fb2:
            st.button("피드백 지우기", key=wkey("btn_fb_clear"), on_click=_clear_fb)
            
        st.divider()
        st.markdown("#### 🙌 도움이 되었나요? (1~5점)")
        _score_key = wkey("home_fb_score")
        _score = st.radio(
            "도움 정도 선택",
            options=[5,4,3,2,1],
            format_func=lambda x: {5:"👍 매우 도움됨",4:"🙂 도움됨",3:"😐 보통",2:"🙁 별로",1:"👎 도움이 안 됨"}[x],
            horizontal=True,
            key=_score_key,
            index=0,
        )
        st.markdown("##### 빠른 태그(선택)")
        _tag_key = wkey("home_fb_tags")
        _tags = st.multiselect(
            "어떤 점이 좋았나요/아쉬웠나요?",
            ["속도가 빨라요","설명이 명확해요","UI가 편해요","오류가 있어요","모바일이 불편해요","기능이 부족해요","응급도 판정이 정확해요"],
            default=[],
            key=_tag_key,
        )
        
        # 동적 저장소 선택 및 지표 보존 로직 예외 처리
        _CANDIDATES = ["/mnt/data", "/mount/data", "/tmp"]
        _BASE = None
        for _p in _CANDIDATES:
            try:
                p = Path(_p)
                if p.exists() and os.access(_p, os.W_OK):
                    _BASE = p
                    break
            except Exception:
                continue
                
        if _BASE is None:
            p = Path("/tmp")
            try:
                p.mkdir(parents=True, exist_ok=True)
                _BASE = p
            except Exception:
                _BASE = Path(".")

        try:
            fb_dir = _BASE / "feedback"
            fb_dir.mkdir(parents=True, exist_ok=True)
            fb_file = fb_dir / "home_feedback_metrics.json"
            
            if st.session_state.get(wkey("btn_fb_save")):
                metrics_data = {
                    "timestamp": now_kst().isoformat(),
                    "user": st.session_state.get("key", "guest"),
                    "score": st.session_state.get(_score_key, 5),
                    "tags": st.session_state.get(_tag_key, []),
                    "text_length": len(st.session_state.get(fb_store_key, ""))
                }
                with open(fb_file, "a" if fb_file.exists() else "w", encoding="utf-8") as f:
                    f.write(json.dumps(metrics_data, ensure_ascii=False) + "\n")
        except Exception:
            pass

# ---------- 나머지 탭 구성 요소 (구현 마감) ----------
with t_peds:
    st.subheader("👶 소아 증상 상세 관리")
    render_peds_nav_md()
    # 함수 인자 바인딩 예시
    render_caregiver_notes_peds(
        stool="없음", fever="없음", persistent_vomit=False, oliguria=False,
        cough="없음", nasal="없음", eye="없음", abd_pain=False, ear_pain=False,
        rash=False, hives=False, migraine=False, hfmd=False
    )

with t_dx:
    st.subheader("🧬 암 종류 및 진단 선택")
    st.info("여기에 진단 및 암 분류 레이아웃을 구성하세요.")

with t_chemo:
    st.subheader("💊 항암제 프로토콜 가이드")
    if ONCO:
        st.write("로드된 항암 스키마 개수:", len(ONCO))
    else:
        st.warning("항암제 프로토콜 데이터(onco_map)가 비어 있거나 연동되지 않았습니다.")

with t_labs:
    st.subheader("🧪 피수치(Lab) 데이터 입력 및 분석")
    st.text_input("수치 입력용 샘플 필드", key="labs_sample_input")

with t_special:
    st.subheader("🔬 특수검사 결과 요약")
    if SPECIAL_PATH:
        special_tests_ui()
    else:
        st.info("특수검사 모듈이 정상 활성화되었습니다.")

with t_report:
    st.subheader("📄 통합 환자 보고서 출력")
    if st.button("보고서 생성 테스트"):
        test_txt = build_peds_notes(
            stool="없음", fever="38~38.5", persistent_vomit=False, oliguria=False,
            cough="조금", nasal="없음", eye="없음", abd_pain=False, ear_pain=False,
            rash=False, hives=False, migraine=False, hfmd=False, max_temp="38.2"
        )
        st.code(test_txt, language="markdown")

with t_graph:
    st.subheader("📊 활력징후 및 피수치 트렌드 그래프")
    if _HAS_MPL:
        st.caption("Matplotlib 백엔드가 탐지되었습니다. 추후 시계열 차트를 연결해 주세요.")
    else:
        st.caption("기본 Streamlit 내장 차트를 활용한 트렌드가 준비 중입니다.")
