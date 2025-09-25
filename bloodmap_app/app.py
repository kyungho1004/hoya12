# app.py — Stable Form-Gated UI [PATCH v2025-09-25-2]
import datetime as _dt
import streamlit as st

# ---------- Banner (safe fallback) ----------
try:
    from branding import render_deploy_banner
except Exception:
    def render_deploy_banner(*a, **k): 
        pass

st.set_page_config(page_title="Bloodmap — Stable", layout="wide")
st.title("Bloodmap — 안정화 패치")
render_deploy_banner("https://bloodmap.streamlit.app/", "한국시간 기준 · 세포/면역치료 비표기 · 제작/자문: Hoya/GPT")

# ---------- Utils ----------
def wkey(name: str) -> str:
    who = st.session_state.get("key", "guest")
    return f"{who}:{name}"

def enko(en: str, ko: str) -> str:
    return f"{en} / {ko}" if ko else en

def _num(x):
    """문자→숫자 변환(콤마/공백 허용). 실패 시 None."""
    try:
        s = str(x).strip().replace(",", "")
        if s == "":
            return None
        return float(s)
    except Exception:
        return None

def egfr_2009(cr_mgdl: float, age: int, sex: str) -> float:
    """CKD-EPI (2009) – 간단 구현 (성별만 적용, 인종계수 없음)."""
    try:
        sex_f = (sex == "여")
        k = 0.7 if sex_f else 0.9
        a = -0.329 if sex_f else -0.411
        mn = min(cr_mgdl / k, 1)
        mx = max(cr_mgdl / k, 1)
        sex_fac = 1.018 if sex_f else 1.0
        val = 141 * (mn ** a) * (mx ** -1.209) * (0.993 ** age) * sex_fac
        return round(val, 1)
    except Exception:
        return 0.0

# ---------- Static data ----------
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
    ],
    "🧠 고형암 (Solid Tumors)": [
        ("Wilms Tumor", "윌름스 종양(신장)"),
        ("Neuroblastoma", "신경모세포종"),
    ],
    "🦴 육종 (Sarcoma)": [
        ("Osteosarcoma", "골육종"),
        ("Ewing Sarcoma", "유잉육종"),
    ],
    "🧩 희귀암 및 기타": [
        ("Langerhans Cell Histiocytosis (LCH)", "랜게르한스세포 조직구증"),
        ("Juvenile Myelomonocytic Leukemia (JMML)", "소아 골수단핵구성 백혈병"),
    ],
}

CHEMO_MAP = {
    "Acute Lymphoblastic Leukemia (ALL)": [
        "6-Mercaptopurine (메르캅토퓨린)",
        "Methotrexate (메토트렉세이트)",
        "Cytarabine/Ara-C (시타라빈)",
        "Vincristine (빈크리스틴)",
    ],
    "Acute Promyelocytic Leukemia (APL)": [
        "ATRA (트레티노인/베사노이드)",
        "Arsenic Trioxide (아르세닉 트리옥사이드)",
        "MTX (메토트렉세이트)",
        "6-MP (메르캅토퓨린)",
    ],
    "Acute Myeloid Leukemia (AML)": [
        "Ara-C (시타라빈)",
        "Daunorubicin (다우노루비신)",
        "Idarubicin (이다루비신)",
    ],
    "Chronic Myeloid Leukemia (CML)": [
        "Imatinib (이마티닙)",
        "Dasatinib (다사티닙)",
        "Nilotinib (닐로티닙)",
    ],
    "Diffuse Large B-cell Lymphoma (DLBCL)": ["R-CHOP", "R-EPOCH", "Polatuzumab combos"],
    "Burkitt Lymphoma": ["CODOX-M/IVAC"],
    "Hodgkin Lymphoma": ["ABVD"],
    "Wilms Tumor": ["Vincristine", "Dactinomycin", "Doxorubicin"],
    "Neuroblastoma": ["Cyclophosphamide", "Topotecan", "Cisplatin", "Etoposide"],
    "Osteosarcoma": ["MAP"],
    "Ewing Sarcoma": ["VDC/IE"],
    "LCH": ["Vinblastine", "Prednisone"],
    "JMML": ["Azacitidine", "SCT"],
}

# ---------- Sidebar ----------
with st.sidebar:
    st.header("프로필")
    st.session_state["key"] = st.text_input(
        "별명#PIN", 
        value=st.session_state.get("key", "guest"), 
        key=wkey("user_key")
    )
    st.caption("이 키는 저장/그래프 경로 네임스페이스로 사용됩니다.")

# ---------- Tabs ----------
t_home, t_labs, t_dx, t_chemo, t_report = st.tabs(
    ["🏠 홈", "🧪 피수치 입력", "🧬 암 선택", "💊 항암제", "📄 해석하기"]
)

# ---------- HOME ----------
with t_home:
    st.info("무한 재실행 방지: 모든 입력은 **폼 제출** 버튼을 눌러 저장됩니다. 결과는 '해석하기'에서만 생성됩니다.")

