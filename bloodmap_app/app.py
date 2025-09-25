# app.py — BloodMap Minimal Functional UI
import datetime as _dt
import math
import streamlit as st

# ---------- Branding banner (safe fallback) ----------
try:
    from branding import render_deploy_banner
except Exception:
    def render_deploy_banner(*a, **k): 
        st.caption("KST · 세포·면역치료는 표기하지 않습니다 · 제작/자문: Hoya/GPT")

st.set_page_config(page_title="BloodMap", layout="wide")
st.title("BloodMap")
render_deploy_banner("https://bloodmap.streamlit.app/", "제작: Hoya/GPT · 자문: Hoya/GPT")

# ---------- Helpers ----------
def wkey(name:str)->str:
    return f"bm_{abs(hash(name))%10_000_000}_{name}"

def color_badge(text, level):
    colors = {"ok":"🟢","warn":"🟡","alert":"🚨"}
    return f"{colors.get(level,'')} {text}"

# ---------- Sidebar: Profile ----------
with st.sidebar:
    st.subheader("프로필")
    nick = st.text_input("별명", value="게스트", key=wkey("nick"))
    age_group = st.selectbox("구분", ["소아","성인","일상"], index=1, key=wkey("agegrp"))
    st.markdown("—")
    st.caption("혼돈 방지 및 범위 밖 안내: 저희는 **세포·면역 치료(CAR‑T, TCR‑T, NK, HSCT 등)**는 표기하지 않습니다.")

# ---------- Main: Inputs ----------
st.header("피수치 입력")
col1, col2, col3 = st.columns(3)

with col1:
    WBC = st.number_input("WBC (×10³/µL)", min_value=0.0, step=0.1, key=wkey("WBC"))
    Hb  = st.number_input("Hb (g/dL)", min_value=0.0, step=0.1, key=wkey("Hb"))
    PLT = st.number_input("PLT (×10³/µL)", min_value=0.0, step=1.0, key=wkey("PLT"))
    ANC = st.number_input("ANC (cells/µL)", min_value=0.0, step=10.0, key=wkey("ANC"))
with col2:
    CRP = st.number_input("CRP (mg/dL)", min_value=0.0, step=0.1, key=wkey("CRP"))
    Na  = st.number_input("Na (mEq/L)", min_value=0.0, step=0.5, key=wkey("Na"))
    K   = st.number_input("K (mEq/L)", min_value=0.0, step=0.1, key=wkey("K"))
    Alb = st.number_input("Albumin (g/dL)", min_value=0.0, step=0.1, key=wkey("Alb"))
with col3:
    Ca  = st.number_input("Calcium (mg/dL)", min_value=0.0, step=0.1, key=wkey("Ca"))
    AST = st.number_input("AST (U/L)", min_value=0.0, step=1.0, key=wkey("AST"))
    ALT = st.number_input("ALT (U/L)", min_value=0.0, step=1.0, key=wkey("ALT"))
    Glu = st.number_input("Glucose (mg/dL)", min_value=0.0, step=1.0, key=wkey("Glu"))

st.markdown("---")
st.header("진단 · 카테고리")
cat = st.selectbox(
    "암 카테고리",
    ["혈액암","림프종","육종","고형암","희귀암"],
    key=wkey("cat")
)

DIAG = {
    "혈액암": ["ALL","AML","APL"],
    "림프종": ["호지킨 림프종","비호지킨 림프종"],
    "육종": ["유잉육종","골육종","횡문근육종"],
    "고형암": ["신경모세포종","윌름스 종양","간모세포종"],
    "희귀암": ["LCH","JMML"]
}
dx = st.selectbox("진단(예시)", DIAG.get(cat, []), key=wkey("dx"))

st.markdown("---")
st.header("특수검사(선택)")
spec_gene  = st.text_input("유전자/표지자", key=wkey("gene"))
spec_image = st.text_input("이미징/기타", key=wkey("image"))
spec_note  = st.text_area("메모", key=wkey("note"))

