# -*- coding: utf-8 -*-
import streamlit as st
from . import config

# ---- Try normal import first ----
try:
    from .utils import css_load, num_input, safe_float, pediatric_guard, pin_4_guard
except Exception:
    # ---- Safe local fallbacks (utils.py 없어도 동작) ----
    def css_load():
        try:
            with open("bloodmap_app/style.css", "r", encoding="utf-8") as f:
                st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
        except Exception:
            pass
    def safe_float(x):
        try:
            if x is None: return None
            if isinstance(x, str) and x.strip()=="": return None
            return float(x)
        except Exception:
            return None
    def num_input(label: str, key: str, unit: str=None, step: float=0.1, format_decimals: int=2):
        ph = "예: " + ("0" if format_decimals==0 else "0." + ("0"*format_decimals))
        val = st.text_input(label + (f" ({unit})" if unit else ""), key=key, placeholder=ph)
        return safe_float(val)
    def pediatric_guard(years_input, months_input):
        def _to_int(v):
            try:
                if v is None: return 0
                if isinstance(v, str) and v.strip()=="": return 0
                return int(float(v))
            except Exception:
                return 0
        y = _to_int(years_input); m = _to_int(months_input)
        return max(y*12 + m, 0)
    def pin_4_guard(pin_str: str) -> str:
        only = "".join(ch for ch in (pin_str or "") if ch.isdigit())
        return (only[-4:]).zfill(4) if only else "0000"

def _header():
    st.set_page_config(page_title="피수치 가이드 / BloodMap", layout="centered")
    css_load()
    st.title(config.APP_TITLE)
    st.caption(config.APP_TAGLINE)

def _nickname_pin():
    st.subheader("프로필")
    col1, col2 = st.columns([2,1], vertical_alignment="center")
    with col1:
        nick = st.text_input("별명", key="nick", placeholder="예: 우리공듀")
    with col2:
        raw_pin = st.text_input("PIN 4자리", key="pin", placeholder="0000")
        pin = pin_4_guard(raw_pin)
        st.caption(f"저장 키: {nick.strip() if nick else '사용자'}#{pin}")
    return (nick or "").strip(), pin

def _cancer_section():
    st.subheader("암 그룹 · 항암제/항생제")
    group = st.selectbox("암 그룹 선택", config.CANCER_GROUPS, index=0)
    if group == "육종":
        st.multiselect("육종 (진단명 선택)", options=config.SARCOMA_TYPES, key="sarcoma_types")
    st.multiselect("항암제 (한글 표기)", options=config.ANTICANCER_BY_GROUP.get(group, []), key="anticancer_sel")
    st.selectbox("아라시티딘(ARA-C) 제형", config.ARAC_FORMS, key="arac_form", index=0)
    st.checkbox("ATRA (캡슐) 복용 중", key="atra_caps")
    st.multiselect("항생제 (한글 표기)", options=config.ANTIBIOTICS, key="abx_sel")
    return group

def _base_panel():
    st.subheader("기본 4항목 입력")
    c1,c2,c3,c4 = st.columns(4)
    with c1: wbc = num_input("WBC (×10³/µL)", "wbc", step=0.1, format_decimals=1)
    with c2: hb = num_input("Hb (g/dL)", "hb", step=0.1, format_decimals=1)
    with c3: plt = num_input("혈소판 (×10³/µL)", "plt", step=1, format_decimals=0)
    with c4: anc = num_input("ANC (/µL)", "anc", step=10, format_decimals=0)
    return {"wbc": wbc, "hb": hb, "plt": plt, "anc": anc}

def _order_panel():
    st.subheader("ORDER 기반 20항목 입력")
    cols = st.columns(3)
    values = {}
    for idx, (key, label, unit, decs) in enumerate(config.ORDER):
        col = cols[idx % 3]
        with col:
            val = num_input(label, f"ord_{key}", unit=unit, format_decimals=(decs if decs is not None else 2))
            values[key] = val
    return values

def _special_tests():
    st.subheader("특수검사 (토글)")
    out = {}
    for title, items in config.SPECIAL_PANELS.items():
        with st.expander(title, expanded=False):
            for key, label, unit, decs in items:
                val = num_input(label, f"sp_{key}", unit=unit, format_decimals=(decs if decs is not None else 2))
                out[key] = val
    return out

def _pediatric_helper():
    st.subheader("👶 소아 계산 도우미")
    c1, c2 = st.columns(2)
    with c1:
        years = st.text_input("나이(년)", key="p_years", placeholder="예: 5")
    with c2:
        months = st.text_input("나이(개월)", key="p_months", placeholder="예: 6")
    total_months = pediatric_guard(years, months)
    st.caption(f"자동 계산: 총 {total_months} 개월")

def _guides(values):
    st.subheader("영양/안전 가이드")
    cuts = config.CUTS
    guides = []
    alb = safe_float(values.get("albumin"))
    if alb is not None and alb < cuts["albumin_low"]:
        guides.append(config.NUTRITION_GUIDE["albumin_low"])
    k = safe_float(values.get("k"))
    if k is not None and k < cuts["k_low"]:
        guides.append(config.NUTRITION_GUIDE["k_low"])
    hb = safe_float(values.get("hb"))
    if hb is not None and hb < cuts["hb_low"]:
        guides.append(config.NUTRITION_GUIDE["hb_low"])
    na = safe_float(values.get("na"))
    if na is not None and na < cuts["na_low"]:
        guides.append(config.NUTRITION_GUIDE["na_low"])
    ca = safe_float(values.get("ca"))
    if ca is not None and ca < cuts["ca_low"]:
        guides.append(config.NUTRITION_GUIDE["ca_low"])
    anc = safe_float(values.get("anc"))
    if anc is not None and anc < cuts["anc_neutropenia"]:
        guides.append(config.NUTRITION_GUIDE["anc_low"])

    if guides:
        for g in guides:
            st.warning(g)
    else:
        st.info("조건에 해당하는 가이드가 아직 없습니다. 필요한 항목을 입력해주세요.")

def main():
    _header()
    _nickname_pin()
    _cancer_section()
    base = _base_panel()
    more = _order_panel()
    values = {**base, **more}
    _special_tests()
    _pediatric_helper()
    _guides(values)
    st.divider()
    st.caption("저장 키(별명#PIN)는 중복 방지를 위해 사용됩니다.")
    st.caption("본 앱은 참고용이며, 의학적 판단은 의료진에게 문의하세요.")

if __name__ == "__main__":
    main()
