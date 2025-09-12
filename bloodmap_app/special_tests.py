# -*- coding: utf-8 -*-
"""
특수검사 UI/해석 모듈 (카테고리 토글 + 즐겨찾기)
- 소변검사: 요침사 RBC/WBC 추가
- 혈액(적혈구 지수/망상): MCV, MCH, MCHC, RDW, Retic(%) 추가
"""
from __future__ import annotations
from typing import List, Optional
import streamlit as st

def _num(x):
    try:
        if x is None: return None
        if isinstance(x, (int,float)): return float(x)
        s = str(x).replace(",", "").strip()
        return float(s) if s else None
    except Exception:
        return None

def _flag(kind: Optional[str]) -> str:
    return {"ok":"🟢 정상","warn":"🟡 주의","risk":"🚨 위험"}.get(kind or "", "")

def _emit(lines: List[str], kind: Optional[str], msg: str):
    tag = _flag(kind)
    lines.append(f"{tag} {msg}" if tag else msg)

def _tog_key(name: str) -> str: return f"tog_{name}"
def _fav_key(name: str) -> str: return f"fav_{name}"

SECTIONS = [
    ("소변검사", "urine"),
    ("혈액(적혈구 지수/망상)", "rbcindex"),   # ✅ 신규 섹션
    ("보체 (C3/C4/CH50)", "complement"),
    ("지질검사 (TC/TG/HDL/LDL)", "lipid"),
    ("심부전 지표 (BNP / NT-proBNP)", "heartfail"),
    ("당 검사 (식전/1h/2h)", "glucose"),
    ("심장/근육 (CK / CK-MB / Troponin)", "cardio"),
    ("간담도 (GGT / ALP)", "hepatobiliary"),
    ("췌장 (Amylase / Lipase)", "pancreas"),
    ("응고 (PT-INR / aPTT / Fibrinogen / D-dimer)", "coag"),
    ("염증 (ESR / Ferritin / PCT)", "inflammation"),
    ("젖산 (Lactate)", "lactate")
]

def _fav_list():
    st.session_state.setdefault("fav_tests", [])
    return st.session_state["fav_tests"]

