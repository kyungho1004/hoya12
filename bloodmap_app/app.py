
# app.py — Safe Boot (minimal to bypass server errors)
import datetime as _dt
import streamlit as st

# --- Branding (safe no-op) ---
try:
    from branding import render_deploy_banner
except Exception:
    def render_deploy_banner(*a, **k): pass

st.set_page_config(page_title="Bloodmap — Safe Boot", layout="wide")
st.title("Bloodmap — Safe Boot")
render_deploy_banner("https://bloodmap.streamlit.app/", "제작: Hoya/GPT · 자문: Hoya/GPT")

st.info("🛟 안전 모드로 부팅했습니다. (서버 오류 회피용 최소 기능)")

# --- Helpers ---
def wkey(name:str)->str:
    return f"bm_{name}"

def enko(en:str, ko:str)->str:
    return f"{en} — {ko}" if ko else en

# --- Single-line diagnosis picker (no tabs, no external maps) ---
GROUPS = {
    "🧬 림프종": [
        ("Diffuse Large B-cell Lymphoma (DLBCL)", "미만성 거대 B세포 림프종"),
        ("Hodgkin Lymphoma", "호지킨 림프종"),
        ("Burkitt Lymphoma", "버킷 림프종"),
    ],
    "🩸 백혈병": [
        ("Acute Lymphoblastic Leukemia (ALL)", "급성 림프모구 백혈병"),
        ("Acute Myeloid Leukemia (AML)", "급성 골수성 백혈병"),
        ("Acute Promyelocytic Leukemia (APL)", "급성 전골수성 백혈병"),
    ],
    "🦴 육종": [
        ("Osteosarcoma", "골육종"),
        ("Ewing Sarcoma", "유잉육종"),
    ],
    "🧠 고형암": [
        ("Wilms Tumor", "윌름스 종양"),
        ("Neuroblastoma", "신경모세포종"),
    ],
}

t_home, t_labs, t_dx, t_report = st.tabs(["홈","피수치","암 선택","보고서"])

with t_home:
    st.write("이 모드는 서버 오류를 우선 복구하기 위한 최소 기능만 제공합니다.")
    st.write("정상 모드 복귀 준비가 되면 '안전모드 해제' 토글을 끄고 리런하세요.")

with t_labs:
    st.subheader("피수치 입력 (안전모드 최소)")
    col1,col2,col3,col4,col5 = st.columns(5)
    with col1: sex = st.selectbox("성별", ["여","남"], key=wkey("sex"))
    with col2: age = st.number_input("나이(세)", 1, 110, 40, key=wkey("age"))
    with col3: wt  = st.number_input("체중(kg)", 0.0, 300.0, 0.0, 0.5, key=wkey("wt"))
    with col4: cr  = st.number_input("Cr (mg/dL)", 0.0, 20.0, 0.8, 0.1, key=wkey("cr"))
    with col5: day = st.date_input("측정일", value=_dt.date.today(), key=wkey("date"))
    # eGFR (CKD-EPI 2009) — simplified
    def egfr_2009(cr_mgdl:float, age:int, sex:str):
        sex_f = (sex=="여"); k = 0.7 if sex_f else 0.9; a = -0.329 if sex_f else -0.411
        mn = min(cr_mgdl/k,1); mx = max(cr_mgdl/k,1); sex_fac = 1.018 if sex_f else 1.0
        return round(141*(mn**a)*(mx**-1.209)*(0.993**age)*sex_fac,1)
    egfr = egfr_2009(cr, int(age), sex)
    st.metric("eGFR (CKD-EPI 2009)", f"{egfr} mL/min/1.73㎡")
    if st.button("➕ 현재 값 추가", key=wkey("add_row")):
        st.session_state.setdefault("lab_rows", []).append({
            "date":str(day),"sex":sex,"age":int(age),"weight(kg)":wt,"Cr(mg/dL)":cr,"eGFR":egfr
        })
    rows = st.session_state.get("lab_rows", [])
    if rows:
        st.write("최근 입력:")
        for r in rows[-5:]:
            st.write(r)

with t_dx:
    st.subheader("암 선택 (한 줄 선택)")
    joined = []
    for G, lst in GROUPS.items():
        for en, ko in lst:
            joined.append((f"{G} | {enko(en, ko)}", en, ko))
    labels = [lab for lab, _, _ in joined]
    sel = st.selectbox("진단명을 선택", labels, key=wkey("dx_one_select"))
    _, en_dx, ko_dx = next(x for x in joined if x[0]==sel)
    colA, colB = st.columns([1,1])
    with colA:
        if st.button("선택 저장", key=wkey("dx_save_one")):
            st.session_state["dx_en"] = en_dx
            st.session_state["dx_ko"] = ko_dx
            st.success(f"저장됨: {enko(en_dx, ko_dx)}")
    with colB:
        if st.button("초기화", key=wkey("dx_clear")):
            st.session_state.pop("dx_en", None)
            st.session_state.pop("dx_ko", None)
            st.info("진단 선택이 초기화되었습니다.")

with t_report:
    st.subheader("보고서 (안전모드)")
    rows = st.session_state.get("lab_rows", [])
    dx_en = st.session_state.get("dx_en",""); dx_ko = st.session_state.get("dx_ko","")
    lines = ["# Bloodmap — 안전모드 보고서",""]
    if dx_en or dx_ko:
        lines.append(f"## 진단명: {enko(dx_en, dx_ko)}")
    if rows:
        head = list(rows[-1].keys())
        lines.append("## 최근 입력 (표)")
        lines.append("| " + " | ".join(head) + " |")
        lines.append("|" + "|".join(["---"]*len(head)) + "|")
        for r in rows[-5:]:
            lines.append("| " + " | ".join(str(r.get(k,'')) for k in head) + " |")
    lines.append("")
    lines.append(f"_생성 시각: {_dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_")
    md = "\n".join(lines)
    st.code(md, language="markdown")
    st.download_button("💾 보고서 .md 다운로드", data=md.encode("utf-8"),
                       file_name="bloodmap_report_safe.md", mime="text/markdown", key=wkey("dl_md"))
