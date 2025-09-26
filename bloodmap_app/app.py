
# app.py — Bloodmap (Enhanced v6 patch)
import os
import datetime as _dt
import streamlit as st

# -------- Safe banner (no-op if missing) --------
try:
    from branding import render_deploy_banner
except Exception:
    def render_deploy_banner(*a, **k): return None

# Oncology maps / drug DB / AE UI
try:
    from onco_map import build_onco_map, dx_display, auto_recs_by_dx
except Exception:
    build_onco_map = lambda: {}
    dx_display = lambda g,d: f"{g} - {d}"
    def auto_recs_by_dx(*args, **kwargs): return {"chemo": [], "targeted": [], "abx": []}

try:
    from drug_db import DRUG_DB, ensure_onco_drug_db, display_label, key_from_label
except Exception:
    DRUG_DB = {}
    def ensure_onco_drug_db(db): pass
    def display_label(k, db=None): return str(k)
    def key_from_label(s, db=None): return str(s).split(" (")[0]

try:
    from ui_results import collect_top_ae_alerts
except Exception:
    def collect_top_ae_alerts(*a, **k): return []

try:
    from lab_diet import lab_diet_guides
except Exception:
    def lab_diet_guides(labs, heme_flag=False): return []

try:
    from peds_dose import acetaminophen_ml, ibuprofen_ml
except Exception:
    def acetaminophen_ml(*a, **k): return (0.0, 0.0)
    def ibuprofen_ml(*a, **k): return (0.0, 0.0)

try:
    from peds_profiles import get_symptom_options
except Exception:
    def get_symptom_options(d):
        return {"콧물":["없음","투명"],"기침":["없음","조금"],"설사":["없음","1~2회"],"발열":["없음","37~37.5 (미열)"],"눈꼽":["없음"]}

# -------- Page config --------
st.set_page_config(page_title="Bloodmap", layout="wide")
st.title("Bloodmap")
render_deploy_banner("https://bloodmap.streamlit.app/", "제작: Hoya/GPT · 자문: Hoya/GPT")
st.caption("※ 모든 날짜/시간/스케줄 표기는 한국시간(Asia/Seoul) 기준입니다. 세포·면역치료는 표기하지 않습니다.")

# -------- Globals --------
ensure_onco_drug_db(DRUG_DB)  # DRUG_DB 채우기
ONCO = build_onco_map()

def wkey(name:str)->str:
    who = st.session_state.get("key","guest")
    return f"{who}:{name}"

# ====== Sidebar: 프로필 & 오늘 체온/응급도 빠른 입력 ======
with st.sidebar:
    st.header("프로필")
    st.session_state["key"] = st.text_input("별명#PIN", value=st.session_state.get("key","guest"), key=wkey("user_key"))
    st.caption("좌측 프로필은 저장/CSV 경로 키로 쓰입니다.")
    temp = st.number_input("현재 체온(℃)", 34.0, 42.5, 36.8, 0.1, key=wkey("cur_temp"))
    hr   = st.number_input("심박수(bpm)", 0, 250, 0, 1, key=wkey("cur_hr"))
    sbp  = st.number_input("수축혈압(mmHg)", 0, 280, 0, 1, key=wkey("cur_sbp"))

# ====== Helpers ======
def egfr_2009(cr_mgdl:float, age:int, sex:str):
    sex_f = (sex=="여"); k = 0.7 if sex_f else 0.9; a = -0.329 if sex_f else -0.411
    mn = min(cr_mgdl/k,1); mx = max(cr_mgdl/k,1); sex_fac = 1.018 if sex_f else 1.0
    return round(141*(mn**a)*(mx**-1.209)*(0.993**age)*sex_fac,1)

def anc_band(anc: float) -> str:
    if anc is None:
        return "(미입력)"
    try:
        anc = float(anc)
    except Exception:
        return "(값 오류)"
    if anc < 500: return "🚨 중증 호중구감소(<500)"
    if anc < 1000: return "🟧 중등도 호중구감소(500~999)"
    if anc < 1500: return "🟡 경도 호중구감소(1000~1499)"
    return "🟢 정상(≥1500)"

