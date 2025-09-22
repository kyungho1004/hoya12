# -*- coding: utf-8 -*-
import json, os
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))

PATH = "/mnt/data/metrics/visits.json"

def _load() -> dict:
    try:
        with open(PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"total_visits":0, "unique_count":0, "today": {"date":"", "visits":0, "unique":0}, "uids": {}}

def _save(data: dict):
    os.makedirs(os.path.dirname(PATH), exist_ok=True)
    with open(PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def bump(uid: str):
    d = _load()
    today = datetime.now(KST).strftime("%Y-%m-%d")
    if d.get("today",{}).get("date") != today:
        d["today"] = {"date": today, "visits": 0, "unique": 0}
        d["uids"] = {}
    d["total_visits"] = int(d.get("total_visits",0)) + 1
    d["today"]["visits"] += 1
    if uid not in d["uids"]:
        d["uids"][uid] = True
        d["today"]["unique"] += 1
        d["unique_count"] = int(d.get("unique_count",0)) + 1
    _save(d)
    return d
