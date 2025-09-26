# app.py — Minimal, always-on inputs (Labs, Diagnosis, Chemo, Special Tests)
import datetime as _dt
import streamlit as st
from peds_profiles import get_symptom_options
from peds_dose import acetaminophen_ml, ibuprofen_ml, estimate_weight_from_age_months
from special_tests import special_tests_ui
import json
import pytz
from pdf_export import export_md_to_pdf
import re

# -------- Safe banner (no-op if missing) --------
try:
    from branding import render_deploy_banner
except Exception:
    def render_deploy_banner(*a, **k): return None

st.set_page_config(page_title="Bloodmap (Minimal)", layout="wide")
st.title("Bloodmap (Minimal)")

# ---- Lab normals/thresholds ----
NORMALS = {
    "WBC": (4.0, 10.0, "10^3/µL"),
    "Hb": (12.0, 16.0, "g/dL"),
    "PLT": (150.0, 400.0, "10^3/µL"),
    "ANC": (1_500.0, 8_000.0, "/µL"),
    "Na": (135.0, 145.0, "mmol/L"),
    "K": (3.5, 5.1, "mmol/L"),
    "Ca": (8.5, 10.5, "mg/dL"),
    "P": (2.5, 4.5, "mg/dL"),
    "Alb": (3.5, 5.2, "g/dL"),
    "Glu": (70.0, 140.0, "mg/dL"),
    "T.P": (6.4, 8.3, "g/dL"),
    "AST": (0.0, 40.0, "U/L"),
    "ALP": (40.0, 130.0, "U/L"),
    "CRP": (0.0, 0.5, "mg/dL"),
    "UA": (3.5, 7.2, "mg/dL"),
    "T.b": (0.2, 1.2, "mg/dL"),
    "Cr(mg/dL)": (0.6, 1.3, "mg/dL"),
}

# Severity thresholds for quick banners (subset)
THRESH = {
    "ANC_critical": 500,
    "Na_low": 130,
    "Na_high": 150,
    "K_low": 3.0,
    "K_high": 6.0,
    "Hb_low": 7.0,
    "PLT_low": 20.0,
    "Ca_low": 7.0,
    "Glu_high": 300.0,
    "CRP_high": 10.0,
}

def lab_badge(name:str, value):
    lo, hi, unit = NORMALS.get(name, (None, None, ""))
    if value is None:
        return ""
    try:
        v = float(value)
    except Exception:
        return ""
    if lo is not None and hi is not None:
        if v < lo:
            return f"🟡 {v} {unit} (low {lo}-{hi})"
        if v > hi:
            return f"🟡 {v} {unit} (high {lo}-{hi})"
        return f"🟢 {v} {unit} (normal {lo}-{hi})"
    return f"{v} {unit}"

def lab_warnings(row: dict):
    warns = []
    anc = row.get("ANC")
    if anc is not None and float(anc) < THRESH["ANC_critical"]:
        warns.append(f"ANC {anc} /µL < {THRESH['ANC_critical']} → 🚨 강한 감염위험")
    na = row.get("Na")
    if na is not None:
        if float(na) < THRESH["Na_low"]:
            warns.append(f"Na {na} mmol/L < {THRESH['Na_low']} → 🚨 저나트륨")
        if float(na) > THRESH["Na_high"]:
            warns.append(f"Na {na} mmol/L > {THRESH['Na_high']} → 🚨 고나트륨")
    k = row.get("K")
    if k is not None:
        if float(k) < THRESH["K_low"] or float(k) > THRESH["K_high"]:
            warns.append(f"K {k} mmol/L 경계( {THRESH['K_low']}–{THRESH['K_high']} )")
    hb = row.get("Hb")
    if hb is not None and float(hb) < THRESH["Hb_low"]:
        warns.append(f"Hb {hb} g/dL < {THRESH['Hb_low']} → 수혈 고려")
    plt = row.get("PLT")
    if plt is not None and float(plt) < THRESH["PLT_low"]:
        warns.append(f"PLT {plt}k/µL < {THRESH['PLT_low']} → 출혈주의")
    ca = row.get("Ca")
    if ca is not None and float(ca) < THRESH["Ca_low"]:
        warns.append(f"Ca {ca} mg/dL < {THRESH['Ca_low']} → 경련/부정맥 위험")
    glu = row.get("Glu")
    if glu is not None and float(glu) > THRESH["Glu_high"]:
        warns.append(f"Glu {glu} mg/dL > {THRESH['Glu_high']} → 고혈당")
    crp = row.get("CRP")
    if crp is not None and float(crp) > THRESH["CRP_high"]:
        warns.append(f"CRP {crp} mg/dL > {THRESH['CRP_high']} → 염증/감염 의심")
    return warns



