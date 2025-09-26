
# app.py — Bloodmap (v6.3: PEDS symptom scoring + antipyretic dosing)
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

# ====== UI helpers ======
def wkey(name:str)->str:
    who = st.session_state.get("key","guest")
    return f"{who}:{name}"

def _parse_float(txt):
    if txt is None: return None
    s = str(txt).strip().replace(",", "")
    if s == "": return None
    try:
        return float(s)
    except Exception:
        return None

# ====== Helpers ======
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

def emergency_level(labs: dict, temp_c, hr, symptoms: dict) -> tuple[str, list[str]]:
    # 증상 기반(혈압 제거, 수치 미입력 시 영향 없음)
    anc = labs.get("ANC")
    plt = labs.get("PLT")
    crp = labs.get("CRP")
    hb  = labs.get("Hb")
    alerts = []

    t = temp_c if isinstance(temp_c,(int,float)) else _parse_float(temp_c)
    a = anc if isinstance(anc,(int,float)) else _parse_float(anc)
    p = plt if isinstance(plt,(int,float)) else _parse_float(plt)
    c = crp if isinstance(crp,(int,float)) else _parse_float(crp)
    h = hb  if isinstance(hb,(int,float)) else _parse_float(hb)
    heart = hr if isinstance(hr,(int,float)) else _parse_float(hr)

    risk = 0
    if a is not None and a < 500:
        risk += 3; alerts.append("ANC<500: 발열 시 응급(FN)")
    elif a is not None and a < 1000:
        risk += 2; alerts.append("ANC 500~999: 감염 주의")

    if t is not None and t >= 38.5:
        risk += 2; alerts.append("고열(≥38.5℃)")
    elif t is not None and t >= 38.0:
        risk += 1; alerts.append("발열(38.0~38.4℃)")

    if p is not None and p < 20000:
        risk += 2; alerts.append("혈소판 <20k: 출혈 위험")
    if h is not None and h < 7.0:
        risk += 1; alerts.append("중증 빈혈(Hb<7)")
    if c is not None and c >= 10:
        risk += 1; alerts.append("CRP 높음(≥10)")

    if heart and heart > 130:
        risk += 1; alerts.append("빈맥")

    # symptom-driven boosts
    if symptoms.get("hematuria"):
        risk += 1; alerts.append("혈뇨")
    if symptoms.get("melena"):
        risk += 2; alerts.append("흑색변(상부위장관 출혈 의심)")
    if symptoms.get("hematochezia"):
        risk += 2; alerts.append("혈변(하부위장관 출혈 의심)")
    if symptoms.get("chest_pain"):
        risk += 2; alerts.append("흉통")
    if symptoms.get("dyspnea"):
        risk += 2; alerts.append("호흡곤란")
    if symptoms.get("confusion"):
        risk += 3; alerts.append("의식저하/혼돈")
    if symptoms.get("oliguria"):
        risk += 2; alerts.append("소변량 급감(탈수/신장 문제 의심)")
    if symptoms.get("persistent_vomit"):
        risk += 2; alerts.append("지속 구토")
    if symptoms.get("petechiae"):
        risk += 2; alerts.append("점상출혈")

    if risk >= 5: return "🚨 응급", alerts
    if risk >= 2: return "🟧 주의", alerts
    return "🟢 안심", alerts

# ====== Sidebar: 프로필 & 오늘 체온/심박 ======
with st.sidebar:
    st.header("프로필")
    st.session_state["key"] = st.text_input("별명#PIN", value=st.session_state.get("key","guest"), key=wkey("user_key"))
    st.caption("좌측 프로필은 저장/CSV 경로 키로 쓰입니다.")
    temp = st.text_input("현재 체온(℃)", value=st.session_state.get(wkey("cur_temp"), ""), key=wkey("cur_temp"), placeholder="36.8")
    hr   = st.text_input("심박수(bpm)", value=st.session_state.get(wkey("cur_hr"), ""), key=wkey("cur_hr"), placeholder="0")

# ====== Tabs ======
t_home, t_labs, t_dx, t_chemo, t_peds, t_special, t_report = st.tabs(
    ["🏠 홈","🧪 피수치 목록","🧬 암 선택","💊 항암제","👶 소아 증상","🔬 특수검사","📄 보고서"]
)

