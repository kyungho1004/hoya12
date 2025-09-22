
# -*- coding: utf-8 -*-
import streamlit as st

def ensure_med_defaults(group, dx, uid, chemo_choices, tgt_choices, abx_choices, auto_recs_by_dx, DRUG_DB, enable=True):
    """
    멀티셀렉트 위젯을 만들기 전에 호출하세요.
    - group/dx가 바뀌었고 enable=True일 때만 기본값을 세션에 주입합니다.
    - choices 형식: [(code, label), ...]
    - DRUG_DB는 넘기지만 내부에선 예외 방지용으로만 사용.
    """
    if not enable:
        return
    try:
        recs = auto_recs_by_dx(group, dx, DRUG_DB) or {}
    except Exception:
        recs = {}
    d_ch = list(recs.get("chemo") or [])
    d_tg = list((recs.get("targeted") or []) + (recs.get("immuno") or []))
    d_ab = list(recs.get("abx") or [])

    # code -> label 매핑
    label_by_code_chemo = {c:l for c,l in (chemo_choices or [])}
    label_by_code_tgt   = {c:l for c,l in (tgt_choices or [])}
    label_by_code_abx   = {c:l for c,l in (abx_choices or [])}

    def _opt(mapping, codes):
        return [f"{c} — {mapping.get(c, c)}" for c in codes if c in mapping]

    sig = f"{group}::{dx}"
    last_key = f"__last_dx_for_drugs_{uid}"
    if st.session_state.get(last_key) != sig:
        st.session_state[last_key] = sig
        st.session_state[f"drug_chemo_{uid}"] = _opt(label_by_code_chemo, d_ch)
        st.session_state[f"drug_tgt_{uid}"]   = _opt(label_by_code_tgt, d_tg)
        st.session_state[f"drug_abx_{uid}"]   = _opt(label_by_code_abx, d_ab)
