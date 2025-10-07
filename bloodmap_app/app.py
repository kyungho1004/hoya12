
import streamlit as st
import datetime as _dt

st.set_page_config(page_title="Bloodmap v7.17a (Single-File Lock)", layout="wide")
st.title("Bloodmap v7.17a (Single-File Lock)")

st.markdown(
    """> In memory of Eunseo, a little star now shining in the sky.
> This app is made with the hope that she is no longer in pain,
> and resting peacefully in a world free from all hardships."""
)
st.caption("※ 외부 모듈/파일을 사용하지 않는 단일 파일 버전입니다.")

# ---- helpers ----
def wkey(name:str)->str:
    who = st.session_state.get("key","guest#PIN")
    return f"{who}:{name}"

def _parse_float(txt):
    if txt is None: return None
    s = str(txt).strip().replace(",", "")
    if s == "": return None
    try: return float(s)
    except Exception: return None

def float_input(label:str, key:str, placeholder:str=""):
    val = st.text_input(label, value=str(st.session_state.get(key, "")), key=key, placeholder=placeholder)
    return _parse_float(val)

def export_md_to_pdf(md_text: str) -> bytes:
    # 대체 PDF: 내용을 그대로 바이트로 반환 (형식은 PDF가 아니지만 다운로드 가능)
    return md_text.encode("utf-8")

def ensure_unique_pin(key: str, auto_suffix: bool=True):
    if not key: return "guest#PIN", False, "empty"
    if "#" not in key: key += "#0001"
    return key, False, "ok"

DEFAULT_WEIGHTS = {
    "w_anc_lt500": 1.0, "w_anc_500_999": 1.0, "w_temp_38_0_38_4": 1.0, "w_temp_ge_38_5": 1.0,
    "w_plt_lt20k": 1.0, "w_hb_lt7": 1.0, "w_crp_ge10": 1.0, "w_hr_gt130": 1.0,
    "w_hematuria": 1.0, "w_melena": 1.0, "w_hematochezia": 1.0, "w_chest_pain": 1.0,
    "w_dyspnea": 1.0, "w_confusion": 1.0, "w_oliguria": 1.0, "w_persistent_vomit": 1.0, "w_petechiae": 1.0,
}
def get_weights():
    key = st.session_state.get("key","guest#PIN")
    store = st.session_state.setdefault("weights", {})
    return store.setdefault(key, DEFAULT_WEIGHTS.copy())

def anc_band(anc):
    if anc is None: return "(미입력)"
    try: anc = float(anc)
    except Exception: return "(값 오류)"
    if anc < 500: return "🚨 중증 호중구감소(<500)"
    if anc < 1000: return "🟧 중등도(500~999)"
    if anc < 1500: return "🟡 경도(1000~1499)"
    return "🟢 정상(≥1500)"

def emergency_level(labs: dict, temp_c, hr, symptoms: dict):
    anc = labs.get("ANC") if isinstance(labs, dict) else None
    plt = labs.get("PLT") if isinstance(labs, dict) else None
    crp = labs.get("CRP") if isinstance(labs, dict) else None
    hb  = labs.get("Hb")  if isinstance(labs, dict) else None

    t = temp_c if isinstance(temp_c,(int,float)) else _parse_float(temp_c)
    a = anc if isinstance(anc,(int,float)) else _parse_float(anc)
    p = plt if isinstance(plt,(int,float)) else _parse_float(plt)
    c = crp if isinstance(crp,(int,float)) else _parse_float(crp)
    h = hb  if isinstance(hb,(int,float)) else _parse_float(hb)
    heart = hr if isinstance(hr,(int,float)) else _parse_float(hr)

    W = get_weights()
    reasons = []; contrib = []
    def add(name, base, wkey):
        w = W.get(wkey, 1.0); s = base * w
        contrib.append({"factor": name, "base": base, "weight": w, "score": s})
        reasons.append(name)

    if a is not None and a < 500:      add("ANC<500", 3, "w_anc_lt500")
    elif a is not None and a < 1000:   add("ANC 500~999", 2, "w_anc_500_999")
    if t is not None and t >= 38.5:    add("고열 ≥38.5℃", 2, "w_temp_ge_38_5")
    elif t is not None and t >= 38.0:  add("발열 38.0~38.4℃", 1, "w_temp_38_0_38_4")
    if p is not None and p < 20000:    add("혈소판 <20k", 2, "w_plt_lt20k")
    if h is not None and h < 7.0:      add("중증 빈혈(Hb<7)", 1, "w_hb_lt7")
    if c is not None and c >= 10:      add("CRP ≥10", 1, "w_crp_ge10")
    if heart and heart > 130:          add("빈맥(HR>130)", 1, "w_hr_gt130")

    if symptoms.get("hematuria"):       add("혈뇨", 1, "w_hematuria")
    if symptoms.get("melena"):          add("흑색변", 2, "w_melena")
    if symptoms.get("hematochezia"):    add("혈변", 2, "w_hematochezia")
    if symptoms.get("chest_pain"):      add("흉통", 2, "w_chest_pain")
    if symptoms.get("dyspnea"):         add("호흡곤란", 2, "w_dyspnea")
    if symptoms.get("confusion"):       add("의식저하/혼돈", 3, "w_confusion")
    if symptoms.get("oliguria"):        add("소변량 급감", 2, "w_oliguria")
    if symptoms.get("persistent_vomit"):add("지속 구토", 2, "w_persistent_vomit")
    if symptoms.get("petechiae"):       add("점상출혈", 2, "w_petechiae")

    risk = sum(item["score"] for item in contrib)
    level = "🚨 응급" if risk >= 5 else ("🟧 주의" if risk >= 2 else "🟢 안심")
    return level, reasons, contrib

