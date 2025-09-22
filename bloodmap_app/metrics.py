# -*- coding: utf-8 -*-
import json, os, tempfile
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))

ENV_PATH = os.getenv("BLOODMAP_METRICS_PATH", "").strip()
DEF_PATHS = [
    ENV_PATH if ENV_PATH else "/mnt/data/metrics/visits.json",
    os.path.join(tempfile.gettempdir(), "bloodmap_metrics", "visits.json"),
]

def _ensure_dir_for(path: str):
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)

def _writable_dir(d: str) -> bool:
    try:
        _ensure_dir_for(os.path.join(d, ".probe"))
        testfile = os.path.join(d, ".probe")
        with open(testfile, "w", encoding="utf-8") as f:
            f.write("ok")
        os.remove(testfile)
        return True
    except Exception:
        return False

def _pick_save_path() -> str:
    if ENV_PATH:
        try:
            _ensure_dir_for(ENV_PATH)
            d = os.path.dirname(ENV_PATH)
            if _writable_dir(d):
                return ENV_PATH
        except Exception:
            pass
    for p in DEF_PATHS:
        try:
            _ensure_dir_for(p)
            if _writable_dir(os.path.dirname(p)):
                return p
        except Exception:
            continue
    p = os.path.join(tempfile.gettempdir(), "bloodmap_metrics", "visits.json")
    _ensure_dir_for(p)
    return p

def _load_any() -> tuple[dict, str]:
    for p in DEF_PATHS:
        try:
            if p and os.path.exists(p):
                with open(p, "r", encoding="utf-8") as f:
                    return json.load(f), p
        except Exception:
            continue
    return {"total_visits":0, "unique_count":0, "today": {"date":"", "visits":0, "unique":0}, "uids": {}}, _pick_save_path()

def _save(data: dict) -> str:
    path = _pick_save_path()
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)
    return path

def bump(uid: str):
    d, _ = _load_any()
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
    saved_path = _save(d)
    return {**d, "_path": saved_path}
