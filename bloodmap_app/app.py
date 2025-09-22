
# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import date, timedelta, timezone, datetime
import csv, os, io, json, hashlib, math

# ---- 외부 모듈(프로젝트 기존 파일) ----
from peds_profiles import get_symptom_options
from core_utils import nickname_pin, clean_num, schedule_block
from drug_db import DRUG_DB, ensure_onco_drug_db, display_label
from onco_map import build_onco_map, auto_recs_by_dx, dx_display
from ui_results import results_only_after_analyze, render_adverse_effects, collect_top_ae_alerts
from pdf_export import export_md_to_pdf

# ---- 고정 ----
KST = timezone(timedelta(hours=9))

def _data_root():
    for d in [os.getenv("BLOODMAP_DATA_ROOT","").strip(), "/mnt/data", os.path.join(os.getenv("TMPDIR") or "/tmp","bloodmap_data")]:
        if not d: continue
        try:
            os.makedirs(d, exist_ok=True)
            p = os.path.join(d, ".probe"); open(p,"w").write("ok"); os.remove(p)
            return d
        except Exception:
            continue
    d = os.path.join(os.getenv("TMPDIR") or "/tmp","bloodmap_data"); os.makedirs(d, exist_ok=True); return d

# ---------------- 프로필 + PIN ----------------
def _pin_path(uid): 
    root=_data_root(); p=os.path.join(root,"profile",f"{uid}.pin"); os.makedirs(os.path.dirname(p), exist_ok=True); return p
def _prof_path(uid):
    root=_data_root(); p=os.path.join(root,"profile",f"{uid}.json"); os.makedirs(os.path.dirname(p), exist_ok=True); return p

def _hash_pin(pin:str)->str:
    return hashlib.sha256(("bloodmap_salt::"+(pin or "")).encode("utf-8")).hexdigest()

def save_profile(uid:str, prof:dict, pin:str|None=None):
    if pin is not None:
        open(_pin_path(uid),"w",encoding="utf-8").write(_hash_pin(pin))
    tmp=_prof_path(uid)+".tmp"
    json.dump(prof, open(tmp,"w",encoding="utf-8"), ensure_ascii=False, indent=2)
    os.replace(tmp,_prof_path(uid))

def load_profile(uid:str)->dict:
    try: return json.load(open(_prof_path(uid),"r",encoding="utf-8"))
    except Exception: return {}

def check_pin(uid:str, pin:str)->bool:
    try:
        want=open(_pin_path(uid),"r",encoding="utf-8").read().strip()
        return want == _hash_pin(pin)
    except Exception:
        return True  # 설정 안되어 있으면 통과

def render_profile_box(uid:str):
    st.markdown("### 👤 프로필 / PIN")
    with st.expander("프로필 열기/저장", expanded=False):
        age_y = st.number_input("나이(세)", min_value=0, step=1, value=st.session_state.get("age_y", 30), key=f"age_{uid}")
        sex = st.selectbox("성별", ["남","여"], key=f"sex_{uid}")
        height_cm = st.number_input("키(cm)", min_value=0.0, step=0.1, value=170.0, key=f"h_{uid}")
        weight = st.number_input("체중(kg)", min_value=0.0, step=0.1, value=60.0, key=f"w_{uid}")
        syrup_apap = st.text_input("APAP 시럽 농도(예: 160 mg/5mL)", value="160/5", key=f"sap_{uid}")
        syrup_ibu = st.text_input("IBU 시럽 농도(예: 100 mg/5mL)", value="100/5", key=f"sib_{uid}")
        if st.button("💾 프로필 저장", key=f"save_prof_{uid}"):
            save_profile(uid, {"age":age_y,"sex":sex,"height_cm":height_cm,"weight":weight,
                               "syrup_apap":syrup_apap,"syrup_ibu":syrup_ibu})
            st.success("프로필 저장됨")
        if st.button("📥 프로필 불러오기", key=f"load_prof_{uid}"):
            p=load_profile(uid); 
            if p: st.session_state[f"age_{uid}"]=p.get("age",30); st.session_state[f"sex_{uid}"]=p.get("sex","남")
            st.session_state[f"h_{uid}"]=p.get("height_cm",170.0); st.session_state[f"w_{uid}"]=p.get("weight",60.0)
            st.success("프로필 불러옴")
    with st.expander("PIN 설정/검증", expanded=False):
        pin_set = st.text_input("새 PIN(4-6자리)", type="password", key=f"pinset_{uid}")
        pin_chk = st.text_input("열람 PIN 입력", type="password", key=f"pinchk_{uid}")
        c1,c2 = st.columns(2)
        with c1:
            if st.button("🔐 PIN 저장", key=f"savepin_{uid}"):
                if pin_set and pin_set.isdigit() and 4<=len(pin_set)<=6:
                    save_profile(uid, load_profile(uid), pin=pin_set); st.success("PIN 저장/갱신")
                else:
                    st.error("숫자 4–6자리로 설정해주세요")
        with c2:
            if st.button("✅ PIN 확인", key=f"checkpin_{uid}"):
                st.success("통과") if check_pin(uid, pin_chk) else st.error("PIN 불일치")

# -------------- 케어로그 --------------
def _carelog_path(uid): 
    p=os.path.join(_data_root(),"care_log",f"{uid}.json"); os.makedirs(os.path.dirname(p), exist_ok=True); return p
def carelog_load(uid):
    try: return json.load(open(_carelog_path(uid),"r",encoding="utf-8"))
    except Exception: return []
def carelog_save(uid, data):
    tmp=_carelog_path(uid)+".tmp"; json.dump(data, open(tmp,"w",encoding="utf-8"), ensure_ascii=False, indent=2); os.replace(tmp,_carelog_path(uid))
def carelog_add(uid, e): d=carelog_load(uid); d.append(e); carelog_save(uid,d)

