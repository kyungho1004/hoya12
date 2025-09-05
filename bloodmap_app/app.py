
import streamlit as st
from .config import VERSION

APP_TITLE = "피수치 해석기"
GLOBAL_DISCLAIMER = (
    "이 해석기는 해석을 도와주는 도구이며, 모든 수치는 개발자와 무관합니다.\n"
    "피수치 및 결과 해석 관련 문의는 반드시 주치의와 상담하시기 바랍니다."
)

def _to_float(x):
    try:
        return float(str(x).replace(",","").strip())
    except:
        return None

def _metric_row(labels_keys):
    cols = st.columns(len(labels_keys))
    outs = {}
    for (label, key), c in zip(labels_keys, cols):
        outs[key] = c.text_input(label, value=st.session_state.get(key,""), key=key)
    return outs

def _interpret_adult():
    msgs = []
    WBC = _to_float(st.session_state.get("WBC_20")); Hb = _to_float(st.session_state.get("Hb_20"))
    PLT = _to_float(st.session_state.get("PLT_20")); ANC = _to_float(st.session_state.get("ANC_20"))
    CRP = _to_float(st.session_state.get("CRP_20")); Na = _to_float(st.session_state.get("Na_20"))
    K = _to_float(st.session_state.get("K_20")); Cr = _to_float(st.session_state.get("Cr_20"))
    Tb = _to_float(st.session_state.get("Tb_20")); BNP = _to_float(st.session_state.get("BNP_20"))
    if ANC is not None:
        if ANC < 500: msgs.append("⚠️ 중증 호중구감소(ANC<500): 발열 시 패혈증 위험 — 즉시 내원 권고")
        elif ANC < 1000: msgs.append("주의: 중등도 호중구감소(ANC<1000)")
        elif ANC < 1500: msgs.append("경도 호중구감소(ANC<1500)")
    if Hb is not None and Hb < 10: msgs.append("빈혈(Hb<10) — 증상/산소포화도 고려하여 평가")
    if PLT is not None:
        if PLT < 50: msgs.append("⚠️ 혈소판 감소(PLT<50k): 출혈주의, 처치 전 확인")
        elif PLT < 100: msgs.append("혈소판 경감(PLT<100k)")
    if CRP is not None and CRP >= 5: msgs.append("염증수치 상승(CRP≥5)")
    if Na is not None and Na < 130: msgs.append("저나트륨(Na<130)")
    if K is not None:
        if K >= 5.5: msgs.append("⚠️ 고칼륨(K≥5.5) — 심전도/약물검토 필요")
        elif K < 3.0: msgs.append("저칼륨(K<3.0)")
    if Cr is not None and Cr >= 2.0: msgs.append("신장기능 저하(Cr≥2.0) 의심")
    if Tb is not None and Tb >= 2.0: msgs.append("담즙정체/간기능 이상(Tb≥2.0) 의심")
    if BNP is not None and BNP > 100: msgs.append("BNP 상승(>100) — 심부전/과수분 상태 고려")
    # ACR/UPCR
    ACR_v = st.session_state.get("ACR_value"); UPCR_v = st.session_state.get("UPCR_value")
    if ACR_v:
        try:
            v = float(ACR_v)
            if v >= 300: msgs.append("단백뇨(ACR≥300 mg/g)")
            elif v >= 30: msgs.append("미세알부민뇨(ACR 30–299 mg/g)")
        except: pass
    if UPCR_v:
        try:
            v = float(UPCR_v)
            if v >= 300: msgs.append("UPCR≥300 mg/g (중등도 이상 단백뇨)")
            elif v >= 150: msgs.append("UPCR≥150 mg/g (경증 이상 단백뇨)")
        except: pass

    if not msgs:
        msgs = ["특이 위험 신호 없음(입력값 기준). 증상/진찰/영상·검사와 함께 종합 판단 필요."]
    return msgs

