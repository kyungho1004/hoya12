# -*- coding: utf-8 -*-
from typing import Dict, List, Any, Tuple

def results_only_after_analyze(st) -> bool:
    if st.session_state.get("analyzed"):
        st.divider()
        st.markdown("## 결과")
        st.caption("아래에는 피수치 해석과 식이가이드, 약물 부작용만 표시합니다.")
        return True
    return False


def render_adverse_effects(st, regimen: List[str], DRUG_DB: Dict[str, Dict[str, Any]]) -> None:
    if not regimen:
        return
    st.markdown("#### 💊 약물 부작용(요약)")
    for key in regimen:
        info = (DRUG_DB or {}).get(key) or (DRUG_DB or {}).get(key.lower()) or (DRUG_DB or {}).get((key or "").strip())
        if not info:
            st.write(f"- {key}: 데이터 없음")
            continue
        alias = info.get("alias", key)
        moa = info.get("moa", "")
        ae  = info.get("ae", "")
        # 굵고 선명하게(색은 기본 다크 텍스트). Streamlit 마크다운 HTML 허용.
        html = f"""
<div style="margin: 8px 0 14px 0; line-height:1.5">
  <div><strong>• {key} ({alias})</strong></div>
  {f'<div style="opacity:.85">· <strong>기전/특징:</strong> {moa}</div>' if moa else ''}
  {f'<div><strong>· 주의/부작용:</strong> {ae}</div>' if ae else ''}
</div>
""".strip()
        st.markdown(html, unsafe_allow_html=True)

def build_report_md(ctx: Dict[str, Any], labs: Dict[str, Any], diet_lines: List[str], regimen: List[str], DRUG_DB: Dict[str, Dict[str, Any]]) -> str:
    """간단 .md 보고서 빌더 (상단 링크/크레딧, 하단 문의 포함)."""
    lines = []
    # 상단
    lines.append("# BloodMap 결과 보고서")
    lines.append("[피수치 가이드 공식카페 바로가기](https://cafe.naver.com/bloodmap)")
    lines.append("제작 Hoya/GPT · 자문 Hoya/GPT")
    lines.append("")
    # 진단/모드
    mode = ctx.get("mode", "-")
    if mode == "암":
        if ctx.get("dx_label"):
            lines.append(f"**진단:** {ctx.get('dx_label')}")
        lines.append("")
    elif mode == "소아":
        lines.append("**소아 모드 결과**")
        lines.append("")
    # 피수치 요약
    if labs:
        lines.append("## 피수치 요약")
        for k, v in labs.items():
            lines.append(f"- {k}: {v if v is not None else ''}")
        lines.append("")
    # 식이가이드
    if diet_lines:
        lines.append("## 식이가이드")
        for L in diet_lines:
            lines.append(f"- {L}")
        lines.append("")
    # 약물 부작용 (선택 항암제)
    if mode == "암" and regimen:
        lines.append("## 약물 부작용(요약) — 선택 항암제")
        for key in regimen:
            info = (DRUG_DB or {}).get(key) or (DRUG_DB or {}).get(key.lower()) or (DRUG_DB or {}).get((key or "").strip())
            if not info:
                lines.append(f"- {key}: 데이터 없음")
                continue
            alias = info.get("alias", key)
            moa = info.get("moa", "")
            ae  = info.get("ae", "")
            lines.append(f"- **{key} ({alias})**")
            if moa: lines.append(f"  - 기전/특징: {moa}")
            if ae:  lines.append(f"  - 주의/부작용: {ae}")
        lines.append("")
    # 하단 문구
    lines.append("---")
    lines.append("본 수치는 참고용이며, 해석 결과는 개발자와 무관합니다.")
    lines.append("약 변경, 복용 중단 등은 반드시 주치의와 상의 후 결정하시기 바랍니다.")
    lines.append("이 앱은 개인정보를 절대 수집하지 않으며, 어떠한 개인정보 입력도 요구하지 않습니다.")
    lines.append("")
    lines.append("문의나 버그 제보는 공식카페로 해주시면 감사합니다: https://cafe.naver.com/bloodmap")
    return "
".join(lines)

def download_report_buttons(st, md_text: str):
    """화면 하단에 .md / .txt 동시 다운로드 버튼 제공"""
    st.markdown("---")
    st.markdown("#### 📥 보고서 다운로드")
    st.download_button(label="⬇️ .md 저장", data=md_text, file_name="bloodmap_report.md", mime="text/markdown")
    st.download_button(label="⬇️ .txt 저장", data=md_text, file_name="bloodmap_report.txt", mime="text/plain")
