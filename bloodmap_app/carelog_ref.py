
# -*- coding: utf-8 -*-
from __future__ import annotations
import os, json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Tuple
import streamlit as st

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

def _path(uid:str)->str:
    p = os.path.join(_root(), "care_log", f"{uid}.json")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    return p

def load(uid:str)->List[Dict[str,Any]]:
    try:
        return json.load(open(_path(uid),"r",encoding="utf-8"))
    except Exception:
        return []

def save(uid:str, data:List[Dict[str,Any]]):
    tmp = _path(uid)+".tmp"
    json.dump(data, open(tmp,"w",encoding="utf-8"), ensure_ascii=False, indent=2)
    os.replace(tmp, _path(uid))

def add(uid:str, e:Dict[str,Any]):
    d = load(uid); d.append(e); save(uid, d)

def analyze_symptoms(entries: List[Dict[str,Any]]) -> Tuple[List[str], List[str]]:
    em, gen = [], []
    from collections import Counter
    cnt = Counter(e.get("type") for e in entries)
    # counts within windows (we assume entries already filtered by 24h when passed in)
    vomit2h = sum(1 for e in entries if e.get("type")=="vomit")
    diarr24 = sum(1 for e in entries if e.get("type")=="diarrhea")
    kinds = [e.get("kind") for e in entries if e.get("type") in ("vomit","diarrhea")]
    has_green_vomit = any(k and "초록" in k for k in kinds)
    has_bloody = any(k and ("혈변" in k or "검은" in k) for k in kinds)
    fevers = [float(e.get("temp") or 0) for e in entries if e.get("type")=="fever"]
    has_high_fever = any(t >= 39.0 for t in fevers)
    if has_bloody: em.append("혈변/검은변/녹색혈변")
    if has_green_vomit: em.append("초록(담즙) 구토")
    if vomit2h >= 3: em.append("2시간 내 구토 ≥3회")
    if diarr24 >= 6: em.append("24시간 설사 ≥6회")
    if has_high_fever: em.append("고열 ≥39.0℃")
    gen = ["혈변/검은변","초록 구토","의식저하/경련/호흡곤란","6시간 무뇨·중증 탈수","고열 지속","심한 복통/팽만/무기력"]
    return em, gen

def _ko_line(e:Dict[str,Any])->str:
    t = e.get("type"); ts = e.get("ts","")
    if not t: return ""
    if t == "fever": return f"- {ts} · 발열 {e.get('temp')}℃"
    if t == "apap": return f"- {ts} · APAP {e.get('mg')} mg"
    if t == "ibu":  return f"- {ts} · IBU {e.get('mg')} mg"
    if t == "vomit": 
        k = e.get("kind"); return f"- {ts} · 구토" + (f" ({k})" if k else "")
    if t == "diarrhea":
        k = e.get("kind"); return f"- {ts} · 설사" + (f" ({k})" if k else "")
    return f"- {ts} · {t}"

def _filter_window(entries: List[Dict[str,Any]], hours:int)->List[Dict[str,Any]]:
    now = datetime.now(KST)
    out = []
    for e in entries or []:
        try: ts = datetime.fromisoformat(e.get("ts"))
        except Exception: continue
        if (now - ts).total_seconds() <= hours*3600:
            out.append(e)
    return out

def render(uid:str, nick:str, default_hours:int=24)->Tuple[List[str], List[Dict[str,Any]]]:
    st.markdown("### 🗒️ 케어로그")
    c1,c2,c3 = st.columns(3)
    with c1:
        if st.button("발열 +", key=f"btn_fever_{uid}"):
            t = st.number_input("현재 체온(℃)", value=38.0, step=0.1, key=f"temp_now_{uid}")
            add(uid, {"type":"fever","temp":t,"ts": datetime.now(KST).isoformat()})
            st.success("발열 기록됨")
    with c2:
        vk = st.selectbox("구토 유형", ["흰","노랑","초록(담즙)","기타"], index=1, key=f"vomit_kind_{uid}")
        if st.button("구토 +", key=f"btn_vomit_{uid}"):
            add(uid, {"type":"vomit","kind":vk,"ts": datetime.now(KST).isoformat()})
            st.success("구토 기록됨")
    with c3:
        dk = st.selectbox("설사 유형", ["노랑","진한노랑","거품","녹색","녹색혈변","혈변","검은색","기타"], index=0, key=f"diarr_kind_{uid}")
        if st.button("설사 +", key=f"btn_diarr_{uid}"):
            add(uid, {"type":"diarrhea","kind":dk,"ts": datetime.now(KST).isoformat()})
            st.success("설사 기록됨")

    st.divider()
    show = st.toggle("최근 로그 보기", value=False, key=f"toggle_show_{uid}")
    win = st.segmented_control("표시 시간창", options=[2,6,12,24], format_func=lambda h: f"{h}h", key=f"win_{uid}")
    if not show:
        st.caption("※ 입력 후 ‘최근 로그 보기’를 켜면 표시됩니다.")
        return [], []

    entries = _filter_window(load(uid), int(win))
    if not entries:
        st.info(f"최근 {win}시간 이내 기록 없음.")
        return [], []
    st.markdown(f"#### 최근 {win}h — {nick} ({uid})")
    lines = [_ko_line(e) for e in sorted(entries, key=lambda x: x.get("ts",""))]
    for L in lines: st.write(L)
    em, gen = analyze_symptoms(entries)
    if em: st.error("🚨 응급도: " + " · ".join(em))
    st.caption("일반 응급실 기준: " + " · ".join(gen))
    return lines, entries
