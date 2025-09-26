
# app_master4.py — Bloodmap (MASTER++++)
import os, json, time, hashlib, importlib.util
import datetime as _dt
import pandas as pd
import streamlit as st

# ---------- Safe banner ----------
try:
    from branding import render_deploy_banner
except Exception:
    def render_deploy_banner(*a, **k): return None

# ---------- eGFR utils ----------
try:
    from utils_egfr import egfr_ckd_epi_2021, egfr_schwartz_peds
except Exception:
    def egfr_ckd_epi_2021(cr_mgdl: float, age: int, sex_female: bool) -> float:
        kappa = 0.7 if sex_female else 0.9
        alpha = -0.241 if sex_female else -0.302
        min_scr = min(cr_mgdl / kappa, 1.0)
        max_scr = max(cr_mgdl / kappa, 1.0)
        coef_sex = 1.012 if sex_female else 1.0
        return round(142.0 * (min_scr ** alpha) * (max_scr ** -1.200) * (0.9938 ** age) * coef_sex, 1)
    def egfr_schwartz_peds(cr_mgdl: float, height_cm: float, k: float = 0.413) -> float:
        if cr_mgdl <= 0: return 0.0
        return round(k * float(height_cm) / float(cr_mgdl), 1)

# ---------- Special tests loader (patched preferred) ----------
def _load_special_tests():
    cand = "/mnt/data/special_tests.patched.py"
    if os.path.exists(cand):
        spec = importlib.util.spec_from_file_location("special_tests_patched", cand)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    else:
        try:
            import special_tests as mod
            return mod
        except Exception:
            return None
STMOD = _load_special_tests()

st.set_page_config(page_title="Bloodmap (MASTER++++)", layout="wide")
st.title("Bloodmap (MASTER++++)")
render_deploy_banner("https://bloodmap.streamlit.app/", "제작: Hoya/GPT · 자문: Hoya/GPT")


# ===== Storage path resolver (portable) =====
import os, tempfile, pathlib as _pl

def _pick_base_dir() -> str:
    # Priority: env → /mnt/data → /mount/data → ~/.local/share/bloodmap → ./data → temp
    candidates = []
    env = os.environ.get("BLOODMAP_DATA_DIR")
    if env: candidates.append(env)
    candidates += ["/mnt/data", "/mount/data",
                   str(_pl.Path.home()/".local/share/bloodmap"),
                   str(_pl.Path.cwd()/ "data"),
                   str(_pl.Path(tempfile.gettempdir())/ "bloodmap")]
    for base in candidates:
        try:
            _pl.Path(base).mkdir(parents=True, exist_ok=True)
            testfile = _pl.Path(base)/".write_test"
            with open(testfile, "w") as f: f.write("ok")
            testfile.unlink(missing_ok=True)
            return base
        except Exception:
            continue
    # Last resort: current dir (might be read-only)
    return str(_pl.Path.cwd())

BLOODMAP_BASE = _pick_base_dir()
def bloodmap_path(*parts:str) -> str:
    p = _pl.Path(BLOODMAP_BASE).joinpath(*parts)
    p.parent.mkdir(parents=True, exist_ok=True)
    return str(p)


# ---------- Helpers & Paths ----------
def wkey(name:str)->str:
    who = st.session_state.get("key","guest")
    return f"{who}:{name}"

def enko(en:str, ko:str)->str:
    return f"{en} / {ko}" if ko else en

def _now_kst_str():
    return _dt.datetime.now().strftime("%Y-%m-%d %H:%M")

SAVE_DIR = bloodmap_path("bloodmap_graph")
CARE_DIR = bloodmap_path("care_log")
PROF_DIR = bloodmap_path("profile")
MET_DIR  = bloodmap_path("metrics")

