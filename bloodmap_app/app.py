
# -*- coding: utf-8 -*-
import streamlit as st
from datetime import datetime, timedelta

# -------- Safe rerun shim (Streamlit version agnostic) --------
def _safe_rerun():
    try:
        st.rerun()  # new versions
    except Exception:
        try:
            st.experimental_rerun()  # old versions
        except Exception:
            pass

# -------- Optional robust imports for peds_guide --------
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
            # Safe shims
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

# -------- Helpers --------
def wkey(s: str) -> str:
    return f"bm_{s}"

st.set_page_config(page_title="피수치 도우미", layout="wide")
st.sidebar.success("APP BUILD: KST-helper + timer + safe_rerun")

st.markdown("### 피수치 도우미")
st.caption("제작: Hoya/GPT · 교육/보조용")

# -------- Tabs (single creation) --------
t_home, t_labs, t_dx, t_chemo, t_peds, t_special, t_report, t_graph = st.tabs([
    "🏠 홈", "🧪 피수치/해석", "🧾 암 선택", "💊 항암제", "👶 소아 증상", "🧪 특수검사", "📄 보고서", "📊 기록/그래프"
])

with t_home:
    st.subheader("홈")
    st.write("공지/가이드 영역")

with t_labs:
    st.subheader("피수치/해석")
    st.write("검사값 해석 UI 자리")

with t_dx:
    st.subheader("암 선택")
    st.write("진단 선택 UI 자리")

with t_chemo:
    st.subheader("항암제")
    st.write("항암제/프로토콜 안내")

with t_special:
    st.subheader("특수검사")
    st.write("특수검사 도우미")

with t_report:
    st.subheader("보고서")
    st.write("요약 보고서 미리보기/텍스트 구성")
    # 기록/그래프 패널은 이 탭에 넣지 않습니다 (요청 반영).

# -------- Pediatric tab --------
with t_peds:
    st.subheader("소아 증상 · 보호자 설명")
    st.number_input("체중(kg)", min_value=0.0, step=0.1, key=wkey("weight_kg"))

    try:
        render_symptom_explain_peds()
    except Exception:
        pass

    
# ---- 추가: 기본 입력 (나이/체중) & 주의 문구 ----
age_months = st.number_input("나이(개월)", min_value=0, max_value=216, step=1, key=wkey("age_months"))
if age_months is not None and age_months < 3:
    st.error("⚠ 3개월 미만 발열은 응급 평가가 필요할 수 있어요. 즉시 진료를 권합니다.")

# ---- 추가: 체중별 해열제 권장량 표 (mg) ----
wt = st.session_state.get(wkey("weight_kg"))
if wt not in (None, ""):
    try:
        w = float(str(wt).replace(",", "."))
        apap_min, apap_max = round(w*10), round(w*15)
        ibu_min,  ibu_max  = round(w*5),  round(w*10)
        st.markdown("#### 체중별 권장량 (mg)")
        st.markdown(f"- APAP(아세트아미노펜): **{apap_min}–{apap_max} mg** (1회)")
        st.markdown(f"- IBU(이부프로펜): **{ibu_min}–{ibu_max} mg** (1회)")
        st.caption("※ 제품별 농도(mg/mL, mg/정)는 다르니 라벨을 확인하세요. APAP 1일 최대 60 mg/kg, IBU 1일 최대 40 mg/kg(6개월 미만 금지).")
    except Exception:
        pass

# ---- 추가: ORS(경구수액) 혼합 가이드 ----
with st.expander("🍶 ORS(경구수액) 혼합 가이드", expanded=False):
    st.write("- 시판 ORS 용법을 우선 따르세요.")
    st.write("- 가정용 대체(WHO 비율 예시): **깨끗한 물 1 L + 설탕 평티스푼 6 + 소금 평티스푼 1/2** 잘 녹여 사용.")
    st.caption("※ 심한 탈수/지속 구토/무반응은 즉시 진료. 영아는 반드시 의료진 지시에 따르세요.")

# ---- 추가: RSV & Adenovirus 보호자 설명(간단 요약) ----
with st.expander("🦠 RSV / Adenovirus 보호자 설명", expanded=False):
    st.markdown("**RSV (호흡기세포융합바이러스)**")
    st.write("- 주 증상: 콧물, 기침, 천명, 호흡곤란. 영유아에서 호흡수 증가/함몰호흡 시 즉시 진료.")
    st.write("- 가정 관리: 수분, 비강흡인, 체온관리. 고위험군(미숙아/심폐질환)은 저역치 진료.")
    st.markdown("**Adenovirus (아데노바이러스)**")
    st.write("- 주 증상: 고열, 인후염/결막염/장염 가능. 발열 지속 기간이 길 수 있음.")
    st.write("- 가정 관리: 해열·수분·휴식. 결막염 의심 시 손위생/수건 공동사용 금지.")
    st.caption("※ 호흡곤란, 지속 고열(>72시간), 탈수, 의식저하, 경련 등 응급증상 시 즉시 진료.")
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
                _safe_rerun()
            if apap_log:
                st.caption("오늘 기록")
                today = now_kst().date()
                for ts in sorted([t for t in apap_log if t.date()==today]):
                    st.markdown(f"- {ts.strftime('%H:%M (KST)')}")
                if st.button("APAP 기록 초기화", key=wkey("apap_clear")):
                    st.session_state[wkey("apap_log")] = []
                    _safe_rerun()

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
                _safe_rerun()
            if st.button("IBU 기록 초기화", key=wkey("ibu_clear")) and ibu_log:
                st.session_state[wkey("ibu_log")] = []
                _safe_rerun()
            if ibu_log:
                st.caption("오늘 기록")
                today = now_kst().date()
                for ts in sorted([t for t in ibu_log if t.date()==today]):
                    st.markdown(f"- {ts.strftime('%H:%M (KST)')}")

        # (선택) 60초 자동 새로고침
        try:
            from streamlit_autorefresh import st_autorefresh
            st_autorefresh(interval=60_000, limit=None, key=wkey("antipy_autorefresh"))
            st.caption("⏱ 타이머 자동 갱신: 60초 간격")
        except Exception:
            if st.button("남은 시간 갱신", key=wkey("antipy_refresh")):
                _safe_rerun()

    # 호출(소아 탭 맨 아래)
    render_antipy_helper_kst()

# -------- Record/Graph Tab (only here) --------
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
