# -*- coding: utf-8 -*-
"""
BloodMap — 복원 패치 v3.3 (암 분류 고정/증상입력 추가/임포트 보강)
- 암 분류: 혈액암/림프종/육종/고형암/희귀암 순서로 고정(빼먹지 않음)
- 증상입력 탭 추가: 소아/성인 모드, 기본 증상 체크, triage 요약(폴백 포함)
- 이전 개선 유지: pandas/ANC-addon 안전 임포트, 날짜 내림차순 정렬, 소아 eGFR(슈바르츠)/성인(CKD‑EPI 2009)
"""
import os, json, csv, datetime as _dt
import streamlit as st

# ---------------- Safe imports ----------------
# Branding
try:
    from branding import render_deploy_banner
except Exception:
    def render_deploy_banner(*a, **k): 
        st.caption("🔗 BloodMap — 한국시간 기준 / 세포·면역 치료 비표기 / 제작·자문: Hoya/GPT")

# PDF export
try:
    from pdf_export import export_md_to_pdf
except Exception:
    def export_md_to_pdf(md:str) -> bytes:
        return (md or '').encode('utf-8')

# Core utils
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

# Diet
try:
    from lab_diet import lab_diet_guides
except Exception:
    def lab_diet_guides(labs, heme_flag=False):
        return []

# ANC addon (optional)
try:
    from anc_diet_addon import lab_diet_guides_anc_addon
except Exception:
    def lab_diet_guides_anc_addon(labs):
        return []

# Special tests
try:
    from special_tests import special_tests_ui
except Exception:
    def special_tests_ui(): 
        st.caption("특수검사 모듈 누락")
        return []

# Pediatrics dose (optional)
try:
    from peds_dose import acetaminophen_ml, ibuprofen_ml, estimate_weight_from_age_months
except Exception:
    def acetaminophen_ml(*a, **k): return (0.0, 0.0)
    def ibuprofen_ml(*a, **k): return (0.0, 0.0)
    def estimate_weight_from_age_months(m): return 0.0

# Adult rules (optional triage)
try:
    from adult_rules import get_adult_options, triage_advise
except Exception:
    def get_adult_options(): return {}
    def triage_advise(*a, **k): return ""

# Onco map / labels
try:
    from onco_map import build_onco_map, auto_recs_by_dx, dx_display
except Exception:
    def build_onco_map(): return {}
    def auto_recs_by_dx(group, dx, DRUG_DB=None, ONCO_MAP=None): return {"chemo":[],"targeted":[],"abx":[]}
    def dx_display(group, dx): return f"{group} - {dx}"

# Drug DB (robust label wrapper)
try:
    import drug_db as _drugdb
    DRUG_DB = getattr(_drugdb, "DRUG_DB", {})
    if hasattr(_drugdb, "ensure_onco_drug_db"):
        _drugdb.ensure_onco_drug_db(DRUG_DB)
    def _label(k: str) -> str:
        try:
            return _drugdb.display_label(k, DRUG_DB)
        except TypeError:
            try:
                return _drugdb.display_label(k)
            except Exception:
                return str(k)
except Exception:
    DRUG_DB = {}
    def _label(k:str)->str: return str(k)

# AE UI
try:
    from ui_results import render_adverse_effects, collect_top_ae_alerts
except Exception:
    def render_adverse_effects(st_module, drug_keys, db): 
        if drug_keys: st_module.write(", ".join(drug_keys))
    def collect_top_ae_alerts(drug_keys, db=None): 
        return []

# Pandas with safe fallback
try:
    import pandas as pd  # optional but preferred
except Exception:
    pd = None

# ---------------- Page meta & CSS ----------------
st.set_page_config(page_title="BloodMap — 복원 패치 v3.3", layout="wide")
st.title("BloodMap (암 분류/증상입력/정렬/소아 eGFR 패치)")
render_deploy_banner("https://bloodmap.streamlit.app/", "제작: Hoya/GPT · 자문: Hoya/GPT")

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

def _save_labs_csv(rows:list):
    """별명#PIN 기반 CSV 저장. pandas 없으면 csv 모듈로 대체."""
    try:
        uid = st.session_state.get("key","guest").replace("/", "_")
        base = "/mnt/data/bloodmap_graph"
        os.makedirs(base, exist_ok=True)
        path = os.path.join(base, f"{uid}.labs.csv")
        if pd is not None:
            df = pd.DataFrame(rows)
            df.to_csv(path, index=False, encoding="utf-8")
        else:
            if not rows:
                return path
            # write with csv module
            keys = list({k for r in rows for k in r.keys()})
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=keys)
                w.writeheader()
                for r in rows:
                    w.writerow(r)
        return path
    except Exception as e:
        st.warning(f"CSV 저장 실패: {e}")
        return ""

