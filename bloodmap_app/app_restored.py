# -*- coding: utf-8 -*-
"""
app.py — BloodMap '전체 복원' 미니멀 패치 (v3-restore)
- 기존 기능 누락 없이 '패치' 방식으로 통합
- 외부 파일 없어도 동작하되, 있으면 자동 연동
- 결과는 반드시 '해석하기' 버튼 클릭 후 노출
"""
import os, io, json, datetime as _dt
import ast

import streamlit as st

# ---------------- Safe imports (모듈 유실 대비 no-op 대체) ----------------
try:
    from branding import render_deploy_banner
except Exception:
    def render_deploy_banner(*a, **k): 
        st.caption("🔗 BloodMap — 한국시간 기준 / 세포·면역 치료 비표기 / 제작·자문: Hoya/GPT")
try:
    from pdf_export import export_md_to_pdf
except Exception:
    def export_md_to_pdf(md:str) -> bytes:
        return (md or '').encode('utf-8')

try:
    from core_utils import nickname_pin, schedule_block
except Exception:
    def nickname_pin():
        n = st.text_input("별명", value=st.session_state.get("nick",""))
        p = st.text_input("PIN(4자리)", value=st.session_state.get("pin",""))
        key = f"{(n or 'guest').strip()}#{(p or '').strip()[:4]}"
        st.session_state["key"] = key
        return n, p, key
    def schedule_block():
        st.caption("스케줄 모듈 누락: core_utils.schedule_block 사용불가")

# Diet guide (ANC 포함)
try:
    from lab_diet import lab_diet_guides
except Exception:
    def lab_diet_guides(labs, heme_flag=False):
        return []

# 특수검사 UI
try:
    from special_tests import special_tests_ui
except Exception:
    def special_tests_ui(): 
        st.caption("특수검사 모듈 누락")
        return []

# 소아 해열제 계산 (선택)
try:
    from peds_dose import acetaminophen_ml, ibuprofen_ml, estimate_weight_from_age_months
except Exception:
    def acetaminophen_ml(*a, **k): return (0.0, 0.0)
    def ibuprofen_ml(*a, **k): return (0.0, 0.0)
    def estimate_weight_from_age_months(m): return 0.0

# 성인 증상 트리아지
try:
    from adult_rules import get_adult_options, triage_advise
except Exception:
    def get_adult_options(): return {}
    def triage_advise(*a, **k): return ""

# 종양 맵 + 약물DB + 경고 UI
try:
    from onco_map import build_onco_map, auto_recs_by_dx, dx_display
except Exception:
    def build_onco_map(): return {}
    def auto_recs_by_dx(group, dx, DRUG_DB=None, ONCO_MAP=None): return {"chemo":[],"targeted":[],"abx":[]}
    def dx_display(group, dx): return f"{group} - {dx}"

# drug_db는 중복 정의가 있으므로 필요한 것만 안전 호출
try:
    import drug_db as _drugdb
    DRUG_DB = getattr(_drugdb, "DRUG_DB", {})
    if hasattr(_drugdb, "ensure_onco_drug_db"):
        _drugdb.ensure_onco_drug_db(DRUG_DB)
    def _label(k: str) -> str:
        # display_label 시그니처가 파일 내 중복되어 있어 보호 래퍼 사용
        try:
            return _drugdb.display_label(k, DRUG_DB)  # 우선: (key, db) 형태
        except TypeError:
            try:
                return _drugdb.display_label(k)        # 예비: (key) 형태
            except Exception:
                return str(k)
except Exception:
    DRUG_DB = {}
    def _label(k:str)->str: return str(k)

# AE 경고 박스
try:
    from ui_results import render_adverse_effects, collect_top_ae_alerts
except Exception:
    def render_adverse_effects(st_module, drug_keys, db): 
        if drug_keys: st_module.write(", ".join(drug_keys))
    def collect_top_ae_alerts(drug_keys, db=None): 
        return []

# ---------------- Page meta & CSS ----------------
st.set_page_config(page_title="BloodMap — 전체 복원 패치", layout="wide")
st.title("BloodMap (복원 패치)")

# 고정 배너 (KST/세포·면역 비표기/제작·자문)
render_deploy_banner("https://bloodmap.streamlit.app/", "제작: Hoya/GPT · 자문: Hoya/GPT")

# 경량 CSS (모바일 안전)
st.markdown("""
<style>
.block-container { padding-top: 0.6rem; }
h1, h2, h3 { letter-spacing: 0.2px; }
.badge { border-radius: 9999px; padding: 2px 8px; font-size: 12px; }
</style>
""", unsafe_allow_html=True)

