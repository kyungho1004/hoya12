"""
Pediatric fever & antipyretic helper (non-intrusive).
- Delegates to peds_dose if available (APAP/IBU ml calc).
- Respects existing guardrails (no scheduling logic here).
"""
from __future__ import annotations
from typing import Optional

def _calc_apap(age_months: float, weight_kg: Optional[float]):
    try:
        import peds_dose as _pd
        ml, est_w = _pd.acetaminophen_ml(age_months, weight_kg)
        return ml, est_w
    except Exception:
        return None, None

def _calc_ibu(age_months: float, weight_kg: Optional[float]):
    try:
        import peds_dose as _pd
        ml, est_w = _pd.ibuprofen_ml(age_months, weight_kg)
        return ml, est_w
    except Exception:
        return None, None

def render_peds_fever(st):
    try:
        with st.expander("소아 해열제(보호자용, β)", expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                age_m = st.number_input("나이(개월)", min_value=0.0, step=1.0, key="peds_age_m")
                wt = st.number_input("몸무게(kg, 선택)", min_value=0.0, step=0.1, key="peds_wt_kg")
                wt = wt if wt > 0 else None
            with c2:
                st.markdown("- **아세트아미노펜(APAP)**: 4시간 간격 이상")
                st.markdown("- **이부프로펜(IBU)**: 6시간 간격 이상")
                st.caption("※ 24시간 총량 가드레일은 기존 시스템에서 관리됩니다. 여기서는 용량 참고만 제공합니다.")

            apap_ml, est_w = _calc_apap(age_m, wt)
            ibu_ml, _ = _calc_ibu(age_m, wt)
            if apap_ml is not None or ibu_ml is not None:
                st.markdown("#### 권장 용량(시럽 mL)")
                st.markdown(f"- APAP: **{apap_ml} mL**" if apap_ml is not None else "- APAP: 계산 불가")
                st.markdown(f"- IBU: **{ibu_ml} mL**" if ibu_ml is not None else "- IBU: 계산 불가")
                if est_w:
                    st.caption(f"(계산에 사용된 체중: 약 {est_w} kg)")
            st.markdown("---")
            st.markdown("**연락 필요(발열 가드)**")
            st.markdown("- 38.5°C 이상 지속, 처치에도 호전 없을 때")
            st.markdown("- 39.0°C 이상이거나, 경련·의식저하 동반 시 즉시 연락")
    except Exception:
        pass