def analyze_symptoms(entries):
    em, gen = [], []
    kinds = [e.get("kind") for e in entries if e.get("type") in ("vomit","diarrhea")]
    has_green_vomit = any(k and "초록" in k for k in kinds)
    has_bloody = any(k and ("혈변" in k or "검은" in k or "녹색혈변" in k) for k in kinds)
    fevers = [float(e.get("temp") or 0) for e in entries if e.get("type")=="fever"]
    has_high_fever = any(t >= 39.0 for t in fevers)
    vomit_ct = sum(1 for e in entries if e.get("type")=="vomit")
    diarr_ct = sum(1 for e in entries if e.get("type")=="diarrhea")
    if has_bloody: em.append("혈변/검은변/녹색혈변")
    if has_green_vomit: em.append("초록(담즙) 구토")
    if vomit_ct >= 3: em.append("2시간 내 구토 ≥3회")
    if diarr_ct >= 6: em.append("24시간 설사 ≥6회")
    if has_high_fever: em.append("고열 ≥39.0℃")
    gen = ["혈변/검은변","초록 구토","의식저하/경련/호흡곤란","6시간 무뇨·중증 탈수","고열 지속","심한 복통/팽만/무기력"]
    return em, gen

def render_carelog(uid, nick):
    st.markdown("### 🗒️ 케어로그")
    c1,c2,c3,c4 = st.columns(4)
    with c1:
        if st.button("발열 +", key=f"btn_fever_{uid}"):
            t = st.number_input("현재 체온(℃)", value=38.0, step=0.1, key=f"temp_now_{uid}")
            carelog_add(uid, {"type":"fever","temp":t,"ts": datetime.now(KST).isoformat()})
            st.success("발열 기록됨")
    with c2:
        vk = st.selectbox("구토 유형", ["흰","노랑","초록(담즙)","기타"], index=1, key=f"vomit_kind_{uid}")
        if st.button("구토 +", key=f"btn_vomit_{uid}"):
            carelog_add(uid, {"type":"vomit","kind":vk,"ts": datetime.now(KST).isoformat()})
            st.success("구토 기록됨")
    with c3:
        dk = st.selectbox("설사 유형", ["노랑","진한노랑","거품","녹색","녹색혈변","혈변","검은색","기타"], index=0, key=f"diarr_kind_{uid}")
        if st.button("설사 +", key=f"btn_diarr_{uid}"):
            carelog_add(uid, {"type":"diarrhea","kind":dk,"ts": datetime.now(KST).isoformat()})
            st.success("설사 기록됨")
    with c4:
        if st.button("APAP 160mg 기록 +", key=f"btn_apap_{uid}"):
            carelog_add(uid, {"type":"apap","mg":160,"ts": datetime.now(KST).isoformat()}); st.success("APAP 기록됨")
        if st.button("IBU 100mg 기록 +", key=f"btn_ibu_{uid}"):
            carelog_add(uid, {"type":"ibu","mg":100,"ts": datetime.now(KST).isoformat()}); st.success("IBU 기록됨")

    st.divider()
    show = st.toggle("최근 로그 보기", value=False, key=f"toggle_show_{uid}")
    win = st.segmented_control("표시 시간창", options=[2,6,12,24], format_func=lambda h: f"{h}h", key=f"win_{uid}")
    if not show:
        st.caption("※ 입력 후 ‘최근 로그 보기’를 켜면 표시됩니다.")
        return [], []

    now = datetime.now(KST)
    entries = [e for e in carelog_load(uid) if (now - datetime.fromisoformat(e.get("ts"))).total_seconds() <= int(win)*3600]
    if not entries:
        st.info(f"최근 {win}시간 이내 기록 없음.")
        return [], []
    st.markdown(f"#### 최근 {win}h — {nick} ({uid})")
    def _ko_line(e):
        t = e.get("type"); ts = e.get("ts","")
        if t == "fever": return f"- {ts} · 발열 {e.get('temp')}℃"
        if t == "apap": return f"- {ts} · APAP {e.get('mg')} mg"
        if t == "ibu":  return f"- {ts} · IBU {e.get('mg')} mg"
        if t == "vomit":
            k = e.get("kind"); return f"- {ts} · 구토" + (f" ({k})" if k else "")
        if t == "diarrhea":
            k = e.get("kind"); return f"- {ts} · 설사" + (f" ({k})" if k else "")
        return f"- {ts} · {t}"
    lines = [_ko_line(e) for e in sorted(entries, key=lambda x: x.get("ts",""))]
    for L in lines: st.write(L)
    em, gen = analyze_symptoms(entries)
    if em: st.error("🚨 응급도: " + " · ".join(em))
    st.caption("일반 응급실 기준: " + " · ".join(gen))
    return lines, entries