# ====== HOME ======
with t_home:
    st.subheader("요약")
    labs = st.session_state.get("labs_dict", {})
    level_tmp, reasons_tmp = emergency_level(labs, temp, hr, {})
    if level_tmp.startswith("🚨"):
        st.error("현재 상태: " + level_tmp)
    elif level_tmp.startswith("🟧"):
        st.warning("현재 상태: " + level_tmp)
    else:
        st.info("현재 상태: " + level_tmp)

    st.markdown("---")
    st.subheader("응급도 체크(증상 기반)")
    c1,c2,c3,c4,c5,c6 = st.columns(6)
    with c1: hematuria = st.checkbox("혈뇨", key=wkey("sym_hematuria"))
    with c2: melena = st.checkbox("흑색변", key=wkey("sym_melena"))
    with c3: hematochezia = st.checkbox("혈변", key=wkey("sym_hematochezia"))
    with c4: chest_pain = st.checkbox("흉통", key=wkey("sym_chest"))
    with c5: dyspnea = st.checkbox("호흡곤란", key=wkey("sym_dyspnea"))
    with c6: confusion = st.checkbox("의식저하", key=wkey("sym_confusion"))
    d1,d2,d3 = st.columns(3)
    with d1: oliguria = st.checkbox("소변량 급감", key=wkey("sym_oliguria"))
    with d2: persistent_vomit = st.checkbox("지속 구토", key=wkey("sym_pvomit"))
    with d3: petechiae = st.checkbox("점상출혈", key=wkey("sym_petechiae"))

    sym = dict(hematuria=hematuria, melena=melena, hematochezia=hematochezia,
               chest_pain=chest_pain, dyspnea=dyspnea, confusion=confusion,
               oliguria=oliguria, persistent_vomit=persistent_vomit, petechiae=petechiae)

    level, reasons = emergency_level(labs, temp, hr, sym)
    if level.startswith("🚨"):
        st.error("응급도: " + level + " — " + " · ".join(reasons))
    elif level.startswith("🟧"):
        st.warning("응급도: " + level + " — " + " · ".join(reasons))
    else:
        st.info("응급도: " + level + (" — " + " · ".join(reasons) if reasons else ""))

    # Top AE alerts from current chemo list
    meds = st.session_state.get("chemo_keys", [])
    if meds:
        st.markdown("**선택된 약물 응급 경고(Top)**")
        top_alerts = collect_top_ae_alerts(meds, DRUG_DB)
        for a in (top_alerts or []):
            st.error(a)


# ====== LABS: inputs (requested order, with Korean labels) ======
with t_labs:
    st.subheader("피수치 입력 (요청 순서) — ± 버튼 없이 직접 숫자 입력")
    st.caption("표기 예: 4.5 / 135 / 0.8  (숫자와 소수점만 입력)")

    # helper re-declare (in case)
    def _parse_float(txt):
        if txt is None: return None
        s = str(txt).strip().replace(",", "")
        if s == "": return None
        try:
            return float(s)
        except Exception:
            return None
    def float_input(label:str, key:str, placeholder:str=""):
        val = st.text_input(label, value=str(st.session_state.get(key, "")), key=key, placeholder=placeholder)
        return _parse_float(val)

    order = [
        ("WBC","백혈구"), ("Ca","칼슘"), ("Glu","혈당"), ("CRP","CRP"),
        ("Hb","혈색소"), ("P","인(Phosphorus)"), ("T.P","총단백"), ("Cr","크레아티닌"),
        ("PLT","혈소판"), ("Na","나트륨"), ("AST","AST"), ("T.B","총빌리루빈"),
        ("ANC","절대호중구"), ("Alb","알부민"), ("ALT","ALT"), ("BUN","BUN")
    ]

    # layout: 4 columns grid
    cols = st.columns(4)
    values = {}
    for idx, (abbr, kor) in enumerate(order):
        col = cols[idx % 4]
        with col:
            values[abbr] = float_input(f"{abbr} — {kor}", key=wkey(abbr))

    # Save to session
    labs_dict = st.session_state.get("labs_dict", {})
    for k,v in values.items():
        labs_dict[k] = v
    st.session_state["labs_dict"] = labs_dict

    # ANC badge if available
    st.markdown(f"**ANC 분류:** {{anc_band(values.get('ANC'))}}")

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

# ====== CHEMO ======
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

