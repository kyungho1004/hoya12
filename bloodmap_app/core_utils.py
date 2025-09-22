# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta


# ---------- 프로필/계정 유틸 ----------
import os, json, time, hashlib

PROFILE_DIR = "/mnt/data/profile"
PROFILE_INDEX = os.path.join(PROFILE_DIR, "index.json")

def _ensure_dirs():
    try:
        os.makedirs(PROFILE_DIR, exist_ok=True)
    except Exception:
        pass

def _norm_nick(n: str) -> str:
    s = (n or "").strip().lower()
    # 공백/특수문자 제거, 한글/영문/숫자만 남김
    keep = []
    for ch in s:
        if ch.isalnum() or ('\uac00' <= ch <= '\ud7a3'):
            keep.append(ch)
    return "".join(keep)

def _load_profiles_index() -> dict:
    _ensure_dirs()
    try:
        with open(PROFILE_INDEX, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _save_profiles_index(idx: dict) -> None:
    _ensure_dirs()
    tmp = PROFILE_INDEX + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(idx or {}, f, ensure_ascii=False, indent=2)
    os.replace(tmp, PROFILE_INDEX)

def _make_uid(nickname: str, pin4: str) -> str:
    raw = f"{(nickname or '').strip()}::{pin4}::{time.time()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

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

def nickname_pin():
    # 별명/PIN/저장 버튼 한 줄 배치
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        n = st.text_input("별명", placeholder="예: 은서엄마", key="nickname_field")
    with c2:
        p = st.text_input("PIN(4자리 숫자)", max_chars=4, placeholder="0000", key="pin_field")
    with c3:
        save_clicked = st.button("저장", use_container_width=True, type="primary")
        st.caption(" ")

    # 항상 숫자 4자리로 정규화 프리뷰
    p2 = "".join(ch for ch in (p or "") if ch.isdigit())[:4]
    if p and p2 != p:
        st.warning("PIN은 숫자 4자리만 허용됩니다.")
        try: st.toast("PIN 4자리 필요", icon="⚠️")
        except Exception: pass

    # key는 별명#PIN(프리뷰) 형태로 유지(기존 호환)
    key = (n.strip()+"#"+p2) if (n and p2) else (n or "guest")
    st.session_state["key"] = key

    # 저장 눌렀을 때만 검증/등록/로그인
    if save_clicked:
        nkey = _norm_nick(n)
        if not nkey:
            st.warning("별명을 입력하세요.")
            try: st.toast("별명 필요", icon="⚠️")
            except Exception: pass
            st.stop()
        if not p2 or len(p2) != 4:
            st.warning("PIN(4자리 숫자)을 입력하세요.")
            st.stop()

        idx = _load_profiles_index()
        rec = idx.get(nkey)

        if rec:  # 기존 별명
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
        else:     # 새 별명 등록 (별명은 유일)
            uid = _make_uid(n, p2)
            idx[nkey] = {"uid": uid, "pin": p2, "nickname": n, "created_ts": int(time.time())}
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



# === OVERRIDE: robust profile save path & helpers ===
try:
    import os, json, hashlib, time as _time, tempfile
    # Resolve profile index path with env overrides
    BASE_DATA_DIR = os.environ.get("BLOODMAP_DATA_DIR", "/mnt/data")
    PROFILE_INDEX = os.environ.get(
        "BLOODMAP_PROFILE_INDEX",
        os.path.join(BASE_DATA_DIR, "profile", "index.json")
    )

    def _ensure_dirs_for(path: str):
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
        except Exception:
            pass

    def _save_profiles_index(idx: dict) -> None:
        # primary path
        target = PROFILE_INDEX
        _ensure_dirs_for(target)
        tmp = target + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(idx or {}, f, ensure_ascii=False, indent=2)
            os.replace(tmp, target)
            return
        except Exception:
            # fallback to app dir
            try:
                app_dir = os.path.dirname(__file__)
                fallback = os.path.join(app_dir, "profile", "index.json")
                _ensure_dirs_for(fallback)
                tmp2 = fallback + ".tmp"
                with open(tmp2, "w", encoding="utf-8") as f:
                    json.dump(idx or {}, f, ensure_ascii=False, indent=2)
                os.replace(tmp2, fallback)
                globals()["PROFILE_INDEX"] = fallback
                return
            except Exception:
                pass
except Exception:
    pass
# === /OVERRIDE ===
