
import datetime as _dt
import os, sys, json
from pathlib import Path
import importlib.util
import streamlit as st

APP_VERSION = "v7.17e (Safe Import + Peds + Onco/Chemo)"

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

# ---------- Try load optional modules with graceful fallback ----------
# Branding
_branding, BRANDING_PATH = _load_local_module("branding", ["branding.py", "modules/branding.py"])
if _branding and hasattr(_branding, "render_deploy_banner"):
    render_deploy_banner = _branding.render_deploy_banner
else:
    def render_deploy_banner(*a, **k): return None

# Core utils (PIN uniqueness)
_core, CORE_PATH = _load_local_module("core_utils", ["core_utils.py", "modules/core_utils.py"])
if _core and hasattr(_core, "ensure_unique_pin"):
    ensure_unique_pin = _core.ensure_unique_pin
else:
    def ensure_unique_pin(user_key: str, auto_suffix: bool=True):
        if not user_key: return "guest#PIN", False, "empty"
        if "#" not in user_key: user_key += "#0001"
        return user_key, False, "ok"

# PDF export
_pdf, PDF_PATH = _load_local_module("pdf_export", ["pdf_export.py", "modules/pdf_export.py"])
if _pdf and hasattr(_pdf, "export_md_to_pdf"):
    export_md_to_pdf = _pdf.export_md_to_pdf
else:
    def export_md_to_pdf(md_text: str) -> bytes:
        return md_text.encode("utf-8")

# Oncology map
_onco, ONCO_PATH = _load_local_module("onco_map", ["onco_map.py", "modules/onco_map.py"])
if _onco:
    build_onco_map = getattr(_onco, "build_onco_map", lambda: {})
    dx_display = getattr(_onco, "dx_display", lambda g,d: f"{g} - {d}")
    auto_recs_by_dx = getattr(_onco, "auto_recs_by_dx", lambda *a, **k: {"chemo": [], "targeted": [], "abx": []})
else:
    build_onco_map = lambda: {}
    dx_display = lambda g,d: f"{g} - {d}"
    def auto_recs_by_dx(*args, **kwargs): return {"chemo": [], "targeted": [], "abx": []}

# Drug DB
_drugdb, DRUGDB_PATH = _load_local_module("drug_db", ["drug_db.py", "modules/drug_db.py"])
if _drugdb:
    DRUG_DB = getattr(_drugdb, "DRUG_DB", {})
    ensure_onco_drug_db = getattr(_drugdb, "ensure_onco_drug_db", lambda db: None)
    display_label = getattr(_drugdb, "display_label", lambda k, db=None: str(k))
    key_from_label = getattr(_drugdb, "key_from_label", lambda s, db=None: s.split(" (")[0] if s else "")
else:
    DRUG_DB = {}
    def ensure_onco_drug_db(db): pass
    def display_label(k, db=None): return str(k)
    def key_from_label(s, db=None): return s.split(" (")[0] if s else ""

# UI results / AE alerts
_ui, UI_PATH = _load_local_module("ui_results", ["ui_results.py", "modules/ui_results.py"])
if _ui and hasattr(_ui, "collect_top_ae_alerts"):
    collect_top_ae_alerts = _ui.collect_top_ae_alerts
else:
    def collect_top_ae_alerts(*a, **k): return []

# Diet guide by labs
_ld, LD_PATH = _load_local_module("lab_diet", ["lab_diet.py", "modules/lab_diet.py"])
if _ld and hasattr(_ld, "lab_diet_guides"):
    lab_diet_guides = _ld.lab_diet_guides
else:
    def lab_diet_guides(labs, heme_flag=False): return []

# Pediatric dosing
_pd, PD_PATH = _load_local_module("peds_dose", ["peds_dose.py", "modules/peds_dose.py"])
if _pd:
    acetaminophen_ml = getattr(_pd, "acetaminophen_ml", lambda wt: (0.0,0.0))
    ibuprofen_ml = getattr(_pd, "ibuprofen_ml", lambda wt: (0.0,0.0))
