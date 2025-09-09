# -*- coding: utf-8 -*-
import os, json, time
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
USERS = os.path.join(DATA_DIR, "users.json")
RECORDS = os.path.join(DATA_DIR, "records.json")

def _load(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def _save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def register_user(user_key: str) -> bool:
    db = _load(USERS, {})
    if user_key in db:
        return False  # already exists
    db[user_key] = {"created": int(time.time())}
    _save(USERS, db)
    return True

def append_record(user_key: str, labs: dict) -> None:
    db = _load(RECORDS, {})
    recs = db.get(user_key, [])
    recs.append({"ts": int(time.time()), "labs": labs})
    db[user_key] = recs
    _save(RECORDS, db)

def get_records(user_key: str):
    db = _load(RECORDS, {})
    return db.get(user_key, [])
