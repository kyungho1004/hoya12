
# -*- coding: utf-8 -*-
"""
onco_antipyretic_log
- Antipyretic/Care log UI + 24h renderer (한국어 라벨 + 세부유형 + 개인별 파일명)
- Drop‑in for app_onco_with_log.py
"""
from __future__ import annotations
import os, json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List
import streamlit as st

KST = timezone(timedelta(hours=9))

# --------------- basic data paths (safe, with /tmp fallback) ---------------
def _writable_dir(d: str) -> bool:
    try:
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, ".probe")
        with open(p, "w", encoding="utf-8") as f: f.write("ok")
        os.remove(p); return True
    except Exception:
        return False

def _data_root() -> str:
    cand = []
    env = os.getenv("BLOODMAP_DATA_ROOT", "").strip()
    if env: cand.append(env)
    cand.append("/mnt/data")
    cand.append(os.path.join(os.getenv("TMPDIR") or "/tmp", "bloodmap_data"))
    for d in cand:
        if _writable_dir(d): return d
    d = os.path.join(os.getenv("TMPDIR") or "/tmp", "bloodmap_data")
    os.makedirs(d, exist_ok=True)
    return d

def _data_path(*parts: str) -> str:
    return os.path.join(_data_root(), *parts)

# --------------- storage helpers ---------------
def _carelog_path(uid: str) -> str:
    return _data_path("care_log", f"{uid}.json")

