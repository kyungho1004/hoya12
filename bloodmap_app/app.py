
# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import altair as alt
import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# ---------- OPTIONAL PROJECT IMPORTS (guarded) ----------
# Safe to remove or replace. Used only if present.
try:
    from peds_dose import acetaminophen_ml, ibuprofen_ml   # EDIT HERE: connect your dose funcs
except Exception:
    # Fallback simple estimators (for demo only) — replace with real functions
    def acetaminophen_ml(age_months, weight_kg):
        if not weight_kg: return 0, None
        # 10–15 mg/kg, assume syrup 160 mg/5mL => 3.125 mg/mL → 1 mL ≈ 3.2 mg
        mg = max(10, min(15, 12)) * weight_kg
        ml = round(mg / (160/5), 1)
        return ml, {"note": "fallback"}
    def ibuprofen_ml(age_months, weight_kg):
        if not weight_kg: return 0, None
        # 5–10 mg/kg, assume syrup 100 mg/5mL
        mg = max(5, min(10, 8)) * weight_kg
        ml = round(mg / (100/5), 1)
        return ml, {"note": "fallback"}

try:
    from pdf_export import export_md_to_pdf                # EDIT HERE: your md->pdf exporter
except Exception:
    export_md_to_pdf = None

# ---------- GLOBAL / VERSION / TIMEZONE ----------
KST = ZoneInfo("Asia/Seoul")
APP_VERSION = "v1.0.1"
RULESET_DATE = "2025-09-19"

def kst_now() -> datetime:
    return datetime.now(KST)

def is_read_only() -> bool:
    # Read-only shared view via ?view=read
    try:
        qp = st.query_params
        v = qp.get("view", None)
        if isinstance(v, list):
            v = v[0] if v else None
        return (str(v).lower() == "read")
    except Exception:
        return st.session_state.get("read_only_hint", False)

# ---------- PAGE / HEADER ----------
st.set_page_config(page_title="BloodMap — 피수치가이드", layout="wide")
st.title("BloodMap — 피수치가이드")
st.info("📌 **즐겨찾기** — PC: Ctrl/⌘+D, 모바일: 브라우저 공유 → **홈 화면에 추가**")

# ---------- EMERGENCY CHECKLIST ----------
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

# ---------- CARE LOG / GUARDRAILS / ICS / SHARE ----------
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
    base = "https://bloodmap.streamlit.app/"   # EDIT HERE: 배포 주소로 교체
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
        st.download_button("⬇️ TXT", data=md.replace("# ","").replace("## ",""), file_name="care_log.txt")
        if export_md_to_pdf:
            try:
                pdf_bytes = export_md_to_pdf(md)
                st.download_button("⬇️ PDF", data=pdf_bytes, file_name="care_log.pdf", mime="application/pdf")
            except Exception as e:
                st.caption(f"PDF 변환 오류: {e}")
        ics_data = generate_ics(kst_now(), have_apap=(apap_ml is not None), have_ibu=(ibu_ml is not None))
        st.download_button("📅 캘린더(.ics)", data=ics_data, file_name="care_times.ics", mime="text/calendar", key=f"ics_{section_title}")
    else:
        st.caption("저장된 케어 로그가 없습니다. 위의 버튼으로 기록을 추가하세요.")

# ---------- SPECIAL TESTS (EDIT HERE: plug your own UI) ----------
def special_tests_ui_safe():
    """EDIT HERE: 기존 special_tests_ui()를 여기로 바꿔 연결하세요.
       반환은 리스트[str] 형태 (해석 라인들)."""
    try:
        # 프로젝트의 실제 함수를 자동 탐지/호출
        from special_tests import special_tests_ui as _real_ui
        return _real_ui()
    except Exception:
        # 데모(없을 때 빈 리스트)
        with st.expander("특수검사 입력(데모)"):
            st.text_input("예) 페리틴", key="demo_sp_ferritin")
            st.text_input("예) LDH", key="demo_sp_ldh")
        return []

def special_tests_block():
    sp_lines = special_tests_ui_safe()
    lines_blocks = []
    lines_blocks.append(("특수검사 해석", sp_lines if sp_lines else ["(입력값 없음 또는 특이 소견 없음)"]))
    return lines_blocks

