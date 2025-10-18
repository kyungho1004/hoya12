# app_patch_mobile.py  — 모바일 안정/딥링크/상단바/라디오 네비/피드백 원자저장 + 소아(안정) 폼
import streamlit as st
import json as _json, uuid as _uuid, datetime as _dt
from pathlib import Path as _Path
import os as _os

# -------------------- (A) 딥링크 라우팅 + 상단 고정 안전바 + 라디오 네비 --------------------
def _apply_query_routing():
    try:
        qp = st.query_params if hasattr(st, "query_params") else {}
    except Exception:
        qp = {}
    view = str(qp.get("view","")).lower() if isinstance(qp, dict) else ""
    mode = str(qp.get("mode","")).lower() if isinstance(qp, dict) else ""
    if view == "home" and mode in ("","stable"):
        st.session_state["home_emerg_stable"] = True
    if view == "peds" and mode in ("","stable"):
        st.session_state["peds_stable_mode"] = True

def _sticky_safety_bar():
    st.markdown("""<style>
    .sticky-bar{position:sticky;top:0;z-index:999}
    .sticky-wrap{background:#f8fafc;padding:6px 10px;border-bottom:1px solid #e2e8f0;border-radius:8px}
    .pill{display:inline-block;padding:2px 8px;border-radius:999px;font-weight:600;margin-right:6px}
    .pill-green{background:#dcfce7;color:#166534}.pill-yellow{background:#fef9c3;color:#854d0e}.pill-red{background:#fee2e2;color:#991b1b}
    </style>""", unsafe_allow_html=True)
    level = st.session_state.get("safety_level","")
    msg = st.session_state.get("safety_msg","")
    if not msg:
        if st.session_state.get("home_emerg_stable", False) or st.session_state.get("peds_stable_mode", False):
            msg = "안정 모드 활성화 — 입력 중 리런 최소화"
        else:
            msg = "일반 모드 — 필요 시 안정 모드 토글 사용"
    pill = {"green":"pill-green","yellow":"pill-yellow","red":"pill-red"}.get(level,"")
    html = '<div class="sticky-bar"><div class="sticky-wrap">'
    if pill: html += f'<span class="pill {pill}">{level.upper()}</span>'
    html += f'<span>{msg}</span></div></div>'
    st.markdown(html, unsafe_allow_html=True)

def _render_mobile_nav():
    st.session_state.setdefault("nav_radio_main", "기본탭")
    nav = st.radio("이동", ["기본탭","홈(안정)","소아(안정)"], key="nav_radio_main", horizontal=True)
    if nav == "홈(안정)":
        st.session_state["home_emerg_stable"] = True
    elif nav == "소아(안정)":
        st.session_state["peds_stable_mode"] = True

# -------------------- (B) 소아(안정 모드) 폼: 변비/설사/구토 + URI 통합 섹션 --------------------
def _render_peds_stable_form():
    try:
        from peds_guide import (
            render_section_constipation,
            render_section_diarrhea,
            render_section_vomit,
        )
        try:
            from peds_guide import render_section_uri_general as _render_uri
        except Exception:
            _render_uri = None
    except Exception:
        return  # peds_guide 없으면 조용히 통과

    st.info("🧒 소아(안정 모드): 폼으로 표시됩니다. 변경 후 '입력 업데이트'를 눌러 반영됩니다.")
    with st.form("peds_stable_form"):
        render_section_constipation()
        render_section_diarrhea()
        render_section_vomit()
        if _render_uri: _render_uri()
        st.form_submit_button("입력 업데이트")

# -------------------- (C) 피드백: 일일 중복 방지 + 원자 저장 --------------------
def _fb_today_dir():
    d = _Path("/mnt/data/feedback/entries") / _dt.datetime.utcnow().strftime("%Y%m%d")
    d.mkdir(parents=True, exist_ok=True)
    return d

def _fb_signature(section: str, rating: int, text: str) -> str:
    base = f"{section}|{rating}|{(text or '').strip()}".strip()
    return str(abs(hash(base)))

def _fb_already_exists(sig: str) -> bool:
    d = _fb_today_dir()
    for p in d.glob("*.json"):
        try:
            data = _json.loads(p.read_text(encoding="utf-8"))
            if data.get("sig")==sig:
                return True
        except Exception:
            continue
    return False

def save_feedback_atomic(section: str, rating: int, text: str, extra: dict=None) -> bool:
    sig = _fb_signature(section, rating, text)
    if st.session_state.get("fb_sig_today") == sig:
        return False
    if _fb_already_exists(sig):
        st.session_state["fb_sig_today"] = sig
        return False
    payload = {
        "ts": _dt.datetime.utcnow().isoformat()+"Z",
        "section": section, "rating": int(rating), "text": (text or ""),
        "sig": sig, "meta": (extra or {}),
    }
    d = _fb_today_dir()
    tmp = d / f"{_uuid.uuid4().hex}.tmp"
    out = d / f"{payload['ts'].replace(':','').replace('.','_')}_{sig}.json"
    tmp.write_text(_json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    _os.replace(tmp, out)
    st.session_state["fb_sig_today"] = sig
    return True

# -------------------- (D) 초기 진입 지점 --------------------
def init_top():
    _apply_query_routing()
    _sticky_safety_bar()
    _render_mobile_nav()
    # 소아 안정 모드면 탭 렌더 전에 여기서 소아만 표시하고 종료
    if st.session_state.get("peds_stable_mode", False):
        _render_peds_stable_form()
        st.stop()
    # 홈(안정)은 홈 탭 코드를 함수로 뺀 다음, app.py 내부에서 불러주면 안전함 (다음 라운드에 마이그레이션)
