
# --- Optional addons (fail-safe import) ---
try:
    from onco_mini_toggle import render_onco_mini  # type: ignore
except Exception:
    def render_onco_mini(ctx=None):
        return None

try:
    from mini_schedule import mini_schedule_ui  # type: ignore
except Exception:
    def mini_schedule_ui(storage_key="mini_sched"):
        import streamlit as st
        st.info("미니 스케줄 모듈이 로드되지 않았습니다.")

try:
    from report_qr import render_qr, qr_url  # type: ignore
except Exception:
    def render_qr(st, data: str, size: int = 220, caption: str|None=None):
        import streamlit as st
        st.caption("QR 모듈이 로드되지 않았습니다.")
    def qr_url(data: str, size: int = 220, ec: str = "M") -> str:
        return ""

# 암환자 보조 패널(해열제/설사) — 독립 try/except
try:
    from cancer_support_panel import render_onco_support  # type: ignore
except Exception:
    def render_onco_support(labs=None, storage_key="onco_support"):
        return {}
