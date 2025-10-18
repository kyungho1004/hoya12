
# -*- coding: utf-8 -*-
"""
guards_smoke.py - BloodMap safety self-check (P0)
- Checks imports for core/optional modules
- Ensures critical dirs exist and are writable
- Renders a banner at the top; app continues regardless
"""
from __future__ import annotations

import os
import importlib
from datetime import datetime, timedelta, timezone

try:
    import streamlit as st
except Exception:  # pragma: no cover
    st = None  # type: ignore

KST = timezone(timedelta(hours=9))

REQUIRED_MODULES = [
    "branding",
    "pdf_export",
    "core_utils",
]
OPTIONAL_MODULES = [
    "peds_guide",
    "peds_dose",
    "special_tests",
    "onco_map",
    "drug_db",
]

CRITICAL_DIRS = [
    "/mnt/data",
    "/mnt/data/care_log",
    "/mnt/data/profile",
    "/mnt/data/bloodmap_graph",
]


def _try_import(name: str):
    try:
        mod = importlib.import_module(name)
        return name, True, getattr(mod, "__file__", "") or ""
    except Exception as e:  # pragma: no cover
        return name, False, f"{type(e).__name__}: {e}"


def _check_dirs():
    probs = []
    for d in CRITICAL_DIRS:
        try:
            os.makedirs(d, exist_ok=True)
        except Exception as e:
            probs.append(f"create failed: {d} — {e}")
            continue
        # write test
        try:
            testfile = os.path.join(d, ".bm_wrk")
            with open(testfile, "wb") as f:
                f.write(b"ok")
            os.remove(testfile)
        except Exception as e:
            probs.append(f"write failed: {d} — {e}")
    return probs


def run_safety_banner():
    if st is None:  # pragma: no cover
        return

    issues = []

    # imports
    for name in REQUIRED_MODULES:
        n, ok, detail = _try_import(name)
        if not ok:
            issues.append(f"required import failed: {n} — {detail}")
    for name in OPTIONAL_MODULES:
        n, ok, detail = _try_import(name)
        if not ok:
            issues.append(f"optional import missing (fallback to safe-mode): {n} — {detail}")

    # dirs
    issues.extend(_check_dirs())

    if not issues:
        st.success("✅ 안전 점검 통과 (KST %s)" % datetime.now(KST).strftime("%Y-%m-%d %H:%M"))
    else:
        with st.container(border=True):
            st.warning("🚧 안전 점검 경고 — 아래 항목을 확인하세요.")
            for it in issues:
                st.write("- " + it)
            st.caption("앱은 계속 동작합니다. 일부 기능은 안전모드로 대체될 수 있습니다.")
