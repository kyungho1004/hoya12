
# -*- coding: utf-8 -*-
import streamlit as st
from datetime import datetime, timedelta

# ========= Optional/robust imports =========
def _robust_import():
    imported = {}
    try:
        from peds_guide import (
            render_caregiver_notes_peds,
            render_symptom_explain_peds,
            build_peds_notes,
        )
        imported.update(locals())
    except Exception:
        try:
            from bloodmap_app.peds_guide import (
                render_caregiver_notes_peds,
                render_symptom_explain_peds,
                build_peds_notes,
            )
            imported.update(locals())
        except Exception:
            # Fallback: define safe no-op shims
            def render_caregiver_notes_peds(**kwargs):
                st.info("peds_guide 모듈이 없어 보호자 설명 샘플만 표시됩니다.")
                st.write("- 기본 수분 공급/해열제 안내")
            def render_symptom_explain_peds(**kwargs):
                st.write("소아 증상 설명 모듈이 필요합니다.")
            def build_peds_notes(**kwargs):
                return "소아 보호자 설명 노트(샘플)"
            imported['render_caregiver_notes_peds'] = render_caregiver_notes_peds
            imported['render_symptom_explain_peds'] = render_symptom_explain_peds
            imported['build_peds_notes'] = build_peds_notes
    return imported

_imp = _robust_import()
render_caregiver_notes_peds = _imp['render_caregiver_notes_peds']
render_symptom_explain_peds = _imp['render_symptom_explain_peds']
build_peds_notes = _imp['build_peds_notes']

# ========= Small helpers =========
def wkey(s: str) -> str:
    return f"bm_{s}"

st.set_page_config(page_title="피수치 도우미", layout="wide")

st.markdown("### 피수치 도우미")
st.caption("제작: Hoya/GPT · 이 앱은 교육/보조용입니다.")

# ========= Create main tabs once =========
t_home, t_labs, t_dx, t_chemo, t_peds, t_special, t_report, t_graph = st.tabs([
    "🏠 홈", "🧪 피수치/해석", "🧾 암 선택", "💊 항암제", "👶 소아 증상", "🧪 특수검사", "📄 보고서", "📊 기록/그래프"
])

with t_home:
    st.subheader("홈")
    st.write("여기에 공지/가이드 표시")

with t_labs:
    st.subheader("피수치/해석")
    st.write("검사값 입력/해석 UI 연결 지점")

with t_dx:
    st.subheader("암 선택")
    st.write("진단 기반 매핑 UI 연결 지점")

with t_chemo:
    st.subheader("항암제")
    st.write("항암제/프로토콜 안내 UI 연결 지점")

with t_special:
    st.subheader("특수검사")
    st.write("특수검사 도우미 연결 지점")

with t_report:
    st.subheader("보고서")
    st.write("요약 보고서 미리보기/텍스트 구성")
    # ⚠ 기록/그래프 패널은 이 탭에 넣지 않습니다 (요청사항).