else:
    def acetaminophen_ml(w): return (0.0,0.0)
    def ibuprofen_ml(w): return (0.0,0.0)

# Special tests
_sp, SPECIAL_PATH = _load_local_module("special_tests", ["special_tests.py", "modules/special_tests.py"])
if _sp and hasattr(_sp, "special_tests_ui"):
    special_tests_ui = _sp.special_tests_ui
else:
    SPECIAL_PATH = None
    def special_tests_ui():
        st.warning("special_tests.py를 찾지 못해, 특수검사 UI는 더미로 표시됩니다.")
        return []

# ---------- App skeleton ----------
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

# Preload oncologic structures
ensure_onco_drug_db(DRUG_DB)
ONCO = build_onco_map() or {}

# ---------- Helpers ----------
def wkey(name:str)->str:
    who = st.session_state.get("key","guest#PIN")
    return f"{who}:{name}"

def _parse_float(txt):
    if txt is None: return None
    s = str(txt).strip().replace(",", "")
    if s == "": return None
    try:
        return float(s)
    except Exception:
        return None

def float_input(label:str, key:str, placeholder:str=""):
    val = st.text_input(label, value=str(st.session_state.get(key, "")), key=key, placeholder=placeholder)
    return _parse_float(val)

# ====== Emergency helpers + Weights ======
DEFAULT_WEIGHTS = {
    # labs
    "w_anc_lt500": 1.0, "w_anc_500_999": 1.0,
    "w_temp_38_0_38_4": 1.0, "w_temp_ge_38_5": 1.0,
    "w_plt_lt20k": 1.0, "w_hb_lt7": 1.0, "w_crp_ge10": 1.0, "w_hr_gt130": 1.0,
    # symptoms
    "w_hematuria": 1.0, "w_melena": 1.0, "w_hematochezia": 1.0,
    "w_chest_pain": 1.0, "w_dyspnea": 1.0, "w_confusion": 1.0,
    "w_oliguria": 1.0, "w_persistent_vomit": 1.0, "w_petechiae": 1.0,
}
def get_weights():
    key = st.session_state.get("key","guest#PIN")
    store = st.session_state.setdefault("weights", {})
    return store.setdefault(key, DEFAULT_WEIGHTS.copy())

def anc_band(anc: float) -> str:
    if anc is None:
        return "(미입력)"
    try:
        anc = float(anc)
    except Exception:
        return "(값 오류)"
    if anc < 500: return "🚨 중증 호중구감소(<500)"
    if anc < 1000: return "🟧 중등도 호중구감소(500~999)"
    if anc < 1500: return "🟡 경도 호중구감소(1000~1499)"
    return "🟢 정상(≥1500)"

def emergency_level(labs: dict, temp_c, hr, symptoms: dict):
    anc = labs.get("ANC") if isinstance(labs, dict) else None
    plt = labs.get("PLT") if isinstance(labs, dict) else None
    crp = labs.get("CRP") if isinstance(labs, dict) else None
    hb  = labs.get("Hb")  if isinstance(labs, dict) else None

    t = temp_c if isinstance(temp_c,(int,float)) else _parse_float(temp_c)
    a = anc if isinstance(anc,(int,float)) else _parse_float(anc)
    p = plt if isinstance(plt,(int,float)) else _parse_float(plt)
    c = crp if isinstance(crp,(int,float)) else _parse_float(crp)
    h = hb  if isinstance(hb,(int,float)) else _parse_float(hb)
    heart = hr if isinstance(hr,(int,float)) else _parse_float(hr)

    W = get_weights()
    reasons = []
    contrib = []

    def add(name, base, wkey):
        w = W.get(wkey, 1.0)
        s = base * w
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

    risk = sum(item["score"] for item in contrib)
    level = "🚨 응급" if risk >= 5 else ("🟧 주의" if risk >= 2 else "🟢 안심")
    return level, reasons, contrib

# ====== LAB REFERENCE/VALIDATION ======
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
    rng = lab_ref(is_peds).get(abbr); 
    if rng is None or val in (None, ""): return None
    try: v = float(val)
    except Exception: return "형식 오류"
    lo, hi = rng
    if v < lo: return f"⬇️ 기준치 미만({lo}~{hi})"
    if v > hi: return f"⬆️ 기준치 초과({lo}~{hi})"
    return "정상범위"