# ---------- LABS (FORM-GATED) ----------
with t_labs:
    st.subheader("피수치 (스피너 제거·문자 입력)")
    with st.form(key=wkey("form_labs")):
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            sex = st.radio("성별", ["여", "남"], horizontal=True, key=wkey("sex"))
        with col2:
            age_raw = st.text_input("나이(세)", value=str(st.session_state.get(wkey("age_val"), "")), placeholder="예: 40", key=wkey("age"))
        with col3:
            wt_raw = st.text_input("체중(kg)", value=str(st.session_state.get(wkey("wt_val"), "")), placeholder="예: 60.5", key=wkey("wt"))
        with col4:
            cr_raw = st.text_input("Cr (mg/dL)", value=str(st.session_state.get(wkey("cr_val"), "")), placeholder="예: 0.8", key=wkey("cr"))
        with col5:
            day = st.date_input("측정일", value=_dt.date.today(), key=wkey("date"))
        submitted = st.form_submit_button("저장")
    if submitted:
        age_val = _num(age_raw); wt_val = _num(wt_raw); cr_val = _num(cr_raw)
        if age_val is None or cr_val is None:
            st.error("나이/Cr는 숫자로 입력하세요.")
        else:
            st.session_state[wkey("age_val")] = int(age_val)
            st.session_state[wkey("wt_val")] = float(wt_val) if wt_val is not None else 0.0
            st.session_state[wkey("cr_val")] = float(cr_val)
            st.session_state[wkey("date_val")] = str(day)
            # 계산은 저장 시 1회
            egfr = egfr_2009(float(cr_val), int(age_val), sex)
            st.session_state[wkey("egfr")] = egfr
            st.success(f"저장됨 (eGFR {egfr} mL/min/1.73㎡)")
            # 최근 5개 버퍼
            st.session_state.setdefault("lab_rows", [])
            st.session_state["lab_rows"].append({
                "date": str(day), "sex": sex, "age": int(age_val),
                "weight(kg)": float(wt_val) if wt_val is not None else 0.0,
                "Cr(mg/dL)": float(cr_val), "eGFR": egfr
            })
            if len(st.session_state["lab_rows"]) > 50:
                st.session_state["lab_rows"] = st.session_state["lab_rows"][-50:]
    # 미리보기
    rows = st.session_state.get("lab_rows", [])
    if rows:
        st.write("최근 입력(최대 5개):")
        for r in rows[-5:]:
            st.write(r)

# ---------- DIAGNOSIS (INLINE RADIO) ----------
with t_dx:
    st.subheader("암 선택 — 일렬 라디오 2단")
    group = st.radio("카테고리", list(GROUPS.keys()), horizontal=True, key=wkey("dx_group"))
    labels = [enko(en, ko) for en, ko in GROUPS[group]]
    sel = st.radio("진단명", labels, horizontal=True, key=wkey("dx_sel"))
    with st.form(key=wkey("form_dx")):
        save_dx = st.form_submit_button("선택 저장")
    if save_dx:
        try:
            idx = labels.index(sel) if sel in labels else 0
        except Exception:
            idx = 0
        en_dx, ko_dx = GROUPS[group][idx]
        st.session_state["dx_en"] = en_dx
        st.session_state["dx_ko"] = ko_dx
        st.success(f"저장됨: {enko(en_dx, ko_dx)}")

# ---------- CHEMO (FORM-GATED) ----------
with t_chemo:
    st.subheader("항암제")
    en_dx = st.session_state.get("dx_en")
    ko_dx = st.session_state.get("dx_ko", "")
    if not en_dx:
        st.info("먼저 '암 선택'에서 진단을 저장하세요.")
    else:
        st.write(f"현재 진단: **{enko(en_dx, ko_dx)}**")
        suggestions = CHEMO_MAP.get(en_dx, CHEMO_MAP.get(ko_dx, []))
        with st.form(key=wkey("form_chemo")):
            picked = st.multiselect("항암제를 선택/추가", suggestions, default=suggestions, key=wkey("chemo_ms"))
            extra = st.text_input("추가 항암제(쉼표 구분)", key=wkey("chemo_extra"))
            save_chemo = st.form_submit_button("항암제 저장")
        if save_chemo:
            merged = picked[:]
            if extra.strip():
                for x in [t.strip() for t in extra.split(",") if t.strip()]:
                    if x not in merged:
                        merged.append(x)
            st.session_state["chemo_list"] = merged
            st.success("저장됨. '해석하기' 탭에서 확인하세요.")

# ---------- REPORT (EXPLICIT GATE) ----------
with t_report:
    st.subheader("해석하기 (버튼 누를 때만 생성)")
    with st.form(key=wkey("form_report")):
        make = st.form_submit_button("해석 생성")
    if make:
        dx = enko(st.session_state.get("dx_en", ""), st.session_state.get("dx_ko", ""))
        meds = st.session_state.get("chemo_list", [])
        rows = st.session_state.get("lab_rows", [])
        eg = st.session_state.get(wkey("egfr"))
        lines = []
        lines.append("# Bloodmap Report")
        lines.append(f"**진단명**: {dx if dx.strip() else '(미선택)'}")
        lines.append("")
        lines.append("## 항암제 요약")
        if meds:
            for m in meds: lines.append(f"- {m}")
        else:
            lines.append("- (없음)")
        if rows:
            lines.append("")
            lines.append("## 최근 검사 (최대 5개)")
            head = ["date","sex","age","weight(kg)","Cr(mg/dL)","eGFR"]
            lines.append("| " + " | ".join(head) + " |")
            lines.append("|" + "|".join(["---"] * len(head)) + "|")
            for r in rows[-5:]:
                lines.append("| " + " | ".join(str(r.get(k,'')) for k in head) + " |")
        if eg is not None:
            lines.append("")
            lines.append(f"**eGFR 요약**: {eg} mL/min/1.73㎡")
        lines.append("")
        lines.append(f"_생성 시각(KST): {_dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_")
        md = "\n".join(lines)
        st.code(md, language="markdown")
        st.download_button("💾 보고서 .md 다운로드", data=md.encode("utf-8"),
                           file_name="bloodmap_report.md", mime="text/markdown", key=wkey("dl_md"))
