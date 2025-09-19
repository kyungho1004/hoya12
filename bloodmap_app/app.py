
# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# ---------- Project imports (guarded) ----------
# We try real modules first; if missing, we fall back to safe stubs.
try:
    from core_utils import nickname_pin, clean_num, schedule_block
except Exception:
    def nickname_pin(): return "게스트#0000"
    def clean_num(x): return x
    def schedule_block(*a, **k): return ""

try:
    from drug_db import DRUG_DB, ensure_onco_drug_db, display_label
except Exception:
    DRUG_DB = {}
    def ensure_onco_drug_db(): return {}
    def display_label(x): return str(x)

try:
    from onco_map import build_onco_map, auto_recs_by_dx, dx_display
except Exception:
    def build_onco_map(*a, **k): return {}
    def auto_recs_by_dx(*a, **k): return []
    def dx_display(x): return str(x)

try:
    from ui_results import results_only_after_analyze, render_adverse_effects, collect_top_ae_alerts
except Exception:
    def results_only_after_analyze(*a, **k): return []
    def render_adverse_effects(*a, **k): return []
    def collect_top_ae_alerts(*a, **k): return []

try:
    from lab_diet import lab_diet_guides
except Exception:
    def lab_diet_guides(*a, **k): return []

try:
    from peds_profiles import get_symptom_options
except Exception:
    def get_symptom_options(): return {"발열":[],"구토":[],"설사":[]}

try:
    from peds_dose import acetaminophen_ml, ibuprofen_ml
except Exception:
    def acetaminophen_ml(age_m, wt_kg):
        if not wt_kg: return None, None
        # 10–15 mg/kg, syrup 160 mg/5mL
        ml = round((12*wt_kg)/(160/5), 1)
        return ml, {}
    def ibuprofen_ml(age_m, wt_kg):
        if not wt_kg: return None, None
        # 5–10 mg/kg, syrup 100 mg/5mL
        ml = round((8*wt_kg)/(100/5), 1)
        return ml, {}

try:
    from pdf_export import export_md_to_pdf
except Exception:
    export_md_to_pdf = None

try:
    from special_tests import special_tests_ui
except Exception:
    def special_tests_ui():
        with st.expander("특수검사 입력"):
            st.text_input("예) 페리틴")
            st.text_input("예) CRP")
        return []

# ---------- Global / Time ----------
KST = ZoneInfo("Asia/Seoul")
APP_VERSION = "v2.0.0-full"
RULESET_DATE = "2025-09-19"

def kst_now(): return datetime.now(KST)

# Stable, namespaced key prefix for this session (avoid DuplicateElementKey/Id)
st.session_state.setdefault("UID", str(uuid.uuid4())[:8])
KP = st.session_state["UID"]

# ---------- Page ----------
st.set_page_config(page_title="BloodMap — 피수치가이드 (완전체)", layout="wide")
st.title("BloodMap — 피수치가이드 (완전체)")
st.info("📌 **즐겨찾기** — PC: Ctrl/⌘+D, 모바일: 브라우저 공유 → **홈 화면에 추가**")

