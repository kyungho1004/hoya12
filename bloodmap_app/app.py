# -*- coding: utf-8 -*-
import streamlit as st
from datetime import datetime

# ====================== App Setup ======================
st.set_page_config(page_title="피수치 홈", layout="wide")

# ---------------------- Helpers -----------------------
def entered(x):
    return x is not None and x != ""

def num_input(label, key=None, step=0.1, decimals=1, placeholder=""):
    v = st.text_input(label, key=key, placeholder=placeholder)
    if v is None or v == "":
        return None
    try:
        if decimals == 0:
            return int(float(v))
        return round(float(v), decimals)
    except Exception:
        return None

def calc_corrected_ca(ca, alb):
    try:
        ca = float(ca); alb = float(alb)
        return round(ca + 0.8*(4.0 - alb), 1)
    except Exception:
        return None

def calc_homa_ir(glu_f, insulin):
    try:
        return round((float(glu_f) * float(insulin)) / 405.0, 2)
    except Exception:
        return None

def calc_friedewald_ldl(tc, hdl, tg):
    try:
        tg = float(tg)
        if tg >= 400:
            return None
        return round(float(tc) - float(hdl) - (tg/5.0), 1)
    except Exception:
        return None

def stage_egfr(egfr):
    try:
        e = float(egfr)
    except Exception:
        return None, None
    if e >= 90:   return "G1", "정상/고정상 (≥90)"
    if 60 <= e < 90:  return "G2", "경도 감소 (60–89)"
    if 45 <= e < 60:  return "G3a", "중등도 감소 (45–59)"
    if 30 <= e < 45:  return "G3b", "중등도~중증 감소 (30–44)"
    if 15 <= e < 30:  return "G4", "중증 감소 (15–29)"
    return "G5", "신부전 (<15)"

def stage_acr(acr_mg_g):
    try:
        a = float(acr_mg_g)
    except Exception:
        return None, None
    if a < 30: return "A1", "정상-경도 증가 (<30 mg/g)"
    if a <= 300: return "A2", "중등도 증가 (30–300 mg/g)"
    return "A3", "중증 증가 (>300 mg/g)"

def child_pugh_score(albumin, bilirubin, inr, ascites, enceph):
    """Return (score, class). If albumin/bilirubin/INR any missing -> (0, None)."""
    def _alb(a):
        try:
            a = float(a)
        except Exception:
            return None
        if a > 3.5:
            return 1
        elif 2.8 <= a <= 3.5:
            return 2
        else:
            return 3

    def _tb(b):
        try:
            b = float(b)
        except Exception:
            return None
        if b < 2:
            return 1
        elif 2 <= b <= 3:
            return 2
        else:
            return 3

    def _inr(x):
        try:
            x = float(x)
        except Exception:
            return None
        if x < 1.7:
            return 1
        elif 1.7 <= x <= 2.3:
            return 2
        else:
            return 3

    def _cat(v):
        mapping = {"없음": 1, "경미": 2, "중증": 3}
        return mapping.get(v, 0)

    a_s = _alb(albumin)
    b_s = _tb(bilirubin)
    i_s = _inr(inr)

    if a_s is None or b_s is None or i_s is None:
        return 0, None

    total = a_s + b_s + i_s + _cat(ascites) + _cat(enceph)
    if 5 <= total <= 6:
        klass = "A"
    elif 7 <= total <= 9:
        klass = "B"
    else:
        klass = "C"
    return total, klass

# ---------------------- Session -----------------------
if "records" not in st.session_state:
    st.session_state.records = {}

st.title("🩺 피수치 홈")
st.caption("모바일 친화 · PIN 중복방지 · 보고서 출력")

# Nick & PIN (4 digits)
c1, c2 = st.columns([2,1])
with c1:
    nick = st.text_input("별명", placeholder="예: 하늘이아빠")
with c2:
    pin = st.text_input("4자리 PIN", max_chars=4, placeholder="0000")
nickname_key = f"{nick}#{pin}" if nick and pin and len(pin)==4 and pin.isdigit() else None
if not nickname_key:
    st.warning("별명과 4자리 PIN(숫자 4자리)을 입력하세요.")
else:
    st.success(f"세션: {nickname_key}")