LAB_REF_ADULT = {"WBC": (4.0, 10.0), "Hb": (12.0, 16.0), "PLT": (150, 400),
    "ANC": (1500, 8000), "CRP": (0.0, 5.0), "Na": (135, 145),
    "Cr": (0.5, 1.2), "Glu": (70, 140), "Ca": (8.6, 10.2),
    "P": (2.5, 4.5), "T.P": (6.4, 8.3), "AST": (0, 40), "ALT": (0, 41),
    "T.B": (0.2, 1.2), "Alb": (3.5, 5.0), "BUN": (7, 20)}
LAB_REF_PEDS = {"WBC": (5.0, 14.0), "Hb": (11.0, 15.0), "PLT": (150, 450),
    "ANC": (1500, 8000), "CRP": (0.0, 5.0), "Na": (135, 145),
    "Cr": (0.2, 0.8), "Glu": (70, 140), "Ca": (8.8, 10.8),
    "P": (4.0, 6.5), "T.P": (6.0, 8.0), "AST": (0, 50), "ALT": (0, 40),
    "T.B": (0.2, 1.2), "Alb": (3.8, 5.4), "BUN": (5, 18)}
def lab_ref(is_peds: bool): return LAB_REF_PEDS if is_peds else LAB_REF_ADULT
def lab_validate(abbr: str, val, is_peds: bool):
    rng = lab_ref(is_peds).get(abbr); 
    if rng is None or val in (None, ""): return None
    try: v = float(val)
    except Exception: return "형식 오류"
    lo, hi = rng
    if v < lo: return f"⬇️ 기준치 미만({lo}~{hi})"
    if v > hi: return f"⬆️ 기준치 초과({lo}~{hi})"
    return "정상범위"

with st.sidebar:
    st.header("프로필")
    raw_key = st.text_input("별명#PIN", st.session_state.get("key","guest#PIN"))
    unique_key, _, _ = ensure_unique_pin(raw_key, auto_suffix=True)
    st.session_state["key"] = unique_key
    temp = st.text_input("현재 체온(℃)", value=st.session_state.get(wkey("cur_temp"), ""), key=wkey("cur_temp"))
    hr   = st.text_input("심박수(bpm)", value=st.session_state.get(wkey("cur_hr"), ""), key=wkey("cur_hr"))

tab_labels = ["🏠 홈","🧪 피수치 입력","📄 보고서"]
t_home, t_labs, t_report = st.tabs(tab_labels)

