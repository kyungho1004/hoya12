# -*- coding: utf-8 -*-
import streamlit as st
from . import config

# ---- Safe helpers (fallbacks; no external utils module required) ----
def css_load():
    try:
        with open("bloodmap_app/style.css", "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception:
        pass

def safe_float(x):
    try:
        if x is None: return None
        if isinstance(x, str) and x.strip()=="": return None
        return float(x)
    except Exception:
        return None

def num_input(label: str, key: str, unit: str=None, step: float=0.1, format_decimals: int=2):
    ph = "예: " + ("0" if format_decimals==0 else "0." + ("0"*format_decimals))
    val = st.text_input(label + (f" ({unit})" if unit else ""), key=key, placeholder=ph)
    return safe_float(val)

def pediatric_guard(years_input, months_input):
    def _to_int(v):
        try:
            if v is None: return 0
            if isinstance(v, str) and v.strip()=="": return 0
            return int(float(v))
        except Exception:
            return 0
    y = _to_int(years_input); m = _to_int(months_input)
    return max(y*12 + m, 0)

def pin_4_guard(pin_str: str) -> str:
    only = "".join(ch for ch in (pin_str or "") if str(ch).isdigit())
    return (only[-4:]).zfill(4) if only else "0000"

# ---- Header / Profile ----
def _header():
    st.set_page_config(page_title="피수치 가이드 / BloodMap", layout="centered")
    css_load()
    st.title(config.APP_TITLE)
    st.caption(config.APP_TAGLINE)

def _profile():
    st.subheader("프로필")
    c1, c2 = st.columns([2,1])
    with c1:
        nick = st.text_input("별명", key="nick", placeholder="예: 우리공듀")
    with c2:
        raw_pin = st.text_input("PIN 4자리", key="pin", placeholder="0000")
        pin = pin_4_guard(raw_pin)
        st.caption(f"저장 키: {(nick or '').strip() or '사용자'}#{pin}")
    return (nick or '').strip(), pin

# ---- Diagnosis dictionaries ----
HEM_DIAG = ["AML", "APL", "ALL", "CML", "CLL"]
SOLID_DIAG = [
    "폐암", "유방암", "위암", "대장암", "간암", "췌장암", "담도암",
    "자궁내막암", "구강암/후두암", "피부암(흑색종)", "신장암", "갑상선암",
    "난소암", "자궁경부암", "전립선암", "뇌종양", "식도암", "방광암"
]
SARCOMA_DIAG = config.SARCOMA_TYPES
RARE_DIAG = ["담낭암", "부신암", "망막모세포종", "흉선암", "신경내분비종양", "간모세포종", "비인두암", "GIST"]

DRUGS_BY_DIAG = {
    "AML": ["아라시티딘(ARA-C)", "도우노루비신", "이다루비신", "사이클로포스파미드", "에토포사이드", "메토트렉세이트(MTX)", "G-CSF"],
    "APL": ["아트라(ATRA)", "이다루비신", "도우노루비신", "아라시티딘(ARA-C)", "G-CSF"],
    "ALL": ["빈크리스틴", "아스파라가제", "도우노루비신", "사이클로포스파미드", "메토트렉세이트(MTX)", "아라시티딘(ARA-C)", "에토포사이드"],
    "CML": ["이미티닙", "다사티닙", "닐로티닙", "하이드록시우레아"],
    "CLL": ["플루다라빈", "사이클로포스파미드", "리툭시맙"],
    "폐암": ["시스플라틴", "카보플라틴", "파클리탁셀", "도세탁셀", "젬시타빈", "페메트렉시드", "게피티닙", "엘로티닙", "오시머티닙", "알렉티닙", "베바시주맙", "펨브롤리주맙", "니볼루맙"],
    "유방암": ["독소루비신", "사이클로포스파미드", "파클리탁셀", "도세탁셀", "트라스투주맙", "베바시주맙"],
    "위암": ["시스플라틴", "옥살리플라틴", "5-FU", "카페시타빈", "파클리탁셀", "트라스투주맙", "펨브롤리주맙"],
    "대장암": ["5-FU", "카페시타빈", "옥살리플라틴", "이리노테칸", "베바시주맙"],
    "간암": ["소라페닙", "렌바티닙", "베바시주맙", "펨브롤리주맙", "니볼루맙"],
    "췌장암": ["젬시타빈", "옥살리플라틴", "이리노테칸", "5-FU"],
    "담도암": ["젬시타빈", "시스플라틴", "베바시주맙"],
    "자궁내막암": ["카보플라틴", "파클리탁셀"],
    "구강암/후두암": ["시스플라틴", "5-FU", "도세탁셀"],
    "피부암(흑색종)": ["다카르바진", "파클리탁셀", "니볼루맙", "펨브롤리주맙"],
    "신장암": ["수니티닙", "파조파닙", "베바시주맙", "니볼루맙", "펨브롤리주맙"],
    "갑상선암": ["렌바티닙", "소라페닙"],
    "난소암": ["카보플라틴", "파클리탁셀", "베바시주맙"],
    "자궁경부암": ["시스플라틴", "파클리탁셀", "베바시주맙"],
    "전립선암": ["도세탁셀", "카바지탁셀"],
    "뇌종양": ["테모졸로마이드", "베바시주맙"],
    "식도암": ["시스플라틴", "5-FU", "파클리탁셀", "니볼루맙", "펨브롤리주맙"],
    "방광암": ["시스플라틴", "젬시타빈", "베바시주맙", "펨브롤리주맙", "니볼루맙"],
    "연부조직육종": ["독소루비신", "이포스파마이드", "파조파닙"],
    "골육종": ["고용량 메토트렉세이트(MTX)", "도우노루비신", "시스플라틴", "이포스파마이드"],
    "유잉육종": ["빈크리스틴", "독소루비신", "시클로포스파미드", "이포스파마이드", "에토포사이드"],
    "활막육종": ["이포스파마이드", "독소루비신", "파조파닙"],
    "지방육종": ["독소루비신", "이포스파마이드"],
    "섬유육종": ["독소루비신", "이포스파마이드"],
    "평활근육종": ["독소루비신", "이포스파마이드", "파조파닙"],
    "혈관육종": ["독소루비신", "파클리탁셀"],
    "담낭암": ["젬시타빈", "시스플라틴"],
    "부신암": ["미토테인", "에토포사이드", "독소루비신", "시스플라틴"],
    "망막모세포종": ["빈크리스틴", "에토포사이드", "카보플라틴"],
    "흉선암": ["사이클로포스파미드", "독소루비신", "시스플라틴"],
    "신경내분비종양": ["에토포사이드", "시스플라틴", "수니티닙"],
    "간모세포종": ["시스플라틴", "독소루비신"],
    "비인두암": ["시스플라틴", "5-FU", "젬시타빈", "베바시주맙", "니볼루맙", "펨브롤리주맙"],
    "GIST": ["이미티닙", "수니티닙", "레고라페닙"],
}

# ---- Panels ----
def panel_topnav():
    st.subheader("분류 선택")
    return st.segmented_control("모드", options=["소아 일상", "감염질환", "혈액암", "고형암", "육종", "희귀암"], key="top_mode")

def panel_peds_daily():
    st.subheader("소아(일상/호흡기) 입력")
    def _n(label, key, decimals=1, placeholder=""):
        raw = st.text_input(label, key=key, placeholder=placeholder)
        try:
            return None if raw.strip()=="" else round(float(raw), decimals)
        except Exception:
            return None
    vals = {}
    vals["age_m"]  = _n("나이(개월)", "ped_age", 0, "예: 18")
    vals["temp_c"] = _n("체온(℃)", "ped_temp", 1, "예: 38.2")
    vals["rr"]     = _n("호흡수(/분)", "ped_rr", 0, "예: 42")
    vals["spo2"]   = _n("산소포화도(%)", "ped_spo2", 0, "예: 96")
    vals["u24"]    = _n("24시간 소변 횟수", "ped_u", 0, "예: 6")
    vals["ret"]    = _n("흉곽 함몰(0/1)", "ped_ret", 0, "0 또는 1")
    vals["nf"]     = _n("콧벌렁임(0/1)", "ped_nf", 0, "0 또는 1")
    vals["ap"]     = _n("무호흡(0/1)", "ped_ap", 0, "0 또는 1")
    # Risk banner
    danger=False; urgent=False; notes=[]
    if vals["spo2"] is not None and vals["spo2"] < 92: danger=True; notes.append("SpO₂<92%")
    if vals["ap"]   is not None and vals["ap"] >=1: danger=True; notes.append("무호흡")
    if vals["rr"]   is not None and vals["age_m"] is not None:
        if (vals["age_m"] <= 12 and vals["rr"]>60) or (vals["age_m"]>12 and vals["rr"]>50):
            urgent=True; notes.append("호흡수 상승")
    if vals["temp_c"] is not None and vals["temp_c"]>=39.0: urgent=True; notes.append("고열")
    if vals["ret"] is not None and vals["ret"]>=1: urgent=True; notes.append("흉곽 함몰")
    if vals["nf"] is not None and vals["nf"]>=1: urgent=True; notes.append("콧벌렁임")
    if vals["u24"] is not None and vals["u24"] < 3: urgent=True; notes.append("소변 감소")
    if danger: st.error("🚑 위급 신호: 즉시 병원/응급실 평가 권고 — " + ", ".join(notes))
    elif urgent: st.warning("⚠️ 주의: 빠른 진료 필요 — " + ", ".join(notes))
    else: st.info("🙂 가정관리 가능 신호(경과 관찰)")
    return vals

def panel_infect():
    st.subheader("소아 감염질환")
    # 간단한 내장 리스트(문구는 최소). 실제 데이터 테이블은 연결 시 확장 가능.
    diseases = {
        "급성 후두염(Croup)": {"핵심":"개짖는기침, 흡기성 천명", "진단":"임상", "특징":"야간악화, 스테로이드 효과"},
        "세기관지염": {"핵심":"RSV 흔함", "진단":"RSV 항원/임상", "특징":"영아, 산소요구 가능"},
        "폐렴": {"핵심":"발열/기침/호흡곤란", "진단":"X-ray", "특징":"세균/바이러스 다양"},
        "AOM(중이염)": {"핵심":"귀통증, 발열", "진단":"이경", "특징":"항생제 고려"},
    }
    sel = st.selectbox("질환", list(diseases.keys()))
    info = diseases[sel]
    st.write(f"- 핵심: {info['핵심']}")
    st.write(f"- 진단: {info['진단']}")
    st.write(f"- 특징: {info['특징']}")
    return {"infect": sel, **info}

def panel_cancer(group_name: str):
    st.subheader(f"{group_name} · 진단명")
    if group_name == "혈액암":
        diag = st.selectbox("진단명", HEM_DIAG, key="diag_h")
    elif group_name == "고형암":
        diag = st.selectbox("진단명", SOLID_DIAG, key="diag_s")
    elif group_name == "육종":
        diag = st.selectbox("진단명", SARCOMA_DIAG, key="diag_sa")
    else:
        diag = st.selectbox("진단명", RARE_DIAG, key="diag_r")
    drug_opts = DRUGS_BY_DIAG.get(diag) or config.ANTICANCER_BY_GROUP.get(group_name, [])
    st.multiselect("항암제 (한글 표기)", options=drug_opts, key=f"anticancer_{group_name}")
    st.selectbox("아라시티딘(ARA-C) 제형", config.ARAC_FORMS, key=f"arac_form_{group_name}")
    st.checkbox("ATRA (캡슐) 복용 중", key=f"atra_caps_{group_name}")
    st.multiselect("항생제 (한글 표기)", options=config.ANTIBIOTICS, key=f"abx_{group_name}")
    return diag

def panel_base4():
    st.subheader("기본 4항목 입력")
    c1,c2,c3,c4 = st.columns(4)
    with c1: wbc = num_input("WBC (×10³/µL)", "wbc", step=0.1, format_decimals=1)
    with c2: hb  = num_input("Hb (g/dL)", "hb", step=0.1, format_decimals=1)
    with c3: plt = num_input("혈소판 (×10³/µL)", "plt", step=1, format_decimals=0)
    with c4: anc = num_input("ANC (/µL)", "anc", step=10, format_decimals=0)
    return {"wbc": wbc, "hb": hb, "plt": plt, "anc": anc}

def panel_order20():
    st.subheader("ORDER 기반 20항목 입력")
    cols = st.columns(3)
    values = {}
    for idx, (key, label, unit, decs) in enumerate(config.ORDER):
        col = cols[idx % 3]
        with col:
            val = num_input(label, f"ord_{key}", unit=unit, format_decimals=(decs if decs is not None else 2))
            values[key] = val
    return values

def panel_special():
    st.subheader("특수검사 (토글)")
    out = {}
    for title, items in config.SPECIAL_PANELS.items():
        with st.expander(title, expanded=False):
            for key, label, unit, decs in items:
                val = num_input(label, f"sp_{key}", unit=unit, format_decimals=(decs if decs is not None else 2))
                out[key] = val
    return out

def panel_guides(values):
    st.subheader("영양/안전 가이드")
    cuts = config.CUTS
    guides = []
    alb = safe_float(values.get("albumin"))
    if alb is not None and alb < cuts["albumin_low"]:
        guides.append(config.NUTRITION_GUIDE["albumin_low"])
    k = safe_float(values.get("k"))
    if k is not None and k < cuts["k_low"]:
        guides.append(config.NUTRITION_GUIDE["k_low"])
    hb = safe_float(values.get("hb"))
    if hb is not None and hb < cuts["hb_low"]:
        guides.append(config.NUTRITION_GUIDE["hb_low"])
    na = safe_float(values.get("na"))
    if na is not None and na < cuts["na_low"]:
        guides.append(config.NUTRITION_GUIDE["na_low"])
    ca = safe_float(values.get("ca"))
    if ca is not None and ca < cuts["ca_low"]:
        guides.append(config.NUTRITION_GUIDE["ca_low"])
    anc = safe_float(values.get("anc"))
    if anc is not None and anc < cuts["anc_neutropenia"]:
        guides.append(config.NUTRITION_GUIDE["anc_low"])
    if guides:
        for g in guides: st.warning(g)
    else:
        st.info("조건에 해당하는 가이드가 아직 없습니다. 필요한 항목을 입력해주세요.")

# ---- Main ----
def main():
    _header()
    _profile()
    mode = panel_topnav()

    if mode == "소아 일상":
        ped_vals = panel_peds_daily()
        base = {}; more = {}
    elif mode == "감염질환":
        inf = panel_infect()
        base = {}; more = {}
    else:
        # Cancer groups share the same lab panels & guides
        diag = panel_cancer(mode)
        base = panel_base4()
        more = panel_order20()
        panel_special()

    # unified guide section (uses any available values)
    values = {**base, **more}
    panel_guides(values)

    st.divider()
    st.caption("저장 키(별명#PIN)로 중복 방지 · 숫자만 허용/자동 정리")
    st.caption("참고용 앱입니다. 모든 의학적 판단은 주치의와 상의하세요.")

if __name__ == "__main__":
    main()
