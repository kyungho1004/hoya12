# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta, timezone

from branding import render_deploy_banner
from core_utils import nickname_pin, clean_num, schedule_block
from drug_db import DRUG_DB, ensure_onco_drug_db, display_label, key_from_label, picklist
from ui_results import results_only_after_analyze, render_adverse_effects, collect_top_ae_alerts
from lab_diet import lab_diet_guides
from special_tests import special_tests_ui
from pdf_export import export_md_to_pdf
from safety import (
    now_kst, urgent_banners, egfr_ckd_epi_2021, egfr_schwartz_2009,
    next_allowed, total_24h_mg, limit_for_day, block_ibu_reason, apap_caution_reason
)
from report_builder import build_report_blocks
from metrics import bump as bump_metrics

KST = timezone(timedelta(hours=9))
# ---- Writable data root helpers (ENV + /mnt/data + /tmp fallback) ----
import tempfile
def _ensure_dir_for(path: str):
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)

def _writable_dir(d: str) -> bool:
    try:
        os.makedirs(d, exist_ok=True)
        probe = os.path.join(d, ".probe")
        with open(probe, "w", encoding="utf-8") as f:
            f.write("ok")
        os.remove(probe)
        return True
    except Exception:
        return False

def _data_root() -> str:
    env = os.getenv("BLOODMAP_DATA_ROOT", "").strip()
    cand = [env] if env else ["/mnt/data"]
    cand.append(os.path.join(tempfile.gettempdir(), "bloodmap_data"))
    for r in cand:
        if not r:
            continue
        if _writable_dir(r):
            return r
    # last resort: tmp
    r = os.path.join(tempfile.gettempdir(), "bloodmap_data")
    os.makedirs(r, exist_ok=True)
    return r

def _data_path(*parts) -> str:
    return os.path.join(_data_root(), *parts)

# ---- Disk I/O helpers ----
import json, os
def _profile_path(uid:str): return _data_path("profile", f"{uid}.json")
def _carelog_path(uid:str): return _data_path("care_log", f"{uid}.json")

def load_profile(uid: str):
    try:
        with open(_profile_path(uid),"r",encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_profile(uid: str, data: dict):
    path = _profile_path(uid)
    _ensure_dir_for(path)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)

def load_carelog(uid: str):
    try:
        with open(_carelog_path(uid),"r",encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_carelog(uid: str, entries: list):
    path = _carelog_path(uid)
    _ensure_dir_for(path)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)

# ---- ICS export helper ----
def build_ics_for_next_doses(apap_next, ibu_next):
    def ics_event(dt, title):
        # naive ICS VEVENT (KST)
        return (
            "BEGIN:VEVENT\n"
            f"DTSTART;TZID=Asia/Seoul:{dt.strftime('%Y%m%dT%H%M%S')}\n"
            f"SUMMARY:{title}\n"
            "END:VEVENT\n"
        )
    parts = ["BEGIN:VCALENDAR\nPRODID:-//BloodMap//carelog//KR\nVERSION:2.0\n"]
    if apap_next:
        for i in range(3):
            parts.append(ics_event(apap_next + timedelta(hours=4*i), "APAP 다음 가능 시각"))
    if ibu_next:
        for i in range(3):
            parts.append(ics_event(ibu_next + timedelta(hours=6*i), "IBU 다음 가능 시각"))
    parts.append("END:VCALENDAR\n")
    return "".join(parts)


# ------------ 초기 세팅 ------------
st.set_page_config(page_title="BloodMap — 피수치가이드", page_icon="🩸", layout="centered")
render_deploy_banner("https://bloodmap.streamlit.app/", "만든이: Hoya/GPT · 자문: Hoya/GPT")
st.title("BloodMap — 피수치가이드")

st.info(
    "이 앱은 의료행위가 아니며, **참고용**입니다. 진단·치료를 **대체하지 않습니다**.\n"
    "약 변경/복용 중단 등은 반드시 주치의와 상의하세요. 모든 시간은 한국시간(KST) 기준입니다."
)
st.markdown("문의/버그 제보: **[피수치 가이드 공식카페](https://cafe.naver.com/bloodmap)**")

