# -*- coding: utf-8 -*-
import os
import datetime
import streamlit as st
import pandas as pd

from .config import VERSION, APP_TITLE, BRAND, KST_NOTE
from .utils import (
    is_valid_pin, key_from,
    compute_acr, compute_upcr, interpret_acr, interpret_upcr,
    pediatric_guides, build_report_md, build_report_txt, build_report_pdf_bytes
)
from .graphs import render_graphs
from . import drug_data

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
os.makedirs(DATA_DIR, exist_ok=True)
HISTORY_CSV = os.path.join(DATA_DIR, "history.csv")

def load_css():
    try:
        css_path = os.path.join(os.path.dirname(__file__), "style.css")
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception:
        pass

def save_row(row: dict):
    cols = [
        "timestamp","user_key","category","diagnosis",
        "WBC","Hb","PLT","ANC","CRP",
        "Urine Alb (mg/L)","Urine Prot (mg/dL)","Urine Cr (mg/dL)",
        "Ferritin","LDH","Uric acid","ESR","Retic(%)","β2-microglobulin","Coombs",
        "AST","ALT","ALP","GGT","Total bilirubin",
        "Na","K","Ca","Mg","Phos","INR","aPTT","Fibrinogen","D-dimer","Triglycerides","Lactate",
        "ACR (mg/g)","UPCR (mg/g)","Chemo","Antibiotics"
    ]
    df_new = pd.DataFrame([row], columns=cols)
    if os.path.exists(HISTORY_CSV):
        try:
            df_old = pd.read_csv(HISTORY_CSV)
            df = pd.concat([df_old, df_new], ignore_index=True)
        except Exception:
            df = df_new
    else:
        df = df_new
    df.to_csv(HISTORY_CSV, index=False)