mode = st.selectbox("모드 선택", ["일반/암", "소아(일상/호흡기)", "소아(감염질환)"])
expert_mode = st.checkbox("🧑‍⚕️ 전문가 모드", value=False, help="전문가용 계산기/가이드를 표시합니다.")

# ---------------------- Containers --------------------
vals = {}
extra = {}
meta = {"nickname": nick, "pin": pin, "time": datetime.now().strftime("%Y-%m-%d %H:%M")}

# =================== Mode: 일반/암 =====================
if mode == "일반/암":
    st.subheader("🧪 기본 입력")
    cg = st.columns(5)
    with cg[0]: vals["Ca"] = num_input("칼슘 Ca (mg/dL)", "ca", decimals=1, placeholder="예: 8.8")
    with cg[1]: vals["Albumin"] = num_input("Albumin (g/dL)", "alb", decimals=1, placeholder="예: 3.0")
    with cg[2]: vals["Creatinine"] = num_input("Creatinine (mg/dL)", "cr", decimals=1, placeholder="예: 1.2")
    with cg[3]: vals["Glucose(f)"] = num_input("공복혈당 (mg/dL)", "glu", decimals=0, placeholder="예: 100")
    with cg[4]:
        insulin_opt = st.checkbox("인슐린 수치 입력", value=False)
        if insulin_opt:
            vals["Insulin"] = num_input("인슐린 (µIU/mL)", "ins", decimals=1, placeholder="예: 10")

    # ECOG
    with st.expander("🧍 ECOG 수행도 (0–4)", expanded=False):
        ecog = st.selectbox("ECOG", ["", "0", "1", "2", "3", "4"], index=0)
        if ecog: extra["ECOG"] = ecog

    # Child-Pugh
    with st.expander("🧮 Child-Pugh 계산기 (간암/HCC 우선 사용)", expanded=False):
        cp_c1, cp_c2, cp_c3 = st.columns(3)
        with cp_c1:
            cp_albumin = num_input("Albumin (g/dL)", "cp_alb", decimals=1)
            cp_bili = num_input("Total Bilirubin (mg/dL)", "cp_tb", decimals=1)
        with cp_c2:
            cp_inr = num_input("INR", "cp_inr", decimals=2)
            ascites = st.selectbox("복수", ["없음","경미","중증"])
        with cp_c3:
            enceph = st.selectbox("간성뇌병증", ["없음","경미","중증"])
        extra["Child-Pugh 입력"] = {"Alb": cp_albumin, "TB": cp_bili, "INR": cp_inr, "Ascites": ascites, "Encephalopathy": enceph}
        sc, klass = child_pugh_score(cp_albumin, cp_bili, cp_inr, ascites, enceph)
        if sc and sc >= 5:
            st.info(f"Child-Pugh 총점: **{sc}** → 등급 **{klass}**")
            extra["Child-Pugh Score/Class"] = f"{sc} ({klass})"

    # 암 그룹 & 진단
    st.subheader("🧬 암 그룹/진단 선택")
    group = st.selectbox("암 그룹 선택", ["미선택/일반", "혈액암", "고형암", "육종", "희귀암"])
    cancer = ""
    if group == "혈액암":
        heme_display = [
            "급성 골수성 백혈병(AML)",
            "급성 전골수구성 백혈병(APL)",
            "급성 림프모구성 백혈병(ALL)",
            "만성 골수성 백혈병(CML)",
            "만성 림프구성 백혈병(CLL)",
        ]
        cancer = st.selectbox("혈액암(진단명)", heme_display)

    elif group == "고형암":
        cancer = st.selectbox("고형암(진단명)", [
            "폐암(Lung cancer)","유방암(Breast cancer)","위암(Gastric cancer)",
            "대장암(Colorectal cancer)","간암(HCC)","췌장암(Pancreatic cancer)",
            "담도암(Cholangiocarcinoma)","자궁내막암(Endometrial cancer)",
            "구강암/후두암","피부암(흑색종)","신장암(RCC)",
            "갑상선암","난소암","자궁경부암","전립선암","뇌종양(Glioma)","식도암","방광암"
        ])

    elif group == "육종":
        cancer = st.selectbox("육종(진단명)", [
            "골육종(Osteosarcoma)","연부조직 육종(Soft tissue sarcoma)"
        ])

    elif group == "희귀암":
        cancer = st.selectbox("희귀암(진단명)", [
            "지정 없음(기타)"
        ])

    # TOP 패널
    st.subheader("🔲 TOP 패널 (토글로 확장)")
    # 빈혈
    t_anemia = st.checkbox("빈혈 패널", value=False)
    if t_anemia:
        c = st.columns(4)
        with c[0]: extra["Fe"] = num_input("철 Fe (µg/dL)", "fe", decimals=0)
        with c[1]: extra["Ferritin"] = num_input("Ferritin (Fer, ng/mL)", "ferr", decimals=0)
        with c[2]: extra["TIBC"] = num_input("TIBC (Total Iron Binding Capacity, µg/dL)", "tibc", decimals=0)
        with c[3]: extra["TSAT(%)"] = num_input("Transferrin Sat. (TSAT, %)", "tsat", decimals=1)
        c2 = st.columns(3)
        with c2[0]: extra["Retic(%)"] = num_input("망상적혈구(%) (Retic %)", "retic", decimals=1)
        with c2[1]: extra["Vit B12"] = num_input("비타민 B12 (pg/mL)", "b12", decimals=0)
        with c2[2]: extra["Folate"] = num_input("엽산(Folate, ng/mL)", "folate", decimals=1)

    # 전해질 확장
    t_elec = st.checkbox("전해질 확장", value=False)
    if t_elec:
        c = st.columns(4)
        with c[0]: extra["Mg"] = num_input("Magnesium (mg/dL)", "mg", decimals=2)
        with c[1]: extra["Phos"] = num_input("Phosphate (Phos/P, mg/dL)", "phos", decimals=1)
        with c[2]: extra["iCa"] = num_input("이온화칼슘 iCa (iCa, mmol/L)", "ica", decimals=2)
        with c[3]:
            if entered(vals.get("Ca")) and entered(vals.get("Albumin")):
                ca_corr = calc_corrected_ca(vals["Ca"], vals["Albumin"])
                if ca_corr is not None:
                    st.info(f"보정 칼슘(Alb 반영): **{ca_corr} mg/dL**")
                    st.caption("공식: Ca + 0.8×(4.0 - Alb), mg/dL 기준")
                    extra["Corrected Ca"] = ca_corr

    # 신장/단백뇨
    t_kid = st.checkbox("신장/단백뇨 패널", value=False)
    if t_kid:
        c = st.columns(4)
        with c[0]: age = num_input("나이 (세)", "age", decimals=0, placeholder="예: 60")
        with c[1]: sex = st.selectbox("성별", ["F","M"])
        with c[2]:
            if entered(vals.get("Creatinine")) and entered(age):
                try:
                    cr = float(vals["Creatinine"]); a = float(age)
                    egfr = round(142 * min(cr/0.7,1)**-0.241 * max(cr/0.7,1)**-1.2 * (0.9938**a) * (1.012 if sex=="F" else 1.0), 0)
                except Exception:
                    egfr = None
                if egfr is not None:
                    st.info(f"eGFR(자동계산): **{egfr} mL/min/1.73m²**")
                    extra["eGFR"] = egfr
                    g, gl = stage_egfr(egfr)
                    if g:
                        st.caption(f"CKD G-stage: **{g}** · {gl}")
                        extra["CKD G-stage"] = f"{g} ({gl})"
        with c[3]:
            st.caption("UACR/UPCR 정량은 아래 요검사(정량)에서 입력")

    # 갑상선
    t_thy = st.checkbox("갑상선 패널", value=False)
    if t_thy:
        c = st.columns(3)
        with c[0]: extra["TSH"] = num_input("TSH (µIU/mL)", "tsh", 0.1, 2)
        with c[1]: extra["FT4"] = num_input("Free T4 (ng/dL)", "ft4", 0.1, 2)
        with c[2]:
            if st.checkbox("Total T3 추가", value=False):
                extra["TT3"] = num_input("Total T3 (ng/dL)", "tt3", 1, 0)

    # 염증/패혈증
    t_sep = st.checkbox("염증/패혈증 패널", value=False)
    if t_sep:
        c = st.columns(3)
        with c[0]: extra["CRP"] = num_input("CRP (mg/dL)", "crp", 0.1, 2)
        with c[1]: extra["PCT"] = num_input("Procalcitonin (PCT, ng/mL)", "pct", 0.1, 2)
        with c[2]: extra["Lactate"] = num_input("Lactate (mmol/L)", "lac", 0.1, 1)

    # 당대사/대사증후군
    t_meta = st.checkbox("당대사/대사증후군", value=False)
    if t_meta:
        if entered(vals.get("Glucose(f)")) and insulin_opt and entered(vals.get("Insulin")):
            h = calc_homa_ir(vals["Glucose(f)"], vals["Insulin"])
            if h is not None:
                st.info(f"HOMA-IR: **{h}**")
                st.caption("HOMA-IR = (공복혈당×인슐린)/405")
                extra["HOMA-IR"] = h

    # 지질 확장
    t_lipid = st.checkbox("지질 확장", value=False)
    if t_lipid:
        c = st.columns(4)
        with c[0]: tc = num_input("Total Cholesterol (mg/dL)", "tc", 1, 0)
        with c[1]: hdl = num_input("HDL-C (mg/dL)", "hdl", 1, 0)
        with c[2]: tg = num_input("Triglyceride (mg/dL)", "tg", 1, 0)
        with c[3]: extra["ApoB"] = num_input("ApoB (mg/dL)", "apob", 1, 0)
        if entered(tc) and entered(hdl):
            non_hdl = round(tc - hdl, 0)
            st.info(f"Non-HDL-C: **{non_hdl} mg/dL**")
            extra["Non-HDL-C"] = non_hdl
        if entered(tc) and entered(hdl) and entered(tg):
            if float(tg) >= 400:
                st.warning("TG ≥ 400 mg/dL: Friedewald LDL 계산이 비활성화됩니다.")
            else:
                ldl = calc_friedewald_ldl(tc, hdl, tg)
                if ldl is not None:
                    st.info(f"Friedewald LDL: **{ldl} mg/dL**")

    # 요검사(정성/정량)
    with st.expander("🧫 요검사(기본) — 정성 + 정량(선택)", expanded=False):
        cq = st.columns(4)
        with cq[0]: hematuria_q = st.selectbox("혈뇨(정성)", ["", "+", "++", "+++"], index=0)
        with cq[1]: proteinuria_q = st.selectbox("단백뇨(정성)", ["", "-", "+", "++"], index=0)
        with cq[2]: wbc_q = st.selectbox("백혈구(정성)", ["", "-", "+", "++"], index=0)
        with cq[3]: gly_q = st.selectbox("요당(정성)", ["", "-", "+++"], index=0)
        _desc_hema = {"+":"소량 검출","++":"중등도 검출","+++":"고농도 검출"}
        _desc_prot = {"-":"음성","+":"경도 검출","++":"중등도 검출"}
        _desc_wbc  = {"-":"음성","+":"의심 수준","++":"양성"}
        _desc_gly  = {"-":"음성","+++":"고농도 검출"}
        if hematuria_q: extra["혈뇨(정성)"] = f"{hematuria_q} ({_desc_hema.get(hematuria_q,'')})"
        if proteinuria_q: extra["단백뇨(정성)"] = f"{proteinuria_q} ({_desc_prot.get(proteinuria_q,'')})"
        if wbc_q: extra["백혈구뇨(정성)"] = f"{wbc_q} ({_desc_wbc.get(wbc_q,'')})"
        if gly_q: extra["요당(정성)"] = f"{gly_q} ({_desc_gly.get(gly_q,'')})"

        with st.expander("정량(선택) — UPCR/ACR 계산", expanded=False):
            u_prot = num_input("요단백 (mg/dL)", "ex_upr", 0.1, 1)
            u_cr   = num_input("소변 Cr (mg/dL)", "ex_ucr", 0.1, 1)
            u_alb  = num_input("소변 알부민 (mg/L)", "ex_ualb", 0.1, 1)
            upcr = acr = None
            if entered(u_cr) and entered(u_prot):
                upcr = round((u_prot * 1000.0) / float(u_cr), 1)
                st.info(f"UPCR(요단백/Cr): **{upcr} mg/g** (≈ 1000×[mg/dL]/[mg/dL])")
            if entered(u_cr) and entered(u_alb):
                acr = round((u_alb * 100.0) / float(u_cr), 1)
                st.info(f"ACR(소변 알부민/Cr): **{acr} mg/g** (≈ 100×[mg/L]/[mg/dL])")
            if acr is not None:
                extra["ACR(mg/g)"] = acr
                a, a_label = stage_acr(acr)
                if a:
                    st.caption(f"Albuminuria A-stage: **{a}** · {a_label}")
                    extra["Albuminuria stage"] = f"{a} ({a_label})"
            if upcr is not None:
                extra["UPCR(mg/g)"] = upcr

    # 특수 검사 (보체)
    with st.expander("🧬 특수 검사 (보체)", expanded=False):
        col = st.columns(3)
        with col[0]: extra["C3"] = num_input("보체 C3 (mg/dL)", "c3", 1, 0)
        with col[1]: extra["C4"] = num_input("보체 C4 (mg/dL)", "c4", 1, 0)
        with col[2]: extra["CH50"] = num_input("CH50 (U/mL)", "ch50", 1, 0)

    # 항암제/항생제 + 프리셋
    st.markdown("### 💊 항암제/항생제")
    preset = st.selectbox("레짐 프리셋", ["없음","APL(ATRA+ATO)","유방 AC-T","대장 FOLFOX","대장 FOLFIRI","림프종 CHOP"], index=0)
    if st.button("프리셋 적용"):
        preset_map = {
            "없음": [],
            "APL(ATRA+ATO)": ["ATRA","Arsenic trioxide","Idarubicin","6-MP","MTX"],
            "유방 AC-T": ["Doxorubicin","Cyclophosphamide","Paclitaxel"],
            "대장 FOLFOX": ["Oxaliplatin","5-FU","Leucovorin"],
            "대장 FOLFIRI": ["Irinotecan","5-FU","Leucovorin"],
            "림프종 CHOP": ["Cyclophosphamide","Doxorubicin","Vincristine","Prednisolone"],
        }
        st.session_state["selected_drugs"] = preset_map.get(preset, [])
    drug_choices = ["ATRA","Arsenic trioxide","Idarubicin","Daunorubicin","6-MP","MTX","Cyclophosphamide","Doxorubicin","Paclitaxel","Oxaliplatin","5-FU","Leucovorin","Irinotecan","Vincristine","Prednisolone"]
    selected = st.multiselect("항암제(한글/영문 혼용 가능)", drug_choices, default=st.session_state.get("selected_drugs", []), key="selected_drugs")
    abx = st.text_input("항생제(한글 표기 가능, 쉼표로 구분)", placeholder="예: 세프트리악손, 아지스로마이신")
    if selected: extra["항암제"] = selected
    if abx: extra["항생제"] = [x.strip() for x in abx.split(",") if x.strip()]

    # 전문가 도구 (토글)
    if expert_mode:
        st.subheader("🧪 전문가 도구 (전문가 전용)")
        with st.expander("BSA / 체중기반 용량 계산 (Mosteller)", expanded=False):
            wt = st.text_input("체중 (kg)", key="exp_wt", placeholder="예: 60")
            ht = st.text_input("신장 (cm)", key="exp_ht", placeholder="예: 165")
            dose_mg_m2 = st.text_input("약제 용량 (mg/m²)", key="exp_dose_m2", placeholder="예: 75 (선택)")
            try:
                w = float(wt) if wt else None
                h = float(ht) if ht else None
            except Exception:
                w = h = None
            if w and h:
                try:
                    bsa = round(((w * h) / 3600.0) ** 0.5, 2)
                    st.info(f"BSA: **{bsa} m²** (Mosteller)")
                    if dose_mg_m2:
                        d = float(dose_mg_m2); total = round(d * bsa, 1)
                        st.success(f"총 용량: **{total} mg** ( {d} mg/m² × {bsa} m² )")
                except Exception:
                    st.warning("BSA 계산 실패")
        with st.expander("간/신기능 용량 감량 힌트 (참고용)", expanded=False):
            g = extra.get("eGFR"); cp = extra.get("Child-Pugh Score/Class")
            if g is not None:
                try:
                    g = float(g)
                    if g < 30: st.error("eGFR < 30: 감량/회피 고려")
                    elif g < 60: st.warning("eGFR 30–59: 주의")
                    else: st.info("eGFR ≥ 60: 통상 범주")
                except: pass
            if cp:
                if "C" in str(cp): st.error("Child-Pugh C: 감량/금기 검토")
                elif "B" in str(cp): st.warning("Child-Pugh B: 감량 고려")
                elif "A" in str(cp): st.info("Child-Pugh A: 통상 범주")
        with st.expander("빈혈 미니 알고리즘 (Ferritin/TSAT/Retic 참고)", expanded=False):
            fer = extra.get("Ferritin"); tsat = extra.get("TSAT(%)"); retic = extra.get("Retic(%)")
            msgs = []
            try:
                if fer is not None and float(fer) < 30: msgs.append("Ferritin < 30 → 철결핍 가능")
                if tsat is not None and float(tsat) < 20: msgs.append("TSAT < 20% → 철결핍 의심")
                if retic is not None and float(retic) < 1.0: msgs.append("Retic 낮음 → 생산 저하 가능")
            except: pass
            if msgs:
                for m in msgs: st.warning("• " + m)
            else:
                st.info("입력 값이 부족하거나 기준 해당 없음")

