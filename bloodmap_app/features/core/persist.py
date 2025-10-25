"""
Core persistence helpers — non-intrusive status panel for PIN/Profile/Graphs dirs.
This does NOT change existing save logic; only ensures directories and displays paths.
"""
from __future__ import annotations
import os

PROFILE_DIR = "/mnt/data/profile"
GRAPH_DIR = "/mnt/data/bloodmap_graph"
CARE_DIR = "/mnt/data/care_log"

def _ensure_dir(p: str):
    try:
        os.makedirs(p, exist_ok=True)
    except Exception:
        pass

def render_persist_status(st):
    try:
        _ensure_dir(PROFILE_DIR)
        _ensure_dir(GRAPH_DIR)
        _ensure_dir(CARE_DIR)
        with st.expander("저장 경로 상태(프로필·그래프·케어로그)", expanded=False):
            st.markdown(f"- 프로필: **{PROFILE_DIR}**")
            st.markdown(f"- 그래프 외부저장: **{GRAPH_DIR}**")
            st.markdown(f"- 케어로그: **{CARE_DIR}**")
            st.caption("※ 경로만 보조 표시합니다. 저장 로직은 기존 코드가 담당합니다.")
    except Exception:
        pass
