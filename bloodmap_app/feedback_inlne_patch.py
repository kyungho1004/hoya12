
import os
from datetime import datetime
from typing import Tuple
import pandas as pd
import streamlit as st

try:
    from zoneinfo import ZoneInfo  # Python 3.9+
    _KST = ZoneInfo("Asia/Seoul")
except Exception:
    _KST = None

_METRICS_DIR = "/mnt/data/metrics"
_USAGE_CSV = os.path.join(_METRICS_DIR, "usage_stats.csv")
_FEEDBACK_CSV = os.path.join(_METRICS_DIR, "feedback.csv")

def _kst_now() -> datetime:
    if _KST is not None:
        return datetime.now(_KST)
    return datetime.utcnow()

def _today_str() -> str:
    return _kst_now().strftime("%Y-%m-%d")

def _ensure_metrics_dir() -> None:
    os.makedirs(_METRICS_DIR, exist_ok=True)

def _ensure_usage_file() -> None:
    _ensure_metrics_dir()
    if not os.path.exists(_USAGE_CSV):
        pd.DataFrame(columns=["date", "daily_opens"]).to_csv(_USAGE_CSV, index=False)

def _ensure_feedback_file() -> None:
    _ensure_metrics_dir()
    if not os.path.exists(_FEEDBACK_CSV):
        cols = ["ts_kst", "name_or_nick", "contact", "category", "rating", "message", "page"]
        pd.DataFrame(columns=cols).to_csv(_FEEDBACK_CSV, index=False)

def _load_usage_df() -> pd.DataFrame:
    _ensure_usage_file()
    try:
        return pd.read_csv(_USAGE_CSV)
    except Exception:
        return pd.DataFrame(columns=["date", "daily_opens"])

def _save_usage_df(df: pd.DataFrame) -> None:
    tmp = _USAGE_CSV + ".tmp"
    df.to_csv(tmp, index=False)
    os.replace(tmp, _USAGE_CSV)

def increment_daily_session_once(session_key: str = "_bm_session_counted") -> None:
    if st.session_state.get(session_key):
        return
    st.session_state[session_key] = True
    df = _load_usage_df()
    today = _today_str()
    if (df["date"] == today).any():
        df.loc[df["date"] == today, "daily_opens"] = df.loc[df["date"] == today, "daily_opens"].fillna(0).astype(int) + 1
    else:
        df = pd.concat([df, pd.DataFrame([{"date": today, "daily_opens": 1}])], ignore_index=True)
    _save_usage_df(df)

def get_usage_metrics():
    df = _load_usage_df()
    today = _today_str()
    if df.empty:
        daily = 0
        total = 0
        last7 = pd.DataFrame(columns=["date", "daily_opens"])
    else:
        daily = int(df.loc[df["date"] == today, "daily_opens"].sum())
        total = int(df["daily_opens"].fillna(0).astype(int).sum())
        last7 = df.tail(7).copy()
    return daily, total, last7

def render_usage_panel() -> None:
    increment_daily_session_once()
    daily, total, last7 = get_usage_metrics()
    c1, c2 = st.columns(2)
    c1.metric("오늘 방문(세션)", f"{daily}명", help="한국시간(KST) 기준 오늘 이 앱을 연 세션 수")
    c2.metric("누적 방문(세션)", f"{total}명", help="배포 이후 누적 세션 수")
    if not last7.empty:
        st.caption("최근 7일 방문 추이")
        st.line_chart(last7.set_index("date")["daily_opens"])

def set_current_tab_hint(name: str) -> None:
    st.session_state["_bm_current_tab"] = name

def render_feedback_box(default_category: str = "일반 의견", page_hint: str = "") -> None:
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
            rating = st.slider("전반적 만족도", min_value=1, max_value=5, value=4)
            msg = st.text_area("메시지", placeholder="자유롭게 적어주세요. (예: 어떤 화면에서 어떤 문제가 발생했는지, 원하는 기능 등)")
            submitted = st.form_submit_button("보내기")
            if submitted:
                ts = _kst_now().strftime("%Y-%m-%d %H:%M:%S")
                row = {
                    "ts_kst": ts,
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

def render_feedback_admin() -> None:
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
