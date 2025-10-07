import datetime as _dt
import os, json, sys
from pathlib import Path
import importlib.util
import streamlit as st

# PDF export support
try:
    from pdf_export import export_md_to_pdf
except Exception:
    def export_md_to_pdf(md_text: str) -> bytes:
        return md_text.encode("utf-8")

# -------- Safe banner (no-op if missing) --------
try:
    from branding import render_deploy_banner
except Exception:
    def render_deploy_banner(*a, **k): return None

# Core utils: PIN duplication prevention
try:
    from core_utils import ensure_unique_pin
except Exception:
    def ensure_unique_pin(user_key: str, auto_suffix: bool=True):
        return user_key or "guest#PIN", False, "fallback"

# Oncology maps / drug DB / AE UI
try:
    from onco_map import build_onco_map, dx_display, auto_recs_by_dx
except Exception:
    build_onco_map = lambda: {}
    dx_display = lambda g,d: f"{g} - {d}"
    def auto_recs_by_dx(*args, **kwargs): return {"chemo": [], "targeted": [], "abx": []}

try:
    from drug_db import DRUG_DB, ensure_onco_drug_db, display_label, key_from_label
except Exception:
    DRUG_DB = {}
    def ensure_onco_drug_db(db): pass
    def display_label(k, db=None): return str(k)
    def key_from_label(s, db=None):
        if not s: return ""
        pos = s.find(" (")
        return s[:pos] if pos>0 else s

try:
    from ui_results import collect_top_ae_alerts
except Exception:
    def collect_top_ae_alerts(*a, **k): return []

try:
    from lab_diet import lab_diet_guides
except Exception:
    def lab_diet_guides(labs, heme_flag=False): return []

try:
    from peds_dose import acetaminophen_ml, ibuprofen_ml
except Exception:
    def acetaminophen_ml(*a, **k): return (0.0, 0.0)
    def ibuprofen_ml(*a, **k): return (0.0, 0.0)

# -------- Page config --------
st.set_page_config(page_title="Bloodmap", layout="wide")
st.title("Bloodmap")
st.markdown(
    """> In memory of Eunseo, a little star now shining in the sky.
> This app is made with the hope that she is no longer in pain,
> and resting peacefully in a world free from all hardships."""
)
st.markdown("---")
render_deploy_banner("https://bloodmap.streamlit.app/", "제작: Hoya/GPT · 자문: Hoya/GPT")
st.caption("※ 모든 날짜/시간 표기는 Asia/Seoul 기준입니다.")

