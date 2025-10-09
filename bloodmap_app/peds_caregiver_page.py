
# -*- coding: utf-8 -*-
"""
peds_caregiver_page.py
- 보호자 모드: 병명 다중 선택 → 일괄 PDF/ZIP 생성, 미리보기/공유
"""
from typing import List, Optional
import streamlit as st
import inspect


def _safe_branding_banner():
    """Call branding.render_deploy_banner with backward-compatible signature."""
    app_url = "https://bloodmap.streamlit.app"
    made_by = "Hoya/GPT"
    try:
        from branding import render_deploy_banner as _rdb
    except Exception:
        try:
            import streamlit as st
            st.info("제작/자문: Hoya/GPT · ⏱ KST · 혼돈 방지: 세포·면역치료 비표기")
        except Exception:
            pass
        return
    try:
        import inspect
        sig = inspect.signature(_rdb)
        if len(sig.parameters) >= 2:
            _rdb(app_url, made_by)
        else:
            _rdb()
    except TypeError:
        try:
            _rdb(app_url, made_by)
        except Exception:
            try:
                import streamlit as st
                st.info(f"제작/자문: {made_by} · ⏱ KST")
            except Exception:
                pass
    except Exception:
        try:
            import streamlit as st
            st.info("제작/자문: Hoya/GPT · ⏱ KST")
        except Exception:
            pass

def render_caregiver_mode(default_weight_kg: Optional[float]=None):
    st.header("🧩 보호자 모드 — 병명별 안내 묶음")
    _safe_branding_banner()

    names = condition_names()
    picks = st.multiselect("배포할 병명을 선택하세요", names, default=names[:3])
    weight = st.number_input("아이 체중 (kg)", min_value=0.0, step=0.5,
                             value=float(default_weight_kg) if default_weight_kg else 0.0,
                             key="cg_weight")
    add_antipy = st.checkbox("해열제 요약 포함", value=True)

    st.divider()
    if not picks:
        st.info("상단에서 하나 이상 선택하세요.")
        return

    # 미리보기(첫 항목)
    first = picks[0]
    text = (build_share_text(first, weight) if add_antipy else build_text(first))
    st.subheader("미리보기")
    st.write(text)

    # PDF/ZIP 생성
    if export_md_to_pdf:
        pdf_files = []
        for name in picks:
            tex = (build_share_text(name, weight) if add_antipy else build_text(name))
            pdf = export_md_to_pdf(tex)
            pdf_files.append((name, pdf))

        # 개별 다운로드
        st.subheader("개별 PDF 다운로드")
        for name, pdf in pdf_files:
            st.download_button(f"{name}.pdf 저장", data=pdf, file_name=f"{name}.pdf",
                               mime="application/pdf", key=f"dl_{name}")

        # ZIP 묶음
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            for name, pdf in pdf_files:
                z.writestr(f"{name}.pdf", pdf)
        st.download_button("선택 항목 ZIP로 다운로드", data=buf.getvalue(),
                           file_name="caregiver_pack.zip", mime="application/zip",
                           key="dl_zip")
    else:
        st.info("PDF 엔진이 없어 미리보기만 제공됩니다. (pdf_export 모듈 필요)")