# ====== Sidebar (PIN + vitals) ======
with st.sidebar:
    st.header("프로필")
    raw_key = st.text_input("별명#PIN", value=st.session_state.get("key","guest#PIN"), key="user_key_raw")
    unique_key, was_modified, msg = ensure_unique_pin(raw_key, auto_suffix=True)
    st.session_state["key"] = unique_key
    if was_modified:
        st.warning(msg + f" → 현재 키: {unique_key}")
    else:
        st.caption("PIN 확인됨")
    temp = st.text_input("현재 체온(℃)", value=st.session_state.get(wkey("cur_temp"), ""), key=wkey("cur_temp"), placeholder="36.8")
    hr   = st.text_input("심박수(bpm)", value=st.session_state.get(wkey("cur_hr"), ""), key=wkey("cur_hr"), placeholder="0")

# ====== Tabs ======
tab_labels = ["🏠 홈","🧪 피수치 입력","🧬 암 선택","💊 항암제","👶 소아 증상","🔬 특수검사","📄 보고서"]
t_home, t_labs, t_dx, t_chemo, t_peds, t_special, t_report = st.tabs(tab_labels)

# ====== HOME ======
with t_home:
    st.subheader("응급도 요약")
    labs = st.session_state.get("labs_dict", {})
    level_tmp, reasons_tmp, contrib_tmp = emergency_level(labs, st.session_state.get(wkey("cur_temp")), st.session_state.get(wkey("cur_hr")), {})
    if level_tmp.startswith("🚨"):
        st.error("현재 상태: " + level_tmp)
    elif level_tmp.startswith("🟧"):
        st.warning("현재 상태: " + level_tmp)
    else:
        st.info("현재 상태: " + level_tmp)

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

    sym = dict(hematuria=hematuria, melena=melena, hematochezia=hematochezia,
               chest_pain=chest_pain, dyspnea=dyspnea, confusion=confusion,
               oliguria=oliguria, persistent_vomit=persistent_vomit, petechiae=petechiae)

    level, reasons, contrib = emergency_level(labs, st.session_state.get(wkey("cur_temp")), st.session_state.get(wkey("cur_hr")), sym)
    if level.startswith("🚨"):
        st.error("응급도: " + level + " — " + " · ".join(reasons))
    elif level.startswith("🟧"):
        st.warning("응급도: " + level + " — " + " · ".join(reasons))
    else:
        st.info("응급도: " + level + (" — " + " · ".join(reasons) if reasons else ""))

    if contrib:
        st.markdown("**응급도 기여도(Why)**")
        total = sum(x["score"] for x in contrib) or 1.0
        rows = []
        for item in contrib:
            pct = round(100.0 * item["score"]/total, 1)
            rows.append({"요인": item["factor"],"기본점수": item["base"],"가중치": item["weight"],"반영점수": round(item["score"],2),"기여도%": pct})
        try:
            import pandas as pd
            st.dataframe(pd.DataFrame(rows).sort_values("반영점수", ascending=False), use_container_width=True)
        except Exception:
            for r in sorted(rows, key=lambda x:-x["반영점수"]):
                st.write(f"- {r['요인']} — 점수 {r['반영점수']} (기본 {r['기본점수']} × 가중치 {r['가중치']}, {r['기여도%']}%)")

