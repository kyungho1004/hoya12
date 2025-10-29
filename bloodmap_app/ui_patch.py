# ui_patch.py — BloodMap runtime patch (NO-SEED key prefixer + AE fallbacks)
# Import this module as the FIRST import in app.py:
#     import ui_patch  # keep this as the very first import

def _bm_apply_widget_patches_noseed():
    try:
        import streamlit as st, uuid
        ss = st.session_state
        ss.setdefault("_sp_ns", "sp" + uuid.uuid4().hex[:8])

        # capture whatever current toggle/checkbox are, then wrap WITHOUT writing session
        _orig_toggle = st.toggle
        def _patched_toggle(label, *args, **kwargs):
            k = kwargs.get("key", None)
            if isinstance(k, str) and not k.startswith("__sp__/"):
                kwargs["key"] = f"__sp__/{ss['_sp_ns']}/{k}"
            return _orig_toggle(label, *args, **kwargs)
        st.toggle = _patched_toggle

        _orig_checkbox = st.checkbox
        def _patched_checkbox(label, *args, **kwargs):
            k = kwargs.get("key", None)
            if isinstance(k, str) and not k.startswith("__sp__/"):
                kwargs["key"] = f"__sp__/{ss['_sp_ns']}/{k}"
            return _orig_checkbox(label, *args, **kwargs)
        st.checkbox = _patched_checkbox
    except Exception:
        pass

# Apply key prefixer immediately on import
_bm_apply_widget_patches_noseed()

# --- AE resolver safe fallbacks (used only if ae_resolve is missing) ---
try:
    from ae_resolve import resolve_key, get_ae, get_checks, render_arac_wrapper  # type: ignore
except Exception:
    def resolve_key(x):
        return str(x) if x is not None else ""
    def get_ae(key):
        return ""
    def get_checks(key):
        return []
    def render_arac_wrapper(title: str, default: str = "Cytarabine"):
        import streamlit as st
        options = ["Cytarabine", "Ara-C IV", "Ara-C SC", "Ara-C HDAC"]
        idx = options.index(default) if default in options else 0
        return st.radio(title, options, index=idx, key="__ae__/arac_form")

# Expose names if app.py expects them in globals()
try:
    _resolve  # type: ignore
except Exception:
    _resolve = resolve_key
