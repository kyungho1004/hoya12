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


def render_exports(st, ctx: Dict[str, Any]):
    from io import StringIO
    import datetime
    lines = []
    lines.append('# 피수치 해석 보고서')
    lines.append('- 생성시각: ' + str(datetime.datetime.now()))
    lines.append('- 모드: ' + str(ctx.get('mode','-')))
    lines.append('- 진단: ' + str(ctx.get('dx_label','-')))
    labs = ctx.get('labs') or {}
    if labs:
        lines.append('## 입력한 수치')
        for k,v in labs.items():
            lines.append(f'- {k}: {v}')
    md = '\n'.join(lines)
    st.download_button('📥 보고서(.md) 다운로드', md, file_name='report.md', mime='text/markdown')
    st.download_button('📥 보고서(.txt) 다운로드', md, file_name='report.txt', mime='text/plain')
    st.caption('PDF 내보내기는 추후 활성화됩니다.')