# ====== LABS ======
with t_labs:
    st.subheader("피수치 입력 — 붙여넣기 지원")
    st.caption("표기 예: 4.5 / 135 / 0.8  (숫자와 소수점만 입력)")
    use_peds = st.checkbox("소아 기준(참조범위/검증에 적용)", value=False, key=wkey("labs_use_peds"))
    order = [("WBC","백혈구"), ("Ca","칼슘"), ("Glu","혈당"), ("CRP","CRP"),
             ("Hb","혈색소"), ("P","인(Phosphorus)"), ("T.P","총단백"), ("Cr","크레아티닌"),
             ("PLT","혈소판"), ("Na","나트륨"), ("AST","AST"), ("T.B","총빌리루빈"),
             ("ANC","절대호중구"), ("Alb","알부민"), ("ALT","ALT"), ("BUN","BUN")]
    with st.expander("📋 검사값 붙여넣기(자동 인식)", expanded=False):
        pasted = st.text_area("예: WBC: 4.5\nHb 12.3\nPLT, 200", height=120, key=wkey("labs_paste"))
        if st.button("붙여넣기 파싱 → 적용", key=wkey("parse_paste")):
            parsed = {}
            if pasted:
                for line in str(pasted).splitlines():
                    s = line.strip()
                    if not s: continue
                    for sep in [":", ",", "\t"]:
                        if sep in s:
                            parts = [p for p in s.split(sep) if p.strip()]
                            if len(parts) >= 2:
                                k = parts[0].strip().upper()
                                v = parts[1].strip()
                                alias = {"TP":"T.P","TB":"T.B"}
                                if k in alias: k = alias[k]
                                parsed[k] = v
                                break
                    else:
                        toks = s.split()
                        if len(toks) >= 2 and any(ch.isdigit() for ch in toks[-1]):
                            k = toks[0].strip().upper(); v = toks[-1].strip()
                            alias = {"TP":"T.P","TB":"T.B"}
                            if k in alias: k = alias[k]
                            parsed[k] = v
            if parsed:
                for abbr,_ in order:
                    if abbr in parsed: st.session_state[wkey(abbr)] = parsed[abbr]
                st.success(f"적용됨: {', '.join(list(parsed.keys())[:12])} ...")

    cols = st.columns(4); values = {}
    def _parse_float(txt):
        if txt is None: return None
        s = str(txt).strip().replace(",", "")
        if s == "": return None
        try: return float(s)
        except Exception: return None
    for i,(abbr,kor) in enumerate(order):
        with cols[i%4]:
            val = st.text_input(f"{abbr} — {kor}", value=str(st.session_state.get(wkey(abbr), "")), key=wkey(abbr))
            values[abbr] = _parse_float(val)
            msg = lab_validate(abbr, values[abbr], use_peds)
            if msg: st.caption(("✅ " if msg=="정상범위" else "⚠️ ")+msg)
    labs_dict = st.session_state.get("labs_dict", {}); labs_dict.update(values)
    st.session_state["labs_dict"] = labs_dict
    st.markdown(f"**ANC 분류:** {anc_band(values.get('ANC'))}")

# ====== DX (암 선택) ======
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

    # 자동 추천(있으면)
    recs = auto_recs_by_dx(group, disease, DRUG_DB) or {}
    if any(recs.values()):
        st.markdown("**자동 추천 요약**")
        for cat, arr in recs.items():
            if not arr: continue
            st.write(f"- {cat}: " + ", ".join(arr))

# ====== CHEMO (항암제) ======
def _aggregate_all_aes(meds, db):
    result = {}
    if not isinstance(meds, (list, tuple)) or not meds:
        return result
    ae_fields = ["ae","ae_ko","adverse_effects","adverse","side_effects","side_effect","warnings","warning","black_box","boxed_warning","toxicity","precautions","safety","safety_profile","notes"]
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
    st.subheader("항암제 선택 및 부작용")
    if not DRUG_DB:
        st.warning("drug_db 가 로드되지 않아 목록이 비어있습니다. drug_db.py를 같은 폴더나 modules/ 에 두세요.")
    # 드롭다운 라벨 만들기
    labels = []
    for key, rec in DRUG_DB.items():
        try:
            labels.append(display_label(key, DRUG_DB))
        except Exception:
            labels.append(str(key))
    labels = sorted(set(labels)) if labels else []
    picked_labels = st.multiselect("투여/계획 약물 선택", options=labels, key=wkey("drug_pick"))
    # 라벨->키
    picked_keys = [key_from_label(lbl, DRUG_DB) for lbl in picked_labels]
    st.session_state["chemo_keys"] = picked_keys

    if picked_keys:
        st.markdown("### 선택 약물")
        for k in picked_keys:
            st.write("- " + display_label(k, DRUG_DB))
        # 부작용 종합
        ae_map = _aggregate_all_aes(picked_keys, DRUG_DB)
        st.markdown("### 항암제 부작용(전체)")
        if ae_map:
            for k, arr in ae_map.items():
                st.write(f"- **{display_label(k, DRUG_DB)}**")
                for ln in arr:
                    st.write(f"  - {ln}")
        else:
            st.write("- (DB에 상세 부작용 없음)")