def emergency_level(labs: dict, temp_c: float, hr:int, sbp:int) -> tuple[str, list[str]]:
    # 규칙 기반 응급도
    anc = labs.get("ANC")
    plt = labs.get("PLT")
    crp = labs.get("CRP")
    hb  = labs.get("Hb")
    alerts = []

    try: t = float(temp_c)
    except: t = 0.0
    try: a = float(anc) if anc is not None else None
    except: a = None
    try: p = float(plt) if plt is not None else None
    except: p = None
    try: c = float(crp) if crp is not None else None
    except: c = None
    try: h = float(hb) if hb is not None else None
    except: h = None

    risk = 0
    if a is not None and a < 500:
        risk += 3; alerts.append("ANC<500: 발열 시 응급(FN)")
    elif a is not None and a < 1000:
        risk += 2; alerts.append("ANC 500~999: 감염 주의")

    if t >= 38.5:
        risk += 2; alerts.append("고열(≥38.5℃)")
    elif t >= 38.0:
        risk += 1; alerts.append("발열(38.0~38.4℃)")

    if p is not None and p < 20000:
        risk += 2; alerts.append("혈소판 <20k: 출혈 위험")
    if h is not None and h < 7.0:
        risk += 1; alerts.append("중증 빈혈(Hb<7)")
    if c is not None and c >= 10:
        risk += 1; alerts.append("CRP 높음(≥10)")

    if sbp and sbp < 90:
        risk += 2; alerts.append("저혈압")
    if hr and hr > 130:
        risk += 1; alerts.append("빈맥")

    if risk >= 4: return "🚨 응급", alerts
    if risk >= 2: return "🟧 주의", alerts
    return "🟢 안심", alerts

# ====== Tabs ======
t_home, t_labs, t_dx, t_chemo, t_peds, t_special, t_report = st.tabs(
    ["🏠 홈","🧪 피수치 입력","🧬 암 선택","💊 항암제","👶 소아 증상","🔬 특수검사","📄 보고서"]
)

# ====== HOME: 응급도 상시 표시 ======
with t_home:
    st.subheader("응급도(실시간)")
    labs = st.session_state.get("labs_dict", {})
    level, reasons = emergency_level(labs, st.session_state.get(wkey("cur_temp")), st.session_state.get(wkey("cur_hr")), st.session_state.get(wkey("cur_sbp")))
    if level.startswith("🚨"):
        st.error(level + " — " + " · ".join(reasons))
    elif level.startswith("🟧"):
        st.warning(level + " — " + " · ".join(reasons))
    else:
        st.info(level + (" — " + " · ".join(reasons) if reasons else ""))
    # Top AE alerts from current chemo list
    meds = st.session_state.get("chemo_keys", [])
    if meds:
        st.markdown("**선택된 약물 응급 경고(Top)**")
        top_alerts = collect_top_ae_alerts(meds, DRUG_DB)
        for a in (top_alerts or []):
            st.error(a)

