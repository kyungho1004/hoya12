
import streamlit as st
import pandas as pd
import pathlib, time

# ========= App Meta =========
VERSION = "BM-SCHED-2025-09-18-FINAL1"
st.set_page_config(page_title="BloodMap — 해열제·설사 스케줄러", layout="wide")
st.title("BloodMap — 피수치가이드")

# Sidebar Debug (for deployment verification)
p = pathlib.Path(__file__)
st.sidebar.markdown("### 🔧 디버그")
st.sidebar.write("FILE:", p.as_posix())
st.sidebar.write("MTime:", time.ctime(p.stat().st_mtime))
st.sidebar.write("Version:", VERSION)

# ========= Helpers =========
def _tz_now():
    try:
        return pd.Timestamp.now(tz="Asia/Seoul")
    except Exception:
        return pd.Timestamp.utcnow().tz_localize("UTC").tz_convert("Asia/Seoul")

def nickname_pin():
    st.markdown("#### 👤 사용자 식별 (별명 + PIN)")
    c1, c2 = st.columns([2,1])
    with c1:
        nick = st.text_input("별명", key="nick", placeholder="예: 민수엄마")
    with c2:
        pin = st.text_input("PIN (4자리)", key="pin", type="password", max_chars=4, placeholder="1234")
    key = f"{nick.strip()}#{pin.strip()}" if nick and pin and len(pin.strip())==4 else "guest"
    st.session_state["key"] = key
    return nick, pin, key

def _init_event_log():
    st.session_state.setdefault("event_log", {})
    key0 = st.session_state.get("key","guest")
    if key0 not in st.session_state["event_log"]:
        st.session_state["event_log"][key0] = pd.DataFrame(columns=["DT","유형","용량(ml)","체온(℃)","메모"])
    return key0

def _append_event(kind: str, when, dose=None, temp=None, note: str=""):
    key0 = _init_event_log()
    df = st.session_state["event_log"][key0]
    row = {"DT": pd.to_datetime(when), "유형": str(kind), "용량(ml)": dose, "체온(℃)": temp, "메모": note}
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True).sort_values("DT")
    st.session_state["event_log"][key0] = df

def _last_time_of(kind: str):
    key0 = _init_event_log()
    df = st.session_state["event_log"][key0]
    if df.empty: return None
    dff = df[df["유형"]==kind]
    if dff.empty: return None
    return pd.to_datetime(dff["DT"].iloc[-1])

def _next_window(last_dt, lo_h: float, hi_h: float):
    if last_dt is None: return None, None
    lo = last_dt + pd.to_timedelta(lo_h, unit="h")
    hi = last_dt + pd.to_timedelta(hi_h, unit="h")
    return lo, hi

def _cross_window(last_dt, gap_h: float = 2.0):
    if last_dt is None: return None
    return last_dt + pd.to_timedelta(gap_h, unit='h')

def _check_dose_conflict(kind: str, when):
    """동일계열 최소간격: 아세트아미노펜 4h, 이부프로펜계열 6h. 교차 2h 권장."""
    fam = "APAP" if "아세트아미노펜" in kind else ("IBU" if "이부프로펜" in kind else None)
    if fam is None:
        return True, ""
    last_same = _last_time_of("해열제(아세트아미노펜)") if fam=="APAP" else _last_time_of("해열제(이부프로펜계열)")
    need_h = 4 if fam=="APAP" else 6
    if last_same is not None and when < last_same + pd.to_timedelta(need_h, unit="h"):
        nxt = (last_same + pd.to_timedelta(need_h, unit="h")).tz_convert("Asia/Seoul").strftime("%H:%M")
        return False, f"{'아세트아미노펜' if fam=='APAP' else '이부프로펜계열'} 최소 간격 {need_h}시간 미만입니다. 다음 가능: {nxt}"
    other = _last_time_of("해열제(이부프로펜계열)") if fam=="APAP" else _last_time_of("해열제(아세트아미노펜)")
    if other is not None and when < other + pd.to_timedelta(2, unit="h"):
        return True, "⚠️ 직전 다른 계열과 2시간 이내 병용 가능성. 권장 교차 간격은 2시간입니다."
    return True, ""

# ========= Pediatric dose helpers =========
def _peds_dose_ml(age_months: int|None, weight_kg: float|None):
    """Try to compute pediatric 1회 용량(ml) using local modules if available.
    Returns (apap_ml, ibu_ml) or (None, None) if unavailable.
    """
    try:
        try:
            from peds_dose_override import acetaminophen_ml as _ap, ibuprofen_ml as _ib  # type: ignore
        except Exception:
            from peds_dose import acetaminophen_ml as _ap, ibuprofen_ml as _ib  # type: ignore
        ap_ml,_ = _ap(age_months or 0, weight_kg or None)
        ib_ml,_ = _ib(age_months or 0, weight_kg or None)
        return ap_ml, ib_ml
    except Exception:
        return None, None

