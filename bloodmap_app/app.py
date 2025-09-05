# -*- coding: utf-8 -*-
import streamlit as st

# --- Safe fallback for inject_css (in case utils import was pruned during deploy) ---
try:
    _ = inject_css  # type: ignore # noqa
except Exception:
    def inject_css():
        try:
            with open("bloodmap_app/style.css", "r", encoding="utf-8") as _f:
                st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)
        except Exception:
            pass

from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.graphics.barcode import qr as rl_qr
from reportlab.lib.units import mm
from datetime import datetime
try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo=None
# Safe import (handles stale/partial deployments)
try:
    from .utils import inject_css, section, subtitle, num_input, pin_valid, warn_banner, load_profiles, save_profile, recent_profiles
except Exception:  # pragma: no cover
    import streamlit as st
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.graphics.barcode import qr as rl_qr
from reportlab.lib.units import mm
from datetime import datetime
try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo=None
    def inject_css():
        try:
            with open("bloodmap_app/style.css", "r", encoding="utf-8") as f:
                st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
        except Exception:
            pass
    def section(title:str): st.markdown(f"## {title}")
    def subtitle(text:str): st.markdown(f"<div class='small'>{text}</div>", unsafe_allow_html=True)
    def num_input(label:str, key:str, min_value=None, max_value=None, step=None, format=None, placeholder=None):
        return st.number_input(label, key=key, min_value=min_value, max_value=max_value, step=step, format=format if format else None, help=placeholder)
    def pin_valid(pin_text:str)->bool: return str(pin_text).isdigit() and len(str(pin_text)) == 4
    def warn_banner(text:str): st.markdown(f"<span class='badge'>⚠️ {text}</span>", unsafe_allow_html=True)

from .drug_data import CANCER_GROUPS, CHEMO_BY_GROUP_OR_DX, ANTIBIOTICS_KR

APP_TITLE = "피수치 해석기"
APP_VERSION = "v3.8.2"

def _header_share():
    with st.expander("🔗 공유하기 / Share"):
        st.write("• 카카오/메신저 공유 링크, 카페/블로그, 앱 주소 QR은 다음 빌드에서 연결됩니다.")
        st.code("https://bloodmap.example", language="text")


def _patient_bar():
    st.markdown("""
    <div class='card'>
      <b>결과 상단 표기</b> — 별명·PIN 4자리 (중복 방지)
    </div>
    """, unsafe_allow_html=True)

    colA, colB, colC = st.columns([2,1,1])
    nickname = colA.text_input("별명", key="nickname", placeholder="예: 민수맘 / Hoya")
    pin = colB.text_input("PIN 4자리", key="pin", max_chars=4, placeholder="0000")
    if pin and not pin_valid(pin):
        st.error("PIN은 숫자 4자리만 허용됩니다.")

    storage_key = f"{nickname}#{pin}" if (nickname and pin_valid(pin)) else None
    if storage_key:
        colC.button("저장", on_click=lambda: save_profile(storage_key))
        st.info(f"저장 키: **{storage_key}**")
        # 최근 사용 키
        rec = recent_profiles()
        if rec:
            st.caption("최근 사용: " + " · ".join(rec))

    # 접근성 토글
    col1, col2, col3 = st.columns([1,1,1])
    col1.toggle("큰 글자", key="acc_lg")
    col2.toggle("고대비", key="acc_hc")
    if col3.button("초기화"):
        _reset_all()



# --- Safe fallbacks for helper functions (in case of partial deploy) ---
try:
    _ = _timestamp_badge  # noqa: F821
except Exception:
    def _timestamp_badge():
        from datetime import datetime
        try:
            from zoneinfo import ZoneInfo
            ts = datetime.now(ZoneInfo("Asia/Seoul"))
        except Exception:
            ts = datetime.now()
        st.caption(f"빌드 {APP_VERSION} · {ts.strftime('%Y-%m-%d %H:%M')} KST")

try:
    _ = _apply_accessibility  # noqa: F821
