# app.py — Minimal, always-on inputs (Labs, Diagnosis, Chemo, Special Tests)
import datetime as _dt
import streamlit as st
from drug_db import DRUG_DB
from ui_results import collect_top_ae_alerts
from special_tests import special_tests_ui
from lab_diet import lab_diet_guides

# -------- Safe banner (no-op if missing) --------
try:
    from branding import render_deploy_banner
except Exception:
    def render_deploy_banner(*a, **k): return None

st.set_page_config(page_title="Bloodmap (Minimal)", layout="wide")
st.title("Bloodmap (Minimal)")
render_deploy_banner("https://bloodmap.streamlit.app/", "제작: Hoya/GPT · 자문: Hoya/GPT")

# -------- Helpers --------
def wkey(name:str)->str:
    who = st.session_state.get("key","guest")
    return f"{who}:{name}"
def enko(en:str, ko:str)->str:
    return f"{en} / {ko}" if ko else en

# -------- Inline defaults (no external files) --------
GROUPS = {
    "🩸 혈액암 (Leukemia/MDS/MPN)": [
        ("Acute Lymphoblastic Leukemia (ALL)", "급성 림프모구 백혈병"),
        ("T-ALL", "T-세포 급성 림프모구 백혈병"),
        ("B-ALL", "B-세포 급성 림프모구 백혈병"),
        ("Acute Myeloid Leukemia (AML)", "급성 골수성 백혈병"),
        ("Acute Promyelocytic Leukemia (APL)", "급성 전골수성 백혈병"),
        ("Chronic Myeloid Leukemia (CML)", "만성 골수성 백혈병"),
        ("Chronic Lymphocytic Leukemia (CLL)", "만성 림프구성 백혈병"),
        ("Hairy Cell Leukemia", "털세포 백혈병"),
        ("Myelodysplastic Syndrome (MDS)", "골수형성이상증후군"),
        ("Myeloproliferative Neoplasms (MPN)", "골수증식성 종양"),
        ("Polycythemia Vera (PV)", "진성 적혈구증가증"),
        ("Essential Thrombocythemia (ET)", "본태성 혈소판증가증"),
        ("Primary Myelofibrosis (PMF)", "원발성 골수섬유증"),
    ],
    "🧬 림프종 (Lymphoma)": [
        ("Hodgkin Lymphoma", "호지킨 림프종"),
        ("Diffuse Large B-cell Lymphoma (DLBCL)", "미만성 거대 B세포 림프종"),
        ("Follicular Lymphoma (FL)", "여포성 림프종"),
        ("Mantle Cell Lymphoma (MCL)", "외투세포 림프종"),
        ("Marginal Zone Lymphoma (MZL)", "변연부 림프종"),
        ("Burkitt Lymphoma", "버킷 림프종"),
        ("Primary CNS Lymphoma", "원발성 중추신경계 림프종"),
        ("T-cell Lymphoma (PTCL/NOS)", "말초 T세포 림프종(비특이형)"),
        ("Anaplastic Large Cell Lymphoma (ALCL)", "역형성 대세포 림프종"),
        ("NK/T-cell Lymphoma", "NK/T 세포 림프종"),
        ("Waldenström Macroglobulinemia", "월덴스트롬 거대글로불린혈증"),
    ],
    "🧠 고형암 (Solid Tumors)": [
        ("Breast Cancer", "유방암"),
        ("Lung Cancer - NSCLC", "폐암-비소세포"),
        ("Lung Cancer - SCLC", "폐암-소세포"),
        ("Colorectal Cancer", "대장암"),
        ("Gastric Cancer", "위암"),
        ("Pancreatic Cancer", "췌장암"),
        ("Liver Cancer (Hepatocellular Carcinoma)", "간세포암"),
        ("Cholangiocarcinoma", "담관암"),
        ("Biliary Tract Cancer", "담도암"),
        ("Esophageal Cancer", "식도암"),
        ("Head and Neck Cancer", "두경부암"),
        ("Thyroid Cancer", "갑상선암"),
        ("Renal Cell Carcinoma", "신장암"),
        ("Urothelial/Bladder Cancer", "요로상피/방광암"),
        ("Prostate Cancer", "전립선암"),
        ("Ovarian Cancer", "난소암"),
        ("Cervical Cancer", "자궁경부암"),
        ("Endometrial Cancer", "자궁내막암"),
        ("Testicular Germ Cell Tumor", "고환 생식세포종양"),
        ("Neuroendocrine Tumor (NET)", "신경내분비종양"),
        ("Melanoma", "흑색종"),
        ("Merkel Cell Carcinoma", "메르켈세포암"),
    ],
    "🦴 육종 (Sarcoma)": [
        ("Undifferentiated Pleomorphic Sarcoma (UPS)", "미분화 다형성 육종"),
        ("Leiomyosarcoma (LMS)", "평활근육종"),
        ("Liposarcoma", "지방육종"),
        ("Synovial Sarcoma", "활막육종"),
        ("Rhabdomyosarcoma", "횡문근육종"),
        ("GIST (Gastrointestinal Stromal Tumor)", "위장관기질종양"),
        ("Angiosarcoma", "혈관육종"),
        ("Ewing Sarcoma", "유잉육종"),
        ("Osteosarcoma", "골육종"),
        ("Chondrosarcoma", "연골육종"),
        ("Dermatofibrosarcoma Protuberans (DFSP)", "피부섬유육종"),
    ],
    "🧩 희귀암 및 소아": [
        ("Wilms Tumor", "윌름스 종양"),
        ("Neuroblastoma", "신경모세포종"),
        ("Medulloblastoma", "수모세포종"),
        ("Ependymoma", "상의세포종"),
        ("Retinoblastoma", "망막모세포종"),
        ("Hepatoblastoma", "간모세포종"),
        ("Langerhans Cell Histiocytosis (LCH)", "랜게르한스세포 조직구증"),
        ("Juvenile Myelomonocytic Leukemia (JMML)", "소아 골수단핵구성 백혈병"),
    ],
}
CHEMO_MAP = {
    "Acute Lymphoblastic Leukemia (ALL)": [
        "6-Mercaptopurine (메르캅토퓨린)","Methotrexate (메토트렉세이트)","Cytarabine/Ara-C (시타라빈)","Vincristine (빈크리스틴)"],
    "Acute Promyelocytic Leukemia (APL)": [
        "ATRA (트레티노인/베사노이드)","Arsenic Trioxide (아르세닉 트리옥사이드)","MTX (메토트렉세이트)","6-MP (메르캅토퓨린)"],
    "Acute Myeloid Leukemia (AML)": [
        "Ara-C (시타라빈)","Daunorubicin (다우노루비신)","Idarubicin (이다루비신)"],
    "Chronic Myeloid Leukemia (CML)": [
        "Imatinib (이마티닙)","Dasatinib (다사티닙)","Nilotinib (닐로티닙)"],
    "Diffuse Large B-cell Lymphoma (DLBCL)": ["R-CHOP","R-EPOCH","Polatuzumab combos"],
    "Burkitt Lymphoma": ["CODOX-M/IVAC"],
    "Hodgkin Lymphoma": ["ABVD"],
    "Wilms Tumor": ["Vincristine","Dactinomycin","Doxorubicin"],
    "Neuroblastoma": ["Cyclophosphamide","Topotecan","Cisplatin","Etoposide"],
    "Osteosarcoma": ["MAP"], "Ewing Sarcoma": ["VDC/IE"],
    "LCH": ["Vinblastine","Prednisone"], "JMML": ["Azacitidine","SCT"],
}

