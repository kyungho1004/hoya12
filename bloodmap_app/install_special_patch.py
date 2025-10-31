
#!/usr/bin/env python3
# install_special_patch.py — one-shot installer for BloodMap special_tests hard-fix
# Usage: python install_special_patch.py [/mount/src/hoya12/bloodmap_app]
import sys, os, shutil, re, pathlib, datetime

DEFAULT_APP_DIR = "/mount/src/hoya12/bloodmap_app"
APP_DIR = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_APP_DIR

STAMP = "PATCH_SAFE_ST_20251031_072502"
BAD_SUFFIX = ".BAD_20251031_072502"

SRC_DIR = "/mnt/data"

SAFE_FILES = [
    ("app.py", "app.py"),
    ("special_tests.py", "special_tests.py"),
    ("app_report_special_patch.py", "app_report_special_patch.py"),
    ("app_special_import_shim.py", "app_special_import_shim.py"),
]

def backup(p):
    if os.path.exists(p):
        shutil.copy2(p, p + ".bak")

def ensure_dir(d):
    if not os.path.isdir(d):
        raise SystemExit(f"[X] App directory not found: {d}")

def quarantine_conflicts(root):
    # Move ANY special_tests.py outside target to *.BAD
    moved = []
    for p in pathlib.Path(root).rglob("special_tests.py"):
        dst = str(p) + BAD_SUFFIX
        shutil.move(str(p), dst)
        moved.append((str(p), dst))
    # Also look for monkeypatch signatures across tree
    suspects = []
    for p in pathlib.Path(root).rglob("*.py"):
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if re.search(r"st\.toggle\s*=", text) or "_wrap_toggle" in text or "_patched_toggle" in text:
            suspects.append(str(p))
    return moved, suspects

def deploy_safe_files(app_dir):
    for src_name, dst_name in SAFE_FILES:
        src = os.path.join(SRC_DIR, src_name)
        dst = os.path.join(app_dir, dst_name)
        if not os.path.exists(src):
            print(f"[!] Missing source: {src} (skipping)")
            continue
        # backup existing
        backup(dst)
        # place file
        if src_name == "app.py":
            shutil.move(src, dst)
        else:
            shutil.copy2(src, dst)
        print(f"[✓] Deployed {dst_name}")
    # Inject verification caption at top of app.py if not present
    app_py = os.path.join(app_dir, "app.py")
    try:
        txt = open(app_py, "r", encoding="utf-8").read()
    except Exception as e:
        print("[!] Could not open app.py:", e); return
    if "special_tests loaded from:" not in txt:
        inject = '\nimport importlib\ntry:\n    _stmod = importlib.import_module("special_tests")\n    st.caption(f"special_tests loaded from: {getattr(_stmod, "__file__", None)}")\nexcept Exception as _e:\n    st.caption(f"special_tests import failed: {_e}")\n\n'
        # place after first 'import streamlit as st'
        idx = txt.find("import streamlit as st")
        if idx != -1:
            idx_end = idx + len("import streamlit as st")
            txt = txt[:idx_end] + inject + txt[idx_end:]
            open(app_py, "w", encoding="utf-8").write(txt)
            print("[✓] Injected verification caption into app.py")
        else:
            print("[!] Could not find 'import streamlit as st' to inject verifier")

def main():
    print("[*] Installer start =>", APP_DIR)
    ensure_dir(APP_DIR)
    moved, suspects = quarantine_conflicts(APP_DIR)
    for src, dst in moved:
        print(f"[→] Quarantined {src} -> {dst}")
    if suspects:
        print("[!] Warning: possible widget monkeypatch found in:")
        for s in suspects:
            print("    -", s)
    deploy_safe_files(APP_DIR)
    print("[✓] Done. Please restart the Streamlit app process now.")
    print("[i] On the UI, look for the caption 'special_tests loaded from: ...' to confirm the active file.")

if __name__ == "__main__":
    main()