# ---------------- Sidebar ----------------
with st.sidebar:
    st.header("프로필 / 스케줄")
    nickname_pin()
    schedule_block()
    st.caption("※ 좌측 프로필은 저장/CSV 경로 키로 쓰입니다.")

# ---------------- Tabs ----------------
T = st.tabs(["🏠 홈","🧪 피수치 입력","🧬 암/진단","💊 항암제","🔬 특수검사","🍽️ 식이가이드","🩺 증상입력","⚠️ 부작용 경고","📄 보고서"]
)
t_home, t_labs, t_dx, t_chemo, t_special, t_diet, t_symp, t_ae, t_report = T

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

    # eGFR: 성인 CKD‑EPI(2009), 소아 Schwartz(키 필요)
    def egfr_ckd_epi_2009(cr_mgdl:float, age:int, sex:str):
        sex_f = (sex=="여"); k = 0.7 if sex_f else 0.9; a = -0.329 if sex_f else -0.411
        mn = min(cr_mgdl/k,1); mx = max(cr_mgdl/k,1); sex_fac = 1.018 if sex_f else 1.0
        return round(141*(mn**a)*(mx**-1.209)*(0.993**age)*sex_fac,1)
    def egfr_schwartz(cr_mgdl:float, height_cm:float):
        if (cr_mgdl or 0) <= 0 or (height_cm or 0) <= 0:
            return None
        return round(0.413 * (height_cm) / cr_mgdl, 1)

    pediatric = (int(age) < 18)
    height_cm = None
    if pediatric:
        height_cm = st.number_input("키 (cm) — 소아 eGFR(슈바르츠) 계산용", 30.0, 220.0, 120.0, 0.5, key=wkey("height_cm"))
        egfr = egfr_schwartz(cr, height_cm)
        mode_badge = "소아(슈바르츠)"
        if egfr is None:
            st.caption("소아 eGFR 계산에는 **키(cm)**와 **Cr**가 필요합니다. 값이 없으면 eGFR 표시를 보류합니다.")
    else:
        egfr = egfr_ckd_epi_2009(cr, int(age), sex)
        mode_badge = "성인(CKD‑EPI 2009)"

    if egfr is not None:
        st.metric(f"eGFR — {mode_badge}", f"{egfr} mL/min/1.73㎡")
    else:
        st.metric(f"eGFR — {mode_badge}", "계산 보류")

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

    st.session_state.setdefault("lab_rows", [])
    if st.button("➕ 현재 값 추가", key=wkey("add_row")):
        row = {"date":str(day),"mode":("소아" if pediatric else "성인"),
               "sex":sex,"age":int(age),"height_cm":height_cm if pediatric else "",
               "weight(kg)":wt,"Cr":cr,"eGFR":(egfr if egfr is not None else ""),
               "Alb":alb,"K":k,"Hb":hb,"Na":na,"Ca":ca,"Glu":glu,"AST":ast,"ALT":alt,"UA":ua,"CRP":crp,"ANC":anc,"PLT":plt}
        st.session_state["lab_rows"].append(row)
        path = _save_labs_csv(st.session_state["lab_rows"])
        if path: st.success(f"저장됨 → {path}")

    rows = st.session_state["lab_rows"]
    if rows:
        rows_sorted = sorted(rows, key=lambda r: r.get("date",""), reverse=True)
        st.write("최근 입력(최대 5개, **날짜 내림차순**):")
        head = ["date","mode","sex","age","height_cm","weight(kg)","Cr","eGFR","Alb","K","Hb","Na","Ca","Glu","AST","ALT","UA","CRP","ANC","PLT"]
        if pd is not None:
            df = pd.DataFrame(rows_sorted)[head].head(5)
            st.dataframe(df, use_container_width=True)
        else:
            st.table([{k: r.get(k, "") for k in head} for r in rows_sorted[:5]])

