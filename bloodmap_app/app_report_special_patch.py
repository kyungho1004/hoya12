# app_report_special_patch.py — bridge for special tests (coalesce + render + debug)
import streamlit as st
from typing import List, Dict, Any

def _coalesce_special_lines() -> List[str]:
    candidates = [
        "special_interpretations",
        "special_lines",
        "special_tests_lines",
        "special_tests.report_lines",
        "special.notes",
    ]
    out: List[str] = []
    for k in candidates:
        v = st.session_state.get(k)
        if isinstance(v, list):
            out.extend([str(x) for x in v if x is not None])
        elif isinstance(v, str) and v.strip():
            out.append(v.strip())
    # dedupe order-preserving
    seen = set(); deduped = []
    for s in out:
        if s not in seen:
            seen.add(s); deduped.append(s)
    return deduped

def bridge_special_to_report() -> List[str]:
    lines = _coalesce_special_lines()
    st.session_state["special_interpretations"] = lines
    return lines

def render_special_report_section(title: str = "## 특수검사 해석(각주 포함)", debug: bool = True) -> None:
    st.markdown(title)
    lines = st.session_state.get("special_interpretations", [])
    if not lines:
        st.info("특수검사 입력은 있었지만 해석 문장이 아직 없습니다. (조건 충족 시 자동 추가되거나, UI 요약이 기록됩니다.)")
    else:
        for s in lines:
            st.write(f"- {s}")
    if debug:
        with st.expander("🔎 특수검사 디버그 보기", expanded=False):
            snapshot: Dict[str, Any] = {
                "special_interpretations": st.session_state.get("special_interpretations"),
                "special_lines": st.session_state.get("special_lines"),
                "special_tests_lines": st.session_state.get("special_tests_lines"),
                "special_tests.report_lines": st.session_state.get("special_tests.report_lines"),
                "special.notes": st.session_state.get("special.notes"),
            }
            st.write(snapshot)
