#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BloodMap repo cleaner
- Resolves 'utils.py' vs 'utils/' name conflict by renaming utils.py -> app_utils.py
- Rewrites specific imports to use app_utils (only for user_key/init_state)
- Ensures bloodmap_app/app.py has a universal import header
- Normalizes fonts folder and config FONT_PATH_REG auto-detection
- Ensures streamlit_app.py launches bloodmap_app.app:main
Run from the repository root:  python fix_bloodmap_repo.py
"""

import os, re, sys, shutil, io
from pathlib import Path

ROOT = Path(".").resolve()
PKG = ROOT / "bloodmap_app"
APP = PKG / "app.py"
UTILS_FILE = PKG / "utils.py"
APP_UTILS = PKG / "app_utils.py"
UTILS_PKG = PKG / "utils"
CONFIG = PKG / "config.py"
STREAMLIT_ENTRY = ROOT / "streamlit_app.py"
FONTS = ROOT / "fonts"
FONFS = ROOT / "fonfs"
HEADER_MARK = "Universal Import Header"
HEADER_FILE = Path(__file__).with_name("UNIVERSAL_IMPORT_HEADER.py")

def info(msg): print("•", msg)

def replace_in_file(path: Path, replacements: list[tuple[str,str]]):
    txt = path.read_text(encoding="utf-8")
    orig = txt
    for a, b in replacements:
        txt = re.sub(a, b, txt)
    if txt != orig:
        path.write_text(txt, encoding="utf-8")
        return True
    return False

def add_universal_header():
    if not APP.exists():
        info("WARN: bloodmap_app/app.py not found, skip header")
        return False
    txt = APP.read_text(encoding="utf-8")
    if HEADER_MARK in txt:
        info("Header already present.")
        return False
    header = HEADER_FILE.read_text(encoding="utf-8")
    APP.write_text(header + "\n\n" + txt, encoding="utf-8")
    info("Inserted Universal Import Header into bloodmap_app/app.py")
    return True

def rename_utils_file():
    if UTILS_FILE.exists():
        # Only rename if a package 'utils/' also exists to avoid conflict
        if UTILS_PKG.exists():
            shutil.move(str(UTILS_FILE), str(APP_UTILS))
            info("Renamed utils.py -> app_utils.py (to avoid conflict with utils package)")
            return True
        else:
            # No conflict; still rename for future safety
            shutil.move(str(UTILS_FILE), str(APP_UTILS))
            info("Renamed utils.py -> app_utils.py")
            return True
    return False

def rewrite_imports():
    changed = 0
    for path in PKG.rglob("*.py"):
        if path.name == "__init__.py": continue
        # Precise replacements for user_key/init_state only
        c1 = replace_in_file(path, [
            (r"from\s+\.utils\s+import\s+user_key,\s*init_state", "from .app_utils import user_key, init_state"),
            (r"from\s+utils\s+import\s+user_key,\s*init_state", "from app_utils import user_key, init_state"),
        ])
        if c1: 
            changed += 1
            info(f"Updated imports in {path.relative_to(ROOT)}")
    return changed

def normalize_fonts_and_config():
    # Prefer folder name 'fonts'
    if FONFS.exists() and not FONTS.exists():
        shutil.move(str(FONFS), str(FONTS))
        info("Renamed fonfs/ -> fonts/")
    # Patch config.py to auto-detect available font file
    if CONFIG.exists():
        txt = CONFIG.read_text(encoding="utf-8")
        if "FONT_PATH_REG" not in txt:
            txt = "import os\n" + txt
            CONFIG.write_text(txt, encoding="utf-8")
        add = r