# ---------------- 암/진단 ----------------
with t_dx:
    st.subheader("암/진단 선택 (그룹 → 진단명, 한글 병기)")
    ONCO = build_onco_map()
    desired_groups = ["혈액암","림프종","육종","고형암","희귀암"]
    if ONCO:
        groups = [g for g in desired_groups if g in ONCO] + [g for g in ONCO.keys() if g not in desired_groups]
    else:
        groups = desired_groups
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
    grp = st.session_state.get("dx_group","");
    dx  = st.session_state.get("dx_name","");
    st.caption(f"현재 진단: {dx_display(grp or '(미선택)', dx or '(미선택)')}")
    recs = auto_recs_by_dx(grp, dx, DRUG_DB=DRUG_DB, ONCO_MAP=build_onco_map())
    suggestions = []
    for cat in ("chemo","targeted","abx"):
        for k in recs.get(cat, []):
            lab = _label(k)
            if lab not in suggestions:
                suggestions.append(lab)
    suggestions = sorted(suggestions, key=lambda s: s.lower())
    picked = st.multiselect("항암제를 선택/추가", suggestions, default=suggestions, key=wkey("chemo_ms"))
    extra = st.text_input("추가 항암제(쉼표 구분)", key=wkey("chemo_extra"))
    if extra.strip():
        more = [x.strip() for x in extra.split(",") if x.strip()]
        for x in more:
            if x not in picked: picked.append(x)
    if st.button("항암제 저장", key=wkey("chemo_save")):
        keys = []
        for lab in picked:
            pos = lab.find(" (")
            k = lab[:pos] if pos>0 else lab
            k = k.strip().strip("'").strip('"')
            keys.append(k)
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
    guides = lab_diet_guides(labs, heme_flag=heme_flag) or []
    guides_extra = lab_diet_guides_anc_addon(labs) or []
    guides = guides + guides_extra
    if guides:
        for g in guides: st.write("- " + g)
    else:
        st.caption("권장 식이가이드가 표시될 조건이 없습니다.")

# ---------------- 증상입력 ----------------
with t_symp:
    st.subheader("증상 입력(소아/성인) + Triage 요약")
    # 연령군: 자동/소아/성인
    inferred_group = "소아" if int(st.session_state.get(wkey("age"), 40)) < 18 else "성인"
    age_mode = st.radio("연령군", ["자동","소아","성인"], index=0, horizontal=True, key=wkey("age_mode"))
    age_group = inferred_group if age_mode == "자동" else age_mode

    # 기본 증상 필드
    c1,c2,c3,c4 = st.columns(4)
    with c1: temp = st.number_input("체온(℃)", 34.0, 42.5, 36.8, 0.1, key=wkey("sym_temp"))
    with c2: days = st.number_input("증상 기간(일)", 0, 60, 0, key=wkey("sym_days"))
    with c3: pain = st.slider("통증(0~10)", 0, 10, 0, key=wkey("sym_pain"))
    with c4: bleeding = st.checkbox("출혈/멍 쉽게 생김", key=wkey("sym_bleed"))

    d1,d2,d3,d4 = st.columns(4)
    with d1: dysp = st.checkbox("호흡곤란", key=wkey("sym_dysp"))
    with d2: chest = st.checkbox("흉통", key=wkey("sym_chest"))
    with d3: conf = st.checkbox("혼동/의식저하", key=wkey("sym_conf"))
    with d4: rash = st.checkbox("발진", key=wkey("sym_rash"))

    gi1,gi2 = st.columns(2)
    with gi1: vomit = st.checkbox("구토", key=wkey("sym_vomit"))
    with gi2: diarrhea = st.checkbox("설사", key=wkey("sym_diarrhea"))

    detail = st.text_area("자유기술(선택)", key=wkey("sym_note"))

    # 간단 규칙 기반 응급 플래그 (폴백)
    alerts = []
    if temp >= 38.0 and (st.session_state.get(wkey("anc")) or 0) < 500:
        alerts.append("🚨 발열 + ANC<500 → **호중구감소성 발열 의심: 즉시 내원/응급 연락**")
    if dysp or chest or conf:
        alerts.append("🚨 호흡곤란/흉통/의식변화 → **즉시 응급평가 권고**")
    if bleeding and (st.session_state.get(wkey("plt")) or 0) < 50:
        alerts.append("⚠️ 출혈 + PLT 낮음 → **출혈 위험, 병원 연락**")
    if pain >= 7:
        alerts.append("⚠️ 통증 7/10 이상 → **진통/평가 필요**")

    # adult_rules.triage_advise가 있으면 호출
    triage = ""
    try:
        triage = triage_advise(
            symptoms={
                "temp": float(temp), "days": int(days), "pain": int(pain),
                "bleeding": bool(bleeding), "dyspnea": bool(dysp), "chest_pain": bool(chest),
                "confusion": bool(conf), "rash": bool(rash), "vomit": bool(vomit), "diarrhea": bool(diarrhea),
                "detail": detail,
            },
            age_group=age_group,
            onc_group=st.session_state.get("dx_group",""),
        ) or ""
    except Exception:
        triage = ""

    # 출력
    if alerts:
        st.error("\n".join(alerts))
    if triage:
        st.info(triage)

    # 저장
    if st.button("증상 기록 저장", key=wkey("sym_save")):
        st.session_state["symptom_summary"] = { 
            "age_group": age_group, "temp": temp, "days": days, "pain": pain,
            "bleeding": bleeding, "dyspnea": dysp, "chest_pain": chest, "confusion": conf,
            "rash": rash, "vomit": vomit, "diarrhea": diarrhea, "detail": detail,
            "alerts": alerts, "triage": triage,
        }
        st.success("증상 기록 저장됨. 보고서에 포함됩니다.")

