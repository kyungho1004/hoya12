# app.py — Minimal, always-on inputs (Labs, Diagnosis, Chemo, Special Tests) [PATCH v2025-09-25]
import datetime as _dt
import streamlit as st

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

def _num(x):
    """문자→숫자 변환(콤마/공백 허용). 실패 시 None."""
    try:
        s = str(x).strip().replace(",", "")
        if s == "": return None
        return float(s)
    except Exception:
        return None

# -------- Inline defaults (no external files) --------
GROUPS = {
    "🩸 혈액암 (Leukemia)": [
        ("Acute Lymphoblastic Leukemia (ALL)", "급성 림프모구 백혈병"),
        ("Acute Myeloid Leukemia (AML)", "급성 골수성 백혈병"),
        ("Acute Promyelocytic Leukemia (APL)", "급성 전골수성 백혈병"),
        ("Chronic Myeloid Leukemia (CML)", "만성 골수성 백혈병"),
    ],
    "🧬 림프종 (Lymphoma)": [
        ("Hodgkin Lymphoma", "호지킨 림프종"),
        ("Diffuse Large B-cell Lymphoma (DLBCL)", "미만성 거대 B세포 림프종"),
        ("Burkitt Lymphoma", "버킷 림프종"),
    ],
    "🧠 고형암 (Solid Tumors)": [
        ("Wilms Tumor", "윌름스 종양(신장)"),
        ("Neuroblastoma", "신경모세포종"),
    ],
    "🦴 육종 (Sarcoma)": [
        ("Osteosarcoma", "골육종"),
        ("Ewing Sarcoma", "유잉육종"),
    ],
    "🧩 희귀암 및 기타": [
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
    st.subheader("피수치 입력 (스피너 제거·직접 입력)")
    col1,col2,col3,col4,col5 = st.columns(5)
    with col1:
        sex = st.radio("성별", ["여","남"], horizontal=True, key=wkey("sex"))
    with col2:
        age_raw = st.text_input("나이(세)", value=str(st.session_state.get(wkey("age_val"), "")), placeholder="예: 40", key=wkey("age"))
        age_val = _num(age_raw)
        age = int(age_val) if age_val is not None else 40
        st.session_state[wkey("age_val")] = age
    with col3:
        wt_raw  = st.text_input("체중(kg)", value=str(st.session_state.get(wkey("wt_val"), "")), placeholder="예: 60.5", key=wkey("wt"))
        wt_val = _num(wt_raw)
        wt  = float(wt_val) if wt_val is not None else 0.0
        st.session_state[wkey("wt_val")] = wt
    with col4:
        cr_raw  = st.text_input("Cr (mg/dL)", value=str(st.session_state.get(wkey("cr_val"), "")), placeholder="예: 0.8", key=wkey("cr"))
        cr_val = _num(cr_raw)
        cr  = float(cr_val) if cr_val is not None else 0.8
        st.session_state[wkey("cr_val")] = cr
    with col5:
        day = st.date_input("측정일", value=_dt.date.today(), key=wkey("date"))
    # eGFR (CKD-EPI 2009) — simplified impl (에러 안전화)
    def egfr_2009(cr_mgdl:float, age:int, sex:str):
        try:
            sex_f = (sex=="여"); k = 0.7 if sex_f else 0.9; a = -0.329 if sex_f else -0.411
            mn = min(cr_mgdl/k,1); mx = max(cr_mgdl/k,1); sex_fac = 1.018 if sex_f else 1.0
            return round(141*(mn**a)*(mx**-1.209)*(0.993**age)*sex_fac,1)
        except Exception:
            return 0.0
    egfr = egfr_2009(cr, int(age), sex)
    st.metric("eGFR (CKD-EPI 2009)", f"{egfr} mL/min/1.73㎡")
    # simple rows w/o pandas
    st.session_state.setdefault("lab_rows", [])
    if st.button("➕ 현재 값 추가", key=wkey("add_row")):
        st.session_state["lab_rows"].append({"date":str(day),"sex":sex,"age":int(age),"weight(kg)":wt,"Cr(mg/dL)":cr,"eGFR":egfr})
    rows = st.session_state["lab_rows"]
    if rows:
        st.write("최근 입력:")
        for r in rows[-5:]:
            st.write(r)

with t_dx:
    st.subheader("암 선택 (한 번에 선택)")
    # ✅ 탭/다중 선택창 제거 → 일렬 라디오 버튼으로 단순화
    group = st.radio("카테고리", list(GROUPS.keys()), horizontal=True, key=wkey("dx_group"))
    labels = [enko(en,ko) for en,ko in GROUPS[group]]
    sel = st.radio("진단명", labels, horizontal=True, key=wkey("dx_sel"))
    try:
        idx = labels.index(sel) if sel in labels else 0
    except Exception:
        idx = 0
    en_dx, ko_dx = GROUPS[group][idx]
    if st.button("선택 저장", key=wkey("dx_save")):
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
    st.subheader("특수검사")
    # Always show basic fields so it's never empty
    a,b,c = st.columns(3)
    sp1 = a.text_input("유전자/표지자 (예: BCR-ABL1)", key=wkey("spec_gene"))
    sp2 = b.text_input("이미징/기타 (예: PET/CT 결과)", key=wkey("spec_img"))
    sp3 = c.text_input("기타 메모", key=wkey("spec_note"))
    st.session_state["special"] = {"gene":sp1,"image":sp2,"note":sp3}

with t_report:
    st.subheader("보고서 (.md)")
    dx = enko(st.session_state.get("dx_en",""), st.session_state.get("dx_ko",""))
    meds = st.session_state.get("chemo_list", [])
    rows = st.session_state.get("lab_rows", [])
    spec = st.session_state.get("special", {})
    lines = []
    lines.append("# Bloodmap Report")
    lines.append(f"**진단명**: {dx if dx.strip() else '(미선택)'}")
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
    if any(spec.values()):
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
