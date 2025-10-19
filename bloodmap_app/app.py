
# -*- coding: utf-8 -*-
from __future__ import annotations

import streamlit as st
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# ---------------- 페이지 설정 & 상단 타이틀 ----------------
APP_VERSION = "항상 여러분들의 힘이 되도록 노력하겠습니다. 여러분들의 피드백이 업데이트에 많은 도움이 됩니다"
st.set_page_config(page_title="Bloodmap", page_icon="🩸", layout="wide")
st.title(f"Bloodmap {APP_VERSION}")
st.caption("Bloodmap 항상 여러분들의 힘이 되도록 노력하겠습니다. 여러분들의 피드백이 업데이트에 많은 도움이 됩니다")

# ---------------- 탭 구성 (요청 순서 고정) ----------------
tab_labels = ["🏠 홈","👶 소아 증상","🧬 암 선택","💊 항암제(진단 기반)","🧪 피수치 입력","🔬 특수검사","📄 보고서","📊 기록/그래프"]
t_home, t_peds, t_dx, t_chemo, t_labs, t_special, t_report, t_graph = st.tabs(tab_labels)

# ================= 공용 유틸/헬퍼 =================
_KST = ZoneInfo("Asia/Seoul")
def wkey(name: str) -> str:
    return f"bm_{name}"

# ---------- PATCH[P0] 해열제 24h 배지(누적/쿨다운) ----------
def _carelog_24h_totals(log=None):
    log = log or st.session_state.get('care_log', [])
    now = datetime.now(_KST)
    since = now - timedelta(hours=24)
    total_apap = 0.0
    total_ibu = 0.0
    last_apap = None
    last_ibu = None
    for rec in (log or []):
        try:
            ts = rec.get('ts')
            if isinstance(ts, str):
                ts = datetime.fromisoformat(ts)
        except Exception:
            ts = None
        if ts and ts < since:
            continue
        drug = (rec.get('drug') or '').lower()
        try:
            mg = float(rec.get('mg') or 0)
        except Exception:
            mg = 0.0
        if 'apap' in drug or 'acetaminophen' in drug or '타이레놀' in drug:
            total_apap += mg
            if ts and (last_apap is None or ts > last_apap):
                last_apap = ts
        if 'ibu' in drug or 'ibuprofen' in drug or '이부프로펜' in drug:
            total_ibu += mg
            if ts and (last_ibu is None or ts > last_ibu):
                last_ibu = ts
    return dict(now=now, total_apap=total_apap, total_ibu=total_ibu, last_apap=last_apap, last_ibu=last_ibu)

def _render_antipyretic_badges():
    info = _carelog_24h_totals()
    weight = st.session_state.get('weight_kg') or 0
    apap_limit = st.session_state.get('apap_24h_limit_mg', 75*weight) or 3000
    apap_limit = max(apap_limit, 3000)
    ibu_limit  = st.session_state.get('ibu_24h_limit_mg', 40*weight) or 1200

    def next_time(last_ts, cooldown_h):
        if not last_ts:
            return None
        return last_ts + timedelta(hours=cooldown_h)

    next_apap = next_time(info['last_apap'], 4)
    next_ibu  = next_time(info['last_ibu'], 6)

    col1, col2, col3 = st.columns([1,1,2])
    with col1:
        st.metric('APAP 24h 누적', f"{info['total_apap']:.0f} mg", f"남음 {max(0, apap_limit - info['total_apap']):.0f} mg")
    with col2:
        st.metric('IBU 24h 누적', f"{info['total_ibu']:.0f} mg", f"남음 {max(0, ibu_limit - info['total_ibu']):.0f} mg")
    with col3:
        line = []
        if next_apap: line.append(f"APAP 다음 가능: {next_apap.strftime('%H:%M')}")
        if next_ibu:  line.append(f"IBU 다음 가능: {next_ibu.strftime('%H:%M')}")
        st.caption(' · '.join(line) if line else '최근 복용 기록 없음')
    if info['total_apap'] >= apap_limit or info['total_ibu'] >= ibu_limit:
        st.warning('🚨 24시간 총량 한도를 초과했습니다. 복용을 중단하고 의료진과 상의하세요.')
    elif info['total_apap'] >= apap_limit*0.8 or info['total_ibu'] >= ibu_limit*0.8:
        st.info('⚠️ 24시간 총량의 80%를 넘었습니다. 중복 성분(복합감기약 포함) 주의하세요.')

# ---------- PATCH[P1] 소아 Sticky Quick-Nav ----------
def _peds_sticky_nav():
    st.markdown(
        """
        <style>
        .peds-sticky{position:sticky; top:64px; z-index:9; background:rgba(250,250,250,0.9);
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
        """,
        unsafe_allow_html=True
    )