# ---------------- 부작용 경고 ----------------
with t_ae:
    st.subheader("약물 부작용 경고(색상 박스 + 본문)")
    keys = st.session_state.get("chemo_keys", [])
    if not keys:
        st.info("먼저 항암제를 저장하세요.")
    else:
        tops = collect_top_ae_alerts(keys, db=DRUG_DB)
        if tops:
            st.error(" / ".join(tops))
        render_adverse_effects(st, keys, DRUG_DB)

# ---------------- 보고서 ----------------
with t_report:
    st.subheader("보고서 (.md / .pdf)")
    grp = st.session_state.get("dx_group","");
    dx  = st.session_state.get("dx_name","");
    keys = st.session_state.get("chemo_keys", []);
    rows = st.session_state.get("lab_rows", []);
    spec_lines = st.session_state.get("special_lines", []);
    sym = st.session_state.get("symptom_summary", {})

    lines = []
    lines.append("# BloodMap Report")
    lines.append(f"**진단명**: {dx_display(grp or '(미선택)', dx or '(미선택)')}")
    lines.append("")
    lines.append("## 항암제 요약")
    if keys:
        for k in keys:
            lines.append(f"- {_label(k)}")
    else:
        lines.append("- (없음)")
    if rows:
        lines.append("")
        lines.append("## 최근 검사 (최대 5개, 날짜 내림차순)")
        head = ["date","mode","sex","age","height_cm","weight(kg)","Cr","eGFR","Alb","K","Hb","Na","Ca","Glu","AST","ALT","UA","CRP","ANC","PLT"]
        lines.append("| " + " | ".join(head) + " |")
        lines.append("|" + "|".join(["---"]*len(head)) + "|")
        rows_sorted = sorted(rows, key=lambda r: r.get("date",""), reverse=True)
        for r in rows_sorted[:5]:
            lines.append("| " + " | ".join(str(r.get(k,'')) for k in head) + " |")
    if spec_lines:
        lines.append("")
        lines.append("## 특수검사")
        for s in spec_lines:
            lines.append(f"- {s}")
    # 식이가이드
    latest = rows[-1] if rows else {}
    labs = {k: latest.get(k) for k in ["Alb","K","Hb","Na","Ca","Glu","AST","ALT","Cr","BUN","UA","CRP","ANC","PLT"]}
    heme_flag = (grp == "혈액암")
    guides = (lab_diet_guides(labs, heme_flag=heme_flag) or []) + (lab_diet_guides_anc_addon(labs) or [])
    if guides:
        lines.append("")
        lines.append("## 식이가이드")
        for g in guides: lines.append(f"- {g}")
    # 증상/triage
    if sym:
        lines.append("")
        lines.append("## 증상 및 Triage 요약")
        lines.append(f"- 연령군: {sym.get('age_group','-')}")
        lines.append(f"- 체온: {sym.get('temp','-')} ℃ / 기간: {sym.get('days','-')}일 / 통증: {sym.get('pain','-')}/10")
        flags = [k for k,v in [ ('출혈',sym.get('bleeding')),('호흡곤란',sym.get('dyspnea')),('흉통',sym.get('chest_pain')),('의식저하',sym.get('confusion')),('발진',sym.get('rash')),('구토',sym.get('vomit')),('설사',sym.get('diarrhea')) ] if v]
        if flags:
            lines.append("- 동반증상: " + ", ".join(flags))
        if sym.get('detail'):
            lines.append("- 메모: " + sym['detail'].replace("\n"," ").strip())
        if sym.get('alerts'):
            lines.append("- ⚠️ 경고: " + " / ".join(sym['alerts']))
        if sym.get('triage'):
            lines.append("- Triage: " + sym['triage'])

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

# ---------------- 해석하기 게이트 ----------------
with st.container():
    c1, c2, c3 = st.columns([1,1,6])
    with c1:
        if st.button("🔍 해석하기", key=wkey("analyze")):
            st.session_state["analyzed"] = True
            st.toast("해석 완료. '식이가이드/증상/부작용/보고서' 탭에서 결과 확인!", icon="✅")
    with c2:
        if st.button("♻️ 초기화", key=wkey("reset")):
            for k in list(st.session_state.keys()):
                if k.startswith(st.session_state.get("key","guest")+":"):
                    del st.session_state[k]
            st.experimental_rerun()
    with c3:
        st.caption("※ '해석하기' 이후 결과 탭들이 의미 있게 채워집니다.")

if not st.session_state.get("analyzed"):
    with t_diet: st.info("아직 '해석하기'를 누르지 않았습니다.")
    with t_symp: st.info("아직 '해석하기'를 누르지 않았습니다.")
    with t_ae:   st.info("아직 '해석하기'를 누르지 않았습니다.")
    with t_report: st.info("아직 '해석하기'를 누르지 않았습니다.")
