
# -*- coding: utf-8 -*-
import os, sys, json
from pathlib import Path
import streamlit as st

# ======================== SAFE PATH / IMPORT LAYER ============================
APP_DIR = Path(__file__).resolve().parent
CANDIDATE_ROOTS = [
    APP_DIR,
    APP_DIR.parent,
    Path("/mount/src/hoya12/bloodmap_app"),
    Path("/mnt/data"),
]

def resolve_path(*relparts, must_exist=True):
    rel = Path(*relparts)
    for root in CANDIDATE_ROOTS:
        p = (root / rel).resolve()
        if p.exists() or not must_exist:
            return p
    return None

def import_from_file(mod_name, candidates):
    import importlib.util
    for cand in candidates:
        if not cand: 
            continue
        p = cand if isinstance(cand, Path) else Path(cand)
        if p.exists():
            spec = importlib.util.spec_from_file_location(mod_name, str(p))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            sys.modules[mod_name] = mod
            return mod, str(p)
    return None, None

SAVE_DIR = Path(os.environ.get("BLOODMAP_SAVE_DIR", "/tmp")).resolve()
SAVE_DIR.mkdir(parents=True, exist_ok=True)
AUTOSAVE_JSON = SAVE_DIR / "autosave.json"

onco_map, ONCO_MAP_PATH = import_from_file("onco_map", [
    resolve_path("onco_map.py"),
    resolve_path("../onco_map.py"),
    resolve_path("/mnt/data/onco_map.py", must_exist=False),
])
special_tests, SPECIAL_TESTS_PATH = import_from_file("special_tests", [
    resolve_path("special_tests.py"),
    resolve_path("../special_tests.py"),
    resolve_path("/mnt/data/special_tests.py", must_exist=False),
])
lab_diet, LAB_DIET_PATH = import_from_file("lab_diet", [
    resolve_path("lab_diet.py"),
    resolve_path("../lab_diet.py"),
    resolve_path("/mnt/data/lab_diet.py", must_exist=False),
])
pdf_export, PDF_EXPORT_PATH = import_from_file("pdf_export", [
    resolve_path("pdf_export.py"),
    resolve_path("../pdf_export.py"),
    resolve_path("/mnt/data/pdf_export.py", must_exist=False),
])

# ============================== UTILITIES =====================================
def wkey(name: str) -> str:
    """Per-user namespacing for widget keys to avoid duplicates."""
    uid = st.session_state.get("_uid", "user")
    return f"{uid}:{name}"

def autosave_state():
    try:
        data = {k: v for k, v in st.session_state.items() if isinstance(k, str)}
        AUTOSAVE_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        st.warning(f"자동 저장 실패: {e}")

def _parse_float(x):
    try:
        if x is None or x == "":
            return None
        if isinstance(x, (int, float)):
            return float(x)
        s = str(x).replace(",", "").strip()
        return float(s)
    except Exception:
        return None

def safe_download(label: str, *, data: bytes|str|None=None, file_path: str|Path|None=None,
                  file_name: str="download.txt", mime: str="text/plain", key: str|None=None):
    if data is None and (not file_path or not Path(file_path).exists()):
        st.error("⚠️ 파일을 찾을 수 없습니다")
        return
    if data is None:
        data = Path(file_path).read_bytes()
    st.download_button(label, data=data, file_name=file_name, mime=mime, key=key)

# ========================= SESSION DEFAULTS ===================================
if "_uid" not in st.session_state:
    st.session_state["_uid"] = "local"
if "peds_notes" not in st.session_state:
    st.session_state["peds_notes"] = []
if "peds_actions" not in st.session_state:
    st.session_state["peds_actions"] = []
if "labs_dict" not in st.session_state:
    st.session_state["labs_dict"] = {}
if "onco_group" not in st.session_state:
    st.session_state["onco_group"] = ""
if "onco_dx" not in st.session_state:
    st.session_state["onco_dx"] = ""
if "selected_agents" not in st.session_state:
    st.session_state["selected_agents"] = []

