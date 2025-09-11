import re
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
        st.write(f"- **{key} ({alias})**")
        if moa: st.caption(f"  · 기전/특징: {moa}")
        if ae:  st.caption(f"  · 주의/부작용: {ae}")

def _mark_risk(ae_text: str):
    if not ae_text: return (False, ae_text)
    serious = ["분화증후군","QT","torsade","부정맥","심정지","심독성","간부전","췌장염","신부전","신독성","폐독성","간독성","무과립구증","패혈증","아나필락시","스티븐스","독성표피괴사","중증 피부반응","출혈","혈전","폐색전증","심낭삼출","흉막삼출","저혈압","호흡곤란"]
    common  = ["골수억제","중성구감소","빈혈","혈소판감소","간효소 상승","고중성지방혈증","점막염","구내염","오심","구토","피로","발진"]
    txt = ae_text; low = txt.lower(); flagged = False
    for kw in serious:
        if kw.lower() in low:
            flagged = True; txt = re.sub(kw, "🚨 "+kw, txt, flags=re.IGNORECASE)
    for kw in common:
        if kw.lower() in low:
            flagged = True; txt = re.sub(kw, "🚨 "+kw, txt, count=1, flags=re.IGNORECASE)
    return (flagged, txt)


def build_report_md(ctx, labs, diet_lines, regimen, DRUG_DB):
    lines = []
    lines.append("# BloodMap 결과 보고서")
    lines.append("[피수치 가이드 공식카페 바로가기](https://cafe.naver.com/bloodmap)")
    lines.append("제작 Hoya/GPT · 자문 Hoya/GPT")
    lines.append("")
    mode = (ctx or {}).get("mode", "-")
    if mode == "암":
        dx_label = (ctx or {}).get("dx_label") or ""
        if dx_label:
            lines.append(f"**진단:** {dx_label}")
            lines.append("")
    elif mode == "소아":
        lines.append("**소아 모드 결과**")
        lines.append("")
    if labs:
        lines.append("## 피수치 요약")
        for k, v in labs.items():
            lines.append(f"- {k}: {v if v is not None else ''}")
        lines.append("")
    if diet_lines:
        lines.append("## 식이가이드")
        for L in diet_lines:
            lines.append(f"- {L}")
        lines.append("")
    if mode == "암" and regimen:
        lines.append("## 약물 부작용(요약) — 선택 항암제")
        for key in regimen:
            info = (DRUG_DB or {}).get(key) or (DRUG_DB or {}).get(str(key or '').lower()) or (DRUG_DB or {}).get((key or '').strip())
            if not info:
                lines.append(f"- {key}: 데이터 없음"); continue
            alias = info.get("alias", key); moa = info.get("moa", ""); ae = info.get("ae", "")
            lines.append(f"- **{key} ({alias})**")
            if moa: lines.append(f"  - 기전/특징: {moa}")
            if ae:  lines.append(f"  - 주의/부작용: {ae}")
        lines.append("")
    lines.append("---")
    lines.append("본 수치는 참고용이며, 해석 결과는 개발자와 무관합니다.")
    lines.append("약 변경, 복용 중단 등은 반드시 주치의와 상의 후 결정하시기 바랍니다.")
    lines.append("이 앱은 개인정보를 절대 수집하지 않으며, 어떠한 개인정보 입력도 요구하지 않습니다.")
    lines.append("")
    lines.append("문의나 버그 제보는 공식카페로 해주시면 감사합니다: https://cafe.naver.com/bloodmap")
    return "\n".join(lines)

def download_report_buttons(st, md_text: str):
    st.markdown("---")
    st.markdown("#### 📥 보고서 다운로드")
    st.download_button(label="⬇️ .md 저장", data=md_text, file_name="bloodmap_report.md", mime="text/markdown")
    st.download_button(label="⬇️ .txt 저장", data=md_text, file_name="bloodmap_report.txt", mime="text/plain")