# ---------- Sidebar (프로필 + PIN + 방문자 통계 + 단위 가드) ----------
with st.sidebar:
    st.header("프로필")
    st.session_state["key"] = st.text_input("별명#PIN 키", value=st.session_state.get("key","guest"), key=wkey("user_key"))
    uid = st.session_state["key"].strip() or "guest"
    st.caption("별명은 저장/CSV 경로 키로 쓰입니다.")

    # PIN 잠금
    pin_path = os.path.join(PROF_DIR, f"{uid}.pin")
    pin_set = os.path.exists(pin_path)
    with st.expander("🔒 PIN 잠금", expanded=False):
        if not pin_set:
            new_pin = st.text_input("새 PIN (4~6자리)", type="password", key=wkey("setpin"))
            if st.button("PIN 설정", key=wkey("btn_setpin")):
                if new_pin and new_pin.isdigit() and 4 <= len(new_pin) <= 6:
                    h = hashlib.sha256(new_pin.encode()).hexdigest()
                    json.dump({"hash":h}, open(pin_path,"w"))
                    st.success("PIN 설정 완료")
                else:
                    st.error("4~6자리 숫자만 허용")
            st.caption("※ PIN 미설정 상태에서는 가드 없이 사용됩니다.")
            st.session_state["pin_ok"] = True  # 미설정 시 기본 허용
        else:
            chk_pin = st.text_input("PIN 확인", type="password", key=wkey("chkpin"))
            ok = False
            try:
                saved = json.load(open(pin_path,"r")).get("hash","")
                ok = (hashlib.sha256(chk_pin.encode()).hexdigest()==saved)
            except Exception:
                pass
            st.session_state["pin_ok"] = ok
            st.caption("잠금 해제 상태: " + ("✅" if ok else "🔒"))

    # 단위 가드 토글
    st.subheader("단위 가드")
    unit_cr = st.selectbox("Cr 입력 단위", ["mg/dL","μmol/L"], key=wkey("unit_cr"))
    st.caption("※ μmol/L 입력 시 자동으로 mg/dL로 변환되어 계산됩니다. (mg/dL = μmol/L ÷ 88.4)")

    # 방문자 통계
    met_path = os.path.join(MET_DIR, "visits.json")
    try:
        D = json.load(open(met_path,"r",encoding="utf-8"))
    except Exception:
        D = {"unique":[], "visits":[]}
    if uid not in D["unique"]:
        D["unique"].append(uid)
    D["visits"].append({"uid": uid, "ts": int(time.time())})
    json.dump(D, open(met_path,"w",encoding="utf-8"), ensure_ascii=False)
    today = _dt.datetime.now().strftime("%Y-%m-%d")
    today_count = sum(1 for v in D["visits"] if _dt.datetime.fromtimestamp(v["ts"]).strftime("%Y-%m-%d")==today)
    st.caption(f"👥 오늘: {today_count} · 누적 고유: {len(D['unique'])} · 총 방문: {len(D['visits'])}")

# ---------- Groups / Chemo ----------
GROUPS = {
    "🩸 혈액암 (Leukemia)": [
        ("Acute Lymphoblastic Leukemia (ALL)", "급성 림프모구 백혈병"),
        ("Acute Myeloid Leukemia (AML)", "급성 골수성 백혈병"),
        ("Acute Promyelocytic Leukemia (APL)", "급성 전골수성 백혈병"),
        ("Chronic Myeloid Leukemia (CML)", "만성 골수성 백혈병"),
    ],
    "🧬 림프종 (Lymphoma)": [
        ("Hodgkin Lymphoma", "호지킨 림프종"),
        ("Diffuse Large B-cell Lymphoma (DLBCL)", "미만성 거대 B세포 림프종"),
        ("Burkitt Lymphoma", "버킷 림프종"),
        ("T-cell Lymphoma", "T세포 림프종"),
    ],
    "🏥 고형암 (Solid Tumors)": [
        ("Neuroblastoma", "신경아세포종"),
        ("Wilms Tumor (Nephroblastoma)", "윌름스 종양"),
        ("Hepatoblastoma", "간모세포종"),
        ("Medulloblastoma", "수모세포종"),
        ("Retinoblastoma", "망막아세포종"),
    ],
    "🦴 육종 (Sarcoma)": [
        ("Osteosarcoma", "골육종"),
        ("Ewing Sarcoma", "유잉 육종"),
        ("Rhabdomyosarcoma", "횡문근육종"),
        ("Synovial Sarcoma", "윤활막육종"),
    ],
}
CHEMO_MAP = {
    "Acute Lymphoblastic Leukemia (ALL)": ["6-Mercaptopurine (6-MP)","Methotrexate (MTX)","Prednisone","Vincristine"],
    "Acute Myeloid Leukemia (AML)": ["Cytarabine (Ara-C)","Daunorubicin","Idarubicin","Etoposide"],
    "Acute Promyelocytic Leukemia (APL)": ["ATRA (Tretinoin, 베사노이드)","Arsenic Trioxide","MTX","6-MP"],
    "Chronic Myeloid Leukemia (CML)": ["Imatinib","Dasatinib","Nilotinib"],
    "Neuroblastoma": ["Cyclophosphamide","Topotecan","Cisplatin","Etoposide"],
    "Wilms Tumor (Nephroblastoma)": ["Vincristine","Dactinomycin","Doxorubicin"],
    "Osteosarcoma": ["MAP"], "Ewing Sarcoma": ["VDC/IE"],
    "Hodgkin Lymphoma": ["ABVD"], "Diffuse Large B-cell Lymphoma (DLBCL)": ["R-CHOP"],
}