# ============================ DIAGNOSTICS PANEL ===============================
def diagnostics_panel():
    st.subheader("🔧 진단 패널 (경로/모듈 상태)")
    def flag(ok): return "✅ 로드됨" if ok else "❌ 오류/미발견"
    st.write(f"onco_map: {flag(bool(onco_map))} — 경로: {ONCO_MAP_PATH or 'N/A'}")
    st.write(f"special_tests: {flag(bool(special_tests))} — 경로: {SPECIAL_TESTS_PATH or 'N/A'}")
    st.write(f"lab_diet: {flag(bool(lab_diet))} — 경로: {LAB_DIET_PATH or 'N/A'}")
    st.write(f"pdf_export: {flag(bool(pdf_export))} — 경로: {PDF_EXPORT_PATH or 'N/A'}")
    st.caption(f"자동저장 파일: {AUTOSAVE_JSON}")

# ============================= ONCO SELECTION =================================
def load_onco():
    if onco_map and hasattr(onco_map, "ONCO_GROUPS"):
        groups = list(onco_map.ONCO_GROUPS.keys())
        dx_map = onco_map.ONCO_GROUPS
    else:
        groups = ["혈액암", "고형암"]
        dx_map = {
            "혈액암": ["APL", "AML", "ALL", "CML", "CLL", "DLBCL", "Hodgkin", "다발골수종"],
            "고형암": ["Colon/Rectal", "Gastric", "Pancreas", "Biliary", "Hepatocellular",
                      "Breast", "NSCLC", "SCLC", "Head & Neck", "NPC",
                      "Ovary", "Cervix", "Prostate", "GIST", "RCC", "Glioma"],
        }
    return groups, dx_map

def onco_select_ui():
    groups, dx_map = load_onco()
    st.session_state["onco_group"] = st.selectbox("암종 그룹", groups, key=wkey("onco_group"))
    choices = dx_map.get(st.session_state["onco_group"], [])
    st.session_state["onco_dx"] = st.selectbox("진단(암종)", choices, key=wkey("onco_dx"))

# ============================== CHEMO SECTION =================================
# Minimal DB + protocols (확장 가능)
CHEMO_PROTOCOLS = {
 "APL": ["ATRA (Tretinoin)", "Arsenic Trioxide (ATO)", "Doxorubicin", "Idarubicin", "Daunorubicin"],
 "AML": ["Cytarabine", "Daunorubicin", "Idarubicin", "Etoposide"],
 "ALL": ["Vincristine", "Methotrexate (MTX)", "Mercaptopurine (6-MP)", "Prednisone", "Pegaspargase"],
 "CML": ["Imatinib", "Dasatinib", "Nilotinib"],
 "CLL": ["Ibrutinib", "Acalabrutinib", "Venetoclax", "Rituximab"],
 "DLBCL": ["Rituximab", "Cyclophosphamide", "Doxorubicin", "Vincristine", "Prednisone"],
 "Hodgkin": ["Doxorubicin", "Dacarbazine", "Vinblastine"],
 "Multiple Myeloma": ["Bortezomib", "Lenalidomide", "Prednisone", "Carfilzomib", "Daratumumab"],
 "Colon/Rectal": ["5-FU", "Capecitabine", "Oxaliplatin", "Irinotecan", "Bevacizumab"],
 "Gastric": ["Capecitabine", "5-FU", "Oxaliplatin", "Cisplatin", "Trastuzumab"],
 "Pancreas": ["Gemcitabine", "Nab-Paclitaxel", "Irinotecan", "Oxaliplatin"],
 "Biliary": ["Gemcitabine", "Cisplatin"],
 "Hepatocellular": ["Atezolizumab", "Bevacizumab", "Sorafenib", "Lenvatinib"],
 "Breast": ["Cyclophosphamide", "Doxorubicin", "Paclitaxel", "Docetaxel", "Trastuzumab", "Pertuzumab", "AIs"],
 "NSCLC": ["Cisplatin", "Carboplatin", "Pemetrexed", "Paclitaxel", "Docetaxel", "Osimertinib", "Pembrolizumab"],
 "SCLC": ["Cisplatin", "Carboplatin", "Etoposide"],
 "Head & Neck": ["Cisplatin", "5-FU", "Cetuximab"],
 "NPC": ["Cisplatin", "5-FU"],
 "Ovary": ["Carboplatin", "Paclitaxel", "Bevacizumab", "Olaparib"],
 "Cervix": ["Cisplatin", "Paclitaxel", "Bevacizumab", "Pembrolizumab"],
 "Prostate": ["Docetaxel", "Abiraterone", "Enzalutamide"],
 "GIST": ["Imatinib", "Sunitinib", "Regorafenib"],
 "RCC": ["Sunitinib", "Pazopanib", "Nivolumab", "Ipilimumab"],
 "Glioma": ["Temozolomide"],
}