# ---- Home selector helpers ----
def _flatten_groups(groups_dict):
    items = []
    for big, arr in groups_dict.items():
        for code, name in arr:
            items.append(f"{code} · {name}")
    return items

render_deploy_banner("https://bloodmap.streamlit.app/", "제작: Hoya/GPT · 자문: Hoya/GPT")


# ---- PIN Lock (sidebar) ----
st.sidebar.subheader("🔒 PIN 잠금")
pin_set = st.session_state.get("pin_set", False)
if not pin_set:
    new_pin = st.sidebar.text_input("새 PIN 설정 (4~8자리)", type="password", key="pin_new")
    if new_pin and 4 <= len(new_pin) <= 8:
        st.session_state["pin_hash"] = new_pin
        st.session_state["pin_set"] = True
        st.sidebar.success("PIN 설정 완료")
else:
    trial = st.sidebar.text_input("PIN 입력해 잠금 해제", type="password", key="pin_try")
    st.session_state["pin_ok"] = (trial == st.session_state.get("pin_hash"))
    if st.session_state.get("pin_ok"):
        st.sidebar.success("잠금 해제됨")
    else:
        st.sidebar.info("일부 민감 탭은 PIN 필요")

# ---- Helpers ----
def wkey(name:str)->str:
    return f"key_{name}"

from datetime import datetime, timedelta
KST = pytz.timezone("Asia/Seoul")

def now_kst():
    return datetime.now(KST)

def _ics_event(title, start_dt, minutes=0):
    dt_str = start_dt.strftime("%Y%m%dT%H%M%S")
    return ("BEGIN:VCALENDAR\nVERSION:2.0\nBEGIN:VEVENT\n"
            f"SUMMARY:{title}\nDTSTART:{dt_str}\nEND:VEVENT\nEND:VCALENDAR")

def _get_log():
    return st.session_state.setdefault("care_log", [])

def _save_log_disk():
    try:
        import os, json
        os.makedirs("/mnt/data/care_log", exist_ok=True)
        with open("/mnt/data/care_log/default.json","w",encoding="utf-8") as f:
            json.dump(_get_log(), f, ensure_ascii=False, indent=2, default=str)
    except Exception:
        pass

def add_med_record(kind:str, name:str, dose_mg:float):
    rec = {"ts": now_kst().strftime("%Y-%m-%d %H:%M:%S"), "kind":kind, "name":name, "dose_mg":dose_mg}
    _get_log().append(rec); _save_log_disk()

def last_intake_minutes(name:str):
    tslist = []
    for r in _get_log()[::-1]:
        if r.get("name")==name:
            try:
                ts = KST.localize(datetime.strptime(r["ts"], "%Y-%m-%d %H:%M:%S"))
            except Exception:
                continue
            tslist.append(ts)
    if not tslist: return None
    return (now_kst() - tslist[0]).total_seconds() / 60.0

def total_last24_mg(name_set:set):
    total=0.0
    for r in _get_log():
        try:
            t = KST.localize(datetime.strptime(r["ts"], "%Y-%m-%d %H:%M:%S"))
        except Exception:
            continue
        if (now_kst()-t) <= timedelta(hours=24) and r.get("name") in name_set:
            total += float(r.get("dose_mg") or 0)
    return total

