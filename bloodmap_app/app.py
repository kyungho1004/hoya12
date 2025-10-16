
import os
import tempfile
from datetime import datetime
import pandas as pd
import streamlit as st

st.set_page_config(page_title="BloodMap", layout="wide", page_icon="🩸")

# =============================
# KST helpers
# =============================
try:
    from zoneinfo import ZoneInfo  # Python 3.9+
    _KST = ZoneInfo("Asia/Seoul")
except Exception:
    _KST = None

def kst_now() -> datetime:
    return datetime.now(_KST) if _KST else datetime.utcnow()

# =============================
# Inline Feedback Bundle (self‑contained)
# =============================
def _feedback_dir():
    for p in [
        os.environ.get("BLOODMAP_DATA_DIR"),
        os.path.join(os.path.expanduser("~"), ".bloodmap", "metrics"),
        "/mnt/data/metrics",
        "/mount/data/metrics",
        os.path.join(tempfile.gettempdir(), "bloodmap_metrics"),
    ]:
        if not p:
            continue
        try:
            os.makedirs(p, exist_ok=True)
            probe = os.path.join(p, ".probe")
            with open(probe, "w", encoding="utf-8") as f:
                f.write("ok")
            os.remove(probe)
            return p
        except Exception:
            continue
    p = os.path.join(tempfile.gettempdir(), "bloodmap_metrics")
    os.makedirs(p, exist_ok=True)
    return p

_FB_DIR = _feedback_dir()
_FEEDBACK_CSV = os.path.join(_FB_DIR, "feedback.csv")

def _atomic_save_csv(df: pd.DataFrame, path: str) -> None:
    tmp = path + ".tmp"
    df.to_csv(tmp, index=False)
    os.replace(tmp, path)

# hint helper (no-op if caller didn't define it elsewhere)
def set_current_tab_hint(name: str):
    st.session_state["_bm_current_tab"] = name

def render_feedback_box(default_category: str = "일반 의견", page_hint: str = "") -> None:
    """Unique form/widget keys per page_hint to avoid Streamlit duplicate key errors."""
    if not os.path.exists(_FEEDBACK_CSV):
        cols = ["ts_kst","name_or_nick","contact","category","rating","message","page"]
        _atomic_save_csv(pd.DataFrame(columns=cols), _FEEDBACK_CSV)

    categories = ["버그 제보","개선 요청","기능 아이디어","데이터 오류 신고","일반 의견"]
    try:
        default_index = categories.index(default_category)
    except ValueError:
        default_index = categories.index("일반 의견")

    key_suffix = (page_hint or "Sidebar").replace(" ", "_")

    with st.form(f"feedback_form_{key_suffix}", clear_on_submit=True):
        name = st.text_input("이름/별명 (선택)", key=f"fb_name_{key_suffix}")
        contact = st.text_input("연락처(이메일/카톡ID, 선택)", key=f"fb_contact_{key_suffix}")
        category = st.selectbox("분류", categories, index=default_index, key=f"fb_cat_{key_suffix}")
        rating = st.slider("전반적 만족도", 1, 5, 4, key=f"fb_rating_{key_suffix}")
        msg = st.text_area("메시지", placeholder="자유롭게 적어주세요.", key=f"fb_msg_{key_suffix}")
        if st.form_submit_button("보내기", use_container_width=True):
            row = {
                "ts_kst": kst_now().strftime("%Y-%m-%d %H:%M:%S"),
                "name_or_nick": (name or "").strip(),
                "contact": (contact or "").strip(),
                "category": category,
                "rating": int(rating),
                "message": (msg or "").strip(),
                "page": (page_hint or st.session_state.get("_bm_current_tab","")).strip(),
            }
            try:
                df = pd.read_csv(_FEEDBACK_CSV)
            except Exception:
                df = pd.DataFrame(columns=list(row.keys()))
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
            _atomic_save_csv(df, _FEEDBACK_CSV)
            st.success("고맙습니다! 피드백이 저장되었습니다. (KST 기준)")

