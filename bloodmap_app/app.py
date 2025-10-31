# app.py — hardened build: force-use built-in SAFE special_tests UI (no external monkeypatch risk)
import streamlit as st
import re
from typing import List, Optional

# ===== Built-in SAFE special tests UI =====
def _stable_uid() -> str:
    uid = st.session_state.get("_uid") or st.session_state.get("key") or "guest"
    return re.sub(r'[^a-zA-Z0-9_.-]', '_', str(uid))

def _slug(x: str) -> str:
    return re.sub(r'[^a-zA-Z0-9_.-]+', '_', str(x)).strip('_') or "x"

def _sec_ns(sec_id: Optional[str]) -> str:
    sid = _slug(sec_id or "root")
    return f"{_stable_uid()}.special.safe.{sid}"

# per-rerun used-keys registry (robust init)
_tick = st.session_state.get("_sp_tick_safe", 0) + 1
st.session_state["_sp_tick_safe"] = _tick
st.session_state.setdefault("_sp_used_keys_safe", set())
if st.session_state.get("_sp_used_tick_safe") != _tick:
    st.session_state["_sp_used_tick_safe"] = _tick
    st.session_state["_sp_used_keys_safe"] = set()

def _mint_key(base: str) -> str:
    used = st.session_state.setdefault("_sp_used_keys_safe", set())
    if base not in used:
        used.add(base); return base
    i = 2
    while True:
        k = f"{base}.dup{i}"
        if k not in used:
            used.add(k); return k
        i += 1

def _tog_key(sec_id: str) -> str:
    return _mint_key(f"{_sec_ns(sec_id)}.tog")

def _sel_key(sec_id: str, label: str) -> str:
    return _mint_key(f"{_sec_ns(sec_id)}.sel.{_slug(label)}")

def _w_key(sec_id: str, label: str) -> str:
    return _mint_key(f"{_sec_ns(sec_id)}.w.{_slug(label)}")

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
    lines: List[str] = []
    st.caption("특수검사 모듈 (built-in safe) — 외부 모듈 무시")

    # urine
    with special_section("urine"):
        on = st.toggle("소변 검사 보기", key=_tog_key("urine"))
        if on:
            c1, c2 = st.columns(2)
            with c1:
                alb = st.selectbox("Albumin (알부민뇨)", ["없음","+","++","+++"], index=0, key=_sel_key("urine","Albumin"))
                upcr = st.text_input("UPCR (단백/크레아티닌 비)", key=_w_key("urine","UPCR"))
            with c2:
                rbc = st.text_input("RBC/HPF", key=_w_key("urine","RBC"))
                wbc = st.text_input("WBC/HPF", key=_w_key("urine","WBC"))
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
        on2 = st.toggle("대변 검사 보기", key=_tog_key("stool"))
        if on2:
            color = st.selectbox("변 색상", ["노란","녹색","검은","피 섞임"], index=0, key=_sel_key("stool","색상"))
            freq  = st.text_input("하루 횟수", key=_w_key("stool","횟수"))
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

# ===== App body (demo minimal) =====
st.title("BloodMap — Hardened Demo")
if st.button("특수검사 실행(데모)"):
    try:
        L = special_tests_ui()
        st.success(f"특수검사 결과 {len(L)}건")
    except Exception as e:
        st.error(f"실행 오류: {e}")

# Report bridge (inline minimal)
def _render_report():
    lines = st.session_state.get("special_interpretations", [])
    st.markdown("## 특수검사 해석(각주 포함)")
    if not lines:
        st.info("특수검사 입력은 있었지만 해석 문장이 아직 없습니다.")
    else:
        for s in lines:
            st.write(f"- {s}")
    with st.expander("🔎 특수검사 디버그 보기"):
        st.write({
            "special_interpretations": st.session_state.get("special_interpretations"),
        })

_render_report()