# -------- 해열제 가드 --------
def render_antipy_guard(profile, labs, care_entries):
    def _within_24h(ts):
        try: return (datetime.now(KST) - datetime.fromisoformat(ts)).total_seconds() <= 24*3600
        except Exception: return False
    apap_total = 0.0; ibu_total = 0.0; last_apap=None; last_ibu=None
    for e in care_entries or []:
        if not _within_24h(e.get("ts","")): continue
        if e.get("type")=="apap": apap_total += float(e.get("mg") or 0); last_apap = e.get("ts")
        if e.get("type")=="ibu":  ibu_total  += float(e.get("mg") or 0); last_ibu  = e.get("ts")
    age = int(profile.get("age", 30)); is_adult = age >= 18
    weight = float(profile.get("weight", 60))
    lim_apap = min(4000.0 if is_adult else 75.0*(weight or 0), 4000.0)
    lim_ibu  = min(1200.0 if is_adult else 30.0*(weight or 0), 1200.0)
    def _next(last_ts,h): 
        if not last_ts: return None
        try: return (datetime.fromisoformat(last_ts)+timedelta(hours=h)).strftime("%H:%M")
        except Exception: return None
    st.caption(f"APAP 24h: {int(apap_total)}/{int(lim_apap)} mg · 다음가능: {_next(last_apap,4) or '—'}")
    st.caption(f"IBU 24h: {int(ibu_total)}/{int(lim_ibu)} mg · 다음가능: {_next(last_ibu,6) or '—'}")
    # Safety gates
    plt = labs.get("PLT"); egfr = labs.get("eGFR"); ast_v = labs.get("AST"); alt_v = labs.get("ALT")
    if isinstance(plt,(int,float)) and plt < 50000: st.error("IBU 금지: PLT < 50k")
    if isinstance(egfr,(int,float)) and egfr < 60: st.warning("eGFR < 60: IBU 주의")
    if (isinstance(ast_v,(int,float)) and ast_v > 120) or (isinstance(alt_v,(int,float)) and alt_v > 120): st.warning("AST/ALT > 120: APAP 간기능 주의")

# -------- 응급 배너 --------
def render_emergency_banners(labs, care_entries):
    has_recent_fever = any(e.get("type")=="fever" and float(e.get("temp") or 0) >= 38.0 for e in (care_entries or []))
    anc = labs.get("ANC")
    if isinstance(anc,(int,float)) and anc < 500 and has_recent_fever:
        st.error("🚨 발열성 호중구감소증(FN) 의심: 최근 24h 발열 + ANC<500 → 즉시 진료 권고")
    na = labs.get("Na"); k = labs.get("K")
    if isinstance(na,(int,float)) and (na < 125 or na > 155): st.error("🚨 전해질 경보: Na <125 또는 >155")
    if isinstance(k,(int,float)) and k >= 6.0: st.error("🚨 전해질 경보: K ≥ 6.0")

# -------- eGFR 계산 --------
def egfr_calculate(age_y, sex, scr_mgdl, height_cm=None):
    if scr_mgdl is None:
        return None
    try:
        a = float(age_y or 0)
        s = float(scr_mgdl)
    except Exception:
        return None
    if a < 18:
        if not height_cm: return None
        k = 0.413
        return round((k * float(height_cm)) / max(s, 0.0001), 1)
    # CKD-EPI 2021
    female = (sex == "여")
    kappa = 0.7 if female else 0.9
    alpha = -0.241 if female else -0.302
    egfr = 142.0 * (min(s/kappa,1.0)**alpha) * (max(s/kappa,1.0)**-1.200) * (0.9938**a) * (1.012 if female else 1.0)
    return round(egfr,1)

# -------- 단위 가드/자동 변환 --------
def convert_units(labs_vals, unit_opts):
    memo = []
    out = dict(labs_vals)
    # Glucose mg/dL <-> mmol/L (1 mmol/L = 18 mg/dL)
    if unit_opts.get("Glu") == "mmol/L" and out.get("Glu") is not None:
        out["Glu"] = round(float(out["Glu"])*18.0,1); memo.append("Glucose: mmol/L→mg/dL 변환(×18)")
    # Phosphate P mg/dL <-> mmol/L (1 mg/dL = 0.323 mmol/L → 1 mmol/L ≈ 3.10 mg/dL)
    if unit_opts.get("P") == "mmol/L" and out.get("P") is not None:
        out["P"] = round(float(out["P"])*3.10,2); memo.append("P: mmol/L→mg/dL 변환(×3.10)")
    # Calcium mg/dL <-> mmol/L (1 mmol/L = 4.0 mg/dL)
    if unit_opts.get("Ca") == "mmol/L" and out.get("Ca") is not None:
        out["Ca"] = round(float(out["Ca"])*4.0,2); memo.append("Ca: mmol/L→mg/dL 변환(×4.0)")
    # Creatinine μmol/L <-> mg/dL (1 mg/dL = 88.4 μmol/L → 1 μmol/L ≈ 0.0113 mg/dL)
    if unit_opts.get("Cr") == "μmol/L" and out.get("Cr") is not None:
        out["Cr"] = round(float(out["Cr"])/88.4,3); memo.append("Cr: μmol/L→mg/dL 변환(÷88.4)")
    # Alias: CR -> Cr
    if out.get("CR") is not None and (out.get("Cr") is None):
        out["Cr"] = out["CR"]
    return out, memo

# -------- 그래프 CSV --------
def graph_csv_path(uid): 
    p=os.path.join(_data_root(),"bloodmap_graph",f"{uid}.labs.csv"); os.makedirs(os.path.dirname(p), exist_ok=True); return p

def append_graph_csv(uid, labs, when):
    path = graph_csv_path(uid)
    cols = ["Date","WBC","Hb","PLT","ANC","Ca","Na","K","Cl","Alb","Glu","AST","ALT","Cr","CRP","UA","T.B","P","TC","TG","HDL","LDL","NonHDL"]
    row = {"Date": when};  [row.__setitem__(c, labs.get(c)) for c in cols[1:]]
    exists = os.path.exists(path)
    with open(path,"a", newline="", encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=cols)
        if not exists: w.writeheader()
        w.writerow(row)
    return path

def load_last_row(uid):
    path = graph_csv_path(uid)
    if not os.path.exists(path): return None
    try:
        df = pd.read_csv(path)
        if df.empty: return None
        last = df.sort_values("Date").iloc[-1].to_dict()
        return last
    except Exception:
        return None


