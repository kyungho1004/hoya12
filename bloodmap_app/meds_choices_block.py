
# -*- coding: utf-8 -*-
"""
meds_choices_block — 약물 선택 UI 블록(견고 로더 내장)
사용법:
    from meds_choices_block import render_drug_selectors
    sel_chemo, sel_tgt, sel_abx = render_drug_selectors(st, uid, group, dx, auto_recs_by_dx)
"""

from __future__ import annotations
from typing import List, Tuple
import streamlit as st

from drug_db_guard import load_choices
from meds_auto_helper import ensure_med_defaults

def _multiselect_labeled(label: str, choices: list[tuple[str,str]], key: str) -> list[str]:
    # choices: [(code, "라벨"), ...]
    opts = [f"{c} — {lbl}" for c, lbl in choices]
    sel  = st.multiselect(label, opts, key=key)
    return [s.split(" — ", 1)[0] for s in sel]

def render_drug_selectors(st, uid: str, group: str, dx: str, auto_recs_by_dx) -> tuple[list[str], list[str], list[str]]:
    # 1) 로드 (drug_db → json 폴백)
    ch = load_choices()
    chemo_choices = ch["chemo"]
    tgt_choices   = ch["tgt"]
    abx_choices   = ch["abx"]

    st.caption(f"선택지: 항암제 {len(chemo_choices)} · 표적·면역 {len(tgt_choices)} · 항생제 {len(abx_choices)}")

    # 2) 자동 추천(멀티셀렉트 렌더 직전 주입)
    freeze_auto = st.toggle("진단 변경 시 자동 추천 적용", value=True, key=f"freeze_auto_{uid}")
    ensure_med_defaults(group, dx, uid, chemo_choices, tgt_choices, abx_choices,
                        auto_recs_by_dx=auto_recs_by_dx, DRUG_DB=None, enable=freeze_auto)

    # 3) 선택 UI
    sel_chemo = _multiselect_labeled("항암제(세포독성)", chemo_choices, key=f"drug_chemo_{uid}")
    sel_tgt   = _multiselect_labeled("표적·면역", tgt_choices, key=f"drug_tgt_{uid}")
    sel_abx   = _multiselect_labeled("항생제", abx_choices, key=f"drug_abx_{uid}")

    if not (chemo_choices or tgt_choices or abx_choices):
        st.error("약물 DB를 찾을 수 없습니다. final_drug_coverage.json 경로를 확인하세요.")
    return sel_chemo, sel_tgt, sel_abx
