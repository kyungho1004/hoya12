
# app.py — BloodMap (safe, connected)
# - Robust imports with fallbacks
# - Input min/max via validators.py
# - "해석하기" gate to avoid spinner/long work before click
# - Connects: branding, special_tests, lab_diet, onco_map, drug_db, ui_results, pdf_export
from __future__ import annotations
import os, sys, traceback, importlib
import datetime as _dt

import streamlit as st

# ---------- Safe optional imports ----------
def _opt(name, attr=None, fallback=None):
    try:
        m = importlib.import_module(name)
        return getattr(m, attr) if attr else m
    except Exception:
        return fallback

branding = _opt("branding")
render_deploy_banner = _opt("branding", "render_deploy_banner", lambda: st.caption("KST 안내·세포치료 비표기·제작: Hoya/GPT"))
special_tests_ui = _opt("special_tests", "special_tests_ui", lambda: [])
lab_diet_guides = _opt("lab_diet", "lab_diet_guides", lambda labs, heme_flag=False: ["(식이가이드 모듈 없음: 기본 안내) 생채소 금지 · 완전가열 · 살균식품 권장 · 남은 음식 2시간 후 폐기"])
onco_map = _opt("onco_map")
CHEMO_MAP = getattr(onco_map, "CHEMO_MAP", {}) if onco_map else {}
drug_db = _opt("drug_db")
ensure_onco_drug_db = getattr(drug_db, "ensure_onco_drug_db", lambda db: None)
DRUG_DB = getattr(drug_db, "DRUG_DB", {})
ALIAS_FALLBACK = getattr(drug_db, "ALIAS_FALLBACK", {})
ui_results = _opt("ui_results")
collect_top_ae_alerts = getattr(ui_results, "collect_top_ae_alerts", lambda drug_keys=None, ref=None: [])
pdf_export = _opt("pdf_export")
export_markdown_to_pdf = getattr(pdf_export, "export_markdown_to_pdf", None)

# Validators (min/max/step)
validators = _opt("validators")
if validators is None:
    class _DummyVal:
        def num_field(self, *a, **k): return st.number_input(*a, **k)
        def clamp(self, f, v): return v
    validators = _DummyVal()
num_field = getattr(validators, "num_field")

# ---------- Page config & CSS ----------
st.set_page_config(page_title="BloodMap", page_icon="🩸", layout="wide")
st.title("🩸 BloodMap")
try:
    render_deploy_banner()
except Exception:
    st.caption("KST 기준 · 세포/면역 치료 비표기 · 제작·자문: Hoya/GPT")

css_path = "/mnt/data/style.css"
if os.path.exists(css_path):
    try:
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception:
        pass

# ---------- Helpers ----------
def wkey(k: str) -> str:
    return f"bm_{k}"

def alias_name(k: str) -> str:
    return ALIAS_FALLBACK.get(k, k)

def to_labs_dict(row: dict) -> dict:
    def g(x): return row.get(x)
    return {
        "Alb": g("Alb"), "K": g("K"), "Hb": g("Hb"), "Na": g("Na"),
        "Ca": g("Ca"), "Glucose": g("Glucose") or g("Glu"),
        "Cr": g("Cr"), "BUN": g("BUN"), "AST": g("AST"),
        "ALT": g("ALT"), "UA": g("UA"), "CRP": g("CRP"),
        "ANC": g("ANC"), "PLT": g("PLT"),
    }

# ---------- DB bootstrap ----------
try:
    ensure_onco_drug_db(DRUG_DB)
except Exception:
    pass

# ---------- Inputs ----------
st.subheader("기본 정보")
cols = st.columns([1,1,1,1])
with cols[0]:
    sex = st.selectbox("성별", ["F","M"], key=wkey("sex"))
with cols[1]:
    age = num_field("나이 (yr)", field="Age", key=wkey("age"), value=30)
with cols[2]:
    weight = num_field("체중 (kg)", field="Weight", key=wkey("wt"), value=60.0)
