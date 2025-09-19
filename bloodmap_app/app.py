
# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import altair as alt
import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# ===== Optional project modules (best-effort import) =====
# PDF export
try:
    from pdf_export import export_md_to_pdf  # expected in project
except Exception:
    export_md_to_pdf = None

# Pediatric dosing (try a few common names)
def _resolve_peds_dose():
    funcs = {}
    try:
        import peds_dose as _pd
        for name in ["acetaminophen_ml","dose_acetaminophen","calc_apap_ml"]:
            if hasattr(_pd, name): funcs["apap"] = getattr(_pd, name)
        for name in ["ibuprofen_ml","dose_ibuprofen","calc_ibu_ml"]:
            if hasattr(_pd, name): funcs["ibu"] = getattr(_pd, name)
    except Exception:
        pass
    if "apap" not in funcs:
        def _apap(age_months, weight_kg):
            if not weight_kg: return 0, {"note": "fallback"}
            mg = 12 * weight_kg  # 10~15 mg/kg 중간값
            ml = round(mg / (160/5), 1)
            return ml, {"note": "fallback"}
        funcs["apap"] = _apap
    if "ibu" not in funcs:
        def _ibu(age_months, weight_kg):
            if not weight_kg: return 0, {"note": "fallback"}
            mg = 8 * weight_kg   # 5~10 mg/kg 중간값
            ml = round(mg / (100/5), 1)
            return ml, {"note": "fallback"}
        funcs["ibu"] = _ibu
    return funcs["apap"], funcs["ibu"]
acetaminophen_ml, ibuprofen_ml = _resolve_peds_dose()

# Special tests UI
def special_tests_ui_safe():
    try:
        from special_tests import special_tests_ui as _real_ui
        return _real_ui()
    except Exception:
        # Minimal placeholder
        with st.expander("특수검사 입력(데모)"):
            st.text_input("예) 페리틴", key="demo_sp_ferritin")
            st.text_input("예) LDH", key="demo_sp_ldh")
        return []

# ===== Globals =====
KST = ZoneInfo("Asia/Seoul")
APP_VERSION = "prod-1.0.0"
RULESET_DATE = "2025-09-19"

def kst_now() -> datetime:
    return datetime.now(KST)

def is_read_only() -> bool:
    try:
        qp = st.query_params
        v = qp.get("view", None)
        if isinstance(v, list): v = v[0] if v else None
        return (str(v).lower() == "read")
    except Exception:
        return st.session_state.get("read_only_hint", False)

# ===== Page =====
st.set_page_config(page_title="BloodMap — 피수치가이드 (Prod)", layout="wide")
st.title("BloodMap — 피수치가이드 (Prod)")
st.info("📌 **즐겨찾기** — PC: Ctrl/⌘+D, 모바일: 브라우저 공유 → **홈 화면에 추가**")

# ===== Emergency checklist =====
def emergency_checklist_md() -> str:
    now = kst_now().strftime("%Y-%m-%d %H:%M")
    return "\n".join([
        "# 🆘 비상 안내(보호자용)",
        f"- 출력 시각(KST): {now}",
        "",
        "## 즉시 진료(응급)",
        "- 축 처짐/깨우기 어려움, 반복 구토/탈수 의심",
        "- 호흡곤란/입술 청색증, 경련/의식저하",
        "- 지속 고열(> 38.5℃) + 해열제 반응 없음",
        "- 혈변/흑변, 심한 복통/혈뇨",
        "",
        "## 1단계(자가 대처)",
        "- ORS: 5분마다 5–10 mL 소량",
        "- 설사/구토 1회마다 **10 mL/kg** 보충",
        "- 해열제 간격(APAP 4–6h, IBU 6–8h), **성분 중복 금지**",
        "",
        "## 2단계(외래 연락/방문)",
        "- 탈수 징후(소변 감소/입마름/눈물 적음)",
        "- 24–48시간 지속되는 발열/설사/구토",
        "",
        "## 3단계(응급실)",
        "- 위의 응급 신호가 하나라도 해당",
        "",
        "---",
        "_이 안내는 참고용이며, 반드시 주치의 지침을 우선합니다._",
    ])

with st.sidebar.expander("🆘 비상 안내(체크리스트)"):
    st.markdown(emergency_checklist_md())

