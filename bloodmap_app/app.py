# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import os, json, tempfile
from datetime import date, datetime, timedelta, timezone

# ---- Timezone ----
KST = timezone(timedelta(hours=9))

# ---- Writable data root helpers (ENV + /mnt/data + /tmp fallback) ----
def _ensure_dir_for(path: str):
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)

def _writable_dir(d: str) -> bool:
    try:
        os.makedirs(d, exist_ok=True)
        probe = os.path.join(d, ".probe")
        with open(probe, "w", encoding="utf-8") as f:
            f.write("ok")
        os.remove(probe)
        return True
    except Exception:
        return False

def _data_root() -> str:
    env = os.getenv("BLOODMAP_DATA_ROOT", "").strip()
    cands = [env] if env else ["/mnt/data"]
    cands.append(os.path.join(tempfile.gettempdir(), "bloodmap_data"))
    for root in cands:
        if not root:
            continue
        if _writable_dir(root):
            return root
    root = os.path.join(tempfile.gettempdir(), "bloodmap_data")
    os.makedirs(root, exist_ok=True)
    return root

def _data_path(*parts) -> str:
    return os.path.join(_data_root(), *parts)

# ---- Profile/Carelog disk I/O ----
def _profile_path(uid: str) -> str:
    return _data_path("profile", f"{uid}.json")

def _carelog_path(uid: str) -> str:
    return _data_path("care_log", f"{uid}.json")

def load_profile(uid: str):
    try:
        with open(_profile_path(uid), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_profile(uid: str, data: dict):
    path = _profile_path(uid)
    _ensure_dir_for(path)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)

def load_carelog(uid: str):
    try:
        with open(_carelog_path(uid), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_carelog(uid: str, entries: list):
    path = _carelog_path(uid)
    _ensure_dir_for(path)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)

# ---- Minimal stub UI to verify save_profile works without /mnt/data PermissionError ----
st.set_page_config(page_title="BloodMap Hotfix P3", page_icon="🩸", layout="centered")
st.title("BloodMap Hotfix — Profile/Carelog Writable Path")

nick = st.text_input("별명", value=st.session_state.get("nick","guest"))
pin  = st.text_input("PIN(4자리)", value=st.session_state.get("pin","0000"))
uid = f"{nick}_{pin}" if nick and pin else "guest_0000"

# Load existing
prof0 = load_profile(uid)
c1,c2,c3,c4 = st.columns(4)
with c1: sex = st.selectbox("성별", ["여","남"], index=0 if prof0.get("sex","여")=="여" else 1)
with c2: age = st.number_input("나이(년)", min_value=0, step=1, value=int(prof0.get("age",30)))
with c3: height_cm = st.number_input("키(cm)", min_value=0.0, step=0.5, value=float(prof0.get("height_cm",160.0)))
with c4: weight_kg = st.number_input("체중(kg)", min_value=0.0, step=0.1, value=float(prof0.get("weight_kg",50.0)))

if st.button("프로필 저장"):
    data = {"sex":sex, "age":int(age), "height_cm":float(height_cm), "weight_kg":float(weight_kg)}
    save_profile(uid, data)
    st.success(f"저장 OK → {_profile_path(uid)}")

# Carelog quick test
if st.button("케어로그 샘플 추가"):
    now = datetime.now(KST).isoformat()
    rows = load_carelog(uid)
    rows.append({"type":"fever","temp":38.0,"ts":now})
    save_carelog(uid, rows)
    st.success(f"케어로그 OK → {_carelog_path(uid)}")
