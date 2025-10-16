
# -*- coding: utf-8 -*-
import os, io, json, textwrap
import datetime as _dt

import streamlit as st
import pandas as pd

# Optional matplotlib
try:
    import matplotlib.pyplot as plt
except Exception:
    plt = None

# ---------- Optional modules (safe import) ----------
try:
    from drug_db import DRUG_DB
except Exception:
    DRUG_DB = {}

try:
    from pdf_export import export_md_to_pdf  # optional
except Exception:
    def export_md_to_pdf(md: str) -> bytes:
        # fallback: return utf-8 bytes (TXT)
        return md.encode("utf-8")

# ---------- Small utils ----------
def wkey(s: str) -> str:
    """Namespace widget keys to avoid duplicates across tabs."""
    return f"bm_{s}"

def now_kst() -> _dt.datetime:
    return _dt.datetime.now(tz=_dt.timezone(_dt.timedelta(hours=9)))

def display_label(key, db):
    try:
        info = db.get(key) or {}
        return info.get("label") or key
    except Exception:
        return str(key)

def _aggregate_all_aes(meds, db):
    """Collect adverse effects by med key list from DRUG_DB-like mapping."""
    out = {}
    for k in meds or []:
        info = (db or {}).get(k) or {}
        aes = info.get("adverse") or info.get("adverse_effects") or []
        if isinstance(aes, dict):
            # flatten dict (e.g., {"common": [...]})
            flat = []
            for vv in aes.values():
                if isinstance(vv, (list, tuple)):
                    flat.extend([str(x) for x in vv])
                else:
                    flat.append(str(vv))
            aes = flat
        out[k] = [str(x) for x in (aes or [])]
    return out

# Session init
st.session_state.setdefault("lab_history", [])  # list of {"ts": iso, "labs": {...}}

# ---------- App Header ----------
st.set_page_config(page_title="BloodMap", layout="wide")
st.markdown("<style> .stTabs [data-baseweb='tab'] {font-size: 16px;} </style>", unsafe_allow_html=True)
st.title("🩸 BloodMap")

# ---------- Tabs ----------
t_home, t_labs, t_cancer, t_chemo, t_peds, t_special, t_report, t_graph = st.tabs([
    "🏠 홈", "🧪 피수치 입력", "🧬 암 선택", "💊 항암제(진단 기반)", "👶 소아 증상", "🧭 특수검사", "📄 보고서", "📊 기록/그래프"
])

# ---------- 홈 ----------
with t_home:
    st.markdown("#### 소개")
    st.write("이 앱은 피수치 기록과 그래프, 보고서 작성, 소아 모듈(해열제 스케줄/정밀용량) 등을 제공합니다.")
    st.info("그래프는 **오른쪽 마지막 탭**에서만 표시됩니다.")

# ---------- 피수치 입력 (간단 버전) ----------
with t_labs:
    st.markdown("#### 최근 검사값 입력")
    cols = st.columns(6)
    labs = {}
    labs["WBC"] = cols[0].text_input("WBC", key=wkey("lab_WBC"))
    labs["Hb"]  = cols[1].text_input("Hb",  key=wkey("lab_Hb"))
    labs["PLT"] = cols[2].text_input("PLT", key=wkey("lab_PLT"))
    labs["ANC"] = cols[3].text_input("ANC", key=wkey("lab_ANC"))
    labs["CRP"] = cols[4].text_input("CRP", key=wkey("lab_CRP"))
    labs["Na"]  = cols[5].text_input("Na",  key=wkey("lab_Na"))
    cols2 = st.columns(6)
    labs["K"]   = cols2[0].text_input("K",   key=wkey("lab_K"))
    labs["Ca"]  = cols2[1].text_input("Ca",  key=wkey("lab_Ca"))
    labs["Cr"]  = cols2[2].text_input("Cr",  key=wkey("lab_Cr"))
    labs["BUN"] = cols2[3].text_input("BUN", key=wkey("lab_BUN"))
    labs["AST"] = cols2[4].text_input("AST", key=wkey("lab_AST"))
    labs["ALT"] = cols2[5].text_input("ALT", key=wkey("lab_ALT"))
    cols3 = st.columns(3)
    labs["T.B"] = cols3[0].text_input("T.B", key=wkey("lab_TB"))
    labs["Alb"] = cols3[1].text_input("Alb", key=wkey("lab_Alb"))
    labs["Glu"] = cols3[2].text_input("Glu", key=wkey("lab_Glu"))

    st.markdown("---")
    c1, c2 = st.columns([1,3])
    with c1:
        if st.button("➕ 현재 값을 기록에 추가", key=wkey("add_lab_rec")):
            entry = {"ts": now_kst().isoformat(), "labs": {k:v for k,v in labs.items() if str(v).strip() != ""}}
            st.session_state["lab_history"].append(entry)
            st.success("기록에 추가했습니다. (그래프 탭에서 확인)")

    with c2:
        st.caption("입력된 값은 세션의 기록에 저장됩니다. CSV 저장은 그래프 탭의 내보내기를 사용하세요.")