def med_guard_apap_ibu_ui(weight_kg: float):
    st.subheader("해열제 가드레일(APAP/IBU)")
    col1,col2,col3 = st.columns(3)
    with col1:
        apap = st.number_input("Acetaminophen 복용량 (mg)", 0, 2000, 0, 50, key=wkey("apap"))
        if st.button("기록(APAP)", key=wkey("btn_apap")) and apap>0:
            add_med_record("antipyretic","APAP", apap)
    with col2:
        ibu  = st.number_input("Ibuprofen 복용량 (mg)", 0, 1600, 0, 50, key=wkey("ibu"))
        if st.button("기록(IBU)", key=wkey("btn_ibu")) and ibu>0:
            add_med_record("antipyretic","IBU", ibu)
    with col3:
        if st.button("24h 요약 .ics 내보내기", key=wkey("ics_btn")):
            nxt = now_kst() + timedelta(hours=4)
            st.download_button("⬇️ .ics 저장", data=_ics_event("다음 복용 가능 시각(APAP 기준)", nxt).encode("utf-8"),
                               file_name="next_dose_apap.ics", mime="text/calendar", key=wkey("dl_ics"))
    apap_cd_min = 240
    ibu_cd_min  = 360
    wt = weight_kg or 0.0
    apap_max24 = min(4000.0, 60.0*wt if wt>0 else 4000.0)
    ibu_max24  = min(1200.0, 30.0*wt if wt>0 else 1200.0)
    apap_24 = total_last24_mg({"APAP"})
    ibu_24  = total_last24_mg({"IBU"})
    apap_last = last_intake_minutes("APAP")
    ibu_last  = last_intake_minutes("IBU")
    if apap_last is not None and apap_last < apap_cd_min:
        st.error(f"APAP 쿨다운 미충족: {int(apap_cd_min - apap_last)}분 남음")
    if ibu_last is not None and ibu_last < ibu_cd_min:
        st.error(f"IBU 쿨다운 미충족: {int(ibu_cd_min - ibu_last)}분 남음")
    if apap_24 > apap_max24:
        st.error(f"APAP 24시간 한도 초과: {apap_24:.0f}mg / 허용 {apap_max24:.0f}mg")
    else:
        st.caption(f"APAP 24h 합계 {apap_24:.0f}mg / 허용 {apap_max24:.0f}mg")
    if ibu_24 > ibu_max24:
        st.error(f"IBU 24시간 한도 초과: {ibu_24:.0f}mg / 허용 {ibu_max24:.0f}mg")
    else:
        st.caption(f"IBU 24h 합계 {ibu_24:.0f}mg / 허용 {ibu_max24:.0f}mg")

def risk_banner():
    apap_cd_min = 240; ibu_cd_min = 360
    apap_last = last_intake_minutes("APAP"); ibu_last = last_intake_minutes("IBU")
    apap_over = total_last24_mg({"APAP"}) > min(4000.0, 60.0*(st.session_state.get("wt") or 0.0))
    ibu_over  = total_last24_mg({"IBU"})  > min(1200.0, 30.0*(st.session_state.get("wt") or 0.0))
    if (apap_last is not None and apap_last < apap_cd_min) or (ibu_last is not None and ibu_last < ibu_cd_min) or apap_over or ibu_over:
        st.warning("🚨 최근 투약 관련 주의 필요: 쿨다운 미충족 또는 24시간 합계 초과 가능")


# -------- Helpers --------
def wkey(name:str)->str:
    who = st.session_state.get("key","guest")
    return f"{who}:{name}"
def enko(en:str, ko:str)->str:
    return f"{en} / {ko}" if ko else en

# -------- Inline defaults (no external files) --------

