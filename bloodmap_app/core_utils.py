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
def nickname_pin():
    c1,c2 = st.columns([2,1])
    with c1: n = st.text_input("별명", placeholder="예: 은서엄마")
    with c2: p = st.text_input("PIN(4자리 숫자)", max_chars=4, placeholder="0000")
    p2 = "".join([c for c in (p or "") if c.isdigit()])[:4]
    if p and p2!=p: st.warning("PIN은 숫자 4자리만 허용됩니다.")
    key = (n.strip()+"#"+p2) if (n and p2) else (n or "guest")
    st.session_state["key"] = key
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

# ---------- eGFR (CKD-EPI 2009) ----------
def egfr_ckd_epi_2009(scr_mg_dl, age_years, sex: str):
    """Return eGFR (mL/min/1.73m2) using CKD-EPI 2009 for adults (>=18y).
    sex: 'M' or 'F' (case-insensitive). Returns None if inputs invalid.
    """
    try:
        scr = float(scr_mg_dl); age = int(age_years)
        if age < 18: return None
        sex = (sex or '').strip().upper()
        k = 0.7 if sex=='F' else 0.9
        a = -0.329 if sex=='F' else -0.411
        min_scr = min(scr/k, 1.0)
        max_scr = max(scr/k, 1.0)
        egfr = 141 * (min_scr ** a) * (max_scr ** -1.209) * (0.993 ** age)
        if sex == 'F':
            egfr *= 1.018
        # Ethnicity factor omitted intentionally
        return round(egfr)
    except Exception:
        return None

# ---------- Care log I/O ----------
def _care_log_path():
    import os
    d = "/mnt/data/care_log"
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "log.csv")

def read_care_log():
    p = _care_log_path()
    try:
        import pandas as pd
        if os.path.exists(p):
            return pd.read_csv(p)
    except Exception:
        pass
    import pandas as pd
    return pd.DataFrame(columns=["ts_kst","uid","med","dose_mg","weight_kg","note"])

def append_care_log(uid, med, dose_mg, weight_kg=None, note=""):
    import pandas as pd, datetime as _dt
    df = read_care_log()
    ts = _dt.datetime.now(tz=_dt.timezone(_dt.timedelta(hours=9))).strftime("%Y-%m-%d %H:%M:%S")
    row = {"ts_kst": ts, "uid": uid or "guest", "med": med, "dose_mg": dose_mg, "weight_kg": weight_kg, "note": note}
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(_care_log_path(), index=False)
    return row

# ---------- Dose guardrails ----------
def _last_intake_time(df, uid, med):
    try:
        sdf = df[df["uid"]==uid]
        sdf = sdf[sdf["med"]==med]
        if sdf.empty: return None
        last = sdf.iloc[-1]["ts_kst"]
        from datetime import datetime
        try:
            return datetime.strptime(last, "%Y-%m-%d %H:%M:%S")
        except Exception:
            return None
    except Exception:
        return None

def _total_intake_24h(df, uid, med):
    from datetime import datetime, timedelta
    now = datetime.now() + timedelta(hours=9)  # naive KST-ish
    try:
        sdf = df[(df["uid"]==uid) & (df["med"]==med)]
        if sdf.empty: return 0.0
        tot = 0.0
        for _, r in sdf.iterrows():
            try:
                t = datetime.strptime(str(r["ts_kst"]), "%Y-%m-%d %H:%M:%S")
                if (now - t).total_seconds() <= 86400:
                    tot += float(r["dose_mg"] or 0)
            except Exception:
                pass
        return tot
    except Exception:
        return 0.0

def check_guard_apap(uid, dose_mg, weight_kg=None):
    """Cooldown: ≥4h, 24h total ≤ 75 mg/kg (max 4000 mg).
    Returns (ok: bool, message: str, next_allow_ts: str|None, remaining_mg: float|None)
    """
    df = read_care_log()
    # cooldown
    from datetime import datetime, timedelta
    last = _last_intake_time(df, uid, "APAP")
    if last:
        delta = datetime.now() - last
        if delta.total_seconds() < 4*3600:
            next_ts = (last + timedelta(hours=4)).strftime("%Y-%m-%d %H:%M:%S")
            return (False, "APAP는 최소 4시간 간격이 필요합니다.", next_ts, None)
    # total 24h
    total = _total_intake_24h(df, uid, "APAP")
    max_total = None
    if weight_kg:
        try:
            max_total = min(75.0*float(weight_kg), 4000.0)
        except Exception:
            max_total = 4000.0
    else:
        max_total = 4000.0
    if total + float(dose_mg) > max_total:
        return (False, "24시간 총량을 초과합니다.", None, max_total - total)
    return (True, "투약 가능합니다.", None, max_total - (total + float(dose_mg)))

def check_guard_ibu(uid, dose_mg, weight_kg=None):
    """Cooldown: ≥6h, 24h total ≤ 30 mg/kg (max 1200 mg OTC).
    Conservative pediatric cap used.
    """
    df = read_care_log()
    from datetime import datetime, timedelta
    last = _last_intake_time(df, uid, "IBU")
    if last:
        delta = datetime.now() - last
        if delta.total_seconds() < 6*3600:
            next_ts = (last + timedelta(hours=6)).strftime("%Y-%m-%d %H:%M:%S")
            return (False, "IBU는 최소 6시간 간격이 필요합니다.", next_ts, None)
    total = _total_intake_24h(df, uid, "IBU")
    if weight_kg:
        try:
            max_total = min(30.0*float(weight_kg), 1200.0)
        except Exception:
            max_total = 1200.0
    else:
        max_total = 1200.0
    if total + float(dose_mg) > max_total:
        return (False, "24시간 총량을 초과합니다.", None, max_total - total)
    return (True, "투약 가능합니다.", None, max_total - (total + float(dose_mg)))

# ---------- ICS helper ----------
def make_ics(title, start_ts):
    """Create a simple .ics VEVENT starting at start_ts (YYYY-MM-DD HH:MM:SS KST assumed)."""
    import os
    path = "/mnt/data/care_log/next_med.ics"
    try:
        os.makedirs("/mnt/data/care_log", exist_ok=True)
        dtstart = re.sub(r'[-: ]','', start_ts)[:14]  # YYYYMMDDHHMMSS
        content = "BEGIN:VCALENDAR\\nVERSION:2.0\\nPRODID:-//BloodMap//KR//EN\\nBEGIN:VEVENT\\nUID:next-med@bloodmap\\nDTSTART;TZID=Asia/Seoul:%s\\nSUMMARY:%s\\nEND:VEVENT\\nEND:VCALENDAR" % (dtstart, title)
        with open(path,"w",encoding="utf-8") as f:
            f.write(content)
        return path
    except Exception:
        return None
