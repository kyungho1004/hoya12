# app.py — complete UI with cancer type selection and rich lab inputs
import datetime as _dt
import os as _os
import typing as _t
import streamlit as st

# ---- Safe banner import (package/flat/no-op) ----
try:
    from branding import render_deploy_banner  # flat
except Exception:
    try:
        from .branding import render_deploy_banner  # package
    except Exception:
        def render_deploy_banner(*args, **kwargs):
            return None

# optional pandas
try:
    import pandas as pd
except Exception:
    pd = None

# ---- Page setup ----
st.set_page_config(page_title="Bloodmap", layout="wide")
st.title("Bloodmap")
render_deploy_banner("https://bloodmap.streamlit.app/", "제작: Hoya/GPT · 자문: Hoya/GPT")

# ---- Style (optional) ----
try:
    with open("style.css", "r", encoding="utf-8") as _f:
        st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)
except Exception:
    pass

# ---- Helpers ----
def wkey(name: str) -> str:
    try:
        who = st.session_state.get("key", "guest")
        mode_now = st.session_state.get("mode", "main")
        return f"{mode_now}:{who}:{name}"
    except Exception:
        return name

def init_care_log(user_key: str):
    st.session_state.setdefault("care_log", {})
    st.session_state["care_log"].setdefault(user_key, [])
    return st.session_state["care_log"][user_key]

def save_labs_csv(df, key: str):
    try:
        save_dir = "/mnt/data/bloodmap_graph"
        _os.makedirs(save_dir, exist_ok=True)
        csv_path = _os.path.join(save_dir, f"{key}.labs.csv")
        if pd is None:
            raise RuntimeError("pandas not available")
        df.to_csv(csv_path, index=False, encoding="utf-8")
        st.caption(f"외부 저장 완료: {csv_path}")
    except Exception as _e:
        st.warning("외부 저장 실패: " + str(_e))

# eGFR util (prefer core_utils if available)
def _egfr_local(scr_mgdl: float, age_y: int, sex: str) -> _t.Optional[float]:
    try:
        if scr_mgdl is None or age_y is None:
            return None
        sex_f = (sex == "여")
        k = 0.7 if sex_f else 0.9
        a = -0.329 if sex_f else -0.411
        min_cr = min(scr_mgdl / k, 1)
        max_cr = max(scr_mgdl / k, 1)
        sex_fac = 1.018 if sex_f else 1.0
        val = 141 * (min_cr ** a) * (max_cr ** -1.209) * (0.993 ** int(age_y)) * sex_fac
        return round(val, 1)
    except Exception:
        return None

try:
    from core_utils import egfr_ckd_epi_2009 as egfr_fn  # type: ignore
except Exception:
    egfr_fn = _egfr_local