# ---------- Tabs ----------
t_home, t_labs, t_dx, t_chemo, t_special, t_peds, t_import, t_report = st.tabs(
    ["🏠 홈","🧪 피수치 입력","🧬 암 선택","💊 항암제/해열제","🔬 특수검사","🧒 소아 추정","📥 CSV/엑셀","📄 보고서"]
)

with t_home:
    st.info("각 탭에 기본 입력창이 항상 표시됩니다. 외부 파일 없어도 작동합니다.")

# ---------- Labs + FN/전해질 배너 ----------

with t_labs:
    st.subheader("피수치 입력")
    # --- 기본 인구학/Cr 입력(단위 가드 반영) ---
    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: sex = st.selectbox("성별", ["여","남"], key=wkey("sex"))
    with c2: age = st.number_input("나이(세)", 0, 110, 40, key=wkey("age"))
    with c3: wt  = st.number_input("체중(kg)", 0.0, 300.0, 0.0, 0.5, key=wkey("wt"))

    # Creatinine with unit guard (sidebar toggle exists in v4_fix? guard local fallback)
    unit_cr = st.session_state.get(wkey("unit_cr")) or st.session_state.get("unit_cr") or "mg/dL"
    if unit_cr == "μmol/L":
        cr_umol = st.number_input("Cr (μmol/L)", 0.0, 1768.0, 70.0, 1.0, key=wkey("cr_umol"))
        cr = round(cr_umol / 88.4, 3)
        st.caption(f"자동 변환 → Cr {cr} mg/dL")
    else:
        cr  = st.number_input("Cr (mg/dL)", 0.0, 20.0, 0.8, 0.1, key=wkey("cr_mgdl"))

    with c5: day = st.date_input("측정일", value=_dt.date.today(), key=wkey("date"))

    # --- 전해질/혈구/간/당/단백 패널 ---
    e1,e2,e3 = st.columns(3)
    with e1:
        Na = st.number_input("Na (mEq/L)", 100.0, 180.0, 140.0, 0.1, key=wkey("Na"))
        K  = st.number_input("K (mEq/L)", 2.0, 10.0, 4.0, 0.1, key=wkey("K"))
        Alb = st.number_input("Albumin (g/dL)", 1.0, 6.0, 4.0, 0.1, key=wkey("Alb"))
    with e2:
        # Glucose unit guard
        g_unit = st.selectbox("Glucose 단위", ["mg/dL","mmol/L"], index=0, key=wkey("glu_unit"))
        if g_unit == "mmol/L":
            glu_mmol = st.number_input("Glucose (mmol/L)", 0.0, 50.0, 5.5, 0.1, key=wkey("glu_mmol"))
            Glucose = round(glu_mmol * 18.0, 1)  # to mg/dL
            st.caption(f"자동 변환 → {Glucose} mg/dL")
        else:
            Glucose = st.number_input("Glucose (mg/dL)", 0.0, 1000.0, 95.0, 1.0, key=wkey("glu_mg"))
        # Phosphate unit guard
        p_unit = st.selectbox("P 단위", ["mg/dL","mmol/L"], index=0, key=wkey("p_unit"))
        if p_unit == "mmol/L":
            p_mmol = st.number_input("P (mmol/L)", 0.0, 5.0, 1.2, 0.1, key=wkey("p_mmol"))
            P = round(p_mmol * 3.1, 2)  # to mg/dL
            st.caption(f"자동 변환 → {P} mg/dL")
        else:
            P = st.number_input("P (mg/dL)", 0.0, 20.0, 3.5, 0.1, key=wkey("p_mg"))
    with e3:
        # Calcium unit guard (+ corrected Ca)
        ca_unit = st.selectbox("Calcium 단위", ["mg/dL","mmol/L"], index=0, key=wkey("ca_unit"))
        if ca_unit == "mmol/L":
            ca_mmol = st.number_input("Calcium (mmol/L)", 0.0, 5.0, 2.3, 0.01, key=wkey("ca_mmol"))
            Ca = round(ca_mmol * 4.0, 2)  # approx factor 4.0
            st.caption(f"자동 변환 → {Ca} mg/dL")
        else:
            Ca = st.number_input("Calcium (mg/dL)", 0.0, 20.0, 9.2, 0.1, key=wkey("ca_mg"))
        AST = st.number_input("AST (U/L)", 0.0, 10000.0, 28.0, 1.0, key=wkey("AST"))
        ALT = st.number_input("ALT (U/L)", 0.0, 10000.0, 30.0, 1.0, key=wkey("ALT"))

    b1,b2,b3 = st.columns(3)
    with b1:
        WBC = st.number_input("WBC (10^3/µL)", 0.0, 500.0, 6.0, 0.1, key=wkey("WBC"))
    with b2:
        Hb = st.number_input("Hb (g/dL)", 0.0, 30.0, 12.5, 0.1, key=wkey("Hb"))
    with b3:
        PLT = st.number_input("PLT (10^3/µL)", 0.0, 2000.0, 250.0, 1.0, key=wkey("PLT"))
    CRP = st.number_input("CRP (mg/dL)", 0.0, 50.0, 0.2, 0.1, key=wkey("CRP"))

    # eGFR — CKD-EPI 2021 (adult) / Schwartz (peds)
    is_peds = int(age) < 18
    if is_peds:
        ht = st.number_input("키(cm)", 40.0, 220.0, 120.0, 0.5, key=wkey("height"))
        egfr = egfr_schwartz_peds(cr, float(ht))
        st.metric("eGFR (Schwartz, 소아)", f"{egfr} mL/min/1.73㎡")
    else:
        egfr = egfr_ckd_epi_2021(cr, int(age), sex == "여")
        st.metric("eGFR (CKD-EPI 2021)", f"{egfr} mL/min/1.73㎡")

    # 보정 칼슘
    Ca_corr = None
    try:
        Ca_corr = round(Ca + 0.8*(4.0 - Alb), 2)
        st.caption(f"보정 칼슘: {Ca_corr} mg/dL (Alb=4 기준)")
    except Exception:
        pass

    # 기록 버튼 → CSV 보존
    st.session_state.setdefault("lab_rows", [])
    if st.button("➕ 현재 값 추가", key=wkey("add_row")):
        st.session_state["lab_rows"].append({
            "date": str(day),
            "sex": sex, "age": int(age), "weight(kg)": wt,
            "Cr(mg/dL)": cr, "eGFR": egfr, "Na": Na, "K": K, "P(mg/dL)": P,
            "Alb(g/dL)": Alb, "Ca(mg/dL)": Ca, "Ca_corr(mg/dL)": Ca_corr,
            "AST": AST, "ALT": ALT, "Glucose(mg/dL)": Glucose,
            "WBC(1e3/uL)": WBC, "Hb(g/dL)": Hb, "PLT(1e3/uL)": PLT, "CRP(mg/dL)": CRP, "ANC": int(st.session_state.get(wkey("ANC"), 1500))
        })
        # Persist
        uid = st.session_state.get("key","guest").strip() or "guest"
        csv_path = os.path.join(SAVE_DIR, f"{uid}.labs.csv")
        import pandas as _pd
        _df = _pd.DataFrame(st.session_state["lab_rows"])
        if not _df.empty:
            _df["date"] = _df["date"].astype(str)
            _df.sort_values("date", inplace=True)
            _df.to_csv(csv_path, index=False)

    rows = st.session_state["lab_rows"]
    # Δ 표시
    if rows:
        import pandas as _pd
        df = _pd.DataFrame(rows)
        def delta(col, fmt="{:+.2f}"):
            try:
                return fmt.format(float(df[col].iloc[-1]) - float(df[col].iloc[-2]))
            except Exception:
                return ""
        st.caption(f"Δ eGFR: {delta('eGFR', '{:+.1f}')} · Δ Cr: {delta('Cr(mg/dL)')} · Δ Na: {delta('Na')} · Δ K: {delta('K')}")

    # --- 핵심 패널 요약 테이블 (아이콘/색상) ---
    def flag(val, lo, hi, unit=""):
        try:
            v = float(val)
        except Exception:
            return "⚪", f"{val}{unit}"
        if v < lo:  return "🔴", f"{v}{unit}"
        if v > hi:  return "🔴", f"{v}{unit}"
        mid_margin = (hi-lo)*0.1
        if v < lo+mid_margin or v > hi-mid_margin:
            return "🟡", f"{v}{unit}"
        return "🟢", f"{v}{unit}"

    # 단순 성인 레퍼런스 (프로젝트 표준과 맞추기 쉽게 구성)
    refs = {
        "Na": (135, 145), "K": (3.5, 5.1), "P(mg/dL)": (2.5, 4.5), "Alb(g/dL)": (3.5, 5.0),
        "Ca(mg/dL)": (8.6, 10.2), "AST": (0, 40), "ALT": (0, 41), "Glucose(mg/dL)": (70, 140),
        "Cr(mg/dL)": (0.6, 1.2), "WBC(1e3/uL)": (4.0, 11.0), "Hb(g/dL)": (11.5, 17.5),
        "PLT(1e3/uL)": (150, 450), "CRP(mg/dL)": (0, 0.5), "ANC": (1500, 8000)
    }
    latest = {}
    if rows:
        latest = rows[-1]
        st.markdown("#### 핵심 패널 요약")
        data = []
        order = ["Na","K","P(mg/dL)","Alb(g/dL)","Ca(mg/dL)","AST","ALT","Glucose(mg/dL)","Cr(mg/dL)","WBC(1e3/uL)","Hb(g/dL)","PLT(1e3/uL)","CRP(mg/dL)","ANC"]
        names = {"Na":"Na","K":"K","P(mg/dL)":"P","Alb(g/dL)":"Albumin","Ca(mg/dL)":"Ca","AST":"AST","ALT":"ALT","Glucose(mg/dL)":"Glucose","Cr(mg/dL)":"Cr","WBC(1e3/uL)":"WBC","Hb(g/dL)":"Hb","PLT(1e3/uL)":"PLT","CRP(mg/dL)":"CRP","ANC":"ANC"}
        for k in order:
            lo,hi = refs[k]
            icon, txt = flag(latest.get(k), lo, hi)
            data.append(f"{names[k]} {txt} {icon}")
        st.write(", ".join(data))

    # 🚨 FN/전해질 응급 배너 (재사용)
    show_fn = False
    # care_log 기반은 Report/chemo에서 활용, 여기선 현재 입력값으로 판정
    if latest:
        try:
            if float(latest.get("ANC", 1500)) < 500:
                # care log 발열 여부는 별도 배너에서 확인
                pass
        except Exception:
            pass
    if Na < 125 or Na > 155 or K >= 6.0:
        st.error("🚨 전해질 위기치: Na<125 또는 >155, K≥6.0 → **즉시 평가 권고**")

