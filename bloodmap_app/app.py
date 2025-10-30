
# app.recovery.safe.v2.py — BloodMap SAFE-BOOT (권한 에러 내성 패치)
from __future__ import annotations
import streamlit as st
import json, os, io, tempfile
from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))

# ===== helpers =====
def _bm_defaults():
    ss = st.session_state
    ss.setdefault("_route", ss.get("_route_last", "dx"))
    ss.setdefault("_route_last", ss.get("_route", "dx"))
    ss.setdefault("_home_intent", True)
    ss.setdefault("_ctx_tab", None)
    for k in ("labs_dict","peds_inputs","chemo_inputs","special_interpretations","care_log"):
        ss.setdefault(k, {})
    ss.setdefault("profile", {"maker": "Hoya/GPT", "tz":"KST"})

def _pin_route(name: str):
    ss = st.session_state
    ss["_route"] = name
    if name != "home":
        ss["_route_last"] = name
    try:
        qp = st.query_params
        if qp.get("route") != name: st.query_params.update(route=name)
    except Exception:
        try:
            if (st.experimental_get_query_params().get("route") or [""])[0] != name:
                st.experimental_set_query_params(route=name)
        except Exception:
            pass

def _first_writable_dir(candidates: list[str]) -> tuple[str | None, str]:
    """Return first writable dir; create if needed. Also verify by writing a small probe file."""
    note = ""
    for d in candidates:
        try:
            os.makedirs(d, exist_ok=True)
            probe_path = os.path.join(d, ".write_probe")
            with open(probe_path, "w", encoding="utf-8") as f:
                f.write("ok")
            os.remove(probe_path)
            if d.startswith("/mnt/data"):
                note = "(/mnt/data 유지)"
            else:
                note = f"(권한 문제로 대체 경로 사용: {d})"
            return d, note
        except PermissionError:
            continue
        except OSError:
            continue
    return None, "(모든 후보 경로 쓰기 불가)"

_bm_defaults()

# ===== Optional modules (soft import) =====
_special_ui = None
try:
    from special_tests import special_tests_ui as _special_ui
except Exception as e:
    _special_err = e
else:
    _special_err = None

_peds_render = None
try:
    from pages_peds import render_peds_page as _peds_render
except Exception as e:
    _peds_err = e
else:
    _peds_err = None

_brand = None
try:
    import branding as _branding
    _brand = getattr(_branding, "render_deploy_banner", None)
except Exception:
    _brand = None

# ===== UI =====
st.set_page_config(page_title="BloodMap · SAFE-BOOT v2", layout="wide")
if _brand:
    try: _brand()
    except Exception: pass

st.title("🩸 BloodMap · SAFE-BOOT v2 (복구용)")
st.caption("한국시간: " + datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S"))

tabs = st.tabs(["🏠 홈","🧬 암","💊 항암제","📊 피수치","🔬 특수검사","👶 소아","🧾 보고서"])

# 홈
with tabs[0]:
    st.write("앱 복구용 안전 모드입니다. 입력/저장/특수검사 동작 확인에 집중합니다.")
    if st.button("피수치로 이동", key="go_labs"):
        _pin_route("labs")
        st.rerun()

with tabs[1]:
    st.info("암 탭(임시).")

with tabs[2]:
    st.info("항암제 탭(임시).")

with tabs[3]:
    st.header("📊 피수치 입력(복구 모드)")
    st.caption("입력값은 세션에 보존됩니다.")
    labs = st.session_state.get("labs_dict", {})
    colA, colB, colC = st.columns(3)
    with colA:
        labs["WBC"] = st.text_input("WBC", labs.get("WBC",""), key="lab_WBC")
        labs["Hb"]  = st.text_input("Hb",  labs.get("Hb",""), key="lab_Hb")
        labs["PLT"] = st.text_input("PLT", labs.get("PLT",""), key="lab_PLT")
    with colB:
        labs["CRP"] = st.text_input("CRP", labs.get("CRP",""), key="lab_CRP")
        labs["Na"]  = st.text_input("Na",  labs.get("Na",""), key="lab_Na")
        labs["K"]   = st.text_input("K",   labs.get("K",""), key="lab_K")
    with colC:
        labs["Alb"] = st.text_input("Albumin", labs.get("Alb",""), key="lab_Alb")
        labs["Ca"]  = st.text_input("Calcium", labs.get("Ca",""), key="lab_Ca")
        labs["AST"] = st.text_input("AST", labs.get("AST",""), key="lab_AST")

    st.session_state["labs_dict"] = labs
    if st.button("저장(세션)", key="save_labs"):
        st.success("세션에 저장되었습니다.")

    # 외부 저장 (권한 내성)
    candidates = [
        "/mnt/data/bloodmap_graph",
        "/mnt/data",
        os.path.join(tempfile.gettempdir(), "bloodmap_graph"),
        os.getcwd(),
    ]
    save_dir, note = _first_writable_dir(candidates)
    st.caption(f"외부 저장 경로 후보 테스트: {note}")
    uid = "default_user"
    if st.button("CSV 외부 저장", key="save_csv"):
        if save_dir is None:
            st.error("쓰기 가능한 외부 저장 경로가 없습니다. (권한 문제)")
        else:
            import pandas as pd
            df = pd.DataFrame([labs])
            out_path = os.path.join(save_dir, f"{uid}.labs.csv")
            try:
                df.to_csv(out_path, index=False, encoding="utf-8")
                st.success(f"외부 저장 완료: {out_path}")
            except Exception as e:
                st.error(f"외부 저장 실패: {e}")

with tabs[4]:
    st.session_state["_ctx_tab"] = "special"
    st.header("🔬 특수검사")
    if _special_ui:
        try:
            lines = _special_ui()
            if lines:
                st.write("###### 요약")
                for ln in lines:
                    st.write("- " + ln)
        except Exception as e:
            st.error(f"특수검사 모듈 오류: {e}")
    else:
        st.warning("특수검사 모듈을 불러오지 못했습니다. special_tests.py 를 확인하세요.")
        if _special_err:
            st.exception(_special_err)

with tabs[5]:
    st.header("👶 소아")
    if _peds_render:
        try:
            _peds_render()
        except Exception as e:
            st.error(f"소아 모듈 오류: {e}")
    else:
        st.info("소아 모듈 연결 전(복구 모드). pages_peds.py 확인 필요.")

with tabs[6]:
    st.header("🧾 간단 보고서(복구 모드)")
    st.write("**입력된 피수치(세션):**")
    st.json(st.session_state.get("labs_dict", {}))
    summ = st.session_state.get("special_interpretations", {})
    if summ:
        st.write("**특수검사 요약:**")
        st.json(summ)
    st.caption("정식 보고서는 원본 모듈 복귀 후 정상화됩니다.")

st.divider()
st.caption("제작 · 자문: Hoya/GPT — SAFE-BOOT v2 (KST)")
