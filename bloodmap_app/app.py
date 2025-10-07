
import streamlit as st
import datetime as _dt

# ------------- Safe stubs (no external deps) -------------
def export_md_to_pdf(md_text: str) -> bytes:
    # Fallback PDF: just return bytes so download works even without real PDF lib
    return md_text.encode("utf-8")

def render_deploy_banner(*a, **k): return None

def ensure_unique_pin(key: str, auto_suffix: bool=True):
    if not key: return "guest#PIN", False, "empty"
    if "#" not in key: key += "#0001"
    return key, False, "ok"

def lab_diet_guides(labs: dict, heme_flag=False):
    out = []
    try:
        ca = float(labs.get("Ca")) if labs.get("Ca") not in (None, "") else None
        if ca is not None and ca < 8.5: out.append("칼슘 낮음: 칼슘 보충 및 영양 식이.")
        na = float(labs.get("Na")) if labs.get("Na") not in (None, "") else None
        if na is not None and na < 135: out.append("저나트륨: 수분 제한 및 전해질 보충 고려.")
    except Exception:
        pass
    return out

# ------------- UI helpers -------------
st.set_page_config(page_title="Bloodmap (Safe Mode)", layout="wide")
st.title("Bloodmap (Safe Mode)")
st.markdown(
    """> In memory of Eunseo, a little star now shining in the sky.
> This app is made with the hope that she is no longer in pain,
> and resting peacefully in a world free from all hardships."""
)
st.markdown("---")
render_deploy_banner("", "")

def wkey(name:str)->str:
    who = st.session_state.get("key","guest#PIN")
    return f"{who}:{name}"

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

DEFAULT_WEIGHTS = {
    "w_anc_lt500": 1.0, "w_anc_500_999": 1.0,
    "w_temp_38_0_38_4": 1.0, "w_temp_ge_38_5": 1.0,
    "w_plt_lt20k": 1.0, "w_hb_lt7": 1.0, "w_crp_ge10": 1.0, "w_hr_gt130": 1.0,
    "w_hematuria": 1.0, "w_melena": 1.0, "w_hematochezia": 1.0,
    "w_chest_pain": 1.0, "w_dyspnea": 1.0, "w_confusion": 1.0,
    "w_oliguria": 1.0, "w_persistent_vomit": 1.0, "w_petechiae": 1.0,
}
def get_weights():
    key = st.session_state.get("key","guest#PIN")
    store = st.session_state.setdefault("weights", {})
    return store.setdefault(key, DEFAULT_WEIGHTS.copy())

def anc_band(anc: float) -> str:
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
    alerts = []
    t = temp_c if isinstance(temp_c,(int,float)) else _parse_float(temp_c)
    a = anc if isinstance(anc,(int,float)) else _parse_float(anc)
    p = plt if isinstance(plt,(int,float)) else _parse_float(plt)
    c = crp if isinstance(crp,(int,float)) else _parse_float(crp)
    h = hb  if isinstance(hb,(int,float)) else _parse_float(hb)
    heart = hr if isinstance(hr,(int,float)) else _parse_float(hr)
    W = get_weights()
    risk = 0.0
    if a is not None and a < 500:   risk += 3 * W["w_anc_lt500"]; alerts.append("ANC<500: 발열 시 응급(FN)")
    elif a is not None and a < 1000: risk += 2 * W["w_anc_500_999"]; alerts.append("ANC 500~999: 감염 주의")
    if t is not None and t >= 38.5: risk += 2 * W["w_temp_ge_38_5"]; alerts.append("고열(≥38.5℃)")
    elif t is not None and t >= 38.0: risk += 1 * W["w_temp_38_0_38_4"]; alerts.append("발열(38.0~38.4℃)")
    if p is not None and p < 20000: risk += 2 * W["w_plt_lt20k"]; alerts.append("혈소판 <20k: 출혈 위험")
    if h is not None and h < 7.0:   risk += 1 * W["w_hb_lt7"]; alerts.append("중증 빈혈(Hb<7)")
    if c is not None and c >= 10:   risk += 1 * W["w_crp_ge10"]; alerts.append("CRP 높음(≥10)")
    if heart and heart > 130:       risk += 1 * W["w_hr_gt130"]; alerts.append("빈맥")
    # symptoms ignored in safe mode inputs
    if risk >= 5: return "🚨 응급", alerts
    if risk >= 2: return "🟧 주의", alerts
    return "🟢 안심", alerts

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

# ---------- Sidebar ----------
with st.sidebar:
    st.header("프로필")
    raw_key = st.text_input("별명#PIN", st.session_state.get("key","guest#PIN"))
    unique_key, was_modified, msg = ensure_unique_pin(raw_key, auto_suffix=True)
    st.session_state["key"] = unique_key
    st.caption(f"현재 키: {unique_key}")
    temp = st.text_input("현재 체온(℃)", value=st.session_state.get(wkey("cur_temp"), ""),
                         key=wkey("cur_temp"), placeholder="36.8")
    hr   = st.text_input("심박수(bpm)", value=st.session_state.get(wkey("cur_hr"), ""),
                         key=wkey("cur_hr"), placeholder="0")

