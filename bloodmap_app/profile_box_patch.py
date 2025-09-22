
# -*- coding: utf-8 -*-
"""
profile_box_patch (shim)
- Exposes: render_profile_box_fixed(uid, save_profile, load_profile, check_pin)
- If profile_box has implementation, forward to it. Otherwise use inline safe version.
"""
from __future__ import annotations

try:
    from profile_box import render_profile_box_fixed  # type: ignore
except Exception:
    import streamlit as st

    def render_profile_box_fixed(uid: str, save_profile, load_profile, check_pin):
        st.markdown("### 👤 프로필 / PIN")

        # 불러오기 트리거 선처리(위젯 렌더 전에 세션에 주입 → 충돌 방지)
        trig_key = f"__load_prof_trig_{uid}"
        if st.session_state.get(trig_key):
            p = load_profile(uid) or {}
            st.session_state[f"age_{uid}"] = int(p.get("age", 30) or 30)
            st.session_state[f"sex_{uid}"] = p.get("sex", "남")
            st.session_state[f"h_{uid}"]   = float(p.get("height_cm", 170.0) or 170.0)
            st.session_state[f"w_{uid}"]   = float(p.get("weight", 60.0) or 60.0)
            st.session_state[f"sap_{uid}"] = str(p.get("syrup_apap", "160/5"))
            st.session_state[f"sib_{uid}"] = str(p.get("syrup_ibu", "100/5"))
            st.session_state[trig_key] = False
            st.rerun()

        with st.expander("프로필 열기/저장", expanded=False):
            age_default = st.session_state.get(f"age_{uid}", 30)
            sex_default = st.session_state.get(f"sex_{uid}", "남")
            h_default   = st.session_state.get(f"h_{uid}", 170.0)
            w_default   = st.session_state.get(f"w_{uid}", 60.0)

            age_y = st.number_input("나이(세)", min_value=0, step=1, value=age_default, key=f"age_{uid}")
            sex = st.selectbox("성별", ["남","여"], index=(0 if sex_default=="남" else 1), key=f"sex_{uid}")
            height_cm = st.number_input("키(cm)", min_value=0.0, step=0.1, value=h_default, key=f"h_{uid}")
            weight = st.number_input("체중(kg)", min_value=0.0, step=0.1, value=w_default, key=f"w_{uid}")
            syrup_apap = st.text_input("APAP 시럽 농도(예: 160 mg/5mL)", value=st.session_state.get(f"sap_{uid}", "160/5"), key=f"sap_{uid}")
            syrup_ibu = st.text_input("IBU 시럽 농도(예: 100 mg/5mL)", value=st.session_state.get(f"sib_{uid}", "100/5"), key=f"sib_{uid}")
            pin_inline = st.text_input("프로필과 함께 저장할 PIN(선택, 4–6자리)", type="password", key=f"pin_inline_{uid}")

            c1, c2 = st.columns(2)
            with c1:
                if st.button("💾 프로필 저장", key=f"save_prof_{uid}"):
                    pin_ok = pin_inline and pin_inline.isdigit() and 4 <= len(pin_inline) <= 6
                    save_profile(uid, {"age":st.session_state.get(f"age_{uid}",30),
                                       "sex":st.session_state.get(f"sex_{uid}","남"),
                                       "height_cm":st.session_state.get(f"h_{uid}",170.0),
                                       "weight":st.session_state.get(f"w_{uid}",60.0),
                                       "syrup_apap":st.session_state.get(f"sap_{uid}","160/5"),
                                       "syrup_ibu":st.session_state.get(f"sib_{uid}","100/5")},
                                 pin=(pin_inline if pin_ok else None))
                    st.success("프로필 저장됨" + (" + PIN" if pin_ok else ""))
            with c2:
                if st.button("📥 프로필 불러오기", key=f"load_prof_{uid}"):
                    st.session_state[trig_key] = True
                    st.stop()

        with st.expander("PIN 검증만", expanded=False):
            pin_chk = st.text_input("열람 PIN 입력", type="password", key=f"pinchk_{uid}")
            if st.button("✅ PIN 확인", key=f"checkpin_{uid}"):
                st.success("통과") if check_pin(uid, pin_chk) else st.error("PIN 불일치")