def suggest_agents_by_onco(group: str, dx: str):
    key = (dx or "").upper()
    for k, agents in CHEMO_PROTOCOLS.items():
        if k.upper() in key:
            return agents
    return CHEMO_PROTOCOLS.get(dx, [])

def chemo_ui():
    st.markdown("### 💊 항암제")
    all_options = sorted({a for arr in CHEMO_PROTOCOLS.values() for a in arr})
    selected = st.multiselect("항암제 선택", all_options, key=wkey("agents"))
    if st.button("암종 기반 추천 항암제 불러오기", key=wkey("load_proto")):
        sug = suggest_agents_by_onco(st.session_state.get("onco_group"), st.session_state.get("onco_dx"))
        if sug:
            st.session_state["selected_agents"] = sug
            st.success("암종 기반 추천 적용됨")
        else:
            st.info("추천 목록 없음")
    st.session_state["selected_agents"] = st.session_state.get("selected_agents") or selected

# ============================== LABS + DIET ===================================
LAB_KEYS = ["WBC","Hb","Plt","ANC","Ca","P","Na","K","Alb","Glu","TP","AST","ALT","LD","CRP","Cr","UA","Tb"]

def labs_ui():
    st.markdown("### 🧪 피수치 입력")
    cols = st.columns(3)
    values = {}
    for i, key in enumerate(LAB_KEYS):
        with cols[i%3]:
            values[key] = st.text_input(key, value="", key=wkey(f"lab_{key}"))
    st.session_state["labs_dict"] = values

def diet_guides(context=None, key_prefix="diet_"):
    st.markdown("### 🥗 식이가이드")
    # Try lab_diet first
    if lab_diet and hasattr(lab_diet, "build_diet_ui"):
        try:
            lab_diet.build_diet_ui(st.session_state.get("labs_dict", {}), key_prefix=key_prefix)
            return
        except Exception as e:
            st.warning(f"lab_diet 연동 오류: {e}")
    # Fallback minimal rules (only show when 해당 수치가 입력되어 있고 위험 범위인 경우)
    labs = st.session_state.get("labs_dict", {})
    def get(k): return _parse_float(labs.get(k))
    shown = False
    if (get("ANC") is not None) and get("ANC") < 500:
        st.write("- (수치) **ANC 낮음**: 날 것 금지, 충분히 익혀서, 과일은 껍질 제거/데치기")
        shown = True
    if (get("Na") is not None) and get("Na") < 135:
        st.write("- (수치) **저나트륨혈증**: 자유수 과다섭취 주의, 수분계획은 지시 따르기")
        shown = True
    if (get("K") is not None) and get("K") > 5.0:
        st.write("- (수치) **고칼륨혈증**: 바나나·오렌지·토마토·감자 등 고칼륨식 다량 섭취 피하기, 채소는 데쳐서")
        shown = True
    if not shown:
        st.caption("입력된 수치에서 식이가이드 필요 항목이 없습니다.")

# ============================== SPECIAL TESTS =================================
def special_tests_ui():
    st.markdown("### 🧬 특수검사")
    if special_tests and hasattr(special_tests, "SPECIAL_TESTS"):
        for k, v in special_tests.SPECIAL_TESTS.items():
            with st.expander(k):
                st.write(v.get("indication",""))
                st.write(v.get("prep",""))
    else:
        st.info("특수검사 모듈을 찾지 못했습니다.")

