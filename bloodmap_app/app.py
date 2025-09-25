
# app.py — Minimal+, ordered flow with ABX & diet guides
import datetime as _dt
import math
import streamlit as st

# -------- Safe banner (no-op if missing) --------
try:
    from branding import render_deploy_banner
except Exception:
    def render_deploy_banner(*a, **k): return None

# Diet guide
try:
    from lab_diet import lab_diet_guides
except Exception:
    def lab_diet_guides(labs, heme_flag=False): return []

# Special tests (rich UI)
try:
    from special_tests import special_tests_ui
except Exception:
    special_tests_ui = None

# Optional AE alerts
try:
    from ui_results import collect_top_ae_alerts
except Exception:
    def collect_top_ae_alerts(drug_keys, db=None): return []

# Optional drug DB helpers (labels in Korean)
try:
    from drug_db import display_label as _drug_label, key_from_label as _drug_key, DRUG_DB, ensure_onco_drug_db
    ensure_onco_drug_db(DRUG_DB)
except Exception:
    DRUG_DB = {}
    def _drug_label(x, db=None): return str(x)
    def _drug_key(x): return str(x)

st.set_page_config(page_title="Bloodmap (Ordered)", layout="wide")
st.title("Bloodmap (Ordered)")
render_deploy_banner("https://bloodmap.streamlit.app/", "제작: Hoya/GPT · 자문: Hoya/GPT")

# -------- Helpers --------
def wkey(name:str)->str:
    who = st.session_state.get("key","guest")
    return f"{who}:{name}"

def enko(en:str, ko:str)->str:
    return f"{en} / {ko}" if ko else en

def _num(s):
    try:
        if s is None: return None
        if isinstance(s, (int,float)): return float(s)
        txt = str(s).strip().replace(",", "")
        if txt == "": return None
        return float(txt)
    except Exception:
        return None

# -------- Inline defaults (no external files) --------

GROUPS = {
    "🩸 혈액암 (Leukemia)": [
        ("Acute Lymphoblastic Leukemia (ALL)", "급성 림프모구 백혈병"),
        ("Acute Myeloid Leukemia (AML)", "급성 골수성 백혈병"),
        ("Acute Promyelocytic Leukemia (APL)", "급성 전골수성 백혈병"),
        ("Chronic Myeloid Leukemia (CML)", "만성 골수성 백혈병"),
        ("Chronic Lymphocytic Leukemia (CLL)", "만성 림프구성 백혈병"),
        ("Juvenile Myelomonocytic Leukemia (JMML)", "소아 골수단핵구성 백혈병"),
        ("Mixed Phenotype Acute Leukemia (MPAL)", "혼합표현형 급성백혈병"),
        ("Myelodysplastic Syndromes (MDS)", "골수형성이상증후군"),
    ],
    "🧬 림프종 (Lymphoma)": [
        ("Hodgkin Lymphoma", "호지킨 림프종"),
        ("Nodular Sclerosis HL", "결절경화형 호지킨"),
        ("Mediastinal (Thymic) Large B-cell Lymphoma", "종격동(흉선) 거대B세포림프종"),
        ("Diffuse Large B-cell Lymphoma (DLBCL)", "미만성 거대 B세포 림프종"),
        ("Follicular Lymphoma", "여포성 림프종"),
        ("Marginal Zone Lymphoma (MZL)", "변연부 림프종"),
        ("Mantle Cell Lymphoma (MCL)", "외투세포 림프종"),
        ("Burkitt Lymphoma", "버킷 림프종"),
        ("T-lymphoblastic Lymphoma", "T림프모구 림프종"),
        ("Peripheral T-cell Lymphoma (PTCL-NOS)", "말초 T세포 림프종"),
        ("Anaplastic Large Cell Lymphoma (ALCL)", "미분화 대세포 림프종"),
        ("NK/T-cell Lymphoma, nasal type", "NK/T 세포 림프종 비강형"),
    ],
    "🦴 육종 (Sarcoma)": [
        ("Osteosarcoma", "골육종"),
        ("Ewing Sarcoma", "유잉육종"),
        ("Rhabdomyosarcoma", "횡문근육종"),
        ("Synovial Sarcoma", "윤활막 육종"),
        ("Leiomyosarcoma", "평활근육종"),
        ("Undifferentiated Pleomorphic Sarcoma", "미분화 다형성 육종"),
    ],
    "🧠 고형암 (Solid Tumors)": [
        ("Neuroblastoma", "신경모세포종"),
        ("Wilms Tumor", "윌름스 종양(신장)"),
        ("Hepatoblastoma", "간모세포종"),
        ("Retinoblastoma", "망막모세포종"),
        ("Medulloblastoma", "수질모세포종"),
        ("Ependymoma", "상의세포종"),
        ("ATRT", "비정형 기형종/유사종양"),
        ("Germ Cell Tumor", "생식세포종양"),
        ("Thyroid Carcinoma", "갑상선암"),
        ("Osteofibrous Dysplasia-like Tumor", "골섬유이형성 유사 종양"),
    ],
    "🧩 희귀암 및 기타": [
        ("Langerhans Cell Histiocytosis (LCH)", "랜게르한스세포 조직구증"),
        ("Rosai-Dorfman Disease", "로자이-도프만병"),
        ("Histiocytic Sarcoma", "조직구성 육종"),
        ("Chordoma", "척색종"),
        ("Pheochromocytoma/Paraganglioma", "갈색세포종/부신경절종"),
    ],
}


