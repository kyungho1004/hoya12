
# care_log_ui.py — 케어로그 UI 래퍼 (패치 방식, 기존 로직 삭제/변경 없이 '호출'만 제공)
from __future__ import annotations

def render(st, wkey=None, profile=None):
    """간단한 케어로그 패널.
    - 기존 앱의 케어로그/가드레일을 대체하지 않고, 화면에 '추가'로 제공.
    - 세션 키: 'care_log' (list). 없으면 생성.
    - APAP/IBU 쿨다운/24h 총량 등 핵심 로직은 기존 코드에 위임. 여기서는 기록/표시만.
    """
    try:
        ss = st.session_state
        log = ss.get("care_log")
        if log is None:
            ss["care_log"] = []
            log = ss["care_log"]

        with st.expander("📝 케어 로그 (추가 패널)", expanded=False):
            c1, c2 = st.columns([2,1])
            note = c1.text_input("메모", key=(wkey("cl_note") if callable(wkey) else "cl_note"))
            if c2.button("추가", key=(wkey("cl_add") if callable(wkey) else "cl_add")):
                import datetime as _dt
                ss["care_log"].append({
                    "time": _dt.datetime.now().isoformat(timespec="seconds"),
                    "text": note or "",
                })
                st.success("추가됨")
            if log:
                for i, e in enumerate(reversed(log[-50:]), start=1):
                    st.write(f"{i}. {e.get('time','')} · {e.get('text','')}")
            else:
                st.caption("기록 없음")
    except Exception:
        # UI 실패 시 앱은 계속
        pass