# ---------- Diagnosis ----------
with t_dx:
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

# ---------- Chemo + Antipyretic Guardrails (APAP/IBU) ----------
def _care_path(uid:str)->str:
    return os.path.join(CARE_DIR, f"{uid}.json")

def _load_log(uid:str):
    p = _care_path(uid)
    try: return json.load(open(p,"r",encoding="utf-8"))
    except: return []

def _save_log(uid:str, L):
    json.dump(L, open(_care_path(uid),"w",encoding="utf-8"), ensure_ascii=False)

def _ics_event(summary:str, dt: _dt.datetime, duration_min:int=0)->str:
    # Minimal single-event ICS
    dtstart = dt.strftime("%Y%m%dT%H%M%S")
    ics = [
        "BEGIN:VCALENDAR","VERSION:2.0","PRODID:-//Bloodmap//KST//KR","CALSCALE:GREGORIAN",
        "BEGIN:VEVENT",
        f"UID:{int(time.time())}@bloodmap",
        f"DTSTAMP:{dtstart}",
        f"DTSTART:{dtstart}",
        f"SUMMARY:{summary}",
        "END:VEVENT","END:VCALENDAR"
    ]
    return "\r\n".join(ics)

with t_chemo:
    st.subheader("항암제 및 해열제")
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

    st.markdown("---")
    st.subheader("해열제 가드레일(APAP/IBU)")
    uid = st.session_state.get("key","guest").strip() or "guest"

    # PIN 보호: PIN 설정되어 있고 잠금 해제 안 됐다면 차단
    pin_path = os.path.join(PROF_DIR, f"{uid}.pin")
    if os.path.exists(pin_path) and not st.session_state.get("pin_ok", False):
        st.warning("🔒 PIN 해제 필요: 해열제 기록·케어로그 접근이 잠겨 있습니다.")
    else:
        log = _load_log(uid)
        now = time.time()
        def total_24h(drug):
            mg = 0.0
            for x in log:
                if x.get("drug")==drug and (now - x.get("ts",0) <= 24*3600):
                    mg += float(x.get("dose_mg", 0))
            return mg
        def last_ts(drug):
            ts = 0
            for x in log:
                if x.get("drug")==drug:
                    ts = max(ts, x.get("ts",0))
            return ts

        # 입력 보조(체중/시럽 농도)
        cc1,cc2,cc3 = st.columns(3)
        with cc1: syrup = st.selectbox("시럽 농도", ["없음/정제","APAP 160 mg/5mL","IBU 100 mg/5mL"], key=wkey("syrup"))
        with cc2: dose_ml = st.number_input("투여량(mL)", 0.0, 100.0, 0.0, 0.5, key=wkey("dose_ml"))
        with cc3: dose_mg_manual = st.number_input("직접 입력: 용량(mg)", 0.0, 4000.0, 0.0, 10.0, key=wkey("dose_mg_manual"))
        def calc_mg(drug):
            if dose_mg_manual>0: return float(dose_mg_manual)
            if "160 mg/5mL" in syrup and drug=="APAP": return dose_ml * (160.0/5.0)
            if "100 mg/5mL" in syrup and drug=="IBU":  return dose_ml * (100.0/5.0)
            return 0.0

        # 규칙
        wt = st.session_state.get("weight(kg)", 0.0) or st.session_state.get(wkey("wt"), 0.0)
        try: wt = float(wt)
        except: wt = 0.0
        apap_daily_max = max(75.0*wt, 0.0)
        ibu_daily_max  = max(30.0*wt, 0.0)
        if wt >= 40:
            apap_daily_max = min(apap_daily_max, 4000.0)
            ibu_daily_max  = min(ibu_daily_max, 1200.0)

        cool_apap = 4*3600
        cool_ibu  = 6*3600
        last_apap = last_ts("APAP")
        last_ibu  = last_ts("IBU")
        can_apap  = (time.time() - last_apap) >= cool_apap
        can_ibu   = (time.time() - last_ibu) >= cool_ibu

        # PLT / eGFR
        plt_input = st.number_input("최근 혈소판(PLT, x10^3/µL)", 0, 1000, value=200, key=wkey("plt_v"))
        last_egfr = None
        if st.session_state.get("lab_rows"):
            try: last_egfr = st.session_state["lab_rows"][-1].get("eGFR")
            except: pass
        if last_egfr is None: last_egfr = 100.0
        if last_egfr < 60:
            st.warning("eGFR<60: IBU 사용 시 **신장 기능 주의**")

        # 24h 요약 표시
        colsum1, colsum2 = st.columns(2)
        with colsum1:
            st.info(f"APAP 24h 합계: {total_24h('APAP'):.0f} mg / 한도 {apap_daily_max:.0f} mg")
        with colsum2:
            st.info(f"IBU  24h 합계: {total_24h('IBU'):.0f} mg / 한도 {ibu_daily_max:.0f} mg")

        # 버튼 + 기록
        colA, colB = st.columns(2)
        with colA:
            dose_apap = calc_mg("APAP")
            disabledA = (dose_apap<=0 or not can_apap or (total_24h('APAP')+dose_apap>apap_daily_max))
            clickedA = st.button(f"APAP 기록(+{dose_apap:.0f} mg)", key=wkey("btn_apap"), disabled=disabledA, help="쿨다운 4h, 24h 총량 한도 적용")
            if clickedA:
                if not can_apap: st.error("APAP 쿨다운 미충족(마지막 복용 후 4시간 필요)")
                elif total_24h('APAP')+dose_apap>apap_daily_max: st.error("APAP 24시간 총량 초과 — 기록 차단")
                else:
                    log.append({"ts": time.time(), "kind":"antipyretic", "drug":"APAP", "dose_mg": dose_apap, "KST": _now_kst_str()})
                    _save_log(uid, log)
                    st.success("APAP 기록됨")
        with colB:
            dose_ibu = calc_mg("IBU")
            plt_block = plt_input < 50
            disabledB = (dose_ibu<=0 or not can_ibu or (total_24h('IBU')+dose_ibu>ibu_daily_max) or plt_block)
            clickedB = st.button(f"IBU 기록(+{dose_ibu:.0f} mg)", key=wkey("btn_ibu"), disabled=disabledB, help="쿨다운 6h, 24h 총량, PLT<50k 차단")
            if clickedB:
                if plt_block: st.error("IBU 차단: PLT < 50k")
                elif not can_ibu: st.error("IBU 쿨다운 미충족(마지막 복용 후 6시간 필요)")
                elif total_24h('IBU')+dose_ibu>ibu_daily_max: st.error("IBU 24시간 총량 초과 — 기록 차단")
                else:
                    log.append({"ts": time.time(), "kind":"antipyretic", "drug":"IBU", "dose_mg": dose_ibu, "KST": _now_kst_str()})
                    _save_log(uid, log)
                    st.success("IBU 기록됨")

        # 다음 복용 .ics 내보내기
        next_apap = _dt.datetime.now() if last_apap==0 else _dt.datetime.fromtimestamp(last_apap) + _dt.timedelta(seconds=cool_apap)
        next_ibu  = _dt.datetime.now() if last_ibu==0  else _dt.datetime.fromtimestamp(last_ibu)  + _dt.timedelta(seconds=cool_ibu)
        apap_ics = _ics_event("다음 APAP 복용 가능", next_apap)
        ibu_ics  = _ics_event("다음 IBU 복용 가능",  next_ibu)
        st.download_button("📅 다음 APAP 복용 .ics", data=apap_ics.encode("utf-8"), file_name="next_APAP.ics", mime="text/calendar", key=wkey("ics_apap"))
        st.download_button("📅 다음 IBU 복용 .ics",  data=ibu_ics.encode("utf-8"),  file_name="next_IBU.ics",  mime="text/calendar", key=wkey("ics_ibu"))