CHEMO_MAP = {
    # Leukemia
    "Acute Lymphoblastic Leukemia (ALL)": [
        "6-Mercaptopurine (메르캅토퓨린)","Methotrexate (메토트렉세이트)",
        "Cytarabine/Ara-C (시타라빈)","Vincristine (빈크리스틴)","Dexamethasone (덱사메타손)"
    ],
    "Acute Promyelocytic Leukemia (APL)": [
        "ATRA (트레티노인/베사노이드)","Arsenic Trioxide (아르세닉 트리옥사이드)","MTX (메토트렉세이트)","6-MP (메르캅토퓨린)"
    ],
    "Acute Myeloid Leukemia (AML)": [
        "Ara-C (시타라빈)","Daunorubicin (다우노루비신)","Idarubicin (이다루비신)","Etoposide (에토포시드)"
    ],
    "Chronic Myeloid Leukemia (CML)": ["Imatinib (이마티닙)","Dasatinib (다사티닙)","Nilotinib (닐로티닙)"],
    "Chronic Lymphocytic Leukemia (CLL)": ["FCR (플루다라빈/사이클로포스파미드/리툭시맙)","Bendamustine+Rituximab"],
    "Juvenile Myelomonocytic Leukemia (JMML)": ["Azacitidine","Stem Cell Transplant"],
    "Mixed Phenotype Acute Leukemia (MPAL)": ["ALL-like protocols","AML-like protocols"],
    "Myelodysplastic Syndromes (MDS)": ["Azacitidine","Decitabine"],

    # Lymphoma
    "Hodgkin Lymphoma": ["ABVD","OEPA/COEP (peds)"],
    "Nodular Sclerosis HL": ["ABVD","BEACOPP (risk-adapted)"],
    "Mediastinal (Thymic) Large B-cell Lymphoma": ["DA-EPOCH-R"],
    "Diffuse Large B-cell Lymphoma (DLBCL)": ["R-CHOP","R-EPOCH","Polatuzumab-based"],
    "Follicular Lymphoma": ["R-CHOP","Bendamustine+Rituximab"],
    "Marginal Zone Lymphoma (MZL)": ["Rituximab","R-CHOP"],
    "Mantle Cell Lymphoma (MCL)": ["R-CHOP","R-DHAP","BTK inhibitors"],
    "Burkitt Lymphoma": ["CODOX-M/IVAC","Hyper-CVAD"],
    "T-lymphoblastic Lymphoma": ["ALL-like protocols"],
    "Peripheral T-cell Lymphoma (PTCL-NOS)": ["CHOP", "CHOEP"],
    "Anaplastic Large Cell Lymphoma (ALCL)": ["CHOP","Brentuximab vedotin+CHP"],
    "NK/T-cell Lymphoma, nasal type": ["SMILE","P-GEMOX"],

    # Sarcoma
    "Osteosarcoma": ["MAP (MTX/DOX/CDDP)"],
    "Ewing Sarcoma": ["VDC/IE"],
    "Rhabdomyosarcoma": ["VAC/VI"],
    "Synovial Sarcoma": ["Ifosfamide","Doxorubicin"],
    "Leiomyosarcoma": ["Gemcitabine/Docetaxel","Doxorubicin"],
    "Undifferentiated Pleomorphic Sarcoma": ["Doxorubicin","Ifosfamide"],

    # Solid tumors
    "Neuroblastoma": ["Cyclophosphamide","Topotecan","Cisplatin","Etoposide","Anti-GD2"],
    "Wilms Tumor": ["Vincristine","Dactinomycin","Doxorubicin"],
    "Hepatoblastoma": ["Cisplatin","Doxorubicin"],
    "Retinoblastoma": ["Carboplatin","Etoposide","Vincristine"],
    "Medulloblastoma": ["Cisplatin","Cyclophosphamide","Vincristine"],
    "Ependymoma": ["Surgery/Radiation","Platinum-based (selected)"],
    "ATRT": ["High-dose chemotherapy", "Methotrexate (high-dose)"],
    "Germ Cell Tumor": ["BEP (Bleomycin/Etoposide/Cisplatin)","EP"],
    "Thyroid Carcinoma": ["Surgery","RAI","TKIs (advanced)"],
    "Osteofibrous Dysplasia-like Tumor": ["Observation/Surgery"],

    # Rare/Other
    "LCH": ["Vinblastine","Prednisone"],
    "Rosai-Dorfman Disease": ["Steroids","Sirolimus"],
    "Histiocytic Sarcoma": ["CHOP-like","Ifosfamide/Etoposide"],
    "Chordoma": ["Surgery/Radiation","Imatinib (selected)"],
    "Pheochromocytoma/Paraganglioma": ["Surgery","CVD (Cyclophosphamide/Vincristine/Dacarbazine)","MIBG"],
}