# ====== LABS: Full inputs + eGFR + Diet guide ======
with t_labs:
    st.subheader("피수치 입력")
    # row 1: identity
    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: sex = st.selectbox("성별", ["여","남"], key=wkey("sex"))
    with c2: age = st.number_input("나이(세)", 1, 110, 40, key=wkey("age"))
    with c3: wt  = st.number_input("체중(kg)", 0.0, 300.0, 0.0, 0.5, key=wkey("wt"))
    with c4: cr  = st.number_input("Cr (mg/dL)", 0.0, 20.0, 0.8, 0.1, key=wkey("cr"))
    with c5: day = st.date_input("측정일", value=_dt.date.today(), key=wkey("date"))

    egfr = egfr_2009(cr, int(age), sex)
    st.metric("eGFR (CKD-EPI 2009)", f"{egfr} mL/min/1.73㎡")

    # row 2: 핵심 CBC/염증
    r1 = st.columns(6)
    with r1[0]: WBC = st.number_input("WBC (×10⁹/L)", 0.0, 300.0, 0.0, 0.1, key=wkey("WBC"))
    with r1[1]: ANC = st.number_input("ANC (절대호중구, /µL)", 0.0, 20000.0, 0.0, 100.0, key=wkey("ANC"))
    with r1[2]: Hb  = st.number_input("Hb (g/dL)", 0.0, 25.0, 0.0, 0.1, key=wkey("Hb"))
    with r1[3]: PLT = st.number_input("PLT (×10³/µL)", 0.0, 1000.0, 0.0, 1.0, key=wkey("PLT"))
    with r1[4]: CRP = st.number_input("CRP (mg/L)", 0.0, 500.0, 0.0, 0.5, key=wkey("CRP"))
    with r1[5]: Glu = st.number_input("Glucose (mg/dL)", 0.0, 1000.0, 0.0, 1.0, key=wkey("Glu"))

    # row 3: 전해질/간/요산/알부민/칼슘
    r2 = st.columns(6)
    with r2[0]: Na  = st.number_input("Na (mmol/L)", 0.0, 200.0, 0.0, 0.5, key=wkey("Na"))
    with r2[1]: K   = st.number_input("K (mmol/L)", 0.0, 10.0, 0.0, 0.1, key=wkey("K"))
    with r2[2]: Alb = st.number_input("Albumin (g/dL)", 0.0, 6.0, 0.0, 0.1, key=wkey("Alb"))
    with r2[3]: Ca  = st.number_input("Calcium (mg/dL)", 0.0, 20.0, 0.0, 0.1, key=wkey("Ca"))
    with r2[4]: AST = st.number_input("AST (U/L)", 0.0, 2000.0, 0.0, 1.0, key=wkey("AST"))
    with r2[5]: ALT = st.number_input("ALT (U/L)", 0.0, 2000.0, 0.0, 1.0, key=wkey("ALT"))
    UA = st.number_input("Uric Acid (mg/dL)", 0.0, 30.0, 0.0, 0.1, key=wkey("UA"))

    # Save labs in session
    labs_dict = {
        "sex": sex, "age": int(age), "weight": wt, "date": str(day),
        "Cr": cr, "eGFR": egfr, "WBC": WBC, "ANC": ANC, "Hb": Hb, "PLT": PLT,
        "CRP": CRP, "Glu": Glu, "Na": Na, "K": K, "Alb": Alb, "Ca": Ca, "AST": AST, "ALT": ALT, "UA": UA
    }
    st.session_state["labs_dict"] = labs_dict

    # ANC 세분화 배지
    st.markdown(f"**ANC 분류:** {anc_band(ANC)}")

    # 식이가이드 (전체 출력, heme_flag는 선택된 그룹이 혈액암일 때)
    current_group = st.session_state.get("onco_group", "")
    heme_flag = True if current_group == "혈액암" else False
    diets = lab_diet_guides(labs_dict, heme_flag=heme_flag)
    if diets:
        st.markdown("### 🍚 식이가이드(자동)")
        for line in diets:
            st.write("- " + line)

# ====== DX: 온코 그룹/암종 전체 맵 ======
with t_dx:
    st.subheader("암 선택")
    groups = list(ONCO.keys())
    if not groups:
        st.info("진단 맵을 불러오지 못했습니다.")
    else:
        grp_tabs = st.tabs(groups)
        for i, g in enumerate(groups):
            with grp_tabs[i]:
                dx_names = list((ONCO.get(g) or {}).keys())
                if not dx_names:
                    st.caption("항목 없음")
                    continue
                disp = [dx_display(g, d) for d in dx_names]
                sel = st.selectbox("진단명을 선택하세요", disp, key=wkey(f"dx_sel_{i}"))
                if st.button("선택 저장", key=wkey(f"dx_save_{i}")):
                    idx = disp.index(sel)
                    picked = dx_names[idx]
                    st.session_state["dx_raw"] = picked
                    st.session_state["dx_disp"] = sel
                    st.session_state["onco_group"] = g
                    st.success(f"저장됨: {sel}")

# ====== CHEMO: 진단 기반 자동 추천 + 사용자 추가 ======
with t_chemo:
    st.subheader("항암제")
    dx = st.session_state.get("dx_raw")
    g  = st.session_state.get("onco_group")
    if not dx or not g:
        st.info("먼저 '암 선택'에서 저장하세요.")
    else:
        st.write(f"현재 진단: **{st.session_state.get('dx_disp','')}**")
        recs = auto_recs_by_dx(g, dx, DRUG_DB, ONCO)
        base_list = recs.get("chemo", []) + recs.get("targeted", []) + recs.get("abx", [])
        base_list = [k for k in base_list if k]
        options = [display_label(k, DRUG_DB) for k in base_list]
        default = options
        picked_labels = st.multiselect("항암제를 선택/추가", options, default=default, key=wkey("chemo_ms"))
        extra = st.text_input("추가 항암제(쉼표 구분, 예: Vancomycin, Cefepime)", key=wkey("chemo_extra"))
        picked_keys = [key_from_label(lbl, DRUG_DB) for lbl in picked_labels]
        if extra.strip():
            more = [key_from_label(x.strip(), DRUG_DB) for x in extra.split(",") if x.strip()]
            for x in more:
                if x and x not in picked_keys:
                    picked_keys.append(x)
        if st.button("항암제 저장", key=wkey("chemo_save")):
            st.session_state["chemo_keys"] = picked_keys
            st.success("저장됨. 홈/보고서에서 확인")

