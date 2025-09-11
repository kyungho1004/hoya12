# -*- coding: utf-8 -*-
import streamlit as st

from drug_db import DRUG_DB, ensure_onco_drug_db
from onco_map import build_onco_map, auto_recs_by_dx
from ui_results import results_only_after_analyze, render_adverse_effects, peds_diet_guide

ensure_onco_drug_db(DRUG_DB)
ONCO_MAP = build_onco_map()

st.set_page_config(page_title="BloodMap (Modular)", layout="wide")
st.title("BloodMap — Modular Scaffold")

# --- UI ---
mode = st.radio("모드 선택", ["소아", "암"], horizontal=True)
group = None; dx = None; disease = None; labs = {}

if mode == "소아":
    # 기본값을 공백이 아닌 '로타'로 설정 → 빈 셀처럼 보이지 않게
    disease = st.selectbox(
        "소아 질환",
        ["로타", "독감", "RSV", "아데노", "마이코", "수족구", "편도염", "코로나", "중이염"],
        index=0
    )
else:
    group = st.selectbox("암 카테고리", ["혈액암", "림프종", "고형암", "육종", "희귀암"], index=0)
    if group == "혈액암":
        dx = st.selectbox("진단", ["APL", "AML", "ALL", "CML"], index=0)
    elif group == "림프종":
        dx = st.selectbox("진단", ["B거대세포(DLBCL)"], index=0)
    elif group == "고형암":
        dx = st.selectbox("진단", ["폐선암"], index=0)
    else:
        dx = st.text_input("진단(직접 입력)")

# --- Trigger ---
st.button("🔎 해석하기", key="analyze_main", on_click=lambda: st.session_state.update({
    "analyzed": True,
    "analysis_ctx": {"mode": mode, "group": group, "dx": dx, "disease": disease, "labs": labs, "vals": labs or {}},
}))

# --- Results-only ---
if results_only_after_analyze(st):
    ctx = st.session_state.get("analysis_ctx", {})

    st.subheader("🧪 피수치 해석")
    st.info("기존 해석 함수 연결 자리입니다. (데모)")

    if ctx.get("mode") == "소아":
        st.subheader("🥗 식이가이드")
        foods, avoid, tips = peds_diet_guide(ctx.get("disease"), ctx.get("vals", {}))
        st.markdown("**권장 예시**")
        for f in foods: st.markdown(f"- {f}")
        st.markdown("**피해야 할 예시**")
        for a in avoid: st.markdown(f"- {a}")
        if tips:
            st.markdown("**케어 팁**")
            for t in tips: st.markdown(f"- {t}")

    if ctx.get("mode") == "암":
        st.subheader("💊 부작용(요약)")
        rec = auto_recs_by_dx(ctx.get("group"), ctx.get("dx"), DRUG_DB, ONCO_MAP)
        render_adverse_effects(st, rec["chemo"] + rec["targeted"], DRUG_DB)

    st.stop()