ABX_DEFAULTS = [
    "Piperacillin/Tazobactam",
    "Cefepime",
    "Meropenem",
    "Imipenem/Cilastatin",
    "Aztreonam",
    "Amikacin",
    "Vancomycin",
    "Linezolid",
    "Daptomycin",
    "Ceftazidime",
    "Levofloxacin",
    "TMP-SMX",
    "Metronidazole",
    "Amoxicillin/Clavulanate",
]

# -------- Sidebar (always visible) --------
with st.sidebar:
    st.header("프로필")
    st.session_state["key"] = st.text_input("별명#PIN", value=st.session_state.get("key","guest"), key=wkey("user_key"))
    st.caption("좌측 프로필은 저장/CSV 경로 키로 쓰입니다.")

# -------- Tabs (ordered) --------
t_home, t_dx, t_chemo, t_abx, t_labs, t_special, t_report = st.tabs(
    ["🏠 홈","🧬 암 선택","💊 항암제","🦠 항생제","🧪 피수치 입력","🔬 특수검사","📄 보고서"]
)

with t_home:
    st.info("흐름: **암 선택 → 항암제/항생제 선택 → 피수치 입력 → 해석하기** 순서입니다. 결과는 '해석하기' 버튼을 눌러야만 표시됩니다.")

with t_dx:
    st.subheader("암 선택")
    grp_tabs = st.tabs(list(GROUPS.keys()))
    for i,(g, lst) in enumerate(GROUPS.items()):
        with grp_tabs[i]:
            labels = [enko(en,ko) for en,ko in lst]
            sel = st.selectbox("진단명을 선택하세요", labels, key=wkey(f"dx_sel_{i}"))
            en_dx, ko_dx = lst[labels.index(sel)]
            if st.button("선택 저장", key=wkey(f"dx_save_{i}")):
                st.session_state["dx_group"] = g
                st.session_state["dx_en"] = en_dx
                st.session_state["dx_ko"] = ko_dx
                st.success(f"저장됨: {enko(en_dx, ko_dx)}")