# ========= UI: Always-on Scheduler =========
nick, pin, key = nickname_pin()
st.divider()



# --- Streamlit <=1.30 호환용 datetime 입력 ---
def _datetime_picker(label: str, key_prefix: str, default_ts):
    # default_ts: tz-aware pandas.Timestamp (Asia/Seoul)
    import datetime as _dt
    import pandas as _pd
    if default_ts is None:
        default_ts = _tz_now()
    local = default_ts.tz_convert("Asia/Seoul")
    dcol = st.columns([1,1])
    with dcol[0]:
        d = st.date_input(label + " (날짜)", value=local.date(), key=key_prefix+"_date")
    with dcol[1]:
        t = st.time_input(label + " (시각)", value=_dt.time(local.hour, local.minute), key=key_prefix+"_time")
    combined = _pd.Timestamp.combine(d, t).tz_localize("Asia/Seoul")
    return combined

with st.expander("⏱️ 해열제·설사 스케줄러 (소아/성인)", expanded=True):
    st.caption("아세트아미노펜/이부프로펜계열 기록 · 한국시간 · 동일계열 4/6h 간격 · 교차 2h 안내")

    who = st.radio("대상", ["소아","성인"], horizontal=True, key="who_sched")
    apap_ml_auto = None
    ibu_ml_auto  = None

    if who == "소아":
        c1, c2 = st.columns(2)
        with c1:
            age_m = st.number_input("나이(개월)", min_value=0, step=1, value=0, key="age_m")
        with c2:
            weight = st.number_input("체중(kg)", min_value=0.0, step=0.1, value=0.0, key="weight")
        apap_ml_auto, ibu_ml_auto = _peds_dose_ml(age_m, weight)
        if apap_ml_auto is not None and ibu_ml_auto is not None:
            st.caption(f"소아 1회 기준: 아세트아미노펜 {apap_ml_auto} ml · 이부프로펜계열 {ibu_ml_auto} ml")
        else:
            st.caption("소아 용량 계산 모듈을 찾을 수 없어 표시만 진행합니다. (버튼 기록은 가능)")
    else:
        w_ad = st.number_input("성인 체중(kg)", min_value=0.0, step=0.5, value=0.0, key="weight_adult")
        if w_ad > 0:
            ap_min=int(round(w_ad*10)); ap_max=int(round(w_ad*15))
            ib_min=int(round(w_ad*5));  ib_max=int(round(w_ad*10))
            st.caption(f"성인 정보용: 아세트아미노펜 {ap_min}–{ap_max} mg (4–6h), 이부프로펜계열 {ib_min}–{ib_max} mg (6–8h)")

    # Quick buttons
    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button("지금 복용: 아세트아미노펜", use_container_width=True):
            when = _tz_now()
            ok, msg = _check_dose_conflict("해열제(아세트아미노펜)", when)
            if not ok: st.error(msg)
            else:
                _append_event("해열제(아세트아미노펜)", when, dose=apap_ml_auto, temp=None, note="1회 복용")
                st.success("아세트아미노펜 복용 시간이 기록되었습니다.")
    with b2:
        if st.button("지금 복용: 이부프로펜", use_container_width=True):
            when = _tz_now()
            ok, msg = _check_dose_conflict("해열제(이부프로펜계열)", when)
            if not ok: st.error(msg)
            else:
                _append_event("해열제(이부프로펜계열)", when, dose=ibu_ml_auto, temp=None, note="1회 복용")
                st.success("이부프로펜계열 복용 시간이 기록되었습니다.")
    with b3:
        if st.button("지금: 설사 1회", use_container_width=True):
            _append_event("설사", _tz_now(), dose=1, temp=None, note="1회")
            st.warning("설사 1회가 기록되었습니다. ORS 보충을 권장합니다.")

    with st.expander("수동 입력(시간/용량/체온/메모)", expanded=False):
        dcol = st.columns(4)
        with dcol[0]:
            dt_in = _datetime_picker("시간(한국시간)", "fd_dt", _tz_now())
        with dcol[1]:
            kind = st.selectbox("유형", ["해열제(아세트아미노펜)","해열제(이부프로펜계열)","설사"], key="fd_kind")
        with dcol[2]:
            dose = st.number_input("용량(ml, 선택)", min_value=0.0, step=0.5, value=0.0, key="fd_dose")
            dose = None if dose == 0.0 else dose
        with dcol[3]:
            temp = st.number_input("체온(℃, 선택)", min_value=0.0, step=0.1, value=0.0, key="fd_temp")
            temp = None if temp == 0.0 else temp
        note = st.text_input("메모(선택)", value="", key="fd_note")
        if st.button("기록 추가", key="fd_add"):
            if kind == "설사":
                _append_event(kind, dt_in, dose=1, temp=temp, note=note or "1회")
                st.success("기록이 추가되었습니다.")
            else:
                ok, msg = _check_dose_conflict(kind, dt_in)
                if not ok: st.error(msg)
                else:
                    _append_event(kind, dt_in, dose=dose, temp=temp, note=note)
                    st.success("기록이 추가되었습니다.")

    # Summary / Next windows
    key0 = _init_event_log()
    df = st.session_state["event_log"][key0]

    ap_last = _last_time_of("해열제(아세트아미노펜)")
    ib_last = _last_time_of("해열제(이부프로펜계열)")
    ap_lo, ap_hi = _next_window(ap_last, 4, 6) if ap_last is not None else (None, None)
    ib_lo, ib_hi = _next_window(ib_last, 6, 8) if ib_last is not None else (None, None)

    g1, g2 = st.columns(2)
    with g1:
        st.markdown("**아세트아미노펜 다음 복용 가능 시간**")
        if ap_last is None:
            st.caption("기록 없음")
        else:
            st.metric("마지막 복용", ap_last.tz_convert("Asia/Seoul").strftime("%Y-%m-%d %H:%M"))
            st.write(f"가능: **{ap_lo.tz_convert('Asia/Seoul').strftime('%H:%M')} ~ {ap_hi.tz_convert('Asia/Seoul').strftime('%H:%M')}**")
    with g2:
        st.markdown("**이부프로펜계열 다음 복용 가능 시간**")
        if ib_last is None:
            st.caption("기록 없음")
        else:
            st.metric("마지막 복용", ib_last.tz_convert("Asia/Seoul").strftime("%Y-%m-%d %H:%M"))
            st.write(f"가능: **{ib_lo.tz_convert('Asia/Seoul').strftime('%H:%M')} ~ {ib_hi.tz_convert('Asia/Seoul').strftime('%H:%M')}**")

    cxa, cxb = st.columns(2)
    with cxa:
        st.markdown("**이부프로펜 → 아세트아미노펜 교차(2h)**")
        cross_ap = _cross_window(ib_last, 2.0) if ib_last is not None else None
        st.caption("기록 없음" if cross_ap is None else f"다음 가능: **{cross_ap.tz_convert('Asia/Seoul').strftime('%H:%M')}**")
    with cxb:
        st.markdown("**아세트아미노펜 → 이부프로펜 교차(2h)**")
        cross_ib = _cross_window(ap_last, 2.0) if ap_last is not None else None
        st.caption("기록 없음" if cross_ib is None else f"다음 가능: **{cross_ib.tz_convert('Asia/Seoul').strftime('%H:%M')}**")

    if not df.empty:
        dfv = df.copy()
        dfv["DT"] = pd.to_datetime(dfv["DT"]).dt.tz_localize("UTC").dt.tz_convert("Asia/Seoul")
        st.dataframe(dfv.sort_values("DT", ascending=False), use_container_width=True, height=240)
        csv = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button("⬇️ CSV 내보내기", data=csv, file_name="fever_diarrhea_log.csv")
    else:
        st.caption("기록이 없습니다. 상단 버튼으로 '지금' 기록을 남겨보세요.")

