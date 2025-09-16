# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import List, Dict, Tuple, Optional
import json, hashlib
from datetime import datetime, timedelta, date, time
import pandas as pd

try:
    import streamlit as st  # type: ignore
except Exception:
    class _Dummy:
        def __getattr__(self, k): return lambda *a, **k: None
    st = _Dummy()  # type: ignore

TONES = ["기본","더-친절","초-간결"]

def ui_sidebar_settings() -> str:
    with st.sidebar:
        st.markdown("### ⚙️ 설정")
        tone = st.radio("‘짧은 해석’ 톤", TONES, index=0, horizontal=True)
        st.session_state["tone_preset"] = tone
        st.caption("프리셋은 리스트/보고서 문구에 즉시 반영됩니다.")
    return tone

# --- Tone helpers ---

def toneize_line(line: str, tone: Optional[str] = None) -> str:
    tone = tone or st.session_state.get("tone_preset") or "기본"
    s = str(line or "").strip()
    if tone == "초-간결":
        if "→" in s:
            s = s.split("→", 1)[0].strip()
        out = []
        skip = 0
        for ch in s:
            if ch == "(":
                skip += 1; continue
            if ch == ")":
                skip = max(0, skip-1); continue
            if skip == 0:
                out.append(ch)
        s = "".join(out).strip()
    elif tone == "더-친절":
        if "권고" in s or "필요" in s or "주의" in s:
            s += " 부탁드려요."
        elif "가능" in s or "권장" in s:
            s += " 도움이 되실 거예요."
        else:
            s += " 괜찮으시면 그렇게 해주세요."
    return s

def toneize_lines(lines: List[str], tone: Optional[str] = None) -> List[str]:
    return [toneize_line(L, tone) for L in (lines or [])]

# --- Antipyretic schedule ---
from peds_dose import acetaminophen_ml, ibuprofen_ml
from datetime import datetime as _dt

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

def ui_antipyretic_card(age_m: int, weight_kg: Optional[float], temp_c: float, key: str) -> List[Tuple[str, _dt, float]]:
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

    # Guards
    guard_msgs: List[str] = []
    if (age_m or 0) < 6 and ibu_ml and ibu_ml > 0:
        guard_msgs.append("⚠️ 생후 6개월 미만 이부프로펜은 **의사 지시가 없는 한 권장되지 않습니다**.")
    if weight_kg and weight_kg <= 0:
        guard_msgs.append("⚠️ 체중을 입력하면 더 정확한 용량 계산이 가능합니다.")
    if guard_msgs:
        st.warning("\n".join(guard_msgs))

    sched = _gen_schedule(now, apap_ml, ibu_ml, last_apap, last_ibu)
    if sched:
        st.caption("오늘 남은 스케줄")
        table = [{"시간": _fmt_time(t), "약": name, "용량(ml)": vol} for (name, t, vol) in sched if t.date()==date.today()]
        st.table(pd.DataFrame(table))
    btns = st.columns(3)
    if btns[0].button("스케줄 생성/복사", key=f"{key}_copy_sched"):
        lines = [f"{_fmt_time(t)} {name} {vol}ml" for (name, t, vol) in sched]
        st.code("\n".join(lines), language="")
    if btns[1].button("스케줄 저장", key=f"{key}_save_sched"):
        st.session_state.setdefault("antipy_sched", {})
        st.session_state["antipy_sched"][key] = sched
        st.success("스케줄 저장 완료")
    if btns[2].button("초기화", key=f"{key}_clear_sched"):
        st.session_state.setdefault("antipy_sched", {})
        st.session_state["antipy_sched"].pop(key, None)
        st.info("스케줄을 비웠습니다.")
    return sched

# --- Symptom diary ---

def _hash_key(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:12]

