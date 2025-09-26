# app.py — Minimal, always-on inputs (Labs, Diagnosis, Chemo, Special Tests)
import datetime as _dt
import streamlit as st
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
t_home, t_labs, t_dx, t_chemo, t_special, t_care, t_report = st.tabs(
    ["🏠 홈","🧪 피수치 입력","🧬 암 선택","💊 항암제","🔬 특수검사","🩺 케어로그","📄 보고서"]
)

with t_home:
    st.info("각 탭에 기본 입력창이 항상 표시됩니다. 외부 파일 없어도 작동합니다.")

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
    up = st.file_uploader("파일에서 불러오기(CSV)", type=["csv"], key=wkey("csv_up"))
    if up is not None:
        try:
            import pandas as pd
            df = pd.read_csv(up)
            st.session_state["lab_rows"] = df.to_dict(orient="records")
            st.success("CSV 불러오기 완료")
        except Exception as e:
            st.error(f"CSV 파싱 오류: {e}")

    # simple rows w/o pandas
    st.session_state.setdefault("lab_rows", [])
    if st.button("➕ 현재 값 추가", key=wkey("add_row")):
        st.session_state["lab_rows"].append({"date":str(day),"sex":sex,"age":int(age),"weight(kg)":wt,"Cr(mg/dL)":cr,"eGFR":egfr})
        try:
            import os
            import pandas as pd
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
    pass

with t_care:
    st.subheader('케어로그')
    risk_banner()
    med_guard_apap_ibu_ui(st.session_state.get('wt', 0.0))

    st.subheader("특수검사")
    # Always show basic fields so it's never empty
    a,b,c = st.columns(3)
    sp1 = a.text_input("유전자/표지자 (예: BCR-ABL1)", key=wkey("spec_gene"))
    sp2 = b.text_input("이미징/기타 (예: PET/CT 결과)", key=wkey("spec_img"))
    sp3 = c.text_input("기타 메모", key=wkey("spec_note"))
    st.session_state["special"] = {"gene":sp1,"image":sp2,"note":sp3}

with t_report:
    st.subheader("보고서 (.md)")
    if st.button("🏥 ER 원페이지 PDF", key=wkey("btn_erpdf")):
        md_tmp = "# 응급 안내 (요약)\n- 응급 신호: 고열 ≥39℃, 호흡곤란, 지속 구토·설사, 출혈 지속\n- 자가대처: 해열제 쿨다운 준수(APAP 4h/IBU 6h), 수분 보충\n- 즉시 병원가기: 의식저하/경련/혈압저하/혈변·흑변\n- 준비물: 최근 24h 투약기록, 최근 검사표, 알레르기 정보\n"
        pdf_bytes = export_md_to_pdf(md_tmp)
        st.download_button("⬇️ ER_Pamphlet.pdf", data=pdf_bytes, file_name="ER_Pamphlet.pdf", mime="application/pdf", key=wkey("dl_erpdf"))
    dx = enko(st.session_state.get("dx_en",""), st.session_state.get("dx_ko",""))
    meds = st.session_state.get("chemo_list", [])
    rows = st.session_state.get("lab_rows", [])
    spec = st.session_state.get("special", {})
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
        lines.append("|" + "|".join(["---"]*len(head)) + "|")
        for r in rows[-5:]:
            lines.append("| " + " | ".join(str(r.get(k,'')) for k in head) + " |")
    if any(spec.values()):
        lines.append("")
        lines.append("## 특수검사")
        if spec.get("gene"):  lines.append(f"- 유전자/표지자: {spec['gene']}")
        if spec.get("image"): lines.append(f"- 이미징/기타: {spec['image']}")
        if spec.get("note"):  lines.append(f"- 메모: {spec['note']}")
    lines.append("")
    lines.append(f"_생성 시각: {_dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_")
    md = "\n".join(lines)
    st.code(md, language="markdown")
    st.download_button("💾 보고서 .md 다운로드", data=md.encode("utf-8"),
                       file_name="bloodmap_report.md", mime="text/markdown", key=wkey("dl_md"))