with cols[3]:
    temp = num_field("체온 (℃)", field="Temp", key=wkey("temp"), value=36.5)

st.markdown("---")
st.subheader("피수치 입력")

lc1, lc2, lc3, lc4 = st.columns(4)
with lc1:
    WBC = num_field("WBC (x10³/µL)", field="WBC", key=wkey("WBC"))
    Hb  = num_field("Hb (g/dL)", field="Hb", key=wkey("Hb"))
    PLT = num_field("PLT (x10³/µL)", field="PLT", key=wkey("PLT"))
with lc2:
    ANC = num_field("ANC (/µL)", field="ANC", key=wkey("ANC"))
    CRP = num_field("CRP (mg/dL)", field="CRP", key=wkey("CRP"))
    UA  = num_field("Uric Acid (mg/dL)", field="UA", key=wkey("UA"))
with lc3:
    Na  = num_field("Na (mEq/L)", field="Na", key=wkey("Na"))
    K   = num_field("K (mEq/L)",  field="K",  key=wkey("K"))
    Ca  = num_field("Ca (mg/dL)", field="Ca", key=wkey("Ca"))
with lc4:
    Alb = num_field("Albumin (g/dL)", field="Alb", key=wkey("Alb"))
    AST = num_field("AST (U/L)", field="AST", key=wkey("AST"))
    ALT = num_field("ALT (U/L)", field="ALT", key=wkey("ALT"))
gl_cols = st.columns([1,1,1])
with gl_cols[0]:
    BUN = num_field("BUN (mg/dL)", field="BUN", key=wkey("BUN"))
with gl_cols[1]:
    Cr  = num_field("Cr (mg/dL)", field="Cr", key=wkey("Cr"))
with gl_cols[2]:
    Glu = num_field("Glucose (mg/dL)", field="Glucose", key=wkey("Glu"))

# Save a lab row (simple)
if st.button("검사 행 추가", key=wkey("add_row")):
    row = {"date": _dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
           "sex": sex, "age": age, "weight(kg)": weight, "Temp": temp,
           "WBC": WBC, "Hb": Hb, "PLT": PLT, "ANC": ANC, "CRP": CRP,
           "Na": Na, "K": K, "Ca": Ca, "Alb": Alb, "AST": AST, "ALT": ALT,
           "BUN": BUN, "Cr": Cr, "UA": UA, "Glucose": Glu}
    st.session_state.setdefault("lab_rows", []).append(row)
    st.success("한 행을 추가했습니다.")

rows = st.session_state.get("lab_rows", [])

# ---------- Diagnosis / Chemo ----------
st.markdown("---")
st.subheader("암 선택 / 항암제")
dcols = st.columns([2,3])
with dcols[0]:
    dx = st.selectbox("진단(예: AML, ALL, Lymphoma, Solid)", ["", "AML", "ALL", "Lymphoma", "Solid", "Sarcoma", "APL"], key=wkey("dx"))
    if st.button("진단 저장", key=wkey("dx_save")):
        st.session_state["dx_en"] = dx or ""
        st.success("진단을 저장했습니다.")
with dcols[1]:
    suggestions = CHEMO_MAP.get(dx, [])
    meds = st.multiselect("항암제 선택/추가", options=suggestions, default=suggestions, key=wkey("chemo_ms"))
    extra = st.text_input("추가 항암제(쉼표 구분)", key=wkey("chemo_extra"))
    if extra.strip():
        meds.extend([x.strip() for x in extra.split(",") if x.strip()])
    meds = list(dict.fromkeys(meds))
    if st.button("항암제 저장", key=wkey("chemo_save")):
        st.session_state["chemo_meds"] = meds
        st.success("항암제를 저장했습니다.")

# ---------- Tabs ----------
t1, t2, t3, t4 = st.tabs(["🔬 특수검사", "⚠️ 부작용 요약", "📊 최근 검사", "📄 보고서"])

