# -*- coding: utf-8 -*-
def main():
    from datetime import datetime, date
    import streamlit as st

    # ---------- Page / Title ----------
    st.set_page_config(page_title="BloodMap", layout="centered")
    st.title("BloodMap")

    # ---------- Required banner (user requested) ----------
    st.warning(
        "⚠️ 본 수치 해석은 참고용 도구이며, 개발자와 무관합니다.\n\n"
        "- 철분제와 비타민 C 조합은 항암 치료 중인 환자에게 해로울 수 있으므로 반드시 주치의와 상담 후 복용 여부를 결정해야 합니다.\n"
        "- BloodMap은 개인정보를 수집하지 않으며, 입력 정보는 저장되지 않습니다."
    )

    # ---------- Small helpers ----------
    def _f(x):
        try:
            return float(x)
        except Exception:
            return None

    def num(label, key, decimals=1, as_int=False):
        if as_int:
            return st.number_input(label, value=0, step=1, format="%d", key=key)
        fmt = "%." + str(decimals) + "f"
        return st.number_input(label, value=0.0, step=0.1, format=fmt, key=key)

    # ---------- 1) Meta ----------
    st.header("1️⃣ 환자/암·소아 정보")
    c1,c2,c3 = st.columns([2,1,1])
    with c1:
        nickname = st.text_input("별명", placeholder="예: 홍길동")
    with c2:
        pin = st.text_input("PIN(4자리)", max_chars=4, placeholder="1234")
    with c3:
        test_date = st.date_input("검사 날짜", value=date.today())

    # Mode
    mode = st.selectbox("모드 선택", ["일반/암", "소아(일상/호흡기)", "소아(감염질환)"])

    # ---------- 2) 암 그룹/진단 + 항암제(수동 선택) ----------
    group = cancer_label = None
    selected_drugs = []
    if mode == "일반/암":
        group = st.selectbox("암 그룹 선택", ["미선택/일반","혈액암","고형암","육종","소아암","희귀암"])
        if group == "혈액암":
            cancer_label = st.selectbox("혈액암 (진단명)", [
                "AML (급성 골수성 백혈병)", "APL (급성 전골수구성 백혈병)",
                "ALL (급성 림프모구성 백혈병)", "CML (만성 골수성 백혈병)", "CLL (만성 림프구성 백혈병)"
            ])
        elif group == "고형암":
            cancer_label = st.selectbox("고형암 (진단명)", [
                "폐암(Lung cancer)","유방암(Breast cancer)","위암(Gastric cancer)",
                "대장암(Cololoractal cancer)","간암(HCC)","췌장암(Pancreatic cancer)",
                "담도암(Cholangiocarcinoma)","자궁내막암(Endometrial cancer)",
                "구강암/후두암","피부암(흑색종)","신장암(RCC)",
                "갑상선암","난소암","자궁경부암","전립선암","뇌종양(Glioma)","식도암","방광암"
            ])
        elif group == "육종":
            cancer_label = st.selectbox("육종 (진단명)", [
                "연부조직육종 (STS)","골육종 (Osteosarcoma)","유잉육종 (Ewing sarcoma)",
                "평활근육종 (Leiomyosarcoma)","지방육종 (Liposarcoma)",
                "횡문근육종 (Rhabdomyosarcoma)","활막육종 (Synovial sarcoma)"
            ])
        elif group == "소아암":
            cancer_label = st.selectbox("소아암 (진단명)", ["Neuroblastoma","Wilms tumor"])
        elif group == "희귀암":
            cancer_label = st.selectbox("희귀암 (진단명)", [
                "담낭암(Gallbladder cancer)","부신암(Adrenal cancer)","망막모세포종(Retinoblastoma)",
                "흉선종/흉선암(Thymoma/Thymic carcinoma)","신경내분비종양(NET)",
                "간모세포종(Hepatoblastoma)","비인두암(NPC)","GIST"
            ])

        st.markdown("### 💊 항암제 선택 (수동)")
        # 간단한 추천 풀(그룹별)
        rec_map = {
            "혈액암": ["ATRA","ARA-C","Idarubicin","Daunorubicin","Fludarabine","MTX","6-MP","Cyclophosphamide","Etoposide","Hydroxyurea","G-CSF","Imatinib","Dasatinib","Nilotinib"],
            "고형암": ["Cisplatin","Carboplatin","Paclitaxel","Docetaxel","Gemcitabine","Pemetrexed","Trastuzumab","Bevacizumab","Pembrolizumab","Nivolumab","Oxaliplatin","5-FU","Capecitabine","Irinotecan","Sorafenib","Lenvatinib"],
            "육종": ["Doxorubicin","Ifosfamide","Pazopanib","Gemcitabine","Docetaxel","Vincristine","Etoposide","Cisplatin","MTX"],
            "소아암": ["Cyclophosphamide","Ifosfamide","Doxorubicin","Vincristine","Etoposide","Carboplatin","Cisplatin","Topotecan","Irinotecan"],
            "희귀암": ["Imatinib","Sunitinib","Regorafenib","Mitotane","Gemcitabine","Cisplatin","Etoposide","Doxorubicin"],
        }
        show = sorted(set(rec_map.get(group, sum(rec_map.values(), []))))
        q = st.text_input("🔍 항암제 검색", key="drug_search")
        show = [d for d in show if (not q) or (q.lower() in d.lower())]
        selected_drugs = st.multiselect("항암제 선택", show, default=[])

        # 일반 정보 배너
        if any(x in selected_drugs for x in ["MTX","6-MP"]):
            st.info("ℹ️ 유의사항: 개인별 처방/용량은 반드시 담당 의료진 지시를 따르세요.")
        if "MTX" in selected_drugs:
            st.warning("MTX: 보통 **주 1회** 복용 스케줄. NSAIDs/술 과다/탈수는 독성↑ 가능.")
        if "6-MP" in selected_drugs:
            st.warning("6-MP: **TPMT/NUDT15** 낮으면 골수억제↑. Allopurinol/Febuxostat 병용 시 용량조절 필요.")

        # 항암환자 보충제 주의
        st.info("⚠️ 항암 환자 보충제 주의: 철분제·비타민 C 보충제는 치료/질환에 영향 가능 → 임의 복용 금지, 반드시 **주치의와 상담**.")

    # ---------- 3) 기본 혈액 검사 (소아 모드는 기본 숨김) ----------
    st.header("2️⃣ 기본 혈액 검사 수치")
    open_labs = True
    if mode.startswith("소아"):
        open_labs = st.checkbox("🧪 피수치 입력 열기", value=False)
    vals = {}
    if open_labs:
        cols = st.columns(5)
        fields = ["WBC","Hb","PLT","ANC","Na","K","Ca","P","Cr","BUN","AST","ALT","LDH","CRP","Albumin (알부민)","Glucose","TP","UA","TB","BNP"]
        for i, f in enumerate(fields):
            with cols[i % 5]:
                if f in {"WBC","PLT","ANC","Na","K","Ca","P","Cr","BUN","LDH","BNP"}:
                    vals[f] = num(f, key=f"v_{f}", decimals=1)
                elif f in {"AST","ALT","CRP"}:
                    vals[f] = num(f, key=f"v_{f}", decimals=2)
                else:
                    vals[f] = num(f, key=f"v_{f}", decimals=1)

    # ---------- 4) 특수검사 (토글) ----------
    st.subheader("🧪 특수검사")
    if st.checkbox("지질패널 (TG/총콜/HDL/LDL)", value=True):
        c1,c2,c3,c4 = st.columns(4)
        with c1: vals["TG"] = num("TG (중성지방, mg/dL)", key="lip_tg", as_int=True)
        with c2: vals["총콜레스테롤"] = num("총콜레스테롤 (mg/dL)", key="lip_tc", as_int=True)
        with c3: vals["HDL"] = num("HDL (mg/dL)", key="lip_hdl", as_int=True)
        with c4: vals["LDL"] = num("LDL (mg/dL)", key="lip_ldl", as_int=True)
    if st.checkbox("보체/면역 (C3·C4·CH50)", value=False):
        d1,d2,d3 = st.columns(3)
        with d1: vals["C3"] = num("C3 (mg/dL)", key="comp_c3", as_int=True)
        with d2: vals["C4"] = num("C4 (mg/dL)", key="comp_c4", as_int=True)
        with d3: vals["CH50"] = num("CH50 (U/mL)", key="comp_ch50", as_int=True)
    if st.checkbox("요검사 (요단백/잠혈/요당)", value=False):
        u1,u2,u3 = st.columns(3)
        with u1: vals["요단백"] = st.selectbox("요단백", ["-","trace","+","++","+++"], index=0)
        with u2: vals["잠혈"] = st.selectbox("잠혈", ["-","trace","+","++","+++"], index=0)
        with u3: vals["요당"] = st.selectbox("요당", ["-","trace","+","++","+++"], index=0)

    # ---------- 5) 해석 ----------
    st.header("3️⃣ 해석 / 결과")
    run = st.button("🧠 해석하기", use_container_width=True)
    if run:
        # 수치별 해석 (fallback 룰셋)
        st.markdown("#### 🩸 수치별 해석")
        REF = {
            "WBC": (4.0, 10.0), "Hb": (12.0, 17.0), "PLT": (150, 400), "ANC": (1500, None),
            "Na": (135,145), "K": (3.5,5.1), "Ca": (8.6,10.2), "P": (2.5,4.5), "Cr": (0.6,1.3), "BUN": (8,23),
            "AST": (0,40), "ALT": (0,40), "LDH": (0,250), "CRP": (0,0.5),
            "Albumin (알부민)": (3.5,5.0), "Glucose": (70,140), "TP": (6.0,8.3), "UA": (3.5,7.2), "TB": (0.2,1.2),
            "BNP": (0,100)
        }
        lines = []
        for k, v in vals.items():
            val = _f(v)
            if val is None:
                continue
            if k == "ANC":
                if val < 500: lines.append("ANC < 500: **중증 호중구감소증** — 발열 시 즉시 진료.")
                elif val < 1000: lines.append("ANC 500~999: **중등도 호중구감소증** — 감염 주의/외출·식품 위생.")
                elif val < 1500: lines.append("ANC 1000~1499: **경증 호중구감소증** — 위생/감염 주의.")
                else: lines.append("ANC 정상 범위.")
                continue
            lo, hi = REF.get(k, (None, None))
            disp = f"{k} = {val}"
            if lo is not None and val < lo:
                if k == "Hb":
                    lines.append(f"{disp} ↓ — **빈혈 가능**(피로/어지럼).")
                elif k == "PLT":
                    lines.append(f"{disp} ↓ — **혈소판 감소**." if val >= 50 else f"{disp} ↓ — **출혈 위험 高**.")
                elif k == "Na":
                    lines.append(f"{disp} ↓ — **저나트륨혈증** 가능.")
                elif k == "K":
                    lines.append(f"{disp} ↓ — **저칼륨혈증** 가능(근력저하/부정맥).")
                elif k == "Ca":
                    lines.append(f"{disp} ↓ — **저칼슘혈증** 가능.")
                elif k == "Albumin (알부민)":
                    lines.append(f"{disp} ↓ — **영양상태/간·신장** 점검.")
                else:
                    lines.append(f"{disp} ↓")
            elif hi is not None and val > hi:
                if k in ("AST","ALT"):
                    lines.append(f"{disp} ↑ — **간수치 상승**(약물/간염 등) 추적 필요.")
                elif k == "CRP":
                    lines.append(f"{disp} ↑ — **염증/감염 의심**.")
                elif k in ("BUN","Cr"):
                    lines.append(f"{disp} ↑ — **신장 기능 점검**.")
                elif k == "K":
                    lines.append(f"{disp} ↑ — **고칼륨혈증** 주의.")
                elif k == "Na":
                    lines.append(f"{disp} ↑ — **고나트륨혈증** 가능.")
                elif k == "Ca":
                    lines.append(f"{disp} ↑ — **고칼슘혈증** 가능.")
                elif k == "LDH":
                    lines.append(f"{disp} ↑ — **조직 손상/용혈** 가능.")
                else:
                    lines.append(f"{disp} ↑")
            else:
                lines.append(f"{disp} : 정상 범위.")
        if lines:
            for L in lines: st.write("- " + L)
        else:
            st.caption("입력된 피수치가 없습니다.")

        # 음식/생활 가이드 (기본 + 지질)
        st.markdown("#### 🥗 음식/생활 가이드")
        food = []
        alb = _f(vals.get("Albumin (알부민)")); hb = _f(vals.get("Hb")); k = _f(vals.get("K")); na = _f(vals.get("Na")); ca = _f(vals.get("Ca")); anc = _f(vals.get("ANC"))
        if alb is not None and alb < 3.5:
            food.append("알부민 낮음: **단백질 보충**(살코기·생선·달걀·두부/콩) + **소량씩 자주 식사**, 부종 있으면 **짠 음식 줄이기**.")
        # 암 환자 여부
        is_cancer = (mode == "일반/암") and (group in {"혈액암","고형암","육종","소아암","희귀암"})
        if selected_drugs:
            is_cancer = True
        if hb is not None and hb < 12.0:
            if is_cancer:
                food.append("빈혈 경향: **철분 식품** 섭취/보충은 **주치의와 상담 후** 진행. **철분제·비타민 C 보충제는 임의 복용 금지**.")
            else:
                food.append("빈혈 경향: **철분 식품** + **비타민 C** 함께, 식사 전후 **차/커피는 피하기**.")
        if k is not None and k < 3.5:
            food.append("칼륨 낮음: 바나나·감자·토마토·키위·오렌지 등 **칼륨 식품 보충**.")
        if k is not None and k > 5.1:
            food.append("칼륨 높음: 바나나·코코넛워터·감자·시금치 등 **고칼륨 식품 과다 섭취 피하기**, **데치기 조리** 활용.")
        if na is not None and na < 135:
            food.append("저나트륨: **수분 과다섭취 줄이기**, 전해질 균형 유지(무리한 수분제한 금지).")
        if na is not None and na > 145:
            food.append("고나트륨: **가공식품·라면·국물** 줄이고 **물 자주 마시기**.")
        if ca is not None and ca < 8.6:
            food.append("칼슘 낮음: 우유·요거트·치즈/멸치·뼈째 생선·두부·케일 + **비타민 D** 함께.")
        if ca is not None and ca > 10.2:
            food.append("칼슘 높음: **칼슘 보충제 과다 피하기**, **수분 충분히**.")
        if anc is not None:
            if anc < 500:
                food.append("ANC 매우 낮음(<500): **완전가열 조리·위생 철저**, 생고기/회/반숙란/비살균유/샐러드바 **피하기**.")
            elif anc < 1000:
                food.append("ANC 낮음(500~999): **위생관리·완전가열**, **뷔페/상온보관 음식 피하기**.")
            elif anc < 1500:
                food.append("ANC 경계(1000~1499): **위생 주의**(손씻기·세척·껍질 벗기기).")

        tg = _f(vals.get("TG")); tc = _f(vals.get("총콜레스테롤")); hdl = _f(vals.get("HDL")); ldl = _f(vals.get("LDL"))
        if tg is not None and tg >= 200:
            food.append("중성지방(TG) 높음: 단 음료/과자 제한 · 튀김/버터/마요네즈 줄이기 · 라면/가공식품(짠맛) 줄이기 · 채소/등푸른생선/현미·잡곡/소량 견과류 권장.")
        if tc is not None and tc >= 240:
            food.append("총콜레스테롤 높음(≥240): 포화·트랜스지방 줄이기(가공육·튀김·제과) · 가공치즈/크림 줄이기 · 식이섬유(귀리·콩류·과일) 늘리기 · 식물성 스테롤 도움.")
        if tc is not None and 200 <= tc <= 239:
            food.append("총콜레스테롤 경계역(200~239): 위 생활수칙을 참고하여 식습관 개선 권고.")
        if hdl is not None and hdl < 40:
            food.append("HDL 낮음(<40): 규칙적 유산소·체중조절·채소/통곡물·견과류·생선 섭취 권장.")
        if ldl is not None and ldl >= 160:
            food.append("LDL 높음(≥160): 포화지방 제한·식이섬유/식물성 스테롤·등푸른생선 권장.")

        # 항암환자 공통 경고 한 줄
        if is_cancer:
            food.append("⚠️ 항암 환자: **철분제 + 비타민 C 보충**은 치료/질환에 영향 가능 — **임의 복용 금지, 반드시 주치의와 상담**.")

        if food:
            for tip in dict.fromkeys(food):  # dedupe, keep order
                st.markdown(f"- {tip}")
        else:
            st.caption("해당되는 가이드가 없습니다.")

        # 간단 보고서 다운로드 (md)
        report = ["# BloodMap Report",
                  f"- 모드: {mode}",
                  f"- 그룹/진단: {group or '-'} / {cancer_label or '-'}",
                  f"- 별명/PIN: {nickname or '-'} / {(pin or '')}",
                  "## 수치 입력"]
        for k,v in vals.items():
            if v not in ("", None):
                report.append(f"- {k}: {v}")
        report.append("## 가이드")
        report.extend([f"- {t}" for t in dict.fromkeys(food)])

        st.download_button(
            "📥 보고서(.md) 다운로드",
            data="\n".join(report).encode("utf-8"),
            file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown"
        )