# -------- 특수검사 렌더링(안전 필터) --------
def render_special_tests(labs: dict):
    st.subheader("🧬 특수검사 (토글로 입력)")
    lines = []
    # Myoglobin rule (no ULN known): only hard cut
    try:
        mg = labs.get("Myoglobin")
        if isinstance(mg,(int,float)):
            if mg >= 500: lines.append("🔴 Myoglobin ≥500 ng/mL: 심한 근육손상/횡문근융해 가능 — 즉시 평가")
            elif mg is not None: lines.append("🟡 Myoglobin 상승 가능성: 근손상/초기 심근 손상 고려(ULN 비교 필요)")
    except Exception: pass
    # Cardiac enzymes
    try:
        tro = labs.get("Troponin")
        if isinstance(tro,(int,float)) and tro>0.04: lines.append("🔴 Troponin 상승: 심근 손상 의심(참고치 종속)")
    except Exception: pass
    try:
        ckmb = labs.get("CKMB") or labs.get("CK_MB") or labs.get("CK-MB")
        if isinstance(ckmb,(int,float)) and ckmb>5: lines.append("🟡 CK‑MB 상승 가능: 심근 관련성 고려")
    except Exception: pass
    # Coagulation
    try:
        inr = labs.get("INR")
        if isinstance(inr,(int,float)) and inr>=1.5: lines.append("🟡 INR ≥1.5: 출혈 위험 증가, 시술 전 주의")
    except Exception: pass
    try:
        dd = labs.get("D-Dimer") or labs.get("D_dimer")
        if isinstance(dd,(int,float)) and dd>=0.5: lines.append("🟡 D‑Dimer ≥0.5: 혈전성 질환 감별 필요(비특이적)")
    except Exception: pass
    # Null/dirty guard
    lines = [str(x).strip() for x in lines if isinstance(x,(str,)) and str(x).strip() and "NULL" not in str(x).upper()]
    if not lines:
        st.caption("특수검사 입력/해석 없음")
        return []
    for L in lines: st.write("- " + L)
    return lines

# -------- Δ와 식이가이드(빽빽) --------
def delta_icon(cur, prev):
    try:
        if prev is None or cur is None: return ""
        d = float(cur) - float(prev)
        if abs(d) < 1e-9: return "➖"
        return "▲" if d>0 else "▼"
    except Exception:
        return ""

def corrected_calcium(ca_mgdl, alb_gdl):
    try:
        if ca_mgdl is None or alb_gdl is None: return None
        # Payne formula: Corrected Ca = measured Ca + 0.8*(4.0 - albumin)
        return round(float(ca_mgdl) + 0.8*(4.0 - float(alb_gdl)), 2)
    except Exception: return None

def dense_diet_guides(labs, heme_flag=False):
    L=[]; add=L.append
    Na=labs.get("Na"); K=labs.get("K"); Ca=labs.get("Ca"); Alb=labs.get("Alb"); P=labs.get("P"); Glu=labs.get("Glu"); Cr=labs.get("Cr")
    ANC=labs.get("ANC"); eG=labs.get("eGFR"); Tbil=labs.get("T.B"); UA=labs.get("UA"); Cl=labs.get("Cl")
    Ca_corr = corrected_calcium(Ca, Alb) if (Ca is not None and Alb is not None) else None

    # ANC
    if ANC is not None:
        if ANC < 500: add("ANC <500: 생식/샐러드/회 금지, 완전가열 조리, 외식 지양, 과일은 껍질제거·세척 철저")
        elif ANC < 1000: add("ANC 500–1000: 생식 제한, 조리음식 위주, 외식은 조심 선택")
        else: add("ANC ≥1000: 일반 식이 가능하나 위생 준수")
    # Na
    if Na is not None:
        if Na<125: add("Na<125: 물 제한·의료평가 필요(저나트륨)")
        elif Na<135: add("Na 125–134: 수분 과다 피하고 전해질 음료 소량")
        elif Na>155: add("Na>155: 즉시 의료평가(고나트륨)·수분 보충 지도")
        elif Na>145: add("Na 146–155: 충분한 수분 섭취 권장")
    # K
    if K is not None:
        if K>=6.0: add("K≥6.0: 응급 평가(고칼륨)·칼륨 높은 식품 회피(바나나·오렌지·감자 등)")
        elif K>=5.5: add("K 5.5–5.9: 고칼륨 식품 제한·의료진 상담")
        elif K<3.0: add("K<3.0: 바나나·아보카도 등 칼륨 보강, 필요 시 경구제 고려")
        elif K<3.5: add("K 3.0–3.4: 칼륨 보강 식단 권장")
    # Ca (corrected)
    if Ca_corr is not None:
        if Ca_corr<8.0: add(f"보정 Ca<8.0: 칼슘/비타민D 보강 음식, 증상시 평가")
        elif Ca_corr>10.5: add(f"보정 Ca>10.5: 수분섭취 증가, 칼슘/비타민D 과다 회피")
    # Phosphate (P)
    if P is not None:
        if P<2.5: add("P<2.5: 인 풍부 식품(유제품·육류·달걀) 보강")
        elif P>4.5: add("P>4.5: 가공식품·콜라·인산염 첨가물 제한")
    # Albumin
    if Alb is not None:
        if Alb<3.0: add("Alb<3.0: 단백질·열량 보강(육류·달걀·콩류), 작은 끼니 자주")
        elif Alb<3.5: add("Alb 3.0–3.4: 단백질 보강 권장")
    # Glucose
    if Glu is not None:
        if Glu<70: add("혈당<70: 즉시 당분(15g) 섭취·재측정")
        elif Glu>250: add("혈당>250: 수분섭취·케톤 위험시 평가")
        elif Glu>180: add("혈당 180–250: 당질 조절·식후 활동")
    # Creatinine/eGFR
    if Cr is not None:
        if Cr>1.3: add("Cr 상승: 단백질 과다·NSAI Ds 주의, 수분 충분히")
    if eG is not None:
        if eG<30: add("eGFR<30: 칼륨/인 제한 식이, 약물용량 조정 필요")
        elif eG<60: add("eGFR 30–59: 나트륨·칼륨 주의, 수분 관리")
    # Lipids
    LDL = labs.get("LDL"); TC = labs.get("TC"); TG = labs.get("TG"); HDL = labs.get("HDL"); NonHDL = labs.get("NonHDL")
    if LDL is not None:
        if LDL >= 190: add("LDL≥190: 고강도 지질치료 평가, 포화지방/트랜스지방 엄격 제한")
        elif LDL >= 160: add("LDL 160–189: 포화지방 제한·식이섬유↑·운동")
    if TG is not None:
        if TG >= 500: add("TG≥500: 췌장염 위험 — 단당/알코올 제한·의료평가")
        elif TG >= 200: add("TG 200–499: 당질 제한·체중조절·운동")
    if HDL is not None and HDL < 40: add("HDL<40: 유산소 운동·체중감량 권장")
    if NonHDL is not None and NonHDL >= 190: add("Non‑HDL≥190: 지질 집중 관리 필요")

    # Uric acid
    if UA is not None:
        if UA>7.0: add("요산>7: 퓨린 많은 음식(내장·멸치·맥주) 제한·수분 섭취")
    # Bilirubin
    if Tbil is not None:
        if Tbil>2.0: add("총빌리루빈>2: 지방 과다 피하고 간친화 식단, 약물 상호작용 주의")
    # Chloride (보조)
    if Cl is not None and (Cl<95 or Cl>110):
        add("Cl 비정상: 수분·전해질 균형 평가")

    if not L:
        add("특이 식이 제한 없음. 균형 잡힌 식단과 위생 수칙 유지.")
    if heme_flag:
        L.append("혈액암/면역저하 시에는 위 사항을 **보수적으로** 적용.")
    return L

