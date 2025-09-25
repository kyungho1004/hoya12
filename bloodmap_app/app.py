# app.py — Integrated Minimal App (Labs + DX + Chemo + Special Tests + Diet + AE Alerts)
# 한국시간(KST) 기준 / 세포·면역 치료 비표기 안내는 배포 배너에서 고지
import datetime as _dt
import os

import streamlit as st

# -------- Imports (safe try/except wrappers) --------
try:
    from branding import render_deploy_banner  # 배포 배너 (KST/비표기 안내 포함)
except Exception:
    def render_deploy_banner(*a, **k): 
        return None

try:
    from special_tests import special_tests_ui  # 특수검사 UI → lines(List[str]) 반환
except Exception:
    special_tests_ui = None

try:
    from lab_diet import lab_diet_guides      # 피수치 기반 식이가이드
except Exception:
    lab_diet_guides = None

try:
    from onco_map import build_onco_map, auto_recs_by_dx, dx_display
except Exception:
    build_onco_map = auto_recs_by_dx = dx_display = None

try:
    from drug_db import DRUG_DB, ensure_onco_drug_db, display_label
except Exception:
    DRUG_DB = {}
    def ensure_onco_drug_db(db): 
        return None
    def display_label(x, db=None): 
        return str(x)

try:
    from ui_results import collect_top_ae_alerts, render_adverse_effects, results_only_after_analyze
except Exception:
    def collect_top_ae_alerts(drug_keys, db=None): return []
    def render_adverse_effects(st, drug_keys, db): 
        for k in (drug_keys or []): st.write(f"- {k}")
    def results_only_after_analyze(st=None): return True

# Optional PDF export (reportlab 미설치 환경 대비)
try:
    from pdf_export import export_md_to_pdf
except Exception:
    export_md_to_pdf = None

# -------- Page config --------
st.set_page_config(page_title="Bloodmap (Integrated Minimal)", layout="wide")
st.title("Bloodmap (Integrated Minimal)")
render_deploy_banner("https://bloodmap.streamlit.app/", "제작: Hoya/GPT · 자문: Hoya/GPT")

# Optional CSS
_css_path = "/mnt/data/style.css"
if os.path.exists(_css_path):
    with open(_css_path, "r", encoding="utf-8") as _f:
        st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)

# -------- Drug DB bootstrap --------
try:
    ensure_onco_drug_db(DRUG_DB)  # ONCO MAP 참조 약물 자동 등록 & 한글 병기
except Exception:
    pass

# -------- Helpers --------
def wkey(name:str)->str:
    who = st.session_state.get("key","guest")
    return f"{who}:{name}"

def enko(en:str, ko:str)->str:
    return f"{en} / {ko}" if ko else en

def _bool(x): 
    return bool(st.session_state.get(x))

# -------- Diagnosis Groups (inline, 안전 기본셋) --------
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
        "6-Mercaptopurine (메르캅토퓨린)","Methotrexate (메토트렉세이트)","Cytarabine/Ara-C (시타라빈)","Vincristine (빈크리스틴)"],
    "Acute Promyelocytic Leukemia (APL)": [
        "ATRA (트레티노인/베사노이드)","Arsenic Trioxide (아르세닉 트리옥사이드)","MTX (메토트렉세이트)","6-MP (메르캅토퓨린)"],
    "Acute Myeloid Leukemia (AML)": [
        "Ara-C (시타라빈)","Daunorubicin (다우노루비신)","Idarubicin (이다루비신)","6-MP (6-머캅토퓨린)","MTX (메토트렉세이트)"],
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

# ===== Sidebar: Profile =====
with st.sidebar:
    st.header("프로필")
    st.session_state["key"] = st.text_input("별명#PIN", value=st.session_state.get("key","guest"), key=wkey("user_key"))
    st.caption("좌측 프로필은 저장/CSV 경로 키로 쓰입니다.")
    st.divider()
    st.checkbox("보고서는 '해석하기' 버튼 이후 노출", value=True, key=wkey("gate_tip"))

