# ui_patch_ext.py — BloodMap runtime patch (Extended NO-SEED key prefixer + AE fallbacks)
# 사용법: app.py 최상단 첫 줄에 아래 한 줄을 추가하세요.
#   import ui_patch_ext  # MUST be the first import
#
# 이 모듈은 위젯 key 충돌/KeyError를 방지하기 위해 문자열 key에만
# __sp__/{세션UID}/{원래키} 프리픽스를 붙입니다. (세션에 값을 쓰지 않음)

def _bm_apply_widget_patches_noseed_ext():
    try:
        import streamlit as st, uuid

        # 세션 네임스페이스를 읽기 전용으로만 사용 (setdefault는 안전)
        ss = st.session_state
        ss.setdefault("_sp_ns", "sp" + uuid.uuid4().hex[:8])

        def _prefix(kwargs):
            k = kwargs.get("key", None)
            if isinstance(k, str) and not k.startswith("__sp__/"):
                kwargs["key"] = f"__sp__/{ss['_sp_ns']}/{k}"
            return kwargs

        # 이미 패치된 경우 중복 적용 방지
        if getattr(st, "_bm_patch_noseed_ext", False):
            return

        # ---- 공통 래퍼 팩토리 (원본 유지) ----
        def _wrap(fn_name):
            orig = getattr(st, fn_name)
            def _wrapped(*args, **kwargs):
                kwargs = dict(kwargs)  # copy
                kwargs = _prefix(kwargs)
                return orig(*args, **kwargs)
            return orig, _wrapped

        # 최소 충돌군
        for name in [
            "toggle", "checkbox", "radio", "selectbox", "multiselect",
            "slider", "number_input", "text_input", "text_area",
            "date_input", "time_input", "file_uploader",
        ]:
            try:
                orig, wrapped = _wrap(name)
                setattr(st, name, wrapped)
            except Exception:
                pass

        st._bm_patch_noseed_ext = True

    except Exception:
        # 어떤 경우에도 앱이 죽지 않도록
        pass

# 즉시 적용
_bm_apply_widget_patches_noseed_ext()

# --- AE resolver safe fallbacks (ae_resolve가 없을 때만 동작) ---
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

# 글로벌 별칭 보장(일부 코드 호환)
try:
    _resolve  # type: ignore
except Exception:
    _resolve = resolve_key
