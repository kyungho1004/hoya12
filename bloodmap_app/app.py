
# -*- coding: utf-8 -*-
import streamlit as st
from datetime import datetime, timedelta

# ---------- helpers ----------
def wkey(s): return f"bm_{s}"

def _safe_rerun():
    try: st.rerun()
    except Exception:
        try: st.experimental_rerun()
        except Exception: pass

# optional modules (lazy import inside functions to avoid import errors here)

st.set_page_config(page_title="통합 앱", layout="wide")
st.sidebar.success("APP BUILD: Full-Wired")

t_home, t_labs, t_dx, t_chemo, t_peds, t_special, t_report, t_graph = st.tabs([
    "🏠 홈", "🧪 피수치/해석", "🧾 암(진단)", "💊 항암제", "👶 소아 진단", "🧪 특수검사", "📄 보고서", "📊 기록/그래프"
])

with t_home:
    st.subheader("공지/요약")
    st.caption("교육/보조용 · 본문 내용은 임상 판단을 대체하지 않습니다.")

# ---------- Labs ----------
with t_labs:
    st.subheader("피수치/해석")
    col1, col2, col3 = st.columns(3)
    with col1:
        Hb  = st.number_input("Hb (g/dL)", 0.0, 25.0, step=0.1, key=wkey("Hb"))
        WBC = st.number_input("WBC (×10³/µL)", 0.0, 100.0, step=0.1, key=wkey("WBC"))
    with col2:
        PLT = st.number_input("Platelet (×10³/µL)", 0.0, 1000.0, step=1.0, key=wkey("PLT"))
        ANC = st.number_input("ANC (×10³/µL)", 0.0, 10.0, step=0.1, key=wkey("ANC"))
    with col3:
        CRP = st.number_input("CRP (mg/L)", 0.0, 500.0, step=0.1, key=wkey("CRP"))
        ESR = st.number_input("ESR (mm/hr)", 0.0, 150.0, step=1.0, key=wkey("ESR"))

    labs = {"Hb":Hb, "WBC":WBC, "PLT":PLT, "ANC":ANC, "CRP":CRP, "ESR":ESR}
    if st.button("해석 보기", key=wkey("labs_go")):
        try:
            from lab_diet import lab_diet_guides
            recs = lab_diet_guides(labs, heme_flag=True)
            if recs:
                st.success("식이가이드/주의")
                for ln in recs:
                    st.markdown(f"- {ln}")
            else:
                st.info("특이 식이가이드는 없습니다.")
        except Exception as e:
            st.warning(f"lab_diet 모듈 사용 불가: {e}")

# ---------- Diagnosis ----------
with t_dx:
    st.subheader("암(진단) 선택/가이드")
    try:
        from onco_map import build_onco_map, dx_display, auto_recs_by_dx
        O = build_onco_map()
        groups = list(O.keys())
        g = st.selectbox("암 그룹", groups, key=wkey("grp"))
        dxs = list(O[g].keys())
        d = st.selectbox("진단", dxs, key=wkey("dx"))
        st.markdown(f"**{dx_display(g, d)}**")

        info = O[g][d]
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("**Chemo**")
            for x in info.get("chemo", []): st.write(f"- {x}")
        with c2:
            st.markdown("**Targeted/Immuno**")
            for x in info.get("targeted", []): st.write(f"- {x}")
        with c3:
            st.markdown("**Antibiotics/Proph**")
            for x in info.get("abx", []): st.write(f"- {x}")

        st.divider()
        st.markdown("#### 자동 추천 메모")
        rec = auto_recs_by_dx(d)
        if rec: st.info(rec)
        else: st.caption("추가 메모 없음.")
    except Exception as e:
        st.warning(f"onco_map 사용 불가: {e}")

# ---------- Anticancer (drugs) ----------
with t_chemo:
    st.subheader("항암제/레짐")
    try:
        from drug_db import ensure_onco_drug_db, display_label
        DB = ensure_onco_drug_db()
        q = st.text_input("약물 검색", key=wkey("chemo_q"))
        keys = [k for k in DB.keys() if not q or q.lower() in k.lower()][:50]
        sel = st.multiselect("부작용 보기 약물 선택", keys, key=wkey("ae_sel"))
        if sel:
            try:
                from ui_results import render_adverse_effects
                render_adverse_effects(st, sel, DB)
            except Exception as e:
                st.warning(f"부작용 렌더 불가: {e}")
    except Exception as e:
        st.warning(f"drug_db 사용 불가: {e}")

