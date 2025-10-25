"""
Special Tests: core helpers (pure logic; UI-free).
Provide a stable shape to summarize emitted lines.
"""
from __future__ import annotations
from typing import Iterable, Tuple, List

def normalize_lines(lines: Iterable[str]) -> List[Tuple[str, str]]:
    """
    Accepts ['warn|message', 'risk|message', 'message'] and returns
    list of (level, message) where level in {'info','warn','risk'}.
    """
    out: List[Tuple[str, str]] = []
    for l in (lines or []):
        s = str(l or "").strip()
        if not s:
            continue
        if "|" in s:
            level, msg = s.split("|", 1)
            level = (level or "info").strip().lower()
            if level not in ("info","warn","risk"):
                level = "info"
            out.append((level, msg.strip()))
        else:
            out.append(("info", s))
    return out
