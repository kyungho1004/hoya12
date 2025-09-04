# -*- coding: utf-8 -*-
def main():
    # Standard libs
    from datetime import date
    import streamlit as st

    # ---------- Page setup ----------
    st.set_page_config(page_title="BloodMap", layout="centered")

    # CSS: remove +/- steppers and keep clean numeric visuals
    st.markdown(
        """
        <style>
        input[type=number]::-webkit-outer-spin-button,
        input[type=number]::-webkit-inner-spin-button { -webkit-appearance: none; margin: 0; }
        input[type=number] { -moz-appearance: textfield; }
        .stTextInput>div>div>input { font-variant-numeric: tabular-nums; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ---------- Helper: spinner-free numeric input ----------
    def num_in(label, key, decimals=1, as_int=False, placeholder=""):
        ph = placeholder or ("예: " + ("0" if as_int else f"0.{('0'*decimals)}"))
        txt = st.text_input(label, key=key, placeholder=ph)
        if txt is None or txt.strip() == "":
            return None
        s = txt.strip().replace(",", "")
        try:
            v = float(s)
            if as_int:
                return int(v)
            if decimals is None:
                return v
            return round(v, decimals)
        except Exception:
            st.caption("입력 예: " + ph)
            return None

    # ---------- Header & banner ----------
    st.title("BloodMap")
    st.warning(
        "⚠️ 본 수치 해석은 참고용 도구이며, 개발자와 무관합니다.\n\n"
        "- 철분제와 비타민 C 조합은 항암 치료 중인 환자에게 해로울 수 있으므로 반드시 주치의와 상담 후 복용 여부를 결정해야 합니다.\n"
        "- BloodMap은 개인정보를 수집하지 않으며, 입력 정보는 저장되지 않습니다."
    )

    # ---------- Section 1: patient/meta ----------
    st.divider()
    st.header("1️⃣ 환자/암·소아 정보")

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        nickname = st.text_input("별명", placeholder="예: 홍길동")
    with c2:
        pin = st.text_input("PIN(4자리)", max_chars=4, placeholder="1234")
    with c3:
        when = st.date_input("검사 날짜", value=date.today())

    mode = st.selectbox("모드 선택", ["일반/암", "소아(일상/호흡기)", "소아(감염질환)"])

    # For cancer mode
    group = None
    cancer_label = None
    selected_drugs = []

    if mode == "일반/암":
        group = st.selectbox("암 그룹 선택", ["미선택/일반", "혈액암", "고형암", "육종", "소아암", "희귀암"])
        if group == "혈액암":
            cancer_label = st.selectbox(
                "혈액암 (진단명)",
                ["AML (급성 골수성 백혈병)", "APL (급성 전골수구성 백혈병)", "ALL (급성 림프모구성 백혈병)",
                 "CML (만성 골수성 백혈병)", "CLL (만성 림프구성 백혈병)"],
            )
        elif group == "고형암":
            cancer_label = st.selectbox(
                "고형암 (진단명)",
                ["폐암(Lung cancer)","유방암(Breast cancer)","위암(Gastric cancer)","대장암(Cololoractal cancer)",
                 "간암(HCC)","췌장암(Pancreatic cancer)","담도암(Cholangiocarcinoma)","자궁내막암(Endometrial cancer)",
                 "구강암/후두암","피부암(흑색종)","신장암(RCC)","갑상선암","난소암","자궁경부암","전립선암","뇌종양(Glioma)","식도암","방광암"],
            )
        elif group == "육종":
            cancer_label = st.selectbox(
                "육종 (진단명)",
                ["연부조직육종 (STS)","골육종 (Osteosarcoma)","유잉육종 (Ewing sarcoma)",
                 "평활근육종 (Leiomyosarcoma)","지방육종 (Liposarcoma)","횡문근육종 (Rhabdomyosarcoma)","활막육종 (Synovial sarcoma)"],
            )
        elif group == "소아암":
            cancer_label = st.selectbox("소아암 (진단명)", ["Neuroblastoma", "Wilms tumor"])
        elif group == "희귀암":
            cancer_label = st.selectbox(
                "희귀암 (진단명)",
                ["담낭암(Gallbladder cancer)","부신암(Adrenal cancer)","망막모세포종(Retinoblastoma)",
                 "흉선종/흉선암(Thymoma/Thymic carcinoma)","신경내분비종양(NET)","간모세포종(Hepatoblastoma)","비인두암(NPC)","GIST"],
            )

        # Manual anticancer drug selection
        drug_pool = sorted(set([
            # Heme
            "ARA-C","Daunorubicin","Idarubicin","Cyclophosphamide","Etoposide","Fludarabine","Hydroxyurea",
            "MTX","ATRA","G-CSF","6-MP","Imatinib","Dasatinib","Nilotinib","Vincristine","Asparaginase","Topotecan",
            # Solid incl. sarcoma
            "Cisplatin","Carboplatin","Paclitaxel","Docetaxel","Gemcitabine","Pemetrexed","Oxaliplatin",
            "Irinotecan","5-FU","Capecitabine","Trastuzumab","Bevacizumab","Sorafenib","Lenvatinib",
            "Gefitinib","Erlotinib","Osimertinib","Alectinib","Pembrolizumab","Nivolumab","Temozolomide","Ifosfamide","Pazopanib"
        ]))
        q = st.text_input("🔍 항암제 검색(영문/한글)")
        show = [d for d in drug_pool if (not q) or (q.lower() in d.lower())]
        selected_drugs = st.multiselect("항암제 선택", show, default=[])
        for d in selected_drugs:
            _ = num_in(f"{d} - 용량/알약", key=f"med_{d}", decimals=1)

        st.info("⚠️ 항암 환자 보충제 주의: 철분제·비타민 C 등 보충제는 치료/질환에 영향 가능 → 임의 복용 금지, 반드시 주치의와 상담.")

    # ---------- Section 2: Labs ----------
    st.divider()
    hide_default = mode.startswith("소아")
    open_labs = st.checkbox("🧪 피수치 입력 열기", value=not hide_default) if hide_default else True

    # Labels for basic ORDER
    ORDER = ["WBC","Hb","PLT","ANC","Na","K","Ca","P","Cr","BUN","AST","ALT","LDH","CRP","Albumin (알부민)","Glucose","TP","UA","TB","BNP"]

    vals = {}
    def label_ko(s):
        mapping = {
            "WBC":"WBC (백혈구)","Hb":"Hb (혈색소)","PLT":"PLT (혈소판)","ANC":"ANC (절대중성구수)",
            "Na":"Na (나트륨)","K":"K (칼륨)","Ca":"Ca (칼슘)","P":"P (인)","Cr":"Cr (크레아티닌)","BUN":"BUN (혈중요소질소)",
            "AST":"AST (간수치)","ALT":"ALT (간세포 수치)","LDH":"LDH (젖산탈수소효소)","CRP":"CRP (염증수치)",
            "Albumin (알부민)":"Albumin (알부민/단백)","Glucose":"Glucose (혈당)","TP":"TP (총단백)",
            "UA":"UA (요산)","TB":"TB (총빌리루빈)","BNP":"BNP (심부전 표지)",
            "TG":"TG (중성지방, mg/dL)","총콜레스테롤":"총콜레스테롤 (mg/dL)","HDL":"HDL (mg/dL)","LDL":"LDL (mg/dL)",
        }
        return mapping.get(s, s)

    if open_labs:
        st.header("2️⃣ 기본 혈액 검사 수치 (입력한 값만 해석)")
        for name in ORDER:
            dec = 2 if name == "CRP" else 1
            vals[name] = num_in(label_ko(name), key=f"v_{name}", decimals=dec)

    st.markdown("### 🧪 특수검사")
    if st.checkbox("지질패널 (TG/총콜/HDL/LDL)", value=True):
        c1, c2, c3, c4 = st.columns(4)
        with c1: vals["TG"] = num_in(label_ko("TG"), key="lip_tg", decimals=0)
        with c2: vals["총콜레스테롤"] = num_in(label_ko("총콜레스테롤"), key="lip_tc", decimals=0)
        with c3: vals["HDL"] = num_in(label_ko("HDL"), key="lip_hdl", decimals=0)
        with c4: vals["LDL"] = num_in(label_ko("LDL"), key="lip_ldl", decimals=0)

    # ---------- Pediatric inputs ----------
    ped_daily = {}
    ped_infect = {}

    if mode == "소아(일상/호흡기)":
        st.subheader("소아 상태 입력")
        a,b,c = st.columns(3)
        with a:
            ped_daily["temp"] = num_in("체온(°C)", key="pd_temp", decimals=1)
            ped_daily["cough"] = st.selectbox("기침 정도", ["없음","약간","보통","심함"], index=0, key="pd_cough")
        with b:
            ped_daily["rr"] = num_in("호흡수(회/분)", key="pd_rr", decimals=0, as_int=True)
            ped_daily["throat"] = st.selectbox("인후통", ["없음","약간","보통","심함"], index=0, key="pd_throat")
        with c:
            ped_daily["intake"] = num_in("수분 섭취(컵/일)", key="pd_intake", decimals=1)
            ped_daily["ear"] = st.selectbox("귀 아파함", ["없음","약간","보통","심함"], index=0, key="pd_ear")

    if mode == "소아(감염질환)":
        st.subheader("소아 감염질환 선택")
        disease = st.selectbox(
            "질환 선택",
            ["AOM(급성 중이염)","Pharyngitis(인후염)","URTI(상기도감염)","Gastroenteritis(장염)",
             "UTI(요로감염)","Rotavirus(로타)","Adenovirus(아데노)","COVID-19(코로나19)","Influenza(독감)"]
        )
        ped_infect["name"] = disease

        # build inputs
        opts4 = ["없음","약간","보통","심함"]
        cols = st.columns(3)
        def sel(i, title):
            with cols[i%3]:
                return st.selectbox(title, opts4, index=0, key=f"pi_sel_{i}_{title}")
        def nin(i, title, as_int=False):
            with cols[i%3]:
                return num_in(title, key=f"pi_num_{i}_{title}", decimals=0 if as_int else 1, as_int=as_int)

        if disease.startswith("AOM"):
            ped_infect["귀 아파함"] = sel(0,"귀 아파함")
            ped_infect["체온"] = nin(1,"체온(°C)")
            ped_infect["구토/설사"] = sel(2,"구토/설사")
        elif disease.startswith("Pharyngitis"):
            ped_infect["인후통"] = sel(0,"인후통")
            ped_infect["체온"] = nin(1,"체온(°C)")
            ped_infect["기침"] = sel(2,"기침")
        elif disease.startswith("URTI"):
            ped_infect["콧물"] = sel(0,"콧물")
            ped_infect["기침"] = sel(1,"기침")
            ped_infect["체온"] = nin(2,"체온(°C)")
        elif disease.startswith("Gastroenteritis"):
            ped_infect["설사 횟수"] = nin(0,"설사 횟수(회/일)", as_int=True)
            ped_infect["구토 횟수"] = nin(1,"구토 횟수(회/일)", as_int=True)
            ped_infect["복통"] = sel(2,"복통")
        elif disease.startswith("UTI"):
            ped_infect["배뇨통"] = sel(0,"배뇨통")
            ped_infect["빈뇨"] = nin(1,"빈뇨(회/일)", as_int=True)
            ped_infect["체온"] = nin(2,"체온(°C)")
        elif disease.startswith("Rotavirus"):
            ped_infect["설사 횟수"] = nin(0,"설사 횟수(회/일)", as_int=True)
            ped_infect["구토 횟수"] = nin(1,"구토 횟수(회/일)", as_int=True)
            ped_infect["탈수 의심"] = sel(2,"탈수 의심")
        elif disease.startswith("Adenovirus"):
            ped_infect["인후통"] = sel(0,"인후통")
            ped_infect["결막 충혈"] = sel(1,"결막 충혈")
            ped_infect["체온"] = nin(2,"체온(°C)")
        elif disease.startswith("COVID-19"):
            ped_infect["체온"] = nin(0,"체온(°C)")
            ped_infect["기침"] = sel(1,"기침")
            ped_infect["인후통"] = sel(2,"인후통")
        elif disease.startswith("Influenza"):
            ped_infect["체온"] = nin(0,"체온(°C)")
            ped_infect["근육통"] = sel(1,"근육통")
            ped_infect["기침"] = sel(2,"기침")

    # ---------- Run ----------
    st.divider()
    if st.button("🧠 해석하기 / 결과 생성", use_container_width=True):
        st.subheader("📋 해석 결과")

        # Simple lab interpretation fallback
        REF = {
            "WBC": (4.0, 10.0), "Hb": (12.0, 17.0), "PLT": (150, 400), "ANC": (1500, None),
            "Na": (135, 145), "K": (3.5, 5.1), "Ca": (8.6, 10.2), "P": (2.5, 4.5), "Cr": (0.6, 1.3),
            "BUN": (8, 23), "AST": (0, 40), "ALT": (0, 40), "LDH": (0, 250), "CRP": (0, 0.5),
            "Albumin (알부민)": (3.5, 5.0), "Glucose": (70, 140), "TP": (6.0, 8.3), "UA": (3.5, 7.2),
            "TB": (0.2, 1.2), "BNP": (0, 100),
        }
        def fnum(x):
            try: return float(x)
            except: return None

        st.markdown("#### 🩸 수치별 해석")
        out_lines = []
        for k, v in vals.items():
            if v in (None, ""): continue
            x = fnum(v)
            if x is None: continue
            if k == "ANC":
                if x < 500: out_lines.append("ANC < 500: **중증 호중구감소증** — 발열 시 즉시 진료.")
                elif x < 1000: out_lines.append("ANC 500~999: **중등도 호중구감소증** — 감염 주의/외출·식품 위생.")
                elif x < 1500: out_lines.append("ANC 1000~1499: **경증 호중구감소증** — 위생/감염 주의.")
                else: out_lines.append("ANC 정상 범위.")
                continue
            lo, hi = REF.get(k, (None, None))
            disp = f"{label_ko(k)} = {x}"
            if lo is not None and x < lo:
                if k == "Hb": out_lines.append(disp + " ↓ — **빈혈 가능**(피로/어지럼).")
                elif k == "PLT": out_lines.append(disp + (" ↓ — **출혈 위험 高**(멍·코피 주의)." if x < 50 else " ↓ — **혈소판 감소**."))
                elif k == "Na": out_lines.append(disp + " ↓ — **저나트륨혈증** 가능.")
                elif k == "K": out_lines.append(disp + " ↓ — **저칼륨혈증** 가능(근력저하/부정맥).")
                elif k == "Ca": out_lines.append(disp + " ↓ — **저칼슘혈증** 가능(쥐남/저림).")
                elif k == "Albumin (알부민)": out_lines.append(disp + " ↓ — **영양상태/간·신장** 점검.")
                else: out_lines.append(disp + " ↓")
            elif hi is not None and x > hi:
                if k in ("AST","ALT"): out_lines.append(disp + " ↑ — **간수치 상승**(약물/간염 등) 추적 필요.")
                elif k == "CRP": out_lines.append(disp + " ↑ — **염증/감염 의심**.")
                elif k in ("BUN","Cr"): out_lines.append(disp + " ↑ — **신장 기능 점검**.")
                elif k == "K": out_lines.append(disp + " ↑ — **고칼륨혈증**(부정맥 위험) 주의.")
                elif k == "Na": out_lines.append(disp + " ↑ — **고나트륨혈증** 가능.")
                elif k == "Ca": out_lines.append(disp + " ↑ — **고칼슘혈증**(갈증/피로) 가능.")
                elif k == "LDH": out_lines.append(disp + " ↑ — **조직 손상/용혈** 시 상승.")
                else: out_lines.append(disp + " ↑")
            else:
                out_lines.append(disp + " : 정상 범위.")
        if out_lines:
            for line in out_lines:
                st.write("- " + line)
        else:
            st.caption("입력된 피수치가 없습니다.")

        # Food / lifestyle guide (core + lipid)
        def fv(v):
            try: return float(v)
            except: return None
        core = []
        alb = fv(vals.get("Albumin (알부민)"))
        k = fv(vals.get("K")); hb = fv(vals.get("Hb")); na = fv(vals.get("Na")); ca = fv(vals.get("Ca")); anc = fv(vals.get("ANC"))
        cancer_patient = (mode == "일반/암" and group in {"혈액암","고형암","육종","소아암","희귀암"}) or (len(selected_drugs) > 0)

        if alb is not None and alb < 3.5:
            core.append("알부민 낮음: 단백질 보충(살코기·생선·달걀·두부/콩) + 소량씩 자주 식사, 부종 있으면 짠 음식 줄이기.")
        if hb is not None and hb < 12.0:
            if cancer_patient:
                core.append("빈혈 경향: 철분 식품 섭취는 주치의와 상담 후 진행, 철분제·비타민 C 보충제는 임의 복용 금지.")
            else:
                core.append("빈혈 경향: 철분 식품(붉은살코기·간·시금치·콩류) + 비타민 C와 함께, 식사 전후 차/커피는 피하기.")
        if k is not None and k < 3.5:
            core.append("칼륨 낮음: 바나나·감자·토마토·키위·오렌지 등 칼륨 식품 보충(신장질환/약물 치료 중이면 의료진 지시 우선).")
        if k is not None and k > 5.1:
            core.append("칼륨 높음: 고칼륨 식품 과다 섭취 피하고 데치기 조리 활용.")
        if na is not None and na < 135:
            core.append("저나트륨: 물·무당 음료 과다섭취 줄이고 전해질 균형 유지(무리한 수분제한 금지).")
        if na is not None and na > 145:
            core.append("고나트륨: 가공식품·라면·젓갈·국물 줄이고 물 자주 마시기.")
        if ca is not None and ca < 8.6:
            core.append("칼슘 낮음: 우유·요거트·치즈/멸치·뼈째 생선·두부·케일 + 비타민 D 함께.")
        if ca is not None and ca > 10.2:
            core.append("칼슘 높음: 칼슘 보충제 과다 피하고 수분 충분히.")
        if anc is not None:
            if anc < 500:
                core.append("ANC 매우 낮음(<500): 완전가열 조리·위생 철저, 생고기/회/반숙란/비살균유/샐러드바 피하기.")
            elif anc < 1000:
                core.append("ANC 낮음(500~999): 위생관리·완전가열, 상온 보관 음식/뷔페 피하기.")
            elif anc < 1500:
                core.append("ANC 경계(1000~1499): 손씻기·세척·껍질 벗겨 섭취 등 위생 주의.")

        lipid = []
        tg = fv(vals.get("TG")); tc = fv(vals.get("총콜레스테롤")); hdl = fv(vals.get("HDL")); ldl = fv(vals.get("LDL"))
        if tg is not None and tg >= 200:
            lipid.append("중성지방(TG) 높음: 단 음료/과자 제한, 튀김·버터·마요네즈 등 기름진 음식 줄이기, 라면·가공식품(짠맛) 줄이기, 채소·등푸른생선·현미·잡곡·소량 견과류 권장.")
        if tc is not None and tc >= 240:
            lipid.append("총콜레스테롤 높음(≥240): 포화·트랜스지방 줄이기(가공육·튀김·제과), 가공치즈/크림 줄이기, 식이섬유(귀리·콩류·과일) 늘리기, 식물성 스테롤 도움.")
        if tc is not None and 200 <= tc <= 239:
            lipid.append("총콜레스테롤 경계역(200~239): 위 생활수칙 참고하여 식습관 개선 권고.")
        if hdl is not None and hdl < 40:
            lipid.append("HDL 낮음(<40): 규칙적 유산소·체중조절·채소/통곡물·견과류·생선 섭취 권장.")
        if ldl is not None and ldl >= 160:
            lipid.append("LDL 높음(≥160): 포화지방 제한·식이섬유/식물성 스테롤·등푸른생선 권장.")

        tips, seen = [], set()
        for t in core + lipid:
            if t and t not in seen:
                seen.add(t); tips.append(t)

        if cancer_patient:
            cmsg = "항암 환자: 철분제 + 비타민 C 보충은 치료/질환에 영향 가능 — 임의 복용 금지, 반드시 주치의와 상담."
            if cmsg not in seen:
                tips.append(cmsg)

        if tips:
            st.markdown("### 🥗 음식/생활 가이드")
            for t in tips:
                st.markdown("- " + t)

        # Pediatric interpretations
        ped_lines = []
        if mode == "소아(일상/호흡기)":
            def sidx(val):
                arr = ["없음","약간","보통","심함"]
                try: return arr.index(val)
                except: return 0
            t = ped_daily.get("temp"); rr = ped_daily.get("rr")
            if t is not None and float(t) >= 38.0:
                ped_lines.append("체온 ≥ 38℃: 해열·수분 보충, 지속/악화 시 진료 권고.")
            if sidx(ped_daily.get("cough")) >= 2 or sidx(ped_daily.get("throat")) >= 2:
                ped_lines.append("기침/인후통 '보통 이상': 수분·가습, 호흡곤란/열 지속 시 진료.")
            if rr is not None and float(rr) >= 40:
                ped_lines.append("호흡수 증가(≥40회/분): 호흡곤란 관찰 및 진료 고려.")
            if ped_daily.get("intake") is not None and float(ped_daily["intake"]) < 3:
                ped_lines.append("수분 섭취 적음(<3컵/일): 소량씩 자주 수분 보충.")

        if mode == "소아(감염질환)":
            name = ped_infect.get("name","")
            def sidx(val):
                arr = ["없음","약간","보통","심함"]
                try: return arr.index(val)
                except: return 0
            def f(v):
                try: return float(v)
                except: return None
            if name.startswith("AOM"):
                if sidx(ped_infect.get("귀 아파함")) >= 2:
                    ped_lines.append("중이염 의심: 귀 통증 '보통 이상' → 진통제/온찜질, 48시간 지속/고열 시 진료.")
            if name.startswith("Pharyngitis"):
                if sidx(ped_infect.get("인후통")) >= 2:
                    ped_lines.append("인후염 의심: 수분·가습, 연하곤란/호흡곤란 시 진료.")
            if name.startswith("URTI"):
                if sidx(ped_infect.get("기침")) >= 2:
                    ped_lines.append("감기 증상: 휴식·수분·가습, 호흡곤란/열 3일↑ 시 진료 고려.")
            if name.startswith("Gastroenteritis"):
                if f(ped_infect.get("설사 횟수")) and f(ped_infect.get("설사 횟수")) >= 5:
                    ped_lines.append("장염 의심: 탈수 위험 → 소량씩 ORS/수분 보충, 핏변·무반응 시 진료.")
            if name.startswith("UTI"):
                if sidx(ped_infect.get("배뇨통")) >= 2 or (f(ped_infect.get("빈뇨")) and f(ped_infect.get("빈뇨")) >= 8):
                    ped_lines.append("요로감염 의심: 배뇨통/빈뇨 → 진료 및 소변검사 고려.")
            if name.startswith("Rotavirus"):
                if (f(ped_infect.get("설사 횟수")) and f(ped_infect.get("설사 횟수")) >= 5) or sidx(ped_infect.get("탈수 의심")) >= 2:
                    ped_lines.append("로타 의심: 탈수 주의 → ORS/수분 보충, 소변 감소·무기력 시 진료.")
            if name.startswith("Adenovirus"):
                if sidx(ped_infect.get("인후통")) >= 2:
                    ped_lines.append("아데노바이러스 의심: 결막염/인후염 동반 가능 → 위생·증상 완화, 악화 시 진료.")
            if name.startswith("COVID-19"):
                if sidx(ped_infect.get("기침")) >= 2 or sidx(ped_infect.get("인후통")) >= 2:
                    ped_lines.append("코로나19 의심: 휴식·마스크·수분, 호흡곤란/탈수·고위험군은 진료.")
            if name.startswith("Influenza"):
                if (f(ped_infect.get("체온")) and f(ped_infect.get("체온")) >= 38.0) or sidx(ped_infect.get("근육통")) >= 2:
                    ped_lines.append("독감 의심: 초기 48시간 내 고위험군 항바이러스제 고려(의사 지시), 휴식·수분.")

        if ped_lines:
            st.markdown("### 🧒 소아 가이드")
            for ln in ped_lines:
                st.write("- " + ln)

    # Footer
    st.caption("© BloodMap — 참고용 도구")