def render_feedback_admin() -> None:
    pwd = st.text_input("관리자 비밀번호", type="password", key="fb_admin_pwd")
    admin_pw = st.secrets.get("ADMIN_PASS", "9047")
    if admin_pw and pwd == admin_pw:
        if os.path.exists(_FEEDBACK_CSV):
            try:
                df = pd.read_csv(_FEEDBACK_CSV)
            except Exception:
                df = pd.DataFrame(columns=["ts_kst","name_or_nick","contact","category","rating","message","page"])
            st.dataframe(df, use_container_width=True)
            st.download_button("CSV 다운로드", data=df.to_csv(index=False), file_name="feedback.csv", mime="text/csv", use_container_width=True)
        else:
            st.info("아직 피드백이 없습니다.")
    else:
        st.caption("올바른 비밀번호를 입력하면 목록이 표시됩니다." if admin_pw else "ADMIN_PASS가 설정되지 않았습니다.")

def attach_feedback_sidebar(page_hint: str = "Home") -> None:
    """Attach a sidebar feedback form. Internally uses page_hint='Sidebar' to avoid duplicate keys."""
    with st.sidebar:
        st.markdown("### 💬 의견 보내기")
        set_current_tab_hint("Sidebar")
        render_feedback_box(default_category="일반 의견", page_hint="Sidebar")
        st.markdown("---")
        render_feedback_admin()

# =============================
# Header / badge
# =============================
st.markdown("## BloodMap")
st.caption("세포·면역 치료(CAR-T, TCR-T, NK, HSCT 등)는 표기하지 않습니다.")

st.markdown(
    """
    <style>
    #bm-usage .chip{display:inline-block;padding:.22rem .55rem;border-radius:999px;
    font-weight:700;font-size:.95rem;border:1px solid rgba(0,0,0,.08);
    background:linear-gradient(180deg,#f8fafc,#eef2f7)}
    #bm-usage .dot{width:.5rem;height:.5rem;border-radius:999px;display:inline-block;
    margin-right:.35rem;background:#22c55e}
    </style>
    """, unsafe_allow_html=True
)
st.markdown('<div id="bm-usage"><span class="chip"><span class="dot"></span>현재 <strong>170</strong>명 이용중</span></div>', unsafe_allow_html=True)

st.markdown("---")

# =============================
# Tabs
# =============================
t_home, t_labs, t_cancer, t_chemo, t_peds, t_special, t_report, t_graph = st.tabs(
    ["Home", "Labs", "Cancer", "Chemo", "Peds", "Special Tests", "Report", "Graph/Log"]
)

with t_home:
    st.subheader("응급도 체크(증상 기반)")
    # ---- Demo emergency UI (placeholder) ----
    sympt = st.multiselect("증상 선택", ["발열", "의식저하", "흉통", "호흡곤란", "출혈", "구토"], [])
    level = "높음" if any(s in sympt for s in ["의식저하", "호흡곤란", "흉통"]) else ("중간" if "발열" in sympt else "낮음")
    if level == "높음":
        st.error("응급도: " + level)
    elif level == "중간":
        st.warning("응급도: " + level)
    else:
        st.info("응급도: " + level)

    # --- 의견/피드백: 응급도 체크 바로 아래 ---
    st.markdown("### 💬 응급도 체크에 대한 의견")
    set_current_tab_hint("응급도 체크")
    render_feedback_box(default_category="데이터 오류 신고", page_hint="응급도 체크")
    render_feedback_admin()

    st.markdown("---")
    st.caption("여기는 Home 탭의 기타 영역입니다.")

with t_labs:
    st.subheader("Labs")
    st.write("Lab 모듈이 없어도 이 안내는 항상 보입니다.")

with t_cancer:
    st.subheader("Cancer")
    st.write("Cancer 모듈이 없어도 이 안내는 항상 보입니다.")

with t_chemo:
    st.subheader("Chemo")
    st.write("Chemo 모듈이 없어도 이 안내는 항상 보입니다.")

with t_peds:
    st.subheader("Peds")
    st.write("Peds 모듈이 없어도 이 안내는 항상 보입니다.")

with t_special:
    st.subheader("Special Tests")
    st.write("Special Tests 모듈이 없어도 이 안내는 항상 보입니다.")

with t_report:
    st.subheader("Report")
    st.write("Report 모듈이 없어도 이 안내는 항상 보입니다.")

with t_graph:
    st.subheader("Graph/Log")
    st.write("Graph/Log 모듈이 없어도 이 안내는 항상 보입니다.")

# =============================
# Sidebar feedback (always on)
# =============================
attach_feedback_sidebar(page_hint="Home")
