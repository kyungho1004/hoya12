
# ui_patch_safest.py — SAFE PASS-THROUGH (no monkeypatch)
# Keeps API surface but does nothing; prevents unintended key resets or reruns.
from __future__ import annotations

def attach(*args, **kwargs):
    return

# Backwards compatibility shims
def wrap_streamlit_widgets(*args, **kwargs):
    return