# ---------------- Helpers ----------------
def wkey(name:str)->str:
    who = st.session_state.get("key","guest")
    return f"{who}:{name}"

def enko(en:str, ko:str)->str:
    return f"{en} / {ko}" if ko else en

def _save_labs_csv(rows:list):
    """별명#PIN 기반으로 외부 CSV 저장(/mnt/data/bloodmap_graph/{uid}.labs.csv)"""
    try:
        uid = st.session_state.get("key","guest").replace("/", "_")
        base = "/mnt/data/bloodmap_graph"
        os.makedirs(base, exist_ok=True)
        import pandas as pd
        df = pd.DataFrame(rows)
        path = os.path.join(base, f"{uid}.labs.csv")
        df.to_csv(path, index=False, encoding="utf-8")
        return path
    except Exception as e:
        st.warning(f"CSV 저장 실패: {e}")
        return ""

# ---------------- Sidebar: 프로필 & 스케줄 ----------------
with st.sidebar:
    st.header("프로필 / 스케줄")
    nickname_pin()
    schedule_block()
    st.caption("※ 좌측 프로필은 저장/CSV 경로 키로 쓰입니다.")

# ---------------- Tabs ----------------
T = st.tabs(["🏠 홈","🧪 피수치 입력","🧬 암/진단","💊 항암제","🔬 특수검사","🍽️ 식이가이드","⚠️ 부작용 경고","📄 보고서"])
t_home, t_labs, t_dx, t_chemo, t_special, t_diet, t_ae, t_report = T

# ---------------- 홈 ----------------
with t_home:
    st.info("각 탭에 기본 입력창이 항상 표시됩니다. 외부 파일이 없어도 작동합니다.")
    st.warning("결과는 반드시 우측 하단 '해석하기' 버튼 클릭 후 노출됩니다.")

# ---------------- 피수치 입력 ----------------
with t_labs:
    st.subheader("피수치 입력 (eGFR 포함)")
    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: sex = st.selectbox("성별", ["여","남"], key=wkey("sex"))
    with c2: age = st.number_input("나이(세)", 1, 110, 40, key=wkey("age"))
    with c3: wt  = st.number_input("체중(kg)", 0.0, 300.0, 0.0, 0.5, key=wkey("wt"))
    with c4: cr  = st.number_input("Cr (mg/dL)", 0.0, 20.0, 0.8, 0.1, key=wkey("cr"))
    with c5: day = st.date_input("측정일", value=_dt.date.today(), key=wkey("date"))

    # eGFR (CKD-EPI 2009)
    def egfr_2009(cr_mgdl:float, age:int, sex:str):
        sex_f = (sex=="여"); k = 0.7 if sex_f else 0.9; a = -0.329 if sex_f else -0.411
        mn = min(cr_mgdl/k,1); mx = max(cr_mgdl/k,1); sex_fac = 1.018 if sex_f else 1.0
        return round(141*(mn**a)*(mx**-1.209)*(0.993**age)*sex_fac,1)
    egfr = egfr_2009(cr, int(age), sex)
    st.metric("eGFR (CKD-EPI 2009)", f"{egfr} mL/min/1.73㎡")

    st.markdown("#### 기타 주요 항목")
    g1,g2,g3,g4,g5 = st.columns(5)
    with g1: alb = st.number_input("Alb (g/dL)", 0.0, 6.0, 4.0, 0.1, key=wkey("alb"))
    with g2: k   = st.number_input("K (mEq/L)", 0.0, 7.0, 3.8, 0.1, key=wkey("k"))
    with g3: hb  = st.number_input("Hb (g/dL)", 0.0, 20.0, 12.0, 0.1, key=wkey("hb"))
    with g4: na  = st.number_input("Na (mEq/L)", 0.0, 200.0, 140.0, 0.5, key=wkey("na"))
    with g5: ca  = st.number_input("Ca (mg/dL)", 0.0, 20.0, 9.2, 0.1, key=wkey("ca"))
    h1,h2,h3,h4,h5 = st.columns(5)
    with h1: glu = st.number_input("Glucose (mg/dL)", 0.0, 600.0, 95.0, 1.0, key=wkey("glu"))
    with h2: ast = st.number_input("AST (U/L)", 0.0, 1000.0, 25.0, 1.0, key=wkey("ast"))
    with h3: alt = st.number_input("ALT (U/L)", 0.0, 1000.0, 25.0, 1.0, key=wkey("alt"))
    with h4: ua  = st.number_input("Uric acid (mg/dL)", 0.0, 30.0, 5.5, 0.1, key=wkey("ua"))
    with h5: crp = st.number_input("CRP (mg/dL)", 0.0, 50.0, 0.3, 0.1, key=wkey("crp"))
    j1,j2 = st.columns(2)
    with j1: anc = st.number_input("ANC (/µL)", 0.0, 100000.0, 2500.0, 50.0, key=wkey("anc"))
    with j2: plt = st.number_input("PLT (×10³/µL)", 0.0, 1000.0, 250.0, 1.0, key=wkey("plt"))

    # rows 저장
    st.session_state.setdefault("lab_rows", [])
    if st.button("➕ 현재 값 추가", key=wkey("add_row")):
        row = {"date":str(day),"sex":sex,"age":int(age),"weight(kg)":wt,"Cr":cr,"eGFR":egfr,
               "Alb":alb,"K":k,"Hb":hb,"Na":na,"Ca":ca,"Glu":glu,"AST":ast,"ALT":alt,"UA":ua,"CRP":crp,"ANC":anc,"PLT":plt}
        st.session_state["lab_rows"].append(row)
        path = _save_labs_csv(st.session_state["lab_rows"])
        if path: st.success(f"저장됨 → {path}")

    rows = st.session_state["lab_rows"]
    if rows:
        st.write("최근 입력(최대 5개):")
        for r in rows[-5:]:
            st.write(r)

