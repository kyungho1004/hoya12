# app.py — patched final (v6 sandbox for special_tests + report bridge tail)
import streamlit as st

# ========== [PATCH-HEAD] special tests robust wrapper (v6) + import shim + report bridge ==========
try:
    from app_special_import_shim import ensure_special_tests_ui
    _special_tests_ui_orig = ensure_special_tests_ui()
except Exception:
    _special_tests_ui_orig = None

def _sp_slug(x: str) -> str:
    import re
    return re.sub(r'[^a-zA-Z0-9_.-]+', '_', str(x)).strip('_') or "x"

def _sp_ns():
    uid = st.session_state.get("_uid") or st.session_state.get("key") or "guest"
    return f"{_sp_slug(uid)}.special.v6"

def _sp_mint(base: str) -> str:
    used = st.session_state.setdefault("_sp_used_keys_v6", set())
    if base not in used:
        used.add(base); return base
    i = 2
    while True:
        k = f"{base}.dup{i}"
        if k not in used:
            used.add(k); return k
        i += 1

def _sp_key(kind: str, label: str = "x", sec: str = "root") -> str:
    return _sp_mint(f"{_sp_ns()}.{_sp_slug(sec)}.{kind}.{_sp_slug(label)}")

def _run_special_ui_sandbox(ui_func):
    # Capture originals once
    _orig = {
        "toggle": st.toggle,
        "selectbox": st.selectbox,
        "checkbox": getattr(st, "checkbox", None),
        "text_input": st.text_input,
        "text_area": getattr(st, "text_area", None),
        "number_input": getattr(st, "number_input", None),
        "slider": getattr(st, "slider", None),
        "date_input": getattr(st, "date_input", None),
        "time_input": getattr(st, "time_input", None),
    }
    sec = lambda: st.session_state.get("_special_current_section", "root")

    # Safe wrappers (always call originals; mint key if missing)
    def _wrap_toggle(label, key=None, **kw):
        if key is None: key = _sp_key("tog", label, sec())
        return _orig["toggle"](label, key=key, **kw)
    def _wrap_selectbox(label, options, index=0, key=None, **kw):
        if key is None: key = _sp_key("sel", label, sec())
        return _orig["selectbox"](label, options, index=index, key=key, **kw)
    def _wrap_checkbox(label, value=False, key=None, **kw):
        if key is None: key = _sp_key("chk", label, sec())
        return _orig["checkbox"](label, value=value, key=key, **kw)
    def _wrap_text_input(label, value="", max_chars=None, key=None, **kw):
        if key is None: key = _sp_key("txt", label, sec())
        return _orig["text_input"](label, value=value, max_chars=max_chars, key=key, **kw)
    def _wrap_text_area(label, value="", height=None, max_chars=None, key=None, **kw):
        if key is None: key = _sp_key("tar", label, sec())
        return _orig["text_area"](label, value=value, height=height, max_chars=max_chars, key=key, **kw)
    def _wrap_number_input(label, value=0, key=None, **kw):
        if key is None: key = _sp_key("num", label, sec())
        return _orig["number_input"](label, value=value, key=key, **kw)
    def _wrap_slider(label, *args, key=None, **kw):
        if key is None: key = _sp_key("sld", label, sec())
        return _orig["slider"](label, *args, key=key, **kw)
    def _wrap_date_input(label, *args, key=None, **kw):
        if key is None: key = _sp_key("dat", label, sec())
        return _orig["date_input"](label, *args, key=key, **kw)
    def _wrap_time_input(label, *args, key=None, **kw):
        if key is None: key = _sp_key("tim", label, sec())
        return _orig["time_input"](label, *args, key=key, **kw)

    # Apply temporary wrappers
    st.toggle = _wrap_toggle
    st.selectbox = _wrap_selectbox
    if _orig["checkbox"]: st.checkbox = _wrap_checkbox
    st.text_input = _wrap_text_input
    if _orig["text_area"]: st.text_area = _wrap_text_area
    if _orig["number_input"]: st.number_input = _wrap_number_input
    if _orig["slider"]: st.slider = _wrap_slider
    if _orig["date_input"]: st.date_input = _wrap_date_input
    if _orig["time_input"]: st.time_input = _wrap_time_input

    try:
        res = ui_func()
    except Exception as e:
        st.error(f"특수검사 UI 실행 중 오류: {e}")
        res = []
    finally:
        # Restore originals
        for k, v in _orig.items():
            if v is not None:
                setattr(st, k, v)

    # Normalize lines and store
    lines = []
    if isinstance(res, list):
        lines = [str(x) for x in res if x is not None]
    elif isinstance(res, str) and res.strip():
        lines = [res.strip()]
    st.session_state["special_interpretations"] = lines
    return lines

# Replace global callable so existing code uses the sandbox
def special_tests_ui(*args, **kwargs):
    if _special_tests_ui_orig is None:
        try:
            st.warning("special_tests.py를 찾지 못해, 특수검사 UI는 더미로 표시됩니다.")
        except Exception:
            pass
    ui = _special_tests_ui_orig or (lambda: [])
    return _run_special_ui_sandbox(ui)

# Optional: if app calls special_tests_ui elsewhere, provide alias
getattr(st.session_state, "_noop", None)

# Report bridge (imported here; used in tail)
try:
    from app_report_special_patch import bridge_special_to_report, render_special_report_section
except Exception:
    bridge_special_to_report = None
    render_special_report_section = None

# ==========================
# 기존 앱 본문은 여기 아래에 이어짐 (우리는 건드리지 않음)
# ==========================

# (데모용 최소 본문; 실제 배포에서는 기존 본문이 여기에 위치)
st.title("BloodMap — Patched Sandbox App")
st.write("이 빌드는 특수검사 UI를 샌드박스로 감싸 중복키/재귀 충돌을 방지합니다.")
# 특수검사 호출 버튼 (데모)
if st.button("특수검사 실행(데모)"):
    try:
        lines = special_tests_ui()
        st.success(f"특수검사 결과: {lines}")
    except Exception as e:
        st.error(f"실행 오류: {e}")

# ========== [PATCH-TAIL] normalize & render special tests report (safe) ==========
try:
    if bridge_special_to_report:
        try:
            bridge_special_to_report()
        except Exception:
            pass
    if render_special_report_section and st.session_state.get("special_interpretations"):
        try:
            render_special_report_section(title="## 특수검사 해석(각주 포함)", debug=True)
        except Exception:
            pass
except Exception:
    pass