# ============================== BP CLASS ======================================
def bp_classify():
    st.markdown("### ⏱️ 혈압 체크")
    sbp = _parse_float(st.text_input("수축기(mmHg)", key=wkey("sbp")))
    dbp = _parse_float(st.text_input("이완기(mmHg)", key=wkey("dbp")))
    if sbp is None or dbp is None:
        st.write("— SBP/DBP를 입력하세요.")
        return "측정값 없음"
    if sbp >= 140 or dbp >= 90: c = "고혈압 의심"
    elif sbp < 90 or dbp < 60: c = "저혈압/저관류 주의"
    else: c = "정상 범위"
    st.write(f"판정: **{c}**")
    return f"SBP {sbp} / DBP {dbp} — {c}"

# ============================= PEDS GUIDE =====================================
def render_caregiver_notes_peds(
    *,
    stool, fever, persistent_vomit, oliguria, cough, nasal, eye,
    abd_pain, ear_pain, rash, hives, migraine, hfmd,
    constipation=False, anc_low=None, diarrhea=False, key_prefix="peds_",
    wheeze=False, sob=False, throat=False, dysuria=False, hematuria=False
):
    st.header("🧒 소아가이드")
    # ANC 자동 판단
    if anc_low is None:
        anc_val = _parse_float(st.session_state.get("labs_dict", {}).get("ANC"))
        anc_low = (anc_val is not None and anc_val < 500)
    notes = []
    actions = []
    def add_action(title, tips):
        if tips:
            actions.append((title, tips))
            notes.append(f"{title} — {tips[0]}")
    # Fever
    if str(fever) in ["38~38.5","38.5~39","39 이상"]:
        add_action("🌡️ 발열 대처", [
            "옷 가볍게·실내 25–26℃·소량씩 자주 물/ORS",
            "아세트아미노펜 10–15 mg/kg q4–6h, 이부프로펜 10 mg/kg q6–8h(≥6개월); 교차 시 서로 최소 2h",
            "3–5일 지속/조절 어려움·경련·호흡곤란 동반 시 평가"
        ])
    # Diarrhea
    if bool(diarrhea) or (str(stool) in ["3~4회","5~6회","7회 이상"]):
        add_action("💩 설사 대처", [
            "ORS: 1시간 10–20 mL/kg, 이후 1회당 5–10 mL/kg 보충",
            "탄산/아이스 피하고 미지근한 수분"
        ])
    # Constipation
    if bool(constipation):
        add_action("🚻 변비 대처", [
            "수분 50–60 mL/kg/일(지시 범위), 식후 좌변 10–15분",
            "섬유(귀리·프룬·키위·통곡·익힌 채소)"
        ])
    # Vomiting / Oliguria
    if bool(persistent_vomit):
        add_action("🤮 구토", ["소량씩 자주 투명한 수분부터, 탈수/혈성 구토 시 평가"])
    if bool(oliguria):
        add_action("🚨 소변량 급감", ["탈수 가능성 — 수분 계획 재점검, 필요 시 의료평가"])
    # Respiratory
    if str(cough) in ["보통","심함"] or str(nasal) in ["진득","누런"]:
        add_action("🤧 기침/코막힘", ["비강 세척/가습, 간격 준수, 호흡 곤란·늑간함몰 시 평가"])
    if bool(wheeze) or bool(sob):
        add_action("🫁 쌕쌕거림/호흡곤란", ["숨 가쁨·늑간함몰·말수 줄면 즉시 평가", "속효성 기관지확장제 지시 사용, 반응 없으면 진료"])
    # Throat
    if bool(throat):
        add_action("🗣️ 인후통", ["미지근한 물/꿀(>1세)/가글, 자극적 음식 피하기", "고열·연하곤란·호흡곤란 시 평가"])
    # Otitis
    if str(ear_pain) in ["보통","심함"]:
        add_action("👂 귀 통증", [
            "해열·진통제 간격 준수, **귀에 물 들어가지 않게**(샤워/수영 주의)",
            "샤워 후 고개 기울여 물 빼기, 드라이어 약풍 멀리서",
            "분비물/천공 의심 시 점이제 자가 금지·평가"
        ])
    # Eye
    if str(eye) in ["노랑-농성","양쪽"]:
        add_action("👁️ 결막염 의심", ["손씻기·수건/베개 공유 금지", "농성·통증·시력저하 시 평가"])
    # Abd pain
    if str(abd_pain) in ["보통","심함"]:
        add_action("🤕 복통", ["우하복부 국소통/보행 악화/반발통·발열 → 충수염 평가"])
    # Skin/Allergy
    if bool(rash):
        add_action("🌿 피부 발진", ["미온수 샤워·자극 회피, 심한 가려움 냉찜질", "점상출혈/점막병변/호흡곤란 시 즉시"])
    if bool(hives):
        add_action("🍤 두드러기", ["원인 음식/약 중단", "입술/혀부종·호흡곤란 → 아나필락시스 119/응급실"])
    # UTI
    if bool(dysuria) or bool(hematuria):
        add_action("🚻 배뇨 통증/혈뇨", ["수분 증가, 발열·옆구리 통증 동반 시 소변검사 평가"])
    # Headache / HFMD
    if bool(migraine):
        add_action("🧠 두통", ["수분/휴식, 반복 구토·신경학적 이상 시 평가"])
    if bool(hfmd):
        add_action("🖐️ 수족구", ["수분·통증 조절, 입안 통증 시 차가운 음식", "탈수 징후·고열 지속 시 평가"])
    # ANC
    if anc_low:
        add_action("🍽️ ANC 낮음 위생/식이", ["날 것 금지·충분히 익히기", "과일 껍질 제거/데치기", "조리 후 2시간 이내 섭취·뷔페/회/생채소 금지"])

    if actions:
        st.subheader("✅ 증상 입력 기반 즉시 가이드")
        for title, tips in actions:
            st.markdown(f"**{title}**")
            for t in tips: st.markdown(f"- {t}")

    st.session_state["peds_notes"] = notes
    st.session_state["peds_actions"] = actions
    return notes, actions