except Exception:
    def _apply_accessibility():
        # No-op if accessibility helpers aren't loaded
        pass

def _mode_and_cancer_picker():
    st.markdown("### 1️⃣ 소아가이드 / 암 선택")
    mode = st.radio("모드 선택", options=["소아 가이드", "암 종류"], horizontal=True, key="mode_pick")
    picked_group = None
    picked_dx = None

    if mode == "암 종류":
        group = st.radio("암 그룹", options=list(CANCER_GROUPS.keys()), horizontal=True, key="group_pick")
        picked_group = group
        dx_list = CANCER_GROUPS[group]
        dx = st.selectbox("진단(진단명으로 선택)", options=dx_list, key="dx_pick")
        picked_dx = dx
        st.caption("암 그룹/진단 선택 후 바로 아래에서 항암제·항생제를 추가하세요.")
    else:
        peds_cat = st.radio("소아 카테고리", ["일상 가이드", "호흡기", "감염 질환"], horizontal=True, key="peds_cat")

        if peds_cat == "감염 질환":
            with st.expander("감염 질환 토글"):
                c1, c2, c3, c4, c5, c6, c7, c8 = st.columns(8)
                rsv  = c1.checkbox("RSV", key="p_rsv")
                adv  = c2.checkbox("Adenovirus", key="p_adv")
                rota = c3.checkbox("Rotavirus", key="p_rota")
                flu  = c4.checkbox("Influenza", key="p_flu")
                para = c5.checkbox("Parainfluenza", key="p_para")
                hfm  = c6.checkbox("수족구", key="p_hfm")
                noro = c7.checkbox("노로/아스트로", key="p_noro")
                myco = c8.checkbox("마이코플라스마", key="p_myco")

            # Common inputs
            st.markdown("**공통 지표 (선택)**")
            c9, c10, c11, c12 = st.columns(4)
            dur = c9.number_input("증상 기간(일)", key="sx_days", min_value=0, max_value=30, step=1)
            dysp = c10.selectbox("호흡곤란 정도", ["없음", "조금", "보통", "많이", "심함"], key="sx_dysp")
            cyan = c11.checkbox("청색증(입술/손톱 푸르스름) 있음", key="sx_cyan")
            ox_avail = c12.checkbox("펄스옥시미터 있음", key="sx_ox_avail")
            spo2 = None
            if ox_avail:
                spo2 = st.number_input("SpO₂(%)", key="sx_spo2", min_value=50.0, max_value=100.0, step=0.1, format="%.1f")
            st.caption("SpO₂는 가정용 기기가 있을 때만 입력하세요. 없으면 비워두면 됩니다.")

            # RSV

            if rsv:
                st.markdown("**RSV — 증상 입력**")
                c1, c2 = st.columns(2)
                rsv_temp = c1.number_input("발열 — 체온(°C)", key="rsv_temp", min_value=30.0, max_value=42.0, step=0.1, format="%.1f")
                rsv_rhino = c2.selectbox("콧물 색", ["없음", "흰색", "누런색", "피섞임"], key="rsv_rhino")
                fever = _fever_grade_from_temp(rsv_temp)
                rh_map = {"없음":0, "흰색":1, "누런색":2, "피섞임":3}
                _peds_interpret_and_show(fever=fever, extras=[rh_map[rsv_rhino]], duration_days=dur, spo2=spo2, dyspnea=dysp, cyanosis=cyan)

            # Adenovirus
            if adv:
                st.markdown("**Adenovirus — 증상 입력**")
                c1, c2 = st.columns(2)
                adv_temp = c1.number_input("발열 — 체온(°C)", key="adv_temp", min_value=30.0, max_value=42.0, step=0.1, format="%.1f")
                adv_eye = c2.selectbox("눈꼽 분비물", ["없음", "적음", "보통", "심함"], key="adv_eye")
                fever = _fever_grade_from_temp(adv_temp)
                eye_map = {"없음":0, "적음":1, "보통":2, "심함":3}
                _peds_interpret_and_show(fever=fever, extras=[eye_map[adv_eye]], duration_days=dur, spo2=spo2, dyspnea=dysp, cyanosis=cyan)

            # Influenza
            if flu:
                st.markdown("**인플루엔자 — 증상 입력**")
                c1, c2 = st.columns(2)
                flu_temp = c1.number_input("발열 — 체온(°C)", key="flu_temp", min_value=30.0, max_value=42.0, step=0.1, format="%.1f")
                flu_cough = c2.selectbox("기침", ["없음", "보통", "심함"], key="flu_cough")
                fever = _fever_grade_from_temp(flu_temp)
                _peds_interpret_and_show(fever=fever, cough=flu_cough, duration_days=dur, spo2=spo2, dyspnea=dysp, cyanosis=cyan)

            # Parainfluenza
            if para:
                st.markdown("**Parainfluenza — 증상 입력**")
                c1, c2 = st.columns(2)
                para_temp = c1.number_input("발열 — 체온(°C)", key="para_temp", min_value=30.0, max_value=42.0, step=0.1, format="%.1f")
                para_cough = c2.selectbox("기침", ["없음", "조금", "보통", "많이", "심함"], key="para_cough")
                fever = _fever_grade_from_temp(para_temp)
                _peds_interpret_and_show(fever=fever, cough=para_cough, duration_days=dur, spo2=spo2, dyspnea=dysp, cyanosis=cyan)

            # Rotavirus
            if rota:
                st.markdown("**Rotavirus — 증상 입력**")
                c1, c2, c3 = st.columns(3)
                rota_stool = c1.number_input("설사 횟수(회/일)", key="rota_stool", min_value=0, max_value=30, step=1)
                rota_temp = c2.number_input("발열 — 체온(°C)", key="rota_temp", min_value=30.0, max_value=42.0, step=0.1, format="%.1f")
                rota_dysuria = c3.selectbox("배뇨통", ["없음", "조금", "보통", "심함"], key="rota_dysuria")
                fever = _fever_grade_from_temp(rota_temp)
                stool_sev = 0 if rota_stool == 0 else (1 if rota_stool <= 2 else (2 if rota_stool <= 5 else 3))
                dys_map = {"없음":0, "조금":1, "보통":2, "심함":3}
                diarrhea_level = "없음" if stool_sev==0 else ("조금" if stool_sev==1 else ("보통" if stool_sev==2 else "많이"))
                _peds_interpret_and_show(fever=fever, diarrhea=diarrhea_level, extras=[dys_map[rota_dysuria]], duration_days=dur, spo2=spo2, dyspnea=dysp, cyanosis=cyan)

            # 수족구
            if hfm:
                st.markdown("**수족구 — 증상 입력**")
                hfm_temp = st.number_input("발열 — 체온(°C)", key="hfm_temp", min_value=30.0, max_value=42.0, step=0.1, format="%.1f")
                fever = _fever_grade_from_temp(hfm_temp)
                _peds_interpret_and_show(fever=fever, duration_days=dur, spo2=spo2, dyspnea=dysp, cyanosis=cyan)

            # 노로/아스트로
            if noro:
                st.markdown("**노로/아스트로 — 증상 입력**")
                c1, c2, c3 = st.columns(3)
                noro_vomit = c1.selectbox("구토", ["없음", "조금", "보통", "심함"], key="noro_vomit")
                noro_stool = c2.number_input("설사 횟수(회/일)", key="noro_stool", min_value=0, max_value=30, step=1)
                noro_temp = c3.number_input("발열 — 체온(°C)", key="noro_temp", min_value=30.0, max_value=42.0, step=0.1, format="%.1f")
                fever = _fever_grade_from_temp(noro_temp)
                stool_sev = 0 if noro_stool == 0 else (1 if noro_stool <= 2 else (2 if noro_stool <= 5 else 3))
                _peds_interpret_and_show(fever=fever, diarrhea=["없음","조금","보통","많이"][stool_sev], extras=[_peds_severity_score(noro_vomit)], duration_days=dur, spo2=spo2, dyspnea=dysp, cyanosis=cyan)

            # 마이코플라스마
            if myco:
                st.markdown("**마이코플라스마 — 증상 입력**")
                c1, c2 = st.columns(2)
                myco_cough = c1.selectbox("기침", ["안함", "조금", "보통", "심함"], key="myco_cough")
                myco_temp  = c2.number_input("발열 — 체온(°C)", key="myco_temp", min_value=30.0, max_value=42.0, step=0.1, format="%.1f")
                fever = _fever_grade_from_temp(myco_temp)
                _peds_interpret_and_show(fever=fever, cough=myco_cough, duration_days=dur, spo2=spo2, dyspnea=dysp, cyanosis=cyan)

        elif peds_cat == "호흡기":
            st.markdown("**호흡기 예시**")
            c1, c2, c3, c4 = st.columns(4)
            cough   = c1.selectbox("기침", ["안함", "조금", "보통", "심함"], key="sx_cough")
            fever_t = c2.number_input("체온(°C)", key="sx_fever_r_t", min_value=30.0, max_value=42.0, step=0.1, format="%.1f")
            dysp    = c3.selectbox("호흡곤란 정도", ["없음", "조금", "보통", "많이", "심함"], key="sx_dysp_r")
            cyan    = c4.checkbox("청색증 있음", key="sx_cyan_r")
            colx1, colx2 = st.columns(2)
            ox_avail_r = colx1.checkbox("펄스옥시미터 있음", key="sx_ox_avail_r")
            spo2 = None
            if ox_avail_r:
                spo2 = colx2.number_input("SpO₂(%)", key="sx_spo2_r", min_value=50.0, max_value=100.0, step=0.1, format="%.1f")
            fever   = _fever_grade_from_temp(fever_t)
            _peds_interpret_and_show(pain="없음", fever=fever, diarrhea="없음", cough=cough, spo2=spo2, dyspnea=dysp, cyanosis=cyan)
            st.caption("기침/호흡곤란이 심하거나 밤에 악화 시, 또는 고열 지속 시 진료 권장.")

        else:  # 일상 가이드
            st.markdown("**일상 가이드 — 증상 체크**")
            # appetite yes/no + level
            has_app = st.radio("식욕", ["없음", "있음"], horizontal=True, key="app_yesno")
            if has_app == "있음":
                appetite = st.selectbox("식욕 정도", ["조금", "보통", "많음"], key="app_level")
            else:
                appetite = "없음"
            c1, c2, c3, c4 = st.columns(4)
            fever_t  = c1.number_input("발열 — 체온(°C)", key="sx_fever_d_t", min_value=30.0, max_value=42.0, step=0.1, format="%.1f")
            vomit    = c2.selectbox("구토", ["없음", "조금", "보통", "심함"], key="sx_vomit")
            diarrhea = c3.selectbox("설사", ["없음", "조금", "보통", "심함"], key="sx_diarrhea_d")
            urine    = c4.number_input("소변 횟수(회/일)", key="sx_urine_d", min_value=0, max_value=30, step=1)
            # optional: 체중 변화
            weight_delta = st.number_input("체중 변화(kg, 7일)", key="sx_wdelta", min_value=-10.0, max_value=10.0, step=0.1, format="%.1f")
            fever    = _fever_grade_from_temp(fever_t)
            app_map = {"없음":2, "조금":1, "보통":0, "많음":0}
            extra = [app_map.get(appetite,0), _peds_severity_score(vomit)]
            # 탈수 시사: 소변 3회 미만이면 가중
            if urine < 3: extra.append(2)
            # 체중 감소 2% 넘으면 가중(추정치로 1kg 이상 감소 시 경고)
            if weight_delta is not None and weight_delta < -1.0: extra.append(2)
            _peds_interpret_and_show(pain="없음", fever=fever, diarrhea=diarrhea, cough="안함", extras=extra)

    return picked_group, picked_dx









