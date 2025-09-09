# -*- coding: utf-8 -*-
import json, os
from typing import Dict, Any, List
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
def get_user_key(nickname: str, pin4: str) -> str:
    pin4 = (pin4 or "").zfill(4)[:4]
    return f"{nickname.strip()}#{pin4}" if nickname else f"anonymous#{pin4}"
def _path(user_key: str) -> str:
    os.makedirs(DATA_DIR, exist_ok=True)
    return os.path.join(DATA_DIR, f"{user_key}.json")
def load_session(user_key: str) -> Dict[str, Any]:
    fp = _path(user_key)
    if not os.path.exists(fp):
        return {"history": []}
    with open(fp, "r", encoding="utf-8") as f:
        return json.load(f)
def append_history(user_key: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    doc = load_session(user_key)
    doc.setdefault("history", [])
    doc["history"].append(payload)
    with open(_path(user_key), "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    return doc