# -------- Sidebar (always visible) --------
with st.sidebar:
    st.header("프로필")
    st.session_state["key"] = st.text_input("별명#PIN", value=st.session_state.get("key","guest"), key=wkey("user_key"))
    st.caption("좌측 프로필은 저장/CSV 경로 키로 쓰입니다.")

# -------- Tabs --------
t_home, t_labs, t_dx, t_chemo, t_special, t_report = st.tabs(
    ["🏠 홈","🧪 피수치 입력","🧬 암 선택","💊 항암제","🔬 특수검사","📄 보고서"]
)

with t_home:
    st.info("각 탭에 기본 입력창이 항상 표시됩니다. 외부 파일 없어도 작동합니다.")

with t_labs:
    st.subheader("피수치 입력")
    col1,col2,col3,col4,col5 = st.columns(5)
    with col1: sex = st.selectbox("성별", ["여","남"], key=wkey("sex"))
    with col2: age = st.number_input("나이(세)", 1, 110, 40, key=wkey("age"))
    with col3: wt  = st.number_input("체중(kg)", 0.0, 300.0, 0.0, 0.5, key=wkey("wt"))
    with col4: cr  = st.number_input("Cr (mg/dL)", 0.0, 20.0, 0.8, 0.1, key=wkey("cr"))
    with col5: day = st.date_input("측정일", value=_dt.date.today(), key=wkey("date"))
    # eGFR (CKD-EPI 2009) — simplified impl
    def egfr_2009(cr_mgdl:float, age:int, sex:str):
        sex_f = (sex=="여"); k = 0.7 if sex_f else 0.9; a = -0.329 if sex_f else -0.411
        mn = min(cr_mgdl/k,1); mx = max(cr_mgdl/k,1); sex_fac = 1.018 if sex_f else 1.0
        return round(141*(mn**a)*(mx**-1.209)*(0.993**age)*sex_fac,1)
    egfr = egfr_2009(cr, int(age), sex)
    st.metric("eGFR (CKD-EPI 2009)", f"{egfr} mL/min/1.73㎡")

    # 핵심 수치 입력 (식이가이드/경보에 사용)
    colA,colB,colC,colD,colE,colF,colG,colH = st.columns(8)
    with colA: anc = st.number_input("ANC (/µL)", 0, 500000, 0, step=100, key=wkey("anc"))
    with colB: hb  = st.number_input("Hb (g/dL)", 0.0, 25.0, 0.0, 0.1, key=wkey("hb"))
    with colC: plt = st.number_input("PLT (10^3/µL)", 0, 1000, 0, step=1, key=wkey("plt"))
    with colD: crp = st.number_input("CRP (mg/dL)", 0.0, 50.0, 0.0, 0.1, key=wkey("crp"))
    with colE: alb = st.number_input("Albumin (g/dL)", 0.0, 6.0, 0.0, 0.1, key=wkey("alb"))
    with colF: k   = st.number_input("K (mmol/L)", 0.0, 10.0, 0.0, 0.1, key=wkey("k"))
    with colG: na  = st.number_input("Na (mmol/L)", 0.0, 200.0, 0.0, 1.0, key=wkey("na"))
    with colH: ca  = st.number_input("Ca (mg/dL)", 0.0, 20.0, 0.0, 0.1, key=wkey("ca"))
    # simple rows w/o pandas
    st.session_state.setdefault("lab_rows", [])
    if st.button("➕ 현재 값 추가", key=wkey("add_row")):
        st.session_state["lab_rows"].append({
            "date": str(day),
            "sex": sex, "age": int(age), "weight(kg)": wt,
            "Cr(mg/dL)": cr, "eGFR": egfr,
            "ANC": anc, "Hb": hb, "PLT": plt, "CRP": crp, "Alb": alb, "K": k, "Na": na, "Ca": ca
        })
    rows = st.session_state["lab_rows"]
    if rows:
        st.write("최근 입력:")
        for r in rows[-5:]:
            st.write(r)

