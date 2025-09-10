BloodMap Modularization — Quick Wiring
=====================================

Files:
- drug_db.py      : DRUG_DB store + ensure_onco_drug_db()
- onco_map.py     : build_onco_map() + auto_recs_by_dx()
- ui_results.py   : results_only_after_analyze(), render_adverse_effects(), peds_diet_guide()

How to connect in app.py
------------------------
from drug_db import DRUG_DB, ensure_onco_drug_db
from onco_map import build_onco_map, auto_recs_by_dx
from ui_results import results_only_after_analyze, render_adverse_effects, peds_diet_guide

# 1) init (once)
ensure_onco_drug_db(DRUG_DB)
ONCO_MAP = build_onco_map()

# 2) after user picks group/dx:
rec = auto_recs_by_dx(group, dx, DRUG_DB, ONCO_MAP)

# 3) when user presses "해석하기":
if st.button("🔎 해석하기", key="analyze_main"):
    st.session_state["analyzed"] = True
    st.session_state["analysis_ctx"] = {
        "group": group, "dx": dx, "labs": labs, "disease": disease, "vals": labs or {},
    }

# 4) gate to show only results below
if results_only_after_analyze(st):
    ctx = st.session_state.get("analysis_ctx", {})
    # 4-1) 피수치 해석(기존 함수 연결)
    # render_lab_interpretation(ctx["labs"])  # <- 기존 함수 그대로 호출
    # 4-2) 식이가이드
    foods, avoid, tips = peds_diet_guide(ctx.get("disease"), ctx.get("vals", {}))
    st.markdown("**권장 예시**");  [st.markdown(f"- {f}") for f in foods]
    st.markdown("**피해야 할 예시**"); [st.markdown(f"- {a}") for a in avoid]
    if tips:
        st.markdown("**케어 팁**"); [st.markdown(f"- {t}") for t in tips]

    # 4-3) 약물 부작용 (암종/진단에 따른 추천 기반)
    rec = auto_recs_by_dx(ctx.get("group"), ctx.get("dx"), DRUG_DB, ONCO_MAP)
    render_adverse_effects(st, rec["chemo"] + rec["targeted"], DRUG_DB)
    st.stop()