# ===== Tabs =====
t_home, t_labs, t_dx, t_chemo, t_special, t_report = st.tabs(
    ["🏠 홈","🧪 피수치 입력","🧬 암 선택","💊 항암제","🔬 특수검사","📄 보고서"]
)

with t_home:
    st.info("각 탭에 기본 입력창이 항상 표시됩니다. 외부 파일 없어도 작동합니다.")
    st.button("🔎 해석하기", key=wkey("analyze_btn"),
              on_click=lambda: st.session_state.__setitem__("analyzed", True))

with t_labs:
    st.subheader("피수치 입력")
    col1,col2,col3,col4,col5 = st.columns(5)
    with col1: sex = st.selectbox("성별", ["여","남"], key=wkey("sex"))
    with col2: age = st.number_input("나이(세)", 1, 110, 40, key=wkey("age"))
    with col3: wt  = st.number_input("체중(kg)", 0.0, 300.0, 0.0, 0.5, key=wkey("wt"))
    with col4: cr  = st.number_input("Cr (mg/dL)", 0.0, 20.0, 0.8, 0.1, key=wkey("cr"))
    with col5: day = st.date_input("측정일", value=_dt.date.today(), key=wkey("date"))

    # 추가 기본 수치 (Diet/경보용)
    r1 = st.columns(6)
    with r1[0]: wbc = st.number_input("WBC (x10^3/µL)", 0.0, 200.0, 0.0, 0.1, key=wkey("WBC"))
    with r1[1]: hb  = st.number_input("Hb (g/dL)", 0.0, 25.0, 0.0, 0.1, key=wkey("Hb"))
    with r1[2]: plt = st.number_input("PLT (x10^3/µL)", 0.0, 1000.0, 0.0, 1.0, key=wkey("PLT"))
    with r1[3]: anc = st.number_input("ANC (/µL)", 0.0, 10000.0, 0.0, 50.0, key=wkey("ANC"))
    with r1[4]: crp = st.number_input("CRP (mg/dL)", 0.0, 50.0, 0.0, 0.1, key=wkey("CRP"))
    with r1[5]: glu = st.number_input("Glucose (mg/dL)", 0.0, 600.0, 0.0, 1.0, key=wkey("Glu"))

    r2 = st.columns(5)
    with r2[0]: na  = st.number_input("Na (mEq/L)", 0.0, 200.0, 0.0, 0.5, key=wkey("Na"))
    with r2[1]: k   = st.number_input("K (mEq/L)", 0.0, 10.0, 0.0, 0.1, key=wkey("K"))
    with r2[2]: alb = st.number_input("Albumin (g/dL)", 0.0, 6.0, 0.0, 0.1, key=wkey("Alb"))
    with r2[3]: ca  = st.number_input("Calcium (mg/dL)", 0.0, 15.0, 0.0, 0.1, key=wkey("Ca"))
    with r2[4]: ua  = st.number_input("Uric Acid (mg/dL)", 0.0, 30.0, 0.0, 0.1, key=wkey("UA"))

    r3 = st.columns(2)
    with r3[0]: ast = st.number_input("AST (U/L)", 0.0, 1000.0, 0.0, 1.0, key=wkey("AST"))
    with r3[1]: alt = st.number_input("ALT (U/L)", 0.0, 1000.0, 0.0, 1.0, key=wkey("ALT"))

    # eGFR (CKD-EPI 2009) — simplified impl
    def egfr_2009(cr_mgdl:float, age:int, sex:str):
        sex_f = (sex=="여"); k = 0.7 if sex_f else 0.9; a = -0.329 if sex_f else -0.411
        mn = min(cr_mgdl/k,1); mx = max(cr_mgdl/k,1); sex_fac = 1.018 if sex_f else 1.0
        return round(141*(mn**a)*(mx**-1.209)*(0.993**age)*sex_fac,1)
    egfr = egfr_2009(cr, int(age), sex)
    st.metric("eGFR (CKD-EPI 2009)", f"{egfr} mL/min/1.73㎡")

    # 저장 (최근 5개 단순 표기)
    st.session_state.setdefault("lab_rows", [])
    if st.button("➕ 현재 값 추가", key=wkey("add_row")):
        st.session_state["lab_rows"].append({
            "date":str(day),"sex":sex,"age":int(age),"weight(kg)":wt,"Cr(mg/dL)":cr,"eGFR":egfr,
            "WBC":wbc,"Hb":hb,"PLT":plt,"CRP":crp,"Na":na,"K":k,"Alb":alb,"Ca":ca,"Glu":glu,"UA":ua,"ANC":anc,
            "AST":ast,"ALT":alt
        })
    rows = st.session_state["lab_rows"]
    if rows:
        st.write("최근 입력:")
        for r in rows[-5:]:
            st.write(r)

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
                st.session_state["dx_group"] = g.split()[0].strip("🩸🧬🧠🦴🧩")
                st.success(f"저장됨: {enko(en_dx, ko_dx)}")