def load_carelog(uid: str) -> List[Dict[str, Any]]:
    try:
        with open(_carelog_path(uid), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_carelog(uid: str, entries: List[Dict[str, Any]]) -> None:
    p = _carelog_path(uid)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    os.replace(tmp, p)

# --------------- utilities ---------------
def now_kst() -> datetime:
    return datetime.now(KST)

def _qr_png_bytes(text: str) -> bytes:
    import qrcode
    from io import BytesIO
    img = qrcode.make(text)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def build_ics_for_next_doses(apap_next: datetime|None, ibu_next: datetime|None) -> str:
    # Minimal ICS: 2 events if provided
    def _evt(dt: datetime, title: str) -> str:
        stamp = dt.astimezone(KST).strftime("%Y%m%dT%H%M%S")
        return f"BEGIN:VEVENT\nDTSTART;TZID=Asia/Seoul:{stamp}\nSUMMARY:{title}\nEND:VEVENT"
    events = []
    if apap_next: events.append(_evt(apap_next, "APAP 다음 복용"))
    if ibu_next:  events.append(_evt(ibu_next,  "IBU 다음 복용"))
    return "BEGIN:VCALENDAR\n" + "\n".join(events) + "\nEND:VCALENDAR"

def total_24h_mg(entries: List[Dict[str, Any]], kind: str, now: datetime|None=None) -> float:
    now = now or now_kst()
    s = 0.0
    for e in entries or []:
        if e.get("type") != kind: continue
        try:
            ts = datetime.fromisoformat(e.get("ts"))
        except Exception:
            continue
        if (now - ts).total_seconds() <= 24*3600:
            try: s += float(e.get("mg") or 0)
            except Exception: pass
    return s

def _ko_label_event(e: Dict[str, Any]) -> str:
    t = e.get("type"); ts = e.get("ts")
    if t == "fever":
        return f"- {ts} · 발열 {e.get('temp')}℃"
    if t in ("apap","ibu"):
        return f"- {ts} · {t.upper()} {e.get('mg')} mg"
    if t in ("vomit","diarrhea"):
        kind = e.get("kind")
        ko = "구토" if t=="vomit" else "설사"
        return f"- {ts} · {ko}" + (f" ({kind})" if kind else "")
    ko_map = {"vomit":"구토","diarrhea":"설사"}
    return f"- {ts} · {ko_map.get(t, t)}"

# --------------- UI: add‑buttons + 24h renderer ---------------
def render_onco_antipyretic_log(nick: str, uid: str, apap_next=None, ibu_next=None) -> None:
    st.markdown("### 3) 케어로그 & 해열제 (개인별)")
    st.session_state.setdefault("care_log", {})
    care = st.session_state["care_log"].get(uid) or load_carelog(uid)

    # input row
    c1,c2,c3,c4,c5 = st.columns(5)
    with c1:
        if st.button("발열 기록 +", key=f"btn_add_fever_{uid}"):
            t = st.number_input("현재 체온(℃)", min_value=35.0, step=0.1, value=38.0, key=f"temp_add_{uid}")
            care.append({"type":"fever","temp":t,"ts": now_kst().isoformat()})
            save_carelog(uid, care); st.success("발열 기록됨.")
    with c2:
        vomit_kind = st.selectbox("구토 유형", ["흰","노랑","초록(담즙)","기타"], index=1, key=f"vomit_kind_{uid}")
        if st.button("구토 +", key=f"btn_add_vomit_{uid}"):
            care.append({"type":"vomit","kind":vomit_kind,"ts": now_kst().isoformat()})
            save_carelog(uid, care); st.success("구토 기록됨.")
    with c3:
        diarrhea_kind = st.selectbox("설사 유형", ["노랑","진한노랑","거품","녹색","녹색혈변","혈변","검은색","기타"], index=0, key=f"diarrhea_kind_{uid}")
        if st.button("설사 +", key=f"btn_add_diarrhea_{uid}"):
            care.append({"type":"diarrhea","kind":diarrhea_kind,"ts": now_kst().isoformat()})
            save_carelog(uid, care); st.success("설사 기록됨.")
    with c4:
        apap_mg = st.number_input("APAP(아세트아미노펜) 투여량 mg", min_value=0.0, step=50.0, value=0.0, key=f"apap_mg_{uid}")
        if st.button("APAP 투여 기록", key=f"btn_log_apap_{uid}"):
            care.append({"type":"apap","mg":apap_mg,"ts": now_kst().isoformat()})
            save_carelog(uid, care); st.success("APAP 기록됨.")
    with c5:
        ibu_mg = st.number_input("IBU(이부프로펜) 투여량 mg", min_value=0.0, step=50.0, value=0.0, key=f"ibu_mg_{uid}")
        if st.button("IBU 투여 기록", key=f"btn_log_ibu_{uid}"):
            care.append({"type":"ibu","mg":ibu_mg,"ts": now_kst().isoformat()})
            save_carelog(uid, care); st.success("IBU 기록됨.")

    # 24h render
    now = now_kst()
    care_24h = [e for e in care if (now - datetime.fromisoformat(e["ts"])).total_seconds() <= 24*3600]
    if care_24h:
        st.markdown(f"#### 🗒️ 최근 24h 로그 — {nick} ({uid})")
        # summary
        cnt = lambda t: sum(1 for e in care_24h if e.get("type")==t)
        st.caption(f"요약: 발열 {cnt('fever')}회 · 구토 {cnt('vomit')}회 · 설사 {cnt('diarrhea')}회 · APAP {cnt('apap')}회 · IBU {cnt('ibu')}회")
        for e in sorted(care_24h, key=lambda x: x["ts"]):
            st.write(_ko_label_event(e))

        # exports
        ics_data = build_ics_for_next_doses(apap_next, ibu_next)
        st.download_button("📅 다음 3회 복용 일정 (.ics)",
                           data=ics_data, file_name=f"next_doses_{nick or uid}.ics",
                           key=f"dl_ics_{uid}")
        lines = [f"케어로그(최근 24h) — {nick or uid}"] + [_ko_label_event(e) for e in sorted(care_24h, key=lambda x: x["ts"])]
        log_txt = "\n".join(lines)
        st.download_button("⬇️ 케어로그 TXT", data=log_txt, file_name=f"carelog_24h_{nick or uid}.txt", key=f"dl_carelog_txt_{uid}")
        try:
            # Local PDF generator optional: if not present, silently skip
            try:
                from pdf_export import export_md_to_pdf  # type: ignore
                pdf = export_md_to_pdf("\n".join(["# 케어로그(24h)"] + lines))
                st.download_button("⬇️ 케어로그 PDF", data=pdf, file_name=f"carelog_24h_{nick or uid}.pdf", mime="application/pdf", key=f"dl_carelog_pdf_{uid}")
            except Exception:
                pass
            try:
                qr = _qr_png_bytes("\n".join(lines))
                st.download_button("⬇️ 케어로그 QR (PNG)", data=qr, file_name=f"carelog_24h_{nick or uid}.qr.png", mime="image/png", key=f"dl_carelog_qr_{uid}")
            except Exception:
                pass
        except Exception as e:
            st.caption(f"내보내기 오류: {e}")

    st.session_state["care_log"][uid] = care