GROUPS = {
    "🩸 혈액암 (Leukemia/MDS/MPN)": [
        ("ALL (B/T)", "급성 림프모구 백혈병"),
        ("AML", "급성 골수성 백혈병"),
        ("APL", "급성 전골수성 백혈병"),
        ("CML", "만성 골수성 백혈병"),
        ("CLL", "만성 림프구성 백혈병"),
        ("Hairy Cell Leukemia", "털세포 백혈병"),
        ("MDS", "골수형성이상증후군"),
        ("MPN (PV/ET/PMF)", "골수증식성 종양"),
    ],
    "🧬 림프종 (Lymphoma)": [
        ("DLBCL", "미만성 거대 B세포 림프종"),
        ("FL", "여포성 림프종"),
        ("MCL", "외투세포 림프종"),
        ("MZL", "변연부 림프종"),
        ("Burkitt", "버킷 림프종"),
        ("Hodgkin", "호지킨 림프종"),
        ("PTCL/NOS", "말초 T세포 림프종"),
        ("ALCL", "역형성 대세포 림프종"),
        ("NK/T", "NK/T 세포 림프종"),
        ("Primary CNS Lymphoma", "원발성 CNS 림프종"),
        ("Waldenström", "월덴스트롬 거대글로불린혈증")
    ],
    "🧠 고형암 (Solid Tumors)": [
        ("Breast", "유방암"),
        ("NSCLC", "폐암-비소세포"),
        ("SCLC", "폐암-소세포"),
        ("Colorectal", "대장암"),
        ("Gastric", "위암"),
        ("Pancreas", "췌장암"),
        ("HCC", "간세포암"),
        ("Cholangiocarcinoma", "담관암"),
        ("Biliary", "담도암"),
        ("Esophageal", "식도암"),
        ("Head & Neck", "두경부암"),
        ("Thyroid", "갑상선암"),
        ("RCC", "신장암"),
        ("Urothelial/Bladder", "요로상피/방광암"),
        ("Prostate", "전립선암"),
        ("Ovary", "난소암"),
        ("Cervix", "자궁경부암"),
        ("Endometrium", "자궁내막암"),
        ("Testicular GCT", "고환 생식세포종양"),
        ("NET", "신경내분비종양"),
        ("Melanoma", "흑색종"),
        ("Merkel", "메르켈세포암")
    ],
    "🦴 육종 (Sarcoma)": [
        ("UPS", "미분화 다형성 육종"),
        ("LMS", "평활근육종"),
        ("Liposarcoma", "지방육종"),
        ("Synovial Sarcoma", "활막육종"),
        ("Rhabdomyosarcoma", "횡문근육종"),
        ("GIST", "위장관기질종양"),
        ("Angiosarcoma", "혈관육종"),
        ("Ewing", "유잉육종"),
        ("Osteosarcoma", "골육종"),
        ("Chondrosarcoma", "연골육종"),
        ("DFSP", "피부섬유육종")
    ],
    "🧩 희귀/소아": [
        ("Wilms", "윌름스 종양"),
        ("Neuroblastoma", "신경모세포종"),
        ("Medulloblastoma", "수모세포종"),
        ("Ependymoma", "상의세포종"),
        ("Retinoblastoma", "망막모세포종"),
        ("Hepatoblastoma", "간모세포종"),
        ("LCH", "랜게르한스세포 조직구증"),
        ("JMML", "소아 골수단핵구성 백혈병")
    ],
}
CHEMO_MAP = {
    "Acute Lymphoblastic Leukemia (ALL)": [
        "6-Mercaptopurine (메르캅토퓨린)","Methotrexate (메토트렉세이트)","Cytarabine/Ara-C (시타라빈)","Vincristine (빈크리스틴)"],
    "Acute Promyelocytic Leukemia (APL)": [
        "ATRA (트레티노인/베사노이드)","Arsenic Trioxide (아르세닉 트리옥사이드)","MTX (메토트렉세이트)","6-MP (메르캅토퓨린)"],
    "Acute Myeloid Leukemia (AML)": [
        "Ara-C (시타라빈)","Daunorubicin (다우노루비신)","Idarubicin (이다루비신)"],
    "Chronic Myeloid Leukemia (CML)": [
        "Imatinib (이마티닙)","Dasatinib (다사티닙)","Nilotinib (닐로티닙)"],
    "Diffuse Large B-cell Lymphoma (DLBCL)": ["R-CHOP","R-EPOCH","Polatuzumab combos"],
    "Burkitt Lymphoma": ["CODOX-M/IVAC"],
    "Hodgkin Lymphoma": ["ABVD"],
    "Wilms Tumor": ["Vincristine","Dactinomycin","Doxorubicin"],
    "Neuroblastoma": ["Cyclophosphamide","Topotecan","Cisplatin","Etoposide"],
    "Osteosarcoma": ["MAP"], "Ewing Sarcoma": ["VDC/IE"],
    "LCH": ["Vinblastine","Prednisone"], "JMML": ["Azacitidine","SCT"],
}

# -------- Sidebar (always visible) --------
with st.sidebar:
    st.header("프로필")
    st.session_state["key"] = st.text_input("별명#PIN", value=st.session_state.get("key","guest"), key=wkey("user_key"))
    st.caption("좌측 프로필은 저장/CSV 경로 키로 쓰입니다.")