# ---------- Emergency checklist ----------
def emergency_checklist_md() -> str:
    now = kst_now().strftime("%Y-%m-%d %H:%M")
    return "\\n".join([
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

# ---------- Read-only view & share ----------
def is_read_only():
    try:
        qp = st.query_params
        v = qp.get("view", None)
        if isinstance(v, list):
            v = v[0] if v else None
        return (str(v).lower() == "read")
    except Exception:
        return False

def share_link_panel(section_title: str, anchor="#carelog"):
    st.markdown("#### 읽기 전용 공유")
    st.session_state.setdefault("share_key", str(uuid.uuid4())[:8])
    key = st.session_state["share_key"]
    base = "https://bloodmap.streamlit.app/"   # 배포 주소에 맞춰 교체
    url = f"{base}{anchor}?view=read&k={key}"
    st.code(url, language="")
    try:
        import qrcode, io as _io
        img = qrcode.make(url); buf=_io.BytesIO(); img.save(buf, format="PNG")
        st.image(buf.getvalue(), caption="읽기 전용 링크 QR", width=160)
    except Exception:
        st.caption("QR 모듈이 없으면 URL을 복사해 공유하세요.")

# ---------- Care log / Guardrails / Export ----------
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
    return "\\n".join(lines)

GUARD = {"APAP_MAX_DOSES_PER_DAY": 4, "IBU_MAX_DOSES_PER_DAY": 4}

def _today_str(): return kst_now().strftime("%Y-%m-%d")

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
    prod = st.text_input("현재 복용 중인 감기약/해열제 제품명(성분 중복 확인)", key=f"prod_names_{section_title}_{KP}")
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
    lines.append("END:VCALENDAR"); return "\\n".join(lines)

def render_care_log_ui(user_key: str, apap_ml=None, ibu_ml=None, section_title="설사/구토/해열제 기록"):
    st.markdown(f"### {section_title}")
    st.caption("APAP=아세트아미노펜, IBU=이부프로펜계열 (모든 시각은 KST 기준)")
    _init_care_log(user_key)
    now = kst_now()
    ro = is_read_only()
    if ro: st.info("🔒 읽기 전용 모드입니다 — 편집 불가")
    note = st.text_input("메모(선택)", key=f"care_note_{section_title}_{KP}")
    colA, colB, colC, colD = st.columns(4)
    if (not ro) and colA.button("구토 기록 추가", key=f"btn_log_vomit_{section_title}_{KP}"):
        _append_care_log(user_key, "구토",
            f"구토 — 보충 10 mL/kg, 5–10 mL q5min. 다음 점검 { (now+timedelta(minutes=30)).strftime('%H:%M') } / 활력 { (now+timedelta(hours=2)).strftime('%H:%M') } (KST)")
        if note: _append_care_log(user_key, "메모", note); st.success("구토 기록 저장됨")
    if (not ro) and colB.button("설사 기록 추가", key=f"btn_log_diarrhea_{section_title}_{KP}"):
        _append_care_log(user_key, "설사",
            f"설사 — 보충 10 mL/kg. 다음 점검 { (now+timedelta(minutes=30)).strftime('%H:%M') } / 활력 { (now+timedelta(hours=2)).strftime('%H:%M') } (KST)")
        if note: _append_care_log(user_key, "메모", note); st.success("설사 기록 저장됨")
    if (not ro) and colC.button("APAP(아세트아미노펜) 투약", key=f"btn_log_apap_{section_title}_{KP}"):
        dose = f"{apap_ml} ml" if apap_ml is not None else "용량 미기입"
        _append_care_log(user_key, "해열제(APAP)",
            f"{dose} — 다음 복용 { (now+timedelta(hours=4)).strftime('%H:%M') }~{ (now+timedelta(hours=6)).strftime('%H:%M') } KST")
        if note: _append_care_log(user_key, "메모", note); st.success("APAP 기록 저장됨")
    if (not ro) and colD.button("IBU(이부프로펜계열) 투약", key=f"btn_log_ibu_{section_title}_{KP}"):
        dose = f"{ibu_ml} ml" if ibu_ml is not None else "용량 미기입"
        _append_care_log(user_key, "해열제(IBU)",
            f"{dose} — 다음 복용 { (now+timedelta(hours=6)).strftime('%H:%M') }~{ (now+timedelta(hours=8)).strftime('%H:%M') } KST")
        if note: _append_care_log(user_key, "메모", note); st.success("IBU 기록 저장됨")

    df_log = _care_log_df(user_key)
    guardrail_panel(df_log, section_title, apap_enabled=(apap_ml is not None), ibu_enabled=(ibu_ml is not None))
    if not df_log.empty:
        st.dataframe(df_log.tail(50), use_container_width=True, height=240)
        st.markdown("#### 삭제")
        del_idxs = st.multiselect("삭제할 행 인덱스 선택(표 왼쪽 번호)", options=list(df_log.index), key=f"del_idx_{section_title}_{KP}", disabled=ro)
        if (not ro) and st.button("선택 행 삭제", key=f"btn_del_{section_title}_{KP}") and del_idxs:
            st.session_state['care_log'][user_key] = df_log.drop(index=del_idxs).reset_index(drop=True)
            st.success(f"{len(del_idxs)}개 행 삭제 완료")
        st.markdown("#### 읽기 전용 링크")
        share_link_panel(section_title)
        st.markdown("#### 내보내기")
        md = _care_log_to_md(df_log, title="케어 로그")
        st.download_button("⬇️ TXT", data=md.replace("# ","").replace("## ",""), file_name="care_log.txt", key=f"dl_txt_{section_title}_{KP}")
        if export_md_to_pdf:
            try:
                pdf_bytes = export_md_to_pdf(md)
                st.download_button("⬇️ PDF", data=pdf_bytes, file_name="care_log.pdf", mime="application/pdf", key=f"dl_pdf_{section_title}_{KP}")
            except Exception as e:
                st.caption(f"PDF 변환 오류: {e}")
        ics_data = generate_ics(kst_now(), have_apap=(apap_ml is not None), have_ibu=(ibu_ml is not None))
        st.download_button("📅 캘린더(.ics)", data=ics_data, file_name="care_times.ics", mime="text/calendar", key=f"ics_{section_title}_{KP}")
    else:
        st.caption("저장된 케어 로그가 없습니다. 위의 버튼으로 기록을 추가하세요.")

# ---------- Severity renderer ----------
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

# ---------- Modes ----------
st.divider()
seg = getattr(st, "segmented_control", None)
if seg:
    mode = st.segmented_control("모드 선택", options=["암", "일상", "소아(질환)"], key=f"mode_{KP}")
else:
    mode = st.radio("모드 선택", options=["암", "일상", "소아(질환)"], horizontal=True, key=f"mode_{KP}")

# ---------- Mode: Cancer ----------
if mode == "암":
    st.header("🧪 특수검사")
    sp_lines = special_tests_ui()  # always show, even if empty
    lines_blocks = [("특수검사 해석", sp_lines if sp_lines else ["(입력값 없음 또는 특이 소견 없음)"])]

    # Pediatric care toggle under special tests
    on_peds_tool = st.toggle("🧒 소아 해열제/설사 체크 (펼치기)", value=True, key=f"peds_tool_toggle_cancer_{KP}")
    if on_peds_tool:
        age_m_c = st.number_input("나이(개월)", min_value=0, step=1, key=f"ped_age_m_cancer_{KP}")
        weight_c = st.number_input("체중(kg)", min_value=0.0, step=0.1, key=f"ped_weight_cancer_{KP}")
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
    show_normals = st.checkbox("정상 항목도 표시", value=True, key=f"show_normals_cancer_{KP}")
    inputs_present = True
    for title2, lines2 in lines_blocks:
        render_severity_list(title2, lines2 or [], show_normals, inputs_present)

# ---------- Mode: Daily ----------
elif mode == "일상":
    st.header("👶/🧑 일상 케어")
    who = st.radio("대상", options=["소아","성인"], horizontal=True, key=f"daily_target_{KP}")

    if who == "소아":
        age_m = st.number_input("나이(개월)", min_value=0, step=1, key=f"ped_age_m_daily_{KP}")
        wt = st.number_input("체중(kg)", min_value=0.0, step=0.1, key=f"ped_weight_daily_{KP}")
        apap_ml, _ = acetaminophen_ml(age_m, wt or None)
        ibu_ml,  _ = ibuprofen_ml(age_m, wt or None)
        st.warning("이 용량 정보는 **참고용**입니다. 반드시 **주치의와 상담**하십시오.")

        show_care = st.toggle("🧒 소아 해열제/설사 체크 (펼치기)", value=True, key=f"peds_tool_toggle_daily_child_{KP}")
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
        # 성인용 간단 가이드 + 케어 로그
        st.markdown("#### 성인 케어")
        symptoms = st.multiselect("지표 선택", options=["발열","구토","설사","복통","두통"], key=f"adult_sym_{KP}")
        show_care_adult = st.toggle("🧑 해열제/설사 체크 (펼치기)", value=False, key=f"peds_tool_toggle_daily_adult_{KP}")
        if show_care_adult:
            now = kst_now(); st.caption(f"현재 시각 (KST): {now.strftime('%Y-%m-%d %H:%M')}")
            st.write(f"- APAP 권장 간격: **4~6시간** / IBU: **6~8시간**")
            st.markdown("**설사/구토 시간 체크(최소 간격)**")
            st.write("- 구토 시: **5분마다 5–10 mL**씩 소량 제공")
            st.write("- 설사/구토 1회마다: **체중당 10 mL/kg** 추가 보충")
            render_care_log_ui(st.session_state.get("key","guest"), apap_ml=None, ibu_ml=None, section_title="설사/구토/해열제 기록(일상·성인)")

# ---------- Mode: Peds disease ----------
elif mode == "소아(질환)":
    st.header("🧒 소아(질환) 모드")
    dx = st.selectbox("진단/증상", ["발열","구토","설사","호흡기","경련","기타"], key=f"dx_peds_{KP}")
    age_m = st.number_input("나이(개월)", min_value=0, step=1, key=f"ped_age_m_peds_{KP}")
    wt = st.number_input("체중(kg)", min_value=0.0, step=0.1, key=f"ped_weight_peds_{KP}")
    apap_ml, _ = acetaminophen_ml(age_m, wt or None)
    ibu_ml,  _ = ibuprofen_ml(age_m, wt or None)

    show_care_peds = st.toggle("🧒 소아 해열제/설사 체크 (펼치기)", value=True, key=f"peds_tool_toggle_peds_disease_{KP}")
    if show_care_peds:
        now = kst_now()
        st.caption(f"현재 시각 (KST): {now.strftime('%Y-%m-%d %H:%M')}")
        st.write(f"- 다음 APAP: { (now+timedelta(hours=4)).strftime('%H:%M') } ~ { (now+timedelta(hours=6)).strftime('%H:%M') }")
        st.write(f"- 다음 IBU: { (now+timedelta(hours=6)).strftime('%H:%M') } ~ { (now+timedelta(hours=8)).strftime('%H:%M') }")
        st.markdown("**설사/구토 시간 체크(최소 간격)**")
        st.write("- 구토 시: **5분마다 5–10 mL**씩 소량 제공")
        st.write("- 설사/구토 1회마다: **체중당 10 mL/kg** 추가 보충")
        render_care_log_ui(st.session_state.get("key","guest"), apap_ml=apap_ml, ibu_ml=ibu_ml, section_title="설사/구토/해열제 기록(소아·질환)")

# ---------- Report export ----------
def export_report(lines_blocks=None):
    title = "# BloodMap 결과 보고서\\n\\n"
    body = []
    if lines_blocks:
        for t, lines in lines_blocks:
            body.append(f"## {t}\\n")
            for L in (lines or []):
                body.append(f"- {L}\\n")
            body.append("\\n")
    footer = (
        "\\n\\n---\\n"
        "본 수치는 참고용이며, 해석 결과는 개발자와 무관합니다.\\n"
        "약 변경·복용 중단 등은 반드시 **주치의와 상담** 후 결정하십시오.\\n"
        "개인정보를 수집하지 않습니다.\\n"
        "버그/문의: 피수치 가이드 공식카페.\\n"
        f"앱 버전: {APP_VERSION} · 룰셋 업데이트: {RULESET_DATE}\\n"
    )
    md = emergency_checklist_md() + "\\n\\n---\\n\\n" + title + "".join(body) + footer
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("⬇️ Markdown (.md)", data=md, file_name="BloodMap_Report.md", key=f"dl_md_{KP}")
    with c2:
        if export_md_to_pdf:
            try:
                pdf_bytes = export_md_to_pdf(md)
                st.download_button("⬇️ PDF 보고서", data=pdf_bytes, file_name="BloodMap_Report.pdf", mime="application/pdf", key=f"dl_report_pdf_{KP}")
            except Exception as e:
                st.caption(f"PDF 변환 오류: {e}")
        else:
            st.caption("PDF 변환기가 없어 .md로 내보냈습니다. (export_md_to_pdf 연결 시 버튼 활성화)")

with st.expander("📄 보고서 내보내기"):
    if mode == "암":
        export_report(lines_blocks=lines_blocks)
    else:
        export_report(lines_blocks=[("일반 안내", ["현 모드에서는 특수검사 해석이 없습니다."])])

st.caption("본 도구는 참고용입니다. 의료진의 진단/치료를 대체하지 않습니다.")
st.caption("문의/버그 제보: 피수치 가이드 공식카페")