def _interpret_peds():
    msgs = []
    Tmax = _to_float(st.session_state.get("sx_fever_max"))
    days = _to_float(st.session_state.get("sx_fever_days"))
    if Tmax and Tmax >= 39.5: msgs.append("🚑 고열(≥39.5℃): 병원 방문 권고")
    if days and days >= 5: msgs.append("⚠️ 발열 5일 이상 — 진료 권고")
    pain = st.session_state.get("sx_pain")
    if pain and pain != "없음": msgs.append(f"통증: {pain}")
    rhin = st.session_state.get("sx_rhin")
    if rhin and rhin != "없음": msgs.append(f"콧물: {rhin}")
    cough = st.session_state.get("sx_cough")
    if cough and cough != "없음": msgs.append(f"기침: {cough}")
    sore = st.session_state.get("sx_sore")
    if sore and sore != "없음": msgs.append(f"인후통: {sore}")
    if not msgs: msgs = ["특이 위험 신호 없음(입력값 기준). 증상/진찰과 함께 판단 필요."]
    return msgs

def main():
    st.markdown(f"<style>{open('/mnt/data/hoya12/style.css','r',encoding='utf-8').read()}</style>", unsafe_allow_html=True)
    st.title(APP_TITLE)
    st.caption(f"빌드: {VERSION}")
    st.info(GLOBAL_DISCLAIMER)

    # 최상단 모드 토글
    MODE = st.radio(" ", ["암종류","소아질환"], index=0, horizontal=True, key="mode_main")

    # --- 공통: 진단/별명/핀
    c1, c2, c3 = st.columns([2,1,1])
    nickname = c1.text_input("별명", value=st.session_state.get("nickname",""), key="nickname")
    pin = c2.text_input("PIN(4자리)", value=st.session_state.get("pin",""), key="pin", max_chars=4)
    if pin and not str(pin).isdigit() or len(str(pin)) not in (0,4):
        st.warning("PIN은 숫자 4자리 형식이어야 합니다.")

    if MODE == "암종류":
        st.subheader("암 선택")
        grp = st.radio("암 그룹", ["혈액암","고형암","육종","희귀암"], horizontal=True, key="grp")
        if grp == "혈액암":
            diag = st.selectbox("혈액암(진단명)", ["AML","APL","ALL","CML","CLL"], key="diag")
        elif grp == "고형암":
            diag = st.selectbox("고형암(진단명)", ["폐암","유방암","위암","대장암","간암","췌장암","담도암","자궁내막암","식도암","방광암","신장암","갑상선암","난소암","전립선암","뇌종양","구강/후두암"], key="diag")
        elif grp == "육종":
            diag = st.selectbox("육종(진단명)", ["골육종(MAP)","유잉육종(VAC/IE)","횡문근육종","신경모세포종","윌름스종양","간모세포종","GCT(BEP)","수모세포종"], key="diag")
        else:
            diag = st.selectbox("희귀암(진단명)", ["담낭암","부신암","망막모세포종","흉선암","신경내분비종양(NET)","GIST"], key="diag")

        # 항암제(진단별) 멀티선택
        st.markdown("### 🧬 항암제(진단별 선택)")
        default_map = {
            "APL": ["ATRA(트레티노인)", "아르세닉 트리옥사이드(ATO)", "MTX(메토트렉세이트)", "6-MP(머캅토퓨린)"],
            "AML": ["Cytarabine", "Daunorubicin", "Idarubicin"],
            "ALL": ["Vincristine", "Prednisolone", "Asparaginase", "MTX", "6-MP"],
            "골육종(MAP)": ["MTX", "Doxorubicin", "Cisplatin"],
            "유잉육종(VAC/IE)": ["Vincristine","Actinomycin D","Cyclophosphamide","Ifosfamide","Etoposide"],
            "폐암": ["Cisplatin","Carboplatin","Paclitaxel","Pemetrexed","Atezolizumab"],
        }
        chemo_opts = default_map.get(diag, ["Cisplatin","Carboplatin","Paclitaxel","Gemcitabine","5-FU","Oxaliplatin"])
        st.session_state["chemo_by_diagnosis"] = st.multiselect("항암제 선택(진단별)", options=chemo_opts, default=chemo_opts)

        st.markdown("### 🧪 기본 피수치(20종)")
        _metric_row([("WBC(×10³/µL)","WBC_20"),("Hb(g/dL)","Hb_20"),("PLT(×10³/µL)","PLT_20"),("ANC(/µL)","ANC_20"),("CRP(mg/dL)","CRP_20")])
        _metric_row([("Ca(mg/dL)","Ca_20"),("K(mmol/L)","K_20"),("TP(g/dL)","TP_20"),("LD(U/L)","LD_20"),("P(mg/dL)","P_20")])
        _metric_row([("Alb(g/dL)","Alb_20"),("AST(U/L)","AST_20"),("Cr(mg/dL)","Cr_20"),("Na(mmol/L)","Na_20"),("Glu(mg/dL)","Glu_20")])
        _metric_row([("ALT(U/L)","ALT_20"),("UA(mg/dL)","UA_20"),("Tb(mg/dL)","Tb_20"),("Ferritin(ng/mL)","Ferritin_20"),("D-dimer(µg/mL)","Ddimer_20")])

        use_special = st.checkbox("🔬 특수/소변 입력 (선택)", value=False, key="use_special_urine")
        if use_special:
            with st.expander("🔬 특수/소변 검사 (선택)", expanded=True):
                st.caption("요 알부민·요 단백·요 크레아티닌으로 ACR/UPCR을 자동 계산합니다. 필요 항목만 입력하세요.")
                unit = st.radio("요 알부민 단위", ["mg/L","mg/dL"], index=0, horizontal=True, key="u_alb_unit")
                c1,c2,c3,c4 = st.columns(4)
                u_alb = c1.text_input("요 알부민", key="u_alb")
                u_pro = c2.text_input("요 단백 (mg/dL)", key="u_pro")
                u_cr  = c3.text_input("요 크레아티닌 (mg/dL)", key="u_cr")
                s_cr  = c4.text_input("혈청 크레아티닌 (mg/dL)", key="s_cr")

                alb = _to_float(u_alb)
                if alb is not None and unit == "mg/dL":
                    alb *= 10.0
                pro = _to_float(u_pro); ucr = _to_float(u_cr)
                acr  = (alb/(ucr*10.0)) if (alb is not None and ucr not in (None,0)) else None
                upcr = (pro/ucr) if (pro is not None and ucr not in (None,0)) else None

                st.session_state["ACR_value"]  = f"{acr:.1f}" if acr is not None else ""
                st.session_state["UPCR_value"] = f"{upcr:.1f}" if upcr is not None else ""

                m1,m2 = st.columns(2)
                m1.metric("ACR (mg/g)", st.session_state["ACR_value"] or "–")
                m2.metric("UPCR (mg/g)", st.session_state["UPCR_value"] or "–")

                st.divider(); st.subheader("보체 / 소변 정성(선택)")
                cc1,cc2 = st.columns(2)
                st.text_input("C3 (mg/dL)", key="C3_toggle")
                st.text_input("C4 (mg/dL)", key="C4_toggle")
                d1,d2,d3,d4 = st.columns(4)
                st.selectbox("단백뇨(dip)", ["없음","미량","1+","2+","3+","4+"], key="UPRO_dip")
                st.selectbox("WBC esterase", ["없음","양성"], key="ULEU_dip")
                st.selectbox("아질산", ["없음","양성"], key="UNIT_dip")
                st.selectbox("pH", ["<5.0","5.0","6.0","7.0","8.0",">=9.0"], index=1, key="UpH_dip")

        with st.expander("🧠 해석", expanded=False):
            st.warning("철분제+비타민은 항암 환자에게 치명적일 수 있으므로 복용 전 반드시 주치의와 상담하세요.")
            if st.button("해석 보기", key="btn_interpret_adult"):
                msgs = _interpret_adult()
                st.markdown("\n".join([f"- {m}" for m in msgs]))
                st.caption("※ 자동요약은 참고용입니다. 반드시 주치의와 상담하세요.")

        with st.expander("🥗 식이 가이드", expanded=False):
            st.markdown("- 메토트렉세이트 복용 시 알코올/과다 엽산 보충제 주의\n- 시스플라틴 기반 요법 시 수분 섭취 충분히\n- 자몽/세인트존스워트 등 약물 상호작용 음식 주의")

    else:  # 소아질환
        st.subheader("소아 가이드")
        suspect = st.selectbox("의심 질환(참고)", ["아데노바이러스","RSV","인플루엔자","코로나19","파라인플루엔자","리노바이러스","마이코플라스마","GAS 인두염","중이염(AOM)","기관지염/모세기관지염"])
        st.markdown("### 증상 입력")
        c1,c2,c3 = st.columns(3)
        st.radio("통증 정도", ["없음","조금","보통","많이"], horizontal=True, key="sx_pain")
        st.selectbox("콧물", ["없음","맑음","흰색","누런","초록","피섞임"], key="sx_rhin")
        st.selectbox("기침", ["없음","마른기침","가래기침","발작성"], key="sx_cough")
        d1,d2,d3 = st.columns(3)
        st.selectbox("인후통", ["없음","약간","심함"], key="sx_sore")
        st.text_input("발열 기간(일)", key="sx_fever_days")
        st.text_input("최고체온(℃)", key="sx_fever_max")

        show_ped = st.checkbox("소아 피수치 입력", value=False, key="ped_labs_switch")
        if show_ped:
            with st.expander("🧒 소아 피수치(간편)", expanded=True):
                _metric_row([("WBC(×10³/µL)","WBC_ped"),("Hb(g/dL)","Hb_ped"),("PLT(×10³/µL)","PLT_ped"),("ANC(/µL)","ANC_ped"),("CRP(mg/dL)","CRP_ped")])

        with st.expander("🧠 해석", expanded=False):
            if st.button("해석 보기(소아)", key="btn_interpret_peds"):
                msgs = _interpret_peds()
                st.markdown("\n".join([f"- {m}" for m in msgs]))
                st.caption("※ 자동요약은 참고용입니다. 반드시 주치의와 상담하세요.")

    # 결과/내보내기
    st.markdown("---")
    st.markdown("### 결과/내보내기")
    # 간단 텍스트 구성
    lines = []
    lines.append(f"별명: {st.session_state.get('nickname','')}  PIN: {st.session_state.get('pin','')}  모드: {MODE}")
    if st.session_state.get("ACR_value"): lines.append(f"ACR: {st.session_state.get('ACR_value')} mg/g")
    if st.session_state.get("UPCR_value"): lines.append(f"UPCR: {st.session_state.get('UPCR_value')} mg/g")
    for k in ["C3_toggle","C4_toggle","UPRO_dip","ULEU_dip","UNIT_dip","UpH_dip"]:
        v = st.session_state.get(k); ifv = f"{k}={v}" if v else None
        if ifv: lines.append(ifv)
    lines.append("\n[고지문]\n" + GLOBAL_DISCLAIMER)
    export_text = "\n".join(lines)

    cta1, cta2, cta3 = st.columns(3)
    if cta1.download_button("TXT 내보내기", export_text.encode("utf-8"), file_name="result.txt", mime="text/plain"):
        st.success("TXT 파일을 저장했습니다.")
    md_bytes = ("# 결과 요약\n\n" + export_text).encode("utf-8")
    if cta2.download_button("MD 내보내기", md_bytes, file_name="result.md", mime="text/markdown"):
        st.success("MD 파일을 저장했습니다.")
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        import io
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        textobject = c.beginText(15*mm, 280*mm)
        for line in export_text.splitlines():
            textobject.textLine(line)
        c.drawText(textobject); c.showPage(); c.save()
        pdf_data = buf.getvalue()
        if cta3.download_button("PDF 내보내기", pdf_data, file_name="result.pdf", mime="application/pdf"):
            st.success("PDF 파일을 저장했습니다.")
    except Exception as e:
        st.caption("PDF 생성 라이브러리가 없으면 TXT/MD만 사용하세요.")
