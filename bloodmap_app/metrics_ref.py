
# -*- coding: utf-8 -*-
import os, json
from datetime import datetime, timedelta, timezone
KST = timezone(timedelta(hours=9))

def _root()->str:
    for d in [os.getenv("BLOODMAP_DATA_ROOT","").strip(), "/mnt/data", os.path.join(os.getenv("TMPDIR") or "/tmp","bloodmap_data")]:
        if not d: continue
        try:
            os.makedirs(d, exist_ok=True)
            p = os.path.join(d, ".probe"); open(p,"w").write("ok"); os.remove(p)
            return d
        except Exception:
            continue
    d = os.path.join(os.getenv("TMPDIR") or "/tmp","bloodmap_data"); os.makedirs(d, exist_ok=True); return d

PATH = os.path.join(_root(), "metrics", "visits.json"); os.makedirs(os.path.dirname(PATH), exist_ok=True)

def bump(uid:str)->dict:
    try:
        d = json.load(open(PATH,"r",encoding="utf-8"))
    except Exception:
        d = {"total_visits":0,"unique":{}}
    d["total_visits"] = int(d.get("total_visits",0))+1
    uniq = d.setdefault("unique",{})
    uniq[uid] = int(uniq.get(uid,0))+1
    d["today"] = datetime.now(KST).date().isoformat()
    json.dump(d, open(PATH,"w",encoding="utf-8"), ensure_ascii=False, indent=2)
    return d
