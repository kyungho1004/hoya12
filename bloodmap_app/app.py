
# -*- coding: utf-8 -*-
from __future__ import annotations

import os, json, importlib, types
import streamlit as st
from datetime import datetime as _dt, timedelta
from zoneinfo import ZoneInfo

# ---------------- Header ----------------
APP_VERSION = "항상 여러분들의 힘이 되도록 노력하겠습니다. 여러분들의 피드백이 업데이트에 많은 도움이 됩니다"
st.set_page_config(page_title="Bloodmap", page_icon="🩸", layout="wide")
st.title(f"Bloodmap {APP_VERSION}")
st.caption("Bloodmap 항상 여러분들의 힘이 되도록 노력하겠습니다. 여러분들의 피드백이 업데이트에 많은 도움이 됩니다")

# ---------------- Tabs (fixed order) ----------------
tabs = ["🏠 홈","👶 소아 증상","🧬 암 선택","💊 항암제(진단 기반)","🧪 피수치 입력","🔬 특수검사","📄 보고서","📊 기록/그래프"]
t_home, t_peds, t_dx, t_chemo, t_labs, t_special, t_report, t_graph = st.tabs(tabs)

# ================= Utilities =================
_KST = ZoneInfo("Asia/Seoul")
def wkey(x:str)->str: return f"bm_{x}"

def _import(mod:str) -> types.ModuleType|None:
    try: return importlib.import_module(mod)
    except Exception: return None

# ---------- P0: Antipyretic badges ----------
def _carelog_24h_totals(log=None):
    log = log or st.session_state.get('care_log', [])
    now = _dt.now(_KST); since = now - timedelta(hours=24)
    total_apap = 0.0; total_ibu = 0.0; last_apap=None; last_ibu=None
    for rec in (log or []):
        try:
            ts = rec.get('ts')
            if isinstance(ts, str): ts = _dt.fromisoformat(ts[:19])
        except Exception:
            ts = None
        if ts and ts < since: continue
        drug = (rec.get('drug') or '').lower()
        try: mg = float(rec.get('mg') or 0)
        except Exception: mg = 0.0
        if any(k in drug for k in ("apap","acetaminophen","타이레놀")):
            total_apap += mg; 
            if ts and (not last_apap or ts>last_apap): last_apap = ts
        if any(k in drug for k in ("ibu","ibuprofen","이부프로펜")):
            total_ibu  += mg;
            if ts and (not last_ibu  or ts>last_ibu ): last_ibu  = ts
    return dict(now=now,total_apap=total_apap,total_ibu=total_ibu,last_apap=last_apap,last_ibu=last_ibu)

def _render_antipyretic_badges():
    info = _carelog_24h_totals()
    weight = st.session_state.get('weight_kg') or 0
    apap_limit = max(st.session_state.get('apap_24h_limit_mg', 75*weight) or 3000, 3000)
    ibu_limit  =       st.session_state.get('ibu_24h_limit_mg', 40*weight) or 1200
    def _next(ts,h): return ts+timedelta(hours=h) if ts else None
    next_apap=_next(info['last_apap'],4); next_ibu=_next(info['last_ibu'],6)
    c1,c2,c3 = st.columns([1,1,2])
    c1.metric("APAP 24h 누적", f"{info['total_apap']:.0f} mg", f"남음 {max(0, apap_limit-info['total_apap']):.0f} mg")
    c2.metric("IBU 24h 누적",  f"{info['total_ibu']:.0f} mg", f"남음 {max(0, ibu_limit -info['total_ibu']):.0f} mg")
    c3.caption(" · ".join(filter(None,[
        f"APAP 다음 가능: {(_next(info['last_apap'],4)).strftime('%H:%M')}" if _next(info['last_apap'],4) else None,
        f"IBU 다음 가능: {(_next(info['last_ibu'],6)).strftime('%H:%M')}" if _next(info['last_ibu'],6) else None,
    ])) or "최근 복용 기록 없음")
    if info['total_apap']>=apap_limit or info['total_ibu']>=ibu_limit:
        st.warning("🚨 24시간 총량 초과. 복용 중단 및 의료진 상담 필요.")
    elif info['total_apap']>=apap_limit*0.8 or info['total_ibu']>=ibu_limit*0.8:
        st.info("⚠️ 24시간 총량의 80% 초과. 중복 성분 주의.")