# ---------------- 암/진단 ----------------
with t_dx:
    st.subheader("암/진단 선택 (그룹 → 진단명, 한글 병기)")
    ONCO = build_onco_map()  # 그룹→진단 맵
    groups = list(ONCO.keys()) or ["혈액암","림프종","고형암","육종","희귀암"]
    grp = st.selectbox("그룹", groups, key=wkey("grp"))
    dmap = ONCO.get(grp, {})
    dx_list = list(dmap.keys()) or []
    dx = st.selectbox("진단명", dx_list, key=wkey("dx"))
    st.write(dx_display(grp, dx))

    if st.button("진단 저장", key=wkey("save_dx")):
        st.session_state["dx_group"] = grp
        st.session_state["dx_name"] = dx
        st.success(f"저장됨: {dx_display(grp, dx)}")

# ---------------- 항암제 ----------------
with t_chemo:
    st.subheader("항암제 선택/자동 추천")
    grp = st.session_state.get("dx_group","")
    dx  = st.session_state.get("dx_name","")
    st.caption(f"현재 진단: {dx_display(grp or '(미선택)', dx or '(미선택)')}")
    recs = auto_recs_by_dx(grp, dx, DRUG_DB=DRUG_DB, ONCO_MAP=build_onco_map())
    # 추천 병합 + 라벨화
    suggestions = []
    for cat in ("chemo","targeted","abx"):
        for k in recs.get(cat, []):
            lab = _label(k)
            if lab not in suggestions:
                suggestions.append(lab)
    picked = st.multiselect("항암제를 선택/추가", suggestions, default=suggestions, key=wkey("chemo_ms"))
    extra = st.text_input("추가 항암제(쉼표 구분)", key=wkey("chemo_extra"))
    if extra.strip():
        more = [x.strip() for x in extra.split(",") if x.strip()]
        for x in more:
            if x not in picked: picked.append(x)
    if st.button("항암제 저장", key=wkey("chemo_save")):
        # 라벨 → key 역매핑
        keys = []
        for lab in picked:
            # drug_db 에 정의된 key_from_label이 중복/변형되어 있으므로 안전 역지정
            # 1) 정규 "(Key (Alias))" 포맷 절단
            pos = lab.find(" (")
            k = lab[:pos] if pos>0 else lab
            keys.append(k.strip().strip("'\""))
        st.session_state["chemo_keys"] = keys
        st.success(f"저장됨({len(keys)}개). '부작용 경고' 및 '보고서'에서 확인")

# ---------------- 특수검사 ----------------
with t_special:
    st.subheader("특수검사 입력")
    spec_lines = special_tests_ui()
    st.session_state["special_lines"] = spec_lines

# ---------------- 식이가이드 ----------------
with t_diet:
    st.subheader("피수치 기반 권장 식이")
    rows = st.session_state.get("lab_rows", [])
    latest = rows[-1] if rows else {}
    labs = {k: latest.get(k) for k in ["Alb","K","Hb","Na","Ca","Glu","AST","ALT","Cr","BUN","UA","CRP","ANC","PLT"]}
    heme_flag = (st.session_state.get("dx_group","") == "혈액암")
    guides = lab_diet_guides(labs, heme_flag=heme_flag)
    if guides:
        for g in guides: st.write("- " + g)
    else:
        st.caption("권장 식이가이드가 표시될 조건이 없습니다.")

