
# -*- coding: utf-8 -*-
"""
특수검사 UI/해석 모듈 (패치 방식, 기존 기능 삭제 없음)
- ✅ 소변검사/혈구지수/보체/지질/심부전/당/심장·근육/간담도/췌장/응고/염증/젖산
- ✅ 모든 입력 라벨 영어+한글 병기
- ✅ UPCR/ACR 10000 초과 시 '단일 라인' 경고(극고값 + 단위/입력 오류 가능성)
- ✅ Streamlit DuplicateElementId 예방: 모든 위젯에 **고유 key** 부여 (sec_id + 필드명 규칙)
- ✅ 즐겨찾기(★) 유지 — 세션키: fav_tests
"""
from __future__ import annotations
from typing import List, Optional
import streamlit as st

def _num(x):
    try:
        if x is None: return None
        if isinstance(x, (int,float)): return float(x)
        s = str(x).replace(",", "").strip()
        s2 = "".join(ch for ch in s if (ch.isdigit() or ch=='.' or ch=='-'))
        return float(s2) if s2 else None
    except Exception:
        return None

def _flag(kind: Optional[str]) -> str:
    return {"ok":"🟢 정상", "warn":"🟡 주의", "risk":"🚨 위험"}.get(kind or "", "")

def _emit(lines: List[str], kind: Optional[str], msg: str):
    tag = _flag(kind)
    lines.append(f"{tag} {msg}" if tag else msg)

def _key(sec: str, field: str) -> str:
    """모든 위젯에 접두사 포함 key 부여 → 중복 방지"""
    uid = st.session_state.get("_uid", "")
    who = st.session_state.get("key", "guest#PIN")
    return f"sp_{who}_{uid}_{sec}__{field}"

def _tog_key(name: str) -> str: return _key(name, "toggle")
def _fav_btn_key(name: str) -> str: return _key(name, "fav_btn")
def _fav_chip_key(name: str) -> str: return _key(name, "fav_chip")

SECTIONS = [
    ("소변검사 (Urinalysis)", "urine"),
    ("혈구지수/망상 (RBC Indices / Reticulocyte)", "rbcidx"),
    ("보체 (Complement C3/C4/CH50)", "complement"),
    ("지질검사 (Lipid: TC/TG/HDL/LDL)", "lipid"),
    ("심부전 지표 (BNP / NT-proBNP)", "heartfail"),
    ("당 검사 (Glucose: FPG/PPG)", "glucose"),
    ("심장/근육 (CK / CK-MB / Troponin)", "cardio"),
    ("간담도 (GGT / ALP)", "hepatobiliary"),
    ("췌장 (Amylase / Lipase)", "pancreas"),
    ("응고 (PT-INR / aPTT / Fibrinogen / D-dimer)", "coag"),
    ("염증 (ESR / Ferritin / Procalcitonin)", "inflammation"),
    ("젖산 (Lactate)", "lactate"),
]

def _fav_list():
    st.session_state.setdefault("fav_tests", [])
    return st.session_state["fav_tests"]