# ==================== Mode: 소아(일상) ===================
elif mode == "소아(일상/호흡기)":
    st.subheader("👶 기본 입력")
    c = st.columns(3)
    with c[0]: age_m = num_input("나이(개월)", "ped_age_m", 1, 0, "예: 18")
    with c[1]: temp_c = num_input("체온(℃)", "ped_temp", 0.1, 1, "예: 38.2")
    with c[2]:
        spo2_na = st.checkbox("산소포화도 측정기 없음/측정 불가", value=True, key="ped_spo2_na")
        if not spo2_na:
            spo2 = num_input("산소포화도(%)", "ped_spo2", 1, 0, "예: 96")
        else:
            spo2 = None

    with st.expander("👶 증상(간단 선택)", expanded=True):
        runny = st.selectbox("콧물", ["없음","흰색","노란색","피섞임"], key="ped_runny")
        cough_sev = st.selectbox("기침", ["없음","조금","보통","심함"], key="ped_cough_sev")
        extra["ped_simple_sym"] = {"콧물": runny, "기침": cough_sev}

    with st.expander("👀 보호자 관찰 체크리스트", expanded=False):
        obs = {}
        obs["숨 가빠보임(호흡곤란)"] = st.checkbox("숨 가빠보임(호흡곤란)")
        obs["청색증 의심(입술/손발)"] = st.checkbox("청색증 의심(입술/손발)")
        obs["말수 감소·축 늘어짐/보챔"] = st.checkbox("말수 감소·축 늘어짐/보챔")
        obs["탈수 의심(마른 입/눈물↓/소변↓)"] = st.checkbox("탈수 의심(마른 입술/눈물 적음/소변 감소)")
        obs["고열(≥40.0℃)"] = st.checkbox("고열(≥40.0℃)")
        obs["3개월 미만 발열(≥38.0℃)"] = st.checkbox("3개월 미만 발열(≥38.0℃)")
        obs["경련(열성경련 포함)"] = st.checkbox("경련(열성경련 포함)")
        extra["ped_obs"] = {k:v for k,v in obs.items() if v}

    with st.expander("🧮 해열제 용량 계산기", expanded=False):
        wt = st.text_input("체중(kg)", key="antipy_wt", placeholder="예: 10.5")
        med = st.selectbox("해열제", ["아세트아미노펜(acetaminophen)", "이부프로펜(ibuprofen)"], key="antipy_med")
        if med.startswith("아세트"):
            conc = st.selectbox("시럽 농도", ["160 mg/5 mL", "120 mg/5 mL"], key="antipy_conc_acet")
            default_mgkg = 15
        else:
            conc = st.selectbox("시럽 농도", ["100 mg/5 mL"], key="antipy_conc_ibu")
            default_mgkg = 10
        st.caption(f"계산 기준: {default_mgkg} mg/kg (1회분)")
        try:
            w = float(wt)
            mg_num = int(conc.split("mg/")[0])
            ml_denom = int(conc.split("mg/")[1].split()[0].replace("mL",""))
            mg = int(round(w * default_mgkg))
            ml = round(mg * ml_denom / mg_num, 1)
            st.success(f"권장 1회 용량: **{ml} mL** ({conc}) — 체중 {w:g} kg 기준")
            st.caption("참고: Acetaminophen 10–15 mg/kg, Ibuprofen 5–10 mg/kg. 보호자 편의를 위해 단일 기준으로 계산합니다.")
        except Exception:
            st.info("체중을 입력하면 1회 권장 mL가 계산됩니다.")