# 별명/PIN
nick, pin, key = nickname_pin()
has_key = bool(nick and pin and len(pin)==4)
uid = key or "guest"
stats = None
try:
    stats = bump_metrics(uid)  # 방문자 통계 증가
except Exception:
    stats = None

# 약물 DB 로드
ensure_onco_drug_db(DRUG_DB)

# Sidebar 방문자 통계
with st.sidebar:
    st.subheader("👥 방문자 통계")
    import json, os
    path = (stats or {}).get("_path") or "/mnt/data/metrics/visits.json"
    if os.path.exists(path):
        data = json.load(open(path,"r",encoding="utf-8"))
        t = data.get("today",{})
        st.write(f"오늘: 고유 {t.get('unique',0)} / 방문 {t.get('visits',0)}")
        st.write(f"누적 고유: {data.get('unique_count',0)}")
        st.write(f"총 방문수: {data.get('total_visits',0)}")
    st.caption(f"※ 통계 저장경로: {(stats or {}).get('_path') or '/mnt/data/metrics/visits.json'}")

# ------------ 프로필(성별/나이/키/체중/시럽농도 등) ------------
st.markdown("### 0) 프로필")
prof0 = load_profile(uid)
c1,c2,c3,c4 = st.columns(4)
with c1: sex = st.selectbox("성별", ["여","남"], index=0 if prof0.get("sex","여")=="여" else 1)
with c2: age = st.number_input("나이(년)", min_value=0, step=1, value=int(prof0.get("age",30)))
with c3: height_cm = st.number_input("키(cm)", min_value=0.0, step=0.5, value=float(prof0.get("height_cm",160.0)))
with c4: weight_kg = st.number_input("체중(kg)", min_value=0.0, step=0.1, value=float(prof0.get("weight_kg",50.0)))
st.session_state["profile"] = {"sex":sex, "age":age, "height_cm":height_cm, "weight_kg":weight_kg}
save_profile(uid, st.session_state["profile"])

# ------------ 암 모드 Only: 진단 & 약물 선택 ------------
st.markdown("### 1) 암/약물 선택")
group = st.selectbox("암 카테고리", ["혈액암","림프종","고형암","육종","희귀암"], index=0)
dx = st.text_input("진단(영문/축약)", value="APL")
st.caption("세포·면역 치료는 표기하지 않습니다(혼돈 방지 정책).")

# 개인 약물 선택
chemo_opts = ["Tretinoin","Arsenic Trioxide","Cytarabine","Daunorubicin","Idarubicin","MTX","6-MP"]
abx_opts   = ["Piperacillin/Tazobactam","Cefepime","Meropenem","Vancomycin","Levofloxacin","Ceftazidime","TMP-SMX"]
c1,c2 = st.columns(2)
with c1: user_chemo_labels = st.multiselect("항암제(개인)", picklist(chemo_opts), default=[])
with c2: user_abx_labels   = st.multiselect("항생제(개인)", picklist(abx_opts), default=[])
user_chemo = [key_from_label(x) for x in user_chemo_labels]
user_abx   = [key_from_label(x) for x in user_abx_labels]

# ------------ 2) 피수치 입력 + eGFR ------------
st.markdown("### 2) 피수치 입력 (숫자만)")
LABS_ORDER = [
    ("WBC","WBC"), ("Hb","Hb"), ("PLT","PLT"), ("ANC","ANC"),
    ("Na","Na"), ("K","K"), ("P","P"), ("Alb","Alb"), ("Ca","Ca 보정전"), ("Glu","Glu"),
    ("AST","AST"), ("ALT","ALT"), ("CRP","CRP"), ("Cr","Cr"), ("BUN","BUN")
]
labs = {code: clean_num(st.text_input(label, placeholder="예: 4500")) for code, label in LABS_ORDER}

# eGFR 계산
adult = (age >= 18)
egfr = None
if labs.get("Cr"):
    scr = float(labs["Cr"])
    if adult:
        egfr = egfr_ckd_epi_2021(scr, int(age), sex=="여")
    else:
        egfr = egfr_schwartz_2009(scr, float(height_cm))