def special_tests_ui() -> List[str]:
    lines: List[str] = []
    with st.expander("🧪 특수검사 (선택 입력)", expanded=True):
        st.caption("정성검사는 +/++/+++ , 정량검사는 숫자만 입력. ★로 즐겨찾기 고정.")
        favs = _fav_list()
        if favs:
            st.markdown("**⭐ 즐겨찾기**")
            chips = st.columns(len(favs))
            for i, sec_id in enumerate(favs):
                with chips[i]:
                    if st.button(f"★ {sec_id}", key=_fav_chip_key(f"chip_{sec_id}")):
                        st.session_state[_tog_key(sec_id)] = True

        for title, sec_id in SECTIONS:
            c1, c2 = st.columns([0.8, 0.2])
            with c1:
                on = st.toggle(title, key=_tog_key(sec_id), value=bool(st.session_state.get(_tog_key(sec_id), True)))
            with c2:
                isfav = sec_id in favs
                label = "★" if isfav else "☆"
                if st.button(label, key=_fav_btn_key(f"btn_{sec_id}")):
                    if isfav: favs.remove(sec_id)
                    else:
                        if sec_id not in favs: favs.append(sec_id)
            if not on:
                continue

            # --- 소변검사 / Urinalysis ---
            if sec_id == "urine":
                st.markdown("**요시험지/현미경 (Dipstick / Microscopy)**")
                row1 = st.columns(6)
                with row1[0]: alb = st.selectbox("Albumin (알부민뇨)", ["없음","+","++","+++"], index=0, key=_key(sec_id,"alb"))
                with row1[1]: hem = st.selectbox("Hematuria/Blood (혈뇨/잠혈)", ["없음","+","++","+++"], index=0, key=_key(sec_id,"hem"))
                with row1[2]: glu = st.selectbox("Glucose (요당)", ["없음","+","++","+++"], index=0, key=_key(sec_id,"glu"))
                with row1[3]: nit = st.selectbox("Nitrite (아질산염)", ["없음","+","++","+++"], index=0, key=_key(sec_id,"nit"))
                with row1[4]: leu = st.selectbox("Leukocyte esterase (백혈구 에스테라제)", ["없음","+","++","+++"], index=0, key=_key(sec_id,"leu"))
                with row1[5]: sg  = st.text_input("Specific gravity (요비중)", placeholder="예: 1.015", key=_key(sec_id,"sg"))

                row2 = st.columns(4)
                with row2[0]: rbc  = _num(st.text_input("RBC (/HPF, 적혈구/고배율 시야당)", placeholder="예: 0~2 정상, 3↑ 비정상", key=_key(sec_id,"rbc")))
                with row2[1]: wbc  = _num(st.text_input("WBC (/HPF, 백혈구/고배율 시야당)", placeholder="예: 0~4 정상, 5↑ 비정상", key=_key(sec_id,"wbc")))
                with row2[2]: upcr = _num(st.text_input("UPCR (Protein/Cr, 단백/크레아티닌 비율, mg/gCr)", placeholder="예: 120", key=_key(sec_id,"upcr")))
                with row2[3]: acr  = _num(st.text_input("ACR (Albumin/Cr, 알부민/크레아티닌 비율, mg/gCr)", placeholder="예: 25", key=_key(sec_id,"acr")))

                # 시험지/정성
                if alb!="없음": _emit(lines, "warn" if alb in ["+","++"] else "risk", f"알부민뇨 {alb} → 단백뇨 평가 필요")
                if hem!="없음": _emit(lines, "warn" if hem in ["+","++"] else "risk", f"혈뇨(잠혈) {hem} → 요로계 출혈/염증 가능")
                if glu!="없음": _emit(lines, "warn", f"요당 {glu} → 당뇨/세뇨관 이상 가능, 혈당 확인")
                if nit!="없음": _emit(lines, "warn", f"아질산염 {nit} → 세균성 요로감염 가능")
                if leu!="없음": _emit(lines, "warn" if leu in ["+","++"] else "risk", f"Leukocyte esterase {leu} → 백혈구뇨/요로감염 가능")

                # 현미경 수치
                if rbc is not None:
                    if rbc >= 25: _emit(lines, "risk", f"RBC {rbc}/HPF (다량) → 결석/종양/사구체 질환 등 평가 필요")
                    elif rbc >= 3: _emit(lines, "warn", f"RBC {rbc}/HPF (현미경적 혈뇨)")
                if wbc is not None:
                    if wbc >= 20: _emit(lines, "risk", f"WBC {wbc}/HPF (다량) → 급성 요로감염/신우신염 의심")
                    elif wbc >= 5: _emit(lines, "warn", f"WBC {wbc}/HPF (백혈구뇨)")

                # UPCR/ACR 해석 (고값>10000은 '단일 라인'으로 정리)
                if upcr is not None:
                    if upcr > 10000:
                        _emit(lines, "risk", f"UPCR {upcr} mg/gCr → 신증후군 범위(극고값). 단위/입력 오류 가능성도 있어 검사실/의료진에게 문의하세요.")
                    elif upcr >= 3500:
                        _emit(lines, "risk", f"UPCR {upcr} mg/gCr ≥ 3500 → 신증후군 범위 단백뇨 가능")
                    elif upcr >= 500:
                        _emit(lines, "warn", f"UPCR {upcr} mg/gCr 500~3499 → 유의한 단백뇨")
                    elif upcr >= 150:
                        _emit(lines, "warn", f"UPCR {upcr} mg/gCr 150~499 → 경미~중등 단백뇨")
                if acr is not None:
                    if acr > 10000:
                        _emit(lines, "risk", f"ACR {acr} mg/gCr → A3(중증) 범위(극고값). 단위/입력 오류 가능성도 있어 검사실/의료진에게 문의하세요.")
                    elif acr >= 300:
                        _emit(lines, "risk", f"ACR {acr} mg/gCr ≥ 300 → 알부민뇨 A3(중증)")
                    elif acr >= 30:
                        _emit(lines, "warn", f"ACR {acr} mg/gCr 30~299 → 알부민뇨 A2(중등)")
                    elif acr < 30:
                        _emit(lines, "ok",  f"ACR {acr} mg/gCr < 30 → A1 범주")

                # 패턴 종합
                uti_flag = ((wbc is not None and wbc >= 5) or leu!="없음" or nit!="없음")
                if uti_flag:
                    _emit(lines, "warn", "요로감염 의심 패턴 → 요배양/항생제 필요성 상담")

            # --- 혈구지수/망상 ---
            elif sec_id == "rbcidx":
                g1, g2, g3, g4 = st.columns(4)
                with g1: mcv = _num(st.text_input("MCV (Mean Corpuscular Volume, 평균적혈구용적, fL)",  placeholder="예: 75", key=_key(sec_id,"mcv")))
                with g2: mch = _num(st.text_input("MCH (Mean Corpuscular Hemoglobin, 평균적혈구혈색소량, pg)",  placeholder="예: 26", key=_key(sec_id,"mch")))
                with g3: rdw = _num(st.text_input("RDW (Red Cell Distribution Width, 적혈구분포폭, %)",   placeholder="예: 13.5", key=_key(sec_id,"rdw")))
                with g4: ret = _num(st.text_input("Reticulocyte (망상적혈구, %)", placeholder="예: 1.0", key=_key(sec_id,"ret")))
                # MCV
                if mcv is not None:
                    if mcv < 80: _emit(lines, "warn", f"MCV {mcv} < 80 → 소구성 빈혈(철결핍/지중해빈혈 등) 감별")
                    elif mcv > 100: _emit(lines, "warn", f"MCV {mcv} > 100 → 대구성 빈혈(B12/엽산/간질환/골수이상) 감별")
                    else: _emit(lines, "ok", f"MCV {mcv} 정상범위(80~100)")
                # RDW
                if rdw is not None:
                    if rdw > 14.5: _emit(lines, "warn", f"RDW {rdw}% ↑ → 적혈구 크기 불균일(철결핍/혼합결핍) 의심")
                # 조합 규칙
                if mcv is not None and rdw is not None:
                    if mcv < 80 and rdw > 14.5:
                        _emit(lines, "warn", "소구성 + RDW 증가 → **철결핍** 가능성 높음")
                    if mcv < 80 and (rdw <= 14.5):
                        _emit(lines, "warn", "소구성 + RDW 정상 → **지중해 빈혈 보인자** 감별")
                    if mcv > 100 and (ret is not None and ret < 0.5):
                        _emit(lines, "warn", "대구성 + 망상 저하 → **B12/엽산 결핍** 등 생성 저하형")
                # Retic
                if ret is not None:
                    if ret >= 2.0:
                        _emit(lines, "warn", f"Reticulocyte {ret}% ↑ → 용혈/실혈 회복기 등 생산 증가 소견")
                    elif ret < 0.5:
                        _emit(lines, "warn", f"Reticulocyte {ret}% ↓ → 조혈 저하(골수억제/영양결핍) 의심")

            elif sec_id == "complement":
                d1,d2,d3 = st.columns(3)
                with d1: c3   = _num(st.text_input("C3 (Complement 3, 보체 C3, mg/dL)", placeholder="예: 90", key=_key(sec_id,"c3")))
                with d2: c4   = _num(st.text_input("C4 (Complement 4, 보체 C4, mg/dL)", placeholder="예: 20", key=_key(sec_id,"c4")))
                with d3: ch50 = _num(st.text_input("CH50 (Total Complement Activity, 총보체활성, U/mL)", placeholder="예: 50", key=_key(sec_id,"ch50")))
                if c3 is not None and c3 < 85: _emit(lines, "warn", f"C3 낮음({c3}) → 면역복합체 질환/활성화 가능성")
                if c4 is not None and c4 < 15: _emit(lines, "warn", f"C4 낮음({c4}) → 보체소모/면역 이상 가능성")
                if ch50 is not None:
                    if ch50 < 30: _emit(lines, "risk", f"CH50 {ch50} (낮음) → 보체 결핍/소모 의심")
                    elif ch50 < 40: _emit(lines, "warn", f"CH50 {ch50} (경도 저하) → 추적 필요")

            elif sec_id == "lipid":
                c1,c2,c3,c4 = st.columns(4)
                with c1: tc  = _num(st.text_input("TC (총콜레스테롤, mg/dL)", placeholder="예: 180", key=_key(sec_id,"tc")))
                with c2: tg  = _num(st.text_input("TG (중성지방, mg/dL)", placeholder="예: 120", key=_key(sec_id,"tg")))
                with c3: hdl = _num(st.text_input("HDL (고밀도지단백, mg/dL)", placeholder="예: 50", key=_key(sec_id,"hdl")))
                with c4: ldl = _num(st.text_input("LDL (저밀도지단백, mg/dL)", placeholder="예: 110", key=_key(sec_id,"ldl")))
                if ldl is not None and ldl >= 190: _emit(lines, "risk", f"LDL {ldl} ≥ 190 → 매우 높음, 강력한 조치 고려")
                if tg is not None and tg >= 500: _emit(lines, "risk", f"TG {tg} ≥ 500 → 급성 췌장염 위험")
                if hdl is not None and hdl < 40: _emit(lines, "warn", f"HDL {hdl} 낮음 → 심혈관 위험 요인")

            elif sec_id == "heartfail":
                c1,c2 = st.columns(2)
                with c1: bnp   = _num(st.text_input("BNP (B-type Natriuretic Peptide, pg/mL)", placeholder="예: 60", key=_key(sec_id,"bnp")))
                with c2: ntpro = _num(st.text_input("NT-proBNP (pg/mL)", placeholder="예: 150", key=_key(sec_id,"ntpro")))
                if bnp is not None and bnp >= 400: _emit(lines, "warn", f"BNP {bnp} 높음 → 심부전 가능성")
                if ntpro is not None and ntpro >= 900: _emit(lines, "warn", f"NT-proBNP {ntpro} 높음 → 심부전 가능성")

            elif sec_id == "glucose":
                g1,g2 = st.columns(2)
                with g1: fpg = _num(st.text_input("FPG (공복혈당, mg/dL)", placeholder="예: 95", key=_key(sec_id,"fpg")))
                with g2: ppg = _num(st.text_input("PPG (식후2시간 혈당, mg/dL)", placeholder="예: 140", key=_key(sec_id,"ppg")))
                if fpg is not None and fpg >= 126: _emit(lines, "warn", f"FPG {fpg} ≥ 126 → 당뇨병 기준")
                if ppg is not None and ppg >= 200: _emit(lines, "warn", f"PPG {ppg} ≥ 200 → 당뇨병 기준")

            elif sec_id == "cardio":
                c1,c2,c3 = st.columns(3)
                with c1: ck   = _num(st.text_input("CK (Creatine Kinase, U/L)", placeholder="예: 120", key=_key(sec_id,"ck")))
                with c2: ckmb = _num(st.text_input("CK-MB (U/L)", placeholder="예: 20", key=_key(sec_id,"ckmb")))
                with c3: tro  = _num(st.text_input("Troponin (ng/L or ng/mL)", placeholder="예: 12", key=_key(sec_id,"tro")))
                if tro is not None and tro > 99: _emit(lines, "warn", f"Troponin {tro} ↑ → 심근 손상 가능")

            elif sec_id == "hepatobiliary":
                c1,c2 = st.columns(2)
                with c1: ggt = _num(st.text_input("GGT (감마글루타밀전이효소, U/L)", placeholder="예: 25", key=_key(sec_id,"ggt")))
                with c2: alp = _num(st.text_input("ALP (알칼리성 인산분해효소, U/L)", placeholder="예: 100", key=_key(sec_id,"alp")))
                if ggt is not None and ggt > 3*50: _emit(lines, "warn", f"GGT {ggt} ↑ → 담즙정체/약물 영향 가능")
                if alp is not None and alp > 150: _emit(lines, "warn", f"ALP {alp} ↑ → 담도/뼈 질환 감별")

            elif sec_id == "pancreas":
                c1,c2 = st.columns(2)
                with c1: amy = _num(st.text_input("Amylase (U/L)", placeholder="예: 60", key=_key(sec_id,"amy")))
                with c2: lip = _num(st.text_input("Lipase (U/L)", placeholder="예: 50", key=_key(sec_id,"lip")))
                if lip is not None and lip >= 3*60: _emit(lines, "warn", f"Lipase {lip} ↑ → 췌장염 의심")

            elif sec_id == "coag":
                c1,c2,c3,c4 = st.columns(4)
                with c1: inr = _num(st.text_input("PT-INR", placeholder="예: 1.0", key=_key(sec_id,"inr")))
                with c2: apt = _num(st.text_input("aPTT (초)", placeholder="예: 30", key=_key(sec_id,"aptt")))
                with c3: fib = _num(st.text_input("Fibrinogen (mg/dL)", placeholder="예: 300", key=_key(sec_id,"fibrino")))
                with c4: dd  = _num(st.text_input("D-dimer (µg/mL FEU)", placeholder="예: 0.4", key=_key(sec_id,"ddimer")))
                if inr is not None and inr >= 1.5: _emit(lines, "warn", f"INR {inr} ≥ 1.5 → 응고 저하")
                if apt is not None and apt >= 40: _emit(lines, "warn", f"aPTT {apt} ≥ 40초 → 내인계 연장")
                if dd  is not None and dd  >= 1.0: _emit(lines, "warn", f"D-dimer {dd} ≥ 1.0 → 혈전/염증 가능")

            elif sec_id == "inflammation":
                c1,c2,c3 = st.columns(3)
                with c1: esr  = _num(st.text_input("ESR (적혈구침강속도, mm/hr)", placeholder="예: 15", key=_key(sec_id,"esr")))
                with c2: ferr = _num(st.text_input("Ferritin (ng/mL)", placeholder="예: 80", key=_key(sec_id,"ferritin")))
                with c3: pct  = _num(st.text_input("Procalcitonin (ng/mL)", placeholder="예: 0.05", key=_key(sec_id,"pct")))
                if ferr is not None and ferr >= 500: _emit(lines, "warn", f"Ferritin {ferr} ≥ 500 → 염증/HLH 등 감별")
                if pct is not None and pct >= 0.5: _emit(lines, "warn", f"PCT {pct} ≥ 0.5 → 세균감염 가능성")

            elif sec_id == "lactate":
                la = _num(st.text_input("Lactate (mmol/L)", placeholder="예: 1.2", key=_key(sec_id,"lactate")))
                if la is not None and la >= 2.0: _emit(lines, "warn", f"Lactate {la} ≥ 2.0 → 조직 저관류/패혈증 감별")

    # 세션에 결과 저장(선택)
    st.session_state["special_tests_lines"] = lines
    return lines