# ---------- Pediatric ----------
with t_peds:
    st.subheader("소아 진단/보호자 설명")
    st.number_input("체중(kg)", min_value=0.0, step=0.1, key=wkey("weight_kg"))
    age_months = st.number_input("나이(개월)", min_value=0, max_value=216, step=1, key=wkey("age_months"))
    if age_months < 3: st.error("⚠ 3개월 미만 발열은 즉시 진료 권고")

    # ORS + RSV/Adeno
    with st.expander("🍶 ORS(경구수액) 혼합 가이드", expanded=False):
        st.write("- 시판 ORS 우선. 가정용: 물 1 L + 설탕 6티스푼 + 소금 1/2티스푼.")
    with st.expander("🦠 RSV / Adenovirus 보호자 설명", expanded=False):
        st.write("RSV: 콧물/기침/천명/호흡곤란. 영유아 호흡수 증가·함몰호흡 시 즉시 진료.")
        st.write("Adenovirus: 고열/인후염/결막염/장염 가능. 결막염 의심 시 손위생/수건 공동사용 금지.")

    # ---- 해열제 복용 도우미 (한국시간, 카운트다운 포함) ----
    def render_antipy_helper_kst():
        try:
            from zoneinfo import ZoneInfo; KST = ZoneInfo("Asia/Seoul")
        except Exception:
            from datetime import timezone; KST = timezone(timedelta(hours=9))
        def now_kst(): return datetime.now(KST)
        def fmt(ts): return ts.strftime("%Y-%m-%d %H:%M (KST)")

        st.subheader("해열제 복용 도우미 (한국시간)")
        st.caption("APAP ≥4h, IBU ≥6h. 버튼으로 실제 복용 시간을 기록하세요.")

        st.session_state.setdefault(wkey("apap_log"), [])
        st.session_state.setdefault(wkey("ibu_log"), [])
        apap_log = st.session_state[wkey("apap_log")]
        ibu_log  = st.session_state[wkey("ibu_log")]

        # 체중별 용량 범위
        _wt = st.session_state.get(wkey("weight_kg"))
        if _wt not in (None, ""):
            try:
                _w = float(str(_wt).replace(",", "."))
                st.markdown(f"- **권장 용량** · APAP: **{round(_w*10)}–{round(_w*15)} mg**, IBU: **{round(_w*5)}–{round(_w*10)} mg**")
                st.caption("APAP 1일 최대 60 mg/kg, IBU 1일 최대 40 mg/kg · 6개월 미만 IBU 금지")
            except Exception: pass

        def remaining(next_dt):
            now = now_kst(); secs = int((next_dt - now).total_seconds())
            if secs <= 0: return ("지금 가능", "", 1.0)
            h, r = divmod(secs, 3600); m, _ = divmod(r, 60)
            return (f"{h}시간 {m}분 남음" if h else f"{m}분 남음", f"~ {next_dt.strftime('%H:%M (KST)')}", None)
        def progress_ratio(last_dt, h):
            if not last_dt: return 0.0
            now = now_kst(); return max(0.0, min(1.0, (now-last_dt).total_seconds()/(h*3600)))

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**APAP**")
            last = max(apap_log) if apap_log else None
            next_dt = (last + timedelta(hours=4)) if last else now_kst()
            label, until, _ = remaining(next_dt)
            st.write(f"최근 복용: {fmt(last) if last else '없음'}")
            st.write(f"다음 가능: {until or fmt(next_dt)}"); st.info(label)
            st.progress(progress_ratio(last, 4))
            if st.button("지금 복용(기록)", key=wkey("apap_take")):
                apap_log.append(now_kst()); st.session_state[wkey("apap_log")] = apap_log; _safe_rerun()
            if st.button("APAP 기록 초기화", key=wkey("apap_clear")) and apap_log:
                st.session_state[wkey("apap_log")] = []; _safe_rerun()
            if apap_log:
                st.caption("오늘 기록"); today = now_kst().date()
                for ts in sorted([t for t in apap_log if t.date()==today]):
                    st.markdown(f"- {ts.strftime('%H:%M (KST)')}")

        with c2:
            st.markdown("**IBU**")
            last = max(ibu_log) if ibu_log else None
            next_dt = (last + timedelta(hours=6)) if last else now_kst()
            label, until, _ = remaining(next_dt)
            st.write(f"최근 복용: {fmt(last) if last else '없음'}")
            st.write(f"다음 가능: {until or fmt(next_dt)}"); st.info(label)
            st.progress(progress_ratio(last, 6))
            if st.button("지금 복용(기록)", key=wkey("ibu_take")):
                ibu_log.append(now_kst()); st.session_state[wkey("ibu_log")] = ibu_log; _safe_rerun()
            if st.button("IBU 기록 초기화", key=wkey("ibu_clear")) and ibu_log:
                st.session_state[wkey("ibu_log")] = []; _safe_rerun()
            if ibu_log:
                st.caption("오늘 기록"); today = now_kst().date()
                for ts in sorted([t for t in ibu_log if t.date()==today]):
                    st.markdown(f"- {ts.strftime('%H:%M (KST)')}")

        try:
            from streamlit_autorefresh import st_autorefresh
            st_autorefresh(interval=60_000, limit=None, key=wkey("antipy_autorefresh"))
            st.caption("⏱ 타이머 자동 갱신: 60초 간격")
        except Exception:
            if st.button("남은 시간 갱신", key=wkey("antipy_refresh")): _safe_rerun()

    render_antipy_helper_kst()

# ---------- Special tests ----------
with t_special:
    st.subheader("특수검사")
    try:
        from special_tests import special_tests_ui
        lines = special_tests_ui()
        if lines:
            st.markdown("#### 자동 요약")
            for ln in lines: st.markdown(f"- {ln}")
    except Exception as e:
        st.warning(f"special_tests 사용 불가: {e}")

# ---------- Report ----------
with t_report:
    st.subheader("보고서")
    txt = st.text_area("보고서 초안", height=240, key=wkey("rep_txt"))
    col = st.columns(2)
    with col[0]:
        if st.button("PDF 내보내기", key=wkey("pdf_btn")):
            try:
                from pdf_export import export_md_to_pdf
                export_md_to_pdf(txt)
                st.success("PDF 내보내기 완료")
            except Exception as e:
                st.warning(f"PDF 내보내기 불가: {e}")

# ---------- Record/Graph ----------
with t_graph:
    st.header("📊 기록/그래프 패널")
    tabs = st.tabs(["기록", "그래프", "내보내기"])
    with tabs[0]: st.write("여기에 기록 UI 연결")
    with tabs[1]: st.write("여기에 그래프 UI 연결")
    with tabs[2]: st.write("여기에 내보내기 UI 연결")