# ---------- 암/항암제 (요약) ----------
with t_cancer:
    st.markdown("#### 암 선택")
    group = st.selectbox("암 그룹", ["고형암","혈액암","기타"], index=0, key=wkey("grp"))
    disease = st.selectbox("의심/진단명", ["GIST","위암","대장암","유방암","기타"], index=0, key=wkey("dis"))
    st.success(f"선택: {group} / {disease}")

with t_chemo:
    st.markdown("#### 항암제(진단 기반)")
    st.write("선택한 진단에 따른 항암제 후보를 요약합니다.")
    # Dummy example from DB if exists
    meds = []
    if isinstance(DRUG_DB, dict):
        meds = list(DRUG_DB.keys())[:4]
    st.write("후보:", ", ".join(meds) if meds else "—")

# ---------- 소아 증상/해열제 ----------
def _peds_precision_block(weight_kg: float, age_months: int):
    md = []
    try:
        w = float(weight_kg) if weight_kg not in (None, "") else None
    except Exception:
        w = None
    try:
        age_m = int(age_months)
    except Exception:
        age_m = None

    apap_perkg_min = 10
    apap_perkg_max = 15
    apap_daily_max_mg_perkg = 60
    apap_adult_max_mg = 3000
    ibu_perkg = 10
    ibu_daily_max_mg_perkg = 40
    ibu_min_age_months = 6

    if w:
        apap_once_min = int(round(apap_perkg_min * w))
        apap_once_max = int(round(apap_perkg_max * w))
        apap_daily_cap = int(min(apap_daily_max_mg_perkg * w, apap_adult_max_mg))
        ibu_once = int(round(ibu_perkg * w))
        ibu_daily_cap = int(round(ibu_daily_max_mg_perkg * w))
        md.append(f"- **아세트아미노펜(APAP)**: {apap_once_min}–{apap_once_max} mg 1회 (q4–6h), 1일 최대 {apap_daily_cap} mg")
        if age_m is not None and age_m < ibu_min_age_months:
            md.append(f"- **이부프로펜(IBU)**: `6개월 미만 금기` (현재 {age_m}개월). 의사 상담 권장")
        else:
            md.append(f"- **이부프로펜(IBU)**: {ibu_once} mg 1회 (q6–8h), 1일 최대 {ibu_daily_cap} mg")
    else:
        md.append("- 체중이 입력되지 않아 정밀 용량을 계산할 수 없습니다.")

    md.append("**주의/응급 신호(요약)**")
    for f in [
        "3개월 미만 발열(38.0℃ 이상)",
        "탈수 의심: 입 마름, 소변 감소, 보채거나 처짐",
        "48시간 이상 지속되는 고열 혹은 점점 악화",
        "경련, 심한 구토, 호흡곤란, 발진 동반",
    ]:
        md.append(f"- {f}")
    return md