# ---------- Special Tests ----------
with t_special:
    st.subheader("특수검사")
    if STMOD and hasattr(STMOD, "special_tests_ui"):
        lines = STMOD.special_tests_ui()
        st.session_state["special_lines"] = lines
    else:
        st.warning("특수검사 모듈을 불러오지 못했습니다. (patched 또는 기본 모듈 확인)")

# ---------- Peds Inference ----------
with t_peds:
    st.subheader("소아 질병 추정(간단 판별)")
    colA, colB, colC, colD = st.columns(4)
    with colA: d_cnt = st.number_input("설사 횟수(24h)", 0, 30, 0, key=wkey("p_dcnt"))
    with colB: v_cnt2h = st.number_input("구토 횟수(2h)", 0, 20, 0, key=wkey("p_v2h"))
    with colC: fever = st.number_input("최고 체온(℃)", 35.0, 42.0, 37.0, 0.1, key=wkey("p_fever"))
    with colD: cough = st.selectbox("기침 정도", ["없음","약간","보통","심함"], key=wkey("p_cough"))
    sore = st.selectbox("인후통", ["없음","약간","보통","심함"], key=wkey("p_throat"))
    likely = None; notes = []
    if d_cnt >= 4 and fever < 38.0 and cough in ("없음","약간","보통") and sore in ("없음","약간","보통"):
        likely = "바이러스성 장염(로타/노로/아데노40/41 등) 우선"; notes.append("수분보충(ORS 10–20 mL/kg), 구토 시 5–10 mL q5min 권장")
    elif fever >= 38.5 and (cough == "심함" or sore == "심함"): likely = "상기도염/편도염 가능"
    elif v_cnt2h >= 3: likely = "구토성 위장염 가능"
    if likely: st.success(f"우선 추정: **{likely}**"); [st.caption('• '+n) for n in notes]
    else: st.info("입력값이 기준에 해당하지 않습니다. 추가 증상/경과를 확인하세요.")
    st.caption("※ 이 해석은 참고용이며, 정확한 진단은 의료진의 판단에 따릅니다.")

