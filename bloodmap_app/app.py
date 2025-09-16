try:
    from onco_table import ui_onco_table_card
except Exception:
    pass

# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import date

from core_utils import nickname_pin, clean_num, schedule_block
from drug_db import DRUG_DB, ensure_onco_drug_db, display_label
from onco_map import build_onco_map, auto_recs_by_dx, dx_display
from ui_results import results_only_after_analyze, render_adverse_effects, collect_top_ae_alerts
from lab_diet import lab_diet_guides
from peds_profiles import get_symptom_options
from peds_dose import acetaminophen_ml, ibuprofen_ml
from pdf_export import export_md_to_pdf

# === Mode helpers (robust cancer detection) ===
import re as _re
def _tokens_from_fields(vals):
    txt = " ".join(str(v or "") for v in vals)
    return [t for t in _re.split(r"[\\s,|/\\\\]+", txt) if t]

def _is_cancer_mode():
    import streamlit as st
    _ctx = st.session_state.get("analysis_ctx", {})
    vals = []
    for k in ("mode","group","profile","patient_type","flow","view"):
        vals.append(st.session_state.get(k))
        vals.append(_ctx.get(k))
    toks = _tokens_from_fields(vals)
    toks_lower = [t.lower() for t in toks]
    toks_set = set(toks)
    KOR = {"암","암환자","암-환자","암모드","소아암","성인암","종양","항암","백혈병","림프종","육종","종양내과"}
    if KOR & toks_set: return True
    ENG = {"onco","oncology","cancer","hem-onc","heme-onc","hem_onc","hemato-oncology"}
    if any(t in ENG for t in toks_lower): return True
    return False


# === Cancer-first guard (hides Bundle everywhere for cancer) ===
try:
    import streamlit as st
    _ctx = st.session_state.get("analysis_ctx", {})
    mode_fields = " ".join(str(st.session_state.get(k,"")) for k in ("mode","group","profile","patient_type"))
    ctx_fields  = " ".join(str(_ctx.get(k,"")) for k in ("mode","group","profile"))
    combined = (mode_fields + " " + ctx_fields)
    cl = combined.lower()
    is_cancer = _is_cancer_mode()
    if is_cancer:
        st.markdown("## 📊 암환자 피수치 그래프")
        try:
            from onco_charts import ui_onco_trends_card
            ui_onco_trends_card("onco")
        except Exception as e:
            st.info(f"암 그래프 로딩 중: {e}")
        st.session_state["__suppress_bundle"] = True
    else:
        st.session_state["__suppress_bundle"] = False
except Exception as _guard_err:
    pass

# === Injected: Only hide for cancer; show for everyone else ===
try:
    import streamlit as st
    is_cancer = globals().get("_is_cancer_mode", lambda: False)()
    if not is_cancer:
        st.markdown("## 🧩 Bundle V1 — 투약·안전 / 기록·저장 / 보고서·문구")
        _age_m = int(st.session_state.get("age_m") or st.session_state.get("age_months") or 12)
        _wt = float(st.session_state.get("weight") or st.session_state.get("wt") or 40.0)
        _temp = float(st.session_state.get("temp") or 36.8)
        _key = "bundle_simple"
        st.markdown("### 🕒 해열제 24시간 시간표")
        sched_today = ui_antipyretic_card(_age_m, _wt, _temp, key=_key)
        st.markdown("### 기록·저장")
        st.markdown("#### 📈 증상 일지(미니 차트)")
        diary_df = ui_symptom_diary_card(_key)
        st.markdown("### 보고서·문구")
        st.caption("보고서 저장 시, 선택된 섹션은 자동 포함됩니다(시간표/일지/QR).")
        st.session_state.setdefault("bundle_cache", {})
        st.session_state["bundle_cache"]["sched_today"] = sched_today
        st.session_state["bundle_cache"]["diary_df"] = diary_df
except Exception as _simp_err:
    import streamlit as st
    st.info(f"단순 게이트 적용 중: {_simp_err}")