# ===== Care log / Guardrails / ICS / Share =====
def _init_care_log(user_key: str):
    st.session_state.setdefault("care_log", {})
    if user_key not in st.session_state["care_log"]:
        st.session_state["care_log"][user_key] = pd.DataFrame(columns=["ts_kst","type","details"])

def _append_care_log(user_key: str, kind: str, details: str):
    _init_care_log(user_key)
    now = kst_now().strftime("%Y-%m-%d %H:%M")
    row = pd.DataFrame([{"ts_kst": now, "type": kind, "details": details}])
    st.session_state["care_log"][user_key] = pd.concat([st.session_state["care_log"][user_key], row], ignore_index=True)

def _care_log_df(user_key: str) -> pd.DataFrame:
    _init_care_log(user_key)
    return st.session_state["care_log"][user_key]

def _care_log_to_md(df: pd.DataFrame, title="케어 로그") -> str:
    lines = [f"# {title}", "", f"- 내보낸 시각(KST): {kst_now().strftime('%Y-%m-%d %H:%M')}",
             "", "시간(KST) | 유형 | 내용", "---|---|---"]
    for _, r in df.iterrows():
        lines.append(f"{r.get('ts_kst','')} | {r.get('type','')} | {r.get('details','')}")
    return "\n".join(lines)

GUARD = {"APAP_MAX_DOSES_PER_DAY": 4, "IBU_MAX_DOSES_PER_DAY": 4}

def _today_str():
    return kst_now().strftime("%Y-%m-%d")

def guardrail_panel(df_log: pd.DataFrame, section_title: str, apap_enabled: bool=True, ibu_enabled: bool=True):
    st.markdown("#### 해열제 안전 게이지/성분 중복 경고")
    if df_log is None or df_log.empty:
        apap_count = 0; ibu_count = 0
    else:
        df_today = df_log[df_log["ts_kst"].str.startswith(_today_str())]
        apap_count = int((df_today["type"]=="해열제(APAP)").sum())
        ibu_count  = int((df_today["type"]=="해열제(IBU)").sum())
    c1, c2 = st.columns(2)
    with c1:
        if apap_enabled:
            st.metric("APAP 투약(오늘)", f"{apap_count}/{GUARD['APAP_MAX_DOSES_PER_DAY']} 회")
            if apap_count >= GUARD["APAP_MAX_DOSES_PER_DAY"]:
                st.error("오늘 APAP 최대 권장 횟수 도달 — **추가 투약 금지**, 의료진 상담")
    with c2:
        if ibu_enabled:
            st.metric("IBU 투약(오늘)", f"{ibu_count}/{GUARD['IBU_MAX_DOSES_PER_DAY']} 회")
            if ibu_count >= GUARD["IBU_MAX_DOSES_PER_DAY"]:
                st.error("오늘 IBU 최대 권장 횟수 도달 — **추가 투약 금지**, 의료진 상담")
    prod = st.text_input("현재 복용 중인 감기약/해열제 제품명(성분 중복 확인)", key=f"prod_names_{section_title}")
    prod_txt = (prod or "").lower()
    warn_apap = any(x in prod_txt for x in ["타이레놀","아세트아미노펜","apap","acetaminophen","paracetamol"])
    warn_ibu  = any(x in prod_txt for x in ["이부프로펜","ibuprofen","advil","motrin"])
    if warn_apap: st.warning("⚠️ 입력 제품에 **아세트아미노펜(APAP)** 성분이 포함될 수 있어요. **중복 복용 주의**.")
    if warn_ibu:  st.warning("⚠️ 입력 제품에 **이부프로펜(IBU)** 성분이 포함될 수 있어요. **중복 복용 주의**.")

def generate_ics(now_dt, have_apap: bool, have_ibu: bool) -> str:
    def dtfmt(dt): return dt.strftime("%Y%m%dT%H%M%S")
    items = [("수분/탈수 점검", now_dt + timedelta(minutes=30)),
             ("소변/활력 점검", now_dt + timedelta(hours=2))]
    if have_apap: items.append(("APAP 다음 복용 가능(최초시각)", now_dt + timedelta(hours=4)))
    if have_ibu:  items.append(("IBU 다음 복용 가능(최초시각)", now_dt + timedelta(hours=6)))
    lines = ["BEGIN:VCALENDAR","VERSION:2.0","PRODID:-//BloodMap//CareLog//KO"]
    for title, dt in items:
        lines += ["BEGIN:VEVENT", f"DTSTART:{dtfmt(dt)}", f"SUMMARY:{title}", "END:VEVENT"]
    lines.append("END:VCALENDAR"); return "\n".join(lines)