def ui_symptom_diary_card(key: str) -> pd.DataFrame:
    st.markdown("#### 📈 증상 일지(미니 차트)")
    st.session_state.setdefault("diary", {})
    df_prev = st.session_state["diary"].get(key, pd.DataFrame(columns=["Date","Temp","Diarrhea","Vomit"]))

    c1,c2,c3,c4 = st.columns(4)
    with c1: when = st.date_input("날짜", value=date.today(), key=f"{key}_d_when")
    with c2: temp = st.number_input("체온(℃)", min_value=0.0, step=0.1, key=f"{key}_d_temp")
    with c3: diar = st.number_input("설사(회/일)", min_value=0, step=1, key=f"{key}_d_diar")
    with c4: vomi = st.number_input("구토(회/일)", min_value=0, step=1, key=f"{key}_d_vomi")

    cbtn1, cbtn2, cbtn3 = st.columns(3)
    if cbtn1.button("오늘 기록 추가", key=f"{key}_d_add"):
        row = {"Date": when.strftime("%Y-%m-%d"), "Temp": temp, "Diarrhea": int(diar), "Vomit": int(vomi)}
        df = pd.concat([df_prev, pd.DataFrame([row])], ignore_index=True).drop_duplicates(subset=["Date"], keep="last").sort_values("Date")
        st.session_state["diary"][key] = df
        st.success("추가/업데이트 완료")
    elif cbtn2.button("JSON 내보내기", key=f"{key}_d_export"):
        jj = df_prev.to_json(orient="records", force_ascii=False)
        blob = {
            "owner": key,
            "owner_hash": _hash_key(key),
            "data": jj
        }
        st.download_button("⬇️ diary.json", data=json.dumps(blob, ensure_ascii=False, indent=2), file_name=f"diary_{_hash_key(key)}.json")
    elif cbtn3.button("JSON 가져오기", key=f"{key}_d_import"):
        up = st.file_uploader("diary.json 업로드", type=["json"], key=f"{key}_d_upl")
        if up is not None:
            try:
                payload = json.loads(up.getvalue().decode("utf-8"))
                jj = payload.get("data") or "[]"
                df = pd.read_json(jj)
                st.session_state["diary"][key] = df
                st.success("불러오기 완료")
            except Exception as e:
                st.error(f"가져오기 실패: {e}")

    df = st.session_state["diary"].get(key, pd.DataFrame(columns=["Date","Temp","Diarrhea","Vomit"]))
    if not df.empty:
        st.line_chart(df.set_index("Date")[ ["Temp"] ], use_container_width=True)
        st.bar_chart(df.set_index("Date")[ ["Diarrhea","Vomit"] ], use_container_width=True)
        st.dataframe(df, use_container_width=True, height=220)
    else:
        st.caption("아직 기록이 없습니다.")
    return df

# --- Interactions box (암 모드) ---
from interactions import compute_interactions

def render_interactions_box(user_drugs: List[str], labs: Dict[str, float], other_text: str | None = None) -> List[str]:
    alerts = compute_interactions(user_drugs, labs, other_text or "")
    if alerts:
        worst = "🚨" if any(a[0].startswith("🚨") for a in alerts) else "⚠️"
        lines = [f"{lvl} {msg}" for (lvl, msg) in alerts]
        if worst == "🚨":
            st.error("\n".join(lines))
        else:
            st.warning("\n".join(lines))
        return lines
    return []

# --- Report blocks ---
from datetime import datetime as _dt

def md_block_antipy_schedule(sched: List[Tuple[str, _dt, float]]) -> List[str]:
    if not sched: return []
    lines = ["## 🕒 해열제 시간표"]
    today = date.today()
    for name, t, vol in sched:
        if t.date() == today:
            lines.append(f"- {t.strftime('%H:%M')} {name} {vol} mL")
    return lines

def md_block_diary(df: pd.DataFrame) -> List[str]:
    if df is None or df.empty: return []
    last_row = df.tail(1).to_dict("records")[0]
    lines = ["## 📈 증상 일지(오늘/최근7일)"]
    lines.append(f"- 오늘: 체온 {last_row.get('Temp','')}℃ / 설사 {last_row.get('Diarrhea','')}회 / 구토 {last_row.get('Vomit','')}회")
    try:
        df7 = df.tail(7)
        avg_t = df7["Temp"].astype(float).mean()
        avg_d = df7["Diarrhea"].astype(float).mean()
        avg_v = df7["Vomit"].astype(float).mean()
        lines.append(f"- 최근7일 평균: 체온 {avg_t:.1f}℃ / 설사 {avg_d:.1f}회 / 구토 {avg_v:.1f}회")
    except Exception:
        pass
    return lines