with t_peds:
    st.markdown("#### 소아 증상 & 해열제")
    with st.expander("👶 소아 정밀 복용량 계산", expanded=False):
        c1, c2 = st.columns(2)
        weight_kg = c1.number_input("체중(kg)", min_value=0.0, max_value=120.0, value=float(st.session_state.get("peds_w_kg", 0) or 0), step=0.5, key=wkey("peds_w_kg"))
        age_m = c2.number_input("개월 수", min_value=0, max_value=216, value=int(st.session_state.get("peds_age_m", 0) or 0), step=1, key=wkey("peds_age_m"))
        if st.button("계산", key=wkey("peds_precision_calc")):
            for ln in _peds_precision_block(weight_kg, age_m):
                st.write(ln)

    st.markdown("---")
    st.markdown("#### 해열제 스케줄(KST 기준)")
    tz = _dt.timezone(_dt.timedelta(hours=9))  # Asia/Seoul
    today = _dt.date.today()
    now = _dt.datetime.now(tz=tz)
    c1, c2 = st.columns(2)
    with c1:
        apap_last = st.time_input("마지막 APAP(아세트아미노펜) 복용 시각", value=now.time(), key=wkey("kst_apap_last"))
    with c2:
        ibu_last  = st.time_input("마지막 IBU(이부프로펜) 복용 시각", value=now.time(), key=wkey("kst_ibu_last"))
    try:
        apap_dt = _dt.datetime.combine(today, apap_last, tzinfo=tz)
        ibu_dt  = _dt.datetime.combine(today,  ibu_last,  tzinfo=tz)
        next_apap = apap_dt + _dt.timedelta(hours=4)
        next_ibu  = ibu_dt  + _dt.timedelta(hours=6)
        st.caption("쿨다운 규칙: APAP ≥ 4시간, IBU ≥ 6시간 (한국시간 기준).")
        colNA, colNI = st.columns(2)
        with colNA:
            st.metric("다음 APAP 가능 시각 (KST)", next_apap.strftime("%Y-%m-%d %H:%M KST"))
        with colNI:
            st.metric("다음 IBU 가능 시각 (KST)", next_ibu.strftime("%Y-%m-%d %H:%M KST"))
    except Exception:
        st.info("시각 입력을 다시 확인해주세요.")
    st.markdown("---")

# ---------- 특수검사(자리표시자) ----------
with t_special:
    st.markdown("#### 특수검사")
    st.write("특수검사 해석 모듈과 연동할 수 있습니다.")

# ---------- 보고서 ----------
with t_report:
    st.markdown("### 보고서 (.md/.txt/.pdf) — 모든 항목 포함")
    col_report, col_side = st.columns([2, 1])
    with col_report:
        st.markdown("#### 보고서 설정")
        opt_profile = st.checkbox("프로필/활력/모드", value=True, key=wkey("report3_profile"))
        opt_onco   = st.checkbox("항암제 요약/부작용/병용경고", value=True, key=wkey("report3_onco"))
        opt_labs   = st.checkbox("피수치 전항목", value=True, key=wkey("report3_labs"))
        opt_diet   = st.checkbox("식이가이드(샘플)", value=False, key=wkey("report3_diet"))

        # Compose markdown
        md = "# BloodMap 보고서\n\n"
        md += f"- 생성시각(KST): {now_kst().strftime('%Y-%m-%d %H:%M')}\n"

        # Labs
        if opt_labs:
            hist = st.session_state.get("lab_history", [])
            if hist:
                last = hist[-1]
                labs_line = ", ".join([f"{k}:{v}" for k,v in (last.get('labs') or {}).items() if str(v).strip() != ""]) or "—"
                md += "\n## 최근 주요 수치\n" + labs_line + "\n"
            else:
                md += "\n## 최근 주요 수치\n—\n"

        # Onco AE
        if opt_onco:
            meds = list((DRUG_DB or {}).keys())[:3]
            ae_map = _aggregate_all_aes(meds, DRUG_DB)
            md += "\n## 항암제 부작용(선택 약물)\n"
            if ae_map:
                for k, arr in ae_map.items():
                    label = display_label(k, DRUG_DB)
                    md += f"### {label}\n"
                    for ln in arr or []:
                        md += f"- {ln}\n"
            else:
                md += "- (DB에 상세 부작용 없음)\n"

        # Diet sample
        if opt_diet:
            md += "\n## 식이 가이드(샘플)\n- 수분 충분히 섭취\n- 매운 음식 일시 제한\n"

        st.markdown("#### 미리보기")
        st.code(md, language="markdown")
        st.download_button("💾 보고서 .md 다운로드", data=md.encode("utf-8"), file_name="bloodmap_report.md", mime="text/markdown")
        txt_data = md.replace("**", "")
        st.download_button("📝 보고서 .txt 다운로드", data=txt_data.encode("utf-8"), file_name="bloodmap_report.txt", mime="text/plain")
        try:
            pdf_bytes = export_md_to_pdf(md)
            st.download_button("📄 보고서 .pdf 다운로드", data=pdf_bytes, file_name="bloodmap_report.pdf", mime="application/pdf")
        except Exception:
            st.caption("PDF 변환 모듈을 불러오지 못했습니다. .md 또는 .txt를 사용해주세요.")

    with col_side:
        st.info("📊 기록/그래프는 상단의 **📊 기록/그래프** 탭에서 확인하세요.")