def share_link_panel(section_title: str, anchor="#carelog"):
    st.markdown("#### 읽기 전용 공유")
    st.session_state.setdefault("share_key", str(uuid.uuid4())[:8])
    key = st.session_state["share_key"]
    base = "https://bloodmap.streamlit.app/"   # 배포 주소로 교체 가능
    url = f"{base}{anchor}?view=read&k={key}"
    st.code(url, language="")
    try:
        import qrcode, io as _io
        img = qrcode.make(url); buf=_io.BytesIO(); img.save(buf, format="PNG")
        st.image(buf.getvalue(), caption="읽기 전용 링크 QR", width=160)
    except Exception:
        st.caption("QR 모듈이 없으면 URL을 복사해 공유하세요.")

def render_care_log_ui(user_key: str, apap_ml=None, ibu_ml=None, section_title="설사/구토/해열제 기록"):
    st.markdown(f"### {section_title}")
    st.caption("APAP=아세트아미노펜, IBU=이부프로펜계열 (모든 시각은 KST 기준)")
    _init_care_log(user_key)
    now = kst_now()
    ro = is_read_only()
    if ro: st.info("🔒 읽기 전용 모드입니다 — 편집 불가")
    note = st.text_input("메모(선택)", key=f"care_note_{section_title}")
    colA, colB, colC, colD = st.columns(4)
    if (not ro) and colA.button("구토 기록 추가", key=f"btn_log_vomit_{section_title}"):
        _append_care_log(user_key, "구토",
            f"구토 — 보충 10 mL/kg, 5–10 mL q5min. 다음 점검 { (now+timedelta(minutes=30)).strftime('%H:%M') } / 활력 { (now+timedelta(hours=2)).strftime('%H:%M') } (KST)")
        if note: _append_care_log(user_key, "메모", note); st.success("구토 기록 저장됨")
    if (not ro) and colB.button("설사 기록 추가", key=f"btn_log_diarrhea_{section_title}"):
        _append_care_log(user_key, "설사",
            f"설사 — 보충 10 mL/kg. 다음 점검 { (now+timedelta(minutes=30)).strftime('%H:%M') } / 활력 { (now+timedelta(hours=2)).strftime('%H:%M') } (KST)")
        if note: _append_care_log(user_key, "메모", note); st.success("설사 기록 저장됨")
    if (not ro) and colC.button("APAP(아세트아미노펜) 투약", key=f"btn_log_apap_{section_title}"):
        dose = f"{apap_ml} ml" if apap_ml is not None else "용량 미기입"
        _append_care_log(user_key, "해열제(APAP)",
            f"{dose} — 다음 복용 { (now+timedelta(hours=4)).strftime('%H:%M') }~{ (now+timedelta(hours=6)).strftime('%H:%M') } KST")
        if note: _append_care_log(user_key, "메모", note); st.success("APAP 기록 저장됨")
    if (not ro) and colD.button("IBU(이부프로펜계열) 투약", key=f"btn_log_ibu_{section_title}"):
        dose = f"{ibu_ml} ml" if ibu_ml is not None else "용량 미기입"
        _append_care_log(user_key, "해열제(IBU)",
            f"{dose} — 다음 복용 { (now+timedelta(hours=6)).strftime('%H:%M') }~{ (now+timedelta(hours=8)).strftime('%H:%M') } KST")
        if note: _append_care_log(user_key, "메모", note); st.success("IBU 기록 저장됨")

    df_log = _care_log_df(user_key)
    guardrail_panel(df_log, section_title, apap_enabled=(apap_ml is not None), ibu_enabled=(ibu_ml is not None))
    if not df_log.empty:
        st.dataframe(df_log.tail(50), use_container_width=True, height=240)
        st.markdown("#### 삭제")
        del_idxs = st.multiselect("삭제할 행 인덱스 선택(표 왼쪽 번호)", options=list(df_log.index), key=f"del_idx_{section_title}", disabled=ro)
        if (not ro) and st.button("선택 행 삭제", key=f"btn_del_{section_title}") and del_idxs:
            st.session_state['care_log'][user_key] = df_log.drop(index=del_idxs).reset_index(drop=True)
            st.success(f"{len(del_idxs)}개 행 삭제 완료")
        st.markdown("#### 읽기 전용 링크")
        share_link_panel(section_title)
        st.markdown("#### 내보내기")
        md = _care_log_to_md(df_log, title="케어 로그")
        st.download_button("⬇️ TXT", data=md.replace("# ","").replace("## ",""), file_name="care_log.txt", key=f"txt_{section_title}")
        if export_md_to_pdf:
            try:
                pdf_bytes = export_md_to_pdf(md)
                st.download_button("⬇️ PDF", data=pdf_bytes, file_name="care_log.pdf", mime="application/pdf", key=f"pdf_{section_title}")
            except Exception as e:
                st.caption(f"PDF 변환 오류: {e}")
        ics_data = generate_ics(kst_now(), have_apap=(apap_ml is not None), have_ibu=(ibu_ml is not None))
        st.download_button("📅 캘린더(.ics)", data=ics_data, file_name="care_times.ics", mime="text/calendar", key=f"ics_{section_title}")
    else:
        st.caption("저장된 케어 로그가 없습니다. 위의 버튼으로 기록을 추가하세요.")

