# -*- coding: utf-8 -*-
"""
특수검사 UI/해석 모듈 (카테고리 토글 + 즐겨찾기)
- ✅ 소변검사/혈구지수/보체/지질/심부전/당/심장·근육/간담도/췌장/응고/염증/젖산
- ✅ 모든 입력 라벨을 영어+한글 병기(예: "UPCR (Protein/Cr, 단백/크레아티닌 비율)")
- ✅ UPCR/ACR 10000 초과 시 '단일 라인' 경고(극고값 + 단위/입력 오류 가능성)
"""
from __future__ import annotations
from typing import List, Optional
import streamlit as st
import re

def _num(x):
    try:
        if x is None: 
            return None
        if isinstance(x, (int, float)): 
            return float(x)
        
        # [안전핀 보강] ——, 미입력 등의 방해 문자가 들어오면 무조건 에러 없이 패스
        s = str(x).strip()
        if s in ["—-", "—", "-", "——", "(미입력)", "없음", "None", ""]:
            return None
            
        s = s.replace(",", "")
        s2 = "".join(ch for ch in s if (ch.isdigit() or ch=='.' or ch=='-'))
        return float(s2) if s2 else None
    except Exception:
        return None

def _flag(kind: Optional[str]) -> str:
    return {"ok":"🟢 정상", "warn":"🟡 주의", "risk":"🚨 위험"}.get(kind or "", "")

def _emit(lines: List[str], kind: Optional[str], msg: str):
    tag = _flag(kind)
    lines.append(f"{tag} {msg}" if tag else msg)

# === [PATCH 2026-06-11 KST] Streamlit key namespace guard ===
def _special_ns() -> str:
    """Return a stable namespace so special_tests widgets never collide.
    - Keeps previous state by migrating old global keys once.
    - Includes profile key/_uid when available, but falls back safely.
    """
    try:
        raw = st.session_state.get("key") or st.session_state.get("_uid") or "guest"
        safe = "".join(ch if (str(ch).isalnum() or ch in ("-", "_")) else "_" for ch in str(raw))
        return f"stx_{safe}"
    except Exception:
        return "stx_guest"

def _ns_key(kind: str, name: str) -> str:
    return f"{_special_ns()}_{kind}_{name}"

def _migrate_bool_key(old_key: str, new_key: str, default=True):
    try:
        if new_key not in st.session_state and old_key in st.session_state:
            st.session_state[new_key] = st.session_state.get(old_key)
        return bool(st.session_state.get(new_key, default))
    except Exception:
        return bool(default)

def _tog_key(name: str) -> str: return _ns_key("tog", name)
def _fav_key(name: str) -> str: return _ns_key("fav", name)
# === [/PATCH] ===

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
    key = f"{_special_ns()}_fav_tests"
    if key not in st.session_state and "fav_tests" in st.session_state:
        try:
            st.session_state[key] = list(st.session_state.get("fav_tests", []))
        except Exception:
            st.session_state[key] = []
    st.session_state.setdefault(key, [])
    return st.session_state[key]