# Try to load style.css from the same directory as this file (not cwd)
def _inject_style():
    here = Path(__file__).resolve().parent
    cand = here / "style.css"
    if cand.exists():
        try:
            st.markdown(f"<style>{cand.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
            st.caption("style.css 적용됨")
            return True
        except Exception:
            pass
    return False
_inject_style()

# -------- Globals --------
ensure_onco_drug_db(DRUG_DB)  # DRUG_DB 채우기 (no-op if stub)
ONCO = build_onco_map()

# ====== UI helpers ======
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

def emergency_level(labs: dict, temp_c, hr, symptoms: dict) -> tuple[str, list[str]]:
    anc = labs.get("ANC") if isinstance(labs, dict) else None
    plt = labs.get("PLT") if isinstance(labs, dict) else None
    crp = labs.get("CRP") if isinstance(labs, dict) else None
    hb  = labs.get("Hb")  if isinstance(labs, dict) else None
    alerts = []

    t = temp_c if isinstance(temp_c,(int,float)) else _parse_float(temp_c)
    a = anc if isinstance(anc,(int,float)) else _parse_float(anc)
    p = plt if isinstance(plt,(int,float)) else _parse_float(plt)
    c = crp if isinstance(crp,(int,float)) else _parse_float(crp)
    h = hb  if isinstance(hb,(int,float)) else _parse_float(hb)
    heart = hr if isinstance(hr,(int,float)) else _parse_float(hr)

    W = get_weights()
    risk = 0.0
    if a is not None and a < 500:
        risk += 3 * W["w_anc_lt500"]; alerts.append("ANC<500: 발열 시 응급(FN)")
    elif a is not None and a < 1000:
        risk += 2 * W["w_anc_500_999"]; alerts.append("ANC 500~999: 감염 주의")
    if t is not None and t >= 38.5:
        risk += 2 * W["w_temp_ge_38_5"]; alerts.append("고열(≥38.5℃)")
    elif t is not None and t >= 38.0:
        risk += 1 * W["w_temp_38_0_38_4"]; alerts.append("발열(38.0~38.4℃)")
    if p is not None and p < 20000:
        risk += 2 * W["w_plt_lt20k"]; alerts.append("혈소판 <20k: 출혈 위험")
    if h is not None and h < 7.0:
        risk += 1 * W["w_hb_lt7"]; alerts.append("중증 빈혈(Hb<7)")
    if c is not None and c >= 10:
        risk += 1 * W["w_crp_ge10"]; alerts.append("CRP 높음(≥10)")
    if heart and heart > 130:
        risk += 1 * W["w_hr_gt130"]; alerts.append("빈맥")

    if symptoms.get("hematuria"):  risk += 1 * W["w_hematuria"]; alerts.append("혈뇨")
    if symptoms.get("melena"):     risk += 2 * W["w_melena"]; alerts.append("흑색변(상부위장관 출혈 의심)")
    if symptoms.get("hematochezia"): risk += 2 * W["w_hematochezia"]; alerts.append("혈변(하부위장관 출혈 의심)")
    if symptoms.get("chest_pain"): risk += 2 * W["w_chest_pain"]; alerts.append("흉통")
    if symptoms.get("dyspnea"):    risk += 2 * W["w_dyspnea"]; alerts.append("호흡곤란")
    if symptoms.get("confusion"):  risk += 3 * W["w_confusion"]; alerts.append("의식저하/혼돈")
    if symptoms.get("oliguria"):   risk += 2 * W["w_oliguria"]; alerts.append("소변량 급감(탈수/신장 문제 의심)")
    if symptoms.get("persistent_vomit"): risk += 2 * W["w_persistent_vomit"]; alerts.append("지속 구토")
    if symptoms.get("petechiae"):  risk += 2 * W["w_petechiae"]; alerts.append("점상출혈")

    if risk >= 5: return "🚨 응급", alerts
    if risk >= 2: return "🟧 주의", alerts
    return "🟢 안심", alerts

# ---- AE aggregation helper (comma/semicolon/newline aware) ----
def _aggregate_all_aes(meds, db):
    result = {}
    if not isinstance(meds, (list, tuple)) or not meds:
        return result
    ae_fields = [
        "ae","ae_ko","adverse_effects","adverse","side_effects","side_effect",
        "warnings","warning","black_box","boxed_warning","toxicity","precautions",
        "safety","safety_profile","notes"
    ]
    for k in meds:
        rec = db.get(k) if isinstance(db, dict) else None
        lines = []
        if isinstance(rec, dict):
            for field in ae_fields:
                v = rec.get(field)
                if not v:
                    continue
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

# ====== LAB REFERENCE/VALIDATION ======
LAB_REF_ADULT = {
    "WBC": (4.0, 10.0), "Hb": (12.0, 16.0), "PLT": (150, 400),
    "ANC": (1500, 8000), "CRP": (0.0, 5.0), "Na": (135, 145),
    "Cr": (0.5, 1.2), "Glu": (70, 140), "Ca": (8.6, 10.2),
    "P": (2.5, 4.5), "T.P": (6.4, 8.3), "AST": (0, 40), "ALT": (0, 41),
    "T.B": (0.2, 1.2), "Alb": (3.5, 5.0), "BUN": (7, 20)
}
LAB_REF_PEDS = {
    "WBC": (5.0, 14.0), "Hb": (11.0, 15.0), "PLT": (150, 450),
    "ANC": (1500, 8000), "CRP": (0.0, 5.0), "Na": (135, 145),
    "Cr": (0.2, 0.8), "Glu": (70, 140), "Ca": (8.8, 10.8),
    "P": (4.0, 6.5), "T.P": (6.0, 8.0), "AST": (0, 50), "ALT": (0, 40),
    "T.B": (0.2, 1.2), "Alb": (3.8, 5.4), "BUN": (5, 18)
}
def lab_ref(is_peds: bool):
    return LAB_REF_PEDS if is_peds else LAB_REF_ADULT
def lab_validate(abbr: str, val, is_peds: bool):
    rng = lab_ref(is_peds).get(abbr)
    if rng is None or val in (None, ""): return None
    try:
        v = float(val)
    except Exception:
        return "형식 오류"
    lo, hi = rng
    if v < lo: return f"⬇️ 기준치 미만({lo}~{hi})"
    if v > hi: return f"⬆️ 기준치 초과({lo}~{hi})"
    return "정상범위"

# ====== Sidebar (PIN unique + vitals + profile save/load) ======
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

# ====== Tabs (fixed labels) ======
tab_labels = ["🏠 홈","🧪 피수치 입력","🧬 암 선택","💊 항암제","👶 소아 증상","🔬 특수검사","📄 보고서"]
t_home, t_labs, t_dx, t_chemo, t_peds, t_special, t_report = st.tabs(tab_labels)

# ====== HOME ======
with t_home:
    st.subheader("요약")
    labs = st.session_state.get("labs_dict", {})
    level_tmp, reasons_tmp = emergency_level(labs, st.session_state.get(wkey("cur_temp")), st.session_state.get(wkey("cur_hr")), {})
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

    level, reasons = emergency_level(labs, st.session_state.get(wkey("cur_temp")), st.session_state.get(wkey("cur_hr")), sym)
    if level.startswith("🚨"):
        st.error("응급도: " + level + " — " + " · ".join(reasons))
    elif level.startswith("🟧"):
        st.warning("응급도: " + level + " — " + " · ".join(reasons))
    else:
        st.info("응급도: " + level + (" — " + " · ".join(reasons) if reasons else ""))

    # --- 환경 진단 패널 (module origin 기반) ---
    import importlib
    with st.expander("🛠 환경 진단(모듈 경로 기반)", expanded=False):
        st.write(f"cwd: {os.getcwd()}")
        here = Path(__file__).resolve().parent
        st.write(f"app dir: {here}")
        targets = [
            ("pdf_export","pdf_export.py"),("special_tests","special_tests.py"),
            ("drug_db","drug_db.py"),("onco_map","onco_map.py"),
            ("ui_results","ui_results.py"),("lab_diet","lab_diet.py"),
            ("peds_dose","peds_dose.py"),("branding","branding.py"),
        ]
        rows = []
        for modname, fname in targets:
            try:
                spec = importlib.util.find_spec(modname)
                ok_imp = spec is not None
                origin = spec.origin if spec else "(not found)"
                file_ok = Path(origin).exists() if spec and origin else False
                rows.append(f"- {fname}: {'✅' if file_ok else '❌'} | import: {'✅' if ok_imp else '❌'} | path: {origin}")
            except Exception as e:
                rows.append(f"- {fname}: ❌ | import: ❌ | err: {e}")
        css_here = (here / "style.css")
        css_cwd  = Path(os.getcwd()) / "style.css"
        rows.append(f"- style.css (app dir): {'✅' if css_here.exists() else '❌'} | {css_here}")
        rows.append(f"- style.css (cwd): {'✅' if css_cwd.exists() else '❌'} | {css_cwd}")
        app_self = Path(__file__)
        rows.append(f"- app.py path: {app_self}")
        st.write("\n".join(rows))

# ====== LABS ======
with t_labs:
    st.subheader("피수치 입력 (요청 순서) — ± 버튼 없이 직접 숫자 입력")
    st.caption("표기 예: 4.5 / 135 / 0.8  (숫자와 소수점만 입력)")
    use_peds = st.checkbox("소아 기준(참조범위/검증에 적용)", value=False, key=wkey("labs_use_peds"))

    order = [
        ("WBC","백혈구"), ("Ca","칼슘"), ("Glu","혈당"), ("CRP","CRP"),
        ("Hb","혈색소"), ("P","인(Phosphorus)"), ("T.P","총단백"), ("Cr","크레아티닌"),
        ("PLT","혈소판"), ("Na","나트륨"), ("AST","AST"), ("T.B","총빌리루빈"),
        ("ANC","절대호중구"), ("Alb","알부민"), ("ALT","ALT"), ("BUN","BUN")
    ]

    cols = st.columns(4)
    values = {}
    for idx, (abbr, kor) in enumerate(order):
        col = cols[idx % 4]
        with col:
            values[abbr] = float_input(f"{abbr} — {kor}", key=wkey(abbr))
            msg = lab_validate(abbr, values[abbr], use_peds)
            if msg:
                if msg == "정상범위":
                    st.caption("✅ " + msg)
                elif msg == "형식 오류":
                    st.warning("형식 오류: 숫자만 입력", icon="⚠️")
                else:
                    st.warning(msg, icon="⚠️")

    labs_dict = st.session_state.get("labs_dict", {})
    labs_dict.update(values)
    st.session_state["labs_dict"] = labs_dict

    st.markdown(f"**ANC 분류:** {anc_band(values.get('ANC'))}")

    st.markdown("### 현재 입력값 요약")
    nonempty = [(abbr, labs_dict.get(abbr)) for abbr,_ in order if labs_dict.get(abbr) not in (None, "")]
    if nonempty:
        for abbr, val in nonempty:
            rng = lab_ref(use_peds).get(abbr)
            rng_txt = f" ({rng[0]}~{rng[1]})" if rng else ""
            st.write(f"- **{abbr}**: {val}{rng_txt}")
    else:
        st.caption("아직 입력된 값이 없습니다. 위의 칸에 숫자를 입력하면 여기서 즉시 보입니다.")

    current_group = st.session_state.get("onco_group", "")
    heme_flag = True if current_group == "혈액암" else False
    diets = lab_diet_guides(labs_dict, heme_flag=heme_flag)
    if diets:
        st.markdown("### 🍚 식이가이드(자동)")
        for line in diets:
            st.write("- " + line)

# ====== DX: 온코 그룹/암종 전체 맵 ======
with t_dx:
    st.subheader("암 선택")
    groups = list(ONCO.keys())
    if not groups:
        st.info("진단 맵을 불러오지 못했습니다.")
    else:
        grp_tabs = st.tabs(groups)
        for i, g in enumerate(groups):
            with grp_tabs[i]:
                dx_names = list((ONCO.get(g) or {}).keys())
                if not dx_names:
                    st.caption("항목 없음")
                    continue
                disp = [dx_display(g, d) for d in dx_names]
                sel = st.selectbox("진단명을 선택하세요", disp, key=wkey(f"dx_sel_{i}"))
                if st.button("선택 저장", key=wkey(f"dx_save_{i}")):
                    idx = disp.index(sel)
                    picked = dx_names[idx]
                    st.session_state["dx_raw"] = picked
                    st.session_state["dx_disp"] = sel
                    st.session_state["onco_group"] = g
                    st.success(f"저장됨: {sel}")

# ====== CHEMO ======
with t_chemo:
    st.subheader("항암제")
    dx = st.session_state.get("dx_raw")
    g  = st.session_state.get("onco_group")
    if not dx or not g:
        st.info("먼저 '암 선택'에서 저장하세요.")
    else:
        st.write(f"현재 진단: **{st.session_state.get('dx_disp','')}**")
        recs = auto_recs_by_dx(g, dx, DRUG_DB, ONCO)
        base_list = recs.get("chemo", []) + recs.get("targeted", []) + recs.get("abx", [])
        base_list = [k for k in base_list if k]
        options = [display_label(k, DRUG_DB) for k in base_list]
        default = options
        picked_labels = st.multiselect("항암제를 선택/추가", options, default=default, key=wkey("chemo_ms"))
        extra = st.text_input("추가 항암제(쉼표 구분, 예: Vancomycin, Cefepime)", key=wkey("chemo_extra"))
        picked_keys = [key_from_label(lbl) for lbl in picked_labels]
        if extra.strip():
            more = [key_from_label(x.strip()) for x in extra.split(",") if x.strip()]
            for x in more:
                if x and x not in picked_keys:
                    picked_keys.append(x)
        if st.button("항암제 저장", key=wkey("chemo_save")):
            st.session_state["chemo_keys"] = picked_keys
            st.success("저장됨. 홈/보고서에서 확인")

# ====== PEDS (symptom-based scoring + antipyretic dosing) ======
with t_peds:
    st.subheader("소아 증상 입력 → 점수 기반 병명 추정 + 해열제 계산")
    st.caption("질병을 미리 고르지 않습니다. 증상만 선택하면 자동으로 점수화해 상위 의심 질환군을 보여줍니다.")
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
    if "38.5" in fever or "39" in fever:
        score["상기도/독감 계열"] += 25
    if cough in ["보통","심함","조금"]:
        score["상기도/독감 계열"] += 20
    if eye in ["노랑-농성","양쪽"]:
        score["결막염 의심"] += 30
    if oliguria:
        score["탈수/신장 문제"] += 40; score["장염 의심"] += 10
    if persistent_vomit:
        score["장염 의심"] += 25; score["탈수/신장 문제"] += 15
    if petechiae:
        score["출혈성 경향"] += 60

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
    try:
        # 체중(kg)만 알고 있을 때 peds_dose API는 age_months=0, weight_kg=체중 으로 호출
        wcol1,wcol2,wcol3 = st.columns([2,1,2])
        with wcol1:
            wt = st.text_input("체중(kg)", value=st.session_state.get(wkey("wt_peds"), ""), key=wkey("wt_peds"), placeholder="예: 12.5")
        wt_val = None
        try:
            wt_val = float(str(wt).strip()) if wt else None
        except Exception:
            wt_val = None

        ap_ml_1 = ib_ml_1 = 0.0
        ap_ml_24h = ib_ml_24h = 0.0

        if wt_val and wt_val > 0:
            try:
                ap_ml_1, _w = acetaminophen_ml(age_months=0, weight_kg=wt_val)
            except Exception:
                ap_ml_1 = 0.0
            try:
                ib_ml_1, _w2 = ibuprofen_ml(age_months=0, weight_kg=wt_val)
            except Exception:
                ib_ml_1 = 0.0

            # 프로젝트 보수 한도: 24시간 최대 4회표시(APAP≥4h, IBU≥6h와 합치)
            ap_ml_24h = round(ap_ml_1 * 4, 0) if ap_ml_1 else 0.0
            ib_ml_24h = round(ib_ml_1 * 4, 0) if ib_ml_1 else 0.0

        with wcol2:
            st.metric("APAP 1회량(ml)", f"{ap_ml_1:.1f}" if ap_ml_1 else "—")
            st.metric("APAP 24h 최대(ml)", f"{ap_ml_24h:.0f}" if ap_ml_24h else "—")
        with wcol3:
            st.metric("IBU 1회량(ml)", f"{ib_ml_1:.1f}" if ib_ml_1 else "—")
            st.metric("IBU 24h 최대(ml)", f"{ib_ml_24h:.0f}" if ib_ml_24h else "—")
        st.caption("쿨다운: APAP ≥4시간, IBU ≥6시간. 중복 복용 주의.")
    except Exception:
        st.caption("peds_dose 모듈이 없어 계산기 일부가 제한됩니다.")

# ====== SPECIAL ======
with t_special:
    try:
        from special_tests import special_tests_ui
        lines = special_tests_ui()
        st.session_state['special_interpretations'] = lines or []
        st.subheader("특수검사 해석")
        if lines:
            for ln in lines:
                st.write("- " + ln)
        else:
            st.info("아직 입력/선택이 없습니다. 위의 '🧪 특수검사'에서 항목을 켜고 값을 넣으면 해석이 여기에 표시됩니다.")
    except Exception:
        st.error("특수검사 모듈을 불러오지 못했습니다.")

# ====== REPORT ======
with t_report:
    st.subheader("보고서 (.md/.txt/.pdf) — 모든 항목 포함")
    key_id   = st.session_state.get("key","(미설정)")
    dx_disp  = st.session_state.get("dx_disp","(미선택)")
    meds     = st.session_state.get("chemo_keys", [])
    labs     = st.session_state.get("labs_dict", {})
    group    = st.session_state.get("onco_group","")
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
    level, reasons = emergency_level(labs or {}, temp, hr, {
        "hematuria": sym["혈뇨"], "melena": sym["흑색변"], "hematochezia": sym["혈변"],
        "chest_pain": sym["흉통"], "dyspnea": sym["호흡곤란"], "confusion": sym["의식저하"],
        "oliguria": sym["소변량 급감"], "persistent_vomit": sym["지속 구토"], "petechiae": sym["점상출혈"],
    })
    spec_lines = st.session_state.get('special_interpretations', [])

    lines = []
    lines.append("# Bloodmap Report (Full)")
    lines.append(f"_생성 시각(KST): {_dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_")
    lines.append("")
    # Dedication
    lines.append("> In memory of Eunseo, a little star now shining in the sky.")
    lines.append("> This app is made with the hope that she is no longer in pain,")
    lines.append("> and resting peacefully in a world free from all hardships.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 프로필")
    lines.append(f"- 키(별명#PIN): {key_id}")
    lines.append("")
    lines.append("## 활력징후")
    lines.append(f"- 체온(℃): {temp if temp not in (None, '') else '—'}")
    lines.append(f"- 심박수(bpm): {hr if hr not in (None, '') else '—'}")
    lines.append("")
    lines.append("## 증상 체크(홈)")
    for k,v in sym.items():
        lines.append(f"- {k}: {'예' if v else '아니오'}")
    lines.append("")
    lines.append("## 응급도 평가")
    lines.append(f"- 현재 응급도: {level}")
    if reasons:
        for r in reasons:
            lines.append(f"  - {r}")
    else:
        lines.append("  - (특이 소견 없음)")
    lines.append("")
    lines.append("## 진단명")
    lines.append(f"- {dx_disp}")
    lines.append("")
    lines.append("## 항암제 요약")
    if meds:
        for m in meds:
            try:
                lines.append(f"- {display_label(m, DRUG_DB)}")
            except Exception:
                lines.append(f"- {m}")
    else:
        lines.append("- (없음)")
    lines.append("")
    # Full AE list (only when available)
    if meds:
        ae_map = _aggregate_all_aes(meds, DRUG_DB)
        if ae_map:
            lines.append("## 항암제 부작용(전체)")
            for k, arr in ae_map.items():
                try:
                    nm = display_label(k, DRUG_DB)
                except Exception:
                    nm = k
                lines.append(f"- {nm}")
                for ln in arr:
                    lines.append(f"  - {ln}")
            lines.append("")
    lines.append("## 피수치 (모든 항목)")
    all_labs = [("WBC","백혈구"),("Ca","칼슘"),("Glu","혈당"),("CRP","CRP"),
                ("Hb","혈색소"),("P","인(Phosphorus)"),("T.P","총단백"),("Cr","크레아티닌"),
                ("PLT","혈소판"),("Na","나트륨"),("AST","AST"),("T.B","총빌리루빈"),
                ("ANC","절대호중구"),("Alb","알부민"),("ALT","ALT"),("BUN","BUN")]
    for abbr, kor in all_labs:
        v = labs.get(abbr) if isinstance(labs, dict) else None
        lines.append(f"- {abbr} ({kor}): {v if v not in (None, '') else '—'}")
    lines.append(f"- ANC 분류: {anc_band(labs.get('ANC') if isinstance(labs, dict) else None)}")
    if diets:
        lines.append("")
        lines.append("## 식이가이드(자동)")
        for d in diets: lines.append(f"- {d}")
    if spec_lines:
        lines.append("")
        lines.append("## 특수검사 해석")
        for ln in spec_lines: lines.append(f"- {ln}")
    lines.append("")
    md = "\n".join(lines)
    st.code(md, language="markdown")

    st.download_button("💾 보고서 .md 다운로드", data=md.encode("utf-8"),
                    file_name="bloodmap_report.md", mime="text/markdown", key=wkey("dl_md"))
    txt_data = md.replace('**','')
    st.download_button("📝 보고서 .txt 다운로드", data=txt_data.encode("utf-8"),
                    file_name="bloodmap_report.txt", mime="text/plain", key=wkey("dl_txt"))
    try:
        pdf_bytes = export_md_to_pdf(md)
        st.download_button("📄 보고서 .pdf 다운로드", data=pdf_bytes,
                        file_name="bloodmap_report.pdf", mime="application/pdf", key=wkey("dl_pdf"))
    except Exception:
        st.caption("PDF 변환 모듈을 불러오지 못했습니다. .md 또는 .txt를 사용해주세요.")