# ---------------- 단위 선택 + 입력 ----------------


def labs_input_with_units(uid, cols_per_row=1):
    st.markdown("### 2) 피수치 입력 + 단위 가드 (분류별)")

    # --- 공통 단위 설정 ---
    unit_opts = {"Glu":"mg/dL","P":"mg/dL","Ca":"mg/dL","Cr":"mg/dL"}
    vals = {}

    def _field(label, code):
        vals[code] = clean_num(st.text_input(label, key=f"lab_{code}_{uid}"))
        if code in ("Glu","P","Ca","Cr"):
            unit_opts[code] = st.selectbox(f"{code} 단위", ["mg/dL","mmol/L"] if code in ("Glu","P","Ca") else ["mg/dL","μmol/L"], key=f"unit_{code}_{uid}")

    # --- 분류 1: 혈액(조혈) ---
    with st.expander("🩸 혈액(조혈) — WBC/Hb/PLT/ANC/CRP", expanded=True):
        _field("WBC(백혈구)", "WBC")
        _field("Hb(혈색소)", "Hb")
        _field("PLT(혈소판)", "PLT")
        _field("ANC", "ANC")
        _field("CRP(C-반응단백)", "CRP")

    # --- 분류 2: 전해질/신장 ---
    with st.expander("💧 전해질/신장 — Na/K/Cl/Cr/UA", expanded=True):
        _field("Na(나트륨)", "Na")
        _field("K(칼륨)", "K")
        _field("Cl(염소)", "Cl")
        _field("Cr(크레아티닌)", "Cr")
        _field("UA(요산)", "UA")

    # --- 분류 3: 간/단백 ---
    with st.expander("🧪 간/단백 — AST/ALT/T.B/Alb", expanded=True):
        _field("AST(간수치)", "AST")
        _field("ALT(간수치)", "ALT")
        _field("T.B(총빌리루빈)", "T.B")
        _field("Alb(알부민)", "Alb")

    # --- 분류 4: 당/무기질 ---
    with st.expander("🍚 당/무기질 — Glu/Ca/P", expanded=True):
        _field("Glu(혈당)", "Glu")
        _field("Ca(칼슘)", "Ca")
        _field("P(인)", "P")

    # --- 특수검사(선택 토글) ---
    st.markdown("### 🧬 특수검사 — 필요 항목만 토글로 표시")
    colA, colB = st.columns(2)
    with colA:
        tg_urine = st.toggle("🥤 뇨검사", value=False, key=f"tg_urine_{uid}")
        tg_lipid = st.toggle("🥑 지질/콜레스테롤", value=False, key=f"tg_lipid_{uid}")
        tg_compl = st.toggle("🧷 보체", value=False, key=f"tg_compl_{uid}")
    with colB:
        tg_card  = st.toggle("❤️ 심근효소", value=False, key=f"tg_card_{uid}")
        tg_coag  = st.toggle("🩹 응고/혈전", value=False, key=f"tg_coag_{uid}")

    if tg_urine:
        with st.expander("🥤 뇨검사", expanded=True):
            _field("요비중(SG)", "U_SG")
            _field("요 pH", "U_pH")
            _field("요단백(정성)", "U_PRO")
            _field("요당(정성)", "U_GLU")
            _field("요케톤(정성)", "U_KET")
            _field("요잠혈(정성)", "U_BLD")
            _field("아질산염(Nitrite)", "U_NIT")
            _field("백혈구 에스터레이스", "U_LEU")
            _field("알부민/크레아티닌비(ACR, mg/g)", "U_ACR")

    if tg_lipid:
        with st.expander("🥑 지질/콜레스테롤", expanded=True):
            _field("총콜레스테롤(TC, mg/dL)", "TC")
            _field("중성지방(TG, mg/dL)", "TG")
            _field("HDL-콜레스테롤(mg/dL)", "HDL")
            _field("LDL-콜레스테롤(calc/direct, mg/dL)", "LDL")
            # Non-HDL은 아래 계산
    if tg_compl:
        with st.expander("🧷 보체", expanded=True):
            _field("C3 (mg/dL)", "C3")
            _field("C4 (mg/dL)", "C4")
            _field("CH50", "CH50")

    if tg_card:
        with st.expander("❤️ 심근효소", expanded=True):
            _field("Troponin", "Troponin")
            _field("CK-MB", "CKMB")
            _field("CK(크레아틴키나제)", "CK")
            _field("Myoglobin(근육)", "Myoglobin")

    if tg_coag:
        with st.expander("🩹 응고/혈전", expanded=True):
            _field("PT(초)", "PT")
            _field("aPTT(초)", "aPTT")
            _field("INR", "INR")
            _field("D-Dimer", "D-Dimer")

    # 변환 & 별칭 병합
    converted, memo = convert_units(vals, unit_opts)
    if memo:
        st.caption("단위 변환 적용: " + " · ".join(memo))

    # 파생값: Non-HDL
    try:
        tc = float(converted.get("TC")) if converted.get("TC") is not None else None
        hdl = float(converted.get("HDL")) if converted.get("HDL") is not None else None
        if tc is not None and hdl is not None:
            converted["NonHDL"] = round(tc - hdl, 1)
    except Exception:
        pass

    return converted