# ---------- Tabs ----------
tab_labels = ["🏠 홈","🧪 피수치 입력","📄 보고서"]
t_home, t_labs, t_report = st.tabs(tab_labels)

with t_home:
    st.subheader("응급도 요약")
    labs = st.session_state.get("labs_dict", {})
    level_tmp, reasons_tmp = emergency_level(labs, st.session_state.get(wkey("cur_temp")),
                                             st.session_state.get(wkey("cur_hr")), {})
    if level_tmp.startswith("🚨"): st.error("현재 상태: " + level_tmp)
    elif level_tmp.startswith("🟧"): st.warning("현재 상태: " + level_tmp)
    else: st.info("현재 상태: " + level_tmp)

with t_labs:
    st.subheader("피수치 입력 (Safe Mode)")
    st.caption("표기 예: 4.5 / 135 / 0.8  (숫자와 소수점만 입력)")
    use_peds = st.checkbox("소아 기준(참조범위/검증에 적용)", value=False, key=wkey("labs_use_peds"))
    order = [("WBC","백혈구"), ("Ca","칼슘"), ("Glu","혈당"), ("CRP","CRP"),
             ("Hb","혈색소"), ("P","인(Phosphorus)"), ("T.P","총단백"), ("Cr","크레아티닌"),
             ("PLT","혈소판"), ("Na","나트륨"), ("AST","AST"), ("T.B","총빌리루빈"),
             ("ANC","절대호중구"), ("Alb","알부민"), ("ALT","ALT"), ("BUN","BUN")]
    cols = st.columns(4)
    values = {}
    for idx, (abbr, kor) in enumerate(order):
        col = cols[idx % 4]
        with col:
            values[abbr] = float_input(f"{abbr} — {kor}", key=wkey(abbr))
            msg = lab_validate(abbr, values[abbr], use_peds)
            if msg:
                if msg == "정상범위": st.caption("✅ " + msg)
                elif msg == "형식 오류": st.warning("형식 오류: 숫자만 입력", icon="⚠️")
                else: st.warning(msg, icon="⚠️")
    labs_dict = st.session_state.get("labs_dict", {}); labs_dict.update(values)
    st.session_state["labs_dict"] = labs_dict
    st.markdown(f"**ANC 분류:** {anc_band(values.get('ANC'))}")
    st.markdown("### 현재 입력값 요약")
    nonempty = [(abbr, labs_dict.get(abbr)) for abbr,_ in order if labs_dict.get(abbr) not in (None, "")]
    if nonempty:
        for abbr, val in nonempty:
            rng = lab_ref(use_peds).get(abbr); rng_txt = f" ({rng[0]}~{rng[1]})" if rng else ""
            st.write(f"- **{abbr}**: {val}{rng_txt}")
    else:
        st.caption("아직 입력된 값이 없습니다.")

with t_report:
    st.subheader("보고서 (.md/.txt/.pdf-fallback)")
    key_id   = st.session_state.get("key","(미설정)")
    labs     = st.session_state.get("labs_dict", {})
    temp = st.session_state.get(wkey("cur_temp"))
    hr   = st.session_state.get(wkey("cur_hr"))
    level, reasons = emergency_level(labs or {}, temp, hr, {})
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
    all_labs = [("WBC","백혈구"),("Ca","칼슘"),("Glu","혈당"),("CRP","CRP"),
                ("Hb","혈색소"),("P","인(Phosphorus)"),("T.P","총단백"),("Cr","크레아티닌"),
                ("PLT","혈소판"),("Na","나트륨"),("AST","AST"),("T.B","총빌리루빈"),
                ("ANC","절대호중구"),("Alb","알부민"),("ALT","ALT"),("BUN","BUN")]
    for abbr, kor in all_labs:
        v = labs.get(abbr) if isinstance(labs, dict) else None
        lines.append(f"- {abbr} ({kor}): {v if v not in (None, '') else '—'}")
    lines.append(f"- ANC 분류: {anc_band(labs.get('ANC') if isinstance(labs, dict) else None)}")
    lines.append("")
    diets = lab_diet_guides(labs, heme_flag=False)
    if diets:
        lines.append("## 식이가이드(자동)")
        for d in diets: lines.append(f"- {d}")
        lines.append("")
    md = "\n".join(lines)
    st.code(md, language="markdown")
    st.download_button("💾 보고서 .md 다운로드", data=md.encode("utf-8"),
                       file_name="bloodmap_report.md", mime="text/markdown", key=wkey("dl_md"))
    st.download_button("📝 보고서 .txt 다운로드", data=md.encode("utf-8"),
                       file_name="bloodmap_report.txt", mime="text/plain", key=wkey("dl_txt"))
    pdf_bytes = export_md_to_pdf(md)
    st.download_button("📄 보고서 .pdf 다운로드(대체)", data=pdf_bytes,
                       file_name="bloodmap_report.pdf", mime="application/pdf", key=wkey("dl_pdf"))
