
# -*- coding: utf-8 -*-
import streamlit as st
from datetime import datetime, timedelta

# ================= Common helpers =================
def wkey(s: str) -> str:
    return f"bm_{s}"

def _safe_rerun():
    try:
        st.rerun()
    except Exception:
        try:
            st.experimental_rerun()
        except Exception:
            pass

def _try_import(name):
    try:
        return __import__(name, fromlist=['*'])
    except Exception:
        return None

def _call_if_exists(mod, names, *args, **kwargs):
    for n in names:
        fn = getattr(mod, n, None) if mod else None
        if callable(fn):
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                st.error(f"{n} 실행 중 오류: {e}")
                return None
    return None

# Attempt to import optional modules
ui_results     = _try_import("ui_results")
lab_diet       = _try_import("lab_diet")
special_tests  = _try_import("special_tests")
onco_map       = _try_import("onco_map")
drug_db        = _try_import("drug_db")
pdf_export     = _try_import("pdf_export")
core_utils     = _try_import("core_utils")
peds_dose      = _try_import("peds_dose")
branding       = _try_import("branding")

# ================= Page config =================
title = getattr(branding, "APP_TITLE", "피수치 홈")
st.set_page_config(page_title=title, layout="wide")
st.sidebar.success("APP BUILD: Full Integrated • KST Helper • Safe Rerun")

st.markdown(f"### {title}")
st.caption(getattr(branding, "APP_TAGLINE", "교육/보조용 • 본문 내용은 임상 판단을 대체하지 않습니다."))

# ================= Tabs =================
t_home, t_labs, t_dx, t_chemo, t_peds, t_special, t_report, t_graph = st.tabs([
    "🏠 홈", "🧪 피수치/해석", "🧾 암(진단)", "💊 항암제", "👶 소아 진단", "🧪 특수검사", "📄 보고서", "📊 기록/그래프"
])

# ================= 홈 =================
with t_home:
    st.subheader("공지/요약")
    _call_if_exists(branding, ["render_home"])
    st.write("왼쪽 탭에서 기능을 선택하세요.")
    if core_utils and hasattr(core_utils, "about"):
        st.caption(core_utils.about())

# ================= 피수치/해석 =================
with t_labs:
    st.subheader("피수치/해석")
    done = _call_if_exists(ui_results, [
        "render_labs_panel", "render_lab_panel", "render_results_ui", "render"
    ])
    if done is None:
        st.info("ui_results 모듈의 렌더 함수를 찾지 못했습니다. 기본 입력 폼을 제공합니다.")
        col1, col2, col3 = st.columns(3)
        with col1:
            hb = st.number_input("Hb (g/dL)", 0.0, 25.0, step=0.1, key=wkey("hb"))
            wbc = st.number_input("WBC (×10³/µL)", 0.0, 100.0, step=0.1, key=wkey("wbc"))
        with col2:
            plt = st.number_input("Platelet (×10³/µL)", 0.0, 1000.0, step=1.0, key=wkey("plt"))
            anc = st.number_input("ANC (×10³/µL)", 0.0, 10.0, step=0.1, key=wkey("anc"))
        with col3:
            crp = st.number_input("CRP (mg/L)", 0.0, 500.0, step=0.1, key=wkey("crp"))
            esr = st.number_input("ESR (mm/hr)", 0.0, 150.0, step=1.0, key=wkey("esr"))
        st.button("임시 해석", key=wkey("labs_go"))

    _call_if_exists(lab_diet, ["render_nutrition", "render_lab_diet"])

# ================= 암(진단) =================
with t_dx:
    st.subheader("암(진단) 선택/가이드")
    done = _call_if_exists(onco_map, ["render_dx", "render_onco_map", "render"])
    if done is None and onco_map and hasattr(onco_map, "CANCER_MAP"):
        st.selectbox("암 종 선택", list(onco_map.CANCER_MAP.keys()), key=wkey("cancer_sel"))
    elif done is None:
        st.info("onco_map 렌더 함수를 찾지 못했습니다.")

# ================= 항암제 =================
with t_chemo:
    st.subheader("항암제/레짐")
    done = _call_if_exists(drug_db, ["render_drugs", "render_chemo", "render"])
    if done is None:
        st.info("drug_db 렌더 함수를 찾지 못했습니다.")
        # Simple lookup fallback if drug_db exposes DB
        db = getattr(drug_db, "DRUGS", None)
        if isinstance(db, dict):
            q = st.text_input("약물 검색", key=wkey("drug_q"))
            if q:
                hits = [k for k in db if q.lower() in k.lower()]
                for h in hits[:50]:
                    st.markdown(f"- **{h}**: {db[h]}")

