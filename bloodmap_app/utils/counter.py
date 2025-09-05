
# -*- coding: utf-8 -*-
import os, json

PATH = "visit_count.json"

def bump():
    try:
        d = json.load(open(PATH, "r", encoding="utf-8"))
    except Exception:
        d = {"count": 0}
    d["count"] = int(d.get("count", 0)) + 1
    json.dump(d, open(PATH, "w", encoding="utf-8"))
    return d["count"]

def count():
    try:
        d = json.load(open(PATH, "r", encoding="utf-8"))
        return int(d.get("count", 0))
    except Exception:
        return 1
