# app.py — Profile(save) + Labs under cancer tabs + eGFR + CSV persistence + Graphs
import datetime as _dt
import os as _os
import typing as _t
import streamlit as st

# ---- Safe banner import ----
try:
    from branding import render_deploy_banner
except Exception:
    try:
        from .branding import render_deploy_banner
    except Exception:
        def render_deploy_banner(*args, **kwargs): return None

# Optional deps
try:
    import pandas as pd
except Exception:
    pd = None

st.set_page_config(page_title="Bloodmap", layout="wide")
st.title("Bloodmap")
render_deploy_banner("https://bloodmap.streamlit.app/", "제작: Hoya/GPT · 자문: Hoya/GPT")

# ---------- helpers ----------
def wkey(name: str) -> str:
    who = st.session_state.get("key", "guest")
    mode_now = st.session_state.get("mode", "main")
    return f"{mode_now}:{who}:{name}"

def egfr_ckd_epi_2009(scr_mgdl: float, age_y: int, sex: str) -> _t.Optional[float]:
    try:
        sex_f = (sex == "여")
        k = 0.7 if sex_f else 0.9
        a = -0.329 if sex_f else -0.411
        min_cr = min(scr_mgdl / k, 1)
        max_cr = max(scr_mgdl / k, 1)
        sex_fac = 1.018 if sex_f else 1.0
        val = 141 * (min_cr ** a) * (max_cr ** -1.209) * (0.993 ** int(age_y)) * sex_fac
        return round(val, 1)
    except Exception:
        return None

def save_labs_csv(df, key: str):
    try:
        save_dir = "/mnt/data/bloodmap_graph"
        _os.makedirs(save_dir, exist_ok=True)
        csv_path = _os.path.join(save_dir, f"{key}.labs.csv")
        if pd is None:
            raise RuntimeError("pandas not available")
        df.to_csv(csv_path, index=False, encoding="utf-8")
        st.caption(f"외부 저장 완료: {csv_path}")
    except Exception as e:
        st.warning(f"외부 저장 실패: {e}")

def load_labs_csv(key: str):
    try:
        import pandas as pd
        path = f"/mnt/data/bloodmap_graph/{key}.labs.csv"
        if _os.path.exists(path):
            return pd.read_csv(path)
    except Exception:
        pass
    return None

def enko(en, ko): return f"{en} / {ko}" if ko else en

# ---------- Spec Groups & Chemo ----------
GROUPS = {
    "🩸 혈액암 (Leukemia)": [
        ("Acute Lymphoblastic Leukemia (ALL)", "급성 림프모구 백혈병"),
        ("Acute Myeloid Leukemia (AML)", "급성 골수성 백혈병"),
        ("Acute Promyelocytic Leukemia (APL)", "급성 전골수성 백혈병"),
        ("Chronic Myeloid Leukemia (CML)", "만성 골수성 백혈병"),
        ("Other Leukemias", "기타 백혈병"),
    ],
    "🧬 림프종 (Lymphoma)": [
        ("Hodgkin Lymphoma", "호지킨 림프종"),
        ("Diffuse Large B-cell Lymphoma (DLBCL)", "미만성 거대 B세포 림프종"),
        ("Burkitt Lymphoma", "버킷 림프종"),
        ("T-lymphoblastic Lymphoma (T-LBL)", "T-림프모구 림프종"),
        ("Anaplastic Large Cell Lymphoma (ALCL)", "역형성 대세포 림프종"),
        ("Primary Mediastinal B-cell Lymphoma (PMBCL)", "원발성 종격동 B세포 림프종"),
        ("Peripheral T-cell Lymphoma (PTCL)", "말초 T세포 림프종"),
        ("Other NHL", "기타 비호지킨 림프종"),
    ],
    "🧠 고형암 (Solid Tumors)": [
        ("Wilms Tumor", "윌름스 종양(신장)"),
        ("Neuroblastoma", "신경모세포종"),
        ("Hepatoblastoma", "간모세포종"),
        ("Retinoblastoma", "망막모세포종"),
        ("Germ Cell Tumor", "생식세포 종양"),
        ("Medulloblastoma", "수모세포종(소뇌)"),
        ("Craniopharyngioma", "두개인두종"),
        ("Other Solid Tumors", "기타 고형 종양"),
    ],
    "🦴 육종 (Sarcoma)": [
        ("Osteosarcoma", "골육종"),
        ("Ewing Sarcoma", "유잉육종"),
        ("Rhabdomyosarcoma", "횡문근육종"),
        ("Other Sarcomas", "기타 연부조직/골 육종"),
    ],
    "🧩 희귀암 및 기타": [
        ("Langerhans Cell Histiocytosis (LCH)", "랜게르한스세포 조직구증"),
        ("Juvenile Myelomonocytic Leukemia (JMML)", "소아 골수단핵구성 백혈병"),
        ("Other Rare", "기타 희귀 아형"),
    ],
}