# ====== PEDS (증상 + 해열제) ======
with t_peds:
    st.subheader("소아 증상 기반 점수 + 해열제 계산")
    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: nasal = st.selectbox("콧물", ["없음","투명","진득","누런"], key=wkey("p_nasal"))
    with c2: cough = st.selectbox("기침", ["없음","조금","보통","심함"], key=wkey("p_cough"))
    with c3: stool = st.selectbox("설사", ["없음","1~2회","3~4회","5~6회","7회 이상"], key=wkey("p_stool"))
    with c4: fever = st.selectbox("발열", ["없음","37~37.5 (미열)","37.5~38","38~38.5","38.5~39","39 이상"], key=wkey("p_fever"))
    with c5: eye   = st.selectbox("눈꼽", ["없음","맑음","노랑-농성","양쪽"], key=wkey("p_eye"))
    d1,d2,d3 = st.columns(3)
    with d1: oliguria = st.checkbox("소변량 급감", key=wkey("p_oliguria"))
    with d2: persistent_vomit = st.checkbox("지속 구토(>6시간)", key=wkey("p_pvomit"))
    with d3: petechiae = st.checkbox("점상출혈", key=wkey("p_petechiae"))
    score = {"장염 의심":0, "상기도/독감 계열":0, "결막염 의심":0, "탈수/신장 문제":0, "출혈성 경향":0}
    if stool in ["3~4회","5~6회","7회 이상"]:
        score["장염 의심"] += {"3~4회":40,"5~6회":55,"7회 이상":70}[stool]
    if "38.5" in fever or "39" in fever: score["상기도/독감 계열"] += 25
    if cough in ["보통","심함","조금"]: score["상기도/독감 계열"] += 20
    if eye in ["노랑-농성","양쪽"]: score["결막염 의심"] += 30
    if oliguria: score["탈수/신장 문제"] += 40; score["장염 의심"] += 10
    if persistent_vomit: score["장염 의심"] += 25; score["탈수/신장 문제"] += 15
    if petechiae: score["출혈성 경향"] += 60
    ordered = sorted(score.items(), key=lambda x: x[1], reverse=True)
    st.write("• " + " / ".join([f"{k}: {v}" for k,v in ordered]))
    top = ordered[0][0] if ordered else "(없음)"
    advice = []
    if top == "장염 의심": advice.append("ORS로 수분 보충, 소변량 관찰")
    if top == "상기도/독감 계열": advice.append("해열제 간격 준수(APAP≥4h, IBU≥6h)")
    if top == "결막염 의심": advice.append("눈 위생, 분비물 제거, 병원 상담 고려")
    if top == "탈수/신장 문제": advice.append("즉시 수분 보충, 소변량/활력 징후 확인, 필요시 병원")
    if top == "출혈성 경향": advice.append("점상출혈/혈변 동반 시 즉시 병원")
    if advice: st.info(" / ".join(advice))
    st.markdown("---")
    st.subheader("해열제 계산기")
    wt = st.number_input("체중(kg)", min_value=0.0, max_value=200.0, value=float(st.session_state.get(wkey("wt_peds"), 0.0)), step=0.1, key=wkey("wt_peds_num"))
    st.session_state[wkey("wt_peds")] = wt
    try:
        ap_ml_1, ap_ml_max = acetaminophen_ml(wt)
        ib_ml_1, ib_ml_max = ibuprofen_ml(wt)
    except Exception:
        ap_ml_1, ap_ml_max, ib_ml_1, ib_ml_max = (0.0,0.0,0.0,0.0)
    colA, colB = st.columns(2)
    with colA:
        st.write(f"아세트아미노펜 1회 권장량: **{ap_ml_1:.1f} mL** (최대 {ap_ml_max:.1f} mL)")
    with colB:
        st.write(f"이부프로펜 1회 권장량: **{ib_ml_1:.1f} mL** (최대 {ib_ml_max:.1f} mL)")
    st.caption("쿨다운: APAP ≥4h, IBU ≥6h. 중복 복용 주의.")