with t_chemo:
    st.subheader("항암제")
    en_dx = st.session_state.get("dx_en")
    ko_dx = st.session_state.get("dx_ko","")
    gname = st.session_state.get("dx_group","")
    if not en_dx:
        st.info("먼저 '암 선택'에서 저장하세요.")
    else:
        st.write(f"현재 진단: **{enko(en_dx, ko_dx)}**")
        # 기본 제안
        suggestions = CHEMO_MAP.get(en_dx, CHEMO_MAP.get(ko_dx, []))
        # onco_map 기반 자동 추천(가능 시)
        try:
            omap = build_onco_map() if build_onco_map else {}
            # group 정규화
            grp = "혈액암" if "혈액암" in gname else \
                  "림프종" if "림프종" in gname else \
                  "고형암" if "고형암" in gname else \
                  "육종" if "육종" in gname else \
                  "희귀암" if "희귀" in gname else ""
            # dx 코드/원문 모두 시도
            auto = auto_recs_by_dx(grp, en_dx, DRUG_DB, omap) if auto_recs_by_dx and grp else {}
            auto_list = list(set((auto.get("chemo") or []) + (auto.get("targeted") or [])))
            suggestions = list(dict.fromkeys((suggestions or []) + [display_label(x, DRUG_DB) for x in auto_list]))
        except Exception:
            pass

        picked = st.multiselect("항암제를 선택/추가", suggestions, default=suggestions, key=wkey("chemo_ms"))
        extra = st.text_input("추가 항암제(쉼표 구분)", key=wkey("chemo_extra"))
        if extra.strip():
            more = [x.strip() for x in extra.split(",") if x.strip()]
            seen, merged = set(), []
            for x in picked + more:
                if x not in seen: seen.add(x); merged.append(x)
            picked = merged
        if st.button("항암제 저장", key=wkey("chemo_save")):
            # 라벨→키 복원
            def to_key(lbl):
                # "Key (Alias)" 또는 Alias만 → 키 추정
                s = str(lbl)
                p = s.find(" (")
                if p>0: return s[:p]
                # alias 역탐색
                for k,v in (DRUG_DB or {}).items():
                    if isinstance(v, dict) and v.get("alias")==s:
                        return k
                return s
            st.session_state["chemo_keys"] = [to_key(x) for x in picked]
            st.session_state["chemo_list"] = picked
            st.success("저장됨. '보고서'에서 확인")