st.caption(f"eGFR: {egfr} mL/min/1.73㎡" if egfr is not None else "eGFR: —")

# 특수검사: Myoglobin 포함
sp_lines = special_tests_ui()

# 저장/그래프 CSV
st.markdown("#### 💾 저장/그래프")
when = st.date_input("측정일", value=date.today())
if st.button("📈 피수치 저장/추가"):
    import os, csv
    path = _data_path("bloodmap_graph", f"{uid}.labs.csv")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    row = {"Date": when.strftime("%Y-%m-%d")}
    for code, _ in LABS_ORDER:
        row[code] = labs.get(code)
    # append or merge unique-date
    if os.path.exists(path):
        import pandas as pd
        df = pd.read_csv(path)
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        df = df.drop_duplicates(subset=["Date"], keep="last").sort_values("Date")
        df.to_csv(path, index=False)
    else:
        import pandas as pd
        pd.DataFrame([row]).to_csv(path, index=False)
    st.success(f"저장 완료 → {path}")

# 긴급 배너
care_entries = st.session_state.get("care_log", {}).get(uid)
if care_entries is None:
    care_entries = load_carelog(uid)
    st.session_state.setdefault("care_log", {})
    st.session_state["care_log"][uid] = care_entries
now = now_kst()
def _dt(ts): 
    try:
        return datetime.fromisoformat(ts)
    except Exception:
        return None
care_24h = [e for e in care_entries if _dt(e.get("ts")) and (now - _dt(e.get("ts"))).total_seconds() <= 24*3600]
banners = urgent_banners(labs, care_24h)
for b in banners:
    st.error(b)

# ------------ 3) 케어로그 + 해열제 게이트 ------------
st.markdown("### 3) 케어로그 & 해열제")
st.caption("모든 기록은 한국시간(KST)으로 저장됩니다.")
def _add_log(entry):
    st.session_state.setdefault("care_log", {})
    st.session_state["care_log"].setdefault(uid, [])
    st.session_state["care_log"][uid].append(entry)
    save_carelog(uid, st.session_state["care_log"][uid])

c1,c2,c3,c4,c5 = st.columns(5)
with c1:
    if st.button("발열 기록 +"):
        t = st.number_input("현재 체온(℃)", min_value=35.0, step=0.1, value=38.0, key="temp_add")
        _add_log({"type":"fever","temp":t,"ts": now.isoformat()})
        st.success("발열 기록됨.")
with c2:
    if st.button("구토 +"):
        _add_log({"type":"vomit","ts": now.isoformat(), "note": ""})
        st.success("구토 기록됨.")
with c3:
    if st.button("설사 +"):
        _add_log({"type":"diarrhea","ts": now.isoformat(), "note": ""})
        st.success("설사 기록됨.")
with c4:
    apap_mg = st.number_input("APAP(아세트아미노펜) 투여량 mg", min_value=0.0, step=50.0, value=0.0)
with c5:
    ibu_mg = st.number_input("IBU(이부프로펜) 투여량 mg", min_value=0.0, step=50.0, value=0.0)

# 24h 총량 및 쿨다운
adult_flag = adult
apap_next = next_allowed(care_entries, "apap")
ibu_next  = next_allowed(care_entries, "ibu")
apap_24 = total_24h_mg(care_entries, "apap", now)
ibu_24  = total_24h_mg(care_entries, "ibu", now)
apap_lim = limit_for_day("apap", float(weight_kg) if weight_kg else None, adult_flag)
ibu_lim  = limit_for_day("ibu", float(weight_kg) if weight_kg else None, adult_flag)

apap_cau = apap_caution_reason(labs)
ibu_block = block_ibu_reason(labs, egfr)

d1,d2 = st.columns(2)
with d1:
    if st.button("APAP 투여 기록"):
        if apap_mg <= 0:
            st.warning("용량을 입력하세요.")
        elif apap_next and now < apap_next:
            st.error(f"쿨다운 중: 다음 가능 시각 {apap_next.strftime('%Y-%m-%d %H:%M KST')}")
        elif apap_24 + apap_mg > apap_lim:
            st.error(f"24h 한도 초과({apap_24:.0f}/{apap_lim:.0f} mg)")
        else:
            _add_log({"type":"apap","mg": apap_mg, "ts": now.isoformat()})
            st.success("APAP 기록됨.")