with t_chemo:
    st.subheader("항암제")
    en_dx = st.session_state.get("dx_en")
    ko_dx = st.session_state.get("dx_ko","")
    if not en_dx:
        st.info("먼저 '암 선택'에서 저장하세요.")
    else:
        st.write(f"현재 진단: **{enko(en_dx, ko_dx)}**")
        suggestions = CHEMO_MAP.get(en_dx, CHEMO_MAP.get(ko_dx, []))
        # 그냥 문자열 목록이므로 라벨 변환은 생략
        picked = st.multiselect("항암제를 선택/추가", suggestions, default=suggestions, key=wkey("chemo_ms"))
        extra = st.text_input("추가 항암제(쉼표 구분)", key=wkey("chemo_extra"))
        if extra.strip():
            more = [x.strip() for x in extra.split(",") if x.strip()]
            seen, merged = set(), []
            for x in picked + more:
                if x not in seen: seen.add(x); merged.append(x)
            picked = merged
        if st.button("항암제 저장", key=wkey("chemo_save")):
            st.session_state["chemo_list"] = picked
            st.success("저장됨. '보고서'에서 확인")

with t_abx:
    st.subheader("항생제")
    # 라벨을 한국어 병기로 변환(가능한 경우)
    abx_labels = [_drug_label(x, DRUG_DB) for x in ABX_DEFAULTS]
    abx_sel = st.multiselect("항생제를 선택/추가", abx_labels, default=abx_labels, key=wkey("abx_ms"))
    abx_extra = st.text_input("추가 항생제(쉼표 구분, 예: Vancomycin, Ceftazidime)", key=wkey("abx_extra"))
    # 라벨 → 키 역변환
    picked_keys = [_drug_key(label) for label in abx_sel]
    if abx_extra.strip():
        more = [s.strip() for s in abx_extra.split(",") if s.strip()]
        for m in more:
            if m not in picked_keys:
                picked_keys.append(m)
    if st.button("항생제 저장", key=wkey("abx_save")):
        st.session_state["abx_list"] = picked_keys
        st.success("저장됨. '보고서'에서 확인")