# ================= 소아 진단 =================
with t_peds:
    st.subheader("소아 진단/보호자 설명")

    # 기본 입력
    st.number_input("체중(kg)", min_value=0.0, step=0.1, key=wkey("weight_kg"))
    age_months = st.number_input("나이(개월)", min_value=0, max_value=216, step=1, key=wkey("age_months"))
    if age_months is not None and age_months < 3:
        st.error("⚠ 3개월 미만 발열은 응급 평가가 필요할 수 있어요. 즉시 진료를 권합니다.")

    # 증상/노트: 외부 모듈 연결 시도
    _call_if_exists(peds_dose, ["render_peds_guide", "render", "render_symptom_explain_peds"])

    # 체중별 해열제 권장량 표
    _wt = st.session_state.get(wkey("weight_kg"))
    if _wt not in (None, ""):
        try:
            _w = float(str(_wt).replace(",", "."))
            _apap_min, _apap_max = round(_w*10), round(_w*15)
            _ibu_min,  _ibu_max  = round(_w*5),  round(_w*10)
            st.markdown("#### 체중별 권장량 (mg)")
            st.markdown(f"- APAP(아세트아미노펜): **{_apap_min}–{_apap_max} mg** (1회)")
            st.markdown(f"- IBU(이부프로펜): **{_ibu_min}–{_ibu_max} mg** (1회)")
            st.caption("※ 제품별 농도 확인. APAP 1일 최대 60 mg/kg, IBU 1일 최대 40 mg/kg(6개월 미만 IBU 금지).")
        except Exception:
            pass

    # ORS/RSV/Adeno expander
    with st.expander("🍶 ORS(경구수액) 혼합 가이드", expanded=False):
        st.write("- 시판 ORS 용법 우선.")
        st.write("- 가정용 대체: **물 1 L + 설탕 6티스푼 + 소금 1/2티스푤**.")
        st.caption("※ 심한 탈수/지속 구토/무반응은 즉시 진료. 영아는 의료진 지시 따르기.")

    with st.expander("🦠 RSV / Adenovirus 보호자 설명", expanded=False):
        st.markdown("**RSV**: 콧물/기침/천명/호흡곤란. 영유아 호흡수 증가/함몰호흡 시 즉시 진료.")
        st.markdown("**Adenovirus**: 고열/인후염/결막염/장염 가능. 발열 지속 길 수 있음.")
        st.caption("※ 호흡곤란, 지속 고열(>72h), 탈수, 의식저하, 경련 등 응급 시 즉시 진료.")

    # ---- 해열제 복용 도우미 (한국시간, 카운트다운 포함) ----
    def render_antipy_helper_kst():
        try:
            from zoneinfo import ZoneInfo
            KST = ZoneInfo("Asia/Seoul")
        except Exception:
            from datetime import timezone
            KST = timezone(timedelta(hours=9))

        def now_kst(): return datetime.now(KST)
        def fmt(ts):   return ts.strftime("%Y-%m-%d %H:%M (KST)")

        st.subheader("해열제 복용 도우미 (한국시간)")
        st.caption("※ 간격 규칙: APAP ≥ 4시간, IBU ≥ 6시간. 버튼으로 실제 복용 시간을 기록하세요.")

        st.session_state.setdefault(wkey("apap_log"), [])
        st.session_state.setdefault(wkey("ibu_log"), [])
        apap_log = st.session_state[wkey("apap_log")]
        ibu_log  = st.session_state[wkey("ibu_log")]

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
                apap_log.append(now_kst()); st.session_state[wkey("apap_log")] = apap_log; _safe_rerun()
            if apap_log:
                st.caption("오늘 기록")
                today = now_kst().date()
                for ts in sorted([t for t in apap_log if t.date()==today]):
                    st.markdown(f"- {ts.strftime('%H:%M (KST)')}")
                if st.button("APAP 기록 초기화", key=wkey("apap_clear")):
                    st.session_state[wkey("apap_log")] = []; _safe_rerun()

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
                ibu_log.append(now_kst()); st.session_state[wkey("ibu_log")] = ibu_log; _safe_rerun()
            if ibu_log:
                st.caption("오늘 기록")
                today = now_kst().date()
                for ts in sorted([t for t in ibu_log if t.date()==today]):
                    st.markdown(f"- {ts.strftime('%H:%M (KST)')}")
                if st.button("IBU 기록 초기화", key=wkey("ibu_clear")):
                    st.session_state[wkey("ibu_log")] = []; _safe_rerun()

        try:
            from streamlit_autorefresh import st_autorefresh
            st_autorefresh(interval=60_000, limit=None, key=wkey("antipy_autorefresh"))
            st.caption("⏱ 타이머 자동 갱신: 60초 간격")
        except Exception:
            if st.button("남은 시간 갱신", key=wkey("antipy_refresh")):
                _safe_rerun()

    render_antipy_helper_kst()

# ================= 특수검사 =================
with t_special:
    st.subheader("특수검사")
    done = _call_if_exists(special_tests, ["render_special", "render_special_tests", "render"])
    if done is None:
        st.info("special_tests 렌더 함수를 찾지 못했습니다.")

# ================= 보고서 =================
with t_report:
    st.subheader("보고서")
    # Compose text using any available builders
    text_parts = []
    txt = _call_if_exists(core_utils, ["build_summary", "build_report_text"])
    if isinstance(txt, str) and txt.strip():
        text_parts.append(txt)
    ptxt = _call_if_exists(peds_dose, ["build_peds_notes", "build_notes"])
    if isinstance(ptxt, str) and ptxt.strip():
        text_parts.append(ptxt)
    final_txt = "\n\n".join(text_parts) if text_parts else "보고서 내용을 입력/선택하여 생성하세요."
    st.text_area("보고서 미리보기", value=final_txt, height=240, key=wkey("report_preview"))

    # Export PDF if available
    if pdf_export and hasattr(pdf_export, "export_pdf"):
        if st.button("PDF 내보내기", key=wkey("pdf_export")):
            try:
                pdf_export.export_pdf(final_txt)
                st.success("PDF 내보내기를 완료했습니다.")
            except Exception as e:
                st.error(f"PDF 내보내기 실패: {e}")
    else:
        st.caption("pdf_export 모듈이 없거나 export_pdf 함수가 없어 텍스트만 제공합니다.")

# ================= 기록/그래프 =================
with t_graph:
    st.header("📊 기록/그래프 패널")
    tabs = st.tabs(["기록", "그래프", "내보내기"])

    with tabs[0]:
        st.markdown("#### 기록")
        _call_if_exists(core_utils, ["render_log_panel", "render_records"])

    with tabs[1]:
        st.markdown("#### 그래프")
        _call_if_exists(core_utils, ["render_graphs", "render_charts"])

    with tabs[2]:
        st.markdown("#### 내보내기")
        _call_if_exists(core_utils, ["render_exports"])