# ============================== REPORT ========================================
def build_report_md():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    md = [f"# 피수치 가이드 – 복구판",
          "",
          f"- 생성시각: {now} KST",
          f"- 제작/자문: Hoya/GPT",
          ""]
    # Labs
    labs = st.session_state.get("labs_dict", {})
    if labs:
        md.append("## 피수치")
        for k in LAB_KEYS:
            v = labs.get(k)
            if v not in (None, "", "None"):
                md.append(f"- {k}: {v}")
        md.append("")
    # BP
    bp_txt = st.session_state.get("bp_txt")
    if bp_txt:
        md.append("## 혈압 분류(압종분류)")
        md.append(f"- {bp_txt}")
        md.append("")
    # Onco
    g = st.session_state.get("onco_group") or ""
    d = st.session_state.get("onco_dx") or ""
    if g or d:
        md.append("## 암종 선택")
        md.append(f"- 그룹: {g} / 진단: {d}")
        md.append("")
    # Peds
    notes = st.session_state.get("peds_notes", [])
    if notes:
        md.append("## 소아가이드 요약")
        for n in notes: md.append(f"- {n}")
        md.append("")
    # Diet (lab-based only shown on UI; for report keep short)
    md.append("## 안내")
    md.append("- 혈액암 환자는 **비타민·철분제 임의 복용 주의**, 반드시 주치의와 상담하세요.")
    md.append("")
    return "\n".join(md)

# ============================== MAIN UI =======================================
st.set_page_config(page_title="피수치 가이드 – 복구판", layout="wide")
st.title("피수치 가이드 – 복구판")
st.caption("한국시간 기준(KST). 세포·면역 치료 등은 혼돈 방지를 위해 화면에 표기하지 않습니다.")

# Nav Tabs: 홈, 암종, 항암제, 피수치, 특수검사, 혈압 체크, 소아가이드, 보고서
tabs = st.tabs(["🏠 홈","🧬 암종","💊 항암제","🧪 피수치","🧬 특수검사","⏱️ 혈압 체크","🧒 소아가이드","🧾 보고서"])

with tabs[0]:
    st.markdown("### 바로가기")
    if st.button("소아 가이드 바로가기", key=wkey("go_peds")):
        st.write("상단 탭에서 **🧒 소아가이드**를 선택하세요.")
    diagnostics_panel()
    autosave_state()

