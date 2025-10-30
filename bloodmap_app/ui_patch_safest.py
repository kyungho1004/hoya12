# ui_patch_safest_v2.py — NO-SEED key prefixer + duplicate-key deduper (per-call ns guard)
# Use as FIRST import in app.py:
#   import ui_patch_safest_v2  # must be first

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

def _bm_prefix(key):
    if isinstance(key, str) and not key.startswith("__sp__/"):
        ns = _bm_get_ns_safe()
        return f"__sp__/{ns}/{key}"
    return key

def _bm_dedupe(key):
    # ensure uniqueness within a single run
    import streamlit as st
    try:
        used = st.session_state.setdefault("__bm_used_keys__", set())
    except Exception:
        used = set()
    k = key
    if k in used:
        # append minimal numeric suffix until unique
        i = 2
        while f"{k}__dup{i}" in used:
            i += 1
        k = f"{k}__dup{i}"
    used.add(k)
    try:
        st.session_state["__bm_used_keys__"] = used
    except Exception:
        pass
    return k

def _bm_fix_key(kwargs):
    k = kwargs.get("key", None)
    if k is None:
        return kwargs
    k = _bm_prefix(k)
    k = _bm_dedupe(k)
    kwargs["key"] = k
    return kwargs

def _bm_apply_widget_patches_safest_v2():
    try:
        import streamlit as st
        # allow reapply to sit outermost
        def _wrap(name):
            orig = getattr(st, name)
            def _wrapped(*args, **kwargs):
                kwargs = dict(kwargs)
                kwargs = _bm_fix_key(kwargs)
                return orig(*args, **kwargs)
            return orig, _wrapped

        for t in [
            "toggle", "checkbox", "radio", "selectbox", "multiselect",
            "slider", "number_input", "text_input", "text_area",
            "date_input", "time_input", "file_uploader",
        ]:
            try:
                orig, wrapped = _wrap(t)
                setattr(st, t, wrapped)
            except Exception:
                pass
    except Exception:
        pass

_bm_apply_widget_patches_safest_v2()

# Optional AE fallbacks (only if ae_resolve missing)
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