# ---------- SEVERITY-COLORED RENDERER ----------
def render_severity_list(title: str, lines: list[str], show_normals: bool, inputs_present: bool):
    st.subheader("🧬 " + title)
    if not lines:
        st.markdown(":green[**(입력은 있었으나 특이 소견 없음)**]" if inputs_present else ":gray[(입력값 없음)]")
        return
    for L in lines:
        txt = str(L); t = txt.lower(); level = "gray"
        if any(k in txt for k in ["위험","응급","심각","위독","G4","G3"]): level = "red"
        elif any(k in txt for k in ["주의","경계","모니터","G2"]): level = "yellow"
        elif any(k in t for k in ["정상","정상범위","ok","양호"]): level = "green"
        if not show_normals and level == "green": continue
        badge = { "red": ":red_circle:", "yellow": ":large_yellow_circle:", "green": ":green_circle:", "gray": ":white_circle:" }.get(level, ":white_circle:")
        color_open = { "red": ":red[", "yellow": ":orange[", "green": ":green[", "gray": ":gray[" }.get(level, ":gray[")
        st.markdown(f"- {badge} {color_open}{txt}]")

# ---------- DEMO CHART WITH SHADED RANGES ----------

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
    # strict dtypes
    dfh["Date"] = pd.to_datetime(dfh["Date"]).dt.tz_localize(None)
    for col in ["WBC,백혈구","Hb,혈색소","PLT,혈소판","CRP","ANC,호중구"]:
        dfh[col] = pd.to_numeric(dfh[col], errors="coerce")
    pick = st.multiselect("표시 항목", ["WBC,백혈구","Hb,혈색소","PLT,혈소판","CRP","ANC,호중구"], default=["WBC,백혈구","Hb,혈색소"], key='lab_trend_pick')
    if pick:
        try:
            age_is_child = st.toggle("연령: 소아 기준 사용", value=False, key="range_child_toggle_demo")
            ranges_adult = {"WBC,백혈구": (4000, 10000), "Hb,혈색소": (12.0, 16.0), "PLT,혈소판": (150, 400), "CRP": (0, 0.5), "ANC,호중구": (1500, 8000)}
            ranges_child = {"WBC,백혈구": (5000, 14500), "Hb,혈색소": (11.0, 15.0), "PLT,혈소판": (150, 400), "CRP": (0, 0.5), "ANC,호중구": (1500, 8000)}
            df_tmp = dfh.copy()
            df_tmp["Date"] = pd.to_datetime(df_tmp["Date"]).dt.tz_localize(None)
            sel_df = df_tmp.set_index("Date")[pick].reset_index().melt("Date", var_name="item", value_name="value")
            # build bands from a single row dataframe (vega-lite friendly)
            lo_hi = {"item": [], "lo": [], "hi": []}
            for it in pick:
                r = (ranges_child if age_is_child else ranges_adult).get(it)
                if r:
                    lo_hi["item"].append(it); lo_hi["lo"].append(float(r[0])); lo_hi["hi"].append(float(r[1]))
            import pandas as _pd
            band_tbl = _pd.DataFrame(lo_hi)
            base = alt.Chart(sel_df).encode(x=alt.X("Date:T", title="Date"), y=alt.Y("value:Q", title="Value"))
            shade = alt.Chart(band_tbl).mark_rect(opacity=0.08).encode(
                y="lo:Q", y2="hi:Q", color=alt.value("lightgray")
            ).properties(width="container")
            line = base.mark_line().encode(color="item:N")
            chart = alt.layer(shade, line, data=sel_df)
            st.altair_chart(chart, use_container_width=True)
        except Exception as e:
            st.warning(f"Altair 렌더링 이슈로 기본 차트로 대체: {e}")
            st.line_chart(dfh.set_index("Date")[pick])
    dfh = pd.DataFrame({
        "Date": pd.date_range(datetime.now() - timedelta(days=14), periods=8, freq="2D"),
        "WBC,백혈구": [4500,5200,6000,7000,6500,9000,8000,7600],
        "Hb,혈색소": [11.8,12.2,12.5,12.7,12.3,12.9,13.1,12.8],
        "PLT,혈소판": [140,180,210,260,300,280,240,220],
        "CRP": [0.4,0.6,0.3,0.2,0.1,0.2,0.5,0.4],
        "ANC,호중구": [1300,1600,2000,2500,2200,3000,2800,2600],
    })
    pick = st.multiselect("표시 항목", ["WBC,백혈구","Hb,혈색소","PLT,혈소판","CRP","ANC,호중구"], default=["WBC,백혈구","Hb,혈색소"], key='lab_trend_pick')
    if pick:
        age_is_child = st.toggle("연령: 소아 기준 사용", value=False, key="range_child_toggle_demo")
        ranges_adult = {"WBC,백혈구": (4000, 10000), "Hb,혈색소": (12.0, 16.0), "PLT,혈소판": (150, 400), "CRP": (0, 0.5), "ANC,호중구": (1500, 8000)}
        ranges_child = {"WBC,백혈구": (5000, 14500), "Hb,혈색소": (11.0, 15.0), "PLT,혈소판": (150, 400), "CRP": (0, 0.5), "ANC,호중구": (1500, 8000)}
        df_tmp = dfh.copy();
        df_tmp["Date"] = pd.to_datetime(df_tmp["Date"]).dt.tz_localize(None)
        sel_df = df_tmp.set_index("Date")[pick].reset_index().melt("Date", var_name="item", value_name="value")
        base = alt.Chart(sel_df).encode(x=alt.X("Date:T", title="Date"), y=alt.Y("value:Q", title="Value"))
        bands = []
        for it in pick:
            r = (ranges_child if age_is_child else ranges_adult).get(it); 
            if not r: continue
            lo, hi = r
            if not sel_df.empty:
                band_df = pd.DataFrame({"Date": [sel_df["Date"].min()], "Date2": [sel_df["Date"].max()], "lo": [lo], "hi": [hi]})
                shade = alt.Chart(band_df).mark_rect(opacity=0.08).encode(x="Date:T", x2="Date2:T", y=alt.Y("lo:Q"), y2=alt.Y("hi:Q"))
                bands.append(shade)
        line = base.mark_line().encode(color="item:N", x="Date:T", y="value:Q")
        chart = (alt.layer(*(bands+[line])) if bands else line)
        st.altair_chart(chart, use_container_width=True)