# ---------- P1: Care Log input/save ----------
CARELOG_PATH = "/mnt/data/care_log.json"

def _carelog_load():
    if "care_log" in st.session_state:
        return st.session_state["care_log"]
    try:
        os.makedirs(os.path.dirname(CARELOG_PATH) or ".", exist_ok=True)
        if os.path.exists(CARELOG_PATH):
            st.session_state["care_log"] = json.loads(open(CARELOG_PATH, "r", encoding="utf-8").read())
        else:
            st.session_state["care_log"] = []
    except Exception:
        st.session_state["care_log"] = []
    return st.session_state["care_log"]

def _carelog_save():
    try:
        os.makedirs(os.path.dirname(CARELOG_PATH) or ".", exist_ok=True)
        open(CARELOG_PATH, "w", encoding="utf-8").write(json.dumps(st.session_state.get("care_log", []), ensure_ascii=False))
    except Exception:
        pass

def _render_carelog_input():
    """해열제 복용 입력 + 최근 기록 테이블/삭제"""
    _carelog_load()
    st.markdown("#### 🧾 해열제 복용 기록 추가")
    col1, col2, col3, col4 = st.columns([1,1,1,1])
    with col1:
        drug = st.selectbox("약물", ["Acetaminophen(APAP)", "Ibuprofen(IBU)", "기타"], index=0, key="cl_drug")
    with col2:
        mg = st.number_input("용량 (mg)", min_value=0.0, step=50.0, key="cl_mg")
    with col3:
        # Streamlit 버전에 따른 입력 폴백
        dt_widget = getattr(st, "datetime_input", None)
        if dt_widget:
            ts = dt_widget("복용 시각", value=_dt.now(_KST), key="cl_ts_dt")
        else:
            d = st.date_input("복용 날짜", value=_dt.now(_KST).date(), key="cl_dt_d")
            t = st.time_input("복용 시간", value=_dt.now(_KST).time(), key="cl_dt_t")
            ts = _dt.combine(d, t)
    with col4:
        note = st.text_input("메모(선택)", key="cl_note")

    cc1, cc2, cc3 = st.columns([1,1,1])
    with cc1:
        if st.button("기록 추가", key="cl_add"):
            st.session_state["care_log"].append({
                "drug": drug,
                "mg": float(mg or 0),
                "ts": ts.isoformat(),
                "note": note or ""
            })
            _carelog_save()
            st.success("복용 기록이 추가되었습니다.")
    with cc2:
        if st.button("오늘 기록 초기화", key="cl_reset_today"):
            today = _dt.now(_KST).date()
            newlog = []
            for r in st.session_state["care_log"]:
                try:
                    d0 = _dt.fromisoformat((r.get("ts","") or "")[:19]).date()
                except Exception:
                    d0 = today
                if d0 != today:
                    newlog.append(r)
            st.session_state["care_log"] = newlog
            _carelog_save()
            st.info("오늘 기록을 초기화했습니다.")
    with cc3:
        if st.button("전체 기록 비우기", key="cl_clear_all"):
            st.session_state["care_log"] = []
            _carelog_save()
            st.warning("전체 기록을 삭제했습니다.")

    # 최근 기록 표
    st.markdown("##### 📋 최근 복용 기록")
    if st.session_state["care_log"]:
        rows = sorted(st.session_state["care_log"], key=lambda r: r.get("ts",""), reverse=True)[:20]
        for idx, r in enumerate(rows):
            c1, c2, c3, c4, c5 = st.columns([1.2, 1.5, 1, 3, 0.8])
            try:
                tsd = _dt.fromisoformat((r.get("ts","") or "")[:19]).strftime("%m-%d %H:%M")
            except Exception:
                tsd = r.get("ts","")
            c1.write(tsd); c2.write(r.get("drug","")); c3.write(f'{float(r.get("mg",0) or 0):.0f} mg'); c4.write(r.get("note",""))
            if c5.button("삭제", key=f"cl_del_{idx}"):
                for j, rr in enumerate(st.session_state["care_log"]):
                    if rr == r:
                        st.session_state["care_log"].pop(j); break
                _carelog_save()
                try: st.experimental_rerun()
                except Exception: pass
    else:
        st.caption("최근 기록 없음")

