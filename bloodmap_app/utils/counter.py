# -*- coding: utf-8 -*-
import os, json

COUNTER_FILE = "/mnt/data/bloodmap_counter.json"

def _read():
    try:
        with open(COUNTER_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"count": 0}

def _write(obj):
    try:
        with open(COUNTER_FILE, "w", encoding="utf-8") as f:
            json.dump(obj, f)
    except Exception:
        pass

def bump():
    obj = _read()
    obj["count"] = int(obj.get("count", 0)) + 1
    _write(obj)

def count():
    return int(_read().get("count", 0))