# ===== Lab inputs + assessment =====
def lab_input_ui(section_id: str, is_child: bool):
    st.markdown("### 🧪 피수치 입력")
    cols = st.columns(5)
    WBC = cols[0].number_input("백혈구(WBC, /μL)", min_value=0, step=100, key=f"WBC_{section_id}")
    Hb  = cols[1].number_input("혈색소(Hb, g/dL)", min_value=0.0, step=0.1, format="%.1f", key=f"Hb_{section_id}")
    PLT = cols[2].number_input("혈소판(PLT, x10^3/μL)", min_value=0, step=10, key=f"PLT_{section_id}")
    CRP = cols[3].number_input("CRP (mg/dL)", min_value=0.0, step=0.1, format="%.1f", key=f"CRP_{section_id}")
    ANC = cols[4].number_input("호중구(ANC, /μL)", min_value=0, step=100, key=f"ANC_{section_id}")
    data = {"WBC": WBC, "Hb": Hb, "PLT": PLT, "CRP": CRP, "ANC": ANC}

    refA = {"WBC": (4000,10000), "Hb": (12.0,16.0), "PLT": (150,400), "CRP": (0,0.5), "ANC": (1500,8000)}
    refC = {"WBC": (5000,14500), "Hb": (11.0,15.0), "PLT": (150,400), "CRP": (0,0.5), "ANC": (1500,8000)}
    ref = refC if is_child else refA

    def assess(val, lo, hi, name):
        if val is None: return ":gray[입력 없음]"
        if name == "CRP":
            if val > hi: return ":red[위험: 염증/감염 가능]"
            return ":green[정상 또는 경미]"
        if val < lo:
            if name in ["Hb","PLT","ANC"]: return ":red[위험: 낮음]"
            return ":yellow[주의: 낮음]"
        if val > hi:
            return ":yellow[주의: 높음]"
        return ":green[정상]"

    st.markdown("#### 해석하기")
    show_normals = st.checkbox("정상 항목도 표시", value=True, key=f"show_normals_{section_id}")
    if st.button("🔎 해석 실행", key=f"btn_analyze_{section_id}"):
        for k, v in data.items():
            lo, hi = ref[k]
            result = assess(v, lo, hi, k)
            if (not show_normals) and ("green[" in result):
                continue
            badge = ":red_circle:" if "red[" in result else (":large_yellow_circle:" if "yellow[" in result else ":green_circle:")
            st.markdown(f"- **{k}**: {badge} {result}")
        if (ANC and ANC < 1000) or (PLT and PLT < 50):
            st.error("응급 주의: 백신/외출/군중 피하고, 출혈/발열 즉시 병원 연락")
        elif CRP and CRP > 0.5:
            st.warning("감염 의심: 탈수 교정, 해열제 간격 준수, 외래 연락 고려")
        else:
            st.success("특별한 이상 소견 없음(데모 기준) — 주치의 판단을 우선하세요.")

    return data, ref

# ===== Special tests block =====
def special_tests_block():
    st.header("🧪 특수검사")
    lines = special_tests_ui_safe()
    return [("특수검사 해석", lines if lines else ["(입력값 없음 또는 특이 소견 없음)"])]