with t_labs:
    st.subheader("피수치 입력")
    col1,col2,col3,col4,col5 = st.columns(5)
    with col1: sex = st.selectbox("성별", ["여","남"], key=wkey("sex"))
    with col2: age = st.number_input("나이(세)", 1, 110, 40, key=wkey("age"))
    with col3: wt  = st.number_input("체중(kg)", 0.0, 300.0, 0.0, 0.5, key=wkey("wt"))
    with col4: cr  = st.number_input("Cr (mg/dL)", 0.0, 20.0, 0.8, 0.1, key=wkey("cr"))
    with col5: day = st.date_input("측정일", value=_dt.date.today(), key=wkey("date"))

    # eGFR (CKD-EPI 2009)
    def egfr_2009(cr_mgdl:float, age:int, sex:str):
        sex_f = (sex=="여"); k = 0.7 if sex_f else 0.9; a = -0.329 if sex_f else -0.411
        mn = min(cr_mgdl/k,1); mx = max(cr_mgdl/k,1); sex_fac = 1.018 if sex_f else 1.0
        return round(141*(mn**a)*(mx**-1.209)*(0.993**age)*sex_fac,1)
    egfr = egfr_2009(cr, int(age), sex)
    st.metric("eGFR (CKD-EPI 2009)", f"{egfr} mL/min/1.73㎡")

    st.markdown("**필요한 것만 입력하세요(빈칸 허용).** 입력한 수치만 해석에 사용합니다.")
    r1 = st.columns(7)
    with r1[0]: Alb = st.text_input("Alb (g/dL)", key=wkey("Alb"))
    with r1[1]: K   = st.text_input("K (mmol/L)", key=wkey("K"))
    with r1[2]: Hb  = st.text_input("Hb (g/dL)", key=wkey("Hb"))
    with r1[3]: Na  = st.text_input("Na (mmol/L)", key=wkey("Na"))
    with r1[4]: Ca  = st.text_input("Ca (mg/dL)", key=wkey("Ca"))
    with r1[5]: Glu = st.text_input("Glucose (mg/dL)", key=wkey("Glu"))
    with r1[6]: UA  = st.text_input("Uric acid (mg/dL)", key=wkey("UA"))

    r2 = st.columns(7)
    with r2[0]: AST = st.text_input("AST (U/L)", key=wkey("AST"))
    with r2[1]: ALT = st.text_input("ALT (U/L)", key=wkey("ALT"))
    with r2[2]: BUN = st.text_input("BUN (mg/dL)", key=wkey("BUN"))
    with r2[3]: CRP = st.text_input("CRP (mg/L)", key=wkey("CRP"))
    with r2[4]: ANC = st.text_input("ANC (/µL)", key=wkey("ANC"))
    with r2[5]: PLT = st.text_input("PLT (×10³/µL)", key=wkey("PLT"))
    with r2[6]:    _ = st.empty()

    # Save row (only provided fields)
    st.session_state.setdefault("lab_rows", [])
    if st.button("➕ 현재 값 추가", key=wkey("add_row")):
        lab = {
            "date": str(day), "sex": sex, "age": int(age), "weight(kg)": wt,
            "Cr(mg/dL)": cr, "eGFR": egfr,
            "Alb": _num(Alb), "K": _num(K), "Hb": _num(Hb), "Na": _num(Na),
            "Ca": _num(Ca), "Glu": _num(Glu), "UA": _num(UA), "AST": _num(AST),
            "ALT": _num(ALT), "BUN": _num(BUN), "CRP": _num(CRP), "ANC": _num(ANC), "PLT": _num(PLT)
        }
        st.session_state["lab_rows"].append(lab)
        st.success("추가되었습니다.")
    rows = st.session_state["lab_rows"]
    if rows:
        st.write("최근 입력:")
        for r in rows[-5:]:
            st.write({k:v for k,v in r.items() if v not in (None, "")})

with t_special:
    st.subheader("특수검사")
    if special_tests_ui:
        lines = special_tests_ui()
        st.session_state["special_lines"] = lines
    else:
        a,b,c = st.columns(3)
        sp1 = a.text_input("유전자/표지자 (예: BCR-ABL1)", key=wkey("spec_gene"))
        sp2 = b.text_input("이미징/기타 (예: PET/CT 결과)", key=wkey("spec_img"))
        sp3 = c.text_input("기타 메모", key=wkey("spec_note"))
        st.session_state["special_lines"] = [s for s in [
            f"- 유전자/표지자: {sp1}" if sp1 else "",
            f"- 이미징/기타: {sp2}" if sp2 else "",
            f"- 메모: {sp3}" if sp3 else "",
        ] if s]

