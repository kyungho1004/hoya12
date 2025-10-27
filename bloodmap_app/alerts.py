
# alerts.py - 위험 배너/경보 모듈 (패치 방식, 삭제 금지 원칙)
from __future__ import annotations

def _safe_get(d, key, default=None):
    try:
        return (d or {}).get(key, default)
    except Exception:
        return default

def _coerce_float(x, default=None):
    try:
        return float(x)
    except Exception:
        return default

def _is_recent_red_flag(care_log, minutes=30):
    # care_log 포맷 자유—최소한 최근 30분 안에 🚨 기록이 있으면 True
    try:
        entries = care_log or []
        if not isinstance(entries, (list, tuple)) or not entries:
            return False
        # 항목에 'time'과 'flag'/'emoji'가 들어있다고 가정, 없으면 best-effort
        import datetime as _dt
        now = _dt.datetime.now()
        for e in reversed(entries):
            t = e.get("time") or e.get("ts") or e.get("timestamp")
            if isinstance(t, (int, float)):
                dt = _dt.datetime.fromtimestamp(t)
            elif isinstance(t, str):
                try:
                    dt = _dt.datetime.fromisoformat(t)
                except Exception:
                    continue
            else:
                continue
            if (now - dt).total_seconds() <= minutes * 60:
                # 내용에 🚨, fever, seizure 등 키워드가 있으면 red flag
                s = (e.get("text") or e.get("note") or e.get("type") or "") + str(e)
                if any(k in s for k in ["🚨", "고열", "응급", "shock", "se저", "호흡곤란"]):
                    return True
        return False
    except Exception:
        return False

def _calc_banners(labs):
    # labs dict에서 최소한의 응급 기준만 확인 (Na, K, Ca, ANC, CRP 등)
    # 상세 임계치는 앱 기존 규칙에 위임. 여기서는 보수적 경고만 띄움.
    flags = []
    na = _coerce_float(_safe_get(labs, "Na"))
    k  = _coerce_float(_safe_get(labs, "K"))
    ca = _coerce_float(_safe_get(labs, "Ca_corr") or _safe_get(labs, "Ca"))
    anc = _coerce_float(_safe_get(labs, "ANC"))
    crp = _coerce_float(_safe_get(labs, "CRP"))
    temp = _coerce_float(_safe_get(labs, "Temp"))

    if anc is not None and anc < 500:
        flags.append(("🚨 호중구감소(ANC<500)", "감염 위험이 매우 높습니다. 38.0℃ 이상이면 즉시 병원 연락."))
    if temp is not None and temp >= 38.5:
        flags.append(("🚨 고열", "해열제 복용 여부 확인 후 병원 연락 권장(39.0℃ 즉시 병원)."))
    if na is not None and (na < 125 or na > 155):
        flags.append(("🚨 나트륨 이상", "신경학적 증상 위험. 수분/이뇨/투석 여부 점검 필요."))
    if k is not None and (k < 2.8 or k > 6.0):
        flags.append(("🚨 칼륨 이상", "심장 부정맥 위험. 즉시 의료진 상담 권장."))
    if ca is not None and (ca < 7.0 or ca > 12.5):
        flags.append(("🚨 칼슘 이상", "신경/근육 증상 위험. 반복 채혈 확인 권장."))
    if crp is not None and crp >= 10:
        flags.append(("⚠️ 염증 상승(CRP)", "임상 증상 동반 시 감염 평가 고려."))

    return flags

def render_risk_banner(st, labs=None, care_log=None, now_kst=None):
    """앱 어디서든 호출 가능한 위험 배너.
    - 인자 없으면 session_state에서 best-effort로 가져와서 표시만 함.
    - 앱 기존 규칙과 충돌하지 않도록, '표시만' 추가 (삭제/대체 없음).
    """
    try:
        ss = st.session_state
        if labs is None:
            labs = ss.get("latest_labs") or ss.get("labs") or {}
        if care_log is None:
            care_log = ss.get("care_log") or []
        flags = _calc_banners(labs)
        recent = _is_recent_red_flag(care_log, minutes=30)
        if recent:
            st.error("🚨 최근 30분 내 응급성 기록이 감지되었습니다. 지금 상태를 다시 확인해 주세요.")
        for title, msg in flags:
            if title.startswith("🚨"):
                st.error(f"**{title}** · {msg}")
            else:
                st.warning(f"**{title}** · {msg}")
    except Exception:
        # 표시 실패는 조용히 무시 (앱 유지)
        pass
