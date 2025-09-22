
# -*- coding: utf-8 -*-
"""
peds_dx_log (hotfix)
- Adds alias `migrate_legacy_peds_dx_if_needed` for backward compatibility.
- Safe to drop-in replace existing peds_dx_log.py.
"""
from __future__ import annotations
import os, json
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List
import streamlit as st

KST = timezone(timedelta(hours=9))

def _data_root() -> str:
    cand = [os.getenv("BLOODMAP_DATA_ROOT","").strip(), "/mnt/data", os.path.join(os.getenv("TMPDIR") or "/tmp", "bloodmap_data")]
    for d in cand:
        if not d: continue
        try:
            os.makedirs(d, exist_ok=True)
            p = os.path.join(d, ".probe"); open(p, "w").write("ok"); os.remove(p); return d
        except Exception: pass
    d = os.path.join(os.getenv("TMPDIR") or "/tmp", "bloodmap_data"); os.makedirs(d, exist_ok=True); return d

def _data_path(*parts: str) -> str: return os.path.join(_data_root(), *parts)
def _peds_dx_path(uid: str) -> str: return _data_path("peds_dx", f"{uid}.json")

def load_peds_dx(uid: str) -> List[Dict[str, Any]]:
    try:
        with open(_peds_dx_path(uid), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_peds_dx(uid: str, rows: List[Dict[str, Any]]) -> None:
    p = _peds_dx_path(uid)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    os.replace(tmp, p)

def _legacy_paths(uid: str) -> List[str]:
    nick_only = uid.split("_")[0] if "_" in uid else uid
    cands = [
        f"/mnt/data/peds_dx/{uid}.json",
        f"/mnt/data/peds/{uid}.dx.json",
        f"/mnt/data/profile/{uid}_peds_dx.json",
        f"/tmp/bloodmap_data/peds_dx/{uid}.json",
        f"/mnt/data/peds_dx/{nick_only}.json",
    ]
    for d in ["/mnt/data/peds_dx", "/mnt/data/peds", "/tmp/bloodmap_data/peds_dx"]:
        try:
            if os.path.isdir(d):
                for fn in os.listdir(d):
                    if nick_only in fn and fn.endswith(".json"):
                        cands.append(os.path.join(d, fn))
        except Exception:
            pass
    out, seen = [], set()
    for p in cands:
        if p and p not in seen:
            out.append(p); seen.add(p)
    return out

def migrate_peds_dx_if_needed(uid: str):
    cur = load_peds_dx(uid)
    if cur: return False, 0, len(cur)
    found, merged = 0, []
    def _norm(rows):
        out = []
        for e in rows or []:
            if isinstance(e, dict):
                ts = e.get("ts") or e.get("date") or e.get("when")
                dx = e.get("dx") or e.get("진단") or e.get("text") or e.get("내용")
                if ts and dx: out.append({"ts": str(ts), "dx": str(dx)})
        return out
    for p in _legacy_paths(uid):
        try:
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                found += 1
                if isinstance(data, list): merged += _norm(data)
                elif isinstance(data, dict):
                    for k in [uid, "peds", "dx", "진단", "logs"]:
                        if k in data and isinstance(data[k], list):
                            merged += _norm(data[k])
                    for v in data.values():
                        if isinstance(v, list): merged += _norm(v)
        except Exception:
            continue
    seen, uniq = set(), []
    for e in merged:
        key = (e.get("ts"), e.get("dx"))
        if key in seen: continue
        seen.add(key); uniq.append(e)
    uniq.sort(key=lambda x: x.get("ts"))
    if uniq:
        save_peds_dx(uid, uniq); return True, found, len(uniq)
    return False, found, 0

# ---- Backward compatible alias (fixes NameError) ----
def migrate_legacy_peds_dx_if_needed(uid: str):
    return migrate_peds_dx_if_needed(uid)

def render_peds_dx_section(nick: str, uid: str) -> None:
    st.markdown("### 🧒 소아 진단 로그")
    try:
        mig, fcnt, cnt = migrate_peds_dx_if_needed(uid)
        if mig: st.success(f"소아 진단 로그 자동 복구: {cnt}건 (원본 {fcnt}개)")
    except Exception as e:
        st.caption(f"진단 로그 복구 스킵: {e}")
    rows = load_peds_dx(uid)
    if rows:
        for e in rows[-10:]:
            st.write(f"- {e.get('ts')} · {e.get('dx')}")
    else:
        st.caption("아직 진단 로그가 없습니다.")
    c1,c2 = st.columns([2,3])
    with c1: dx_text = st.text_input("진단/메모", value="", key=f"peds_dx_text_{uid}")
    with c2: ts_text = st.text_input("기록시각(ISO, 빈칸=지금)", value="", key=f"peds_dx_ts_{uid}")
    if st.button("소아 진단 추가", key=f"btn_add_peds_dx_{uid}"):
        ts = ts_text.strip() or datetime.now(KST).isoformat()
        save_peds_dx(uid, rows + [{"ts": ts, "dx": dx_text.strip()}])
        st.success("추가되었습니다.")
    if rows:
        s = "\n".join([f"- {e.get('ts')} · {e.get('dx')}" for e in rows])
        st.download_button("⬇️ 소아 진단 로그 TXT", data=s, file_name=f"peds_dx_{nick or uid}.txt", key=f"dl_peds_dx_txt_{uid}")
        try:
            from pdf_export import export_md_to_pdf  # type: ignore
            pdf = export_md_to_pdf("# 소아 진단 로그\n\n" + s)
            st.download_button("⬇️ 소아 진단 로그 PDF", data=pdf, file_name=f"peds_dx_{nick or uid}.pdf", mime="application/pdf", key=f"dl_peds_dx_pdf_{uid}")
        except Exception as e:
            st.caption(f"소아 진단 PDF 오류: {e}")
