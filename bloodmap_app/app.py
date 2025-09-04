# -*- coding: utf-8 -*-
import os, json
from pathlib import Path
import streamlit as st

from . import utils

# ---- Local helpers to avoid AttributeError on utils.sanitize_pin ----
import re as _re

def _sanitize_pin(pin: str) -> str:
    digits = _re.sub(r"\D", "", pin or "")
    return (digits + "0000")[:4]

def _make_storage_key(nick: str, pin: str) -> str:
    n = (nick or "").strip()[:24]
    p = _sanitize_pin(pin)
    return f"{n}#{p}" if n else ""

from .drug_data import (
    CATEGORIES, hema_by_dx, solid_by_dx, sarcoma_by_dx, rare_by_dx,
    antibiotic_classes, ara_c_forms
)

APP_TITLE = "🩸 피수치 가이드 / BloodMap"
DATA_DIR = str(Path(__file__).resolve().parent.parent / "data")
STYLE_PATH = Path(__file__).resolve().parent / "style.css"

# ----------------- Helpers -----------------
def load_css():
    if STYLE_PATH.exists():
        with open(STYLE_PATH, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def num_input(label, key, step=0.1, minv=0.0, maxv=None, help=None, format=None):
    return st.number_input(
        label, key=key, step=step, min_value=minv, max_value=maxv, help=help, format=format or "%f"
    )

def anc_badge(anc):
    if anc is None:
        return ""
    try:
        anc = float(anc)
    except Exception:
        return ""
    if anc >= 1000:
        klass = "ok"; msg = "ANC 충분 (≥1000)"
    elif 500 <= anc < 1000:
        klass = "warn"; msg = "주의 (500~999): 위생관리 강화"
    else:
        klass = "danger"; msg = "고위험 (<500): 생야채 금지·조리식 권장"
    return f'<span class="badge {klass}">{msg}</span>'

def _chemo_inputs(selected, prefix="chemo"):
    """
    멀티선택된 항암제 각각에 대해 용량 입력 UI.
    ARA-C와 ATRA는 특별 처리.
    """
    result = {}
    for d in selected:
        if "시타라빈(ARA-C)" in d:
            col1, col2 = st.columns([3,2])
            with col1:
                form = st.selectbox("ARA-C 제형", ara_c_forms, key=f"{prefix}_ara_form_{d}")
            with col2:
                dose = st.number_input("ARA-C 용량 (mg/m² 또는 mg)", min_value=0.0, step=10.0, key=f"{prefix}_ara_dose_{d}")
            result[d] = {"dose": utils.to_float(dose, 0), "form": form}
        elif "베사노이드(ATRA)" in d:
            caps = st.number_input("ATRA 캡슐 개수", min_value=0.0, step=1.0, key=f"{prefix}_atra_caps_{d}")
            result[d] = {"capsules": utils.to_float(caps, 0)}
        else:
            dose = st.number_input(f"{d} 용량 (mg/m² 또는 mg)", min_value=0.0, step=10.0, key=f"{prefix}_dose_{d}")
            result[d] = {"dose": utils.to_float(dose, 0)}
    return result

def _antibiotic_inputs(selected, prefix="abx"):
    result = {}
    for abx in selected:
        dose = st.number_input(f"{abx} 용량 (예: mg/kg 또는 mg)", min_value=0.0, step=10.0, key=f"{prefix}_dose_{abx}")
        result[abx] = {"dose": utils.to_float(dose, 0)}
    return result

def dx_options_for(category):
    if category == "혈액암":
        return list(hema_by_dx.keys())
    if category == "고형암":
        return list(solid_by_dx.keys())
    if category == "육종":
        return list(sarcoma_by_dx.keys())
    if category == "희귀암":
        return list(rare_by_dx.keys())
    return []

def drugs_for(category, dx):
    table = {
        "혈액암": hema_by_dx,
        "고형암": solid_by_dx,
        "육종": sarcoma_by_dx,
        "희귀암": rare_by_dx,
    }.get(category, {})
    return table.get(dx, [])

# ----------------- Main -----------------
def main():
    st.title(APP_TITLE)
    load_css()
    st.markdown('<div class="header-note">제작: Hoya/GPT · 자문: Hoya/GPT — 본 도구는 보호자 이해를 돕기 위한 참고용입니다. 모든 의학적 판단은 의료진의 권한입니다.</div>', unsafe_allow_html=True)
    st.success("✅ bloodmap_app.app.main() OK — 경로/레거시 문제 해결됨")

    # 별명 + PIN (4자리 숫자)
    st.subheader("사용자 식별")
    colA, colB = st.columns([3,1])
    with colA:
        nickname = st.text_input("별명", key="nickname", placeholder="예: 호야")
    with colB:
        pin_raw = st.text_input("PIN (4자리 숫자)", key="pin", max_chars=4, placeholder="0000")
    pin = _sanitize_pin(pin_raw)
    key = _make_storage_key(nickname, pin)
    if key:
        st.caption(f"저장키: **{key}**")

    st.divider()

    # 카테고리 → 진단
    st.subheader("1️⃣ 암 그룹 / 진단 선택")
    category = st.radio("최상위 카테고리", CATEGORIES, horizontal=True)
    dx_list = dx_options_for(category)
    dx = st.selectbox("진단명", dx_list, index=0 if dx_list else None)
    if dx and "기타(직접 입력)" in dx:
        dx = st.text_input("직접 입력 (진단명)", key="dx_manual")

    # 항암제 선택
    st.subheader("2️⃣ 항암제 선택 및 용량 입력")
    chemo_candidates = drugs_for(category, dx) if dx else []
    chemo_selected = st.multiselect("항암제(한글표기)", options=chemo_candidates, default=[])
    chemo_payload = _chemo_inputs(chemo_selected)

    # 항생제 선택
    st.subheader("3️⃣ 항생제(계열) 선택 및 용량")
    abx_selected = st.multiselect("항생제 계열(한글표기)", options=antibiotic_classes, default=[])
    abx_payload = _antibiotic_inputs(abx_selected)

    # 이뇨제
    st.subheader("4️⃣ 이뇨제 사용")
    use_diuretic = st.checkbox("이뇨제 사용 중", value=False)
    if use_diuretic:
        st.warning("이뇨제 사용 시 탈수/전해질 이상 위험 ↑ — 수분 섭취 및 전해질 모니터링 권장")

    # 기본 수치
    st.subheader("5️⃣ 기본 혈액 수치 입력")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        wbc = st.number_input("WBC", min_value=0.0, step=0.1, help="백혈구")
    with c2:
        hb = st.number_input("Hb", min_value=0.0, step=0.1, help="혈색소")
    with c3:
        plt = st.number_input("PLT(혈소판)", min_value=0.0, step=1.0)
    with c4:
        anc = st.number_input("ANC(호중구)", min_value=0.0, step=10.0)

    st.markdown(anc_badge(anc), unsafe_allow_html=True)

    # 특수검사 토글
    st.subheader("6️⃣ 특수검사 (토글)")

    with st.expander("응고 패널 (Coagulation) — PT / aPTT / Fibrinogen / D-dimer"):
        pt = st.number_input("PT (sec)", min_value=0.0, step=0.1)
        aptt = st.number_input("aPTT (sec)", min_value=0.0, step=0.1)
        fib = st.number_input("Fibrinogen (mg/dL)", min_value=0.0, step=1.0)
        dd = st.number_input("D-dimer (µg/mL FEU)", min_value=0.0, step=0.01)

    with st.expander("보체 (Complement) — C3 / C4"):
        c3 = st.number_input("C3 (mg/dL)", min_value=0.0, step=1.0)
        c4 = st.number_input("C4 (mg/dL)", min_value=0.0, step=1.0)

    with st.expander("요검사 (Urinalysis) — 단백뇨(Proteinuria) / 잠혈(Hematuria) / 요당(Glycosuria)"):
        u_prot = st.selectbox("단백뇨 (Proteinuria)", ["음성", "±", "1+", "2+", "3+"], index=0)
        u_bld = st.selectbox("잠혈 (Hematuria)", ["음성", "±", "1+", "2+", "3+"], index=0)
        u_glu = st.selectbox("요당 (Glycosuria)", ["음성", "±", "1+", "2+", "3+"], index=0)

    # 소아: 나이(년) → 개월 자동
    st.subheader("7️⃣ 소아 계산 도우미")
    age_years = st.number_input("나이(년)", min_value=0.0, step=0.5, help="소아 계산용. 입력하면 개월 수가 자동으로 계산됩니다.")
    age_months = utils.to_float(age_years, 0) * 12 if utils.is_pos(age_years) else 0
    st.info(f"자동 계산: **{int(age_months)} 개월**")

    # 저장
    st.divider()
    if st.button("💾 현재 입력 저장", disabled=(not key)):
        payload = {
            "key": key,
            "category": category,
            "diagnosis": dx,
            "chemo": chemo_payload,
            "antibiotics": abx_payload,
            "diuretic": bool(use_diuretic),
            "labs": {"WBC": utils.to_float(wbc), "Hb": utils.to_float(hb), "PLT": utils.to_float(plt), "ANC": utils.to_float(anc)},
            "special": {
                "coag": {"PT": utils.to_float(pt), "aPTT": utils.to_float(aptt), "Fibrinogen": utils.to_float(fib), "D_dimer": utils.to_float(dd)},
                "complement": {"C3": utils.to_float(c3), "C4": utils.to_float(c4)},
                "urinalysis": {"Protein": u_prot, "Blood": u_bld, "Glucose": u_glu},
            },
            "pediatrics": {"age_years": utils.to_float(age_years), "age_months": int(age_months)},
        }
        try:
            path = utils.save_record(DATA_DIR, key, payload)
            st.success(f"저장 완료: {os.path.basename(path)}")
        except Exception as e:
            st.error(f"저장 실패: {e}")
    st.caption("※ 저장키는 **별명#PIN(4자리)** 형식입니다. PIN은 숫자만 허용되며 자동 정리됩니다.")

if __name__ == "__main__":
    main()