def _labs_section():
    ped_mode = st.session_state.get("mode_pick") == "소아 가이드"

    def _labs_body():
        section("3️⃣ 피수치 입력")
        c1, c2, c3, c4 = st.columns(4)
        wbc = num_input("WBC (×10³/µL)", "wbc", min_value=0.0, step=0.1, placeholder="예: 1.2")
        hb  = num_input("Hb (g/dL)", "hb", min_value=0.0, step=0.1, placeholder="예: 9.1")
        plt = num_input("혈소판 PLT (×10³/µL)", "plt", min_value=0.0, step=1.0, placeholder="예: 42")
        anc = num_input("ANC 호중구 (cells/µL)", "anc", min_value=0.0, step=10.0, placeholder="예: 320")

        c5, c6, c7, c8 = st.columns(4)
        ca  = num_input("Ca 칼슘 (mg/dL)", "ca", min_value=0.0, step=0.1, placeholder="예: 8.3")
        na  = num_input("Na 소디움 (mEq/L)", "na", min_value=0.0, step=0.5, placeholder="예: 134")
        k   = num_input("K 포타슘 (mEq/L)", "k", min_value=0.0, step=0.1, placeholder="예: 3.3")
        alb = num_input("Albumin 알부민 (g/dL)", "alb", min_value=0.0, step=0.1, placeholder="예: 2.4")

        c9, c10, c11, c12 = st.columns(4)
        glu = num_input("Glucose 혈당 (mg/dL)", "glu", min_value=0.0, step=1.0, placeholder="예: 105")
        tp  = num_input("Total Protein 총단백 (g/dL)", "tp", min_value=0.0, step=0.1, placeholder="예: 4.4")
        ast = num_input("AST 간수치 (U/L)", "ast", min_value=0.0, step=1.0, placeholder="예: 103")
        alt = num_input("ALT 간세포수치 (U/L)", "alt", min_value=0.0, step=1.0, placeholder="예: 84")

        c13, c14, c15, c16 = st.columns(4)
        crp = num_input("CRP 염증수치 (mg/dL)", "crp", min_value=0.0, step=0.01, placeholder="예: 0.13")
        cr  = num_input("Cr 크레아티닌/신장 (mg/dL)", "cr", min_value=0.0, step=0.01, placeholder="예: 0.84")
        ua  = num_input("UA 요산 (mg/dL)", "ua", min_value=0.0, step=0.1, placeholder="예: 5.6")
        tb  = num_input("TB 총빌리루빈 (mg/dL)", "tb", min_value=0.0, step=0.1, placeholder="예: 0.9")

        with st.expander("🧪 특수검사 (필요 시 열기)"):
            st.write("자주 시행하지 않는 항목은 토글로 열어서 입력합니다.")
            t1 = st.checkbox("응고패널 (PT, aPTT, Fibrinogen, D-dimer)", key="toggle_coag")
            if t1:
                c1a, c2a = st.columns(2)
                num_input("PT (sec)", "pt", min_value=0.0, step=0.1)
                num_input("aPTT (sec)", "aptt", min_value=0.0, step=0.1)
                num_input("Fibrinogen (mg/dL)", "fbg", min_value=0.0, step=1.0)
                num_input("D-dimer (µg/mL FEU)", "dd", min_value=0.0, step=0.01)

            t_lipid = st.checkbox("지질검사 패널 (TC/TG/LDL/HDL)", key="toggle_lipid")
            if t_lipid:
                c1b, c2b, c3b, c4b = st.columns(4)
                num_input("총콜레스테롤 TC (mg/dL)", "tc", min_value=0.0, step=1.0)
                num_input("중성지방 TG (mg/dL)", "tg", min_value=0.0, step=1.0)
                num_input("LDL-C (mg/dL)", "ldl", min_value=0.0, step=1.0)
                num_input("HDL-C (mg/dL)", "hdl", min_value=0.0, step=1.0)

            t_hf = st.checkbox("심부전 표지자 (BNP/NT-proBNP)", key="toggle_hf")
            if t_hf:
                c1c, c2c = st.columns(2)
                num_input("BNP (pg/mL)", "bnp", min_value=0.0, step=1.0)
                num_input("NT-proBNP (pg/mL)", "ntprobnp", min_value=0.0, step=1.0)

            t_ext = st.checkbox("염증/기타 (ESR/PCT/Ferritin/LDH/CK, 소변량)", key="toggle_ext")
            if t_ext:
                c1d, c2d, c3d, c4d, c5d = st.columns(5)
                num_input("ESR (mm/hr)", "esr", min_value=0.0, step=1.0)
                num_input("Procalcitonin PCT (ng/mL)", "pct", min_value=0.0, step=0.01)
                num_input("Ferritin (ng/mL)", "ferritin", min_value=0.0, step=1.0)
                num_input("LDH (U/L)", "ldh", min_value=0.0, step=1.0)
                num_input("CK (U/L)", "ck", min_value=0.0, step=1.0)
                num_input("소변량 (mL/kg/hr)", "uo", min_value=0.0, step=0.1)

        # ANC 경고 배너
        if anc and anc < 500:
            warn_banner("ANC 500 미만 — 생채소·생과일 금지, 모든 음식은 충분히 가열하세요. 조리 후 2시간 지난 음식은 먹지 않기.")

        return dict(wbc=wbc, hb=hb, plt=plt, anc=anc, ca=ca, na=na, k=k, alb=alb, glu=glu, tp=tp, ast=ast, alt=alt, crp=crp, cr=cr, ua=ua, tb=tb)

    if ped_mode:
        with st.expander("3️⃣ 피수치 입력 (소아 — 필요 시 열기)"):
            return _labs_body()
    else:
        return _labs_body()


    # 소아 모드면 전체를 토글(Expander)로 감싸기
    if ped_mode:
        with st.expander("3️⃣ 피수치 입력 (소아 — 필요 시 열기)"):
            return _labs_body()
    else:
        section("3️⃣ 피수치 입력")
        return _labs_body()


