# app_special_import_shim.py — robust loader for special_tests (patch-only)
import sys, importlib.util, pathlib

CANDIDATES = [
    pathlib.Path(__file__).parent / "special_tests.py",
    pathlib.Path("/mount/src/hoya12/bloodmap_app/special_tests.py"),
    pathlib.Path("/mnt/data/special_tests.py"),
]

def _load_from_path(p: pathlib.Path):
    if not p.exists():
        return None
    spec = importlib.util.spec_from_file_location("special_tests", str(p))
    if not spec or not spec.loader:
        return None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["special_tests"] = mod
    spec.loader.exec_module(mod)
    return mod

def ensure_special_tests_ui():
    # 1) normal import
    try:
        import special_tests as st_mod  # type: ignore
        if hasattr(st_mod, "special_tests_ui"):
            return st_mod.special_tests_ui
    except Exception:
        pass
    # 2) search candidates
    for p in CANDIDATES:
        try:
            mod = _load_from_path(p)
            if mod and hasattr(mod, "special_tests_ui"):
                return getattr(mod, "special_tests_ui")
        except Exception:
            continue
    # 3) fallback dummy
    def _dummy_ui():
        try:
            import streamlit as st
            st.warning("special_tests.py를 찾지 못해, 특수검사 UI는 더미로 표시됩니다.")
        except Exception:
            pass
        return []
    return _dummy_ui