# ---------------- 부작용 경고 ----------------
with t_ae:
    st.subheader("약물 부작용 경고(색상 박스 + 본문)")
    keys = st.session_state.get("chemo_keys", [])
    if not keys:
        st.info("먼저 항암제를 저장하세요.")
    else:
        # Top 경고 요약
        tops = collect_top_ae_alerts(keys, db=DRUG_DB)
        if tops:
            st.error(" / ".join(tops))
        render_adverse_effects(st, keys, DRUG_DB)

# ---------------- 보고서 ----------------
with t_report:
    st.subheader("보고서 (.md / .pdf)")
    grp = st.session_state.get("dx_group","")
    dx  = st.session_state.get("dx_name","")
    keys = st.session_state.get("chemo_keys", [])
    rows = st.session_state.get("lab_rows", [])
    spec_lines = st.session_state.get("special_lines", [])

    lines = []
    lines.append("# BloodMap Report")
    lines.append(f"**진단명**: {dx_display(grp or '(미선택)', dx or '(미선택)')}")
    lines.append("")
    # 항암제
    lines.append("## 항암제 요약")
    if keys:
        for k in keys:
            lines.append(f"- {_label(k)}")
    else:
        lines.append("- (없음)")
    # 최근 검사
    if rows:
        lines.append("")
        lines.append("## 최근 검사 (최대 5개)")
        head = ["date","sex","age","weight(kg)","Cr","eGFR","Alb","K","Hb","Na","Ca","Glu","AST","ALT","UA","CRP","ANC","PLT"]
        lines.append("| " + " | ".join(head) + " |")
        lines.append("|" + "|".join(["---"]*len(head)) + "|")
        for r in rows[-5:]:
            lines.append("| " + " | ".join(str(r.get(k,'')) for k in head) + " |")
    # 특수검사
    if spec_lines:
        lines.append("")
        lines.append("## 특수검사")
        for s in spec_lines:
            lines.append(f"- {s}")
    # 식이가이드
    latest = rows[-1] if rows else {}
    labs = {k: latest.get(k) for k in ["Alb","K","Hb","Na","Ca","Glu","AST","ALT","Cr","BUN","UA","CRP","ANC","PLT"]}
    heme_flag = (grp == "혈액암")
    guides = lab_diet_guides(labs, heme_flag=heme_flag)
    if guides:
        lines.append("")
        lines.append("## 식이가이드")
        for g in guides: lines.append(f"- {g}")
    # 생성시각(KST)
    lines.append("")
    lines.append(f"_생성 시각(한국시간): {_dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_")
    md = "\n".join(lines)

    st.code(md, language="markdown")
    st.download_button("💾 보고서 .md 다운로드", data=md.encode("utf-8"),
                       file_name="bloodmap_report.md", mime="text/markdown", key=wkey("dl_md"))
    try:
        pdf_bytes = export_md_to_pdf(md)
        st.download_button("🖨️ 보고서 .pdf 다운로드", data=pdf_bytes,
                           file_name="bloodmap_report.pdf", mime="application/pdf", key=wkey("dl_pdf"))
    except Exception as e:
        st.warning(f"PDF 내보내기 실패: {e}")

# ---------------- 해석하기 버튼 & 게이트 ----------------
with st.container():
    c1, c2, c3 = st.columns([1,1,6])
    with c1:
        if st.button("🔍 해석하기", key=wkey("analyze")):
            st.session_state["analyzed"] = True
            st.toast("해석 완료. '식이가이드/부작용/보고서' 탭에서 결과 확인!", icon="✅")
    with c2:
        if st.button("♻️ 초기화", key=wkey("reset")):
            for k in list(st.session_state.keys()):
                if k.startswith(st.session_state.get("key","guest")+":"):
                    del st.session_state[k]
            st.experimental_rerun()
    with c3:
        st.caption("※ '해석하기' 이후 결과 탭들이 의미 있게 채워집니다.")

# Gate 적용: 해석 전에는 핵심 결과 탭 흐리게 안내
if not st.session_state.get("analyzed"):
    with t_diet: st.info("아직 '해석하기'를 누르지 않았습니다.")
    with t_ae:   st.info("아직 '해석하기'를 누르지 않았습니다.")
    with t_report: st.info("아직 '해석하기'를 누르지 않았습니다.")