# -------- Tabs --------
t_home, t_labs, t_dx, t_chemo, t_special, t_peds, t_care, t_report = st.tabs(
    ["🏠 홈","🧪 피수치 입력","🧬 암 선택","💊 항암제","🔬 특수검사","👶 소아","🩺 케어로그","📄 보고서"]

)
with t_home:

    # 🧭 모드 선택 (화면 단순화)
    mode = st.radio("모드 선택", ["성인(일반)", "소아"], key=wkey("home_mode"), horizontal=True)
    st.session_state["mode"] = "peds" if mode == "소아" else "adult"
    if st.session_state["mode"] == "adult":
        st.caption("간단 모드: 여기서 암을 선택하면 다른 탭도 해당 선택에 맞춰 요약만 보여줘요.")
        adult_list = _flatten_groups(GROUPS)
        sel = st.selectbox("암 선택 (성인)", ["(선택)"] + adult_list, key=wkey("home_adult_dx"))
        if sel and sel != "(선택)":
            code = sel.split(" · ")[0]
            st.session_state["dx"] = code
            st.success(f"진단 선택됨: {sel} — 보고서/요약에 반영됩니다.")
    else:
        st.caption("소아 모드: 소아 패널을 간결하게 사용합니다. (상세는 '👶 소아' 탭)")
        disease = st.selectbox("소아 질환(의심)", ["", "독감", "RSV", "상기도염", "아데노", "마이코", "수족구", "편도염", "코로나", "중이염"], index=0, key=wkey("home_peds_dx"))
        if disease:
            st.session_state["dx"] = f"Peds-{disease}"
            st.success(f"소아 질환 선택됨: {disease} — 보고서/요약에 반영됩니다.")

# 🧭 모드 선택 (화면 단순화)
with t_labs:
    st.subheader("피수치 입력")
    col1,col2,col3,col4,col5 = st.columns(5)
    with col1: sex = st.selectbox("성별", ["여","남"], key=wkey("sex"))
    with col2: age = st.number_input("나이(세)", 1, 110, 40, key=wkey("age"))
    with col3: wt  = st.number_input("체중(kg)", 0.0, 300.0, 0.0, 0.5, key=wkey("wt"))
    with col4: cr  = st.number_input("Cr (mg/dL)", 0.0, 20.0, 0.8, 0.1, key=wkey("cr"))
    with col5: day = st.date_input("측정일", value=_dt.date.today(), key=wkey("date"))
    # eGFR (CKD-EPI 2009) — simplified impl
    def egfr_2009(cr_mgdl:float, age:int, sex:str):
        sex_f = (sex=="여"); k = 0.7 if sex_f else 0.9; a = -0.329 if sex_f else -0.411
        mn = min(cr_mgdl/k,1); mx = max(cr_mgdl/k,1); sex_fac = 1.018 if sex_f else 1.0
        return round(141*(mn**a)*(mx**-1.209)*(0.993**age)*sex_fac,1)
    egfr = egfr_2009(cr, int(age), sex)
    st.metric("eGFR (CKD-EPI 2009)", f"{egfr} mL/min/1.73㎡")

# 핵심 수치 입력 (보고서/식이가이드/경보에 사용)
colA,colB,colC,colD,colE,colF,colG,colH = st.columns(8)
with colA: anc = st.number_input("ANC (/µL)", 0, 500000, 0, step=100, key=wkey("anc"))
with colB: hb  = st.number_input("Hb (g/dL)", 0.0, 25.0, 0.0, 0.1, key=wkey("hb"))
with colC: plt = st.number_input("PLT (10^3/µL)", 0, 1000, 0, step=1, key=wkey("plt"))
with colD: crp = st.number_input("CRP (mg/dL)", 0.0, 50.0, 0.0, 0.1, key=wkey("crp"))
with colE: alb = st.number_input("Albumin (g/dL)", 0.0, 6.0, 0.0, 0.1, key=wkey("alb"))
with colF: k   = st.number_input("K (mmol/L)", 0.0, 10.0, 0.0, 0.1, key=wkey("k"))
with colG: na  = st.number_input("Na (mmol/L)", 0.0, 200.0, 0.0, 1.0, key=wkey("na"))
with colH: ca  = st.number_input("Ca (mg/dL)", 0.0, 20.0, 0.0, 0.1, key=wkey("ca"))

# 정상범위 안내
st.caption("정상범위 예시 — WBC 4.0–10.0k/µL, Hb 12–16 g/dL, PLT 150–400k/µL, Na 135–145, K 3.5–5.1, Ca 8.5–10.5, Alb 3.5–5.2, AST 0–40 U/L, ALP 40–130 U/L, CRP 0–0.5 mg/dL, UA 3.5–7.2 mg/dL, T.b 0.2–1.2 mg/dL")


