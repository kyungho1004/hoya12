# -*- coding: utf-8 -*-
import json, os
COUNTER_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "pageviews.json")

def get_count() -> int:
    if not os.path.exists(COUNTER_PATH):
        return 0
    try:
        with open(COUNTER_PATH, "r", encoding="utf-8") as f:
            return int(json.load(f).get("count", 0))
    except Exception:
        return 0

def bump_count() -> int:
    n = get_count() + 1
    try:
        with open(COUNTER_PATH, "w", encoding="utf-8") as f:
            json.dump({"count": n}, f, ensure_ascii=False)
    except Exception:
        pass
    return n