# =================== Mode: 소아(감염) ===================
else:
    st.subheader("🧒 감염질환 선택")
    infect_sel = st.selectbox("질환", ["아데노바이러스(PCF)","파라인플루엔자","RSV","인플루엔자","로타","노로","기타"])

    with st.expander("🧒 증상 체크리스트", expanded=True):
        sel_sym = []
        name_l = (infect_sel or "").lower()
        base_sym = None
        if ("아데노" in name_l) or ("adeno" in name_l) or ("pcf" in name_l):
            base_sym = ["발열","결막 충혈","눈곱","인후통"]
        elif ("파라" in name_l) or ("parainfluenza" in name_l):
            base_sym = ["발열","기침","콧물"]
        elif ("로타" in name_l) or ("rotavirus" in name_l) or ("노로" in name_l) or ("norovirus" in name_l):
            base_sym = ["설사","구토","탈수 의심"]
        elif ("rsv" in name_l):
            base_sym = ["쌕쌕거림(천명)","흉곽 함몰","무호흡"]
        elif ("인플루엔자" in name_l) or ("influenza" in name_l) or ("독감" in name_l):
            base_sym = ["고열(≥38.5℃)","근육통/전신통","기침"]
        if not base_sym:
            base_sym = ["발열","기침","콧물"]
        for i, s in enumerate(base_sym):
            if st.checkbox(s, key=f"sym_{infect_sel}_{i}"):
                sel_sym.append(s)
        st.session_state["infect_symptoms"] = sel_sym

    with st.expander("🧒 기본 활력/계측 입력", expanded=False):
        age_m_gi = st.text_input("나이(개월)", key="pedinf_age_m", placeholder="예: 18")
        temp_c_gi = st.text_input("체온(℃)", key="pedinf_temp_c", placeholder="예: 38.2")
        rr_gi = st.text_input("호흡수(/분)", key="pedinf_rr", placeholder="예: 42")
        spo2_na_gi = st.checkbox("산소포화도 측정기 없음/측정 불가", key="pedinf_spo2_na", value=True)
        if not spo2_na_gi:
            spo2_gi = st.text_input("산소포화도(%)", key="pedinf_spo2", placeholder="예: 96")
        else:
            spo2_gi = ""
        hr_gi = st.text_input("심박수(/분)", key="pedinf_hr", placeholder="예: 120")
        wt_kg_gi = st.text_input("체중(kg)", key="pedinf_wt", placeholder="예: 10.5")

    with st.expander("👀 보호자 관찰 체크리스트", expanded=False):
        obs2 = {}
        obs2["숨 가빠보임(호흡곤란)"] = st.checkbox("숨 가빠보임(호흡곤란)", key="gi_obs1")
        obs2["청색증 의심(입술/손발)"] = st.checkbox("청색증 의심(입술/손발)", key="gi_obs2")
        obs2["말수 감소·축 늘어짐/보챔"] = st.checkbox("말수 감소·축 늘어짐/보챔", key="gi_obs3")
        obs2["탈수 의심(마른 입/눈물↓/소변↓)"] = st.checkbox("탈수 의심(마른 입술/눈물 적음/소변 감소)", key="gi_obs4")
        obs2["고열(≥40.0℃)"] = st.checkbox("고열(≥40.0℃)", key="gi_obs5")
        obs2["3개월 미만 발열(≥38.0℃)"] = st.checkbox("3개월 미만 발열(≥38.0℃)", key="gi_obs6")
        obs2["경련(열성경련 포함)"] = st.checkbox("경련(열성경련 포함)", key="gi_obs7")
        st.session_state["ped_obs_gi"] = {k:v for k,v in obs2.items() if v}

    with st.expander("🧮 해열제 용량 계산기", expanded=False):
        wt2 = st.text_input("체중(kg)", key="antipy_wt_gi", placeholder="예: 10.5")
        med2 = st.selectbox("해열제", ["아세트아미노펜(acetaminophen)", "이부프로펜(ibuprofen)"], key="antipy_med_gi")
        if med2.startswith("아세트"):
            conc2 = st.selectbox("시럽 농도", ["160 mg/5 mL", "120 mg/5 mL"], key="antipy_conc_acet_gi")
            default_mgkg2 = 15
        else:
            conc2 = st.selectbox("시럽 농도", ["100 mg/5 mL"], key="antipy_conc_ibu_gi")
            default_mgkg2 = 10
        st.caption(f"계산 기준: {default_mgkg2} mg/kg (1회분)")
        try:
            w2 = float(wt2)
            mg_num2 = int(conc2.split("mg/")[0])
            ml_denom2 = int(conc2.split("mg/")[1].split()[0].replace("mL",""))
            mg2 = int(round(w2 * default_mgkg2))
            ml2 = round(mg2 * ml_denom2 / mg_num2, 1)
            st.success(f"권장 1회 용량: **{ml2} mL** ({conc2}) — 체중 {w2:g} kg 기준")
            st.caption("참고: Acetaminophen 10–15 mg/kg, Ibuprofen 5–10 mg/kg. 보호자 편의를 위해 단일 기준으로 계산합니다.")
        except Exception:
            st.info("체중을 입력하면 1회 권장 mL가 계산됩니다.")