# ---- Sidebar ----
with st.sidebar:
    st.header("프로필")
    st.session_state["key"] = st.text_input("별명#PIN", value=st.session_state.get("key", "guest"), key=wkey("user_key"))
    st.session_state["mode"] = st.radio("모드", ["일반", "암", "소아"], index=0, key=wkey("mode_sel"))
    # 암 종류 선택(없으면 로컬 리스트)
    try:
        from onco_map import CANCER_TYPES  # type: ignore
        cancer_list = list(CANCER_TYPES) if isinstance(CANCER_TYPES, (list, tuple)) else list(CANCER_TYPES.keys())
    except Exception:
        cancer_list = ["선택 안함","ALL","AML","Lymphoma","Breast","Lung","Colon","Stomach","Liver","Other"]
    st.session_state["cancer_type"] = st.selectbox("암 종류", cancer_list, index=0, key=wkey("cancer_type"))
    st.markdown("----")
    st.subheader("🧬 진단 및 항암제")
    # onco_map 기반 값 목록(영문 값 유지) + 한국어 병기 표시
    try:
        from onco_map import CANCER_TYPES  # type: ignore
        _vals = list(CANCER_TYPES.keys()) if isinstance(CANCER_TYPES, dict) else list(CANCER_TYPES)
    except Exception:
        _vals = ["Acute Lymphoblastic Leukemia (ALL)",
                 "Acute Promyelocytic Leukemia (APL)",
                 "Ewing Sarcoma",
                 "Chronic Myeloid Leukemia (CML)",
                 "Diffuse Large B-Cell Lymphoma (DLBCL)",
                 "Hodgkin Lymphoma",
                 "Breast Cancer",
                 "Non-Small Cell Lung Cancer (NSCLC)",
                 "Small Cell Lung Cancer (SCLC)",
                 "Colon Cancer",
                 "Gastric Cancer",
                 "Hepatocellular Carcinoma",
                 "Pancreatic Cancer",
                 "Ovarian Cancer",
                 "Cervical Cancer",
                 "Prostate Cancer",
                 "Glioblastoma",
                 "Other"]
    KO = {
        "Acute Lymphoblastic Leukemia": "급성 림프모구 백혈병",
        "Acute Promyelocytic Leukemia": "급성 전골수구성 백혈병",
        "Ewing Sarcoma": "유잉육종",
        "Chronic Myeloid Leukemia": "만성 골수성 백혈병",
        "Diffuse Large B-Cell Lymphoma": "거대 B세포 림프종",
        "Hodgkin Lymphoma": "호지킨 림프종",
        "Breast Cancer": "유방암",
        "Non-Small Cell Lung Cancer": "비소세포 폐암",
        "Small Cell Lung Cancer": "소세포 폐암",
        "Colon Cancer": "대장암",
        "Gastric Cancer": "위암",
        "Hepatocellular Carcinoma": "간세포암",
        "Pancreatic Cancer": "췌장암",
        "Ovarian Cancer": "난소암",
        "Cervical Cancer": "자궁경부암",
        "Prostate Cancer": "전립선암",
        "Glioblastoma": "교모세포종",
        "Other": "기타",
    }
    def _fmt_dx(name: str) -> str:
        if name == "선택":
            return "선택"
        base = name
        abbr = None
        if "(" in name and name.endswith(")"):
            base = name[:name.rfind("(")].strip()
            abbr = name[name.rfind("(")+1:-1].strip()
        base_clean = base
        ko = KO.get(base_clean) or KO.get(name)
        label = base_clean + (f" ({abbr})" if abbr else "")
        if ko:
            label = f"{label} / {ko}"
        return label
    dx_values = ["선택"] + _vals
    selected_cancer = st.selectbox("🧬 진단명을 선택하세요", dx_values, format_func=_fmt_dx, key=wkey("dx_select"))
    chemo_map = {
        "Acute Lymphoblastic Leukemia (ALL)": ["6-MP (메르캅토퓨린)", "MTX (메토트렉세이트)", "Ara-C (시타라빈)", "Vincristine (빈크리스틴)"],
        "Acute Promyelocytic Leukemia (APL)": ["ATRA (베사노이드)", "ATO (아르세닉 트리옥사이드)", "MTX (메토트렉세이트)", "6-MP (메르캅토퓨린)"],
        "Ewing Sarcoma": ["Vincristine (빈크리스틴)", "Doxorubicin (독소루비신)", "Cyclophosphamide (사이클로포스파마이드)", "Ifosfamide (이포스파마이드)", "Etoposide (에토포사이드)"],
    }
    if selected_cancer in chemo_map:
        meds = st.multiselect("💊 사용 중인 항암제를 선택하세요", chemo_map[selected_cancer], key=wkey("chemo_ms"))
    elif selected_cancer in ("선택","Other"):
        st.text("진단명을 선택하시면 항암제가 자동 표시됩니다.")
        meds = []
    else:
        st.info("이 진단에 대한 자동 추천 목록이 아직 등록되지 않았습니다. 직접 입력해주세요.")
        meds = st.text_input("기타 항암제(쉼표로 구분)", key=wkey("chemo_other"))
    st.session_state["chemo_meds"] = meds

    st.markdown("----")
    st.subheader("🧬 진단 및 항암제")
    # 진단 선택 + 자동 항암제 추천
    dx_options = [
        "선택",
        "Acute Lymphoblastic Leukemia (ALL)",
        "Acute Promyelocytic Leukemia (APL)",
        "Ewing Sarcoma",
        "기타",
    ]
    selected_cancer = st.selectbox("🧬 진단명을 선택하세요", dx_options, key=wkey("dx_select"))
    chemo_map = {
        "Acute Lymphoblastic Leukemia (ALL)": ["6-MP (메르캅토퓨린)", "MTX (메토트렉세이트)", "Ara-C (시타라빈)", "Vincristine (빈크리스틴)"],
        "Acute Promyelocytic Leukemia (APL)": ["ATRA (베사노이드)", "ATO (아르세닉 트리옥사이드)", "MTX (메토트렉세이트)", "6-MP (메르캅토퓨린)"],
        "Ewing Sarcoma": ["Vincristine (빈크리스틴)", "Doxorubicin (독소루비신)", "Cyclophosphamide (사이클로포스파마이드)", "Ifosfamide (이포스파마이드)", "Etoposide (에토포사이드)"],
    }
    if selected_cancer in chemo_map:
        meds = st.multiselect("💊 사용 중인 항암제를 선택하세요", chemo_map[selected_cancer], key=wkey("chemo_ms"))
    elif selected_cancer == "기타":
        meds = st.text_input("기타 항암제(쉼표로 구분)", key=wkey("chemo_other"))
    else:
        st.text("진단명을 선택하시면 항암제가 자동 표시됩니다.")
        meds = []
    st.session_state["chemo_meds"] = meds