with d2:
    if st.button("IBU 투여 기록"):
        if ibu_block:
            st.error(ibu_block)
        elif ibu_mg <= 0:
            st.warning("용량을 입력하세요.")
        elif ibu_next and now < ibu_next:
            st.error(f"쿨다운 중: 다음 가능 시각 {ibu_next.strftime('%Y-%m-%d %H:%M KST')}")
        elif ibu_24 + ibu_mg > ibu_lim:
            st.error(f"24h 한도 초과({ibu_24:.0f}/{ibu_lim:.0f} mg)")
        else:
            _add_log({"type":"ibu","mg": ibu_mg, "ts": now.isoformat()})
            st.success("IBU 기록됨.")

st.caption(f"APAP 24h: {apap_24:.0f}/{apap_lim:.0f} mg · 다음가능: {apap_next.strftime('%H:%M') if apap_next else '—'}")
st.caption(f"IBU  24h: {ibu_24:.0f}/{ibu_lim:.0f} mg · 다음가능: {ibu_next.strftime('%H:%M') if ibu_next else '—'}")
if apap_cau: st.warning(apap_cau)

# 최근 24h 케어로그 요약
if care_24h:
    st.markdown("#### 🗒️ 최근 24h 로그")
    for e in sorted(care_24h, key=lambda x: x["ts"]):
        if e["type"]=="fever":
            st.write(f"- {e['ts']} · 발열 {e.get('temp')}℃")
        elif e["type"] in ("apap","ibu"):
            st.write(f"- {e['ts']} · {e['type'].upper()} {e.get('mg')} mg")
        else:
            st.write(f"- {e['ts']} · {e['type']}")

    # Export buttons
    ics_data = build_ics_for_next_doses(apap_next, ibu_next)
    st.download_button("📅 다음 3회 복용 일정 (.ics)", data=ics_data, file_name="next_doses.ics")
    # TXT/PDF export for care log (24h)
    log_lines = ["케어로그(최근 24h)"] + [f"- {e.get('ts')} · {e.get('type')}" + (f" {e.get('temp')}℃" if e.get('type')=='fever' else (f" {e.get('mg')} mg" if e.get('type') in ('apap','ibu') else "")) for e in sorted(care_24h, key=lambda x: x['ts'])]
    log_txt = "\n".join(log_lines)
    st.download_button("⬇️ 케어로그 TXT", data=log_txt, file_name="carelog_24h.txt")
    try:
        from pdf_export import export_md_to_pdf
        log_pdf = export_md_to_pdf("\n".join(["# 케어로그(24h)"] + log_lines))
        st.download_button("⬇️ 케어로그 PDF", data=log_pdf, file_name="carelog_24h.pdf", mime="application/pdf")
    except Exception as e:
        st.caption(f"케어로그 PDF 오류: {e}")

# ------------ 4) 해석/보고서/부작용/식이가이드 ------------
if st.button("🔎 해석하기", key="analyze"):
    st.session_state["analyzed"] = True
    ctx = {
        "group": group, "dx": dx, "labs": labs, "egfr": egfr,
        "user_chemo": user_chemo, "user_abx": user_abx,
        "uid": uid, "profile": st.session_state.get("profile")
    }
    st.session_state["analysis_ctx"] = ctx