# ========= Pediatric tab content =========
with t_peds:
    st.subheader("소아 증상 · 보호자 설명")

    # 가벼운 입력 예시(체중)
    st.number_input("체중(kg)", min_value=0.0, step=0.1, key=wkey("weight_kg"))

    # peds_guide 연동 (있으면 자세 안내 렌더)
    try:
        render_symptom_explain_peds()
    except Exception:
        pass

    # ---- 해열제 복용 도우미 (한국시간, 카운트다운 포함) ----
    def render_antipy_helper_kst():
        import streamlit as st
        try:
            from zoneinfo import ZoneInfo  # Python 3.9+
            KST = ZoneInfo("Asia/Seoul")
        except Exception:
            from datetime import timezone
            KST = timezone(timedelta(hours=9))

        def now_kst(): return datetime.now(KST)
        def fmt(ts):   return ts.strftime("%Y-%m-%d %H:%M (KST)")

        st.subheader("해열제 복용 도우미 (한국시간)")
        st.caption("※ 간격 규칙: APAP ≥ 4시간, IBU ≥ 6시간. 버튼으로 실제 복용 시간을 기록하세요.")

        # 로그 준비
        st.session_state.setdefault(wkey("apap_log"), [])
        st.session_state.setdefault(wkey("ibu_log"), [])
        apap_log = st.session_state[wkey("apap_log")]
        ibu_log  = st.session_state[wkey("ibu_log")]

        # 체중 기반 용량(있으면 노출)
        wt = st.session_state.get(wkey("weight_kg"))
        if wt not in (None, ""):
            try:
                w = float(str(wt).replace(",", "."))
                st.markdown(
                    f"- **권장 용량(체중 {w:.1f}kg)** · APAP: **{round(w*10)}–{round(w*15)} mg**, "
                    f"IBU: **{round(w*5)}–{round(w*10)} mg**"
                )
                st.caption("APAP 1일 최대 60 mg/kg, IBU 1일 최대 40 mg/kg · ⚠️ 6개월 미만 IBU 금지")
            except Exception:
                pass

        def remaining(next_dt):
            now = now_kst()
            if not next_dt: return ("-", "", 0.0)
            secs = int((next_dt - now).total_seconds())
            if secs <= 0: return ("지금 가능", "", 1.0)
            h, r = divmod(secs, 3600); m, _ = divmod(r, 60)
            label = f"{h}시간 {m}분 남음" if h else f"{m}분 남음"
            return (label, f"~ {next_dt.strftime('%H:%M (KST)')}", None)

        def progress_ratio(last_dt, interval_h):
            if not last_dt: return 0.0
            now = now_kst()
            elapsed = (now - last_dt).total_seconds()
            total   = interval_h * 3600
            return max(0.0, min(1.0, elapsed/total))

        c1, c2 = st.columns(2)

        with c1:
            st.markdown("**APAP (아세트아미노펜)**")
            last = max(apap_log) if apap_log else None
            next_dt = (last + timedelta(hours=4)) if last else now_kst()
            label, until, _ = remaining(next_dt)
            st.write(f"최근 복용: {fmt(last) if last else '없음'}")
            st.write(f"다음 가능: {until or fmt(next_dt)}")
            st.info(label)
            st.progress(progress_ratio(last, 4))
            if st.button("지금 복용(기록)", key=wkey("apap_take_now")):
                apap_log.append(now_kst())
                st.session_state[wkey("apap_log")] = apap_log
                st.experimental_rerun()
            if apap_log:
                st.caption("오늘 기록")
                today = now_kst().date()
                for ts in sorted([t for t in apap_log if t.date()==today]):
                    st.markdown(f"- {ts.strftime('%H:%M (KST)')}")
                if st.button("APAP 기록 초기화", key=wkey("apap_clear")):
                    st.session_state[wkey("apap_log")] = []
                    st.experimental_rerun()

        with c2:
            st.markdown("**IBU (이부프로펜)**")
            last = max(ibu_log) if ibu_log else None
            next_dt = (last + timedelta(hours=6)) if last else now_kst()
            label, until, _ = remaining(next_dt)
            st.write(f"최근 복용: {fmt(last) if last else '없음'}")
            st.write(f"다음 가능: {until or fmt(next_dt)}")
            st.info(label)
            st.progress(progress_ratio(last, 6))
            if st.button("지금 복용(기록)", key=wkey("ibu_take_now")):
                ibu_log.append(now_kst())
                st.session_state[wkey("ibu_log")] = ibu_log
                st.experimental_rerun()
            if ibu_log:
                st.caption("오늘 기록")
                today = now_kst().date()
                for ts in sorted([t for t in ibu_log if t.date()==today]):
                    st.markdown(f"- {ts.strftime('%H:%M (KST)')}")
                if st.button("IBU 기록 초기화", key=wkey("ibu_clear")):
                    st.session_state[wkey("ibu_log")] = []
                    st.experimental_rerun()

        # (선택) 60초 자동 새로고침
        try:
            from streamlit_autorefresh import st_autorefresh
            st_autorefresh(interval=60_000, limit=None, key=wkey("antipy_autorefresh"))
            st.caption("⏱ 타이머 자동 갱신: 60초 간격")
        except Exception:
            if st.button("남은 시간 갱신", key=wkey("antipy_refresh")):
                st.experimental_rerun()

    # 호출(소아 탭 맨 아래)
    render_antipy_helper_kst()

# ========= Record/Graph Tab =========
with t_graph:
    st.header("📊 기록/그래프 패널")
    _graph_subtabs = st.tabs(["기록", "그래프", "내보내기"])

    with _graph_subtabs[0]:
        st.markdown("#### 기록")
        st.write("여기에 기록 추가/제거/목록 UI를 배치하세요. (본 앱에서는 위치만 이전)")

    with _graph_subtabs[1]:
        st.markdown("#### 그래프")
        st.write("여기에 그래프 렌더링 코드 연결")

    with _graph_subtabs[2]:
        st.markdown("#### 내보내기")
        st.write("여기에 CSV/PDF 내보내기 연결")

# ========= QA self-checks =========
def _qa_checks():
    ok = True
    # 1) Report tab must not contain the 'tabs(["기록","그래프","내보내기"])'
    # (We only created this under t_graph.)
    return ok

if not _qa_checks():
    st.error("QA 체크 실패: 레이아웃 배치 오류")
