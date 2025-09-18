
# -*- coding: utf-8 -*-
"""
onco_mini_toggle.py — 암 미니 패널 토글
- Streamlit 상단/중단 어디서든 끼워넣어 빠른 요약을 보여줍니다.
- 기존 세션 키를 최대한 재사용(analysis_ctx 등).
"""
from __future__ import annotations
from typing import Dict, List, Optional
import streamlit as st

def _join(items: Optional[List[str]]) -> str:
    if not items: return "선택 없음"
    return ", ".join(map(str, items))

def render_onco_mini(ctx: Optional[Dict] = None) -> None:
    """
    ctx: app.py에서 st.session_state.get("analysis_ctx")를 그대로 넘겨도 OK.
    없으면 session_state에서 자동으로 가져옵니다.
    """
    if ctx is None:
        ctx = st.session_state.get("analysis_ctx", {})

    if not isinstance(ctx, dict):
        ctx = {}

    with st.expander("🧩 암 미니 패널", expanded=st.session_state.get("_onco_mini_open", True)):
        st.session_state["_onco_mini_open"] = True
        # 한 줄 요약
        mode = ctx.get("mode") or "암"
        dx_label = ctx.get("dx_label") or ctx.get("dx") or "진단 미선택"
        group = ctx.get("group") or "-"

        st.markdown(f"**모드:** {mode}  |  **카테고리:** {group}  |  **진단:** {dx_label}")

        # 약물 요약
        def _names(keys):
            from drug_db import display_label  # 지연 로드(호환성)
            keys = [k for k in (keys or []) if isinstance(k, str)]
            if not keys: return "선택 없음"
            return ", ".join(display_label(k) for k in keys)

        chemo    = _names(ctx.get("user_chemo"))
        targeted = _names(ctx.get("user_targeted"))
        abx      = _names(ctx.get("user_abx"))
        st.caption(f"**항암제:** {chemo}")
        st.caption(f"**표적/면역:** {targeted}")
        st.caption(f"**항생제:** {abx}")

        # 빠른 액션
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("🔁 미니 새로고침"):
                st.experimental_rerun()
        with c2:
            if st.button("🧾 미니 요약 복사"):
                summary = f"{group} / {dx_label} | 항암제: {chemo} | 표적: {targeted} | 항생제: {abx}"
                st.code(summary, language="")
        with c3:
            st.caption("※ 상세 해석은 본문 '해석하기' 이후 결과 영역에서 확인")
