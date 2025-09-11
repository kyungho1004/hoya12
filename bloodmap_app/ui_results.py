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


def render_adverse_effects(st, regimen, DRUG_DB):
    """Render selected drugs' adverse effects; AE line is color-highlighted."""
    if not regimen:
        return
    st.markdown("#### 💊 약물 부작용(요약)")
    for key in regimen:
        info = (DRUG_DB or {}).get(key) or (DRUG_DB or {}).get(str(key or "").lower()) or (DRUG_DB or {}).get((key or "").strip())
        if not info:
            st.write(f"- {key}: 데이터 없음")
            continue
        alias = info.get("alias", key)
        moa = info.get("moa", "")
        ae  = info.get("ae", "")
        _, marked = _mark_risk(ae)
        html = f"""
<div style="margin:10px 0 16px 0; line-height:1.55">
  <div style="font-weight:700">• {key} ({alias})</div>
  {f'<div style="opacity:.85">· <strong>기전/특징:</strong> {moa}</div>' if moa else ''}
  {f'<div>· <strong>주의/부작용:</strong> <span style="color:#c1121f; font-weight:700">{marked}</span></div>' if ae else ''}
</div>
""".strip()
        st.markdown(html, unsafe_allow_html=True)


def _mark_risk(ae_text):
    """Return (flagged_bool, marked_text) where serious/common effects are prefixed with 🚨."""
    if not ae_text:
        return (False, ae_text)
    serious = [
        "분화증후군","QT","torsade","부정맥","심정지","심독성","간부전","췌장염","두개내압",
        "신부전","신독성","폐독성","간독성","무과립구증","패혈증","아나필락시","스티븐스",
        "독성표피괴사","중증 피부반응","출혈","혈전","폐색전증","심낭삼출","흉막삼출","저혈압","호흡곤란"
    ]
    common = [
        "골수억제","중성구감소","빈혈","혈소판감소","간효소 상승","고중성지방혈증",
        "점막염","구내염","오심","구토","피로","발진"
    ]
    txt = ae_text
    low = txt.lower()
    flagged = False
    for kw in serious:
        if kw.lower() in low:
            flagged = True
            txt = re.sub(kw, "🚨 "+kw, txt, flags=re.IGNORECASE)
    for kw in common:
        if kw.lower() in low:
            flagged = True
            txt = re.sub(kw, "🚨 "+kw, txt, count=1, flags=re.IGNORECASE)
    return (flagged, txt)