with t_report:
    st.subheader("보고서 / 해석")
    dx = enko(st.session_state.get("dx_en",""), st.session_state.get("dx_ko",""))
    dx_group = st.session_state.get("dx_group","")
    meds = st.session_state.get("chemo_list", [])
    abx  = st.session_state.get("abx_list", [])
    rows = st.session_state.get("lab_rows", [])
    spec_lines = st.session_state.get("special_lines", [])

    st.write(f"**진단명**: {dx if dx.strip() else '(미선택)'}")
    st.write(f"**그룹**: {dx_group or '(미선택)'}")

    if st.button("🧠 해석하기", key=wkey("analyze")):
        st.session_state["analyzed"] = True

    analyzed = bool(st.session_state.get("analyzed"))
    if not analyzed:
        st.info("버튼을 눌러 해석을 실행하세요. (결과는 버튼 이후에만 표시)")
    else:
        # --- Diet guide from latest row
        if rows:
            latest = rows[-1]
            heme_flag = "혈액암" in (dx_group or "")
            labs_for_diet = {k: latest.get(k) for k in ["Alb","K","Hb","Na","Ca","Glu","AST","ALT","Cr(mg/dL)","BUN","UA","CRP","ANC","PLT"]}
            # lab_diet expects keys Alb,K,Hb,Na,Ca,Glu,AST,ALT,Cr,BUN,UA,CRP,ANC,PLT
            labs_for_diet["Cr"] = latest.get("Cr(mg/dL)")
            guide = lab_diet_guides(labs_for_diet, heme_flag=heme_flag)
            if guide:
                st.markdown("### 🍽️ 피수치 기반 식이가이드")
                for g in guide:
                    st.write("- " + g)
        else:
            st.warning("피수치가 없습니다. 식이가이드는 생략됩니다.")

        # --- Top adverse effect alerts (from drug DB if available)
        keys_for_alert = []
        # chemo_list entries are strings (not normalized); abx_list already keys
        for m in meds or []:
            # try to strip " (..." part
            base = m.split(" (")[0]
            keys_for_alert.append(base)
        keys_for_alert += (abx or [])
        alerts = collect_top_ae_alerts(keys_for_alert, DRUG_DB) if keys_for_alert else []
        if alerts:
            st.markdown("### ⚠️ 약물 중대 경고 (Top hits)")
            for a in alerts:
                st.error(a)

        # --- Render markdown summary + download
        lines = []
        lines.append("# Bloodmap Report")
        lines.append(f"**진단명**: {dx if dx.strip() else '(미선택)'}")
        lines.append(f"**그룹**: {dx_group or '(미선택)'}")
        lines.append("")
        lines.append("## 항암제 요약")
        if meds:
            for m in meds: lines.append(f"- {m}")
        else:
            lines.append("- (없음)")
        lines.append("")
        lines.append("## 항생제 요약")
        if abx:
            for k in abx:
                lines.append(f"- {_drug_label(k, DRUG_DB)}")
        else:
            lines.append("- (없음)")
        if rows:
            lines.append("")
            lines.append("## 최근 검사 (최대 5개)")
            # Only include provided fields
            head = ["date","sex","age","weight(kg)","Cr(mg/dL)","eGFR","Alb","K","Hb","Na","Ca","Glu","AST","ALT","BUN","UA","CRP","ANC","PLT"]
            show = [h for h in head if any((r.get(h) not in (None,"")) for r in rows[-5:])]
            lines.append("| " + " | ".join(show) + " |")
            lines.append("|" + "|".join(["---"]*len(show)) + "|")
            for r in rows[-5:]:
                lines.append("| " + " | ".join(str(r.get(k,'')) for k in show) + " |")
        if spec_lines:
            lines.append("")
            lines.append("## 특수검사")
            for s in spec_lines:
                lines.append(f"- {s}")
        if rows:
            if guide:
                lines.append("")
                lines.append("## 피수치 기반 식이가이드")
                for g in guide:
                    lines.append(f"- {g}")
        lines.append("")
        lines.append(f"_생성 시각: {_dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_")
        md = "\\n".join(lines)
        st.download_button("💾 보고서 .md 다운로드", data=md.encode("utf-8"),
                           file_name="bloodmap_report.md", mime="text/markdown", key=wkey("dl_md"))
