
# -*- coding: utf-8 -*-
"""
carelog_renderer_fix.py — v1.2
- Fix: 윈도우 파라미터(win) 안전 파싱 (예: "24h", "24", 24, None → 24로 처리)
- Per‑UID 로딩: /mnt/data/care_log/{uid}.json (없으면 guest/백업 폴더 탐색)
- KST 타임스탬프 표기(로컬 tz 미포함일 때 KST 가정)
- 이벤트 한글화: vomit→구토, diarrhea→설사, fever→발열(℃), apap/ibu→해열제
- 반환: (출력용 라인 리스트, 필터링된 raw entry 리스트)
"""
from __future__ import annotations
from typing import List, Tuple, Dict, Any, Iterable, Optional
import os, json
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9), name="KST")

# ---------- 경로/파일 ----------
def _carelog_path(uid: str) -> str:
    uid = (uid or "guest").strip() or "guest"
    base = "/mnt/data/care_log"
    return os.path.join(base, f"{uid}.json")

def _fallback_paths(uid: str) -> Iterable[str]:
    # 과거 위치/게스트 백업 등 차례로 탐색
    candidates = [
        _carelog_path(uid),
        _carelog_path("guest"),
        os.path.join("/mnt/data", f"{uid}.carelog.json"),
        os.path.join("/mnt/data", "care_log_backup", f"{uid}.json"),
    ]
    seen = set()
    for p in candidates:
        if p and p not in seen:
            seen.add(p)
            yield p

# ---------- 유틸 ----------
def _safe_hours(win: Any, default: int = 24) -> int:
    """'24h', '24', 24, None → 정수 시간(기본 24)"""
    if win is None:
        return default
    try:
        if isinstance(win, (int, float)):
            return max(1, int(win))
        s = str(win).strip().lower()
        s = s.replace("h", "")
        return max(1, int(float(s)))
    except Exception:
        return default

def _parse_ts(ts: str) -> datetime:
    """ISO or loose → aware KST dt. tz 없으면 KST로 가정."""
    if not ts:
        return datetime.now(KST)
    try:
        dt = datetime.fromisoformat(ts)
    except Exception:
        # 2025-09-22T09:15:38.276473+09:00 같은 형태가 아닐 때 유연 파서
        try:
            dt = datetime.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S")
        except Exception:
            return datetime.now(KST)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=KST)  # naive → KST 가정
    return dt.astimezone(KST)

_LABEL_MAP = {
    "vomit": "구토",
    "diarrhea": "설사",
    "fever": "발열",
    "apap": "해열제(APAP)",
    "ibu": "해열제(IBU)",
    "med": "투약",
    "temp": "체온",
}

def _fmt_event(e: Dict[str, Any]) -> str:
    etype = (e.get("type") or e.get("event") or "").strip()
    klabel = _LABEL_MAP.get(etype, etype or "기록")
    note = e.get("note") or e.get("detail") or e.get("value") or ""
    # 발열 숫자 붙이기
    if etype in {"fever", "temp"}:
        try:
            t = float(str(e.get("temp") or e.get("value") or "").replace("℃","").strip())
            if t > 0:
                note = f"{t:.1f}℃"
        except Exception:
            pass
    # 구토/설사 세부분류가 있으면 추가
    if etype in {"vomit", "diarrhea"}:
        sub = (e.get("subtype") or e.get("kind") or "").strip()
        if sub:
            note = f"{sub}"
    return f"{klabel}" + (f" {note}" if note else "")

# ---------- Load & Filter ----------
def carelog_load(uid: str) -> List[Dict[str, Any]]:
    for p in _fallback_paths(uid):
        try:
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    return data
                if isinstance(data, dict) and "entries" in data and isinstance(data["entries"], list):
                    return data["entries"]
        except Exception:
            continue
    return []

def render_carelog(uid: str, nick: Optional[str] = None, win: Any = 24) -> Tuple[List[str], List[Dict[str, Any]]]:
    """
    uid별 최근 win시간(기본 24h) 로그를 한국어로 정렬 출력.
    반환: (출력용 라인 배열, raw entries 배열)
    """
    now_kst = datetime.now(KST)
    hours = _safe_hours(win, 24)
    rows = []
    out_entries: List[Dict[str, Any]] = []

    for e in carelog_load(uid):
        ts_raw = e.get("ts") or e.get("time") or ""
        dt = _parse_ts(ts_raw)
        delta = (now_kst - dt).total_seconds()
        if delta <= hours * 3600:
            out_entries.append(e)
            stamp = dt.strftime("%Y-%m-%d %H:%M") + " KST"
            rows.append(f"{stamp} · {_fmt_event(e)}")

    # 최신순 정렬
    rows.sort(reverse=True)
    out_entries.sort(key=lambda x: _parse_ts(x.get("ts") or x.get("time") or "").timestamp(), reverse=True)

    if not rows:
        who = (nick or uid or "guest")
        rows = [f"최근 {hours}시간 로그 — 없음 ({who})"]

    return rows, out_entries