with t_home:
    st.subheader("응급도 요약")
    labs = st.session_state.get("labs_dict", {})
    level_tmp, reasons_tmp, contrib_tmp = emergency_level(labs, st.session_state.get(wkey("cur_temp")), st.session_state.get(wkey("cur_hr")), {})
    st.write("현재 상태:", level_tmp)

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
    with d2: persistent_vomit = st.checkbox("지속 구토(>6시간)", key=wkey("sym_pvomit"))
    with d3: petechiae = st.checkbox("점상출혈", key=wkey("sym_petechiae"))

    sym = dict(hematuria=hematuria, melena=melena, hematochezia=hematochezia,
               chest_pain=chest_pain, dyspnea=dyspnea, confusion=confusion,
               oliguria=oliguria, persistent_vomit=persistent_vomit, petechiae=petechiae)
    lvl, rea, con = emergency_level(labs, st.session_state.get(wkey("cur_temp")), st.session_state.get(wkey("cur_hr")), sym)
    st.write("응급도:", lvl, "—", " · ".join(rea))
    if con:
        st.markdown("**응급도 기여도(Why)**")
        tot = sum(x["score"] for x in con) or 1.0
        for it in sorted(con, key=lambda x:-x["score"]):
            pct = round(100.0*it["score"]/tot,1)
            st.write(f"- {it['factor']}: 점수 {round(it['score'],2)} (기본{it['base']}×가중치{it['weight']}, {pct}%)")

with t_labs:
    st.subheader("피수치 입력")
    use_peds = st.checkbox("소아 기준", value=False, key=wkey("labs_use_peds"))
    order = [("WBC","백혈구"), ("Ca","칼슘"), ("Glu","혈당"), ("CRP","CRP"),
             ("Hb","혈색소"), ("P","인(Phosphorus)"), ("T.P","총단백"), ("Cr","크레아티닌"),
             ("PLT","혈소판"), ("Na","나트륨"), ("AST","AST"), ("T.B","총빌리루빈"),
             ("ANC","절대호중구"), ("Alb","알부민"), ("ALT","ALT"), ("BUN","BUN")]
    cols = st.columns(4)
    values = {}
    for i,(abbr,kor) in enumerate(order):
        with cols[i%4]:
            values[abbr] = float_input(f"{abbr} — {kor}", key=wkey(abbr))
            msg = lab_validate(abbr, values[abbr], use_peds)
            if msg: st.caption(("✅ " if msg=="정상범위" else "⚠️ ")+msg)
    labs_dict = st.session_state.get("labs_dict", {}); labs_dict.update(values)
    st.session_state["labs_dict"] = labs_dict
    st.markdown(f"**ANC 분류:** {anc_band(values.get('ANC'))}")

with t_report:
    st.subheader("보고서 (.md/.txt/.pdf 대체)")
    key_id   = st.session_state.get("key","(미설정)")
    labs     = st.session_state.get("labs_dict", {})
    temp     = st.session_state.get(wkey("cur_temp"))
    hr       = st.session_state.get(wkey("cur_hr"))
    level, reasons, contrib = emergency_level(labs or {}, temp, hr, {})
    lines = []
    lines.append("# Bloodmap Report (Full)")
    lines.append(f"_생성 시각(KST): {_dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_")
    lines.append("")
    lines.append("> In memory of Eunseo, a little star now shining in the sky.")
    lines.append("> This app is made with the hope that she is no longer in pain,")
    lines.append("> and resting peacefully in a world free from all hardships.")
    lines.append("")
    lines.append("---"); lines.append("")
    lines.append("## 프로필"); lines.append(f"- 키(별명#PIN): {key_id}"); lines.append("")
    lines.append("## 응급도"); lines.append(f"- 현재: {level}"); [lines.append(f"  - {r}") for r in reasons]; lines.append("")
    lines.append("## 피수치")
    for abbr, kor in [("WBC","백혈구"),("Ca","칼슘"),("Glu","혈당"),("CRP","CRP"),
                      ("Hb","혈색소"),("P","인(Phosphorus)"),("T.P","총단백"),("Cr","크레아티닌"),
                      ("PLT","혈소판"),("Na","나트륨"),("AST","AST"),("T.B","총빌리루빈"),
                      ("ANC","절대호중구"),("Alb","알부민"),("ALT","ALT"),("BUN","BUN")]:
        v = labs.get(abbr)
        lines.append(f"- {abbr} ({kor}): {v if v not in (None, '') else '—'}")
    lines.append(f"- ANC 분류: {anc_band(labs.get('ANC'))}")
    md = "\n".join(lines)
    st.code(md, language="markdown")
    st.download_button("💾 .md 다운로드", data=md.encode("utf-8"), file_name="bloodmap_report.md")
    st.download_button("📝 .txt 다운로드", data=md.encode("utf-8"), file_name="bloodmap_report.txt")
    st.download_button("📄 .pdf(대체) 다운로드", data=export_md_to_pdf(md), file_name="bloodmap_report.pdf")
