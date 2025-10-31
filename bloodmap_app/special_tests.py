
# special_tests.py — minimal working stub (patch-only, stable keys)
# - Drop-in for projects where special_tests.py is missing
# - Keeps keys stable; avoids duplicate-render crashes
# - Returns `lines` for report use
#
# ✅ No deletion of existing project features (this file is self-contained)
# ✅ /mnt/data paths untouched (not used here)
# ✅ ast.parse() validated externally

import streamlit as st
from typing import List, Optional
import re

SPECIAL_TESTS_VERSION = "stub-v1"

# === Stable Keys + Duplicate-Render Guard (from v4 patch) ===
st.session_state["_special_run_tick"] = st.session_state.get("_special_run_tick", 0) + 1
if st.session_state.get("_special_used_keys_tick") != st.session_state["_special_run_tick"]:
    st.session_state["_special_used_keys_tick"] = st.session_state["_special_run_tick"]
    st.session_state["_special_used_keys"] = set()

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
    return f"{_stable_uid()}.special.v2.{sid}"

def _mint_key(base: str) -> str:
    used = st.session_state["_special_used_keys"]
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

def _fav_key(sec_id: str) -> str:
    return _mint_key(f"{_sec_ns(sec_id)}.fav")

def _w_key(sec_id: str, label: str) -> str:
    return _mint_key(f"{_sec_ns(sec_id)}.w.{_slug(label)}")

def _sel_key(sec_id: str, label: str) -> str:
    return _mint_key(f"{_sec_ns(sec_id)}.sel.{_slug(label)}")

try:
    _orig_toggle = st.toggle
    def _patched_toggle(label, key=None, **kwargs):
        if key is None:
            sec_id = st.session_state.get("_special_current_section", "root")
            key = _tog_key(sec_id)
        return _orig_toggle(label, key=key, **kwargs)
    st.toggle = _patched_toggle
except Exception:
    pass

try:
    _orig_selectbox = st.selectbox
    def _patched_selectbox(label, options, index=0, key=None, **kwargs):
        if key is None:
            sec_id = st.session_state.get("_special_current_section", "root")
            key = _sel_key(sec_id, label)
        return _orig_selectbox(label, options, index=index, key=key, **kwargs)
    st.selectbox = _patched_selectbox
except Exception:
    pass

try:
    _orig_text_input = st.text_input
    def _patched_text_input(label, value="", max_chars=None, key=None, **kwargs):
        if key is None:
            sec_id = st.session_state.get("_special_current_section", "root")
            key = _w_key(sec_id, label)
        return _orig_text_input(label, value=value, max_chars=max_chars, key=key, **kwargs)
    st.text_input = _patched_text_input
except Exception:
    pass

class special_section:
    def __init__(self, sec_id: str):
        self.sec_id = sec_id
        self._prev = None
        self._skip = False
    def __enter__(self):
        stamp = f"{_sec_ns(self.sec_id)}.__rendered"
        if st.session_state.get(stamp) == st.session_state["_special_run_tick"]:
            self._skip = True
        else:
            st.session_state[stamp] = st.session_state["_special_run_tick"]
        self._prev = st.session_state.get("_special_current_section")
        st.session_state["_special_current_section"] = self.sec_id
        return self
    def __exit__(self, exc_type, exc, tb):
        if self._prev is None:
            st.session_state.pop("_special_current_section", None)
        else:
            st.session_state["_special_current_section"] = self._prev
    @property
    def skip(self) -> bool:
        return self._skip

# === Minimal working UI ===
def special_tests_ui() -> List[str]:
    lines: List[str] = []
    st.caption(f"특수검사 모듈 ({SPECIAL_TESTS_VERSION}) — 안정화 스텁")

    # 1) 소변(urine) 섹션
    with special_section("urine") as sec:
        if not sec.skip:
            on = st.toggle("소변 검사 보기", key=_tog_key("urine"), value=True)
            if on:
                col1, col2 = st.columns(2)
                with col1:
                    alb = st.selectbox("Albumin (알부민뇨)", ["없음","+","++","+++"], index=0, key=_sel_key("urine","Albumin"))
                    upcr = st.text_input("UPCR (단백/크레아티닌 비)", key=_w_key("urine","UPCR"))
                with col2:
                    rbc = st.text_input("RBC/HPF", key=_w_key("urine","RBC/HPF"))
                    wbc = st.text_input("WBC/HPF", key=_w_key("urine","WBC/HPF"))

                # 간단 해석
                if alb and alb != "없음":
                    lines.append(f"알부민뇨 {alb} → 신장 단백뇨 가능성, 추적 권장")
                if upcr:
                    try:
                        v = float(str(upcr).replace(',', '').strip())
                        if v >= 0.2:
                            lines.append(f"UPCR {v} ↑ (≥0.2) — 단백뇨 의심, 신장내과 상담 고려")
                    except:
                        lines.append("UPCR 값이 숫자가 아닙니다.")

    # 2) 대변(stool) 섹션 (샘플)
    with special_section("stool") as sec:
        if not sec.skip:
            on = st.toggle("대변 검사 보기", key=_tog_key("stool"), value=False)
            if on:
                color = st.selectbox("변 색상", ["노란","녹색","검은","피 섞임"], index=0, key=_sel_key("stool","변 색상"))
                freq = st.text_input("하루 횟수", key=_w_key("stool","횟수"))
                if color in ("검은","피 섞임"):
                    lines.append(f"경고: {color} 변 — 즉시 진료 권고")
                try:
                    if freq:
                        n = int(str(freq).strip())
                        if n >= 4:
                            lines.append("설사(≥4회/일) — 수분/ORS 권장, 탈수 체크")
                except:
                    lines.append("횟수 입력이 숫자가 아닙니다.")

    # 결과 저장(보고서에서 활용)
    st.session_state["special_interpretations"] = lines
    return lines

__all__ = ["special_tests_ui", "SPECIAL_TESTS_VERSION", "special_section",
           "_tog_key", "_sel_key", "_w_key", "_fav_key"]