st.divider()

# ========= Cancer Helper (Optional) =========
with st.expander("암환자 해열제 자동 계산 (소아/성인)", expanded=False):
    who_c = st.radio("대상", ["소아","성인"], horizontal=True, key="cx_who")
    if who_c == "소아":
        try:
            try:
                from peds_dose_override import acetaminophen_ml, ibuprofen_ml  # type: ignore
            except Exception:
                from peds_dose import acetaminophen_ml, ibuprofen_ml  # type: ignore
            c1,c2 = st.columns(2)
            with c1: age_m_c = st.number_input("나이(개월)", min_value=0, step=1, value=0, key="cx_age_m")
            with c2: weight_c = st.number_input("체중(kg)", min_value=0.0, step=0.1, value=0.0, key="cx_weight")
            ap_ml,_ = acetaminophen_ml(age_m_c, weight_c or None)
            ib_ml,_ = ibuprofen_ml(age_m_c, weight_c or None)
            st.write(f"소아 1회: 아세트아미노펜 **{ap_ml} ml**, 이부프로펜계열 **{ib_ml} ml**")
        except Exception as _e:
            st.caption(f"소아 용량 계산 오류: {_e}")
    else:
        w_ad = st.number_input("성인 체중(kg)", min_value=0.0, step=0.5, value=0.0, key="cx_weight_ad")
        if w_ad>0:
            ap_min=int(round(w_ad*10)); ap_max=int(round(w_ad*15))
            ib_min=int(round(w_ad*5));  ib_max=int(round(w_ad*10))
            st.write(f"성인 정보용: 아세트아미노펜 {ap_min}–{ap_max} mg (4–6h), 이부프로펜계열 {ib_min}–{ib_max} mg (6–8h)")

# ========= Footer Tips =========
st.sidebar.markdown("### ⭐ 즐겨찾기")
st.sidebar.caption("PC: Ctrl+D · 모바일: 공유 ▶︎ 홈 화면에 추가")