# ---------- CSV/엑셀 가져오기 (PIN 보호) ----------
with t_import:
    st.subheader("CSV/엑셀 가져오기 (PIN 보호)")
    uid = st.session_state.get("key","guest").strip() or "guest"
    if os.path.exists(os.path.join(PROF_DIR, f"{uid}.pin")) and not st.session_state.get("pin_ok", False):
        st.warning("🔒 PIN 해제 필요: CSV/엑셀 병합이 잠겨 있습니다.")
    else:
        csv_path = os.path.join(SAVE_DIR, f"{uid}.labs.csv")
        up = st.file_uploader("CSV 또는 XLSX 업로드", type=["csv","xlsx"], key=wkey("uploader"))
        if up is not None:
            try:
                if up.name.lower().endswith(".xlsx"): dfu = pd.read_excel(up)
                else: dfu = pd.read_csv(up)
                st.write("미리보기:", dfu.head())
                std_cols = ["date","sex","age","weight(kg)","Cr(mg/dL)","eGFR","Na","K","ANC","WBC","Hb","PLT","CRP"]
                map_sel = {}
                for c in std_cols:
                    map_sel[c] = st.selectbox(f"매핑: {c}", ["(없음)"] + list(dfu.columns),
                                              index=(list(dfu.columns).index(c)+1 if c in dfu.columns else 0),
                                              key=wkey(f"map_{c}"))
                if st.button("병합 저장", key=wkey("merge")):
                    out = pd.read_csv(csv_path) if os.path.exists(csv_path) else pd.DataFrame(columns=std_cols)
                    add = pd.DataFrame({k: (dfu[v] if v!="(없음)" else None) for k,v in map_sel.items()})
                    merged = pd.concat([out, add], ignore_index=True)
                    if "date" in merged.columns:
                        merged["date"] = merged["date"].astype(str)
                        merged = merged.sort_values("date")
                    merged.to_csv(csv_path, index=False)
                    st.success("병합 완료 — 그래프/Δ 즉시 반영됨")
            except Exception as e:
                st.error(f"가져오기 실패: {e}")

