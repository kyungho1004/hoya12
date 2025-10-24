
"""
Pediatric wire-ups: safely call pediatric tools from existing modules without top-level imports.
- Tries to call UI helpers if present (non-breaking if missing)
- Provides graceful fallback mini UIs for dosing and fever guidance when upstream UIs are absent.
"""
from __future__ import annotations

# ---------- Fallback mini UIs (no external deps) ----------
def _fallback_antipyretic_ui(st) -> bool:
    """Returns True if rendered. Simple informational calculator with guardrails.
    Prefers peds_dose APIs when available; otherwise uses common reference ranges."""
    try:
        with st.expander("소아 해열제 계산 (fallback, β)", expanded=False):
            col1, col2, col3 = st.columns([1,1,1])
            with col1:
                wt = st.number_input("체중(kg)", min_value=2.0, max_value=100.0, value=15.0, step=0.5, format="%.1f")
            with col2:
                drug = st.selectbox("약물", ["Acetaminophen(아세트아미노펜)", "Ibuprofen(이부프로펜)"])
            with col3:
                conc = st.text_input("시럽 농도 (mg/5mL)", value="160", help="예: 160 → 160mg/5mL 제제")

            # Prefer peds_dose if it exposes a compute API
            used_pd = False
            try:
                import peds_dose as _pd
                for name in ("compute_antipyretic_dose", "calc_antipyretic_dose", "dose_antipyretic_mg_per_dose"):
                    fn = getattr(_pd, name, None)
                    if callable(fn):
                        res = fn(weight_kg=wt, drug="apap" if drug.startswith("Acet") else "ibu")
                        # expect dict with mg_per_dose, min_interval_h, max_daily_mg, comment
                        mg = float(res.get("mg_per_dose", 0.0))
                        min_h = int(res.get("min_interval_h", 4 if drug.startswith("Acet") else 6))
                        max_day = res.get("max_daily_mg")
                        st.markdown(f"**권장 1회 용량:** {mg:.0f} mg")
                        try:
                            c = float(conc or "0")
                        except Exception:
                            c = 0.0
                        if c > 0:
                            mL = mg / (c/5.0)
                            st.markdown(f"**시럽 환산:** {mL:.1f} mL (농도 {c} mg/5mL 기준)")
                        st.caption(f"최소 간격 {min_h}시간 • 최대 1일 용량: {max_day if max_day else '제품 라벨 참조'}")
                        used_pd = True
                        break
            except Exception:
                pass

            if not used_pd:
                # Fallback references (informational, not medical advice)
                # APAP: 10–15 mg/kg q4–6h, max 75 mg/kg/day (일반 참고)
                # IBU: 10 mg/kg q6–8h, max 40 mg/kg/day (≥6 months)
                if drug.startswith("Acet"):
                    mg_per_kg = 12.5  # mid-point
                    min_interval_h = 4
                    max_mg_per_kg_day = 75
                    note = "일반 참고치: 10–15 mg/kg q4–6h, 하루 최대 75 mg/kg"
                else:
                    mg_per_kg = 10.0
                    min_interval_h = 6
                    max_mg_per_kg_day = 40
                    note = "일반 참고치: 10 mg/kg q6–8h, 하루 최대 40 mg/kg (6개월 이상)"
                mg = mg_per_kg * wt
                st.markdown(f"**권장 1회 용량(참고):** 약 {mg:.0f} mg")
                try:
                    c = float(conc or "0")
                except Exception:
                    c = 0.0
                if c > 0:
                    mL = mg / (c/5.0)
                    st.markdown(f"**시럽 환산:** {mL:.1f} mL (농도 {c} mg/5mL 기준)")
                st.caption(f"최소 간격 {min_interval_h}시간 • 1일 최대 {max_mg_per_kg_day} mg/kg — {note}")
                st.info("※ 의료 자문을 대체하지 않습니다. 개별 제품 라벨을 확인하세요.", icon="ℹ️")
            return True
    except Exception:
        return False

def _fallback_fever_guide_ui(st) -> bool:
    try:
        with st.expander("발열 관리 가이드 (fallback, β)", expanded=False):
            st.markdown("""
- **수분 보충**: ORS/미온수 • 탈수 징후 시 빈도↑  
- **환경**: 가볍게 입히고, 과열 피하기  
- **해열제**: 교차·과량 금지, 최소 간격 준수(APAP ≥4h / IBU ≥6h)  
- **즉시 연락/내원**: 3개월 미만 발열, **경련/의식저하/호흡곤란**, 지속 구토, 탈수, **48–72h 이상 지속 고열**
            """)
            return True
    except Exception:
        return False

# ---------- Public wire-up ----------
def render_peds_tools(st) -> None:
    """
    Compact pediatric section:
    - Prefer upstream UIs; if not found, render fallbacks.
    """
    try:
        with st.expander("소아 도구 모음 (β)", expanded=False):
            rendered_any = False
            # Try peds_dose UI
            try:
                import peds_dose as _pd
                for _name in (
                    "render_peds_dose_ui",
                    "render_antipyretic_ui",
                    "render_peds_tools",
                ):
                    fn = getattr(_pd, _name, None)
                    if callable(fn):
                        fn(st)
                        rendered_any = True
                        break
            except Exception:
                pass
            # Try peds_guide UI
            try:
                import peds_guide as _pg
                for _name in (
                    "render_peds_fever_guide",
                    "render_fever_guide",
                    "render_peds_guide",
                ):
                    fn = getattr(_pg, _name, None)
                    if callable(fn):
                        fn(st)
                        rendered_any = True
                        break
            except Exception:
                pass

            # Fallbacks if nothing rendered
            if not rendered_any:
                ok1 = _fallback_antipyretic_ui(st)
                ok2 = _fallback_fever_guide_ui(st)
                if not (ok1 or ok2):
                    st.info("기존 소아 모듈에서 노출된 UI 함수를 찾지 못했습니다.")
    except Exception:
        # Never break parent UI
        pass
