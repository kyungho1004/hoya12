
# -*- coding: utf-8 -*-
import json, os
from typing import Dict, Any
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
def get_user_key(nickname: str, pin4: str) -> str:
    pin4 = (pin4 or "").zfill(4)[:4]
    return f"{nickname.strip()}#{pin4}" if nickname else f"anonymous#{pin4}"
def save_session(user_key: str, payload: Dict[str, Any]) -> str:
    os.makedirs(DATA_DIR, exist_ok=True)
    fp = os.path.join(DATA_DIR, f"{user_key}.json")
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return fp
def load_session(user_key: str) -> Dict[str, Any]:
    fp = os.path.join(DATA_DIR, f"{user_key}.json")
    if not os.path.exists(fp):
        return {}
    with open(fp, "r", encoding="utf-8") as f:
        return json.load(f)