# ====== SPECIAL ======
with t_special:
    st.subheader("특수검사 해석")
    if SPECIAL_PATH:
        st.caption(f"special_tests 로드: {SPECIAL_PATH}")
    lines = special_tests_ui()
    st.session_state['special_interpretations'] = lines or []
    if lines:
        for ln in lines:
            st.write("- " + ln)
    else:
        st.info("아직 입력/선택이 없습니다.")

# ====== REPORT ======
with t_report:
    st.subheader("보고서 (.md/.txt/.pdf) — 모든 항목 포함")
    key_id   = st.session_state.get("key","(미설정)")
    labs     = st.session_state.get("labs_dict", {})
    group    = st.session_state.get("onco_group","")
    disease  = st.session_state.get("onco_disease","")
    dx_disp  = st.session_state.get("dx_disp","(미선택)")
    meds     = st.session_state.get("chemo_keys", [])
    diets    = lab_diet_guides(labs, heme_flag=(group=="혈액암"))
    sym = {
        "혈뇨": st.session_state.get(wkey("sym_hematuria"), False),
        "흑색변": st.session_state.get(wkey("sym_melena"), False),
        "혈변": st.session_state.get(wkey("sym_hematochezia"), False),
        "흉통": st.session_state.get(wkey("sym_chest"), False),
        "호흡곤란": st.session_state.get(wkey("sym_dyspnea"), False),
        "의식저하": st.session_state.get(wkey("sym_confusion"), False),
        "소변량 급감": st.session_state.get(wkey("sym_oliguria"), False),
        "지속 구토": st.session_state.get(wkey("sym_pvomit"), False),
        "점상출혈": st.session_state.get(wkey("sym_petechiae"), False),
    }
    temp = st.session_state.get(wkey("cur_temp"))
    hr   = st.session_state.get(wkey("cur_hr"))
    level, reasons, contrib = emergency_level(labs or {}, temp, hr, {
        "hematuria": sym["혈뇨"], "melena": sym["흑색변"], "hematochezia": sym["혈변"],
        "chest_pain": sym["흉통"], "dyspnea": sym["호흡곤란"], "confusion": sym["의식저하"],
        "oliguria": sym["소변량 급감"], "persistent_vomit": sym["지속 구토"], "petechiae": sym["점상출혈"],
    })
    spec_lines = st.session_state.get('special_interpretations', [])

    st.markdown("#### 내보낼 섹션 선택")
    use_dflt = st.checkbox("기본(모두 포함)", True, key=wkey("rep_all"))
    colp1,colp2 = st.columns(2)
    with colp1:
        sec_profile = st.checkbox("프로필/활력징후", True if use_dflt else False, key=wkey("sec_profile"))
        sec_symptom = st.checkbox("증상 체크", True if use_dflt else False, key=wkey("sec_symptom"))
        sec_emerg   = st.checkbox("응급도 평가(기여도 포함)", True if use_dflt else False, key=wkey("sec_emerg"))
        sec_dx      = st.checkbox("진단명(암 선택)", True if use_dflt else False, key=wkey("sec_dx"))
    with colp2:
        sec_meds    = st.checkbox("항암제 요약/부작용", True if use_dflt else False, key=wkey("sec_meds"))
        sec_labs    = st.checkbox("피수치 전항목", True if use_dflt else False, key=wkey("sec_labs"))
        sec_diet    = st.checkbox("식이가이드", True if use_dflt else False, key=wkey("sec_diet"))
        sec_special = st.checkbox("특수검사 해석", True if use_dflt else False, key=wkey("sec_special"))

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
        lines.append("## 프로필")
        lines.append(f"- 키(별명#PIN): {key_id}")
        lines.append("")
        lines.append("## 활력징후")
        lines.append(f"- 체온(℃): {temp if temp not in (None, '') else '—'}")
        lines.append(f"- 심박수(bpm): {hr if hr not in (None, '') else '—'}")
        lines.append("")

    if sec_symptom:
        lines.append("## 증상 체크(홈)")
        for k,v in sym.items():
            lines.append(f"- {k}: {'예' if v else '아니오'}")
        lines.append("")

    if sec_emerg:
        lines.append("## 응급도 평가")
        lines.append(f"- 현재 응급도: {level}")
        if reasons:
            for r in reasons:
                lines.append(f"  - {r}")
        if contrib:
            lines.append("### 응급도 기여도(Why)")
            total = sum(x["score"] for x in contrib) or 1.0
            for it in sorted(contrib, key=lambda x:-x["score"]):
                pct = round(100.0*it["score"]/total,1)
                lines.append(f"- {it['factor']}: 점수 {round(it['score'],2)} (기본{it['base']}×가중치{it['weight']}, {pct}%)")
        lines.append("")

    if sec_dx:
        lines.append("## 진단명(암)")
        lines.append(f"- 그룹: {group or '(미선택)'}")
        lines.append(f"- 질환: {disease or '(미선택)'}")
        lines.append(f"- 표시: {dx_disp}")
        lines.append("")

    def _aggregate_all_aes(meds, db):
        result = {}
        if not isinstance(meds, (list, tuple)) or not meds: return result
        ae_fields = ["ae","ae_ko","adverse_effects","adverse","side_effects","side_effect","warnings","warning","black_box","boxed_warning","toxicity","precautions","safety","safety_profile","notes"]
        for k in meds:
            rec = db.get(k) if isinstance(db, dict) else None
            lines2 = []
            if isinstance(rec, dict):
                for field in ae_fields:
                    v = rec.get(field)
                    if not v: continue
                    if isinstance(v, str):
                        parts = []
                        for chunk in v.split("\n"):
                            for semi in chunk.split(";"):
                                parts.extend([p.strip() for p in semi.split(",")])
                        lines2 += [p for p in parts if p]
                    elif isinstance(v, (list, tuple)):
                        tmp = []
                        for s in v:
                            for p in str(s).split(","):
                                q = p.strip()
                                if q: tmp.append(q)
                        lines2 += tmp
            seen = set(); uniq = []
            for s in lines2:
                if s not in seen:
                    uniq.append(s); seen.add(s)
            if uniq: result[k] = uniq
        return result

    if sec_meds:
        lines.append("## 항암제 요약")
        if meds:
            for m in meds:
                try: lines.append(f"- {display_label(m, DRUG_DB)}")
                except Exception: lines.append(f"- {m}")
        else:
            lines.append("- (없음)")
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

    if sec_diet and diets:
        lines.append("## 식이가이드(자동)")
        for d in diets: lines.append(f"- {d}")
        lines.append("")

    if sec_special:
        if spec_lines:
            lines.append("## 특수검사 해석")
            for ln in spec_lines: lines.append(f"- {ln}")
            lines.append("")

    md = "\n".join(lines)
    st.code(md, language="markdown")
    st.download_button("💾 보고서 .md 다운로드", data=md.encode("utf-8"), file_name="bloodmap_report.md", mime="text/markdown", key=wkey("dl_md"))
    txt_data = md.replace('**','')
    st.download_button("📝 보고서 .txt 다운로드", data=txt_data.encode("utf-8"), file_name="bloodmap_report.txt", mime="text/plain", key=wkey("dl_txt"))
    try:
        pdf_bytes = export_md_to_pdf(md)
        st.download_button("📄 보고서 .pdf 다운로드", data=pdf_bytes, file_name="bloodmap_report.pdf", mime="application/pdf", key=wkey("dl_pdf"))
    except Exception:
        st.caption("PDF 변환 모듈을 불러오지 못했습니다. .md 또는 .txt를 사용해주세요.")
