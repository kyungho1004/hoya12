"""
Diagnostics Panel — shows render flags & duplicate-key guard status.
Pure UI; does not mutate behavior (except optional clear buttons).
(Alt path: features_dev.diag_panel)
"""
from __future__ import annotations

def _flag_line(ss, k, label=None):
    v = ss.get(k)
    icon = "✅" if v else "▫️"
    return f"{icon} {label or k}: {v}"

def render_diag_panel(st):
    try:
        ss = st.session_state
        with st.expander("🛠 진단 패널 (β)", expanded=False):
            st.markdown("#### 렌더 플래그")
            for k in ["_lean_mode","_modular_render","_ae_main_rendered","_stests_rendered",
                      "_skip_legacy_ae","_skip_legacy_special","_skip_legacy_exports","_skip_legacy_peds"]:
                st.markdown("- " + _flag_line(ss, k))
            st.markdown("---")
            st.markdown("#### 키 네임스페이스")
            ns = ss.get("_stests_ns"); call_ns = ss.get("_stests_call_ns")
            st.code(f"_stests_ns={ns} | _stests_call_ns={call_ns}")
            counts = ss.get("_stests_key_counts") or {}
            st.caption(f"per-name counters: {len(counts)} entries")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("카운터 초기화", key="diag_reset_counts"):
                    ss["_stests_key_counts"] = {}
                    st.success("초기화됨")
            with col2:
                if st.button("플래그 초기화", key="diag_reset_flags"):
                    for k in ["_modular_render","_ae_main_rendered","_stests_rendered"]:
                        ss.pop(k, None)
                    st.success("초기화됨")
    except Exception:
        pass