if results_only_after_analyze(st):
    ctx = st.session_state.get("analysis_ctx", {})
    labs = ctx.get("labs", {})
    st.subheader("🧪 피수치 요약")
    if labs:
        rcols = st.columns(len(labs))
        for i, (k, v) in enumerate(labs.items()):
            with rcols[i]: st.metric(k, v)
    if ctx.get("dx"): st.caption(f"진단: **{ctx['dx']}**")

    # Δ(변화량) from CSV (last two records)
    try:
        path = _data_path("bloodmap_graph", f"{uid}.labs.csv")
        df = pd.read_csv(path) if os.path.exists(path) else None
    except Exception:
        df = None
    if df is not None and len(df)>=2:
        df = df.sort_values("Date")
        last = df.iloc[-1]
        prev = df.iloc[-2]
        deltas = []
        for code, _ in LABS_ORDER:
            try:
                v_last = float(last.get(code))
                v_prev = float(prev.get(code))
                dv = v_last - v_prev
                if abs(dv) > 0:
                    deltas.append(f"{code} Δ {dv:+.1f}")
            except Exception:
                continue
        if deltas:
            st.caption("최근 변화: " + ", ".join(deltas[:8]))

    # 위험/주의 배너
    care_entries = st.session_state.get("care_log", {}).get(uid, [])
    now = now_kst()
    def _dt(ts): 
        try:
            return datetime.fromisoformat(ts)
        except Exception:
            return None
    care_24h = [e for e in care_entries if _dt(e.get("ts")) and (now - _dt(e.get("ts"))).total_seconds() <= 24*3600]
    for b in urgent_banners(labs, care_24h):
        st.error(b)

    # 식이가이드
    st.subheader("🍽️ 식이가이드")
    diet_lines = lab_diet_guides(labs or {}, heme_flag=(group=="혈액암"))
    for L in diet_lines: st.write("- " + L)
    ctx["diet_lines"] = diet_lines

    # 부작용
    st.subheader("💊 부작용")
    ckeys = ctx.get("user_chemo") or []
    akeys = ctx.get("user_abx") or []
    alerts = collect_top_ae_alerts(ckeys+akeys, db=DRUG_DB)
    if alerts: st.error(" / ".join(alerts))
    if ckeys:
        st.markdown("**항암제(세포독성)**")
        render_adverse_effects(st, ckeys, DRUG_DB)
    if akeys:
        st.markdown("**항생제**")
        render_adverse_effects(st, akeys, DRUG_DB)

    # 보고서
    st.subheader("📝 보고서 저장")
    # blocks: 응급도, 24h 케어로그 요약, 부작용 요약
    now = now_kst()
    care_2h = [e for e in care_entries if _dt(e.get("ts")) and (now - _dt(e.get("ts"))).total_seconds() <= 2*3600]
    blocks = build_report_blocks(ctx, care_24h, care_2h, ckeys+akeys)

    # compose MD/TXT
    title = "# BloodMap 결과 (암 모드)\n\n"
    body = []
    body.append(f"- 카테고리: {ctx.get('group')}")
    body.append(f"- 진단: {ctx.get('dx')}")
    if labs:
        labs_t = "; ".join(f"{k}:{v}" for k,v in labs.items() if v is not None)
        body.append(f"- 주요 수치: {labs_t}")
    if ctx.get("egfr") is not None:
        body.append(f"- eGFR: {ctx['egfr']} mL/min/1.73㎡")
    for title2, lines in blocks:
        if lines:
            body.append("\n## " + title2 + "\n" + "\n".join("- " + L for L in lines))
    if ctx.get("diet_lines"):
        body.append("\n## 🍽️ 식이가이드\n" + "\n".join("- " + L for L in ctx["diet_lines"]))
    footer = (
        "\n\n---\n"
        "본 수치는 참고용이며, 해석 결과는 개발자와 무관합니다.\n"
        "약 변경·복용 중단 등은 반드시 **주치의와 상담** 후 결정하십시오.\n"
        "개인정보를 수집하지 않습니다.\n"
        "버그/문의: 피수치 가이드 공식카페.\n"
    )
    md = title + "\n".join(body) + footer
    txt = md.replace("# ","").replace("## ","")

    st.download_button("⬇️ Markdown (.md)", data=md, file_name="BloodMap_Report.md")
    st.download_button("⬇️ 텍스트 (.txt)", data=txt, file_name="BloodMap_Report.txt")
    try:
        pdf_bytes = export_md_to_pdf(md)
        st.download_button("⬇️ PDF (.pdf)", data=pdf_bytes, file_name="BloodMap_Report.pdf", mime="application/pdf")
    except Exception as e:
        st.caption(f"PDF 변환 중 오류: {e}")
