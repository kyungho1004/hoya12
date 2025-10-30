# ui_patch_safest.py — Extended NO-SEED key prefixer with per-call ns guard
# Use as FIRST import in app.py:
#   import ui_patch_safest  # must be first

def _bm_get_ns_safe():
    import streamlit as st, uuid
    ss = st.session_state
    ns = ss.get("_sp_ns", None)
    if not isinstance(ns, str) or not ns:
        try:
            ns = "sp" + uuid.uuid4().hex[:8]
            ss["_sp_ns"] = ns
        except Exception:
            ns = "sp" + uuid.uuid4().hex[:8]
    return ns

def _bm_prefix_kwargs(kwargs):
    k = kwargs.get("key", None)
    if isinstance(k, str) and not k.startswith("__sp__/"):
        ns = _bm_get_ns_safe()
        kwargs["key"] = f"__sp__/{ns}/{k}"
    return kwargs

def _bm_apply_widget_patches_safest():
    try:
        import streamlit as st
        if getattr(st, "_bm_patch_safest", False):
            return

        def _wrap(name):
            orig = getattr(st, name)
            def _wrapped(*args, **kwargs):
                kwargs = dict(kwargs)
                kwargs = _bm_prefix_kwargs(kwargs)
                return orig(*args, **kwargs)
            return orig, _wrapped

        targets = [
            "toggle", "checkbox", "radio", "selectbox", "multiselect",
            "slider", "number_input", "text_input", "text_area",
            "date_input", "time_input", "file_uploader",
        ]
        for t in targets:
            try:
                orig, wrapped = _wrap(t)
                setattr(st, t, wrapped)
            except Exception:
                pass

        st._bm_patch_safest = True
    except Exception:
        pass

_bm_apply_widget_patches_safest()

# Optional AE fallbacks (only if ae_resolve is missing)
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
        opts = ["Cytarabine", "Ara-C IV", "Ara-C SC", "Ara-C HDAC"]
        idx = opts.index(default) if default in opts else 0
        return st.radio(title, opts, index=idx, key="__ae__/arac_form")
try:
    _resolve  # type: ignore
except Exception:
    _resolve = resolve_key