with tabs[1]:
    onco_select_ui()
    autosave_state()

with tabs[2]:
    chemo_ui()
    autosave_state()

with tabs[3]:
    labs_ui()
    diet_guides(context=st.session_state.get("labs_dict", {}))
    autosave_state()

with tabs[4]:
    special_tests_ui()
    autosave_state()

with tabs[5]:
    st.session_state["bp_txt"] = bp_classify()
    autosave_state()

with tabs[6]:
    c1,c2,c3 = st.columns(3)
    with c1:
        stool = st.selectbox("설사 횟수", ["0~2회","3~4회","5~6회","7회 이상"], key=wkey("peds_stool"))
        diarrhea_exp = st.checkbox("설사 있음", key=wkey("peds_diarrhea"))
        fever = st.selectbox("최고 체온", ["37.x","38~38.5","38.5~39","39 이상"], key=wkey("peds_fever"))
        constipation = st.checkbox("변비", key=wkey("peds_constipation"))
    with c2:
        persistent_vomit = st.checkbox("지속 구토", key=wkey("peds_vomit"))
        oliguria = st.checkbox("소변량 급감", key=wkey("peds_oligo"))
        cough = st.selectbox("기침 정도", ["없음","조금","보통","심함"], key=wkey("peds_cough"))
        wheeze = st.checkbox("쌕쌕거림/천명", key=wkey("peds_wheeze"))
        sob = st.checkbox("호흡곤란/숨 가쁨", key=wkey("peds_sob"))
        nasal = st.selectbox("콧물 상태", ["맑음","진득","누런"], key=wkey("peds_nasal"))
    with c3:
        eye = st.selectbox("눈 분비물", ["없음","맑음","노랑-농성","양쪽"], key=wkey("peds_eye"))
        throat = st.checkbox("인후통/목 아픔", key=wkey("peds_throat"))
        abd_pain = st.selectbox("복통", ["없음","조금","보통","심함"], key=wkey("peds_abd"))
        ear_pain = st.selectbox("귀 통증", ["없음","조금","보통","심함"], key=wkey("peds_ear"))
        rash = st.checkbox("피부 발진", key=wkey("peds_rash"))
        hives = st.checkbox("두드러기", key=wkey("peds_hives"))
        dysuria = st.checkbox("배뇨 시 통증", key=wkey("peds_dysuria"))
        hematuria = st.checkbox("혈뇨 의심", key=wkey("peds_hematuria"))
        migraine = st.checkbox("두통/편두통", key=wkey("peds_migraine"))
        hfmd = st.checkbox("수족구 의심", key=wkey("peds_hfmd"))
    notes, actions = render_caregiver_notes_peds(
        stool=stool, fever=fever, persistent_vomit=persistent_vomit, oliguria=oliguria,
        cough=cough, nasal=nasal, eye=eye, abd_pain=abd_pain, ear_pain=ear_pain,
        rash=rash, hives=hives, migraine=migraine, hfmd=hfmd,
        constipation=constipation, diarrhea=diarrhea_exp, key_prefix="peds_",
        wheeze=wheeze, sob=sob, throat=throat, dysuria=dysuria, hematuria=hematuria
    )
    autosave_state()

with tabs[7]:
    st.markdown("## 보고서")
    md = build_report_md()
    st.code(md, language="markdown")
    # Save & downloads
    fname_md = SAVE_DIR / "report.md"
    fname_md.write_text(md, encoding="utf-8")
    safe_download("📥 보고서(.md) 다운로드", file_path=fname_md, file_name="report.md", mime="text/markdown", key=wkey("dl_md"))
    # PDF (optional)
    if pdf_export and hasattr(pdf_export, "export_markdown_to_pdf"):
        try:
            out_pdf = SAVE_DIR / "report.pdf"
            pdf_export.export_markdown_to_pdf(md, str(out_pdf))
            safe_download("📄 보고서 PDF 다운로드", file_path=out_pdf, file_name="report.pdf", mime="application/pdf", key=wkey("dl_pdf"))
        except Exception as e:
            st.warning(f"PDF 생성 실패: {e}")
    autosave_state()
