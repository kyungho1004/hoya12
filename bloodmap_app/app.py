# -*- coding: utf-8 -*-
import streamlit as st
# Safe import (handles stale/partial deployments)
try:
    from .utils import inject_css, section, subtitle, num_input, pin_valid, warn_banner
except Exception:  # pragma: no cover
    import streamlit as st
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
      <b>결과 상단 표기</b> — 별명 + PIN 4자리 (중복 방지)    </div>
    """, unsafe_allow_html=True)
    c1, c2 = st.columns([2,1])
    nickname = c1.text_input("별명", key="nickname", placeholder="예: 민수맘 / Hoya")
    pin = c2.text_input("PIN 4자리", key="pin", max_chars=4, placeholder="0000")
    if pin and not pin_valid(pin):
        st.error("PIN은 숫자 4자리만 허용됩니다.")
    storage_key = f"{nickname}#{pin}" if (nickname and pin_valid(pin)) else None
    if storage_key:
        st.info(f"저장 키: **{storage_key}**")

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
        st.caption("암 그룹/진단 선택 후 아래에서 항암제·항생제를 추가할 수 있습니다.")
    else:
        st.selectbox("소아 질환 카테고리", ["일상 가이드", "호흡기", "감염질환", "혈액암(소아)", "고형암(소아)", "육종(소아)", "희귀암(소아)"], key="peds_cat")
        st.caption("소아 모드에서는 보호자용 가이드를 강조합니다.")

    return picked_group, picked_dx

def _labs_section():
    section("2️⃣ 피수치 입력")
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

    with st.expander("🧪 특수검사 (필요 시 열기)"):
        st.write("자주 시행하지 않는 항목은 토글로 열어서 입력합니다.")
        t1 = st.checkbox("응고패널 (PT, aPTT, Fibrinogen, D-dimer)", key="toggle_coag")
        if t1:
            c1, c2 = st.columns(2)
            num_input("PT (sec)", "pt", min_value=0.0, step=0.1)
            num_input("aPTT (sec)", "aptt", min_value=0.0, step=0.1)
            num_input("Fibrinogen (mg/dL)", "fbg", min_value=0.0, step=1.0)
            num_input("D-dimer (µg/mL FEU)", "dd", min_value=0.0, step=0.01)
        t2 = st.checkbox("보체 (C3, C4, CH50)", key="toggle_complement")
        if t2:
            c1, c2, c3 = st.columns(3)
            num_input("C3 (mg/dL)", "c3", min_value=0.0, step=1.0)
            num_input("C4 (mg/dL)", "c4", min_value=0.0, step=1.0)
            num_input("CH50 (U/mL)", "ch50", min_value=0.0, step=1.0)
        t3 = st.checkbox("요검사 (단백뇨/잠혈/요당)", key="toggle_ua")
        if t3:
            st.selectbox("단백뇨(Proteinuria)", ["없음", "미량", "+", "++", "+++"], key="ua_prot")
            st.selectbox("잠혈(Hematuria)", ["없음", "미량", "+", "++", "+++"], key="ua_hema")
            st.selectbox("요당(Glycosuria)", ["없음", "미량", "+", "++", "+++"], key="ua_glu")

    # ANC 경고 배너
    if anc and anc < 500:
        warn_banner("ANC 500 미만 — 생채소·생과일 금지, 모든 음식은 충분히 가열하세요. 조리 후 2시간 지난 음식은 먹지 않기.")

    return dict(wbc=wbc, hb=hb, plt=plt, anc=anc, ca=ca, na=na, k=k, alb=alb)

def _therapy_section(picked_group, picked_dx):
    section("3️⃣ 약물 선택 (한글 표기)")
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

def main():
    st.set_page_config(page_title=f"{APP_TITLE} {APP_VERSION}", layout="centered", initial_sidebar_state="collapsed")
    inject_css()

    st.title(APP_TITLE)
    st.caption(f"빌드 {APP_VERSION} — 모바일 최적화 UI")

    _header_share()
    _patient_bar()
    picked_group, picked_dx = _mode_and_cancer_picker()
    labs = _labs_section()
    _therapy_section(picked_group, picked_dx)
    _result_section(labs, picked_group, picked_dx)
    _diet_guide_section(labs)

    st.markdown("""<div class='footer-note'>
    본 자료는 보호자의 이해를 돕기 위한 참고용 정보입니다. 수치 기반 판단과 약물 변경은 반드시 주치의와 상담하십시오.
    </div>""", unsafe_allow_html=True)

def _diet_guide_section(labs):
    section("5️⃣ 식이 가이드 (자동)")
    tips = []

    # 기준값(참고용, 병원 기준과 다를 수 있음)
    if labs.get('alb', 0) and labs['alb'] < 3.5:
        tips.append(("알부민 낮음", ["달걀", "연두부", "흰살 생선", "닭가슴살", "귀리죽"]))
    if labs.get('k', 0) and labs['k'] < 3.5:
        tips.append(("칼륨 낮음", ["바나나", "감자", "호박죽", "고구마", "오렌지"]))
    if labs.get('hb', 0) and labs['hb'] < 10.0:
        tips.append(("Hb 낮음", ["소고기", "시금치", "두부", "달걀 노른자", "렌틸콩"]))
    if labs.get('na', 0) and labs['na'] < 135:
        tips.append(("나트륨 낮음", ["전해질 음료", "미역국", "바나나", "오트밀죽", "삶은 감자"]))
    if labs.get('ca', 0) and labs['ca'] < 8.5:
        tips.append(("칼슘 낮음", ["연어통조림", "두부", "케일", "브로콜리", "참깨 제외"]))  # 참깨 제외 안내 유지

    if not tips:
        st.info("입력값 기준으로 필요한 식이 가이드가 없습니다. (정상 범위로 추정)")
        return

    for title, foods in tips:
        st.markdown(f"**• {title}** → 추천 식품 5개: " + ", ".join(foods))

    st.caption("영양제(철분제 등)는 추천에서 제외합니다. **항암 치료 중 철분제는 권장되지 않습니다.** 반드시 주치의와 상의하세요. 철분제+비타민C 병용 시 흡수 증가 가능성이 있습니다.")

if __name__ == "__main__":
    main()