# ====== PEDS (scoring + antipyretic dosing) ======
with t_peds:
    st.subheader("소아 증상 분류(점수 기반) + 해열제 계산")
    disease = st.selectbox("의심 질환(선택 시 기본 옵션 자동 세팅)", ["장염","로타","노로","RSV","독감","상기도염","아데노","마이코","수족구","편도염","코로나","중이염"], key=wkey("peds_dx"))
    opts = get_symptom_options(disease)
    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: nasal = st.selectbox("콧물", opts.get("콧물", ["없음","투명","진득","누런"]), key=wkey("p_nasal"))
    with c2: cough = st.selectbox("기침", opts.get("기침", ["없음","조금","보통","심함"]), key=wkey("p_cough"))
    with c3: stool = st.selectbox("설사", opts.get("설사", ["없음","1~2회","3~4회","5~6회","7회 이상"]), key=wkey("p_stool"))
    with c4: fever = st.selectbox("발열", opts.get("발열", ["없음","37~37.5 (미열)","37.5~38","38~38.5","38.5~39","39 이상"]), key=wkey("p_fever"))
    with c5: eye   = st.selectbox("눈꼽", opts.get("눈꼽", ["없음","맑음","노랑-농성","양쪽"]), key=wkey("p_eye"))

    d1,d2,d3 = st.columns(3)
    with d1: oliguria = st.checkbox("소변량 급감", key=wkey("p_oliguria"))
    with d2: persistent_vomit = st.checkbox("지속 구토(>6시간)", key=wkey("p_pvomit"))
    with d3: petechiae = st.checkbox("점상출혈", key=wkey("p_petechiae"))

    # Scoring
    score = {"장염 의심":0, "상기도/독감 계열":0, "결막염 의심":0, "탈수/신장 문제":0, "출혈성 경향":0}
    if stool in ["3~4회","5~6회","7회 이상"]:
        score["장염 의심"] += {"3~4회":40,"5~6회":55,"7회 이상":70}[stool]
    if "38.5" in fever or "39" in fever:
        score["상기도/독감 계열"] += 25
    if cough in ["보통","심함","조금"]:
        score["상기도/독감 계열"] += 20
    if eye in ["노랑-농성","양쪽"]:
        score["결막염 의심"] += 30
    if oliguria:
        score["탈수/신장 문제"] += 40
        score["장염 의심"] += 10  # 동반 가중치
    if persistent_vomit:
        score["장염 의심"] += 25
        score["탈수/신장 문제"] += 15
    if petechiae:
        score["출혈성 경향"] += 60

    # Sort and display
    ordered = sorted(score.items(), key=lambda x: x[1], reverse=True)
    st.write("• " + " / ".join([f"{k}: {v}" for k,v in ordered]))
    top = ordered[0][0] if ordered else "(없음)"
    advice = []
    if top == "장염 의심":
        advice.append("ORS로 수분 보충, 소변량 관찰")
    if top == "상기도/독감 계열":
        advice.append("해열제 간격 준수(APAP≥4h, IBU≥6h)")
    if top == "결막염 의심":
        advice.append("눈 위생, 분비물 제거, 병원 상담 고려")
    if top == "탈수/신장 문제":
        advice.append("즉시 수분 보충, 소변량/활력 징후 확인, 필요시 병원")
    if top == "출혈성 경향":
        advice.append("점상출혈/혈변 동반 시 즉시 병원")
    if advice:
        st.info(" / ".join(advice))

    # Antipyretic dosing
    st.markdown("---")
    st.subheader("해열제 계산기")
    wcol1,wcol2,wcol3 = st.columns([2,1,2])
    with wcol1:
        wt = st.text_input("체중(kg)", value=st.session_state.get(wkey("wt_peds"), ""), key=wkey("wt_peds"), placeholder="예: 12.5")
    wt_val = None
    try:
        wt_val = float(str(wt).strip()) if wt else None
    except Exception:
        wt_val = None

    ap_ml_1, ap_ml_max = (0.0, 0.0)
    ib_ml_1, ib_ml_max = (0.0, 0.0)
    if wt_val:
        try:
            ap_ml_1, ap_ml_max = acetaminophen_ml(wt_val)
        except Exception:
            ap_ml_1, ap_ml_max = (0.0, 0.0)
        try:
            ib_ml_1, ib_ml_max = ibuprofen_ml(wt_val)
        except Exception:
            ib_ml_1, ib_ml_max = (0.0, 0.0)

    with wcol2:
        st.metric("APAP 1회량(ml)", f"{ap_ml_1:.1f}" if ap_ml_1 else "—")
        st.metric("APAP 24h 최대(ml)", f"{ap_ml_max:.0f}" if ap_ml_max else "—")
    with wcol3:
        st.metric("IBU 1회량(ml)", f"{ib_ml_1:.1f}" if ib_ml_1 else "—")
        st.metric("IBU 24h 최대(ml)", f"{ib_ml_max:.0f}" if ib_ml_max else "—")
    st.caption("쿨다운: APAP ≥4시간, IBU ≥6시간. 중복 복용 주의.")

# ====== SPECIAL ======
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
    diets = []  # 수치 기반 식이가이드는 입력 제거로 비활성화
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

    # 항목 목록만 출력
    lines.append("")
    lines.append("## 피수치 항목(보기용)")
    for abbr, kor in [("WBC","백혈구"),("Hb","혈색소"),("PLT","혈소판"),("ANC","절대호중구"),
                      ("Ca","칼슘"),("P","인"),("Na","나트륨"),("Alb","알부민"),("Glu","혈당"),
                      ("T.P","총단백"),("AST","AST"),("ALT","ALT"),("CRP","CRP"),
                      ("Cr","크레아티닌"),("T.B","총빌리루빈"),("BUN","BUN")]:
        lines.append(f"- {abbr} — {kor}")

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