# ===== Hardened Altair demo chart =====
def lab_trend_demo():
    st.markdown("### 📈 추이(데모 데이터)")
    dfh = pd.DataFrame({
        "Date": pd.date_range(datetime.now() - timedelta(days=14), periods=8, freq="2D"),
        "WBC,백혈구": [4500,5200,6000,7000,6500,9000,8000,7600],
        "Hb,혈색소": [11.8,12.2,12.5,12.7,12.3,12.9,13.1,12.8],
        "PLT,혈소판": [140,180,210,260,300,280,240,220],
        "CRP": [0.4,0.6,0.3,0.2,0.1,0.2,0.5,0.4],
        "ANC,호중구": [1300,1600,2000,2500,2200,3000,2800,2600],
    })
    dfh["Date"] = pd.to_datetime(dfh["Date"]).dt.tz_localize(None)
    for c in ["WBC,백혈구","Hb,혈색소","PLT,혈소판","CRP","ANC,호중구"]:
        dfh[c] = pd.to_numeric(dfh[c], errors="coerce")

    pick = st.multiselect("표시 항목",
                          ["WBC,백혈구","Hb,혈색소","PLT,혈소판","CRP","ANC,호중구"],
                          default=["WBC,백혈구","Hb,혈색소"],
                          key="lab_trend_pick_demo")
    if pick:
        try:
            age_is_child = st.toggle("연령: 소아 기준 사용", value=False, key="range_child_toggle_demo")
            ranges_adult = {"WBC,백혈구": (4000, 10000), "Hb,혈색소": (12.0, 16.0), "PLT,혈소판": (150, 400), "CRP": (0, 0.5), "ANC,호중구": (1500, 8000)}
            ranges_child = {"WBC,백혈구": (5000, 14500), "Hb,혈색소": (11.0, 15.0), "PLT,혈소판": (150, 400), "CRP": (0, 0.5), "ANC,호중구": (1500, 8000)}
            df_tmp = dfh.copy()
            sel_df = df_tmp.set_index("Date")[pick].reset_index().melt("Date", var_name="item", value_name="value")
            lo_hi = {"item": [], "lo": [], "hi": []}
            for it in pick:
                lo, hi = (ranges_child if age_is_child else ranges_adult)[it]
                lo_hi["item"].append(it); lo_hi["lo"].append(float(lo)); lo_hi["hi"].append(float(hi))
            band_tbl = pd.DataFrame(lo_hi)
            base = alt.Chart(sel_df).encode(x=alt.X("Date:T", title="Date"), y=alt.Y("value:Q", title="Value"))
            shade = alt.Chart(band_tbl).mark_rect(opacity=0.08).encode(y="lo:Q", y2="hi:Q", color=alt.value("lightgray"))
            line = base.mark_line().encode(color="item:N")
            st.altair_chart(alt.layer(shade, line, data=sel_df), use_container_width=True)
        except Exception as e:
            st.warning(f"Altair 렌더링 이슈로 기본 차트로 대체: {e}")
            st.line_chart(dfh.set_index("Date")[pick])

# ===== Modes =====
st.divider()
seg = getattr(st, "segmented_control", None)
if seg:
    mode = st.segmented_control("모드 선택", options=["암", "일상", "소아(질환)"], key="mode_select")
else:
    mode = st.radio("모드 선택", options=["암", "일상", "소아(질환)"], horizontal=True, key="mode_select")

if mode == "암":
    # Lab inputs (adult baseline)
    data_cancer, ref_cancer = lab_input_ui("cancer", is_child=False)
    # Special tests
    lines_blocks = special_tests_block()
    # Pediatric care toggle
    on_peds_tool = st.toggle("🧒 소아 해열제/설사 체크 (펼치기)", value=True, key="peds_tool_toggle_cancer")
    if on_peds_tool:
        age_m_c = st.number_input("나이(개월)", min_value=0, step=1, key="ped_age_m_cancer")
        weight_c = st.number_input("체중(kg)", min_value=0.0, step=0.1, key="ped_weight_cancer")
        apap_ml_c, _w1 = acetaminophen_ml(age_m_c, weight_c or None)
        ibu_ml_c,  _w2 = ibuprofen_ml(age_m_c, weight_c or None)
        st.metric("APAP(아세트아미노펜) 1회 평균", f"{apap_ml_c} mL")
        st.metric("IBU(이부프로펜) 1회 평균", f"{ibu_ml_c} mL")
        render_care_log_ui(st.session_state.get("key","guest"), apap_ml=apap_ml_c, ibu_ml=ibu_ml_c, section_title="설사/구토/해열제 기록(암)")
    st.divider()
    lab_trend_demo()