# 추가 핵심 수치
c1,c2,c3,c4 = st.columns(4)
with c1: wbc = st.number_input("WBC (10^3/µL)", 0.0, 500.0, 0.0, 0.1, key=wkey("wbc"))
with c2: glu = st.number_input("Glu (mg/dL)", 0.0, 1000.0, 0.0, 1.0, key=wkey("glu"))
with c3: tp  = st.number_input("T.P (g/dL)", 0.0, 12.0, 0.0, 0.1, key=wkey("tp"))
with c4: p   = st.number_input("P (mg/dL)", 0.0, 20.0, 0.0, 0.1, key=wkey("p"))

d1,d2,d3,d4 = st.columns(4)
with d1: ast_v = st.number_input("AST (U/L)", 0.0, 5000.0, 0.0, 1.0, key=wkey("ast"))
with d2: alp = st.number_input("ALP (U/L)", 0.0, 5000.0, 0.0, 1.0, key=wkey("alp"))
with d3: ua  = st.number_input("UA (mg/dL)", 0.0, 30.0, 0.0, 0.1, key=wkey("ua"))
with d4: tb  = st.number_input("T.b (mg/dL)", 0.0, 30.0, 0.0, 0.1, key=wkey("tb"))


# CSV 불러오기
up = st.file_uploader("파일에서 불러오기(CSV)", type=["csv"], key=wkey("csv_up"))
if up is not None:
    try:
        import pandas as pd
        df = pd.read_csv(up)
        st.session_state["lab_rows"] = df.to_dict(orient="records")
        st.success("CSV 불러오기 완료")
    except Exception as e:
        st.error(f"CSV 파싱 오류: {e}")

# 행 추가
st.session_state.setdefault("lab_rows", [])
if st.button("➕ 현재 값 추가", key=wkey("add_row")):
    st.session_state["lab_rows"].append({
        "date": str(day),
        "sex": sex, "age": int(age), "weight(kg)": wt,
        "Cr(mg/dL)": cr, "eGFR": egfr,
        "ANC": anc, "Hb": hb, "PLT": plt, "CRP": crp, "Alb": alb, "K": k, "Na": na, "Ca": ca, "WBC": wbc, "Glu": glu, "T.P": tp, "P": p, "AST": ast_v, "ALP": alp, "UA": ua, "T.b": tb
    })
    # 외부 저장
    try:
        import os, pandas as pd
        os.makedirs("/mnt/data/bloodmap_graph", exist_ok=True)
        pd.DataFrame(st.session_state["lab_rows"]).to_csv("/mnt/data/bloodmap_graph/default.labs.csv", index=False)
    except Exception:
        pass

rows = st.session_state["lab_rows"]
if rows:
    st.write("최근 입력:")
    for r in rows[-5:]:
        st.write(r)

with t_dx:
    if st.session_state.get('mode')=='peds':
        st.info('소아 모드에서는 성인 암 선택을 숨깁니다. 홈에서 성인 모드로 전환하세요.'); st.stop()
    st.subheader("암 선택")
    grp_tabs = st.tabs(list(GROUPS.keys()))
    for i,(g, lst) in enumerate(GROUPS.items()):
        with grp_tabs[i]:
            labels = [enko(en,ko) for en,ko in lst]
            sel = st.selectbox("진단명을 선택하세요", labels, key=wkey(f"dx_sel_{i}"))
            en_dx, ko_dx = lst[labels.index(sel)]
            if st.button("선택 저장", key=wkey(f"dx_save_{i}")):
                st.session_state["dx_en"] = en_dx
                st.session_state["dx_ko"] = ko_dx
                st.success(f"저장됨: {enko(en_dx, ko_dx)}")

