# ==== PATCH • Special Tests: Auto-keys + Single-run Guard (non-destructive) ====
import re
try:
    import streamlit as st
except Exception:
    st = None

def _sp_ns() -> str:
    if st is None:
        return "sp3v1|no-st"
    who = str(st.session_state.get("key", "guest#PIN"))
    uid = str(st.session_state.get("_uid") or who or "anon")
    route = str(st.session_state.get("_route", "dx"))
    tab = str(st.session_state.get("_tab_active", "특수검사"))
    return f"sp3v1|{uid}|{route}|{tab}"

def _sp_key_counts():
    return st.session_state.setdefault("_sp_key_counts", {}) if st else {}

def _unique_key(base: str) -> str:
    if not st:
        return base
    counters = _sp_key_counts()
    n = int(counters.get(base, 0))
    counters[base] = n + 1
    st.session_state["_sp_key_counts"] = counters
    return base if n == 0 else f"{base}#{n}"

def _k(*parts: str) -> str:
    return "|".join([_sp_ns(), *map(str, parts)])

def _label_to_id(label: str) -> str:
    return re.sub(r"[^0-9a-zA-Z]+", "_", str(label)).strip("_").lower()

# ---- Widget key builders (override-friendly, last definition wins) ----
def _tog_key(sec_id: str) -> str:
    return _unique_key(_k("tog", sec_id))
def _btn_key(elem_id: str) -> str:
    return _unique_key(_k("btn", elem_id))
def _fav_key(elem_id: str) -> str:
    return _unique_key(_k("fav", elem_id))
def _sel_key(elem_id: str) -> str:
    return _unique_key(_k("sel", elem_id))
def _num_key(elem_id: str) -> str:
    return _unique_key(_k("num", elem_id))
def _txt_key(elem_id: str) -> str:
    return _unique_key(_k("txt", elem_id))
def _sl_key(elem_id: str) -> str:
    return _unique_key(_k("sld", elem_id))

# ---- Auto-key wrappers (callsite 수정 불필요) ----
if st is not None:
    if not hasattr(st, "_orig_selectbox"):
        st._orig_selectbox = st.selectbox
    def _selectbox_auto_key(label, options, *args, **kwargs):
        if "key" not in kwargs or kwargs.get("key") in (None, ""):
            kwargs["key"] = _unique_key(_k("sel", _label_to_id(label)))
        return st._orig_selectbox(label, options, *args, **kwargs)
    st.selectbox = _selectbox_auto_key

    if not hasattr(st, "_orig_number_input"):
        st._orig_number_input = st.number_input
    def _number_input_auto_key(label, *args, **kwargs):
        if "key" not in kwargs or kwargs.get("key") in (None, ""):
            kwargs["key"] = _unique_key(_k("num", _label_to_id(label)))
        return st._orig_number_input(label, *args, **kwargs)
    st.number_input = _number_input_auto_key

    if not hasattr(st, "_orig_text_input"):
        st._orig_text_input = st.text_input
    def _text_input_auto_key(label, *args, **kwargs):
        if "key" not in kwargs or kwargs.get("key") in (None, ""):
            kwargs["key"] = _unique_key(_k("txt", _label_to_id(label)))
        return st._orig_text_input(label, *args, **kwargs)
    st.text_input = _text_input_auto_key

    if not hasattr(st, "_orig_slider"):
        st._orig_slider = st.slider
    def _slider_auto_key(label, *args, **kwargs):
        if "key" not in kwargs or kwargs.get("key") in (None, ""):
            kwargs["key"] = _unique_key(_k("sld", _label_to_id(label)))
        return st._orig_slider(label, *args, **kwargs)
    st.slider = _slider_auto_key

# ---- Single-run render guard (module-local; app.py 수정 불필요) ----
try:
    _orig_special_tests_ui = special_tests_ui  # keep original
    def special_tests_ui(*args, **kwargs):
        if st is not None:
            st.session_state.setdefault("_route", "dx")
            st.session_state["_tab_active"] = "특수검사"
            if st.session_state.get("_sp3v1_special_rendered"):
                return st.session_state.get("special_tests_lines", [])
        lines = _orig_special_tests_ui(*args, **kwargs)
        if st is not None:
            if isinstance(lines, list):
                st.session_state["special_tests_lines"] = lines
            st.session_state["_sp3v1_special_rendered"] = True
        return lines
except NameError:
    # original not yet defined; safe to skip
    pass
# ==== /PATCH END ====