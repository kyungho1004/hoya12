# streamlit_app.py — Robust entrypoint with fallback UI
# 1) 기본: app.py를 import하여 전체 UI 실행
# 2) 예외 발생 시: 최소 기능(피수치 입력/해석) Fallback UI 표시

try:
    import app as _app  # app.py의 최상위 Streamlit 코드가 실행됨
except Exception as e:
    import datetime as _dt
    import streamlit as st

    # ---------- Branding banner (safe fallback) ----------
    def _render_banner():
        st.caption("KST · 세포·면역치료는 표기하지 않습니다 · 제작/자문: Hoya/GPT")

    st.set_page_config(page_title="BloodMap (Fallback)", layout="wide")
    st.title("BloodMap (Fallback)")
    _render_banner()
    st.warning("app.py 로드 실패로 Fallback UI가 실행되었습니다.\n오류: {}".format(e))

    # ---------- Helpers ----------
    def wkey(name:str)->str:
        return f"bm_{abs(hash(name))%10_000_000}_{name}"

    def interp_range(val, low=None, high=None):
        if val is None:
            return "ok"
        try:
            v = float(val)
        except Exception:
            return "ok"
        if low is not None and v < low:
            return "alert" if (low - v) / max(low,1) > 0.2 else "warn"
        if high is not None and v > high:
            return "alert" if (v - high) / max(high,1) > 0.2 else "warn"
        return "ok"

    NORMALS_ADULT = {
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

    # ---------- Sidebar ----------
    with st.sidebar:
        st.subheader("프로필")
        nick = st.text_input("별명", value="게스트", key=wkey("nick"))
        age_group = st.selectbox("구분", ["소아","성인","일상"], index=1, key=wkey("agegrp"))
        st.markdown("—")
        st.caption("혼돈 방지 및 범위 밖 안내: 저희는 **세포·면역 치료(CAR‑T, TCR‑T, NK, HSCT 등)**는 표기하지 않습니다.")

    # ---------- Main: Inputs ----------
    st.header("피수치 입력")
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
    st.header("진단 · 카테고리")
    cat = st.selectbox("암 카테고리", ["혈액암","림프종","육종","고형암","희귀암"], key=wkey("cat"))
    age_mode = st.radio("대상", ["소아","성인","일상"], horizontal=True, key=wkey("age_mode"))

    st.markdown("---")
    go = st.button("🔎 해석하기", use_container_width=True, key=wkey("go"))

    def eval_labs():
        res = []
        data = [("WBC",WBC),("Hb",Hb),("PLT",PLT),("CRP",CRP),("ANC",ANC),
                ("Na",Na),("K",K),("Alb",Alb),("Ca",Ca),("AST",AST),("ALT",ALT),("Glu",Glu)]
        for name, val in data:
            low, high = NORMALS_ADULT.get(name,(None,None))
            level = interp_range(val, low, high)
            res.append((name, val, level, low, high))
        return res

    def anc_diet_guide(anc):
        if anc is None:
            return []
        try:
            v = float(anc)
        except Exception:
            return []
        if v < 500:
            return [
                "생채소/날음식 금지(모든 음식은 충분히 가열)",
                "전자레인지 30초 이상 재가열 후 섭취",
                "멸균/살균 처리 제품 권장",
                "조리 후 2시간 지난 음식은 섭취 지양",
                "껍질 과일: 주치의와 상의 후 섭취 결정",
            ]
        elif v < 1000:
            return [
                "익힌 음식 위주, 외식 시 위생 상태 확인",
                "남은 음식은 가급적 재가열 후 섭취",
                "과일/야채는 깨끗이 세척하고 껍질 제거 권장",
                "유제품은 살균 제품 위주",
                "손 위생/도마 구분 철저",
            ]
        else:
            return [
                "일반 위생 수칙 준수",
                "고단백 식단으로 회복 보조(연두부, 흰살 생선 등)",
                "수분 충분 섭취",
                "과도한 날음식은 피하기",
                "조리 후 냉장 보관 철저",
            ]

    if go:
        st.subheader("해석 결과")
        rows = eval_labs()
        for name, val, level, low, high in rows:
            if val and val > 0:
                badge = {"ok":"🟢 정상","warn":"🟡 경계","alert":"🚨 위험"}[level]
                ref = []
                if low is not None: ref.append(f"{low}↓")
                if high is not None: ref.append(f"{high}↑")
                ref_txt = " | 참고: " + " ~ ".join([s for s in ref if s]) if ref else ""
                st.write(f"- **{name}**: {val} {badge}{ref_txt}")
        # ANC 식이가이드
        st.markdown("### ANC 기반 식이가이드")
        for tip in anc_diet_guide(ANC):
            st.write(f"- {tip}")

        # 보고서 .md
        lines = ["# BloodMap 결과 요약"]
        lines.append(f"- 별명: {nick}")
        lines.append(f"- 카테고리: {cat} / 대상: {age_mode}")
        lines.append("## 최근 검사값")
        for name, val, level, low, high in rows:
            if val and val > 0:
                lines.append(f"- {name}: {val} ({level})")
        lines.append("")
        lines.append(f"_생성 시각(KST): {_dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_")
        md = "\n".join(lines)
        st.download_button("💾 보고서 .md 다운로드", data=md.encode("utf-8"),
                           file_name="bloodmap_report.md", mime="text/markdown", key=wkey("dl_md_fb"))
    else:
        st.caption("※ '해석하기' 버튼을 눌러야 결과가 표시됩니다.")