with t_chemo:
    if st.session_state.get('mode')=='peds':
        st.info('소아 모드에서는 성인 항암제 탭을 최소화합니다. 홈에서 성인 모드로 전환하세요.'); st.stop()
    st.subheader("항암제")
    en_dx = st.session_state.get("dx_en")
    ko_dx = st.session_state.get("dx_ko","")
    if not en_dx:
        st.info("먼저 '암 선택'에서 저장하세요.")
    else:
        st.write(f"현재 진단: **{enko(en_dx, ko_dx)}**")
        suggestions = CHEMO_MAP.get(en_dx, CHEMO_MAP.get(ko_dx, []))
        picked = st.multiselect("항암제를 선택/추가", suggestions, default=suggestions, key=wkey("chemo_ms"))
        extra = st.text_input("추가 항암제(쉼표 구분)", key=wkey("chemo_extra"))
        if extra.strip():
            more = [x.strip() for x in extra.split(",") if x.strip()]
            seen, merged = set(), []
            for x in picked + more:
                if x not in seen: seen.add(x); merged.append(x)
            picked = merged
        if st.button("항암제 저장", key=wkey("chemo_save")):
            st.session_state["chemo_list"] = picked
            st.success("저장됨. '보고서'에서 확인")

with t_special:
    if st.session_state.get('mode')=='peds':
        st.info('소아 모드에서는 특수검사를 최소화합니다. 필요 시 성인 모드로 전환하세요.'); st.stop()
    spec_lines = special_tests_ui()



with t_peds:
    if st.session_state.get('mode')=='adult':
        st.info('소아 모드가 아닙니다. 홈에서 소아 모드를 선택하세요.'); st.stop()
    st.subheader("소아 패널")
    col1, col2, col3 = st.columns(3)
    with col1:
        age_years = st.number_input("나이(년)", 0.0, 18.0, 3.0, 0.5, key=wkey("p_agey"))
    with col2:
        age_months_extra = st.number_input("추가 개월", 0, 11, 0, key=wkey("p_agem"))
    with col3:
        wt_input = st.number_input("체중(kg) (선택)", 0.0, 150.0, 0.0, 0.1, key=wkey("p_wt"))
    age_months = int(age_years*12) + int(age_months_extra)
    est_wt = estimate_weight_from_age_months(age_months)
    weight = wt_input if wt_input > 0 else est_wt
    st.caption(f"추정 체중: {est_wt:.1f} kg (미입력 시 적용)")

    # 해열제 1회 권장량 (시럽 기준)
    apap_ml, used_w = acetaminophen_ml(age_months, wt_input if wt_input>0 else None)
    ibu_ml, _       = ibuprofen_ml(age_months, wt_input if wt_input>0 else None)
    st.metric("아세트아미노펜 1회량", f"{apap_ml} mL (기준체중 {used_w} kg)")
    st.metric("이부프로펜 1회량", f"{ibu_ml} mL (기준체중 {used_w} kg)")
    st.caption("참고: 시럽 농도 기준 — APAP 160mg/5mL, IBU 100mg/5mL · APAP 12.5mg/kg, IBU 7.5mg/kg")

    # 증상 프로파일
    disease = st.selectbox("질환(의심)", ["", "독감", "RSV", "상기도염", "아데노", "마이코", "수족구", "편도염", "코로나", "중이염"], index=0, key=wkey("p_dis"))
    opts = get_symptom_options(disease or "_default")
    sel = {}
    cols = st.columns(3)
    idx = 0
    for k, arr in opts.items():
        with cols[idx%3]:
            sel[k] = st.selectbox(k, arr, key=wkey("p_"+k))
        idx += 1

    # 요약 만들기 (보고서에 포함)
lines = []
lines.append("# Bloodmap Report")
lines.append(f"**진단명**: {dx if dx.strip() else '(미선택)'}")
lines.append("")
warns = lab_warnings(labs_latest) if labs_latest else []
if warns:
    lines.append("## 피수치 경보")
    for w in warns:
        lines.append(f"- {w}")
    lines.append("")
# 소아 요약
if 'peds_lines' in st.session_state and st.session_state['peds_lines']:
    lines.append("## 소아 요약")
    for s in st.session_state['peds_lines']:
        lines.append(f"- {s}")
    lines.append("")
lines.append("## 항암제 요약")
if meds:
    for m in meds:
        lines.append(f"- {m}")
else:
    lines.append("- (없음)")
if rows:
    lines.append("")
    lines.append("## 최근 검사 (최대 5개)")
    head = ["date","sex","age","weight(kg)","Cr(mg/dL)","eGFR"]
    lines.append("| " + " | ".join(head) + " |")
    lines.append("|" + "|".join(["---"]*len(head)) + "|")
    for r in rows[-5:]:
        lines.append("| " + " | ".join(str(r.get(k,'')) for k in head) + " |")