CHEMO_MAP = {
    "Acute Lymphoblastic Leukemia (ALL)": [
        "6-Mercaptopurine (메르캅토퓨린)",
        "Methotrexate (메토트렉세이트)",
        "Cytarabine/Ara-C (시타라빈)",
        "Vincristine (빈크리스틴)",
    ],
    "Acute Promyelocytic Leukemia (APL)": [
        "ATRA (트레티노인/베사노이드)",
        "Arsenic Trioxide (아르세닉 트리옥사이드)",
        "Methotrexate (메토트렉세이트)",
        "6-Mercaptopurine (메르캅토퓨린)",
    ],
    "Acute Myeloid Leukemia (AML)": [
        "Cytarabine/Ara-C (시타라빈)",
        "Daunorubicin (다우노루비신)",
        "Idarubicin (이다루비신)",
    ],
    "Chronic Myeloid Leukemia (CML)": [
        "Imatinib (이마티닙)",
        "Dasatinib (다사티닙)",
        "Nilotinib (닐로티닙)",
    ],
    "Chronic Lymphocytic Leukemia (CLL)": [
        "Ibrutinib (이브루티닙)",
        "Venetoclax (베네토클락스)",
        "Obinutuzumab (오비누투주맙)",
    ],
    "Diffuse Large B-cell Lymphoma (DLBCL)": [
        "R-CHOP (리툭시맙+CHOP)",
        "R-EPOCH (리툭시맙+EPOCH)",
        "Polatuzumab-based (폴라투주맙 조합)",
    ],
    "Hodgkin Lymphoma": ["ABVD (도옥소루비신/블레오마이신/빈블라스틴/다카바진)"],
    "Osteosarcoma": ["MAP (메토트렉세이트/독소루비신/시스플라틴)"],
    "Ewing Sarcoma": ["VDC/IE (빈크리스틴/독소루비신/사이클로포스파마이드 + 이포스파마이드/에토포사이드)"],
    "Rhabdomyosarcoma": ["VAC (빈크리스틴/액티노마이신 D/사이클로포스파마이드)"],
    "Wilms Tumor": ["Vincristine (빈크리스틴)", "Dactinomycin (닥티노마이신)", "Doxorubicin (독소루비신)"],
    "Neuroblastoma": ["Cyclophosphamide (사이클로포스파마이드)", "Topotecan (토포테칸)", "Cisplatin (시스플라틴)", "Etoposide (에토포사이드)"],
}

# ---------- Sidebar: Profile (nickname/PIN save) ----------
with st.sidebar:
    st.header("프로필")
    key_val = st.text_input("별명#PIN", value=st.session_state.get("key", ""), placeholder="예: hoya#1234", key=wkey("user_key_input"))
    if st.button("저장", key=wkey("save_profile")):
        st.session_state["key"] = key_val or "guest"
        st.success(f"저장됨: {st.session_state['key']}")
    st.session_state["mode"] = st.radio("모드", ["일반", "암", "소아"], index=1, key=wkey("mode_sel"))

# ---------- Tabs for the 5 groups ----------
tabs = st.tabs(list(GROUPS.keys()))

# Prepare lab state
if "lab_rows" not in st.session_state:
    st.session_state["lab_rows"] = []