# ================= 저장/불러오기/보고서 =================
st.markdown("---")
c = st.columns([1,1,2,2])
with c[0]:
    if nickname_key:
        if st.button("💾 현재 입력 저장"):
            st.session_state.records.setdefault(nickname_key, []).append({"time": datetime.now().isoformat(), "mode": mode, "vals": vals, "extra": extra, "meta": meta})
            st.success("저장됨")
with c[1]:
    if nickname_key and st.session_state.records.get(nickname_key):
        if st.button("↩️ 이전 기록 불러오기"):
            last = st.session_state.records[nickname_key][-1]
            st.info(f"불러온 기록 시각: {last.get('time','')}")

with c[2]:
    a4_opt = st.checkbox("🖨️ A4 프린트 최적화(섹션 구분선)", value=True)
with c[3]:
    show_report = st.checkbox("📄 보고서 미리보기", value=True)

def build_report(mode, meta, vals, extra):
    def _safe(x, default="미입력"):
        return x if x else default

    lines = []
    lines.append(f"# 피수치 리포트 — {_safe(meta.get('nickname',''))}")
    lines.append(f"- 세션: {_safe(meta.get('nickname',''))}#{_safe(meta.get('pin',''))} · 시각: {meta.get('time','')}")
    lines.append("")
    lines.append(f"## 모드: {mode}")
    if vals:
        lines.append("### 기본")
        for k, v in vals.items():
            if entered(v):
                lines.append(f"- {k}: **{v}**")
    if extra:
        lines.append("### 확장/추가")
        for k, v in extra.items():
            if isinstance(v, dict):
                pairs = [f"{kk}={vv}" for kk, vv in v.items() if entered(vv)]
                if pairs:
                    lines.append(f"- {k}: " + ", ".join(pairs))
            elif isinstance(v, list):
                lines.append(f"- {k}: " + ", ".join([str(x) for x in v]))
            else:
                if entered(v):
                    lines.append(f"- {k}: **{v}**")
    lines.append("")
    lines.append("> ⚠️ 본 수치는 참고용이며 개발자와 무관하며, 수치 기반 임의조정은 금지입니다. 반드시 의료진과 상의 후 결정하시기 바랍니다.")
    return "\n".join(lines)

report_md = build_report(mode, meta, {k:v for k,v in vals.items() if entered(v)}, extra)
if a4_opt:
    report_md = report_md.replace("## ", "\n\n---\n\n## ")

if show_report:
    st.markdown(report_md)

st.download_button("⬇️ 보고서 .md 다운로드", report_md, file_name="report.md")
