
import streamlit as st
from typing import Dict, Any, List

# Expect these to exist in your project
from drug_db import ensure_onco_drug_db
try:
    from ui_results_final import render_adverse_effects as _render_aes_shared  # prefer final module if present
except Exception:
    try:
        from ui_results import render_adverse_effects as _render_aes_shared  # fallback to legacy ui_results
    except Exception:
        _render_aes_shared = None

def _load_db() -> Dict[str, Dict[str, Any]]:
    db: Dict[str, Dict[str, Any]] = {}
    ensure_onco_drug_db(db)
    return db

def main():
    st.set_page_config(page_title="피수치 항암제 부작용", layout="wide")
    st.title("피수치 · 항암제 부작용")

    DRUG_DB = _load_db()

    # 실제 프로젝트에서는 기존의 picked_keys 로직을 그대로 사용하세요.
    # 여기서는 데모로 가장 흔한 키만 고릅니다.
    all_keys = sorted(list(DRUG_DB.keys()))
    default_pick = [k for k in all_keys if ("Cytarabine" in k or "Ara-C" in k)][:1]
    picked_keys: List[str] = st.multiselect("선택 약물", options=all_keys, default=default_pick)

    # --- AE 섹션 ---
    st.markdown("### 항암제 부작용(전체)")

    # 1) 공용 렌더러 먼저
    _used_shared_renderer = False
    if _render_aes_shared is not None:
        try:
            _render_aes_shared(st, picked_keys, DRUG_DB)
            _used_shared_renderer = True
        except Exception:
            _used_shared_renderer = False

    # 2) 폴백: 아주 간단한 요약 렌더 (프로젝트의 기존 블록을 여기에 두세요)
    if not _used_shared_renderer:
        st.info("공용 렌더러를 불러오지 못해 간단 보기로 대체합니다.")
        if not picked_keys:
            st.caption("선택된 항암제가 없습니다.")
            return
        for k in picked_keys:
            rec = DRUG_DB.get(k, {})
            alias = rec.get("alias", k)
            st.write(f"- **{alias}**")
            ae = rec.get("ae", "")
            st.caption(ae if ae else "(요약 부작용 정보가 없습니다)")
            st.divider()

if __name__ == "__main__":
    main()