def lab_inputs_block(group_label: str, dx_en: str, dx_ko: str):
    st.markdown("### 🧪 피수치 입력")
    c1,c2,c3,c4,c5 = st.columns(5)
    with c1:
        sex = st.selectbox("성별", ["여","남"], key=wkey(f"{group_label}:{dx_en}:sex"))
    with c2:
        age = st.number_input("나이(세)", min_value=0, max_value=120, value=10, step=1, key=wkey(f"{group_label}:{dx_en}:age"))
    with c3:
        weight = st.number_input("체중(kg)", min_value=0.0, value=0.0, step=0.5, key=wkey(f"{group_label}:{dx_en}:wt"))
    with c4:
        cr = st.number_input("Cr (mg/dL)", min_value=0.0, value=0.8, step=0.1, key=wkey(f"{group_label}:{dx_en}:cr"))
    with c5:
        date = st.date_input("날짜", value=_dt.date.today(), key=wkey(f"{group_label}:{dx_en}:date"))

    egfr = egfr_ckd_epi_2009(cr, int(age), sex)
    if egfr is not None:
        st.metric("eGFR (CKD-EPI 2009)", f"{egfr} mL/min/1.73㎡")

    st.markdown("#### 주요 항목")
    r1c1, r1c2, r1c3, r1c4 = st.columns(4)
    WBC = r1c1.number_input("WBC (10^3/µL)", min_value=0.0, step=0.1, value=5.0, key=wkey(f"{group_label}:{dx_en}:wbc"))
    Hb  = r1c2.number_input("Hb (g/dL)",     min_value=0.0, step=0.1, value=12.0, key=wkey(f"{group_label}:{dx_en}:hb"))
    PLT = r1c3.number_input("PLT (10^3/µL)", min_value=0.0, step=1.0, value=250.0, key=wkey(f"{group_label}:{dx_en}:plt"))
    ANC = r1c4.number_input("ANC (/µL)",     min_value=0.0, step=100.0, value=3000.0, key=wkey(f"{group_label}:{dx_en}:anc"))

    r2c1, r2c2, r2c3, r2c4 = st.columns(4)
    AST = r2c1.number_input("AST (U/L)", min_value=0.0, step=1.0, value=20.0, key=wkey(f"{group_label}:{dx_en}:ast"))
    ALT = r2c2.number_input("ALT (U/L)", min_value=0.0, step=1.0, value=20.0, key=wkey(f"{group_label}:{dx_en}:alt"))
    TB  = r2c3.number_input("T.bil (mg/dL)", min_value=0.0, step=0.1, value=0.8, key=wkey(f"{group_label}:{dx_en}:tbil"))
    ALP = r2c4.number_input("ALP (U/L)", min_value=0.0, step=5.0, value=90.0, key=wkey(f"{group_label}:{dx_en}:alp"))

    r3c1, r3c2, r3c3, r3c4 = st.columns(4)
    Na  = r3c1.number_input("Na (mmol/L)", min_value=0.0, step=0.5, value=140.0, key=wkey(f"{group_label}:{dx_en}:na"))
    K   = r3c2.number_input("K (mmol/L)",  min_value=0.0, step=0.1, value=4.0, key=wkey(f"{group_label}:{dx_en}:k"))
    Cl  = r3c3.number_input("Cl (mmol/L)", min_value=0.0, step=0.5, value=103.0, key=wkey(f"{group_label}:{dx_en}:cl"))
    CRP = r3c4.number_input("CRP (mg/dL)", min_value=0.0, step=0.1, value=0.3, key=wkey(f"{group_label}:{dx_en}:crp"))

    meds_default = CHEMO_MAP.get(dx_en, [])
    st.markdown("### 💊 항암제")
    meds_sel = st.multiselect("항암제를 선택/추가하세요 (영문/한글 병기)", meds_default, default=meds_default, key=wkey(f"{group_label}:{dx_en}:chemo"))
    extra = st.text_input("추가 항암제(쉼표로 구분)", key=wkey(f"{group_label}:{dx_en}:chemo_extra"))
    if extra.strip():
        add = [x.strip() for x in extra.split(",") if x.strip()]
        meds_sel = list(dict.fromkeys(meds_sel + add))

    # add row
    if pd is not None:
        row = {
            "key": st.session_state.get("key","guest"),
            "group": group_label,
            "dx_en": dx_en, "dx_ko": dx_ko,
            "date": str(date), "sex": sex, "age": int(age), "weight(kg)": weight,
            "Cr(mg/dL)": cr, "eGFR": egfr,
            "WBC": WBC, "Hb": Hb, "PLT": PLT, "ANC": ANC,
            "AST": AST, "ALT": ALT, "Tbil": TB, "ALP": ALP,
            "Na": Na, "K": K, "Cl": Cl, "CRP": CRP,
            "meds": "; ".join(meds_sel),
        }
        csave, cadd = st.columns(2)
        if cadd.button("➕ 현재 값 추가", key=wkey(f"{group_label}:{dx_en}:addrow")):
            st.session_state["lab_rows"].append(row)
        # table
        df = pd.DataFrame(st.session_state["lab_rows"] or [row])
        st.dataframe(df, use_container_width=True)
        if csave.button("📁 CSV 저장", key=wkey(f"{group_label}:{dx_en}:savecsv")):
            save_labs_csv(df, st.session_state.get("key","guest"))

        # graphs
        st.markdown("### 📈 추이 그래프")
        try:
            # Convert date to datetime if possible
            dfg = df.copy()
            dfg["date"] = pd.to_datetime(dfg["date"], errors="coerce")
            dfg = dfg.sort_values("date")
            # Select small subset for trends
            cols = [c for c in ["eGFR","CRP","WBC","Hb","PLT"] if c in dfg.columns]
            if cols and not dfg.empty:
                st.line_chart(dfg.set_index("date")[cols])
            else:
                st.info("그래프를 보려면 최소 1행 이상의 데이터가 필요합니다.")
        except Exception as e:
            st.warning(f"그래프 생성 실패: {e}")
    else:
        st.info("pandas 없음: 표/CSV/그래프 기능 비활성화")

for gi, (glabel, dxs) in enumerate(GROUPS.items()):
    with st.tabs(list(GROUPS.keys()))[gi]:
        st.subheader(glabel)
        labels = [enko(en, ko) for en, ko in dxs]
        dx_choice = st.selectbox("진단명을 선택하세요", labels, key=wkey(f"dxsel:{gi}"))
        idx = labels.index(dx_choice)
        dx_en, dx_ko = dxs[idx]
        lab_inputs_block(glabel, dx_en, dx_ko)