def special_tests_ui() -> List[str]:
    lines: List[str] = []
    with st.expander("🧪 특수검사 (선택 입력)", expanded=False):
        st.caption("정성검사는 +/++/+++ , 정량검사는 숫자만 입력. ★로 즐겨찾기 고정.")
        favs = _fav_list()
        if favs:
            st.markdown("**⭐ 즐겨찾기**")
            chips = st.columns(len(favs))
            for i, sec_id in enumerate(favs):
                with chips[i]:
                    if st.button(f"★ {sec_id}", key=_fav_key(f"chip_{sec_id}")):
                        st.session_state[_tog_key(sec_id)] = True

        for title, sec_id in SECTIONS:
            c1, c2 = st.columns([0.8, 0.2])
            with c1:
                on = st.toggle(title, key=_tog_key(sec_id), value=bool(st.session_state.get(_tog_key(sec_id), False)))
            with c2:
                isfav = sec_id in favs
                label = "★" if isfav else "☆"
                if st.button(label, key=_fav_key(f"btn_{sec_id}")):
                    if isfav: favs.remove(sec_id)
                    else:
                        if sec_id not in favs: favs.append(sec_id)
            if not on: 
                continue

            # ---------------- 소변검사 ----------------
            if sec_id == "urine":
                cA,cB,cC,cD = st.columns(4)
                with cA: alb = st.selectbox("알부민뇨", ["없음","+","++","+++"], index=0)
                with cB: hem = st.selectbox("혈뇨(잠혈)", ["없음","+","++","+++"], index=0)
                with cC: glu = st.selectbox("요당", ["없음","+","++","+++"], index=0)
                with cD: nit = st.selectbox("아질산염", ["없음","+","++","+++"], index=0)

                # ✅ 요침사(현미경) 추가
                u1,u2 = st.columns(2)
                with u1: rbc_hpf = _num(st.text_input("요침사 RBC (/HPF)", placeholder="예: 0~2 정상"))
                with u2: wbc_hpf = _num(st.text_input("요침사 WBC (/HPF)", placeholder="예: 0~5 정상"))

                # 정성 해석
                if alb!="없음": _emit(lines, "warn" if alb in ["+","++"] else "risk", f"알부민뇨 {alb} → 신장 질환/단백뇨 평가 필요")
                if hem!="없음": _emit(lines, "warn" if hem in ["+","++"] else "risk", f"혈뇨(잠혈) {hem} → 요로계 출혈/결석/염증 가능성")
                if glu!="없음": _emit(lines, "warn", f"요당 {glu} → 당뇨/신세뇨관 이상 가능, 혈당 확인")
                if nit!="없음": _emit(lines, "warn", f"아질산염 {nit} → 세균성 요로감염 가능")

                # 현미경 해석
                if rbc_hpf is not None:
                    if rbc_hpf >= 10: _emit(lines, "risk", f"요침사 RBC {int(rbc_hpf)}/HPF → 현저 혈뇨, 요석/사구체/종양 감별")
                    elif rbc_hpf >= 3: _emit(lines, "warn", f"요침사 RBC {int(rbc_hpf)}/HPF → 혈뇨, 재검/원인 평가 권장")
                if wbc_hpf is not None:
                    if wbc_hpf >= 10: _emit(lines, "risk", f"요침사 WBC {int(wbc_hpf)}/HPF → 뚜렷한 염증/UTI 의심")
                    elif wbc_hpf >= 5: _emit(lines, "warn", f"요침사 WBC {int(wbc_hpf)}/HPF → 염증 소견, 증상 동반 시 UTI 고려")

            # ---------------- 적혈구 지수/망상 ----------------
            elif sec_id == "rbcindex":
                r1,r2,r3,r4,r5 = st.columns(5)
                with r1: mcv  = _num(st.text_input("MCV (fL)", placeholder="예: 90"))
                with r2: mch  = _num(st.text_input("MCH (pg)", placeholder="예: 30"))
                with r3: mchc = _num(st.text_input("MCHC (g/dL)", placeholder="예: 33"))
                with r4: rdw  = _num(st.text_input("RDW (%)", placeholder="예: 12.5"))
                with r5: retp = _num(st.text_input("망상적혈구 Retic (%)", placeholder="예: 1.0"))

                # 해석
                if mcv is not None:
                    if mcv < 80: _emit(lines, "warn", f"MCV {mcv} fL → 소구성 빈혈(철결핍/만성질환/지중해빈혈 등) 고려")
                    elif mcv > 100: _emit(lines, "warn", f"MCV {mcv} fL → 대구성 빈혈(B12/엽산 결핍, 간질환, 약물) 고려")
                if mchc is not None:
                    if mchc < 32: _emit(lines, "warn", f"MCHC {mchc} g/dL ↓ → 저색소 경향(철결핍 등)")
                    elif mchc > 36: _emit(lines, "warn", f"MCHC {mchc} g/dL ↑ → 구형적혈구증 등 드묾")
                if rdw is not None and rdw >= 15:
                    _emit(lines, "warn", f"RDW {rdw}% ↑ → 적혈구 크기 분산 증가(철결핍/혼합성 빈혈 가능)")
                if retp is not None:
                    if retp > 2: _emit(lines, "warn", f"Retic {retp}% ↑ → 용혈/출혈 후 회복 국면 가능(망상↑)")
                    elif retp < 0.5: _emit(lines, "warn", f"Retic {retp}% ↓ → 저생산성 빈혈(골수억제/영양결핍 등) 고려")

            elif sec_id == "complement":
                d1,d2,d3 = st.columns(3)
                with d1: c3 = _num(st.text_input("C3 (mg/dL)", placeholder="예: 90"))
                with d2: c4 = _num(st.text_input("C4 (mg/dL)", placeholder="예: 20"))
                with d3: ch50 = _num(st.text_input("CH50 (U/mL)", placeholder="예: 50"))
                if c3 is not None and c3 < 85: _emit(lines, "warn", f"C3 낮음({c3}) → 면역복합체 질환/활성화 가능성")
                if c4 is not None and c4 < 15: _emit(lines, "warn", f"C4 낮음({c4}) → 보체소모/면역 이상 가능성")
                if ch50 is not None:
                    if ch50 < 30: _emit(lines, "risk", f"CH50 {ch50} (낮음) → 보체 결핍/소모 의심")
                    elif ch50 < 40: _emit(lines, "warn", f"CH50 {ch50} (경도 저하) → 추적 필요")

            elif sec_id == "lipid":
                l1,l2,l3,l4 = st.columns(4)
                with l1: tc  = _num(st.text_input("총콜레스테롤 TC (mg/dL)", placeholder="예: 180"))
                with l2: tg  = _num(st.text_input("TG (mg/dL)", placeholder="예: 120"))
                with l3: hdl = _num(st.text_input("HDL (mg/dL)", placeholder="예: 55"))
                with l4: ldl = _num(st.text_input("LDL (mg/dL)", placeholder="예: 110"))
                if tc is not None and tc >= 240: _emit(lines, "risk", f"총콜레스테롤 {tc} ≥ 240 → 고지혈증 가능")
                elif tc is not None and tc >= 200: _emit(lines, "warn", f"총콜레스테롤 {tc} 200~239 → 경계역")
                if tg is not None and tg >= 500: _emit(lines, "risk", f"중성지방 {tg} ≥ 500 → 췌장염 위험")
                elif tg is not None and tg >= 200: _emit(lines, "warn", f"중성지방 {tg} 200~499 → 고중성지방혈증")
                if hdl is not None and hdl < 40: _emit(lines, "warn", f"HDL {hdl} < 40 → 낮음")
                if ldl is not None and ldl >= 190: _emit(lines, "risk", f"LDL {ldl} ≥ 190 → 매우 높음")
                elif ldl is not None and ldl >= 160: _emit(lines, "warn", f"LDL {ldl} 160~189 → 높음")
                elif ldl is not None and ldl >= 130: _emit(lines, "warn", f"LDL {ldl} 130~159 → 경계역")

            elif sec_id == "heartfail":
                h5,h6 = st.columns(2)
                with h5: bnp  = _num(st.text_input("BNP (pg/mL)", placeholder="예: 60"))
                with h6: ntp  = _num(st.text_input("NT-proBNP (pg/mL)", placeholder="예: 125"))
                if bnp is not None and bnp >= 100: _emit(lines, "warn", f"BNP {bnp} ≥ 100 → 심부전 의심(연령/신장기능 고려)")
                if ntp is not None and ntp >= 900: _emit(lines, "warn", f"NT-proBNP {ntp} 상승 → 연령/신장 기능 고려")

            elif sec_id == "glucose":
                g1,g2,g3 = st.columns(3)
                with g1: fpg = _num(st.text_input("식전혈당 FPG (mg/dL)", placeholder="예: 95"))
                with g2: ppg1 = _num(st.text_input("식후 1시간 (mg/dL)", placeholder="예: 150"))
                with g3: ppg2 = _num(st.text_input("식후 2시간 (mg/dL)", placeholder="예: 120"))
                if fpg is not None:
                    if fpg >= 126: _emit(lines, "risk", f"FPG {fpg} ≥ 126 → 당뇨병 가능성")
                    elif fpg >= 100: _emit(lines, "warn", f"FPG {fpg} 100~125 → 공복혈당장애")
                if ppg1 is not None and ppg1 >= 200: _emit(lines, "warn", f"식후1h {ppg1} ≥ 200 → 고혈당")
                if ppg2 is not None:
                    if ppg2 >= 200: _emit(lines, "risk", f"식후2h {ppg2} ≥ 200 → 당뇨병 가능성")
                    elif ppg2 >= 140: _emit(lines, "warn", f"식후2h {ppg2} 140~199 → 내당능장애")

            elif sec_id == "cardio":
                h1,h2,h3,h4 = st.columns(4)
                with h1: ck   = _num(st.text_input("CK (U/L)", placeholder="예: 160"))
                with h2: ckmb = _num(st.text_input("CK-MB (ng/mL)", placeholder="예: 2.5"))
                with h3: troI = _num(st.text_input("Troponin I (ng/mL)", placeholder="예: 0.01"))
                with h4: troT = _num(st.text_input("Troponin T (ng/mL)", placeholder="예: 0.005"))
                ulnI = _num(st.text_input("Troponin I ULN(상한)", placeholder="예: 0.04"))
                ulnT = _num(st.text_input("Troponin T ULN(상한)", placeholder="예: 0.014"))
                if ck is not None:
                    if ck >= 5000: _emit(lines, "risk", f"CK {ck} → 횡문근융해 의심(즉시 상담)")
                    elif ck >= 1000: _emit(lines, "warn", f"CK {ck} → 근손상/운동/약물 영향 가능")
                if ckmb is not None and ckmb >= 5: _emit(lines, "warn", f"CK-MB {ckmb} ≥ 5 → 심근 손상 지표 상승 가능")
                if troI is not None and troI >= (ulnI if ulnI is not None else 0.04): _emit(lines, "risk", f"Troponin I {troI} ≥ ULN → 심근 손상 의심")
                if troT is not None and troT >= (ulnT if ulnT is not None else 0.014): _emit(lines, "risk", f"Troponin T {troT} ≥ ULN → 심근 손상 의심")

            elif sec_id == "hepatobiliary":
                a1,a2 = st.columns(2)
                with a1: ggt = _num(st.text_input("GGT (U/L)", placeholder="예: 35"))
                with a2: alp = _num(st.text_input("ALP (U/L)", placeholder="예: 110"))
                if ggt is not None and ggt >= 100: _emit(lines, "warn", f"GGT 상승({ggt}) → 담도/약물 영향 가능")
                if alp is not None and alp >= 150: _emit(lines, "warn", f"ALP 상승({alp}) → 담도/골질환 감별")

            elif sec_id == "pancreas":
                p1,p2 = st.columns(2)
                with p1: amy = _num(st.text_input("Amylase (U/L)", placeholder="예: 60"))
                with p2: lip = _num(st.text_input("Lipase (U/L)", placeholder="예: 40"))
                if amy is not None and amy >= 300: _emit(lines, "warn", f"Amylase 상승({amy}) → 췌장/타장기 영향 가능")
                if lip is not None and lip >= 180:  _emit(lines, "risk", f"Lipase 현저 상승({lip}) → 급성 췌장염 의심")

            elif sec_id == "coag":
                c1,c2,c3,c4 = st.columns(4)
                with c1: inr = _num(st.text_input("PT-INR", placeholder="예: 1.0"))
                with c2: aptt = _num(st.text_input("aPTT (sec)", placeholder="예: 30"))
                with c3: fib = _num(st.text_input("Fibrinogen (mg/dL)", placeholder="예: 300"))
                with c4: dd = _num(st.text_input("D-dimer (µg/mL)", placeholder="예: 0.3"))
                if inr is not None and inr >= 1.5: _emit(lines, "warn", f"INR {inr} ≥ 1.5 → 응고 저하/간기능 저하 가능")
                if aptt is not None and aptt >= 40: _emit(lines, "warn", f"aPTT {aptt} ≥ 40s → 내인성 경로 지연")
                if fib is not None and fib < 150: _emit(lines, "risk", f"Fibrinogen {fib} < 150 → 소모/간기능 저하")
                if dd is not None and dd >= 0.5: _emit(lines, "warn", f"D-dimer {dd} ≥ 0.5 → 혈전/염증 반응 가능(임상과 함께)")

            elif sec_id == "inflammation":
                i1,i2,i3 = st.columns(3)
                with i1: esr = _num(st.text_input("ESR (mm/h)", placeholder="예: 10"))
                with i2: ferr = _num(st.text_input("Ferritin (ng/mL)", placeholder="예: 100"))
                with i3: pct = _num(st.text_input("Procalcitonin (ng/mL)", placeholder="예: 0.05"))
                if esr is not None and esr >= 40: _emit(lines, "warn", f"ESR {esr} ≥ 40 → 염증/만성질환 가능")
                if ferr is not None and ferr >= 300: _emit(lines, "warn", f"Ferritin {ferr} ≥ 300 → 염증/철과부하 감별")
                if pct is not None:
                    if pct >= 2: _emit(lines, "risk", f"PCT {pct} ≥ 2 → 패혈증 가능성 높음")
                    elif pct >= 0.5: _emit(lines, "warn", f"PCT {pct} 0.5~2 → 세균감염 의심")

            elif sec_id == "lactate":
                lc = _num(st.text_input("Lactate (mmol/L)", placeholder="예: 1.5"))
                if lc is not None and lc >= 2: _emit(lines, "warn", f"Lactate {lc} ≥ 2 → 조직저산소/패혈증 감시")
    return lines