def _therapy_section(picked_group, picked_dx):
    section("2️⃣ 약물 선택 (한글 표기)")
    # 항암제
    default_drugs = []
    if picked_dx and picked_dx in CHEMO_BY_GROUP_OR_DX:
        default_drugs = CHEMO_BY_GROUP_OR_DX[picked_dx]
    elif picked_group and picked_group in CHEMO_BY_GROUP_OR_DX:
        default_drugs = CHEMO_BY_GROUP_OR_DX[picked_group]

    chemo = st.multiselect("항암제", options=sorted(set(sum([list(v) for v in CHEMO_BY_GROUP_OR_DX.values()], []))), default=default_drugs, key="chemo")
    abx = st.multiselect("항생제", options=ANTIBIOTICS_KR, key="abx")
    diuretic = st.checkbox("이뇨제 복용", key="diuretic")

    subtitle("약물 요약은 결과 영역과 .md 보고서에 표시됩니다.")
    return dict(chemo=chemo, abx=abx, diuretic=diuretic)

def _result_section(labs, picked_group, picked_dx):
    section("4️⃣ 결과 요약")
    lines = []
    nick = st.session_state.get("nickname") or "(무명)"
    pin = st.session_state.get("pin") or "----"
    lines.append(f"• 사용자: {nick} #{pin}")
    if picked_group: lines.append(f"• 암 그룹: {picked_group}")
    if picked_dx: lines.append(f"• 진단: {picked_dx}")
    # 피수치 — 입력한 항목만
    entered = {k:v for k,v in labs.items() if v not in (None, 0)}
    if entered:
        lines.append("• 입력 수치: " + ", ".join([f"{k.upper()}={v}" for k,v in entered.items()]))
    # 간단 가이드
    if labs.get('anc', 0) != 0 and labs['anc'] < 500:
        lines.append("• 가이드: ANC<500 → 생채소 금지, 가열식 권장, 남은 음식 2시간 후 섭취 금지.")
    if labs.get('hb', 0) != 0 and labs['hb'] < 8.0:
        lines.append("• 가이드: Hb 낮음 → 어지러움/피로 주의, 필요 시 수혈 여부 의료진과 상의.")
    st.write("\n".join(lines))

    report_md = f"""# {APP_TITLE} {APP_VERSION}
- 사용자: {nick} #{pin}
- 암 그룹/진단: {picked_group or '-'} / {picked_dx or '-'}
- 수치: {entered}
> 본 자료는 보호자의 이해를 돕기 위한 참고용이며, 모든 의학적 판단은 담당 의료진의 진료 지침을 따르십시오.
"""
    st.download_button("📥 보고서(.md) 다운로드", report_md, file_name="bloodmap_report.md")

    # TXT 다운로드
    report_txt = (
        f"피수치 해석기 {APP_VERSION}\n"
        f"사용자: {nick} #{pin}\n"
        f"암 그룹/진단: {picked_group or '-'} / {picked_dx or '-'}\n"
        f"수치: {entered}\n"
        "본 자료는 보호자의 이해를 돕기 위한 참고용이며, 모든 의학적 판단은 담당 의료진의 진료 지침을 따르십시오.\n"
    )
    st.download_button("📄 TXT 다운로드", report_txt, file_name="bloodmap_report.txt")

    # PDF 다운로드 (QR 포함)
    url_hint = "https://bloodmap.example"
    pdf_bytes = _make_pdf(nick, pin, picked_group, picked_dx, entered, url_hint)
    st.download_button("🧾 PDF 다운로드", data=pdf_bytes, file_name="bloodmap_report.pdf", mime="application/pdf")