def special_tests_ui() -> List[str]:
    lines: List[str] = []
    with st.expander("🧪 특수검사 (선택 입력)", expanded=True):
        st.caption("정성검사는 +/++/+++ , 정량검사는 숫자만 입력. ★로 즐겨찾기 고정.")
        favs = _fav_list()
        
        # 즐겨찾기 고정 칩 영역
        if favs:
            st.markdown("**⭐ 즐겨찾기**")
            chips = st.columns(len(favs))
            for i, sec_id in enumerate(favs):
                with chips[i]:
                    if st.button(f"★ {sec_id}", key=_fav_key(f"chip_{sec_id}")):
                        st.session_state[_tog_key(sec_id)] = True

        # --- 교정된 카테고리 렌더링 루프 부문 ---
        for title, sec_id in SECTIONS:
            c1, c2 = st.columns([0.8, 0.2])
            with c1:
                # 엉켜있던 중복 루프와 문법 오타를 지우고 깔끔하게 정렬 완료
                on = st.toggle(
                    title, 
                    key=_tog_key(sec_id), 
                    value=_migrate_bool_key(f"tog_{sec_id}", _tog_key(sec_id), True)
                )
            with c2:
                isfav = sec_id in favs
                label = "★" if isfav else "☆"
                if st.button(label, key=_fav_key(f"btn_{sec_id}")):
                    if isfav: 
                        favs.remove(sec_id)
                    else:
                        if sec_id not in favs: 
                            favs.append(sec_id)
                    st.rerun() # 즐겨찾기 상태 즉시 반영을 위한 리런 추가

            if not on:
                continue

            # --- 소변검사 / Urinalysis ---
            if sec_id == "urine":
                st.markdown("**요시험지/현미경 (Dipstick / Microscopy)**")
                row1 = st.columns(6)
                with row1[0]: alb = st.selectbox("Albumin (알부민뇨)", ["없음","+","++","+++"], index=0)
                with row1[1]: hem = st.selectbox("Hematuria/Blood (혈뇨/잠혈)", ["없음","+","++","+++"], index=0)
                with row1[2]: glu = st.selectbox("Glucose (요당)", ["없음","+","++","+++"], index=0)
                with row1[3]: nit = st.selectbox("Nitrite (아질산염)", ["없음","+","++","+++"], index=0)
                with row1[4]: leu = st.selectbox("Leukocyte esterase (백혈구 에스테라제)", ["없음","+","++","+++"], index=0)
                with row1[5]: sg  = st.text_input("Specific gravity (요비중)", placeholder="예: 1.015")

                row2 = st.columns(4)
                with row2[0]: rbc  = _num(st.text_input("RBC (/HPF, 적혈구/고배율 시야당)", placeholder="예: 0~2 정상, 3↑ 비정상"))
                with row2[1]: wbc  = _num(st.text_input("WBC (/HPF, 백혈구/고배율 시야당)", placeholder="예: 0~4 정상, 5↑ 비정상"))
                with row2[2]: upcr = _num(st.text_input("UPCR (Protein/Cr, 단백/크레아티닌 비율, mg/gCr)", placeholder="예: 120"))
                with row2[3]: acr  = _num(st.text_input("ACR (Albumin/Cr, 알부민/크레아티닌 비율, mg/gCr)", placeholder="예: 25"))

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

            # --- 혈구지수/망상 / RBC Indices & Reticulocytes ---
            elif sec_id == "rbcidx":
                g1, g2, g3, g4 = st.columns(4)
                with g1: mcv = _num(st.text_input("MCV (Mean Corpuscular Volume, fL)",  placeholder="예: 75"))
                with g2: mch = _num(st.text_input("MCH (Mean Corpuscular Hemoglobin, pg)",  placeholder="예: 26"))
                with g3: rdw = _num(st.text_input("RDW (Red Cell Distribution Width, %)",   placeholder="예: 13.5"))
                with g4: ret = _num(st.text_input("Reticulocyte (망상적혈구, %)", placeholder="예: 1.0"))
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
                with d1: c3   = _num(st.text_input("C3 (Complement 3, mg/dL)", placeholder="예: 90"))
                with d2: c4   = _num(st.text_input("C4 (Complement 4, mg/dL)", placeholder="예: 20"))
                with d3: ch50 = _num(st.text_input("CH50 (Total Complement Activity, U/mL)", placeholder="예: 50"))
                if c3 is not None and c3 < 85: _emit(lines, "warn", f"C3 낮음({c3}) → 면역복합체 질환/활성화 가능성")
                if c4 is not None and c4 < 15: _emit(lines, "warn", f"C4 낮음({c4}) → 보체소모/면역 이상 가능성")
                if ch50 is not None:
                    if ch50 < 30: _emit(lines, "risk", f"CH50 {ch50} (낮음) → 보체 결핍/소모 의심")
                    elif ch50 < 40: _emit(lines, "warn", f"CH50 {ch50} (경도 저하) → 추적 필요")

            elif sec_id == "lipid":
                l1,l2,l3,l4 = st.columns(4)
                with l1: tc  = _num(st.text_input("Total Cholesterol (mg/dL)", placeholder="예: 180"))
                with l2: tg  = _num(st.text_input("Triglyceride (중성지방, mg/dL)", placeholder="예: 120"))
                with l3: hdl = _num(st.text_input("HDL (고밀도지단백, mg/dL)", placeholder="예: 55"))
                with l4: ldl = _num(st.text_input("LDL (저밀도지단백, mg/dL)", placeholder="예: 110"))
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
                with h5: bnp = _num(st.text_input("BNP (뇌나트륨이뇨펩티드, pg/mL)", placeholder="예: 60"))
                with h6: ntp = _num(st.text_input("NT-proBNP (pg/mL)", placeholder="예: 125"))
                if bnp is not None and bnp >= 100: _emit(lines, "warn", f"BNP {bnp} ≥ 100 → 심부전 의심(연령/신장기능 고려)")
                if ntp is not None and ntp >= 900: _emit(lines, "warn", f"NT-proBNP {ntp} 상승 → 연령/신장 기능 고려")

            elif sec_id == "glucose":
                g1,g2,g3 = st.columns(3)
                with g1: fpg  = _num(st.text_input("FPG (식전혈당, mg/dL)", placeholder="예: 95"))
                with g2: ppg1 = _num(st.text_input("PPG 1h (식후1시간, mg/dL)", placeholder="예: 150"))
                with g3: ppg2 = _num(st.text_input("PPG 2h (식후2시간, mg/dL)", placeholder="예: 120"))
                if fpg is not None:
                    if fpg >= 126: _emit(lines, "risk", f"FPG {fpg} ≥ 126 → 당뇨병 가능성")
                    elif fpg >= 100: _emit(lines, "warn", f"FPG {fpg} 100~125 → 공복혈당장애")
                if ppg1 is not None and ppg1 >= 200: _emit(lines, "warn", f"식후1h {ppg1} ≥ 200 → 고혈당")
                if ppg2 is not None:
                    if ppg2 >= 200: _emit(lines, "risk", f"식후2h {ppg2} ≥ 200 → 당뇨병 가능성")
                    elif ppg2 >= 140: _emit(lines, "warn", f"식후2h {ppg2} 140~199 → 내당능장애")

            elif sec_id == "cardio":
                h1,h2,h3,h4 = st.columns(4)
                with h1: ck   = _num(st.text_input("CK (크레아틴키나아제, U/L)", placeholder="예: 160"))
                with h2: ckmb = _num(st.text_input("CK-MB (MB분획, ng/mL)", placeholder="예: 2.5"))
                with h3: troI = _num(st.text_input("Troponin I (트로포닌 I, ng/mL)", placeholder="예: 0.01"))
                with h4: troT = _num(st.text_input("Troponin T (트로포닌 T, ng/mL)", placeholder="예: 0.005"))
                ulnI = _num(st.text_input("ULN for Troponin I (정상상한, ng/mL)", placeholder="예: 0.04"))
                ulnT = _num(st.text_input("ULN for Troponin T (정상상한, ng/mL)", placeholder="예: 0.014"))
                if ck is not None:
                    if ck >= 5000: _emit(lines, "risk", f"CK {ck} → 횡문근융해 의심(즉시 상담)")
                    elif ck >= 1000: _emit(lines, "warn", f"CK {ck} → 근손상/운동/약물 영향 가능")
                if ckmb is not None and ckmb >= 5: _emit(lines, "warn", f"CK-MB {ckmb} ≥ 5 → 심근 손상 지표 상승 가능")
                if troI is not None and troI >= (ulnI if ulnI is not None else 0.04): _emit(lines, "risk", f"Troponin I {troI} ≥ ULN → 심근 손상 의심")
                if troT is not None and troT >= (ulnT if ulnT is not None else 0.014): _emit(lines, "risk", f"Troponin T {troT} ≥ ULN → 심근 손상 의심")

            elif sec_id == "hepatobiliary":
                a1,a2 = st.columns(2)
                with a1: ggt = _num(st.text_input("GGT (감마지티피, U/L)", placeholder="예: 35"))
                with a2: alp = _num(st.text_input("ALP (알키리인산분해효소, U/L)", placeholder="예: 110"))
                if ggt is not None and ggt >= 100: _emit(lines, "warn", f"GGT 상승({ggt}) → 담도/약물 영향 가능")
                if alp is not None and alp >= 150: _emit(lines, "warn", f"ALP 상승({alp}) → 담도/골질환 감별")

            elif sec_id == "pancreas":
                p1,p2 = st.columns(2)
                with p1: amy = _num(st.text_input("Amylase (아밀라아제, U/L)", placeholder="예: 60"))
                with p2: lip = _num(st.text_input("Lipase (리파아제, U/L)", placeholder="예: 40"))
                if amy is not None and amy >= 300: _emit(lines, "warn", f"Amylase 상승({amy}) → 췌장/타장기 영향 가능")
                if lip is not None and lip >= 180:  _emit(lines, "risk", f"Lipase 현저 상승({lip}) → 급성 췌장염 의심")

            elif sec_id == "coag":
                c1,c2,c3,c4 = st.columns(4)
                with c1: inr  = _num(st.text_input("PT-INR (프로트롬빈 시간)", placeholder="예: 1.0"))
                with c2: aptt = _num(st.text_input("aPTT (활성화 부분 트롬보플라스틴 시간, sec)", placeholder="예: 30"))
                with c3: fib  = _num(st.text_input("Fibrinogen (피브리노겐, mg/dL)", placeholder="예: 300"))
                with c4: dd   = _num(st.text_input("D-dimer (디-다이머, µg/mL)", placeholder="예: 0.3"))
                if inr is not None and inr >= 1.5: _emit(lines, "warn", f"INR {inr} ≥ 1.5 → 응고 저하/간기능 저하 가능")
                if aptt is not None and aptt >= 40: _emit(lines, "warn", f"aPTT {aptt} ≥ 40s → 내인성 경로 지연")
                if fib is not None and fib < 150: _emit(lines, "risk", f"Fibrinogen {fib} < 150 → 소모/간기능 저하")
                if dd is not None and dd >= 0.5: _emit(lines, "warn", f"D-dimer {dd} ≥ 0.5 → 혈전/염증 반응 가능(임상과 함께)")

            elif sec_id == "inflammation":
                i1,i2,i3 = st.columns(3)
                with i1: esr  = _num(st.text_input("ESR (적혈구침강속도, mm/h)", placeholder="예: 10"))
                with i2: ferr = _num(st.text_input("Ferritin (페리틴, ng/mL)", placeholder="예: 100"))
                with i3: pct  = _num(st.text_input("Procalcitonin (ng/mL)", placeholder="예: 0.05"))
                if esr is not None and esr >= 40: _emit(lines, "warn", f"ESR {esr} ≥ 40 → 염증/만성질환 가능")
                if ferr is not None and ferr >= 300: _emit(lines, "warn", f"Ferritin {ferr} ≥ 300 → 염증/철과부하 감별")
                if pct is not None:
                    if pct >= 2: _emit(lines, "risk", f"PCT {pct} ≥ 2 → 패혈증 가능성 높음")
                    elif pct >= 0.5: _emit(lines, "warn", f"PCT {pct} 0.5~2 → 세균감염 의심")

            elif sec_id == "lactate":
                lc = _num(st.text_input("Lactate (젖산, mmol/L)", placeholder="예: 1.5"))
                if lc is not None and lc >= 2: _emit(lines, "warn", f"Lactate {lc} ≥ 2 → 조직저산소/패혈증 감시")

    return lines