# ---- Tabs ----
tab_home, tab_labs, tab_meds = st.tabs(["🏠 홈", "🧪 검사/지표", "💊 해열제 가드"])

with tab_home:
    st.success("앱이 정상 동작 중입니다. 좌측에서 프로필/암 종류를 선택하고 탭을 이용하세요.")

with tab_labs:
    st.subheader("기본 수치 입력")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        sex = st.selectbox("성별", ["여","남"], key=wkey("sex"))
    with c2:
        age = st.number_input("나이(세)", min_value=1, max_value=110, step=1, value=40, key=wkey("age"))
    with c3:
        weight = st.number_input("체중(kg)", min_value=0.0, step=0.5, value=0.0, key=wkey("wt"))
    with c4:
        cr = st.number_input("Cr (mg/dL)", min_value=0.0, step=0.1, value=0.8, key=wkey("cr"))
    with c5:
        today = st.date_input("측정일", value=_dt.date.today(), key=wkey("date"))
    st.caption("※ eGFR(CKD-EPI 2009)은 성별/나이/Cr만 사용합니다. 체중은 표/CSV에 함께 저장됩니다.")
    egfr = egfr_fn(cr, int(age), sex)
    if egfr is not None:
        st.metric("eGFR (CKD-EPI 2009)", f"{egfr} mL/min/1.73㎡")

    st.markdown("#### 주요 혈액/생화학")
    r1c1, r1c2, r1c3, r1c4 = st.columns(4)
    WBC = r1c1.number_input("WBC (10^3/µL)", min_value=0.0, step=0.1, value=5.0, key=wkey("wbc"))
    Hb  = r1c2.number_input("Hb (g/dL)",     min_value=0.0, step=0.1, value=13.0, key=wkey("hb"))
    PLT = r1c3.number_input("Platelet (10^3/µL)", min_value=0.0, step=1.0, value=250.0, key=wkey("plt"))
    ANC = r1c4.number_input("ANC (/µL)", min_value=0.0, step=100.0, value=3000.0, key=wkey("anc"))

    r2c1, r2c2, r2c3, r2c4 = st.columns(4)
    AST = r2c1.number_input("AST (U/L)", min_value=0.0, step=1.0, value=20.0, key=wkey("ast"))
    ALT = r2c2.number_input("ALT (U/L)", min_value=0.0, step=1.0, value=20.0, key=wkey("alt"))
    TB  = r2c3.number_input("T.bil (mg/dL)", min_value=0.0, step=0.1, value=0.8, key=wkey("tbil"))
    ALP = r2c4.number_input("ALP (U/L)", min_value=0.0, step=5.0, value=90.0, key=wkey("alp"))

    r3c1, r3c2, r3c3, r3c4 = st.columns(4)
    Na  = r3c1.number_input("Na (mmol/L)", min_value=0.0, step=0.5, value=140.0, key=wkey("na"))
    K   = r3c2.number_input("K (mmol/L)",  min_value=0.0, step=0.1, value=4.0, key=wkey("k"))
    Cl  = r3c3.number_input("Cl (mmol/L)", min_value=0.0, step=0.5, value=103.0, key=wkey("cl"))
    CRP = r3c4.number_input("CRP (mg/dL)", min_value=0.0, step=0.1, value=0.3, key=wkey("crp"))

    # Build dataframe
    if pd is not None:
        row = {
            "date": str(today), "cancer": st.session_state.get("cancer_type",""),
            "sex": sex, "age": int(age), "weight(kg)": weight, "Cr(mg/dL)": cr, "eGFR": egfr,
            "WBC": WBC, "Hb": Hb, "PLT": PLT, "ANC": ANC,
            "AST": AST, "ALT": ALT, "Tbil": TB, "ALP": ALP,
            "Na": Na, "K": K, "Cl": Cl, "CRP": CRP,
        }
        st.session_state.setdefault("lab_rows", [])
        if st.button("➕ 현재 값 추가", key=wkey("add_row")):
            st.session_state["lab_rows"].append(row)
        df = pd.DataFrame(st.session_state["lab_rows"] or [row])
        st.dataframe(df, use_container_width=True)
        csv_btn = st.button("📁 외부 저장(.csv)", key=wkey("save_csv_btn"))
        if csv_btn:
            save_labs_csv(df, st.session_state.get("key","guest"))
    else:
        st.info("pandas 미탑재: 표/CSV 저장 기능 비활성화")

