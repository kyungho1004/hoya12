
import streamlit as st
import pandas as pd
import pathlib, time
from typing import Optional

# ---------- Page Meta ----------
st.set_page_config(page_title="해열제·설사 스케줄러", layout="wide")
st.title("⏱️ 해열제·설사 스케줄러")

# Debug (helps verify deployment; safe to keep)
p = pathlib.Path(__file__)
st.sidebar.markdown("### 🔧 디버그")
st.sidebar.write("FILE:", p.as_posix())
st.sidebar.write("MTime:", time.ctime(p.stat().st_mtime))

# ---------- Utils ----------
def _tz_now() -> pd.Timestamp:
    try:
        return pd.Timestamp.now(tz="Asia/Seoul")
    except Exception:
        return pd.Timestamp.utcnow().tz_localize("UTC").tz_convert("Asia/Seoul")

def _datetime_picker(label: str, key_prefix: str, default_ts: Optional[pd.Timestamp]) -> pd.Timestamp:
    "Compat picker using date_input + time_input; returns tz-aware Asia/Seoul timestamp"
    import datetime as _dt
    if default_ts is None:
        default_ts = _tz_now()
    local = default_ts.tz_convert("Asia/Seoul")
    c1, c2 = st.columns([1, 1])
    with c1:
        d = st.date_input(label + " (날짜)", value=local.date(), key=key_prefix + "_date")
    with c2:
        t = st.time_input(label + " (시각)", value=_dt.time(local.hour, local.minute), key=key_prefix + "_time")
    return pd.Timestamp.combine(d, t).tz_localize("Asia/Seoul")

def _init_event_log():
    st.session_state.setdefault("event_log_schedpage", pd.DataFrame(columns=["DT","유형","용량(ml)","체온(℃)","메모"]))

def _append_event(kind: str, when, dose=None, temp=None, note: str=""):
    df = st.session_state["event_log_schedpage"]
    row = {"DT": pd.to_datetime(when), "유형": str(kind), "용량(ml)": dose, "체온(℃)": temp, "메모": note}
    st.session_state["event_log_schedpage"] = pd.concat([df, pd.DataFrame([row])], ignore_index=True).sort_values("DT")

def _last_time_of(kind: str):
    df = st.session_state["event_log_schedpage"]
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
    "동일계열 최소간격: 아세트아미노펜 4h, 이부프로펜계열 6h. 교차 2h 권장."
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

def _peds_dose_ml(age_months: int|None, weight_kg: float|None):
    "소아 1회 용량(ml) 자동 계산: peds_dose_override → peds_dose → 실패 시 (None, None)"
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

# ---------- UI ----------
_init_event_log()
st.caption("아세트아미노펜/이부프로펜계열 기록 · 한국시간 · 동일계열 4/6h 간격 · 교차 2h 안내")

who = st.radio("대상", ["소아","성인"], horizontal=True, key="who_sched_page")
apap_ml_auto = None
ibu_ml_auto  = None

if who == "소아":
    c1, c2 = st.columns(2)
    with c1:
        age_m = st.number_input("나이(개월)", min_value=0, step=1, value=0, key="age_m_sched_page")
    with c2:
        weight = st.number_input("체중(kg)", min_value=0.0, step=0.1, value=0.0, key="weight_sched_page")
    apap_ml_auto, ibu_ml_auto = _peds_dose_ml(age_m, weight)
    if apap_ml_auto is not None and ibu_ml_auto is not None:
        st.caption(f"소아 1회 기준: 아세트아미노펜 {apap_ml_auto} ml · 이부프로펜계열 {ibu_ml_auto} ml")
    else:
        st.caption("소아 용량 계산 모듈을 찾을 수 없어 표시만 진행합니다. (버튼 기록은 가능)")
else:
    w_ad = st.number_input("성인 체중(kg)", min_value=0.0, step=0.5, value=0.0, key="weight_adult_sched_page")
    if w_ad > 0:
        ap_min=int(round(w_ad*10)); ap_max=int(round(w_ad*15))
        ib_min=int(round(w_ad*5));  ib_max=int(round(w_ad*10))
        st.caption(f"성인 정보용: 아세트아미노펜 {ap_min}–{ap_max} mg (4–6h), 이부프로펜계열 {ib_min}–{ib_max} mg (6–8h)")

b1, b2, b3 = st.columns(3)
with b1:
    if st.button("지금 복용: 아세트아미노펜", use_container_width=True, key="btn_apap_now_sched_page"):
        when = _tz_now()
        ok, msg = _check_dose_conflict("해열제(아세트아미노펜)", when)
        if not ok: st.error(msg)
        else:
            _append_event("해열제(아세트아미노펜)", when, dose=apap_ml_auto, temp=None, note="1회 복용")
            st.success("아세트아미노펜 복용 시간이 기록되었습니다.")
with b2:
    if st.button("지금 복용: 이부프로펜", use_container_width=True, key="btn_ibu_now_sched_page"):
        when = _tz_now()
        ok, msg = _check_dose_conflict("해열제(이부프로펜계열)", when)
        if not ok: st.error(msg)
        else:
            _append_event("해열제(이부프로펜계열)", when, dose=ibu_ml_auto, temp=None, note="1회 복용")
            st.success("이부프로펜계열 복용 시간이 기록되었습니다.")
with b3:
    if st.button("지금: 설사 1회", use_container_width=True, key="btn_diar_now_sched_page"):
        _append_event("설사", _tz_now(), dose=1, temp=None, note="1회")
        st.warning("설사 1회가 기록되었습니다. ORS 보충을 권장합니다.")

with st.expander("수동 입력(시간/용량/체온/메모)", expanded=False):
    dt_in = _datetime_picker("시간(한국시간)", "fd_dt_sched_page", _tz_now())
    kind = st.selectbox("유형", ["해열제(아세트아미노펜)","해열제(이부프로펜계열)","설사"], key="fd_kind_sched_page")
    c1, c2 = st.columns(2)
    with c1:
        dose = st.number_input("용량(ml, 선택)", min_value=0.0, step=0.5, value=0.0, key="fd_dose_sched_page")
        dose = None if dose == 0.0 else dose
    with c2:
        temp = st.number_input("체온(℃, 선택)", min_value=0.0, step=0.1, value=0.0, key="fd_temp_sched_page")
        temp = None if temp == 0.0 else temp
    note = st.text_input("메모(선택)", value="", key="fd_note_sched_page")
    if st.button("기록 추가", key="fd_add_sched_page"):
        if kind == "설사":
            _append_event(kind, dt_in, dose=1, temp=temp, note=note or "1회")
            st.success("기록이 추가되었습니다.")
        else:
            ok, msg = _check_dose_conflict(kind, dt_in)
            if not ok: st.error(msg)
            else:
                _append_event(kind, dt_in, dose=dose, temp=temp, note=note)
                st.success("기록이 추가되었습니다.")

df = st.session_state["event_log_schedpage"]
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
        st.write(f"가능: **{ib_lo.tz_convert('Asia/Seoul').strftime('%H:%M')} ~ {ib_hi.tz_convert('Asia/Seoul').strftime('%H:%M')}**")  # typo fixed next

# Fix a typo in ib_hi tz convert
# Re-render safely
