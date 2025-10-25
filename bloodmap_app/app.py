"""
app_classic_v2.py — 클래식 레이아웃(요청 순서 반영)
순서: 홈/응급도 → 소아 → 암 선택 → 항암제 → 특수검사 → 내보내기
- 패치 방식: 모든 실제 로직은 features/* 모듈에서 처리
- 핵심 가드(케어로그/해열제 가드/eGFR/응급 배너/그래프 외부저장/ER PDF·CSV/PIN 등) 보존
"""
import streamlit as st
import importlib

# ===== 공통 기본값 시딩 (화면 비어보임 방지) =====
def _seed_defaults():
    ss = st.session_state
    # 라우팅/표시 관련
    ss.setdefault("_lean_mode", True)
    ss.setdefault("_router_tab", "전체")
    ss.setdefault("_show_ae", True)
    ss.setdefault("_show_special", True)
    ss.setdefault("_show_exports", True)
    ss.setdefault("_show_peds", True)
    # 데이터 관련
    if "picked_keys" not in ss:
        ss["picked_keys"] = []
    if "DRUG_DB" not in ss:
        try:
            from drug_db import DRUG_DB as _DB
            ss["DRUG_DB"] = _DB
        except Exception:
            ss["DRUG_DB"] = {}

# ===== 홈/응급도 최상단 고정 렌더 =====
def _render_home_emergency(st):
    # 1) 모듈 우선
    for mod, fn in [
        ("features.home", "render_home"),
        ("features.emergency", "render_emergency_panel"),
        ("features.triage", "render_urgency"),
        ("features.overview", "render_dashboard"),
    ]:
        try:
            m = __import__(mod, fromlist=["_"])
            if hasattr(m, fn):
                getattr(m, fn)(st)
                return
        except Exception:
            pass
    # 2) 레거시 진입(있을 때만)
    try:
        _app = importlib.import_module("app")
        if hasattr(_app, "render_home"):
            getattr(_app, "render_home")(st)
            return
    except Exception:
        pass
    return

# ===== 암 빠른 선택 패널 =====
def _quick_pick_cancer(st):
    ss = st.session_state
    db = ss.get("DRUG_DB", {}) or {}
    picked = list(ss.get("picked_keys", []))

    st.markdown("### 🎗️ 암 빠른 선택")
    col1, col2 = st.columns([2,1])
    with col1:
        q = st.text_input("암/약물 검색", key="_q_cancer", placeholder="예: 위암, 유방암, Sunitinib ...")
    with col2:
        if st.button("선택 초기화", key="_clear_picks"):
            ss["picked_keys"] = []
            st.success("선택을 비웠습니다.")

    st.caption("자주 선택")
    chip_cols = st.columns(6)
    chips = ["유방암", "위암", "대장암", "폐암", "신장암", "혈액암"]
    for i, name in enumerate(chips):
        with chip_cols[i % 6]:
            if st.button(f"➕ {name}", key=f"_chip_{name}"):
                if name not in picked:
                    picked.append(name)

    if q:
        st.caption("검색 결과")
        hit_cols = st.columns(6)
        hits = []
        if isinstance(db, dict):
            for k, rec in db.items():
                label = str(rec.get("label") or k) if isinstance(rec, dict) else str(k)
                if q.lower() in label.lower() or q.lower() in str(k).lower():
                    hits.append(label)
                if len(hits) >= 12:
                    break
        pool = hits or [q]
        for i, name in enumerate(pool):
            with hit_cols[i % 6]:
                if st.button(f"➕ {name}", key=f"_hit_{name}"):
                    if name not in picked:
                        picked.append(name)

    if picked:
        st.caption("현재 선택")
        pill_cols = st.columns(6)
        for i, name in enumerate(picked):
            with pill_cols[i % 6]:
                if st.button(f"❌ {name}", key=f"_rm_{name}"):
                    picked = [x for x in picked if x != name]
        ss["picked_keys"] = picked
    else:
        st.caption("현재 선택 없음")

# ===== 상단 네비 리본(시각적) =====
def _top_nav(st):
    st.markdown(
        """
        <div style="position:sticky;top:0;z-index:999;background:var(--background-color,#ffffff);padding:.5rem 0 .25rem 0;border-bottom:1px solid #eee">
          <span style="margin-right:10px">🏠 홈/응급도</span>
          <span style="margin-right:10px">👶 소아</span>
          <span style="margin-right:10px">🎗️ 암 선택</span>
          <span style="margin-right:10px">💊 항암제</span>
          <span style="margin-right:10px">🧪 특수검사</span>
          <span style="margin-right:10px">📤 내보내기</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

def main():
    st.set_page_config(page_title="클래식 레이아웃 v2", layout="wide")
    _seed_defaults()
    ss = st.session_state
    picked_keys = ss.get("picked_keys", [])
    DRUG_DB = ss.get("DRUG_DB", {})

    # 사이드바 & 경량 모드
    try:
        from features.app_shell import render_sidebar as _shell
        _shell(st)
    except Exception:
        pass
    try:
        from features.app_deprecator import apply_lean_mode as _lean
        _lean(st)
    except Exception:
        pass

    # 상단 네비
    _top_nav(st)

    # === 0) 홈/응급도 — 최상단 고정 ===
    _render_home_emergency(st)

    # === 1) 소아 ===
    try:
        from features.pages.peds import render as _peds
        _peds(st)
    except Exception:
        pass

    # === 2) 암 선택(퀵 픽) ===
    _quick_pick_cancer(st)

    # === 3) 항암제(진단 기반) ===
    try:
        from features.pages.ae import render as _ae
        _ae(st, picked_keys, DRUG_DB)
    except Exception:
        pass

    # === 4) 특수검사 ===
    try:
        from features.pages.special import render as _special
        _special(st)
    except Exception:
        pass

    # === 5) 내보내기 ===
    try:
        from features.pages.exports import render as _exports
        _exports(st, picked_keys)
    except Exception:
        pass

    # (선택) 진단 패널
    try:
        try:
            from features.dev.diag_panel import render_diag_panel as _diag
        except Exception:
            from features_dev.diag_panel import render_diag_panel as _diag
        _diag(st)
    except Exception:
        pass

if __name__ == "__main__":
    main()