def main():
    st.set_page_config(page_title=APP_TITLE, layout="centered", initial_sidebar_state="collapsed")
    load_css()
    st.markdown(f"### {APP_TITLE} — {VERSION}")
    st.caption(f"{BRAND} · {KST_NOTE}")
    st.divider()

    # ===== User identity (별명 + PIN) =====
    c1, c2 = st.columns([2,1])
    with c1:
        alias = st.text_input("별명", placeholder="예: 민트초코")
    with c2:
        pin = st.text_input("PIN (4자리 숫자)", max_chars=4, placeholder="0000")
    valid_pin = is_valid_pin(pin)
    user_key = key_from(alias, pin) if valid_pin else ""
    if not valid_pin and pin:
        st.error("PIN은 숫자 4자리만 가능해요. 예: 0427")
    st.markdown(f"**저장키:** `{user_key or '별명#PIN 형식'}`")

    st.divider()

    # ===== Tabs =====
    tabs = st.tabs(["진단 선택", "기본 수치", "특수/소변", "약물 선택", "소아 가이드", "결과/내보내기"])

    # ===== Diagnosis =====
    with tabs[0]:
        group = st.radio("암 그룹", ["혈액암","고형암","육종","희귀암"], horizontal=True)
        diag_options = list(drug_data.CHEMO_BY_DIAGNOSIS.get(group, {}).keys())
        if not diag_options:
            diag_options = ["-"]
        diagnosis = st.selectbox("진단명", diag_options, index=0)

    # ===== Basic panel =====
    with tabs[1]:
        st.markdown("#### 기본 수치")
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            WBC = st.number_input("WBC(×10³/µL)", min_value=0.0, step=0.1, format="%.1f")
        with c2:
            Hb  = st.number_input("Hb(g/dL)", min_value=0.0, step=0.1, format="%.1f")
        with c3:
            PLT = st.number_input("혈소판(×10³/µL)", min_value=0.0, step=1.0, format="%.0f")
        with c4:
            ANC = st.number_input("호중구 ANC(/µL)", min_value=0.0, step=10.0, format="%.0f")
        with c5:
            CRP = st.number_input("CRP(mg/dL)", min_value=0.0, step=0.1, format="%.2f")

        if ANC:
            if ANC < 500:
                st.info("ANC 가이드: ⚠️ 500 미만 주의")
            elif ANC < 1000:
                st.info("ANC 가이드: ⚠️ 500~999 주의")
            else:
                st.info("ANC 가이드: ✅ 1000 이상 안정")

    # ===== Special/Urine panel =====
    with tabs[2]:
        st.markdown("#### 특수/소변 검사")
        st.caption("요단백·요알부민·혈뇨 등은 필요한 값만 입력하세요.")
        unit_col, _, _ = st.columns(3)
        with unit_col:
            alb_unit = st.radio("요 알부민 단위", ["mg/L","mg/dL"], horizontal=True, index=0)
        u1, u2, u3 = st.columns(3)
        with u1:
            urine_albumin_val = st.number_input(f"요 알부민 ({alb_unit})", min_value=0.0, step=1.0, format="%.1f")
        with u2:
            urine_protein_mg_dL = st.number_input("요 단백 (mg/dL)", min_value=0.0, step=1.0, format="%.1f")
        with u3:
            urine_cr_mg_dL = st.number_input("요 크레아티닌 (mg/dL)", min_value=0.0, step=0.1, format="%.1f")

        urine_albumin_mg_L = urine_albumin_val*10.0 if alb_unit == "mg/dL" else urine_albumin_val
        acr = compute_acr(urine_albumin_mg_L if urine_albumin_mg_L else None, urine_cr_mg_dL if urine_cr_mg_dL else None)
        upcr = compute_upcr(urine_protein_mg_dL if urine_protein_mg_dL else None, urine_cr_mg_dL if urine_cr_mg_dL else None)

        d1, d2 = st.columns(2)
        with d1:
            st.metric("ACR (mg/g)", f"{acr:.0f}" if acr else "-")
            st.caption(interpret_acr(acr))
        with d2:
            st.metric("UPCR (mg/g)", f"{upcr:.0f}" if upcr else "-")
            st.caption(interpret_upcr(upcr))

        st.markdown("#### 특수검사(+)")
        e1,e2,e3 = st.columns(3)
        with e1:
            Ferritin = st.number_input("Ferritin (ng/mL)", min_value=0.0, step=1.0, format="%.1f")
            LDH = st.number_input("LDH (U/L)", min_value=0.0, step=1.0, format="%.0f")
        with e2:
            UricAcid = st.number_input("Uric acid (mg/dL)", min_value=0.0, step=0.1, format="%.2f")
            ESR = st.number_input("ESR (mm/hr)", min_value=0.0, step=1.0, format="%.0f")
        with e3:
            Retic = st.number_input("Retic(%)", min_value=0.0, step=0.1, format="%.1f")
            B2M = st.number_input("β2-microglobulin (mg/L)", min_value=0.0, step=0.1, format="%.2f")
        Coombs = st.selectbox("Coombs test", ["-","Direct(+)","Direct(-)","Indirect(+)","Indirect(-)"])

        from .utils import interpret_ferritin, interpret_ldh, interpret_ua, interpret_esr, interpret_b2m
        extra_msgs = []
        if Ferritin: extra_msgs.append(interpret_ferritin(Ferritin))
        if LDH: extra_msgs.append(interpret_ldh(LDH))
        if UricAcid: extra_msgs.append(interpret_ua(UricAcid))
        if ESR: extra_msgs.append(interpret_esr(ESR))
        if B2M: extra_msgs.append(interpret_b2m(B2M))
        if Coombs and Coombs != "-": extra_msgs.append(f"Coombs: {Coombs}")
        for m in extra_msgs:
            st.caption("• " + m)

        st.info("단위: ACR = Alb(mg/L)/Cr(mg/dL)×100, UPCR = Prot(mg/dL)/Cr(mg/dL)×1000")

        st.markdown("#### 간기능/전해질/응고 (+)")
        l1,l2,l3 = st.columns(3)
        with l1:
            AST = st.number_input("AST (U/L)", min_value=0.0, step=1.0, format="%.0f")
            ALT = st.number_input("ALT (U/L)", min_value=0.0, step=1.0, format="%.0f")
            ALP = st.number_input("ALP (U/L)", min_value=0.0, step=1.0, format="%.0f")
            GGT = st.number_input("GGT (U/L)", min_value=0.0, step=1.0, format="%.0f")
            TBILI = st.number_input("Total bilirubin (mg/dL)", min_value=0.0, step=0.1, format="%.2f")
        with l2:
            Na = st.number_input("Na (mmol/L)", min_value=0.0, step=0.5, format="%.1f")
            K  = st.number_input("K (mmol/L)", min_value=0.0, step=0.1, format="%.1f")
            Ca = st.number_input("Ca (mg/dL)", min_value=0.0, step=0.1, format="%.2f")
            Mg = st.number_input("Mg (mg/dL)", min_value=0.0, step=0.1, format="%.2f")
            Phos = st.number_input("Phos (mg/dL)", min_value=0.0, step=0.1, format="%.2f")
        with l3:
            INR = st.number_input("INR", min_value=0.0, step=0.1, format="%.2f")
            aPTT = st.number_input("aPTT (sec)", min_value=0.0, step=0.5, format="%.1f")
            Fibrinogen = st.number_input("Fibrinogen (mg/dL)", min_value=0.0, step=1.0, format="%.0f")
            Ddimer = st.number_input("D-dimer (µg/mL FEU)", min_value=0.0, step=0.1, format="%.2f")
            TG = st.number_input("Triglycerides (mg/dL)", min_value=0.0, step=1.0, format="%.0f")
            Lactate = st.number_input("Lactate (mmol/L)", min_value=0.0, step=0.1, format="%.2f")

        from .utils import (
            interpret_ast, interpret_alt, interpret_alp, interpret_ggt, interpret_tbili,
            interpret_na, interpret_k, interpret_ca, interpret_mg, interpret_phos,
            interpret_inr, interpret_aptt, interpret_fibrinogen, interpret_ddimer,
            interpret_tg, interpret_lactate
        )
        quick = []
        quick += [interpret_ast(AST), interpret_alt(ALT), interpret_alp(ALP), interpret_ggt(GGT), interpret_tbili(TBILI)]
        quick += [interpret_na(Na), interpret_k(K), interpret_ca(Ca), interpret_mg(Mg), interpret_phos(Phos)]
        quick += [interpret_inr(INR), interpret_aptt(aPTT), interpret_fibrinogen(Fibrinogen), interpret_ddimer(Ddimer)]
        quick += [interpret_tg(TG), interpret_lactate(Lactate)]
        for q in quick:
            if q: st.caption("• " + q)


    # ===== Drugs panel =====
    with tabs[3]:
        st.markdown("#### 항암제/항생제 (한글 병기)")
        chemo_list = drug_data.CHEMO_BY_DIAGNOSIS.get(group, {}).get(diagnosis, [])
        reg_keys = ["-"] + list(drug_data.REGIMENS.keys())
        chosen_reg = st.selectbox("레짐 프리셋", reg_keys, help="예: MAP, VAC/IE, POMP")
        if chosen_reg != "-":
            preset = drug_data.REGIMENS.get(chosen_reg, [])
            base_set = set(chemo_list)
            chemo_list = list(dict.fromkeys(list(preset) + list(base_set)))
            st.caption(f"프리셋 적용: {chosen_reg} → {len(preset)}개 항목 선반영")
        sel_chemo = st.multiselect(
            "항암제 선택",
            options=chemo_list,
            default=(drug_data.REGIMENS.get(chosen_reg, []) if chosen_reg != "-" else []),
            help="복수 선택 가능"
        )

        st.markdown("---")
        abx_classes = list(drug_data.ANTIBIOTICS_BY_CLASS.keys())
        abx_class = st.selectbox("항생제 계열", abx_classes)
        abx_options = drug_data.ANTIBIOTICS_BY_CLASS.get(abx_class, [])
        sel_abx = st.multiselect("항생제 선택", options=abx_options)
        tip = getattr(drug_data, "ABX_CLASS_TIPS", {}).get(abx_class, "")
        if tip:
            st.info(f"계열 안내: {tip}")

    # ===== Pediatrics =====
    with tabs[4]:
        st.markdown("#### 소아 패널 / 해석 가이드")
        c1,c2,c3 = st.columns(3)
        with c1:
            age_years = st.number_input("나이(년)", min_value=0, step=1)
        with c2:
            age_months = st.number_input("나이(개월)", min_value=0, step=1, help="년 입력 시 자동 계산됨")
        with c3:
            weight = st.number_input("체중(kg)", min_value=0.0, step=0.1)
        if age_years and not age_months:
            st.session_state["auto_age_months"] = age_years*12
            st.experimental_rerun()
        group_ped = st.selectbox("소아 질환군", ["-", "소아-일상", "소아-감염", "소아-혈액암", "소아-고형암", "소아-육종", "소아-희귀암"])
        ped_msgs = pediatric_guides({"ANC": ANC}, group_ped, diagnosis)
        for m in ped_msgs:
            st.markdown(f"- {m}")

    # ===== Result / Export =====
    with tabs[5]:
        st.markdown("### 결과 요약")
        sticky = st.empty()
        header_html = f"""
        <div class='sticky-header'>
          <b>{user_key or "별명#PIN 필요"}</b> · {group} · {diagnosis}
        </div>
        """
        sticky.markdown(header_html, unsafe_allow_html=True)

        if user_key:
            st.success(f"사용자: **{user_key}** · 진단: {diagnosis} · 그룹: {group}")
        else:
            st.warning("별명과 유효한 4자리 PIN을 입력하면 저장/내보내기가 활성화됩니다.")

        derived = {}
        if acr:
            derived["ACR (mg/g)"] = f"{acr:.0f}"
        if upcr:
            derived["UPCR (mg/g)"] = f"{upcr:.0f}"

        values = {
            "WBC": WBC if WBC else "",
            "Hb": Hb if Hb else "",
            "PLT": PLT if PLT else "",
            "ANC": ANC if ANC else "",
            "CRP": CRP if CRP else "",
            "Urine Alb (mg/L)": urine_albumin_mg_L if urine_albumin_mg_L else "",
            "Ferritin": Ferritin if "Ferritin" in locals() and Ferritin else "",
            "LDH": LDH if "LDH" in locals() and LDH else "",
            "Uric acid": UricAcid if "UricAcid" in locals() and UricAcid else "",
            "ESR": ESR if "ESR" in locals() and ESR else "",
            "Retic(%)": Retic if "Retic" in locals() and Retic else "",
            "β2-microglobulin": B2M if "B2M" in locals() and B2M else "",
            "Coombs": Coombs if "Coombs" in locals() and Coombs and Coombs!="-" else "",
            "AST": AST if "AST" in locals() and AST else "",
            "ALT": ALT if "ALT" in locals() and ALT else "",
            "ALP": ALP if "ALP" in locals() and ALP else "",
            "GGT": GGT if "GGT" in locals() and GGT else "",
            "Total bilirubin": TBILI if "TBILI" in locals() and TBILI else "",
            "Na": Na if "Na" in locals() and Na else "",
            "K": K if "K" in locals() and K else "",
            "Ca": Ca if "Ca" in locals() and Ca else "",
            "Mg": Mg if "Mg" in locals() and Mg else "",
            "Phos": Phos if "Phos" in locals() and Phos else "",
            "INR": INR if "INR" in locals() and INR else "",
            "aPTT": aPTT if "aPTT" in locals() and aPTT else "",
            "Fibrinogen": Fibrinogen if "Fibrinogen" in locals() and Fibrinogen else "",
            "D-dimer": Ddimer if "Ddimer" in locals() and Ddimer else "",
            "Triglycerides": TG if "TG" in locals() and TG else "",
            "Lactate": Lactate if "Lactate" in locals() and Lactate else "",
            "Urine Prot (mg/dL)": urine_protein_mg_dL if urine_protein_mg_dL else "",
            "Urine Cr (mg/dL)": urine_cr_mg_dL if urine_cr_mg_dL else "",
        }
        meta = {"user_key": user_key or "-", "diagnosis": diagnosis, "category": group}
        md = build_report_md(meta, values, derived, ped_msgs)
        txt = build_report_txt(md)
        pdf_bytes = build_report_pdf_bytes(md)

        cdl1, cdl2, cdl3 = st.columns(3)
        with cdl1:
            st.download_button("📄 결과 .md 다운로드", data=md, file_name=f"{user_key or 'result'}.md", disabled=not user_key)
        with cdl2:
            st.download_button("📝 결과 .txt 다운로드", data=txt, file_name=f"{user_key or 'result'}.txt", disabled=not user_key)
        with cdl3:
            st.download_button("🧾 결과 .pdf 다운로드", data=pdf_bytes, file_name=f"{user_key or 'result'}.pdf", disabled=not user_key)

        if user_key and st.button("💾 결과 저장 (별명#PIN 별 이력)"):
            ts = datetime.datetime.now().isoformat(timespec="milliseconds")
            row = {
                "timestamp": ts,
                "user_key": user_key,
                "category": group,
                "diagnosis": diagnosis,
                "WBC": WBC, "Hb": Hb, "PLT": PLT, "ANC": ANC, "CRP": CRP,
                "Urine Alb (mg/L)": urine_albumin_mg_L,
                "Urine Prot (mg/dL)": urine_protein_mg_dL,
                "Urine Cr (mg/dL)": urine_cr_mg_dL,
                "Ferritin": Ferritin if "Ferritin" in locals() else 0.0,
                "LDH": LDH if "LDH" in locals() else 0.0,
                "Uric acid": UricAcid if "UricAcid" in locals() else 0.0,
                "ESR": ESR if "ESR" in locals() else 0.0,
                "Retic(%)": Retic if "Retic" in locals() else 0.0,
                "β2-microglobulin": B2M if "B2M" in locals() else 0.0,
                "Coombs": Coombs if "Coombs" in locals() else "",
                "AST": AST if "AST" in locals() else 0.0,
                "ALT": ALT if "ALT" in locals() else 0.0,
                "ALP": ALP if "ALP" in locals() else 0.0,
                "GGT": GGT if "GGT" in locals() else 0.0,
                "Total bilirubin": TBILI if "TBILI" in locals() else 0.0,
                "Na": Na if "Na" in locals() else 0.0,
                "K": K if "K" in locals() else 0.0,
                "Ca": Ca if "Ca" in locals() else 0.0,
                "Mg": Mg if "Mg" in locals() else 0.0,
                "Phos": Phos if "Phos" in locals() else 0.0,
                "INR": INR if "INR" in locals() else 0.0,
                "aPTT": aPTT if "aPTT" in locals() else 0.0,
                "Fibrinogen": Fibrinogen if "Fibrinogen" in locals() else 0.0,
                "D-dimer": Ddimer if "Ddimer" in locals() else 0.0,
                "Triglycerides": TG if "TG" in locals() else 0.0,
                "Lactate": Lactate if "Lactate" in locals() else 0.0,
                "ACR (mg/g)": float(f"{acr:.2f}") if acr else 0.0,
                "UPCR (mg/g)": float(f"{upcr:.2f}") if upcr else 0.0,
                "Chemo": "; ".join(sel_chemo) if sel_chemo else "",
                "Antibiotics": "; ".join(sel_abx) if sel_abx else "",
            }

            # Duplicate-safe save: if same user_key & timestamp exists, add suffix; skip exact duplicates
            if os.path.exists(HISTORY_CSV):
                try:
                    df_exist = pd.read_csv(HISTORY_CSV)
                    if not df_exist.empty:
                        # exact duplicate row?
                        cols_chk = list(row.keys())
                        dup_mask = (df_exist[["user_key","timestamp"]]
                                    .assign(_join=1))  # dummy to avoid errors if subset missing
                        # Simple check: same user_key & timestamp
                        same_ts = (df_exist["user_key"]==row["user_key"]) & (df_exist["timestamp"]==row["timestamp"])
                        if same_ts.any():
                            row["timestamp"] = row["timestamp"] + "_1"
                except Exception:
                    pass
            save_row(row)
            st.success("저장 완료! 동일한 별명#PIN으로 누적 기록이 저장됩니다.")
            render_graphs(HISTORY_CSV, user_key)

        # 과거 기록이 있으면 바로 그래프 표시
        if user_key:
            try:
                render_graphs(HISTORY_CSV, user_key)
            except Exception:
                pass
