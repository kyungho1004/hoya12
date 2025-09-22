# --- AUTO: nickname registry helpers (unique nickname, PIN for auth) ---
import os, json, hashlib, time as _time, tempfile

def _profiles_index_path():
    return os.environ.get("BLOODMAP_PROFILE_INDEX", "/mnt/data/profile/index.json")

def _atomic_write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".tmp_idx_", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    finally:
        try: os.remove(tmp)
        except Exception: pass

def _load_profiles_index():
    p = _profiles_index_path()
    if os.path.exists(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def _save_profiles_index(d: dict):
    try:
        _atomic_write_json(_profiles_index_path(), d)
    except Exception:
        pass

def _norm_nick(s: str) -> str:
    return (s or "").strip().lower()

def _make_uid(nick: str, pin: str) -> str:
    seed = f"{_norm_nick(nick)}|{(pin or '').strip()}"
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]

def _migrate_composite_keys(idx: dict) -> dict:
    # Fold keys like "nickname|PIN" into single "nickname"
    changed = False
    items = list(idx.items())
    for k, v in items:
        if "|" in k:
            nkey, p = k.split("|", 1)
            rec = idx.get(nkey)
            if not rec:
                idx[nkey] = {"uid": v.get("uid"), "pin": v.get("pin") or p, "nickname": v.get("nickname") or nkey, "created_ts": v.get("created_ts") or int(_time.time())}
                changed = True
            else:
                # prefer existing uid; if no pin stored, adopt this pin
                if "pin" not in rec or not rec.get("pin"):
                    rec["pin"] = v.get("pin") or p
                    changed = True
            idx.pop(k, None)
            changed = True
    if changed:
        _save_profiles_index(idx)
    return idx
# --- /AUTO ---

import time as _time
import hashlib
import json
import os
# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta

# ---------- 숫자/포맷 유틸 ----------
def clean_num(s):
    if s is None: return None
    try:
        x = str(s).strip().replace("±","").replace("+","").replace(",","")
        if x in {"","-"}: return None
        return float(x)
    except: return None

def round_half(x):
    try: return round(float(x)*2)/2
    except: return None

def temp_band(t):
    try: t = float(t)
    except: return None
    if t < 37: return "36~37℃"
    if t < 38: return "37~38℃"
    if t < 39: return "38~39℃"
    return "≥39℃"

def rr_thr_by_age_m(m):
    try: m = float(m)
    except: return None
    if m < 2: return 60
    if m < 12: return 50
    if m < 60: return 40
    return 30

# ---------- 닉네임/PIN ----------
# --- AUTO: nickname registry helpers ---
def _profiles_index_path():
    return "/mnt/data/profile/index.json"

def _load_profiles_index():
    pth = _profiles_index_path()
    if os.path.exists(pth):
        try:
            with open(pth, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def _save_profiles_index(d: dict):
    try:
        os.makedirs("/mnt/data/profile", exist_ok=True)
        with open(_profiles_index_path(), "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def _norm_nick(s: str) -> str:
    return (s or "").strip().lower()

def _make_uid(nick: str, pin: str) -> str:
    seed = f"{_norm_nick(nick)}|{(pin or '').strip()}"
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]
# --- /AUTO ---
def nickname_pin():
    c1,c2 = st.columns([2,1])
    with c1: n = st.text_input("별명", placeholder="예: 은서엄마")
    with c2: p = st.text_input("PIN(4자리 숫자)", max_chars=4, placeholder="0000")
    p2 = "".join(ch for ch in (p or "") if ch.isdigit())[:4]
    if p and p2 != p:
        st.warning("PIN은 숫자 4자리만 허용됩니다.")
    key = (n.strip()+"#"+p2) if (n and p2) else (n or "guest")
    st.session_state["key"] = key

    nkey = _norm_nick(n)
    if nkey:
        idx = _load_profiles_index()
        idx = _migrate_composite_keys(idx)  # fold legacy entries
        rec = idx.get(nkey)
        if rec:  # nickname exists -> require correct PIN
            if not p2 or len(p2) != 4:
                st.warning("PIN(4자리 숫자)을 입력하세요."); st.stop()
            if rec.get("pin") == p2:
                uid = rec.get("uid")
                st.session_state["user_key"] = uid
                st.caption(f"등록된 별명으로 로그인되었습니다. UID: **{uid}**")
                try: st.toast("로그인 완료", icon="✅")
                except Exception: pass
            else:
                st.error("PIN이 일치하지 않습니다. 기존 PIN이 필요합니다.")
                try: st.toast("잘못된 PIN", icon="❌")
                except Exception: pass
                st.stop()
        else:    # new nickname -> register with provided PIN
            if not p2 or len(p2) != 4:
                st.warning("PIN(4자리 숫자)을 입력하세요."); st.stop()
            uid = _make_uid(n, p2)
            idx[nkey] = {"uid": uid, "pin": p2, "nickname": n, "created_ts": int(_time.time())}
            _save_profiles_index(idx)
            st.session_state["user_key"] = uid
            st.caption(f"새 별명으로 등록되었습니다. UID: **{uid}**")
            try: st.toast("등록 완료", icon="✅")
            except Exception: pass
    return n, p2, key
# ---------- 스케줄 ----------
def schedule_block():
    st.markdown("#### 📅 항암 스케줄(간단)")
    from datetime import date, timedelta
    c1,c2,c3 = st.columns(3)
    with c1: start = st.date_input("시작일", value=date.today())
    with c2: cycle = st.number_input("주기(일)", min_value=1, step=1, value=21)
    with c3: ncyc = st.number_input("사이클 수", min_value=1, step=1, value=6)
    if st.button("스케줄 생성/추가"):
        rows = [{"Cycle": i+1, "Date": (start + timedelta(days=i*int(cycle))).strftime("%Y-%m-%d")} for i in range(int(ncyc))]
        df = pd.DataFrame(rows)
        st.session_state.setdefault("schedules", {})
        st.session_state["schedules"][st.session_state["key"]] = df
        st.success("스케줄이 저장되었습니다.")
    df = st.session_state.get("schedules", {}).get(st.session_state.get("key","guest"))
    if isinstance(df, pd.DataFrame) and not df.empty:
        st.dataframe(df, use_container_width=True, height=180)