with t_special:
    st.subheader("특수검사")
    lines = []
    if special_tests_ui:
        lines = special_tests_ui()
    else:
        # Fallback 간단 입력
        a,b,c = st.columns(3)
        sp1 = a.text_input("유전자/표지자 (예: BCR-ABL1)", key=wkey("spec_gene"))
        sp2 = b.text_input("이미징/기타 (예: PET/CT 결과)", key=wkey("spec_img"))
        sp3 = c.text_input("기타 메모", key=wkey("spec_note"))
        if sp1: lines.append(f"유전자/표지자: {sp1}")
        if sp2: lines.append(f"이미징/기타: {sp2}")
        if sp3: lines.append(f"메모: {sp3}")
    st.session_state["special_lines"] = lines

with t_report:
    st.subheader("보고서 / 결과")
    gated = results_only_after_analyze(st)  # 버튼 이후만 노출
    if not gated:
        st.info("상단 '해석하기' 버튼을 먼저 눌러주세요.")
    else:
        # 수집
        dx = enko(st.session_state.get("dx_en",""), st.session_state.get("dx_ko",""))
        meds = st.session_state.get("chemo_list", [])
        med_keys = st.session_state.get("chemo_keys", [])
        rows = st.session_state.get("lab_rows", [])
        spec = st.session_state.get("special_lines", []) or []

        # 식이가이드
        diet_lines = []
        if lab_diet_guides and rows:
            last = rows[-1]
            labs = {k:last.get(k) for k in ["Alb","K","Hb","Na","Ca","Glu","AST","ALT","Cr(mg/dL)","BUN","UA","CRP","ANC","PLT"]}
            # 키 보정
            labs["Cr"] = labs.pop("Cr(mg/dL)")
            heme_flag = bool(st.session_state.get("dx_group","").find("혈액암")+1)
            diet_lines = lab_diet_guides(labs, heme_flag=heme_flag) or []

        # AE Top Alerts
        top_alerts = []
        try:
            top_alerts = collect_top_ae_alerts(med_keys, DRUG_DB) or []
        except Exception:
            pass

        # 화면 표시 (요약 박스)
        if top_alerts:
            st.error("중요 경고(Top):\n\n" + "\n".join([f"- {x}" for x in top_alerts]))
        if diet_lines:
            st.warning("식이가이드:\n\n" + "\n".join([f"- {x}" for x in diet_lines]))

        if med_keys:
            st.markdown("### 약물 부작용 상세")
            try:
                render_adverse_effects(st, med_keys, DRUG_DB)
            except Exception:
                for k in med_keys: st.write(f"- {k}")

        # MD Report
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
            head = ["date","sex","age","weight(kg)","Cr(mg/dL)","eGFR","WBC","Hb","PLT","CRP","Na","K","Alb","Ca","Glu","UA","ANC","AST","ALT"]
            lines.append("| " + " | ".join(head) + " |")
            lines.append("|" + "|".join(["---"]*len(head)) + "|")
            for r in rows[-5:]:
                lines.append("| " + " | ".join(str(r.get(k,'')) for k in head) + " |")
        if spec:
            lines.append("")
            lines.append("## 특수검사")
            for s in spec:
                lines.append(f"- {s}")
        if diet_lines:
            lines.append("")
            lines.append("## 식이가이드")
            for s in diet_lines:
                lines.append(f"- {s}")
        lines.append("")
        lines.append(f"_생성 시각: {_dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_")

        md = "\n".join(lines)
        st.code(md, language="markdown")
        st.download_button("💾 보고서 .md 다운로드", data=md.encode("utf-8"),
                           file_name="bloodmap_report.md", mime="text/markdown", key=wkey("dl_md"))

        # PDF download (optional)
        if export_md_to_pdf:
            try:
                pdf_bytes = export_md_to_pdf(md)
                st.download_button("🖨️ 보고서 PDF 다운로드", data=pdf_bytes,
                                   file_name="bloodmap_report.pdf", mime="application/pdf",
                                   key=wkey("dl_pdf"))
            except Exception:
                st.caption("PDF 변환 모듈(reportlab) 미설치로 PDF 내보내기를 건너뜁니다.")
