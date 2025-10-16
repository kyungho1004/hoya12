
import os
from datetime import datetime
import pandas as pd
import streamlit as st

# ---- KST helpers ----
try:
    from zoneinfo import ZoneInfo
    _KST = ZoneInfo("Asia/Seoul")
except Exception:
    _KST = None

def kst_now():
    if _KST is not None:
        return datetime.now(_KST)
    from datetime import datetime as _dt
    return _dt.utcnow()

def today_str():
    return kst_now().strftime("%Y-%m-%d")

# ---- Safe import ----
def try_import(name: str):
    try:
        return __import__(name)
    except Exception:
        return None

def safe_call(fn, *a, **k):
    try:
        if callable(fn):
            return fn(*a, **k)
    except Exception as e:
        st.warning(f"모듈 실행 중 오류가 발생했지만 앱은 계속 동작합니다: {e}")

branding = try_import("branding")
ui_results = try_import("ui_results")
special_tests = try_import("special_tests")
peds_dose = try_import("peds_dose")
pdf_export = try_import("pdf_export")
onco_map = try_import("onco_map")
drug_db = try_import("drug_db")
lab_diet = try_import("lab_diet")

# ---- Usage & Feedback (inline) ----
_METRICS_DIR = "/mnt/data/metrics"
_USAGE_CSV = os.path.join(_METRICS_DIR, "usage_stats.csv")
_FEEDBACK_CSV = os.path.join(_METRICS_DIR, "feedback.csv")

def _ensure_metrics_dir():
    os.makedirs(_METRICS_DIR, exist_ok=True)

def _ensure_usage_file():
    _ensure_metrics_dir()
    if not os.path.exists(_USAGE_CSV):
        pd.DataFrame(columns=["date", "daily_opens"]).to_csv(_USAGE_CSV, index=False)

def _ensure_feedback_file():
    _ensure_metrics_dir()
    if not os.path.exists(_FEEDBACK_CSV):
        cols = ["ts_kst", "name_or_nick", "contact", "category", "rating", "message", "page"]
        pd.DataFrame(columns=cols).to_csv(_FEEDBACK_CSV, index=False)

def increment_daily_session_once(session_key: str = "_bm_session_counted"):
    if st.session_state.get(session_key):
        return
    st.session_state[session_key] = True
    _ensure_usage_file()
    try:
        df = pd.read_csv(_USAGE_CSV)
    except Exception:
        df = pd.DataFrame(columns=["date", "daily_opens"])
    t = today_str()
    if (df["date"] == t).any():
        df.loc[df["date"] == t, "daily_opens"] = df.loc[df["date"] == t, "daily_opens"].fillna(0).astype(int) + 1
    else:
        df = pd.concat([df, pd.DataFrame([{"date": t, "daily_opens": 1}])], ignore_index=True)
    tmp = _USAGE_CSV + ".tmp"
    df.to_csv(tmp, index=False)
    os.replace(tmp, _USAGE_CSV)

def get_usage_metrics():
    _ensure_usage_file()
    try:
        df = pd.read_csv(_USAGE_CSV)
    except Exception:
        df = pd.DataFrame(columns=["date", "daily_opens"])
    t = today_str()
    daily = int(df.loc[df["date"] == t, "daily_opens"].sum()) if not df.empty else 0
    total = int(df["daily_opens"].fillna(0).astype(int).sum()) if not df.empty else 0
    last7 = df.tail(7).copy() if not df.empty else pd.DataFrame(columns=["date", "daily_opens"])
    return daily, total, last7

def render_usage_panel():
    increment_daily_session_once()
    daily, total, last7 = get_usage_metrics()
    c1, c2 = st.columns(2)
    c1.metric("오늘 방문(세션)", f"{daily}명", help="한국시간(KST) 기준 오늘 이 앱을 연 세션 수")
    c2.metric("누적 방문(세션)", f"{total}명", help="배포 이후 누적 세션 수")
    if not last7.empty:
        st.caption("최근 7일 방문 추이")
        st.line_chart(last7.set_index("date")["daily_opens"])

def set_current_tab_hint(name: str):
    st.session_state["_bm_current_tab"] = name

