# === PATCH-LOCK: classic hard lock + safety fallbacks ===
from datetime import timedelta, timezone as _tz
import os, sys, types

# KST 보정
try:
    KST
except NameError:
    KST = _tz(timedelta(hours=9))

# 클래식 고정(lean/router UI 무력화)
os.environ["BLOODMAP_CLASSIC"] = "1"
globals()["_CLASSIC_LOCK"] = True

def _noop(*a, **k): return None
for _mod in ("features.app_shell", "features.app_deprecator", "features.app_router"):
    try:
        m = __import__(_mod, fromlist=["*"])
        for flag in ("SHOW_LEAN_TOGGLE","DEFAULT_LEAN","ENABLE_LEAN_UI","ROUTER_ENABLED"):
            try: setattr(m, flag, False)
            except Exception: pass
        for fn in ("render_sidebar","render_lean_toggle","render_jumpbar","mount_router"):
            try: setattr(m, fn, _noop)
            except Exception: pass
    except Exception:
        mod = types.ModuleType(_mod)
        for fn in ("render_sidebar","render_lean_toggle","render_jumpbar","mount_router"):
            setattr(mod, fn, _noop)
        sys.modules[_mod] = mod

# AE 렌더 우선순위 + 폴백
try:
    from ui_results import render_adverse_effect as _ae
except Exception:
    try:
        from ae_bridge import render_adverse_effect as _ae
    except Exception:
        try:
            from ae_resolve import render_adverse_effect as _ae
        except Exception:
            def _ae(drug_key: str, rec: dict | None = None):
                import streamlit as st
                st.markdown(f"- **{drug_key}**: 부작용 정보 준비 중")

# 소아 페이지 모듈 폴백
try:
    import pages_peds as _peds
    _HAS_PEDS = True
except Exception:
    _HAS_PEDS = False

# 안전 DB 핸들러
def _get_db():
    db = globals().get("DRUG_DB")
    return db if isinstance(db, dict) else {}

# 라벨/AE 맵 폴리필(없으면 만들어줌)
if "_label_kor" not in globals():
    def _label_kor(k, label_map=None): return str(k)
if "ae_map" not in globals():
    ae_map = {}
# === /PATCH-LOCK ===
