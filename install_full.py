# -*- coding: utf-8 -*-
"""
install_full_update.py
- write helper modules
- apply apply_full_patch.py to app.py
"""
from pathlib import Path
import subprocess, shutil
from datetime import datetime, timezone, timedelta

FILES = ["graph_store.py","carelog_ext.py","csv_importer.py","unit_guard.py","er_onepage.py","apply_full_patch.py"]

def main():
    root = Path(".")
    for f in FILES:
        src = Path("/mnt/data")/f
        dst = root/f
        dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        print("[write]", f)
    target = root/"app.py"
    if not target.exists():
        print("[error] app.py not found here.")
        return
    # backup
    KST = timezone(timedelta(hours=9))
    stamp = datetime.now(KST).strftime("%Y%m%d_%H%M")
    bak = root/f"app.py.bak_{stamp}"
    shutil.copy2(target, bak); print("[backup]", bak.name)
    # patch
    out = subprocess.check_output(["python","apply_full_patch.py", str(target)])
    (root/"app_patched.py").write_bytes(out)
    # replace
    shutil.move(str(root/"app_patched.py"), str(target))
    print("[ok] app.py replaced. Restart Streamlit.")

if __name__=="__main__":
    main()