def _diet_guide_section(labs):
    section("5️⃣ 식이 가이드 (자동)")
    tips = []

    # 입력값 기반 간단 규칙 (참고용)
    if labs.get('alb') and labs['alb'] < 3.5:
        tips.append(("알부민 낮음", ["달걀", "연두부", "흰살 생선", "닭가슴살", "귀리죽"]))
    if labs.get('k') and labs['k'] < 3.5:
        tips.append(("칼륨 낮음", ["바나나", "감자", "호박죽", "고구마", "오렌지"]))
    if labs.get('hb') and labs['hb'] < 10.0:
        tips.append(("Hb 낮음", ["소고기", "시금치", "두부", "달걀 노른자", "렌틸콩"]))
    if labs.get('na') and labs['na'] < 135:
        tips.append(("나트륨 낮음", ["전해질 음료", "미역국", "바나나", "오트밀죽", "삶은 감자"]))
    if labs.get('ca') and labs['ca'] < 8.5:
        tips.append(("칼슘 낮음", ["연어통조림", "두부", "케일", "브로콜리", "참깨 제외"]))

    if not tips:
        st.info("입력값 기준으로 필요한 식이 가이드가 없습니다. (정상 범위로 추정)")
        return

    for title, foods in tips:
        st.markdown("**• " + title + "** → 추천 식품 5개: " + ", ".join(foods))

    st.caption("영양제(철분제 등)는 추천에서 제외합니다. 항암 치료 중 철분제는 권장되지 않습니다. "
               "철분제와 비타민C 병용 시 흡수 증가 가능성이 있어 반드시 주치의와 상의하세요.")