with t_dx:
    st.subheader("암 선택")
    grp_tabs = st.tabs(list(GROUPS.keys()))
    for i,(g, lst) in enumerate(GROUPS.items()):
        with grp_tabs[i]:
            labels = [enko(en,ko) for en,ko in lst]
            sel = st.selectbox("진단명을 선택하세요", labels, key=wkey(f"dx_sel_{i}"))
            en_dx, ko_dx = lst[labels.index(sel)]
            if st.button("선택 저장", key=wkey(f"dx_save_{i}")):
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

with t_special:
    spec_lines = special_tests_ui()
with t_report:
    st.subheader("보고서 (.md)")
    dx = enko(st.session_state.get("dx_en",""), st.session_state.get("dx_ko",""))
    meds = st.session_state.get("chemo_list", [])
    rows = st.session_state.get("lab_rows", [])
    labs_latest = rows[-1] if rows else {}
    heme_flag = bool(re.search(r"(ALL|AML|APL|CML|CLL|림프|leuk|lymph)", dx or "", flags=re.I))
    diet_lines = lab_diet_guides(labs_latest, heme_flag=heme_flag)
    top_alerts = collect_top_ae_alerts(meds, db=DRUG_DB)
    spec = st.session_state.get("special", {})
    lines = []
    lines.append("# Bloodmap Report")
    lines.append(f"**진단명**: {dx if dx.strip() else '(미선택)'}")
    lines.append("")
    if top_alerts:
        lines.append("## 🚨 약물 중요 경보")
        for a in top_alerts:
            lines.append(f"- {a}")
        lines.append("")
    lines.append("## 항암제 요약")
    if meds:
        for m in meds: lines.append(f"- {m}")
    else:
        lines.append("- (없음)")
    if rows:
        lines.append("")
        lines.append("## 최근 검사 (최대 5개)")
        head = ["date","sex","age","weight(kg)","Cr(mg/dL)","eGFR"]
        lines.append("| " + " | ".join(head) + " |")
        lines.append("|" + "|".join(["---"]*len(head)) + "|")
        for r in rows[-5:]:
            lines.append("| " + " | ".join(str(r.get(k,'')) for k in head) + " |")
    if diet_lines:
        lines.append("")
        lines.append("## 식이가이드 (최근 수치 기반)")
        for s in diet_lines:
            lines.append(f"- {s}")
    if "spec_lines" in globals() and spec_lines:
        lines.append("")
        lines.append("## 특수검사 (요약)")
        for s in spec_lines:
            lines.append(f"- {s}")
    elif any(spec.values()):
        lines.append("")
        lines.append("## 특수검사")
        if spec.get("gene"):  lines.append(f"- 유전자/표지자: {spec['gene']}")
        if spec.get("image"): lines.append(f"- 이미징/기타: {spec['image']}")
        if spec.get("note"):  lines.append(f"- 메모: {spec['note']}")
    lines.append("")
    lines.append(f"_생성 시각: {_dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_")
    md = "\n".join(lines)
    st.code(md, language="markdown")
    st.download_button("💾 보고서 .md 다운로드", data=md.encode("utf-8"),
                       file_name="bloodmap_report.md", mime="text/markdown", key=wkey("dl_md"))