with t1:
    st.caption("특수검사 모듈 결과")
    try:
        spec_lines = special_tests_ui() or []
    except Exception as e:
        st.warning(f"특수검사 모듈 오류: {type(e).__name__}")
        spec_lines = []
    st.session_state["special_lines"] = spec_lines
    if spec_lines:
        st.write("\n".join(f"- {x}" for x in spec_lines))
    else:
        st.info("특수검사 항목이 없습니다.")

with t2:
    meds = st.session_state.get("chemo_meds", [])
    alerts = []
    try:
        alerts = collect_top_ae_alerts(drug_keys=meds, ref=None) or []
    except Exception:
        pass
    if alerts:
        st.error("**중요 부작용 경고**\n\n- " + "\n- ".join(alerts))
    else:
        st.success("표시할 경고가 없습니다.")

with t3:
    if rows:
        st.write(f"총 {len(rows)}개 기록")
        st.dataframe(rows, use_container_width=True)
    else:
        st.info("추가된 검사 행이 없습니다.")

with t4:
    st.caption("보고서는 '해석하기' 버튼 후 생성됩니다.")
    if st.button("🔎 해석하기", key=wkey("analyze")):
        lines = []
        lines.append("# BloodMap 보고서")
        dx_en = st.session_state.get("dx_en","")
        if dx_en:
            lines.append(f"**진단**: {dx_en}")
        meds = st.session_state.get("chemo_meds", [])
        if meds:
            lines.append("**항암제**:")
            for m in meds:
                lines.append(f"- {alias_name(m)}")
        else:
            lines.append("**항암제**: (없음)")

        if rows:
            lines.append("")
            lines.append("## 최근 검사 요약 (최대 5개)")
            head = ["date","sex","age","weight(kg)","Cr","Glucose","WBC","Hb","PLT","ANC","CRP","Na","K","Ca","Alb","AST","ALT","BUN","UA"]
            lines.append("| " + " | ".join(head) + " |")
            lines.append("|" + "|".join(["---"]*len(head)) + "|")
            for r in rows[-5:]:
                lines.append("| " + " | ".join(str(r.get(k,'')) for k in head) + " |")

            # 식이가이드
            try:
                guides = lab_diet_guides(to_labs_dict(rows[-1]), heme_flag=True)
                if guides:
                    lines.append("")
                    lines.append("## 피수치 기반 식이가이드")
                    for g in guides:
                        lines.append(f"- {g}")
            except Exception as e:
                lines.append("")
                lines.append(f"_(식이가이드 생성 실패: {type(e).__name__})_")

        # 특수검사
        spec = st.session_state.get("special_lines", [])
        if spec:
            lines.append("")
            lines.append("## 특수검사")
            for sline in spec:
                lines.append(f"- {sline}")

        # 부작용 요약
        alerts = st.session_state.get("alerts_cache") or []
        if not alerts:
            try:
                alerts = collect_top_ae_alerts(drug_keys=meds, ref=None) or []
            except Exception:
                alerts = []
        if alerts:
            lines.append("")
            lines.append("## 부작용 경고(요약)")
            for a in alerts:
                lines.append(f"- {a}")

        lines.append("")
        lines.append(f"_생성 시각(KST): {_dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_")
        md = "\n".join(lines)
        st.code(md, language="markdown")
        st.download_button("💾 보고서 .md 다운로드", data=md.encode("utf-8"),
                           file_name="bloodmap_report.md", mime="text/markdown", key=wkey("dl_md"))

        # PDF (옵션)
        if export_markdown_to_pdf:
            if st.button("🖨️ PDF 내보내기", key=wkey("pdf_btn")):
                try:
                    pdf_bytes = export_markdown_to_pdf(md)
                    st.download_button("📥 PDF 저장", data=pdf_bytes, file_name="bloodmap_report.pdf", mime="application/pdf", key=wkey("pdf_dl"))
                except Exception as e:
                    st.warning("PDF 모듈이 없어 .md만 지원합니다. (reportlab 설치 필요)")

st.caption("ⓒ Hoya/GPT — 세포/면역 치료는 표기하지 않습니다(혼돈 방지).")