# ---------- Report (ER PDF에 위험 배너/24h 해열제 요약 동시 반영) ----------
with t_report:
    st.subheader("보고서 (.md)")
    dx = enko(st.session_state.get("dx_en",""), st.session_state.get("dx_ko",""))
    meds = st.session_state.get("chemo_list", [])
    rows = st.session_state.get("lab_rows", [])
    spec_lines = st.session_state.get("special_lines", [])

    # 24h antipyretic summary
    uid = st.session_state.get("key","guest").strip() or "guest"
    def _load_log(uid:str):
        p = os.path.join(CARE_DIR, f"{uid}.json")
        try: return json.load(open(p,"r",encoding="utf-8"))
        except: return []
    log = _load_log(uid)
    now = time.time()
    def total_24h(drug):
        mg = 0.0
        for x in log:
            if x.get("drug")==drug and (now - x.get("ts",0) <= 24*3600):
                mg += float(x.get("dose_mg", 0))
        return mg

    # 위험 배너 판정 재사용
    Na = rows[-1].get("Na") if rows else None
    K  = rows[-1].get("K")  if rows else None
    ANC = rows[-1].get("ANC") if rows else None
    fn_flag = False
    try:
        clog = json.load(open(os.path.join(CARE_DIR, f"{uid}.json"),"r",encoding="utf-8"))
        recent_fever = any((x.get("kind")=="fever" and (now - x.get("ts",0) <= 24*3600)) for x in clog)
        if recent_fever and (ANC is not None and ANC < 500):
            fn_flag = True
    except Exception:
        pass
    ele_flag = False
    if Na is not None and (Na < 125 or Na > 155): ele_flag = True
    if K  is not None and (K >= 6.0): ele_flag = True

    lines = []
    # 응급도
    lines.append("## 🆘 증상 기반 응급도(피수치 없이)")
    lines += [
        "- 혈변/검은변, 초록 구토, 2시간 구토≥3회, 24시간 설사≥6회, 고열(≥39℃)은 **즉시 평가 권고**",
        "- 일반 응급실 기준: 의식저하/경련/호흡곤란, 6h 무뇨·중증 탈수, 심한 복통/팽만/무기력"
    ]

    # 위험 배너(문서 반영)
    if fn_flag: lines.append("\n> 🚨 **FN 의심**: 지난 24h 발열 + ANC<500 → 즉시 진료 권고")
    if ele_flag: lines.append("\n> 🚨 **전해질 위기치**: Na<125/>155 또는 K≥6.0 → 즉시 평가 권고")

    # 선택 약물 부작용 — 요약 + 상세
    try:
        from ui_results import collect_top_ae_alerts, render_adverse_effects
        picks = st.session_state.get("chemo_list", [])
        top_alerts = collect_top_ae_alerts(picks, db=None) or []
        if top_alerts:
            lines.append("")
            lines.append("## 💊 선택 약물 부작용 — 중요 경고 요약")
            for t in top_alerts: lines.append(f"- {t}")
        if picks:
            lines.append("")
            lines.append("## 💊 선택 약물 부작용 — 상세")
            detail_md = render_adverse_effects(picks, db=None) or ""
            if detail_md: lines.append(detail_md)
    except Exception:
        pass

    # 진단/항암제
    lines.append("")
    lines.append("## 진단/항암제")
    lines.append(f"- 진단: {dx or '(미선택)'}")
    if meds:
        lines.append("- 항암제:")
        for m in meds: lines.append(f"  - {m}")

    # 최근 피수치
    if rows:
        head = ["date","sex","age","weight(kg)","Cr(mg/dL)","eGFR","Na","K","ANC"]
        lines.append("")
        lines.append("## 최근 피수치(최대 5행)")
        lines.append("| " + " | ".join(head) + " |")
        lines.append("|" + "|".join(["---"]*len(head)) + "|")
        for r in rows[-5:]:
            lines.append("| " + " | ".join(str(r.get(k,'')) for k in head) + " |")

    # 24h 해열제 요약(문서 반영)
    apap_sum = total_24h('APAP'); ibu_sum = total_24h('IBU')
    lines.append("")
    lines.append("## 최근 24h 해열제 요약")
    lines.append(f"- APAP 합계: {apap_sum:.0f} mg")
    lines.append(f"- IBU  합계: {ibu_sum:.0f} mg")

    # 특수검사
    if spec_lines:
        lines.append("")
        lines.append("## 특수검사 요약")
        for ln in spec_lines:
            lines.append("- " + ln if not ln.startswith("-") else ln)

    lines.append("")
    lines.append(f"_생성 시각: {_dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_")
    md = "\n".join(lines)
    st.code(md, language="markdown")

    # 다운로드
    st.download_button("💾 보고서 .md 다운로드", data=md.encode("utf-8"),
                       file_name="bloodmap_report.md", mime="text/markdown", key=wkey("dl_md"))
    try:
        from pdf_export import export_md_to_pdf
        pdf_bytes = export_md_to_pdf(md)
        st.download_button("🖨️ ER 원페이지 PDF", data=pdf_bytes,
                           file_name="bloodmap_ER.pdf", mime="application/pdf", key=wkey("dl_pdf"))
    except Exception:
        pass