# ---------- MODES (Cancer / Daily / Peds disease) ----------
st.divider()
seg = getattr(st, "segmented_control", None)
if seg:
    mode = st.segmented_control("모드 선택", options=["암", "일상", "소아(질환)"], key="mode_select")
else:
    mode = st.radio("모드 선택", options=["암", "일상", "소아(질환)"], horizontal=True, key="mode_select")

if mode == "암":
    st.header("🧪 특수검사")
    lines_blocks = special_tests_block()

    # Pediatric care toggle under special tests
    on_peds_tool = st.toggle("🧒 소아 해열제/설사 체크 (펼치기)", value=True, key="peds_tool_toggle_cancer")
    if on_peds_tool:
        age_m_c = st.number_input("나이(개월)", min_value=0, step=1, key="ped_age_m_cancer")
        weight_c = st.number_input("체중(kg)", min_value=0.0, step=0.1, key="ped_weight_cancer")
        apap_ml_c, _w1 = acetaminophen_ml(age_m_c, weight_c or None)
        ibu_ml_c,  _w2 = ibuprofen_ml(age_m_c, weight_c or None)
        c1, c2 = st.columns(2)
        with c1:
            st.metric("아세트아미노펜(APAP) 시럽 (1회 평균)", f"{apap_ml_c} ml"); st.caption("간격 4~6시간, 하루 최대 4회")
        with c2:
            st.metric("이부프로펜(IBU) 시럽 (1회 평균)", f"{ibu_ml_c} ml"); st.caption("간격 6~8시간, 음식과 함께")
        now = kst_now(); st.caption(f"현재 시각 (KST): {now.strftime('%Y-%m-%d %H:%M')}")
        st.write(f"- 다음 APAP: { (now+timedelta(hours=4)).strftime('%H:%M') } ~ { (now+timedelta(hours=6)).strftime('%H:%M') }")
        st.write(f"- 다음 IBU: { (now+timedelta(hours=6)).strftime('%H:%M') } ~ { (now+timedelta(hours=8)).strftime('%H:%M') }")
        st.markdown("**설사/구토 시간 체크(최소 간격)**")
        st.write("- 구토 시: 5분마다 5–10 mL씩 소량 제공")
        st.write("- 설사/구토 1회마다: 체중당 10 mL/kg 추가 보충")
        render_care_log_ui(st.session_state.get("key","guest"), apap_ml=apap_ml_c, ibu_ml=ibu_ml_c, section_title="설사/구토/해열제 기록(암)")

    st.divider()
    st.subheader("결과/해석")
    show_normals = st.checkbox("정상 항목도 표시", value=True, key="show_normals_cancer")
    inputs_present = True
    for title2, lines2 in lines_blocks:
        render_severity_list(title2, lines2 or [], show_normals, inputs_present)

    lab_trend_demo()