# ---------- P1: Peds sticky nav ----------
def _peds_sticky_nav():
    st.markdown("""
    <style>.peds-sticky{position:sticky; top:64px; z-index:9; background:rgba(250,250,250,.9);
    padding:8px 8px; border:1px solid #eee; border-radius:10px;}
    .peds-sticky a{margin-right:10px; font-weight:600; text-decoration:none;}
    </style>
    <div class="peds-sticky">
      <a href="#peds_constipation">변비</a>
      <a href="#peds_diarrhea">설사</a>
      <a href="#peds_vomit">구토</a>
      <a href="#peds_antipyretic">해열제</a>
      <a href="#peds_ors">ORS</a>
    </div>
    """, unsafe_allow_html=True)

# ---------- P1: ORS PDF (direct) ----------
def _render_ors_pdf_button():
    if st.button("ORS 가이드 PDF 저장", key=wkey("ors_pdf_btn")):
        try:
            _pdf = _import("pdf_export")
            lines = [
                "# ORS(경구수분보충) / 탈수 가이드",
                "- 5~10분마다 소량씩 자주, 토하면 10~15분 휴식 후 재개",
                "- 2시간 이상 소변 없음 / 입마름 / 눈물 감소 / 축 늘어짐 → 진료",
                "- 가능하면 스포츠음료 대신 ORS 용액 사용",
                "",
                "# ORS 집에서 만드는 법 (WHO 권장 비율, 1 L 기준)",
                "- 끓였다 식힌 물 1 L",
                "- 설탕 작은술 6스푼(평평하게) ≈ 27 g",
                "- 소금 작은술 1/2 스푼(평평하게) ≈ 2.5 g",
                "",
                "- 모두 완전히 녹을 때까지 저어주세요.",
                "- 5~10분마다 소량씩 마시고, 토하면 10~15분 쉬었다 재개하세요.",
                "- 맛은 '살짝 짠 단물(눈물맛)' 정도가 정상입니다. 너무 짜거나 달면 물을 더 넣어 희석하세요.",
                "",
                "# 주의",
                "- 과일주스·탄산·순수한 물만 대량 섭취는 피하세요(전해질 불균형 위험).",
                "- 6개월 미만 영아/만성질환/신생아는 반드시 의료진과 상의 후 사용하세요.",
                "- 설탕 대신 꿀 금지(영아 보툴리누스 위험).",
            ]
            md = "\n".join(lines)
            if _pdf and hasattr(_pdf, "export_md_to_pdf"):
                data = _pdf.export_md_to_pdf(md)
            else:
                data = md.encode("utf-8")
            save_path = "/mnt/data/ORS_guide.pdf"
            try:
                os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
                with open(save_path, "wb") as f: f.write(data)
            except Exception:
                save_path = "ORS_guide.pdf"
                with open(save_path, "wb") as f: f.write(data)
            with open(save_path, "rb") as f:
                st.download_button("PDF 다운로드", f, file_name="ORS_guide.pdf",
                                   mime="application/pdf", key=wkey("ors_pdf_dl"))
            st.success(f"ORS 가이드 PDF 저장 완료: {save_path}")
        except Exception as e:
            st.error(f"PDF 생성 실패: {e}")