def _peds_severity_score(value:str)->int:
    table = {
        "없음": 0, "안함": 0, "미열": 1, "조금": 1,
        "보통": 2, "열": 2,
        "많이": 3, "심함": 3, "고열(≥38.5)": 3
    }
    return table.get(value, 0)

def _peds_interpret_and_show(**kwargs):
    # kwargs may include: pain, fever, diarrhea, cough, extras(list[int]), duration_days(int), spo2(float),
    # dyspnea(str), cyanosis(bool)
    pain = _peds_severity_score(kwargs.get("pain"))
    fever = _peds_severity_score(kwargs.get("fever"))
    diarrhea = _peds_severity_score(kwargs.get("diarrhea"))
    cough = _peds_severity_score(kwargs.get("cough"))
    dyspnea = _peds_severity_score(kwargs.get("dyspnea"))
    cyanosis = bool(kwargs.get("cyanosis", False))
    extras = kwargs.get("extras", [])
    duration_days = kwargs.get("duration_days")
    spo2 = kwargs.get("spo2")

    base = max([pain, fever, diarrhea, cough, dyspnea] + (extras or [0]))
    # duration effect
    risk = _risk_with_duration(base, duration_days)

    # Cyanosis is severe by definition
    if cyanosis:
        risk = 3

    # SpO2 thresholds only if measured
    if spo2 is not None:
        try:
            s = float(spo2)
            if s < 92:
                risk = 3
            elif s < 95:
                risk = max(risk, 2)
        except Exception:
            pass

    if risk >= 3:
        st.error("증상이 **심합니다**. 꼭 병원에서 **주치의 상담 또는 응급실 내원**을 권장합니다.")
    elif risk == 2:
        st.warning("증상이 **중등도**입니다. 수분 보충, 해열제 간격 준수 등 대증치료를 하면서 **악화 시 내원**하세요.")
    else:
        st.info("증상이 **경증**으로 추정됩니다. 가정 내 대증치료와 관찰을 권장합니다.")

    # kwargs: pain, fever, diarrhea, cough
    pain = _peds_severity_score(kwargs.get("pain"))
    fever = _peds_severity_score(kwargs.get("fever"))
    diarrhea = _peds_severity_score(kwargs.get("diarrhea"))
    cough = _peds_severity_score(kwargs.get("cough"))
    risk = max(pain, fever, diarrhea, cough)
    if fever >= 3 or diarrhea >= 3 or pain >= 3 or cough >= 3:
        st.error("증상이 **심합니다**. 꼭 병원에서 **주치의 상담 또는 응급실 내원**을 권장합니다.")
    elif risk == 2:
        st.warning("증상이 **중등도**입니다. 수분 보충, 해열제 간격 준수 등 대증치료를 하면서 **악화 시 내원**하세요.")
    else:
        st.info("증상이 **경증**으로 추정됩니다. 가정 내 대증치료와 관찰을 권장합니다.")

