# streamlit_app.py — Strict order: app.py(main) -> side-effect -> fallback
# 요구사항 반영: 암 선택 / 항암제 선택 / 항생제 선택, 피수치 +/- 제거, ANC 식이가이드 유지
import types

_BOOTED = False

def _try_call_entry(mod: types.ModuleType) -> bool:
    """app.py 내 명시적 진입점 실행 시도: run > main > entry 순서"""
    for name in ("run", "main", "entry"):
        fn = getattr(mod, name, None)
        if callable(fn):
            fn()
            return True
    return False

try:
    import streamlit as st
    import app as _app  # app.py = 메인
    if not _try_call_entry(_app):
        # app.py가 최상위에서 렌더하는 구조라면 import만으로 충분
        pass
    _BOOTED = True
except Exception as e:
    # ---- Fallback UI ----
    import datetime as _dt
    import streamlit as st

    st.set_page_config(page_title="BloodMap (Fallback)", layout="wide")
    st.title("BloodMap — Fallback(안전모드)")
    st.caption("KST · 세포·면역치료 비표기 · 제작/자문: Hoya/GPT")
    st.warning("app.py 실행 실패로 Fallback UI가 표시되었습니다.\n오류: {}".format(e))

    # ---------- Helpers ----------
    def wkey(name:str)->str:
        return f"bm_{abs(hash(name))%10_000_000}_{name}"

    NORMALS = {
        "WBC": (4.0, 10.0),
        "Hb": (12.0, 16.0),
        "PLT": (150.0, 450.0),
        "CRP": (0.0, 0.5),
        "ANC": (1500.0, None),
        "Na": (135.0, 145.0),
        "K": (3.5, 5.1),
        "Alb": (3.5, 5.0),
        "Ca": (8.6, 10.2),
        "AST": (0.0, 40.0),
        "ALT": (0.0, 41.0),
        "Glu": (70.0, 199.0),
    }

    def interp(name, val):
        low, high = NORMALS.get(name,(None,None))
        if val is None:
            return "ok"
        try: v=float(val)
        except: return "ok"
        if low is not None and v < low: return "warn" if v >= low*0.8 else "alert"
        if high is not None and v > high: return "warn" if v <= high*1.2 else "alert"
        return "ok"

    def anc_guide(v):
        try: v=float(v)
        except: return []
        if v < 500:
            return [
                "생채소/날음식 금지 (충분 가열)",
                "전자레인지 30초 이상 재가열",
                "멸균·살균 처리 제품 권장",
                "조리 후 2시간 지난 음식 섭취 금지",
                "껍질 과일은 주치의와 상의",
            ]
        if v < 1000:
            return [
                "익힌 음식 위주, 외식 위생 확인",
                "남은 음식 재가열 후 섭취",
                "과일/야채는 세척 후 껍질 제거 권장",
                "유제품은 살균 제품",
                "손 위생/도마 분리",
            ]
        return [
            "일반 위생 수칙",
            "고단백 식단(연두부·흰살생선·닭가슴살 등)",
            "수분 충분 섭취",
            "날음식 과다 금지",
            "냉장 보관 철저",
        ]

    # ---------- Sidebar: 프로필/모드 ----------
    with st.sidebar:
        st.subheader("프로필")
        nick = st.text_input("별명", value="게스트", key=wkey("nick"))
        target = st.radio("대상", ["소아","성인","일상"], horizontal=True, key=wkey("target"))
        st.markdown("---")
        st.caption("혼돈 방지: **세포·면역치료(CAR‑T/TCR‑T/NK/HSCT)**는 표기하지 않습니다.")

    # ---------- 1) 암 선택 ----------
    st.header("① 암 선택")
    colA1, colA2 = st.columns([1,1])
    with colA1:
        cancer_cat = st.selectbox("암 카테고리", ["혈액암","림프종","육종","고형암","희귀암"], key=wkey("cancer_cat"))
    with colA2:
        dx = st.text_input("세부 진단(선택)", key=wkey("dx"))

    # ---------- 2) 항암제 선택 ----------
    st.header("② 항암제 선택")
    chemo_list = [
        "6-MP (6-mercaptopurine)",
        "MTX (Methotrexate)",
        "Vesanoid (ATRA, all-trans retinoic acid)",
        "ARA-C (Cytarabine)",
        "G-CSF (Filgrastim 등)",
    ]
    selected_chemo = st.multiselect("복수 선택 가능", chemo_list, key=wkey("chemo_pick"))

    # ARA-C 제형 옵션(선택 시 나타남)
    ara_c_form = None
    if any("ARA-C" in c for c in selected_chemo):
        ara_c_form = st.selectbox("ARA-C 제형", ["정맥(IV)","피하(SC)","고용량(HDAC)"], key=wkey("ara_form"))

    # ---------- 3) 항생제 선택 ----------
    st.header("③ 항생제 선택")
    abx_list = [
        "Amoxicillin/Clavulanate",
        "Ceftriaxone",
        "Cefepime",
        "Piperacillin/Tazobactam",
        "Vancomycin",
        "Meropenem",
    ]
    selected_abx = st.multiselect("복수 선택 가능", abx_list, key=wkey("abx_pick"))

    st.markdown("---")

    # ---------- 4) 피수치 입력 ----------
    st.header("④ 피수치 입력")
    col1, col2, col3 = st.columns(3)
    with col1:
        WBC = st.number_input("WBC (×10³/µL)", min_value=0.0, step=0.1, key=wkey("WBC"))
        Hb  = st.number_input("Hb (g/dL)", min_value=0.0, step=0.1, key=wkey("Hb"))
        PLT = st.number_input("PLT (×10³/µL)", min_value=0.0, step=1.0, key=wkey("PLT"))
        ANC = st.number_input("ANC (cells/µL)", min_value=0.0, step=10.0, key=wkey("ANC"))
    with col2:
        CRP = st.number_input("CRP (mg/dL)", min_value=0.0, step=0.1, key=wkey("CRP"))
        Na  = st.number_input("Na (mEq/L)", min_value=0.0, step=0.5, key=wkey("Na"))
        K   = st.number_input("K (mEq/L)", min_value=0.0, step=0.1, key=wkey("K"))
        Alb = st.number_input("Albumin (g/dL)", min_value=0.0, step=0.1, key=wkey("Alb"))
    with col3:
        Ca  = st.number_input("Calcium (mg/dL)", min_value=0.0, step=0.1, key=wkey("Ca"))
        AST = st.number_input("AST (U/L)", min_value=0.0, step=1.0, key=wkey("AST"))
        ALT = st.number_input("ALT (U/L)", min_value=0.0, step=1.0, key=wkey("ALT"))
        Glu = st.number_input("Glucose (mg/dL)", min_value=0.0, step=1.0, key=wkey("Glu"))

    st.markdown("---")
    go = st.button("🔎 해석하기", use_container_width=True, key=wkey("go"))

    if go:
        st.subheader("해석 결과")

        # (A) 암/약물 선택 요약
        st.markdown("**암 카테고리**: {}{}".format(
            cancer_cat, f" / {dx}" if dx.strip() else ""
        ))
        if selected_chemo:
            st.markdown("**항암제**: " + ", ".join(selected_chemo))
            if ara_c_form:
                st.caption(f"· ARA-C 제형: {ara_c_form}")
        else:
            st.caption("· 항암제 선택 없음")

        if selected_abx:
            st.markdown("**항생제**: " + ", ".join(selected_abx))
        else:
            st.caption("· 항생제 선택 없음")

        # (B) 피수치 결과 — 값 + 배지만 (±, 참조범위 표식 제거)
        vals = {
            "WBC": WBC, "Hb": Hb, "PLT": PLT, "CRP": CRP, "ANC": ANC,
            "Na": Na, "K": K, "Alb": Alb, "Ca": Ca, "AST": AST, "ALT": ALT, "Glu": Glu
        }
        for k,v in vals.items():
            if v and v>0:
                level = interp(k,v)
                badge = {"ok":"🟢 정상","warn":"🟡 경계","alert":"🚨 위험"}[level]
                st.write(f"- **{k}**: {v} {badge}")

        # (C) ANC 식이가이드
        if ANC and ANC>0:
            st.markdown("### ANC 기반 식이가이드")
            for tip in anc_guide(ANC):
                st.write(f"- {tip}")

        # (D) 간단 .md 보고서
        lines = ["# BloodMap 결과 요약"]
        lines.append(f"- 별명: {nick}")
        lines.append(f"- 대상: {target}")
        lines.append(f"- 암 카테고리: {cancer_cat}" + (f" / {dx}" if dx.strip() else ""))
        if selected_chemo:
            lines.append(f"- 항암제: {', '.join(selected_chemo)}")
            if ara_c_form: lines.append(f"  · ARA-C 제형: {ara_c_form}")
        if selected_abx:
            lines.append(f"- 항생제: {', '.join(selected_abx)}")
        lines.append("## 최근 검사값")
        for k,v in vals.items():
            if v and v>0:
                level = interp(k,v)
                lines.append(f"- {k}: {v} ({level})")
        lines.append("")
        lines.append(f"_생성 시각(KST): {_dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_")
        md = "\n".join(lines)
        st.download_button("💾 보고서 .md 다운로드", data=md.encode("utf-8"),
                           file_name="bloodmap_report.md", mime="text/markdown", key=wkey("dl_md_fb2"))
    else:
        st.caption("※ '해석하기' 버튼을 눌러야 결과가 표시됩니다.")

# 안전장치: 외부에서 import만 된 경우 Streamlit이 최소 한 번은 무언가를 그리도록 보장
if not _BOOTED:
    try:
        import streamlit as st
        st.caption("초기화 완료")
    except Exception:
        pass