# ====== PEDS: 소아 증상 세분화 ======
with t_peds:
    st.subheader("소아 증상 분류(간단)")
    disease = st.selectbox("의심 질환(선택 시 기본 옵션 자동 세팅)", ["장염","로타","노로","RSV","독감","상기도염","아데노","마이코","수족구","편도염","코로나","중이염"], key=wkey("peds_dx"))
    opts = get_symptom_options(disease)
    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: nasal = st.selectbox("콧물", opts.get("콧물", ["없음","투명"]), key=wkey("p_nasal"))
    with c2: cough = st.selectbox("기침", opts.get("기침", ["없음","조금"]), key=wkey("p_cough"))
    with c3: stool = st.selectbox("설사", opts.get("설사", ["없음","1~2회","3~4회"]), key=wkey("p_stool"))
    with c4: fever = st.selectbox("발열", opts.get("발열", ["없음","37~37.5 (미열)","37.5~38 (병원 내원 권장)","38.5~39 (병원/응급실)"]), key=wkey("p_fever"))
    with c5: eye   = st.selectbox("눈꼽", opts.get("눈꼽", ["없음","맑음","노랑-농성"]), key=wkey("p_eye"))

    # 간단 규칙: 장염/호흡기/결막염 범주로 Top 메시지
    score = {"장염 의심":0, "상기도/독감 계열":0, "결막염 의심":0}
    if stool in ["3~4회","5~6회"]:
        score["장염 의심"] += 40
    if "38.5" in fever:
        score["상기도/독감 계열"] += 20
    if cough in ["보통","심함","조금"]:
        score["상기도/독감 계열"] += 20
    if eye in ["노랑-농성","한쪽","양쪽"]:
        score["결막염 의심"] += 25
    tips = []
    if score["장염 의심"] >= 40: tips.append("ORS 수분 보충, 탈수 징후 관찰")
    if score["상기도/독감 계열"] >= 20: tips.append("해열 간격 지키기(APAP≥4h, IBU≥6h)")
    if score["결막염 의심"] >= 25: tips.append("눈 위생, 분비물 제거, 병원 상담 고려")
    st.write("• " + " / ".join([f"{k}: {v}" for k,v in score.items()]))
    if tips:
        st.info(" / ".join(tips))

# ====== SPECIAL: 기존 모듈 그대로 사용(있으면) ======
with t_special:
    try:
        from special_tests import special_tests_ui
        lines = special_tests_ui()
        if lines:
            st.markdown("**특수검사 해석**")
            for ln in lines:
                st.write("- " + ln)
    except Exception:
        st.caption("특수검사 모듈을 불러오지 못했습니다.")

# ====== REPORT ======
with t_report:
    st.subheader("보고서 (.md)")
    dx_disp = st.session_state.get("dx_disp","(미선택)")
    meds = st.session_state.get("chemo_keys", [])
    labs = st.session_state.get("labs_dict", {})
    diets = lab_diet_guides(labs, heme_flag=(st.session_state.get("onco_group","")=="혈액암"))
    ae_top = collect_top_ae_alerts(meds, DRUG_DB)

    lines = []
    lines.append("# Bloodmap Report")
    lines.append(f"**진단명**: {dx_disp}")
    lines.append("")
    lines.append("## 항암제 요약")
    if meds:
        for m in meds: lines.append(f"- {display_label(m, DRUG_DB)}")
    else:
        lines.append("- (없음)")
    if labs:
        lines.append("")
        lines.append("## 주요 수치")
        keys = ["date","WBC","ANC","Hb","PLT","CRP","Na","K","Alb","Ca","AST","ALT","Glu","UA","Cr","eGFR"]
        for k in keys:
            if k in labs and labs.get(k) not in [None, "", 0]:
                lines.append(f"- {k}: {labs.get(k)}")
        lines.append(f"- ANC 분류: {anc_band(labs.get('ANC'))}")
    if diets:
        lines.append("")
        lines.append("## 식이가이드")
        for d in diets: lines.append(f"- {d}")
    if ae_top:
        lines.append("")
        lines.append("## 약물 경고(Top)")
        for a in ae_top: lines.append(f"- {a}")
    lines.append("")
    lines.append(f"_생성 시각(KST): {_dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_")
    md = "\n".join(lines)
    st.code(md, language="markdown")
    st.download_button("💾 보고서 .md 다운로드", data=md.encode("utf-8"),
                    file_name="bloodmap_report.md", mime="text/markdown", key=wkey("dl_md"))
