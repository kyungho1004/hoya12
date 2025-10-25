"""
Diagnosis status panel & sticky toggle for DX route.
- Read-only snapshot of current group/disease in session_state
- Sticky toggle to keep DX active (sets _dx_active True/False)
"""
from __future__ import annotations

def render_diagnosis_panel(st):
    try:
        ss = st.session_state
        group = ss.get("dx_group") or ss.get("group") or "-"
        disease = ss.get("dx_disease") or ss.get("disease") or "-"
        with st.expander("진단 상태 (DX)", expanded=False):
            st.markdown(f"- **그룹**: {group}")
            st.markdown(f"- **진단명**: {disease}")
            keep = st.toggle("진단 탭 고정(dX sticky)", value=bool(ss.get("_dx_active")), key="_dx_toggle")
            if keep != bool(ss.get("_dx_active")):
                ss["_dx_active"] = bool(keep)
            if ss.get("_route") != "dx" and ss.get("_dx_active"):
                st.caption("※ dX 고정 중: 홈으로 튐 방지")
    except Exception:
        pass