# ---------- Action ----------
go = st.button("해석하기", key=wkey("run"))

# ---------- Interpretation ----------
def interp_range(val, low=None, high=None):
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return "warn"
    if low is not None and val < low: 
        return "alert" if (low - val) / max(low,1) > 0.2 else "warn"
    if high is not None and val > high: 
        return "alert" if (val - high) / max(high,1) > 0.2 else "warn"
    return "ok"

NORMALS_ADULT = {
    "WBC": (4.0, 10.0),
    "Hb": (12.0, 16.0),
    "PLT": (150.0, 450.0),
    "CRP": (0.0, 0.5),
    "ANC": (1500.0, None),
    "Na": (135.0, 145.0),
    "K": (3.5, 5.1),
    "Alb": (3.5, 5.0),
    "Ca": (8.6, 10.2),
    "AST": (0.0, 40.0),
    "ALT": (0.0, 41.0),
    "Glu": (70.0, 199.0),
}

def eval_labs():
    res = []
    for name, val in [("WBC",WBC),("Hb",Hb),("PLT",PLT),("CRP",CRP),("ANC",ANC),
                      ("Na",Na),("K",K),("Alb",Alb),("Ca",Ca),("AST",AST),("ALT",ALT),("Glu",Glu)]:
        low, high = NORMALS_ADULT.get(name,(None,None))
        level = interp_range(val, low, high)
        res.append((name, val, level, low, high))
    return res

def anc_diet_guide(anc):
    if anc is None:
        return ""
    anc = float(anc)
    if anc < 500:
        return ("🚨 ANC < 500: 생채소 금지, 모든 음식은 충분히 익혀 섭취, "
                "조리 후 남은 음식 2시간 이후 섭취 금지, 멸균/살균식품 권장, "
                "껍질 있는 과일은 주치의 상담 후 결정.")
    elif anc < 1000:
        return ("🟡 ANC 500~1000: 가급적 익힌 음식 위주, 위생 철저, 남은 음식은 빠르게 냉장.")
    else:
        return ("🟢 ANC ≥ 1000: 일반 권장식이 가능(개별 상태에 따라 조정).")

if go:
    st.subheader("해석 결과")
    rows = eval_labs()
    for name, val, level, low, high in rows:
        rng = []
        if low is not None: rng.append(f"≥ {low}")
        if high is not None: rng.append(f"≤ {high}")
        rng_txt = (" / ".join(rng)) if rng else "참고범위 없음"
        st.write(color_badge(f"{name}: {val}  ({rng_txt})", level))

    # ANC 식이가이드
    st.markdown("---")
    st.markdown("### ANC 식이가이드")
    st.info(anc_diet_guide(ANC))

    # Report (markdown preview + download)
    st.markdown("---")
    st.markdown("### 보고서 미리보기(.md)")
    lines = []
    lines.append(f"# BloodMap 결과 — {nick}")
    lines.append(f"- 구분: {age_group}")
    lines.append(f"- 카테고리/진단: {cat} / {dx}")
    lines.append("")
    lines.append("## 피수치")
    for name, val, level, low, high in rows:
        lines.append(f"- {name}: {val}")
    if any([spec_gene, spec_image, spec_note]):
        lines.append("")
        lines.append("## 특수검사")
        if spec_gene:  lines.append(f"- 유전자/표지자: {spec_gene}")
        if spec_image: lines.append(f"- 이미징/기타: {spec_image}")
        if spec_note:  lines.append(f"- 메모: {spec_note}")
    lines.append("")
    lines.append(f"_생성 시각(KST): {_dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_")
    md = "\n".join(lines)
    st.code(md, language="markdown")
    st.download_button("💾 보고서 .md 다운로드", data=md.encode("utf-8"),
                       file_name="bloodmap_report.md", mime="text/markdown", key=wkey("dl_md"))
else:
    st.caption("※ '해석하기' 버튼을 눌러야 결과가 표시됩니다.")