# ----------------- APP -----------------
ensure_onco_drug_db(DRUG_DB)
ONCO_MAP = build_onco_map()

st.set_page_config(page_title="BloodMap — PRO MAX", page_icon="🩸", layout="centered")
st.title("BloodMap — PRO MAX (모바일/Δ/eGFR/식이가이드/임포트/PIN)")
st.caption("v2025-09-22")

nick, pin, key = nickname_pin()
uid = f"{nick}_{pin}" if (nick and pin) else "guest_0000"

# PIN gate for private sections
with st.sidebar:
    st.markdown("### 🔐 PIN 게이트")
    pin_try = st.text_input("열람 PIN", type="password", key=f"pin_try_{uid}")
    gate_ok = True
    try:
        want = open(os.path.join(_data_root(),"profile",f"{uid}.pin"),"r",encoding="utf-8").read().strip()
        gate_ok = (want == hashlib.sha256(("bloodmap_salt::"+(pin_try or "")).encode("utf-8")).hexdigest())
        st.caption("상태: ✅ 통과" if gate_ok else "상태: 🔒 잠김")
    except Exception:
        st.caption("PIN 미설정")

st.divider()
mode = st.radio("모드 선택", ["암", "일상", "소아"], horizontal=True, key=f"mode_{uid}")
place_carelog_under_special = st.toggle("특수해석 밑에 케어로그 표시", value=True, key=f"carelog_pos_{uid}")
cols_per_row = st.select_slider("입력칸 배열(모바일 1열 추천)", options=[1,2,3,4], value=1, key=f"cols_{uid}")

# 프로필/PIN 박스
render_profile_box(uid)

def show_lab_summary(uid, labs, prof):
    # load last row for deltas
    last = load_last_row(uid) or {}
    # eGFR compute
    eg = egfr_calculate(prof.get("age",30), prof.get("sex","남"), labs.get("Cr"), prof.get("height_cm"))
    if eg is not None: labs["eGFR"] = eg
    # table with deltas
    order = ["WBC","Hb","PLT","ANC","Na","K","Cl","Ca","Alb","Glu","AST","ALT","Cr","CRP","UA","T.B","P","TC","TG","HDL","LDL","NonHDL","eGFR"]
    st.subheader("🧪 요약(Δ 포함)")
    rows = []
    for k in order:
        if k not in labs: continue
        cur = labs.get(k)
        prev = None
        if last:
            prev = last.get(k if k!="eGFR" else "eGFR")
        icon = delta_icon(cur, prev)
        rows.append({"항목":k, "현재":cur, "이전":prev, "Δ": (None if (cur is None or prev is None) else round(float(cur)-float(prev),2)), "":icon})
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, height=320)

