"""
Carelog CSV schema utilities — normalize heterogenous rows.
"""
from __future__ import annotations
from datetime import datetime

WANTED = ["ts","timestamp","type","event","note","qty","unit","temp","hr","bp"]

def normalize_row(r: dict) -> dict:
    """Return a dict with a consistent subset of keys; missing as empty string."""
    out = {}
    for k in WANTED:
        out[k] = str(r.get(k, "")).strip()
    return out

def parse_ts(s: str) -> datetime | None:
    s = (s or "").strip()
    if not s:
        return None
    # Try common formats
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y/%m/%d %H:%M", "%Y.%m.%d %H:%M"):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            pass
    # Fallback: fromisoformat tolerant
    try:
        return datetime.fromisoformat(s.replace("Z","").replace("/", "-").replace(".", "-"))
    except Exception:
        return None
