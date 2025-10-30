# ae_fallback_shim.py — early-safe AE symbols (loaded near top of app.py)
# Non-invasive: only defines symbols if missing; prefers existing modules.

def _install_ae_fallbacks():
    try:
        import builtins
        # If already available in globals/builtins, do nothing
        for name in ("resolve_key", "get_ae", "get_checks", "render_arac_wrapper"):
            if hasattr(builtins, name):
                return
        try:
            # Prefer real module if importable
            from ae_resolve import resolve_key, get_ae, get_checks, render_arac_wrapper  # type: ignore
            builtins.resolve_key = resolve_key
            builtins.get_ae = get_ae
            builtins.get_checks = get_checks
            builtins.render_arac_wrapper = render_arac_wrapper
            return
        except Exception:
            pass

        # Fallback lightweight implementations
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

        builtins.resolve_key = resolve_key
        builtins.get_ae = get_ae
        builtins.get_checks = get_checks
        builtins.render_arac_wrapper = render_arac_wrapper
    except Exception:
        # Never crash the app because of the shim
        pass

_install_ae_fallbacks()
