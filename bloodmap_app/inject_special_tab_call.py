# -*- coding: utf-8 -*-
"""
inject_special_tab_call.py
- Finds the '특수검사' tab/container and injects two lines to call the UI:
    from special_tests_finder import render_special_tests_safe
    render_special_tests_safe()
- Makes a backup app.py.bak once.
"""
import re, ast, shutil
from pathlib import Path

APP = Path("app.py")
if not APP.exists():
    print("[ERR] app.py not found here.")
    raise SystemExit(2)

backup = APP.with_suffix(".py.bak")
if not backup.exists():
    shutil.copy2(APP, backup)

src = APP.read_text(encoding="utf-8")

inject = "\nfrom special_tests_finder import render_special_tests_safe\nrender_special_tests_safe()\n"
changed = False

# Strategy 1: after a header that contains '특수검사'
m = re.search(r"(st\.(?:header|subheader|markdown|title)\([^\n]*?특수검사[^\n]*?\)\s*)", src)
if m and "render_special_tests_safe()" not in src:
    pos = m.end(1)
    src = src[:pos] + inject + src[pos:]
    changed = True

# Strategy 2: inside a tab named '특수검사'
if not changed and "render_special_tests_safe()" not in src:
    m = re.search(r"\(\s*['\"]특수검사['\"]\s*\)", src)  # find tab label literal
    if m:
        # insert shortly after the first occurrence
        idx = m.end(0)
        src = src[:idx] + inject + src[idx:]
        changed = True

# Final: if still not injected, append at end (safe fallback)
if not changed and "render_special_tests_safe()" not in src:
    src += "\n# [AUTO-INSERT] 특수검사 안전 호출\nfrom special_tests_finder import render_special_tests_safe\nrender_special_tests_safe()\n"
    changed = True

ast.parse(src)
APP.write_text(src, encoding="utf-8")
print("[OK] Injected call to render_special_tests_safe(). Backup saved as app.py.bak")
