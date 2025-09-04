
try:
    from ..util_core import build_report, md_to_pdf_bytes_fontlocked
except Exception:
    def build_report(mode, meta, vals, cmp_lines, extra_vals, meds_lines, food_lines, abx_lines):
        title = meta.get("cancer_label") or meta.get("cancer") or ""
        return f"# BloodMap 보고서\n- 모드: {mode}\n- 진단: {title}\n"
    def md_to_pdf_bytes_fontlocked(md_text: str) -> bytes:
        raise RuntimeError("PDF 모듈 없음")