def _fever_grade_from_temp(temp_c: float|None) -> str:
    if not temp_c:
        return "없음"
    try:
        t = float(temp_c)
    except Exception:
        return "없음"
    if t < 37.5: return "없음"
    if 37.5 <= t < 38.0: return "미열"
    if 38.0 <= t < 38.5: return "열"
    return "고열(≥38.5)"

def main():
    st.set_page_config(page_title=f"{APP_TITLE} {APP_VERSION}", layout="centered", initial_sidebar_state="collapsed")
    inject_css()

    st.title(APP_TITLE)
    st.caption(f"빌드 {APP_VERSION} — 모바일 최적화 UI")

    _header_share()
    _timestamp_badge()
    _apply_accessibility()
    _patient_bar()
    st.markdown("""<div class='fixed-action'><button class='btn'>🔍 해석하기 버튼은 아래에 있습니다</button></div>""", unsafe_allow_html=True)
    picked_group, picked_dx = _mode_and_cancer_picker()

    # 모드 확인: 암 종류일 때만 약물 섹션 바로 아래 표시
    if st.session_state.get("mode_pick") == "암 종류":
        _therapy_section(picked_group, picked_dx)

    labs = _labs_section()
    go = st.button('🔍 결과 보기', type='primary')
    if go:
        _result_section(labs, picked_group, picked_dx)
        _diet_guide_section(labs)

    st.markdown("""<div class='footer-note'>
    본 자료는 보호자의 이해를 돕기 위한 참고용 정보입니다. 수치 기반 판단과 약물 변경은 반드시 주치의와 상담하십시오.
    </div>""", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