elif mode == "일상":
    who = st.radio("대상", options=["소아","성인"], horizontal=True, key="daily_target")
    if who == "소아":
        data_child, ref_child = lab_input_ui("daily_child", is_child=True)
        age_m = st.number_input("나이(개월)", min_value=0, step=1, key="ped_age_m_daily")
        wt = st.number_input("체중(kg)", min_value=0.0, step=0.1, key="ped_weight_daily")
        apap_ml, _ = acetaminophen_ml(age_m, wt or None)
        ibu_ml,  _ = ibuprofen_ml(age_m, wt or None)
        st.warning("이 용량 정보는 **참고용**입니다. 반드시 **주치의와 상담**하십시오.")
        show_care = st.toggle("🧒 소아 해열제/설사 체크 (펼치기)", value=True, key="peds_tool_toggle_daily_child")
        if show_care:
            render_care_log_ui(st.session_state.get("key","guest"), apap_ml=apap_ml, ibu_ml=ibu_ml, section_title="설사/구토/해열제 기록(일상·소아)")
    else:
        data_adult, ref_adult = lab_input_ui("daily_adult", is_child=False)
        symptoms = st.multiselect("증상 선택", ["발열","구토","설사","복통","두통"], key="sym_daily_adult")
        show_care_adult = st.toggle("🧑 해열제/설사 체크 (펼치기)", value=False, key="peds_tool_toggle_daily_adult")
        if show_care_adult:
            render_care_log_ui(st.session_state.get("key","guest"), apap_ml=None, ibu_ml=None, section_title="설사/구토/해열제 기록(일상·성인)")

elif mode == "소아(질환)":
    st.header("🧒 소아(질환)")
    dx = st.selectbox("진단/증상", ["발열","구토","설사","호흡기","경련","기타"], key="dx_peds")
    data_peds, ref_peds = lab_input_ui("peds_disease", is_child=True)
    age_m = st.number_input("나이(개월)", min_value=0, step=1, key="ped_age_m_peds")
    wt = st.number_input("체중(kg)", min_value=0.0, step=0.1, key="ped_weight_peds")
    apap_ml, _ = acetaminophen_ml(age_m, wt or None)
    ibu_ml,  _ = ibuprofen_ml(age_m, wt or None)
    show_care_peds = st.toggle("🧒 소아 해열제/설사 체크 (펼치기)", value=True, key="peds_tool_toggle_peds_disease")
    if show_care_peds:
        render_care_log_ui(st.session_state.get("key","guest"), apap_ml=apap_ml, ibu_ml=ibu_ml, section_title="설사/구토/해열제 기록(소아·질환)")

# ===== Report export =====
def export_report(lines_blocks=None):
    title = "# BloodMap 결과 보고서\n\n"
    body = []
    if lines_blocks:
        for t, lines in lines_blocks:
            body.append(f"## {t}\n")
            for L in (lines or []):
                body.append(f"- {L}\n")
            body.append("\n")
    footer = (
        "\n\n---\n"
        "본 수치는 참고용이며, 해석 결과는 개발자와 무관합니다.\n"
        "약 변경·복용 중단 등은 반드시 **주치의와 상담** 후 결정하십시오.\n"
        "개인정보를 수집하지 않습니다.\n"
        "버그/문의: 피수치 가이드 공식카페.\n"
        f"앱 버전: {APP_VERSION} · 룰셋 업데이트: {RULESET_DATE}\n"
    )
    md = emergency_checklist_md() + "\n\n---\n\n" + title + "".join(body) + footer
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("⬇️ Markdown (.md)", data=md, file_name="BloodMap_Report.md", key="btn_md_report")
    with c2:
        if export_md_to_pdf:
            try:
                pdf_bytes = export_md_to_pdf(md)
                st.download_button("⬇️ PDF 보고서", data=pdf_bytes, file_name="BloodMap_Report.pdf", mime="application/pdf", key="btn_pdf_report")
            except Exception as e:
                st.caption(f"PDF 변환 오류: {e}")
        else:
            st.caption("PDF 변환기가 없어 .md로 내보냈습니다. (export_md_to_pdf 연결 시 버튼 활성화)")

with st.expander("📄 보고서 내보내기"):
    export_report(lines_blocks=[("특수검사 해석", ["예시 라인 A", "예시 라인 B"])])

# ===== Demo chart =====
lab_trend_demo()