def render_feedback_box(default_category: str = "일반 의견", page_hint: str = ""):
    _ensure_feedback_file()
    categories = ["버그 제보", "개선 요청", "기능 아이디어", "데이터 오류 신고", "일반 의견"]
    try:
        default_index = categories.index(default_category)
    except ValueError:
        default_index = categories.index("일반 의견")
    with st.expander("💬 피드백 보내기 (익명 가능)", expanded=False):
        with st.form("feedback_form", clear_on_submit=True):
            name = st.text_input("이름/별명 (선택)", key="fb_name")
            contact = st.text_input("연락처(이메일/카톡ID, 선택)", key="fb_contact")
            category = st.selectbox("분류", categories, index=default_index)
            rating = st.slider("전반적 만족도", 1, 5, 4)
            msg = st.text_area("메시지", placeholder="자유롭게 적어주세요. (예: 어떤 화면에서 어떤 문제가 발생했는지, 원하는 기능 등)")
            submitted = st.form_submit_button("보내기")
            if submitted:
                row = {
                    "ts_kst": kst_now().strftime("%Y-%m-%d %H:%M:%S"),
                    "name_or_nick": (name or "").strip(),
                    "contact": (contact or "").strip(),
                    "category": category,
                    "rating": int(rating),
                    "message": (msg or "").strip(),
                    "page": (page_hint or st.session_state.get("_bm_current_tab", "")).strip(),
                }
                try:
                    df = pd.read_csv(_FEEDBACK_CSV)
                except Exception:
                    df = pd.DataFrame(columns=list(row.keys()))
                df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
                df.to_csv(_FEEDBACK_CSV, index=False)
                st.success("고맙습니다! 피드백이 안전하게 저장되었습니다. (KST 기준 시각 기록)")

def render_feedback_admin():
    _ensure_feedback_file()
    with st.expander("🛠 관리자 피드백 보기", expanded=False):
        pwd = st.text_input("관리자 비밀번호", type="password")
        admin_pw = st.secrets.get("ADMIN_PASS", "")
        if admin_pw and pwd == admin_pw:
            if os.path.exists(_FEEDBACK_CSV):
                try:
                    df = pd.read_csv(_FEEDBACK_CSV)
                except Exception:
                    df = pd.DataFrame(columns=["ts_kst","name_or_nick","contact","category","rating","message","page"])
                st.dataframe(df, use_container_width=True)
                st.download_button("CSV 다운로드", data=df.to_csv(index=False), file_name="feedback.csv", mime="text/csv")
            else:
                st.info("아직 피드백이 없습니다.")
        else:
            if admin_pw:
                st.caption("올바른 비밀번호를 입력하면 목록이 표시됩니다.")
            else:
                st.caption("관리자 비밀번호(ADMIN_PASS)가 설정되지 않았습니다. Streamlit Secrets에 ADMIN_PASS를 등록하세요.")

# ---- CSS badge for 170 users ----
def _inject_usage_css_once():
    key = "_bm_usage_css"
    if st.session_state.get(key):
        return
    st.session_state[key] = True
    st.markdown(
        """
        <style>
        #bm-usage { display:flex; gap:.5rem; align-items:center; margin: .25rem 0 .75rem 0; }
        #bm-usage .chip {
          display:inline-block; padding:.22rem .55rem; border-radius:999px;
          font-weight:700; font-size:.95rem; border:1px solid rgba(0,0,0,.08);
          background:linear-gradient(180deg, #f8fafc, #eef2f7);
        }
        #bm-usage .chip .dot { width:.5rem; height:.5rem; border-radius:999px; display:inline-block; margin-right:.35rem; background:#22c55e; }
        </style>
        """,
        unsafe_allow_html=True,
    )

