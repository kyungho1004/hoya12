# -*- coding: utf-8 -*-
from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone, timedelta
import json

ROOT = Path("/mnt/data/care_log")
ROOT.mkdir(parents=True, exist_ok=True)

def kst_now_str():
    KST = timezone(timedelta(hours=9))
    return datetime.now(KST).strftime("%Y-%m-%d %H:%M")

def _uid(nick: str, pin: str) -> str:
    return f"{(nick or '').strip()}_{(pin or '').strip()}"

def _path(nick: str, pin: str) -> Path:
    return ROOT / f"{_uid(nick,pin)}.jsonl"

def add(nick: str, pin: str, kind: str, detail: str):
    data = {"ts_kst": kst_now_str(), "type": kind, "detail": detail}
    p = _path(nick, pin)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False)+"\n")
    return data

def read(nick: str, pin: str, hours: int = 24):
    from datetime import datetime as dt
    items = []
    p = _path(nick, pin)
    if not p.exists(): return []
    cutoff = dt.fromisoformat(kst_now_str())
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line.strip())
                items.append(obj)
            except Exception:
                continue
    # keep latest 24h-ish by simple count (UI will show latest anyway)
    return items[-500:]

def delete_last(nick: str, pin: str):
    p = _path(nick, pin)
    if not p.exists(): return False
    lines = p.read_text(encoding="utf-8").splitlines()
    if not lines: return False
    lines.pop()
    p.write_text("\n".join(lines)+("\n" if lines else ""), encoding="utf-8")
    return True

def export_txt(nick: str, pin: str) -> str:
    items = read(nick, pin, 24)
    lines = [f"[{x.get('ts_kst','')}] {x.get('type','')}: {x.get('detail','')}" for x in items]
    return "케어로그(최근 24h)\n" + "\n".join(lines)

def export_ics(nick: str, pin: str) -> str:
    items = read(nick, pin, 24)
    ICS = ["BEGIN:VCALENDAR","VERSION:2.0","PRODID:-//BloodMap//CareLog//KR"]
    for x in items:
        ts = x.get("ts_kst","").replace("-","").replace(":","").replace(" ","T")
        ICS.append("BEGIN:VEVENT")
        ICS.append(f"DTSTART;TZID=Asia/Seoul:{ts}00")
        ICS.append(f"SUMMARY:{x.get('type','')}")
        ICS.append(f"DESCRIPTION:{x.get('detail','')}")
        ICS.append("END:VEVENT")
    ICS.append("END:VCALENDAR")
    return "\n".join(ICS)
