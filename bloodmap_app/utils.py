
# -*- coding: utf-8 -*-
def to_float(val, default: float = 0.0) -> float:
    try:
        if val is None:
            return default
        return float(val)
    except (TypeError, ValueError):
        return default

def is_pos(val) -> bool:
    try:
        return float(val) > 0
    except Exception:
        return False

def digits_only(s: str, n: int = 4) -> str:
    if not s:
        return ""
    return "".join(ch for ch in str(s) if ch.isdigit())[:n]
