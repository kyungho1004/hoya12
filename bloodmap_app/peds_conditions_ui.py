
# -*- coding: utf-8 -*-
"""
peds_conditions_ui.py
- Streamlit UI for pediatric condition guides
(개선) PDF 내보내기, 체중 기반 해열제 요약, QR(선택) 버튼 추가
"""
from typing import Optional
import streamlit as st

try:
    from branding import render_deploy_banner  # 프로젝트 배너(제작/자문/KST/비표기 고지)
except Exception:
    def render_deploy_banner():
        st.info("제작/자문: Hoya/GPT · ⏱ KST · 혼돈 방지: 세포·면역치료 비표기")

from peds_conditions import condition_names, build_text, build_share_text
# 선택: peds_dose가 있으면 mL 계산에 활용
try:
    import peds_dose
except Exception:
    peds_dose = None

# 선택: qrcode가 있으면 QR 생성
try:
    import qrcode
    QR_OK = True
except Exception:
    QR_OK = False

# 선택: PDF 내보내기
try:
    from pdf_export import export_md_to_pdf
except Exception:
    export_md_to_pdf = None

def _dosing_note_ml(weight_kg: Optional[float]) -> str:
    """peds_dose 모듈이 있으면 mL 안내까지, 없으면 mg 기준만."""
    if not weight_kg or weight_kg <= 0:
        return ""
    apap_mg_min = round(weight_kg * 10)
    apap_mg_max = round(weight_kg * 15)
    ibu_mg = round(weight_kg * 10)
    extra = ""
    # peds_dose에 농도 테이블이 있으면 mL 환산
    try:
        if peds_dose and hasattr(peds_dose, "to_ml"):
            apap_ml = peds_dose.to_ml("APAP", apap_mg_min, apap_mg_max)
            ibu_ml = peds_dose.to_ml("IBU", ibu_mg, ibu_mg)
            extra = f"\n- (참고 mL) APAP {apap_ml} / IBU {ibu_ml}"
    except Exception:
        pass
    return (f"\n\n• 해열제 요약(체중 {weight_kg:.1f}kg 기준):\n"
            f"- APAP: {apap_mg_min}~{apap_mg_max} mg/회 (≥4h)\n"
            f"- IBU: 약 {ibu_mg} mg/회 (≥6h, 생후 6개월 미만 지양){extra}\n"
            f"- 24h 총량/성분중복 확인, 다음 복용 .ics는 앱의 케어로그를 이용하세요.")

def render_peds_conditions_page(default_weight_kg: Optional[float]=None):
    st.header("👶 소아 병명별 한눈에 가이드")
    render_deploy_banner()

    st.caption("보호자 친화 요약 · 참고용 · 최종 판단은 의료진에게")
    name = st.selectbox("병명을 선택하세요", condition_names(), key="peds_cond_name")
    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        weight = st.number_input("아이 체중 (kg)", min_value=0.0, step=0.5,
                                 value=float(default_weight_kg) if default_weight_kg else 0.0,
                                 key="peds_cond_weight")
    with col2:
        add_antipy = st.checkbox("해열제 요약 포함", value=True, key="peds_cond_addapy")
    with col3:
        add_ml = st.checkbox("mL 환산(가능 시)", value=True, key="peds_cond_addml")

    st.divider()
    if add_antipy:
        text = build_share_text(name, weight if weight>0 else None)
        # 추가 mL 안내
        if add_ml:
            text += _dosing_note_ml(weight if weight>0 else None)
    else:
        text = build_text(name)

    st.subheader("요약 보기")
    st.write(text)

    # 공유/다운로드 (TXT)
    st.download_button("요약 텍스트 다운로드 (.txt)", data=text.encode('utf-8'),
                       file_name=f"{name}_가이드.txt", mime="text/plain",
                       key="peds_cond_dl")

    # PDF 내보내기
    if export_md_to_pdf:
        pdf_bin = export_md_to_pdf(text)
        st.download_button("PDF로 내보내기", data=pdf_bin, file_name=f"{name}_가이드.pdf",
                           mime="application/pdf", key="peds_cond_pdf")
    else:
        st.info("PDF 엔진이 없어 TXT로만 저장됩니다. (pdf_export 모듈 필요)")

    # QR 코드 (선택): 배포시 base_url만 바꾸면 공유 링크 인코딩 가능
    base_url = st.text_input("공유용 링크(배포 후 수정하세요)", value="https://bloodmap.streamlit.app/guide")
    share_url = f"{base_url}?name={name}"
    if QR_OK:
        btn = st.button("공유용 QR 만들기", key="peds_qr_btn")
        if btn:
            img = qrcode.make(share_url)
            st.image(img, caption="QR — 카메라로 스캔하여 열기")
    else:
        st.caption("QR 라이브러리가 없어 버튼을 숨겼습니다. (qrcode 설치 시 자동 표시)")

    st.caption("복사 후 카카오톡/문자에 붙여넣어 공유하세요. (도메인 없이도 가능)")
