# HOTFIX: ui_antipyretic_card — schedule persists in session; "초기화" hides table immediately
from __future__ import annotations
from typing import List, Tuple, Optional
from datetime import date, datetime as _dt, timedelta, time
import pandas as pd

import streamlit as st  # assumes Streamlit runtime
from peds_dose import acetaminophen_ml, ibuprofen_ml

def _parse_time_opt(label: str, key: str) -> Optional[_dt]:
    t: Optional[time] = st.time_input(label, value=None, key=key)  # type: ignore[arg-type]
    if t is None:
        return None
    today = date.today()
    return _dt.combine(today, t)

def _ceil_to_next(dt: _dt, minutes: int) -> _dt:
    mod = (dt.minute % minutes)
    base = dt.replace(second=0, microsecond=0)
    if mod == 0:
        return base
    return base + timedelta(minutes=(minutes - mod))

def _gen_schedule(now: _dt, apap_ml: Optional[float], ibu_ml: Optional[float],
                  last_apap: Optional[_dt], last_ibu: Optional[_dt],
                  apap_int_h: int = 6, ibu_int_h: int = 8, hours: int = 24) -> List[Tuple[str, _dt, float]]:
    out: List[Tuple[str, _dt, float]] = []
    horizon = now + timedelta(hours=hours)
    if apap_ml and apap_ml > 0:
        t = _ceil_to_next((last_apap or now), apap_int_h*60)
        while t <= horizon:
            out.append(("아세트아미노펜", t, float(apap_ml)))
            t += timedelta(hours=apap_int_h)
    if ibu_ml and ibu_ml > 0:
        t = _ceil_to_next((last_ibu or now), ibu_int_h*60)
        while t <= horizon:
            out.append(("이부프로펜", t, float(ibu_ml)))
            t += timedelta(hours=ibu_int_h)
    out.sort(key=lambda x: x[1])
    return out

def _fmt_time(dt: _dt) -> str:
    return dt.strftime("%H:%M")

def ui_antipyretic_card(age_m: int, weight_kg: Optional[float], temp_c: float, key: str):
    st.markdown("#### 🕒 해열제 24시간 시간표")
    apap_ml, _w = acetaminophen_ml(age_m, weight_kg or None)
    ibu_ml,  _w = ibuprofen_ml(age_m, weight_kg or None)

    c1,c2,c3 = st.columns(3)
    with c1: st.metric("1회분 — 아세트아미노펜", f"{apap_ml} ml"); st.caption("간격 4–6h, 최대 4회/일")
    with c2: st.metric("1회분 — 이부프로펜", f"{ibu_ml} ml"); st.caption("간격 6–8h")
    with c3: st.metric("현재 체온", f"{temp_c or 0:.1f} ℃")

    now = _dt.now()
    c4,c5 = st.columns(2)
    with c4:
        last_apap = _parse_time_opt("마지막 아세트아미노펜 복용시각 (선택)", key=f"{key}_t_apap")
        apap_now = st.checkbox("아세트아미노펜 이미 먹었어요", value=False, key=f"{key}_apap_now")
        if apap_now: last_apap = now
    with c5:
        last_ibu = _parse_time_opt("마지막 이부프로펜 복용시각 (선택)", key=f"{key}_t_ibu")
        ibu_now = st.checkbox("이부프로펜 이미 먹었어요", value=False, key=f"{key}_ibu_now")
        if ibu_now: last_ibu = now

    # ----- STATE: persist schedule and render from session only -----
    stash = st.session_state.setdefault("antipy_sched", {})
    current = stash.get(key, [])

    colA, colB, colC = st.columns(3)
    if colA.button("스케줄 생성/복사", key=f"{key}_make"):
        sched = _gen_schedule(now, apap_ml, ibu_ml, last_apap, last_ibu)
        stash[key] = sched
        current = sched
        # Show copyable text
        lines = [f"{_fmt_time(t)} {name} {vol}ml" for (name, t, vol) in current]
        st.code("\n".join(lines), language="")
        st.success("스케줄 생성 완료")
    if colB.button("스케줄 저장", key=f"{key}_save"):
        if not current:
            st.info("먼저 스케줄을 생성하세요.")
        else:
            stash[key] = current
            st.success("스케줄 저장 완료")
    if colC.button("초기화", key=f"{key}_clear"):
        stash.pop(key, None)
        current = []
        st.info("스케줄을 비웠습니다.")

    # ----- RENDER from state -----
    if current:
        st.caption("오늘 남은 스케줄")
        table = [{"시간": _fmt_time(t), "약": name, "용량(ml)": vol} for (name, t, vol) in current if t.date()==date.today()]
        df = pd.DataFrame(table).set_index("시간")
        st.dataframe(df, use_container_width=True, height=200)
    else:
        st.caption("현재 저장된 스케줄이 없습니다.")