# ---------- PATCH[P1] ORS 가이드 PDF “직접 저장” 버튼 (list -> str join fix) ----------
def _render_ors_pdf_button():
    """
    pdf_export.export_md_to_pdf()를 문자열 입력으로 호출하여 /mnt/data/ORS_guide.pdf 로 저장 후
    즉시 다운로드 버튼 제공.
    """
    if st.button('ORS 가이드 PDF 저장', key=wkey('ors_pdf_btn')):
        try:
            import pdf_export as _pdf
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
            md = "\n".join(lines)               # ✅ 리스트를 문자열로 변환
            pdf_bytes = _pdf.export_md_to_pdf(md)
            save_path = "/mnt/data/ORS_guide.pdf"
            # ensure directory exists; fallback to current dir if needed
            import os
            try:
                os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
                with open(save_path, "wb") as f:
                    f.write(pdf_bytes)
            except Exception:
                save_path = "ORS_guide.pdf"
                with open(save_path, "wb") as f:
                    f.write(pdf_bytes)
            with open(save_path, "rb") as f:
                st.download_button(
                    "PDF 다운로드", f,
                    file_name="ORS_guide.pdf",
                    mime="application/pdf",
                    key=wkey('ors_pdf_dl')
                )
            st.success(f"ORS 가이드 PDF 저장 완료: {save_path}")
        except Exception as e:
            st.error(f"PDF 생성 실패: {e}")

# ======================= 탭 렌더 =======================

with t_home:
    _render_antipyretic_badges()
    st.write("홈 콘텐츠(기존 내용 유지)")  # 자리표시자

with t_peds:
    _peds_sticky_nav()
    # 실제 ORS/탈수 가이드 expander 내부에 이 버튼을 넣고 싶다면,
    # 해당 expander 블록 안쪽에서 _render_ors_pdf_button() 호출로 이동 가능.
    _render_ors_pdf_button()
    _render_antipyretic_badges()
    st.write("소아 탭 콘텐츠(기존 내용 유지)")  # 자리표시자

with t_dx:
    st.write("암 선택 탭(기존 내용 유지)")

with t_chemo:
    st.write("항암제(진단 기반) 탭(기존 내용 유지)")

with t_labs:
    st.write("피수치 입력 탭(기존 내용 유지)")

with t_special:
    st.write("특수검사 탭(기존 내용 유지)")

with t_report:
    # ----- ER 원페이지 PDF (기존 구현과 호환) -----
    try:
        import pdf_export as _pdf
    except Exception:
        _pdf = None
    st.markdown("### 🏥 ER 원페이지 PDF")
    if st.button("ER 원페이지 PDF 만들기", key=wkey("er_pdf_btn")):
        try:
            import pdf_export as _pdf
        except Exception:
            _pdf = None
        try:
            path = None
            if _pdf and hasattr(_pdf, "export_er_onepager"):
                path = _pdf.export_er_onepager(st.session_state)
            elif _pdf and hasattr(_pdf, "build_er_onepager"):
                path = _pdf.build_er_onepager(st.session_state)
            if not path and _pdf and hasattr(_pdf, "export_md_to_pdf"):
                lines_md = [
                    "# ER 원페이지 요약",
                    "- 환자 기본정보: 보고서 상단 요약을 여기에 정리",
                    "- 최근 주요 피수치: WBC/Hb/Plt, ANC, Cr/eGFR 등",
                    "- 최근 복약/케어 포인트: 해열제, 수분 섭취, ORS 권고",
                    "- 경고 신호: 2시간 무뇨·입마름·눈물 감소·축 늘어짐 등",
                    "- 연락처/다음 내원: 담당자/병동/응급실 번호",
                ]
                md = "\n".join(lines_md)
                pdf_bytes = _pdf.export_md_to_pdf(md)
                save_path = "/mnt/data/ER_onepage.pdf"
                import os
                try:
                    os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
                    with open(save_path, "wb") as f:
                        f.write(pdf_bytes)
                    path = save_path
                except Exception:
                    with open("ER_onepage.pdf", "wb") as f:
                        f.write(pdf_bytes)
                    path = "ER_onepage.pdf"
            if path:
                with open(path, "rb") as f:
                    st.download_button("PDF 다운로드", f,
                        file_name="bloodmap_ER_onepage.pdf",
                        mime="application/pdf",
                        key=wkey("er_pdf_dl"))
                st.success("ER 원페이지 PDF 저장 완료: " + str(path))
            else:
                st.info("pdf_export 모듈에서 원페이지 함수를 찾지 못했고, 폴백 생성도 실패했습니다.")
        except Exception as e:
            st.warning("ER PDF 생성 중 오류: " + str(e))
    # ----- Special Notes (환자별 메모) -----
    with st.expander('📝 Special Notes (환자별 메모)', expanded=False):
        import os
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
        colA, colB = st.columns([1,1])
        with colA:
            if st.button('저장', key=wkey('special_notes_save')):
                try:
                    open(notes_path,'w',encoding='utf-8').write(val or '')
                    st.session_state['special_notes'] = val or ''
                    st.success('저장 완료')
                except Exception as e:
                    st.warning('저장 오류: ' + str(e))
        with colB:
            if st.button('초기화', key=wkey('special_notes_reset')):
                st.session_state['special_notes'] = ''
                try:
                    open(notes_path,'w',encoding='utf-8').write('')
                except Exception:
                    pass
    st.write("보고서 탭(기존 내용 유지)")

with t_graph:
    st.write("기록/그래프 탭(기존 내용 유지)")