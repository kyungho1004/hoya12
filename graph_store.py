# -*- coding: utf-8 -*-
from __future__ import annotations
from pathlib import Path
import json, csv, os
from datetime import datetime, timezone, timedelta

ROOT = Path("/mnt/data/bloodmap_graph")
ROOT.mkdir(parents=True, exist_ok=True)

def _uid(nick: str, pin: str) -> str:
    return f"{(nick or '').strip()}_{(pin or '').strip()}"

def save_config(nick: str, pin: str, config: dict) -> Path:
    uid = _uid(nick, pin)
    p = ROOT / f"{uid}.json"
    p.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    return p

def save_labs_csv(nick: str, pin: str, rows):
    uid = _uid(nick, pin)
    p = ROOT / f"{uid}.labs.csv"
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ts_kst","WBC","Hb","PLT","CRP","ANC","Na","K","Cr"])
        for r in rows:
            w.writerow([r.get("ts_kst",""), r.get("WBC",""), r.get("Hb",""), r.get("PLT",""),
                        r.get("CRP",""), r.get("ANC",""), r.get("Na",""), r.get("K",""), r.get("Cr","")])
    return p

def load_config(nick: str, pin: str) -> dict:
    p = ROOT / f"{_uid(nick,pin)}.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}

def exists(nick: str, pin: str) -> bool:
    return (ROOT / f"{_uid(nick,pin)}.json").exists()

def list_files(nick: str, pin: str):
    uid = _uid(nick, pin)
    return [str(x) for x in ROOT.glob(f"{uid}.*")]
