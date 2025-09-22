
# -*- coding: utf-8 -*-
"""
carelog_utils — Permission-safe, KST, per-UID care log utils
- Exposes: carelog_add, carelog_load, format_care_lines, render_carelog
- Falls back to /tmp when /mnt/data is not writable.
- If carelog_renderer_fix exists, forwards to it.
"""
from __future__ import annotations

# 1) Try forwarding to canonical module if present
try:
    from carelog_renderer_fix import (
        carelog_add, carelog_load, format_care_lines, render_carelog
    )
    # If import succeeded, we are done.
except Exception:
    # 2) Minimal internal implementation with robust path fallback
    import os, json
    from datetime import datetime, timedelta, timezone
    try:
        from zoneinfo import ZoneInfo  # py>=3.9
        KST = ZoneInfo("Asia/Seoul")
    except Exception:
        KST = timezone(timedelta(hours=9))

    def _probe_dir(candidates):
        """Return first path we can create/write a probe file in."""
        for base in candidates:
            if not base:
                continue
            try:
                os.makedirs(base, exist_ok=True)
                probe = os.path.join(base, ".probe")
                with open(probe, "w", encoding="utf-8") as f:
                    f.write("ok")
                os.remove(probe)
                return base
            except Exception:
                continue
        # last resort
        last = os.path.join("/tmp", "bloodmap_data")
        try:
            os.makedirs(last, exist_ok=True)
        except Exception:
            pass
        return last

    _ROOT = _probe_dir([
        os.path.join(os.getenv("BLOODMAP_DATA_ROOT","/mnt/data"), ""),
        os.getenv("TMPDIR"),
        "/tmp",
    ])
    _BASE = os.path.join(_ROOT, "care_log")
    try:
        os.makedirs(_BASE, exist_ok=True)
    except Exception:
        # ignore; we'll try writing files lazily and report failures as False
        pass

    def _path(uid:str)->str:
        uid = (uid or "guest").strip() or "guest"
        return os.path.join(_BASE, f"{uid}.json")

    def _safe_json_load(path:str):
        try:
            if os.path.exists(path):
                with open(path,"r",encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            return []
        return []

    def carelog_load(uid:str):
        data = _safe_json_load(_path(uid))
        out=[]
        for e in data or []:
            if not isinstance(e, dict):
                continue
            ts = e.get("ts")
            # normalize ts → ISO with tz
            try:
                if ts:
                    if "T" in ts and ("+" in ts or ts.endswith("Z")):
                        iso = ts
                    else:
                        # assume local KST if tz missing
                        iso = ts + "+09:00"
                else:
                    iso = datetime.now(KST).isoformat()
            except Exception:
                iso = datetime.now(KST).isoformat()
            e2 = dict(e); e2["ts"] = iso
            out.append(e2)
        out.sort(key=lambda x: x["ts"])
        return out

    def carelog_add(uid:str, entry:dict)->bool:
        cur = carelog_load(uid)
        e = dict(entry or {})
        if not e.get("ts"):
            e["ts"] = datetime.now(KST).isoformat()
        t = (e.get("type") or "").lower()
        temp = e.get("temp")
        mg = e.get("mg")
        if t=="vomit":
            e.setdefault("label_ko","구토")
        elif t=="diarrhea":
            e.setdefault("label_ko","설사")
        elif t=="fever":
            e.setdefault("label_ko", f"발열 {temp}℃" if temp is not None else "발열")
        elif t=="apap":
            e.setdefault("label_ko", f"APAP {mg} mg" if mg is not None else "APAP")
        elif t=="ibu":
            e.setdefault("label_ko", f"IBU {mg} mg" if mg is not None else "IBU")
        else:
            e.setdefault("label_ko", t or "기록")
        cur.append(e)
        # ensure base exists (retry here)
        try:
            os.makedirs(_BASE, exist_ok=True)
        except Exception:
            pass
        try:
            with open(_path(uid),"w",encoding="utf-8") as f:
                json.dump(cur, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            # read-only FS → don't crash; return False
            return False

    def format_care_lines(uid:str, nick:str|None=None, hours:int=24):
        now = datetime.now(KST)
        cutoff = now - timedelta(hours=max(1,int(hours)))
        items = []
        for e in carelog_load(uid):
            ts = e.get("ts")
            try:
                if ts and ts.endswith("Z"):
                    dt = datetime.fromisoformat(ts.replace("Z","+00:00"))
                else:
                    # tolerate "+09:00" or naive
                    dt = datetime.fromisoformat(ts) if ts else now
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=KST)
            except Exception:
                dt = now
            if dt >= cutoff:
                items.append(e)
        items.sort(key=lambda x: x["ts"], reverse=True)
        def _line(e):
            who = f" — {nick}" if nick else ""
            return f"{e.get('ts')} · {e.get('label_ko') or e.get('type','')}{who}"
        return [ _line(e) for e in items ], items

    def render_carelog(st, uid:str, nick:str|None=None, hours_default:int=24):
        win = st.slider(f"최근 로그(시간) — {uid}", min_value=2, max_value=72, value=hours_default, step=2, key=f"win_{uid}")
        c1,c2,c3,c4,c5 = st.columns(5)
        if c1.button("구토", key=f"btn_vomit_{uid}"):
            carelog_add(uid, {"type":"vomit"})
        if c2.button("설사", key=f"btn_diarrhea_{uid}"):
            carelog_add(uid, {"type":"diarrhea"})
        if c3.button("발열 38.0℃", key=f"btn_fever_{uid}"):
            carelog_add(uid, {"type":"fever", "temp":38.0})
        if c4.button("APAP 기록", key=f"btn_apap_{uid}"):
            carelog_add(uid, {"type":"apap", "mg":160})
        if c5.button("IBU 기록", key=f"btn_ibu_{uid}"):
            carelog_add(uid, {"type":"ibu", "mg":100})
        lines, entries = format_care_lines(uid, nick, hours=int(win))
        st.markdown("**🗒️ 최근 로그**")
        st.code("\\n".join(lines) if lines else "표시할 항목이 없습니다.", language="")
        return lines, entries
