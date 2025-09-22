
# -*- coding: utf-8 -*-
"""
carelog_utils (shim)
- 앱에서 기대하는 API: carelog_add, carelog_load, format_care_lines, render_carelog
- 우선 carelog_renderer_fix 모듈로 포워딩하고, 없으면 내부 간소 구현으로 동작합니다.
"""
from __future__ import annotations

try:
    from carelog_renderer_fix import (
        carelog_add, carelog_load, format_care_lines, render_carelog
    )
except Exception:
    # Fallback minimal implementation
    import os, json
    from datetime import datetime, timedelta, timezone
    try:
        from zoneinfo import ZoneInfo  # py>=3.9
        KST = ZoneInfo("Asia/Seoul")
    except Exception:
        KST = timezone(timedelta(hours=9))

    _BASE = os.path.join(os.getenv("BLOODMAP_DATA_ROOT","/mnt/data"), "care_log")
    os.makedirs(_BASE, exist_ok=True)

    def _path(uid:str)->str:
        uid = (uid or "guest").strip() or "guest"
        return os.path.join(_BASE, f"{uid}.json")

    def _load(uid:str):
        p=_path(uid)
        try:
            if os.path.exists(p):
                return json.load(open(p,"r",encoding="utf-8"))
        except Exception:
            pass
        return []

    def carelog_load(uid:str):
        data=_load(uid)
        out=[]
        for e in data:
            if not isinstance(e, dict): 
                continue
            ts = e.get("ts") or datetime.now(KST).isoformat()
            if "T" in ts and not ts.endswith("+09:00") and "Z" not in ts and "+" not in ts:
                ts = ts + "+09:00"
            e2 = dict(e); e2["ts"]=ts; out.append(e2)
        out.sort(key=lambda x: x["ts"])
        return out

    def carelog_add(uid:str, entry:dict)->bool:
        cur = carelog_load(uid)
        e = dict(entry)
        e.setdefault("ts", datetime.now(KST).isoformat())
        t = (e.get("type") or "").lower()
        if t=="vomit":  e.setdefault("label_ko","구토")
        elif t=="diarrhea": e.setdefault("label_ko","설사")
        elif t=="fever": e.setdefault("label_ko", f"발열 {e.get('temp','')}℃".strip())
        elif t=="apap": e.setdefault("label_ko", f"APAP {e.get('mg','')} mg".strip())
        elif t=="ibu":  e.setdefault("label_ko", f"IBU {e.get('mg','')} mg".strip())
        else: e.setdefault("label_ko", t or "기록")
        cur.append(e)
        try:
            os.makedirs(_BASE, exist_ok=True)
            json.dump(cur, open(_path(uid),"w",encoding="utf-8"), ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    def format_care_lines(uid:str, nick:str|None=None, hours:int=24):
        now = datetime.now(KST)
        cutoff = now - timedelta(hours=max(1,int(hours)))
        items = []
        for e in carelog_load(uid):
            try:
                ts = e.get("ts"); 
                dt = datetime.fromisoformat(ts.replace("Z","+00:00"))
            except Exception:
                dt = now
            if dt >= cutoff:
                items.append(e)
        items.sort(key=lambda x: x["ts"], reverse=True)
        def _line(e):
            return f"{e.get('ts')} · {e.get('label_ko') or e.get('type','')}" + (f" — {nick}" if nick else "")
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
        st.code("\n".join(lines) if lines else "표시할 항목이 없습니다.", language="")
        return lines, entries