# === 암 모드 ===
if mode == "암":
    st.markdown("### 1) 암 선택")
    group = st.selectbox("암 카테고리", list(ONCO_MAP.keys()) or ["혈액암"], key=f"oncog_{uid}")
    dx_options = list(ONCO_MAP.get(group, {}).keys()) or ["직접 입력"]
    dx = st.selectbox("진단(영문+한글)", dx_options, key=f"oncodx_{uid}", format_func=lambda x: dx_display(group, x) if x else x)
    if dx == "직접 입력": dx = st.text_input("진단(직접 입력)", key=f"oncodx_manual_{uid}")
    if dx: st.caption(dx_display(group, dx))

    labs = labs_input_with_units(uid, cols_per_row)
    prof = load_profile(uid) or {"age":30,"sex":"남","height_cm":170.0,"weight":60.0}
    show_lab_summary(uid, labs, prof)
    sp_lines = render_special_tests(labs)

    # 저장/그래프 CSV
    st.markdown("#### 💾 저장/그래프 CSV")
    when = st.date_input("측정일", value=date.today(), key=f"when_{uid}")
    c1,c2 = st.columns(2)
    with c1:
        if st.button("📈 피수치 CSV에 저장", key=f"savecsv_{uid}"):
            path = append_graph_csv(uid, labs, when.strftime("%Y-%m-%d")); st.success(f"그래프 CSV 저장: {path}")
    with c2:
        up = st.file_uploader("CSV/엑셀 가져오기(병합)", type=["csv","xlsx"], key=f"u_{uid}")
        if up is not None and st.button("↔️ 병합 실행", key=f"merge_{uid}"):
            try:
                dfu = pd.read_excel(up) if up.name.endswith(".xlsx") else pd.read_csv(up)
                # 간단 매핑 UI
                st.write("열 매핑을 선택하세요:")
                cols = list(dfu.columns)
                date_col = st.selectbox("날짜 열", cols, key=f"map_date_{uid}")
                code_map = {}
                targets = ["WBC","Hb","PLT","ANC","Na","K","Cl","Ca","Alb","Glu","AST","ALT","Cr","CRP","UA","T.B","P","TC","TG","HDL","LDL","NonHDL"]
                for t in targets:
                    code_map[t] = st.selectbox(f"{t} 열", ["(없음)"]+cols, key=f"map_{t}_{uid}")
                if st.button("✅ 매핑 저장·병합", key=f"do_merge_{uid}"):
                    recs = []
                    for _,r in dfu.iterrows():
                        row={"Date": str(r.get(date_col))[:10]}
                        for t, col in code_map.items():
                            if col!="(없음)": row[t]= r.get(col)
                        recs.append(row)
                    # append/merge to CSV
                    path = graph_csv_path(uid)
                    exists = os.path.exists(path)
                    old = pd.read_csv(path) if exists else pd.DataFrame(columns=["Date"]+targets)
                    new = pd.DataFrame(recs)
                    merged = (pd.concat([old,new], ignore_index=True)
                              .drop_duplicates(subset=["Date"], keep="last")
                              .sort_values("Date"))
                    merged.to_csv(path, index=False)
                    st.success(f"병합 완료 → {path}")
            except Exception as e:
                st.error(f"가져오기 오류: {e}")

    # 케어로그/가드/응급배너
    if place_carelog_under_special:
        st.divider(); st.subheader("케어 · 해열제")
        care_lines, care_entries = render_carelog(uid, nick)
        render_antipy_guard(prof, labs, care_entries)
        render_emergency_banners(labs, care_entries)

    # 식이가이드(빽빽)
    st.subheader("🍽️ 식이가이드")
    diet_lines = dense_diet_guides(labs or {}, heme_flag=(group=="혈액암")); [st.write("- "+L) for L in diet_lines]

    # 해석/보고서
    if st.button("🔎 해석하기", key=f"analyze_cancer_{uid}"):
        st.session_state["analyzed"] = True
        st.session_state["analysis_ctx"] = {
            "mode":"암","group":group,"dx":dx,"dx_label": dx_display(group, dx),
            "labs": labs, "diet_lines": diet_lines, "special_tests": sp_lines,
            "user_chemo": [], "user_targeted": [], "user_abx": [],
            "care_lines": care_lines if place_carelog_under_special else [],
            "triage_high": analyze_symptoms(care_entries)[0] if place_carelog_under_special else [],
        }
    schedule_block()


# === 일상 / 소아 — 증상입력 + 예측/트리아지 + 케어로그 ===
else:
    who = st.radio("대상", ["소아","성인"], horizontal=True, key=f"who_{uid}") if mode=="일상" else "소아"
    # 프로필 로드
    prof = load_profile(uid) or {"age":5 if who=="소아" else 30, "sex":"남","height_cm":110.0 if who=="소아" else 170.0, "weight":20.0 if who=="소아" else 60.0}

    if who == "소아":
        # 증상 입력
        try:
            opts = get_symptom_options("기본")
        except Exception:
            opts = {"콧물":["없음","맑음","노랑"], "기침":["없음","가끔","자주"], "설사":["0","1~3","4~6","7+"], "눈꼽":["없음","맑음","노랑-농성"]}
        c1,c2,c3,c4,c5,c6 = st.columns(6)
        with c1: nasal = st.selectbox("콧물", opts.get("콧물",["없음","맑음","노랑"]), key=f"nasal_{uid}")
        with c2: cough = st.selectbox("기침", opts.get("기침",["없음","가끔","자주"]), key=f"cough_{uid}")
        with c3: diarrhea = st.selectbox("설사(횟수/일)", opts.get("설사",["0","1~3","4~6","7+"]), key=f"diarr_{uid}")
        with c4: vomit = st.selectbox("구토(횟수/일)", ["없음","1~2회","3~4회","4~6회","7회 이상"], key=f"vomit_{uid}")
        with c5: temp = st.number_input("체온(℃)", min_value=0.0, step=0.1, value=0.0, key=f"temp_{uid}")
        with c6: eye = st.selectbox("눈꼽", opts.get("눈꼽",["없음","맑음","노랑-농성"]), key=f"eye_{uid}")
        age_m = st.number_input("나이(개월)", min_value=0, step=1, value=int((prof.get("age",5))*12) if prof else 0, key=f"age_m_{uid}")
        weight = st.number_input("체중(kg)", min_value=0.0, step=0.1, value=float(prof.get("weight",20.0)), key=f"wt_{uid}")

        # 예측/트리아지
        try:
            from peds_rules import predict_from_symptoms, triage_advise
            symptoms = {"콧물":nasal,"기침":cough,"설사":diarrhea,"구토":vomit,"체온":temp,"눈꼽":eye}
            preds = predict_from_symptoms(symptoms, temp, age_m)
            st.markdown("#### 🤖 증상 기반 자동 추정")
            top = sorted(preds or [], key=lambda x: x.get('score',0), reverse=True)[:3]
            for p in top:
                label = p.get('label'); score = p.get('score',0); pct = f"{int(round(float(score)))}%" if score is not None else ""
                st.write(f"- **{label}** · 신뢰도 {pct}")
            triage = triage_advise(temp, age_m, diarrhea)
            st.info(triage)
        except Exception as e:
            st.caption(f"예측 모듈 오류: {e}")

    else:
        # 성인
        try:
            from adult_rules import predict_from_symptoms, triage_advise, get_adult_options
            opts = get_adult_options()
        except Exception:
            opts = {"콧물":["없음","맑음","노랑"], "기침":["없음","가끔","자주"], "설사":["0","1~3","4~6","7+"], "눈꼽":["없음","맑음","노랑-농성"]}
        c1,c2,c3,c4,c5,c6 = st.columns(6)
        with c1: nasal = st.selectbox("콧물", opts.get("콧물",["없음","맑음","노랑"]), key=f"nasal_ad_{uid}")
        with c2: cough = st.selectbox("기침", opts.get("기침",["없음","가끔","자주"]), key=f"cough_ad_{uid}")
        with c3: diarrhea = st.selectbox("설사(횟수/일)", opts.get("설사",["0","1~3","4~6","7+"]), key=f"diarr_ad_{uid}")
        with c4: vomit = st.selectbox("구토(횟수/일)", ["없음","1~3회","4~6회","7회 이상"], key=f"vomit_ad_{uid}")
        with c5: temp = st.number_input("체온(℃)", min_value=0.0, step=0.1, value=0.0, key=f"temp_ad_{uid}")
        with c6: eye = st.selectbox("눈꼽", opts.get("눈꼽",["없음","맑음","노랑-농성"]), key=f"eye_ad_{uid}")
        comorb = st.multiselect("주의 대상", ["임신 가능성","간질환 병력","신질환 병력","위장관 궤양/출혈력","항응고제 복용","고령(65+)"], key=f"comorb_{uid}")

        try:
            from adult_rules import predict_from_symptoms, triage_advise
            symptoms = {"콧물":nasal,"기침":cough,"설사":diarrhea,"구토":vomit,"체온":temp,"눈꼽":eye,"병력":",".join(comorb)}
            preds = predict_from_symptoms(symptoms, temp, comorb)
            st.markdown("#### 🤖 증상 기반 자동 추정")
            top = sorted(preds or [], key=lambda x: x.get('score',0), reverse=True)[:3]
            for p in top:
                label = p.get('label'); score = p.get('score',0); pct = f"{int(round(float(score)))}%" if score is not None else ""
                st.write(f"- **{label}** · 신뢰도 {pct}")
            triage = triage_advise(temp, comorb)
            st.info(triage)
        except Exception as e:
            st.caption(f"예측 모듈 오류: {e}")

    # 케어로그/가드/응급배너
    if place_carelog_under_special:
        st.divider(); st.subheader("케어 · 해열제")
        care_lines, care_entries = render_carelog(uid, nick)
        render_antipy_guard(prof, {}, care_entries)
        render_emergency_banners({}, care_entries)
    else:
        care_lines, care_entries = [], []

    # 결과/보고서
    diet_lines = dense_diet_guides({}, heme_flag=(who=="소아"))
    if st.button("🔎 해석하기", key=f"analyze_daily_{uid}"):
        st.session_state["analyzed"] = True
        st.session_state["analysis_ctx"] = {
            "mode":"일상" if who!="소아" else "소아","who":who,
            "labs": {}, "diet_lines": diet_lines,
            "care_lines": care_lines, "triage_high": analyze_symptoms(care_entries)[0] if care_entries else []
        }
