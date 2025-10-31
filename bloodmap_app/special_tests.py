
# special_tests.py — fixed (safe keys, no recursive monkeypatch), v5
import streamlit as st
import re
from typing import List, Optional

SPECIAL_TESTS_VERSION = "fixed-v5"

def _stable_uid() -> str:
    uid = st.session_state.get("_uid")
    if uid:
        return str(uid)
    base = st.session_state.get("key", "guest#unknown")
    return "guest_" + re.sub(r'[^a-zA-Z0-9_.-]', '_', str(base))

def _slug(x: str) -> str:
    return re.sub(r'[^a-zA-Z0-9_.-]+', '_', str(x)).strip('_') or "x"

def _sec_ns(sec_id: Optional[str]) -> str:
    sid = _slug(sec_id or "root")
    return f"{_stable_uid()}.special.v5.{sid}"

st.session_state["_sp_run_tick"] = st.session_state.get("_sp_run_tick", 0) + 1
if st.session_state.get("_sp_used_tick") != st.session_state["_sp_run_tick"]:
    st.session_state["_sp_used_tick"] = st.session_state["_sp_run_tick"]
    st.session_state["_sp_used_keys"] = set()

def _mint_key(base: str) -> str:
    used = st.session_state["_sp_used_keys"]
    if base not in used:
        used.add(base)
        return base
    i = 2
    while True:
        k = f"{base}.dup{i}"
        if k not in used:
            used.add(k)
            return k
        i += 1

def _tog_key(sec_id: str) -> str:
    return _mint_key(f"{_sec_ns(sec_id)}.tog")

def _sel_key(sec_id: str, label: str) -> str:
    return _mint_key(f"{_sec_ns(sec_id)}.sel.{_slug(label)}")

def _w_key(sec_id: str, label: str) -> str:
    return _mint_key(f"{_sec_ns(sec_id)}.w.{_slug(label)}")

_ORIG = {}
def _capture_originals_once():
    global _ORIG
    if _ORIG: return
    _ORIG["toggle"] = st.toggle
    _ORIG["selectbox"] = st.selectbox
    _ORIG["text_input"] = st.text_input
    try: _ORIG["checkbox"] = st.checkbox
    except Exception: pass

def _patch_widgets():
    _capture_originals_once()
    sec = lambda: st.session_state.get("_special_current_section", "root")

    def _wrap_toggle(label, key=None, **kwargs):
        if key is None: key = _tog_key(sec())
        return _ORIG["toggle"](label, key=key, **kwargs)

    def _wrap_selectbox(label, options, index=0, key=None, **kwargs):
        if key is None: key = _sel_key(sec(), label)
        return _ORIG["selectbox"](label, options, index=index, key=key, **kwargs)

    def _wrap_text_input(label, value="", max_chars=None, key=None, **kwargs):
        if key is None: key = _w_key(sec(), label)
        return _ORIG["text_input"](label, value=value, max_chars=max_chars, key=key, **kwargs)

    st.toggle = _wrap_toggle
    st.selectbox = _wrap_selectbox
    st.text_input = _wrap_text_input
    try:
        orig_cb = _ORIG.get("checkbox")
        if orig_cb:
            def _wrap_checkbox(label, value=False, key=None, **kwargs):
                if key is None: key = _sel_key(sec(), label)
                return orig_cb(label, value=value, key=key, **kwargs)
            st.checkbox = _wrap_checkbox
    except Exception:
        pass

class special_section:
    def __init__(self, sec_id: str): self.sec_id = sec_id; self._prev=None
    def __enter__(self):
        self._prev = st.session_state.get("_special_current_section")
        st.session_state["_special_current_section"] = self.sec_id
        return self
    def __exit__(self, exc_type, exc, tb):
        if self._prev is None:
            st.session_state.pop("_special_current_section", None)
        else:
            st.session_state["_special_current_section"] = self._prev

def special_tests_ui() -> List[str]:
    _patch_widgets()
    lines: List[str] = []
    st.caption(f"특수검사 모듈 ({SPECIAL_TESTS_VERSION}) — 안정화")

    # urine
    with special_section("urine"):
        on = st.toggle("소변 검사 보기")
        if on:
            c1, c2 = st.columns(2)
            with c1:
                alb = st.selectbox("Albumin (알부민뇨)", ["없음","+","++","+++"], index=0)
                upcr = st.text_input("UPCR (단백/크레아티닌 비)")
            with c2:
                rbc = st.text_input("RBC/HPF")
                wbc = st.text_input("WBC/HPF")
            lines.append(f"소변 요약: Albumin={alb}, UPCR={upcr or '-'}, RBC/HPF={rbc or '-'}, WBC/HPF={wbc or '-'}")
            if alb and alb != "없음":
                lines.append(f"알부민뇨 {alb} → 단백뇨 가능성, 추적 권장")
            if upcr:
                try:
                    v = float(str(upcr).replace(',', '').strip())
                    if v >= 0.2:
                        lines.append(f"UPCR {v} ↑ (≥0.2) — 단백뇨 의심, 신장내과 상담 고려")
                except:
                    lines.append("UPCR 값이 숫자가 아닙니다.")

    # stool
    with special_section("stool"):
        on2 = st.toggle("대변 검사 보기")
        if on2:
            color = st.selectbox("변 색상", ["노란","녹색","검은","피 섞임"], index=0)
            freq  = st.text_input("하루 횟수")
            lines.append(f"대변 요약: 색상={color}, 횟수/일={freq or '-'}")
            if color in ("검은","피 섞임"):
                lines.append(f"경고: {color} 변 — 즉시 진료 권고")
            try:
                if freq:
                    n = int(str(freq).strip())
                    if n >= 4:
                        lines.append("설사(≥4회/일) — 수분/ORS 권장, 탈수 체크")
            except:
                lines.append("횟수 입력이 숫자가 아닙니다.")

    st.session_state["special_interpretations"] = lines
    return lines

__all__ = ["special_tests_ui", "special_section"]
