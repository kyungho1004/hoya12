"""
Peds ER one-page exporter — snapshot current inputs and create a single-page PDF.
Uses features.pdf_templates + pdf_export or exporters fallback.
"""
from __future__ import annotations

def _collect_ctx(ss) -> dict:
    ctx = {}
    try:
        ctx["title"] = "소아 ER 원페이지"
        ctx["nickname"] = ss.get("nickname") or ss.get("uid") or "-"
        ctx["age_m"] = ss.get("peds_age_m") or "-"
        ctx["wt_kg"] = ss.get("peds_wt_kg") or "-"
        ctx["fever"] = ss.get("last_temp") or ss.get("peds_temp") or "-"
        syms = []
        for k, label in [
            ("peds_sputum","가래"), ("peds_wheeze","쌕쌕"),
            ("peds_stool_color","변 색상"), ("peds_stool_tex","변 질감"),
        ]:
            v = ss.get(k)
            if v:
                syms.append(f"{label}:{v}")
        ctx["symptoms"] = syms
        # try labs if present in session
        labs = {}
        for k, label in [("WBC","WBC"),("Hb","Hb"),("PLT","PLT"),("CRP","CRP"),("ANC","ANC"),
                         ("Na","Na"),("K","K"),("Alb","Albumin"),("Ca","Ca"),("AST","AST"),("ALT","ALT")]:
            v = ss.get(k)
            if v not in (None, ""):
                labs[label] = v
        ctx["labs"] = labs
        ctx["drugs"] = list(ss.get("picked_keys") or [])
    except Exception:
        pass
    return ctx

def render_peds_er_onepage(st):
    try:
        with st.expander("ER 원페이지 PDF (소아)", expanded=False):
            if st.button("PDF 만들기(1장)"):
                from features.pdf_templates import build as _build
                ctx = _collect_ctx(st.session_state)
                els = _build("er_onepage", ctx)
                path = ""
                try:
                    import pdf_export as _pe
                    path = _pe.save_pdf(els, "/mnt/data/exports/er_onepage.pdf", title=ctx.get("title"))
                except Exception:
                    try:
                        from features.exporters import _export_pdf
                        path = _export_pdf(els, "er_onepage.pdf")
                    except Exception:
                        path = ""
                if path:
                    st.success(f"저장됨: {path}")
                    st.write(f"[다운로드]({path})")
    except Exception:
        pass