# ---------------- 결과/보고서 ----------------

def export_report(ctx: dict):
    footer = (
        "\n\n---\n본 수치는 참고용이며, 해석 결과는 개발자와 무관합니다.\n"
        "약 변경·복용 중단 등은 반드시 **주치의와 상담**하십시오.\n"
    )
    title = f"# BloodMap 결과 ({ctx.get('mode','')})\n\n"
    body = []
    if ctx.get("mode") == "암":
        body += [f"- 카테고리: {ctx.get('group')}", f"- 진단: {ctx.get('dx_label') or ctx.get('dx')}"]
    if ctx.get("triage_high"): body.append("- 🆘 응급도: " + " · ".join(ctx["triage_high"]))
    if ctx.get("care_lines"): body.append("\n## 🗒️ 최근 24h 케어로그\n" + "\n".join(ctx["care_lines"]))
    if ctx.get("diet_lines"): body.append("\n## 🍽️ 식이가이드\n" + "\n".join(f"- {x}" for x in ctx["diet_lines"]))
    if ctx.get("special_tests"): body.append("\n## 🧬 특수검사\n" + "\n".join(f"- {x}" for x in ctx["special_tests"]))
    if ctx.get("labs"):
        labs = ctx["labs"].copy()
        if "CR" in labs and "Cr" not in labs: labs["Cr"] = labs["CR"]
        if "eGFR" in labs: body.append(f"- eGFR: {labs['eGFR']} mL/min/1.73㎡")
        labs_t = "; ".join(f"{k}:{v}" for k,v in labs.items() if v is not None and k!="eGFR")
        if labs_t: body.append(f"- 주요 수치: {labs_t}")
    md = title + "\n".join(body) + footer
    txt = md.replace("# ","").replace("## ","")
    return md, txt

if results_only_after_analyze(st):
    ctx = st.session_state.get("analysis_ctx", {})
    if ctx.get("care_lines"):
        st.subheader("🗒️ 최근 24h 케어로그"); [st.write(L) for L in ctx["care_lines"]]
    if ctx.get("triage_high"):
        st.error("🚨 응급도: " + " · ".join(ctx["triage_high"]))
    st.subheader("🍽️ 식이가이드"); [st.write("- "+L) for L in (ctx.get("diet_lines") or [])]
    if ctx.get("labs"):
        st.subheader("🧪 eGFR"); st.write(ctx["labs"].get("eGFR"))
    st.subheader("📝 보고서 저장")
    md, txt = export_report(ctx)
    st.download_button("⬇️ Markdown", data=md, file_name="BloodMap_Report.md", key=f"dl_md_{uid}")
    st.download_button("⬇️ TXT", data=txt, file_name="BloodMap_Report.txt", key=f"dl_txt_{uid}")
    try:
        pdf_bytes = export_md_to_pdf(md); st.download_button("⬇️ PDF", data=pdf_bytes, file_name="BloodMap_Report.pdf", mime="application/pdf", key=f"dl_pdf_{uid}")
    except Exception as e:
        st.caption(f"PDF 변환 오류: {e}")
    st.stop()