# ---------- 그래프 전용 탭 ----------
def render_graph_panel():
    st.markdown("### 📊 기록/그래프(파일 + 세션기록)")

    base_dir = "/mnt/data/bloodmap_graph"
    try:
        os.makedirs(base_dir, exist_ok=True)
    except Exception:
        pass

    # 파일 로딩
    csv_files = []
    try:
        csv_files = [os.path.join(base_dir, f) for f in os.listdir(base_dir) if f.lower().endswith(".csv")]
    except Exception:
        csv_files = []

    file_map = {os.path.basename(p): p for p in csv_files}
    has_csv = bool(file_map)

    src_options = ["세션 기록"] if not has_csv else ["세션 기록", "CSV 파일"]
    src_key = wkey("g2_mode_session_only") if not has_csv else wkey("g2_mode")
    mode = st.radio("데이터 소스", src_options, horizontal=True, key=src_key)

    df = None
    hist = st.session_state.get("lab_history", [])

    if mode == "CSV 파일":
        sel_name = st.selectbox("기록 파일 선택", sorted(file_map.keys()), key=wkey("g2_csv_select"))
        path = file_map[sel_name]
        try:
            df = pd.read_csv(path)
        except Exception as e:
            st.error(f"CSV를 읽을 수 없습니다: {e}")
            df = None
    else:
        if not hist:
            st.info("세션 기록이 없습니다. 📄 보고서 옆 ‘피수치 입력’ 탭에서 값을 추가하세요.")
        else:
            rows = []
            for h in hist:
                row = {"ts": h.get("ts", "")}
                labs = (h.get("labs") or {})
                for k,v in labs.items():
                    row[k] = v
                rows.append(row)
            if rows:
                df = pd.DataFrame(rows)
                try:
                    df["ts"] = pd.to_datetime(df["ts"])
                except Exception:
                    pass

    if df is None:
        return

    # 시간축 정렬/정규화
    time_col = None
    for cand in ["ts", "date", "Date", "timestamp", "Timestamp", "time", "Time", "sample_time"]:
        if cand in df.columns:
            time_col = cand
            break
    if time_col is None:
        df["_ts"] = range(len(df))
        time_col = "_ts"
    else:
        try:
            df["_ts"] = pd.to_datetime(df[time_col])
            time_col = "_ts"
        except Exception:
            pass

    # 항목 선택
    candidates = ["WBC", "Hb", "PLT", "CRP", "ANC", "Na", "Cr", "BUN", "AST", "ALT", "Glu"]
    cols_avail = [c for c in candidates if c in df.columns]
    if not cols_avail:
        cols_avail = [c for c in df.columns if c not in ["_ts", "ts", "date", "Date", "timestamp", "Timestamp", "time", "Time", "sample_time"]]

    picks = st.multiselect("그래프 항목 선택", options=cols_avail, default=cols_avail[:4], key=wkey("g2_cols"))

    # 기간 필터
    period = st.radio("기간", ("전체", "최근 7일", "최근 14일", "최근 30일"), horizontal=True, key=wkey("g2_period"))
    if period != "전체" and "datetime64" in str(df[time_col].dtype):
        days = {"최근 7일": 7, "최근 14일": 14, "최근 30일": 30}[period]
        cutoff = _dt.datetime.now() - _dt.timedelta(days=days)
        try:
            mask = df[time_col] >= cutoff
            df = df[mask]
        except Exception:
            pass

    if not picks:
        st.info("표시할 항목을 선택하세요.")
        return

    # 플롯
    if plt is None:
        st.warning("matplotlib이 없어 간단 표로 대체합니다.")
        st.dataframe(df[[time_col] + picks].tail(50))
    else:
        for m_ in picks:
            try:
                y = pd.to_numeric(df[m_], errors="coerce")
            except Exception:
                y = df[m_]
            fig, ax = plt.subplots()
            ax.plot(df[time_col], y, marker="o")
            ax.set_title(m_)
            ax.set_xlabel("시점")
            ax.set_ylabel(m_)
            fig.autofmt_xdate(rotation=45)
            st.pyplot(fig)

with t_graph:
    render_graph_panel()