with tab_meds:
    st.subheader("해열제 가드레일 (APAP/IBU)")
    from datetime import datetime, timedelta
    try:
        from pytz import timezone
        def _now_kst(): return datetime.now(timezone("Asia/Seoul"))
    except Exception:
        def _now_kst(): return datetime.now()

    def _ics(title: str, when: datetime) -> bytes:
        dt = when.strftime("%Y%m%dT%H%M%S")
        ics = f"BEGIN:VCALENDAR\nVERSION:2.0\nBEGIN:VEVENT\nSUMMARY:{title}\nDTSTART:{dt}\nEND:VEVENT\nEND:VCALENDAR\n"
        return ics.encode("utf-8")

    log = init_care_log(st.session_state.get("key","guest"))

    c1, c2, c3 = st.columns(3)
    limit_apap = c1.number_input("APAP 24h 한계(mg)", min_value=0, value=4000, step=100, key=wkey("apap_limit"))
    limit_ibu  = c2.number_input("IBU  24h 한계(mg)", min_value=0, value=1200, step=100, key=wkey("ibu_limit"))
    _ = c3.number_input("체중(kg, 선택)", min_value=0.0, value=0.0, step=0.5, key=wkey("wt_opt"))

    d1, d2 = st.columns(2)
    apap_now = d1.number_input("APAP 복용량(mg)", min_value=0, value=0, step=50, key=wkey("apap_now"))
    ibu_now  = d2.number_input("IBU 복용량(mg)",  min_value=0, value=0, step=50, key=wkey("ibu_now"))

    if d1.button("APAP 복용 기록", key=wkey("apap_take_btn")):
        last = next((x for x in reversed(log) if x.get("drug")=="APAP"), None)
        now = _now_kst()
        if last:
            last_t = _dt.datetime.fromisoformat(last["t"])
            if (now - last_t).total_seconds() < 4*3600:
                st.error("APAP 쿨다운 4시간 미만입니다.")
            else:
                log.append({"t": now.isoformat(), "drug":"APAP", "dose": apap_now})
        else:
            log.append({"t": now.isoformat(), "drug":"APAP", "dose": apap_now})

    if d2.button("IBU 복용 기록", key=wkey("ibu_take_btn")):
        last = next((x for x in reversed(log) if x.get("drug")=="IBU"), None)
        now = _now_kst()
        if last:
            last_t = _dt.datetime.fromisoformat(last["t"])
            if (now - last_t).total_seconds() < 6*3600:
                st.error("IBU 쿨다운 6시간 미만입니다.")
            else:
                log.append({"t": now.isoformat(), "drug":"IBU", "dose": ibu_now})
        else:
            log.append({"t": now.isoformat(), "drug":"IBU", "dose": ibu_now})

    now = _now_kst()
    apap_24h = sum(x["dose"] for x in log if x.get("drug")=="APAP" and (now - _dt.datetime.fromisoformat(x["t"])).total_seconds() <= 24*3600)
    ibu_24h  = sum(x["dose"] for x in log if x.get("drug")=="IBU"  and (now - _dt.datetime.fromisoformat(x["t"])).total_seconds() <= 24*3600)
    if apap_24h > limit_apap:
        st.error(f"APAP 24h 총 {apap_24h} mg (한계 {limit_apap} mg) 초과")
    if ibu_24h > limit_ibu:
        st.error(f"IBU 24h 총 {ibu_24h} mg (한계 {limit_ibu} mg) 초과")

    last_apap = next((x for x in reversed(log) if x.get("drug")=="APAP"), None)
    if last_apap:
        next_t = _dt.datetime.fromisoformat(last_apap["t"]) + _dt.timedelta(hours=4)
        st.download_button("APAP 다음 복용 .ics", data=_ics("APAP next dose", next_t),
                           file_name="apap_next.ics", mime="text/calendar", key=wkey("apap_ics"))
    last_ibu = next((x for x in reversed(log) if x.get("drug")=="IBU"), None)
    if last_ibu:
        next_t = _dt.datetime.fromisoformat(last_ibu["t"]) + _dt.timedelta(hours=6)
        st.download_button("IBU 다음 복용 .ics", data=_ics("IBU next dose", next_t),
                           file_name="ibu_next.ics", mime="text/calendar", key=wkey("ibu_ics"))