
# bridge: import from util_core if available; else simple fallbacks
try:
    from ..util_core import num_input_generic, entered, _parse_numeric
except Exception:
    import streamlit as st
    def _parse_numeric(raw, decimals=1):
        if raw in ("", None): return None
        try:
            return round(float(raw), decimals)
        except Exception:
            return None
    def num_input_generic(label, key=None, decimals=1, as_int=False, placeholder=""):
        if as_int:
            v = st.number_input(label, key=key, step=1, format="%d")
            return int(v) if v is not None else None
        else:
            v = st.number_input(label, key=key, step=0.1, format="%.{}f".format(decimals))
            return float(v) if v is not None else None
    def entered(x):
        try: return x not in (None, "") and (float(x)==float(x))
        except Exception: return False
