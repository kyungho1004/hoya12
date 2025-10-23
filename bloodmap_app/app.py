# [ULTRA-GUARD] prevent unintended 'home' render on first rerun
try:
    import streamlit as st
    ss = st.session_state
    # Prefer URL route if present
    try:
        url_r = st.query_params.get("route")
        url_r = url_r[0] if isinstance(url_r, list) else url_r
    except Exception:
        url_r = (st.experimental_get_query_params().get("route") or [""])[0]
    if url_r and ss.get("_route") != url_r:
        ss["_route"] = url_r
        ss["_route_last"] = url_r
        st.rerun()
    # If dropping to home without explicit intent, restore last or 'dx'
    if ss.get("_route") == "home" and not ss.get("_home_intent", False):
        target = ss.get("_route_last") or "dx"
        if target != "home":
            ss["_route"] = target
            try:
                if st.query_params.get("route") != target:
                    st.query_params.update(route=target)
            except Exception:
                st.experimental_set_query_params(route=target)
            st.rerun()
except Exception:
    pass


import streamlit as st
from typing import Dict, Any, List

from drug_db import ensure_onco_drug_db

# ---- Route guard to prevent unintended 'home' bounce ----
def _route_guard_pre(default_route: str = "chemo"):
    """Rerun 중 의도치 않은 'home' 하강을 막고 최근 작업 탭으로 복원."""
    try:
        ss = st.session_state
        # 쿼리 파라미터 route 파싱 (신/구 API 모두 대응)
        try:
            qp = st.query_params
            url_route = qp.get("route")
            if isinstance(url_route, list):
                url_route = url_route[0] if url_route else ""
        except Exception:
            try:
                url_route = (st.experimental_get_query_params().get("route") or [""])[0]
            except Exception:
                url_route = ""

        cur  = ss.get("_route") or url_route or default_route
        last = ss.get("_route_last")
        intent_home = ss.get("_home_intent", False)

        # 작업 컨텍스트가 있으면 home 하강 금지
        has_ctx = bool(
            ss.get("picked_keys") or
            ss.get("selected_cancer") or
            ss.get("selected_drug") or
            ss.get("picked_cancer")
        )
        if (cur == "home") and (not intent_home) and (has_ctx or (last and last != "home")):
            cur = last or default_route

        ss["_route"] = cur
        if cur != "home":
            ss["_route_last"] = cur

        # URL 쿼리 파라미터 동기화
        try:
            if st.query_params.get("route") != cur:
                st.query_params.update(route=cur)
        except Exception:
            try:
                st.experimental_set_query_params(route=cur)
            except Exception:
                pass

    except Exception:
        # 최종 안전장치
        pass


def _load_db() -> Dict[str, Dict[str, Any]]:
    db: Dict[str, Dict[str, Any]] = {}
    ensure_onco_drug_db(db)
    return db


def main():
    st.set_page_config(page_title="피수치 항암제 부작용", layout="wide")
    st.title("피수치 · 항암제 부작용")


    DRUG_DB = _load_db()
    all_keys = sorted(list(DRUG_DB.keys()))
    default_pick = [k for k in all_keys if ("Cytarabine" in k or "Ara-C" in k)][:1]

    picked_labels = st.multiselect("선택 약물", options=[DRUG_DB[k].get("alias", k) for k in all_keys],
                                   default=[DRUG_DB[k].get("alias", k) for k in default_pick])
    label_to_key = {DRUG_DB[k].get("alias", k): k for k in all_keys}
    picked_keys: List[str] = [label_to_key.get(lbl) for lbl in picked_labels if lbl in label_to_key]
    st.session_state["picked_keys"] = picked_keys
    # 탭 유지 힌트
    st.session_state["_route_last"] = "chemo"

    # ---- AE Section ----
    _route_guard_pre()  # 헤더 바로 위에서 라우트 고정
    st.markdown("### 항암제 부작용(전체)")
    _used_shared_renderer = False  # NameError 방지 초기화

    # 공용 렌더러 우선
    _render_aes_shared = None
    try:
        from ui_results_final import render_adverse_effects as _render_aes_shared
    except Exception:
        try:
            from ui_results import render_adverse_effects as _render_aes_shared
        except Exception:
            _render_aes_shared = None

    if _render_aes_shared is not None:
        try:
            _render_aes_shared(st, picked_keys, DRUG_DB)
            _used_shared_renderer = True
        except Exception:
            _used_shared_renderer = False

    # 폴백 간단보기
    if not _used_shared_renderer:
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