elif mode == "일상":
    st.header("👶/🧑 일상 케어")
    who = st.radio("대상", options=["소아","성인"], horizontal=True, key="daily_target")

    if who == "소아":
        age_m = st.number_input("나이(개월)", min_value=0, step=1, key="ped_age_m_daily")
        wt = st.number_input("체중(kg)", min_value=0.0, step=0.1, key="ped_weight_daily")
        apap_ml, _ = acetaminophen_ml(age_m, wt or None)
        ibu_ml,  _ = ibuprofen_ml(age_m, wt or None)
        st.warning("이 용량 정보는 **참고용**입니다. 반드시 **주치의와 상담**하십시오.")

        show_care = st.toggle("🧒 소아 해열제/설사 체크 (펼치기)", value=True, key="peds_tool_toggle_daily_child")
        if show_care:
            now = kst_now()
            st.caption(f"현재 시각 (KST): {now.strftime('%Y-%m-%d %H:%M')}")
            st.write(f"- 다음 APAP: { (now+timedelta(hours=4)).strftime('%H:%M') } ~ { (now+timedelta(hours=6)).strftime('%H:%M') }")
            st.write(f"- 다음 IBU: { (now+timedelta(hours=6)).strftime('%H:%M') } ~ { (now+timedelta(hours=8)).strftime('%H:%M') }")
            st.markdown("**설사/구토 시간 체크(최소 간격)**")
            st.write("- 구토 시: **5분마다 5–10 mL**씩 소량 제공")
            st.write("- 설사/구토 1회마다: **체중당 10 mL/kg** 추가 보충")
            st.write(f"- 수분/탈수 점검: **{ (now+timedelta(minutes=30)).strftime('%H:%M') }** (30분 후) · 소변/활력 점검: **{ (now+timedelta(hours=2)).strftime('%H:%M') }** (2시간 후)")
            render_care_log_ui(st.session_state.get("key","guest"), apap_ml=apap_ml, ibu_ml=ibu_ml, section_title="설사/구토/해열제 기록(일상·소아)")

    else:
        # EDIT HERE: 성인용 상세 가이드는 병원/팀 규칙에 맞게 확장
        symptoms = st.multiselect("증상 선택", ["발열","구토","설사","복통","두통"])
        show_care_adult = st.toggle("🧑 해열제/설사 체크 (펼치기)", value=False, key="peds_tool_toggle_daily_adult")
        if show_care_adult:
            now = kst_now(); st.caption(f"현재 시각 (KST): {now.strftime('%Y-%m-%d %H:%M')}")
            st.write(f"- APAP 권장 간격: **4~6시간** / IBU: **6~8시간**")
            st.markdown("**설사/구토 시간 체크(최소 간격)**")
            st.write("- 구토 시: **5분마다 5–10 mL**씩 소량 제공")
            st.write("- 설사/구토 1회마다: **체중당 10 mL/kg** 추가 보충")
            render_care_log_ui(st.session_state.get("key","guest"), apap_ml=None, ibu_ml=None, section_title="설사/구토/해열제 기록(일상·성인)")

elif mode == "소아(질환)":
    st.header("🧒 소아(질환) 모드")
    dx = st.selectbox("진단/증상", ["발열","구토","설사","호흡기","경련","기타"], key="dx_peds")
    age_m = st.number_input("나이(개월)", min_value=0, step=1, key="ped_age_m_peds")
    wt = st.number_input("체중(kg)", min_value=0.0, step=0.1, key="ped_weight_peds")
    apap_ml, _ = acetaminophen_ml(age_m, wt or None)
    ibu_ml,  _ = ibuprofen_ml(age_m, wt or None)

    show_care_peds = st.toggle("🧒 소아 해열제/설사 체크 (펼치기)", value=True, key="peds_tool_toggle_peds_disease")
    if show_care_peds:
        now = kst_now()
        st.caption(f"현재 시각 (KST): {now.strftime('%Y-%m-%d %H:%M')}")
        st.write(f"- 다음 APAP: { (now+timedelta(hours=4)).strftime('%H:%M') } ~ { (now+timedelta(hours=6)).strftime('%H:%M') }")
        st.write(f"- 다음 IBU: { (now+timedelta(hours=6)).strftime('%H:%M') } ~ { (now+timedelta(hours=8)).strftime('%H:%M') }")
        st.markdown("**설사/구토 시간 체크(최소 간격)**")
        st.write("- 구토 시: **5분마다 5–10 mL**씩 소량 제공")
        st.write("- 설사/구토 1회마다: **체중당 10 mL/kg** 추가 보충")
        render_care_log_ui(st.session_state.get("key","guest"), apap_ml=apap_ml, ibu_ml=ibu_ml, section_title="설사/구토/해열제 기록(소아·질환)")

# ---------- REPORT EXPORT (Markdown/PDF) ----------
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
        st.download_button("⬇️ Markdown (.md)", data=md, file_name="BloodMap_Report.md")
    with c2:
        if export_md_to_pdf:
            try:
                pdf_bytes = export_md_to_pdf(md)
                st.download_button("⬇️ PDF 보고서", data=pdf_bytes, file_name="BloodMap_Report.pdf", mime="application/pdf")
            except Exception as e:
                st.caption(f"PDF 변환 오류: {e}")
        else:
            st.caption("PDF 변환기가 없어 .md로 내보냈습니다. (export_md_to_pdf 연결 시 버튼 활성화)")

# ---------- DEMO: EXPORT BUTTON ----------
with st.expander("📄 보고서 내보내기 (데모)"):
    export_report(lines_blocks=[("특수검사 해석", ["예시 라인 A", "예시 라인 B"])])

# ---------- DEMO CHART ----------
lab_trend_demo()