# ---------- P1: ER onepage PDF (fallback) ----------
def _render_er_onepage_button():
    st.markdown("### 🏥 ER 원페이지 PDF")
    if st.button("ER 원페이지 PDF 만들기", key=wkey("er_pdf_btn")):
        try:
            _pdf = _import("pdf_export")
            path = None
            if _pdf and hasattr(_pdf, "export_er_onepager"):
                path = _pdf.export_er_onepager(st.session_state)  # type: ignore
            elif _pdf and hasattr(_pdf, "build_er_onepager"):
                path = _pdf.build_er_onepager(st.session_state)   # type: ignore
            if not path and _pdf and hasattr(_pdf, "export_md_to_pdf"):
                md = "\n".join([
                    "# ER 원페이지 요약",
                    "- 환자 기본정보 요약",
                    "- 최근 주요 피수치: WBC/Hb/Plt, ANC, Cr/eGFR 등",
                    "- 최근 복약/케어 포인트: 해열제, 수분 섭취, ORS 권고",
                    "- 경고 신호: 2시간 무뇨·입마름·눈물 감소·축 늘어짐 등",
                    "- 연락처/다음 내원: 담당자/병동/응급실 번호",
                ])
                pdf_bytes = _pdf.export_md_to_pdf(md)  # type: ignore
                save_path = "/mnt/data/ER_onepage.pdf"
                try:
                    os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
                    with open(save_path, "wb") as f: f.write(pdf_bytes)
                    path = save_path
                except Exception:
                    with open("ER_onepage.pdf", "wb") as f: f.write(pdf_bytes)
                    path = "ER_onepage.pdf"
            if path:
                with open(path, "rb") as f:
                    st.download_button("PDF 다운로드", f,
                        file_name="bloodmap_ER_onepage.pdf",
                        mime="application/pdf", key=wkey("er_pdf_dl"))
                st.success(f"ER 원페이지 PDF 저장 완료: {path}")
            else:
                st.info("pdf_export 모듈에서 원페이지 함수를 찾지 못했고, 폴백 생성도 실패했습니다.")
        except Exception as e:
            st.warning("ER PDF 생성 중 오류: " + str(e))

# =================== Render Tabs ===================
with t_home:
    _render_antipyretic_badges()
    _render_carelog_input()

with t_peds:
    _peds_sticky_nav()
    _render_antipyretic_badges()
    _render_carelog_input()
    _render_ors_pdf_button()

with t_dx:
    mod = _import("onco_map")
    if not (mod and (getattr(mod, "render", None) or getattr(mod, "app", None))):
        st.info("암 선택 화면은 onco_map 모듈에서 제공됩니다.")

with t_chemo:
    mod = _import("drug_db")
    if not (mod and (getattr(mod, "render", None) or getattr(mod, "app", None))):
        st.info("항암제 화면은 drug_db 모듈에서 제공됩니다.")

with t_labs:
    mod = _import("ui_results")
    if not (mod and (getattr(mod, "render_labs", None) or getattr(mod, "render", None))):
        st.info("피수치 입력은 ui_results 모듈에서 제공됩니다.")

with t_special:
    mod = _import("special_tests")
    if not (mod and (getattr(mod, "render", None) or getattr(mod, "app", None))):
        st.info("특수검사는 special_tests 모듈에서 제공됩니다.")

with t_report:
    _render_er_onepage_button()
    # Special Notes
    with st.expander('📝 Special Notes (환자별 메모)', expanded=False):
        notes_path = '/mnt/data/profile/special_notes.txt'
        try:
            os.makedirs('/mnt/data/profile', exist_ok=True)
            if 'special_notes' not in st.session_state:
                if os.path.exists(notes_path):
                    st.session_state['special_notes'] = open(notes_path,'r',encoding='utf-8').read()
                else:
                    st.session_state['special_notes'] = ''
        except Exception:
            st.session_state['special_notes'] = st.session_state.get('special_notes','')
        val = st.text_area('메모(보고서/PDF에 첨부 용)',
                           st.session_state.get('special_notes',''),
                           height=140, key=wkey('special_notes_ta'))
        cA,cB = st.columns([1,1])
        with cA:
            if st.button('저장', key=wkey('special_notes_save')):
                try:
                    open(notes_path,'w',encoding='utf-8').write(val or '')
                    st.session_state['special_notes'] = val or ''
                    st.success('저장 완료')
                except Exception as e:
                    st.warning('저장 오류: ' + str(e))
        with cB:
            if st.button('초기화', key=wkey('special_notes_reset')):
                st.session_state['special_notes'] = ''
                try:
                    open(notes_path,'w',encoding='utf-8').write('')
                except Exception:
                    pass

with t_graph:
    mod = _import("ui_results")
    if not (mod and (getattr(mod, "render_graph", None) or getattr(mod, "render", None))):
        st.info("기록/그래프는 ui_results 모듈에서 제공됩니다.")