def render_usage_badge(count: int = 170):
    _inject_usage_css_once()
    st.markdown(
        f"""
        <div id="bm-usage">
          <div class="chip"><span class="dot"></span>현재 <strong>{count}</strong>명 이용중</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---- Page header ----
st.set_page_config(page_title="BloodMap", layout="wide", page_icon="🩸")
st.markdown("## BloodMap")

branding = try_import("branding")
if branding and hasattr(branding, "render_deploy_banner"):
    try:
        branding.render_deploy_banner("https://bloodmap.streamlit.app/", "제작: Hoya/GPT · 자문: Hoya/GPT")
    except Exception:
        st.caption("제작: Hoya/GPT · 자문: Hoya/GPT · 한국시간(KST) 기준 · *세포·면역 치료는 표기하지 않습니다*")
else:
    st.caption("제작: Hoya/GPT · 자문: Hoya/GPT · 한국시간(KST) 기준 · *세포·면역 치료는 표기하지 않습니다*")

st.info("혼돈 방지 및 범위 밖 안내: 저희는 **세포·면역 치료(CAR-T, TCR-T, NK, HSCT 등)**는 표기하지 않습니다.", icon="ℹ️")

render_usage_badge(170)
render_usage_panel()

st.markdown("---")

tabs = st.tabs(["Home", "Labs", "Cancer", "Chemo", "Peds", "Special Tests", "Report", "Graph/Log"])

# Home
with tabs[0]:
    set_current_tab_hint("Home")
    st.markdown("### 소개")
    st.caption("그래프는 오른쪽 마지막 탭에서만 표시. 소아 KST 스케줄/정밀용량, 응급도(가중치) 평가 포함.")
    ui_results = try_import("ui_results")
    if ui_results:
        for fn_name in ["render_home", "render_ui_home", "render_intro", "render"]:
            if hasattr(ui_results, fn_name):
                safe_call(getattr(ui_results, fn_name)); break
    st.markdown("### 의견 보내기")
    render_feedback_box(default_category="개선 요청", page_hint="Home")
    render_feedback_admin()

# Labs
with tabs[1]:
    set_current_tab_hint("Labs")
    st.markdown("### Lab 해석")
    ui_results = try_import("ui_results")
    if ui_results:
        for fn_name in ["render_labs", "render_lab_tab", "render_main"]:
            if hasattr(ui_results, fn_name):
                safe_call(getattr(ui_results, fn_name)); break
    lab_diet = try_import("lab_diet")
    if lab_diet and hasattr(lab_diet, "render_lab_diet"):
        safe_call(lab_diet.render_lab_diet)

# Cancer
with tabs[2]:
    set_current_tab_hint("Cancer")
    st.markdown("### 암 진단/맵")
    onco_map = try_import("onco_map")
    if onco_map:
        for fn_name in ["render_onco_map", "render", "render_cancer"]:
            if hasattr(onco_map, fn_name):
                safe_call(getattr(onco_map, fn_name)); break

# Chemo
with tabs[3]:
    set_current_tab_hint("Chemo")
    st.markdown("### 항암제/부작용")
    drug_db = try_import("drug_db")
    if drug_db and hasattr(drug_db, "render_drug_db"):
        safe_call(drug_db.render_drug_db)
    onco_map = try_import("onco_map")
    if onco_map and hasattr(onco_map, "render_chemo"):
        safe_call(onco_map.render_chemo)
    peds_dose = try_import("peds_dose")
    if peds_dose and hasattr(peds_dose, "render_peds_dose"):
        safe_call(peds_dose.render_peds_dose)

# Peds
with tabs[4]:
    set_current_tab_hint("Peds")
    st.markdown("### 소아 가이드")
    ui_results = try_import("ui_results")
    if ui_results:
        for fn_name in ["render_peds", "render_peds_tab"]:
            if hasattr(ui_results, fn_name):
                safe_call(getattr(ui_results, fn_name)); break

# Special Tests
with tabs[5]:
    set_current_tab_hint("Special Tests")
    st.markdown("### 특수 검사")
    special_tests = try_import("special_tests")
    if special_tests:
        for fn_name in ["render_special_tests", "render", "render_tab"]:
            if hasattr(special_tests, fn_name):
                safe_call(getattr(special_tests, fn_name)); break

# Report
with tabs[6]:
    set_current_tab_hint("Report")
    st.markdown("### 보고서")
    pdf_export = try_import("pdf_export")
    if pdf_export and hasattr(pdf_export, "render_report"):
        safe_call(pdf_export.render_report)
    else:
        st.caption("보고서(.md/.pdf) 내보내기는 곧 제공됩니다.")

# Graph/Log
with tabs[7]:
    set_current_tab_hint("Graph/Log")
    st.markdown("### 그래프/로그")
    ui_results = try_import("ui_results")
    if ui_results:
        for fn_name in ["render_graphlog", "render_graph", "render_log"]:
            if hasattr(ui_results, fn_name):
                safe_call(getattr(ui_results, fn_name)); break
    st.caption("핀 그래프·케어로그는 외부 저장 경로 유지(/mnt/data/bloodmap_graph).")
