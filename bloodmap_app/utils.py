# -*- coding: utf-8 -*-
import re, os, json, datetime as dt
from typing import Any, Dict

def to_float(x, default=None):
    try:
        if x is None: return default
        if isinstance(x, (int, float)): return float(x)
        s = str(x).strip().replace(",", "")
        if s == "": return default
        return float(s)
    except Exception:
        return default

def is_pos(x) -> bool:
    try:
        return float(x) > 0
    except Exception:
        return False

def sanitize_nickname(nick: str) -> str:
    # Allow Korean/English/number, strip spaces
    nick = (nick or "").strip()
    # Collapse internal whitespace
    nick = re.sub(r"\s+", " ", nick)
    return nick[:24]

def sanitize_pin(pin: str) -> str:
    digits = re.sub(r"\D", "", pin or "")
    digits = (digits + "0000")[:4]
    return digits

def make_storage_key(nick: str, pin: str) -> str:
    n = sanitize_nickname(nick)
    p = sanitize_pin(pin)
    return f"{n}#{p}" if n else ""

def save_record(base_dir: str, key: str, payload: Dict[str, Any]) -> str:
    os.makedirs(base_dir, exist_ok=True)
    safe_key = re.sub(r"[^0-9A-Za-z#가-힣_\.\-]", "_", key)
    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(base_dir, f"{safe_key}_{ts}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return path
