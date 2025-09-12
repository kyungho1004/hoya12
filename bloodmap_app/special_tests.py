# -*- coding: utf-8 -*-
import streamlit as st
from core_utils import clean_num

QUAL = ["없음", "+", "++", "+++"]

def _parse_avg(text: str):
    """쉼표/공백 구분 숫자들을 평균으로 환산 (빈칸/잘못된 값은 무시)."""
    if text is None:
        return None
    s = str(text).replace(";", ",").replace("/", ",").replace(" ", ",")
    vals = []
    for tok in s.split(","):
        tok = tok.strip()
        if not tok:
            continue
        try:
            vals.append(float(tok))
        except Exception:
            pass
    if not vals:
        return None
    return sum(vals) / len(vals)

def _badge(text, color="blue"):
    colors = {"green":"🟢","yellow":"🟡","red":"🔴","blue":"🔹"}
    return f"{colors.get(color,'🔹')} {text}"

def special_tests_ui():
    """특수검사: 카테고리 토글형 입력 + 해석 라인 반환"""
    lines = []
    with st.expander("🧪 특수검사 (토글)", expanded=False):
        # ===== 1) 소변검사 =====
        if st.toggle("소변검사", key="spec_u_toggle"):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                alb = st.selectbox("알부민뇨", QUAL, index=0, key="spec_u_alb")
            with col2:
                heme_q = st.selectbox("잠혈(질적)", QUAL, index=0, key="spec_u_hemeq")
            with col3:
                gly = st.selectbox("요당", QUAL, index=0, key="spec_u_gly")
            with col4:
                nit = st.selectbox("아질산염", ["없음","+"], index=0, key="spec_u_nit")
            # RBC/WBC 평균 입력(쉼표로 여러 번 입력 시 평균)
            r1, r2 = st.columns(2)
            with r1:
                rbc_txt = st.text_input("소변 RBC(/HPF) - 복수 입력 가능", key="spec_u_rbc_txt", placeholder="예) 0, 2, 5")
            with r2:
                wbc_txt = st.text_input("소변 WBC(/HPF) - 복수 입력 가능", key="spec_u_wbc_txt", placeholder="예) 0, 5, 12")
            rbc = _parse_avg(rbc_txt)
            wbc = _parse_avg(wbc_txt)
            # 해석
            if alb != "없음":
                msg = {"+" : "미세단백뇨 가능",
                       "++": "단백뇨 — 신장질환 의심",
                       "+++":"단백뇨 고도 — 신증후군/사구체질환 평가 필요"}[alb]
                lines.append(_badge(f"알부민뇨 {alb} → {msg}", "red" if alb=="+++" else "yellow"))
            if heme_q != "없음":
                lines.append(_badge(f"소변 잠혈 {heme_q} → 혈뇨 가능", "yellow"))
            if gly != "없음":
                lines.append(_badge(f"요당 {gly} → 고혈당/당뇨 평가 필요", "yellow"))
            if nit == "+":
                lines.append(_badge("아질산염 양성 → 세균성 UTI 의심", "yellow"))
            if rbc is not None:
                if rbc > 25: lines.append(_badge(f"RBC 평균 {rbc:.1f}/HPF → 현저한 혈뇨", "red"))
                elif rbc >= 3: lines.append(_badge(f"RBC 평균 {rbc:.1f}/HPF → 현미경적 혈뇨", "yellow"))
                else: lines.append(_badge(f"RBC 평균 {rbc:.1f}/HPF 정상범위", "green"))
            if wbc is not None:
                if wbc > 50: lines.append(_badge(f"WBC 평균 {wbc:.1f}/HPF → 뇨로감염 의심", "red"))
                elif wbc >= 10: lines.append(_badge(f"WBC 평균 {wbc:.1f}/HPF → 무증상/경도 염증 가능", "yellow"))
                else: lines.append(_badge(f"WBC 평균 {wbc:.1f}/HPF 정상범위", "green"))

        # ===== 2) 보체(C3/C4) =====
        if st.toggle("보체 (C3/C4)", key="spec_c_toggle"):
            c1, c2 = st.columns(2)
            with c1:
                c3 = st.text_input("C3 (mg/dL)", key="spec_c3")
            with c2:
                c4 = st.text_input("C4 (mg/dL)", key="spec_c4")
            C3 = clean_num(c3); C4 = clean_num(c4)
            if C3 is not None:
                if C3 < 90: lines.append(_badge(f"C3 {C3} ↓ → 보체 소모(자가면역/감염) 고려", "yellow"))
                elif C3 > 180: lines.append(_badge(f"C3 {C3} ↑ → 급성염증/비특이적 상승", "yellow"))
                else: lines.append(_badge(f"C3 {C3} 정상범위", "green"))
            if C4 is not None:
                if C4 < 10: lines.append(_badge(f"C4 {C4} ↓ → 루푸스/보체소모증 가능", "yellow"))
                elif C4 > 40: lines.append(_badge(f"C4 {C4} ↑ → 염증/비특이적 상승", "yellow"))
                else: lines.append(_badge(f"C4 {C4} 정상범위", "green"))

        # ===== 3) 지질검사 =====
        if st.toggle("지질검사 (TG/HDL/LDL)", key="spec_lip_toggle"):
            l1, l2, l3 = st.columns(3)
            with l1: tg = st.text_input("TG (mg/dL)", key="spec_tg")
            with l2: hdl = st.text_input("HDL (mg/dL)", key="spec_hdl")
            with l3: ldl = st.text_input("LDL (mg/dL)", key="spec_ldl")
            TG = clean_num(tg); HDL = clean_num(hdl); LDL = clean_num(ldl)
            if TG is not None:
                if TG >= 200: lines.append(_badge(f"TG {TG} ≥200 → 고중성지방혈증", "red"))
                elif TG >= 150: lines.append(_badge(f"TG {TG} 150~199 → 경계/주의", "yellow"))
                else: lines.append(_badge(f"TG {TG} 정상범위", "green"))
            if HDL is not None:
                if HDL < 40: lines.append(_badge(f"HDL {HDL} <40 → 낮음", "yellow"))
                else: lines.append(_badge(f"HDL {HDL} 양호", "green"))
            if LDL is not None:
                if LDL >= 160: lines.append(_badge(f"LDL {LDL} ≥160 → 높음", "red"))
                elif LDL >= 130: lines.append(_badge(f"LDL {LDL} 130~159 → 경계", "yellow"))
                else: lines.append(_badge(f"LDL {LDL} 양호", "green"))

        # ===== 4) 심부전 지표 =====
        if st.toggle("심부전 지표 (BNP / NT-proBNP)", key="spec_hf_toggle"):
            h1, h2 = st.columns(2)
            with h1: bnp = st.text_input("BNP (pg/mL)", key="spec_bnp")
            with h2: ntp = st.text_input("NT-proBNP (pg/mL)", key="spec_ntp")
            BNP = clean_num(bnp); NTP = clean_num(ntp)
            if BNP is not None:
                if BNP > 100: lines.append(_badge(f"BNP {BNP} >100 → 심부전/심장 스트레스 가능", "yellow" if BNP<=400 else "red"))
                else: lines.append(_badge(f"BNP {BNP} 정상범위", "green"))
            if NTP is not None:
                if NTP > 125: lines.append(_badge(f"NT-proBNP {NTP} >125 → 상승", "yellow" if NTP<=900 else "red"))
                else: lines.append(_badge(f"NT-proBNP {NTP} 정상범위", "green"))

        # ===== 5) 당 검사 =====
        if st.toggle("당 검사 (식전/식후 1시간/2시간)", key="spec_glu_toggle"):
            g1, g2, g3 = st.columns(3)
            with g1: fpg = st.text_input("식전(FPG)", key="spec_fpg")
            with g2: pp1 = st.text_input("식후 1시간", key="spec_pp1")
            with g3: pp2 = st.text_input("식후 2시간", key="spec_pp2")
            FPG = clean_num(fpg); PP1 = clean_num(pp1); PP2 = clean_num(pp2)
            if FPG is not None:
                if FPG >= 126: lines.append(_badge(f"식전 {FPG} ≥126 → 당뇨 기준", "red"))
                elif FPG >= 100: lines.append(_badge(f"식전 {FPG} 100~125 → 공복혈당장애", "yellow"))
                else: lines.append(_badge(f"식전 {FPG} 정상범위", "green"))
            if PP1 is not None:
                if PP1 > 180: lines.append(_badge(f"식후 1시간 {PP1} >180 → 고혈당", "yellow"))
                else: lines.append(_badge(f"식후 1시간 {PP1} 목표 범위", "green"))
            if PP2 is not None:
                if PP2 > 140: lines.append(_badge(f"식후 2시간 {PP2} >140 → 내당능 저하/고혈당", "yellow"))
                else: lines.append(_badge(f"식후 2시간 {PP2} 목표 범위", "green"))
        # ===== 6) 근육/근손상 지표 (CK / 미오글로빈) =====
        if st.toggle("근육/근손상 (CK / 미오글로빈)", key="spec_muscle_toggle"):
            m1, m2 = st.columns(2)
            with m1: ck_txt = st.text_input("CK (U/L)", key="spec_ck")
            with m2: myo_txt = st.text_input("미오글로빈 (ng/mL)", key="spec_myo")
            CK = clean_num(ck_txt); MYO = clean_num(myo_txt)
            if CK is not None:
                if CK >= 1000: lines.append(_badge(f"CK {CK} ≥1000 → 횡문근융해 의심, 응급 평가 권고", "red"))
                elif CK >= 200: lines.append(_badge(f"CK {CK} 200~999 → 상승: 근손상/격한운동/근염 등", "yellow"))
                else: lines.append(_badge(f"CK {CK} 정상범위", "green"))
            if MYO is not None:
                if MYO >= 85: lines.append(_badge(f"미오글로빈 {MYO} ≥85 → 근손상 가능", "yellow"))
                else: lines.append(_badge(f"미오글로빈 {MYO} 정상범위", "green"))

        # ===== 7) 소변 비율 (UPCR: 요 단백/크레아티닌) =====
        if st.toggle("소변 비율 (UPCR: 단백/크레아티닌)", key="spec_upcr_toggle"):
            u1, u2, u3 = st.columns(3)
            with u1: u_pro_txt = st.text_input("요 단백 (mg/dL)", key="spec_upcr_pro")
            with u2: u_cr_txt  = st.text_input("요 크레아티닌 (mg/dL)", key="spec_upcr_cr")
            # 연령 구분
            age_group = st.selectbox("연령 구분", ["성인","소아 ≥24개월","소아 6~24개월","소아 <6개월"], index=0,
                                     help="가능하면 아이 월령(age_m)을 세션에 넣으면 자동 선택될 수 있습니다.")
            UPRO = clean_num(u_pro_txt); UCR = clean_num(u_cr_txt)
            ratio = None
            if (UPRO is not None) and (UCR not in (None, 0)):
                ratio = UPRO / UCR
                if age_group == "성인":
                    norm, neph = 0.2, 3.5
                elif age_group == "소아 ≥24개월":
                    norm, neph = 0.2, 2.0
                elif age_group == "소아 6~24개월":
                    norm, neph = 0.5, 2.0
                else:
                    norm, neph = 0.8, 2.0
                if ratio < norm:
                    lines.append(_badge(f"UPCR {ratio:.2f} → 정상( < {norm} )", "green"))
                elif ratio < neph:
                    lines.append(_badge(f"UPCR {ratio:.2f} → 단백뇨( {norm} ~ {neph} )", "yellow"))
                else:
                    lines.append(_badge(f"UPCR {ratio:.2f} → 신증후군 범위( ≥ {neph} )", "red"))
            else:
                lines.append("UPCR 계산을 위해 요 단백과 요 크레아티닌을 입력하세요.")

        # ===== 8) 신장/대사 지표 (BUN) =====
        if st.toggle("신장/대사 지표 (BUN)", key="spec_kidney_toggle"):
            bun_txt = st.text_input("BUN (요소질소, mg/dL)", key="spec_bun_txt")
            BUN = clean_num(bun_txt)
            if BUN is not None:
                if BUN > 23: lines.append(_badge(f"BUN {BUN} >23 → 상승: 탈수/신장기능 저하 등 감별", "yellow"))
                else: lines.append(_badge(f"BUN {BUN} 정상범위", "green"))
    

    # 결과가 없으면 안내
    if not lines:
        lines.append("입력값이 없어 해석할 내용이 없습니다.")
    return lines
