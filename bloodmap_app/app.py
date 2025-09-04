# -*- coding: utf-8 -*-
def main():
    from datetime import datetime, date
    import os, sys, importlib, re
    import streamlit as st

    # ---------- Config (safe import) ----------
    try:
        from . import config as cfg
    except Exception:
        try:
            cfg = importlib.import_module("bloodmap_app.config")
        except Exception:
            sys.path.append(os.path.dirname(__file__))
            import config as cfg  # type: ignore

    def _g(name, default):
        try: return getattr(cfg, name)
        except Exception: return default

    APP_TITLE   = _g("APP_TITLE", "BloodMap")
    PAGE_TITLE  = _g("PAGE_TITLE", "BloodMap")
    MADE_BY     = _g("MADE_BY", "")
    CAFE_LINK_MD= _g("CAFE_LINK_MD", "")
    FOOTER_CAFE = _g("FOOTER_CAFE", "")
    DISCLAIMER  = _g("DISCLAIMER", "")
    FONT_PATH_REG = _g("FONT_PATH_REG", "fonts/NanumGothic.ttf")

    # ---------- UI bootstrap ----------
    st.set_page_config(page_title=PAGE_TITLE, layout="centered")

    # CSS: remove +/- steppers from all number-like fields
    st.markdown(\"\"\"
    <style>
    /* Hide spin buttons in Chrome, Safari, Edge, Opera */
    input[type=number]::-webkit-outer-spin-button,
    input[type=number]::-webkit-inner-spin-button { -webkit-appearance: none; margin: 0; }
    /* Hide in Firefox */
    input[type=number] { -moz-appearance: textfield; }
    /* Tighten text inputs a bit */
    .stTextInput>div>div>input { font-variant-numeric: tabular-nums; }
    </style>
    \"\"\", unsafe_allow_html=True)

    # ---------- Label dictionary ----------
    LBL_WBC=_g("LBL_WBC","WBC"); LBL_Hb=_g("LBL_Hb","Hb"); LBL_PLT=_g("LBL_PLT","PLT"); LBL_ANC=_g("LBL_ANC","ANC")
    LBL_Ca=_g("LBL_Ca","Ca"); LBL_P=_g("LBL_P","P"); LBL_Na=_g("LBL_Na","Na"); LBL_K=_g("LBL_K","K")
    LBL_Alb=_g("LBL_Alb","Albumin (알부민)"); LBL_Glu=_g("LBL_Glu","Glucose"); LBL_TP=_g("LBL_TP","TP")
    LBL_AST=_g("LBL_AST","AST"); LBL_ALT=_g("LBL_ALT","ALT"); LBL_LDH=_g("LBL_LDH","LDH"); LBL_CRP=_g("LBL_CRP","CRP")
    LBL_Cr=_g("LBL_Cr","Cr"); LBL_UA=_g("LBL_UA","UA"); LBL_TB=_g("LBL_TB","TB"); LBL_BUN=_g("LBL_BUN","BUN"); LBL_BNP=_g("LBL_BNP","BNP")

    ORDER = _g("ORDER", [LBL_WBC, LBL_Hb, LBL_PLT, LBL_ANC, LBL_Na, LBL_K, LBL_Ca, LBL_P, LBL_Cr,
                         LBL_BUN, LBL_AST, LBL_ALT, LBL_LDH, LBL_CRP, LBL_Alb, LBL_Glu, LBL_TP, LBL_UA, LBL_TB, LBL_BNP])

    ANNO = {
        "WBC": "WBC (백혈구)","Hb": "Hb (혈색소)","PLT": "PLT (혈소판)","ANC": "ANC (절대중성구수)",
        "Na": "Na (나트륨)","K": "K (칼륨)","Ca": "Ca (칼슘)","P": "P (인)","Cr": "Cr (크레아티닌)","BUN": "BUN (혈중요소질소)",
        "AST": "AST (간수치)","ALT": "ALT (간세포 수치)","LDH": "LDH (젖산탈수소효소)","CRP": "CRP (염증수치)",
        "Albumin (알부민)": "Albumin (알부민/단백)","Glucose": "Glucose (혈당)","TP": "TP (총단백)",
        "UA": "UA (요산)","TB": "TB (총빌리루빈)","BNP": "BNP (심부전 표지)",
        "TG": "TG (중성지방, mg/dL)","총콜레스테롤": "총콜레스테롤 (mg/dL)","HDL": "HDL (고밀도지단백, mg/dL)","LDL": "LDL (저밀도지단백, mg/dL)",
    }
    def label_ko(s: str) -> str:
        return ANNO.get(s, s)

    # ---------- Utils (try import, but override num_input to remove steppers) ----------
    try:
        from .utils.inputs import num_input_generic as _num_input_generic_orig
    except Exception:
        _num_input_generic_orig = None

    def num_input_generic(label, key, decimals=1, as_int=False, placeholder=\"\"):
        \"\"\"Spinner-free numeric input using text_input.\")\"\"\"
        fmt = f\"{0:.{decimals}f}\" if decimals is not None else \"0\"
        ph = placeholder or f\"예: {fmt}\"
        txt = st.text_input(label, key=key, placeholder=ph)
        if txt is None or txt == \"\":
            return None
        # normalize
        s = str(txt).strip().replace(\",\", \"\")
        try:
            if as_int:
                return int(float(s))
            v = round(float(s), decimals)
            return v
        except Exception:
            st.caption(\"입력 예: \" + ph)
            return None

    # ---------- Simple fallback interpreter ----------
    REF = {
        \"WBC\": (4.0, 10.0), \"Hb\": (12.0, 17.0), \"PLT\": (150, 400), \"ANC\": (1500, None),
        \"Na\": (135, 145), \"K\": (3.5, 5.1), \"Ca\": (8.6, 10.2), \"P\": (2.5, 4.5), \"Cr\": (0.6, 1.3),
        \"BUN\": (8, 23), \"AST\": (0, 40), \"ALT\": (0, 40), \"LDH\": (0, 250), \"CRP\": (0, 0.5),
        \"Albumin (알부민)\": (3.5, 5.0), \"Glucose\": (70, 140), \"TP\": (6.0, 8.3), \"UA\": (3.5, 7.2),
        \"TB\": (0.2, 1.2), \"BNP\": (0, 100),
    }
    def _f(x):
        try: return float(x)
        except: return None

    def interpret_fallback(vals: dict):
        lines = []
        for k, v in vals.items():
            if v in (\"\", None): continue
            val = _f(v)
            if val is None: continue
            if k == \"ANC\":
                if val < 500: lines.append(\"ANC < 500: **중증 호중구감소증** — 발열 시 즉시 진료.\")
                elif val < 1000: lines.append(\"ANC 500~999: **중등도 호중구감소증** — 감염 주의/외출·식품 위생.\")
                elif val < 1500: lines.append(\"ANC 1000~1499: **경증 호중구감소증** — 위생/감염 주의.\")
                else: lines.append(\"ANC 정상 범위.\")
                continue
            lo, hi = REF.get(k, (None, None))
            disp = f\"{label_ko(k)} = {val}\"
            if lo is not None and val < lo:
                if k == \"Hb\": lines.append(f\"{disp} ↓ — **빈혈 가능**(피로/어지럼).\");
                elif k == \"PLT\": lines.append(f\"{disp} ↓ — **혈소판 감소**.\" if val >= 50 else f\"{disp} ↓ — **출혈 위험 高**(멍·코피 주의).\");
                elif k == \"Na\": lines.append(f\"{disp} ↓ — **저나트륨혈증** 가능.\");
                elif k == \"K\": lines.append(f\"{disp} ↓ — **저칼륨혈증** 가능(근력저하/부정맥).\");
                elif k == \"Ca\": lines.append(f\"{disp} ↓ — **저칼슘혈증** 가능(쥐남/저림).\");
                elif k == \"Albumin (알부민)\": lines.append(f\"{disp} ↓ — **영양상태/간·신장** 점검.\");
                else: lines.append(f\"{disp} ↓\");
            elif hi is not None and val > hi:
                if k in (\"AST\",\"ALT\"): lines.append(f\"{disp} ↑ — **간수치 상승**(약물/간염 등) 추적 필요.\");
                elif k == \"CRP\": lines.append(f\"{disp} ↑ — **염증/감염 의심**.\");
                elif k in (\"BUN\",\"Cr\"): lines.append(f\"{disp} ↑ — **신장 기능 점검**.\");
                elif k == \"K\": lines.append(f\"{disp} ↑ — **고칼륨혈증**(부정맥 위험) 주의.\");
                elif k == \"Na\": lines.append(f\"{disp} ↑ — **고나트륨혈증** 가능.\");
                elif k == \"Ca\": lines.append(f\"{disp} ↑ — **고칼슘혈증**(갈증/피로) 가능.\");
                elif k == \"LDH\": lines.append(f\"{disp} ↑ — **조직 손상/용혈** 시 상승.\");
                else: lines.append(f\"{disp} ↑\");
            else:
                lines.append(f\"{disp} : 정상 범위.\")
        return lines

    # ---------- Header + banner ----------
    st.title(APP_TITLE); st.markdown(MADE_BY); st.markdown(CAFE_LINK_MD)
    st.warning(\"\"\"⚠️ 본 수치 해석은 참고용 도구이며, 개발자와 무관합니다.

- 철분제와 비타민 C 조합은 항암 치료 중인 환자에게 해로울 수 있으므로 반드시 주치의와 상담 후 복용 여부를 결정해야 합니다.
- BloodMap은 개인정보를 수집하지 않으며, 입력 정보는 저장되지 않습니다.\"\"\")

    # ---------- Section 1: Meta ----------
    st.divider()
    st.header(\"1️⃣ 환자/암·소아 정보\")
    # Force 3 columns (2:1:1) as in screenshot
    c1,c2,c3 = st.columns([2,1,1])
    with c1:
        nickname = st.text_input(\"별명\", placeholder=\"예: 홍길동\")
    with c2:
        pin = st.text_input(\"PIN(4자리)\", max_chars=4, placeholder=\"1234\")
    with c3:
        test_date = st.date_input(\"검사 날짜\", value=date.today())
    mode = st.selectbox(\"모드 선택\", [\"일반/암\",\"소아(일상/호흡기)\",\"소아(감염질환)\"])

    group = cancer_key = cancer_label = None
    selected_drugs = []

    # ---------- Cancer section (manual drug select) ----------
    if mode == \"일반/암\":
        group = st.selectbox(\"암 그룹 선택\", [\"미선택/일반\",\"혈액암\",\"고형암\",\"육종\",\"소아암\",\"희귀암\"])
        if group == \"혈액암\":
            cancer_label = st.selectbox(\"혈액암 (진단명)\", [\"AML (급성 골수성 백혈병)\",\"APL (급성 전골수구성 백혈병)\",\"ALL (급성 림프모구성 백혈병)\",\"CML (만성 골수성 백혈병)\",\"CLL (만성 림프구성 백혈병)\"])
        elif group == \"고형암\":
            cancer_label = st.selectbox(\"고형암 (진단명)\", [\"폐암(Lung cancer)\",\"유방암(Breast cancer)\",\"위암(Gastric cancer)\",\"대장암(Cololoractal cancer)\",\"간암(HCC)\",\"췌장암(Pancreatic cancer)\",\"담도암(Cholangiocarcinoma)\",\"자궁내막암(Endometrial cancer)\",\"구강암/후두암\",\"피부암(흑색종)\",\"신장암(RCC)\",\"갑상선암\",\"난소암\",\"자궁경부암\",\"전립선암\",\"뇌종양(Glioma)\",\"식도암\",\"방광암\"])        
        elif group == \"육종\":
            cancer_label = st.selectbox(\"육종 (진단명)\", [\"연부조직육종 (STS)\",\"골육종 (Osteosarcoma)\",\"유잉육종 (Ewing sarcoma)\",\"평활근육종 (Leiomyosarcoma)\",\"지방육종 (Liposarcoma)\",\"횡문근육종 (Rhabdomyosarcoma)\",\"활막육종 (Synovial sarcoma)\"])
        elif group == \"소아암\":
            cancer_label = st.selectbox(\"소아암 (진단명)\", [\"Neuroblastoma\",\"Wilms tumor\"])
        elif group == \"희귀암\":
            cancer_label = st.selectbox(\"희귀암 (진단명)\", [\"담낭암(Gallbladder cancer)\",\"부신암(Adrenal cancer)\",\"망막모세포종(Retinoblastoma)\",\"흉선종/흉선암(Thymoma/Thymic carcinoma)\",\"신경내분비종양(NET)\",\"간모세포종(Hepatoblastoma)\",\"비인두암(NPC)\",\"GIST\"])

        # Drug candidates (union by group)
        heme = [\"ARA-C\",\"Daunorubicin\",\"Idarubicin\",\"Cyclophosphamide\",\"Etoposide\",\"Fludarabine\",\"Hydroxyurea\",\"MTX\",\"ATRA\",\"G-CSF\",\"6-MP\",\"Imatinib\",\"Dasatinib\",\"Nilotinib\",\"Vincristine\",\"Asparaginase\",\"Topotecan\"]
        solid = [\"Cisplatin\",\"Carboplatin\",\"Paclitaxel\",\"Docetaxel\",\"Gemcitabine\",\"Pemetrexed\",\"Oxaliplatin\",\"Irinotecan\",\"5-FU\",\"Capecitabine\",\"Trastuzumab\",\"Bevacizumab\",\"Sorafenib\",\"Lenvatinib\",\"Gefitinib\",\"Erlotinib\",\"Osimertinib\",\"Alectinib\",\"Pembrolizumab\",\"Nivolumab\",\"Temozolomide\"]
        sarcoma = [\"Doxorubicin\",\"Ifosfamide\",\"Pazopanib\",\"Gemcitabine\",\"Docetaxel\",\"Vincristine\",\"Cyclophosphamide\",\"Etoposide\",\"Cisplatin\",\"MTX\"]
        pool = heme + solid + sarcoma
        drug_search = st.text_input(\"🔍 항암제 검색(영문/한글)\", key=\"drug_search\")
        show_drugs = [d for d in sorted(set(pool)) if (not drug_search) or (drug_search.lower() in d.lower())]
        selected_drugs = st.multiselect(\"항암제 선택\", show_drugs, default=[])
        for d in selected_drugs:
            _ = num_input_generic(f\"{d} - 용량/알약\", key=f\"med_{d}\", decimals=1)

        st.info(\"⚠️ **항암 환자 보충제 주의**: 철분제·비타민 C 등 보충제는 치료/질환에 영향 가능 → **임의 복용 금지, 반드시 주치의와 상담**.\")

    # ---------- Section 2: Labs ----------
    st.divider()
    hide_default = mode.startswith(\"소아\")
    open_labs = st.checkbox(\"🧪 피수치 입력 열기\", value=not hide_default) if hide_default else True

    vals = {}
    if open_labs:
        st.header(\"2️⃣ 기본 혈액 검사 수치 (입력한 값만 해석)\")
        for name in ORDER:
            decimals = 2 if name==LBL_CRP else 1
            vals[name] = num_input_generic(label_ko(name), key=f\"v_{name}\", decimals=decimals)

    # Special: Lipid panel
    st.markdown(\"### 🧪 특수검사\")
    if st.checkbox(\"지질패널 (TG/총콜/HDL/LDL)\", value=True):
        c1,c2,c3,c4 = st.columns(4)
        with c1: vals['TG'] = num_input_generic(label_ko(\"TG\"), key=\"lip_TG\", decimals=0)
        with c2: vals['총콜레스테롤'] = num_input_generic(label_ko(\"총콜레스테롤\"), key=\"lip_TCHOL\", decimals=0)
        with c3: vals['HDL'] = num_input_generic(label_ko(\"HDL\"), key=\"lip_HDL\", decimals=0)
        with c4: vals['LDL'] = num_input_generic(label_ko(\"LDL\"), key=\"lip_LDL\", decimals=0)

    # ---------- Run ----------
    st.divider()
    run = st.button(\"🧠 해석하기 / 결과 생성\", use_container_width=True)
    if run:
        st.subheader(\"📋 해석 결과\")

        is_cancer = (mode == \"일반/암\") and (group in {\"혈액암\",\"고형암\",\"육종\",\"소아암\",\"희귀암\"})
        if selected_drugs: is_cancer = True

        # 수치별 해석
        st.markdown(\"#### 🩸 수치별 해석\")
        lines = interpret_fallback(vals)
        for line in lines: st.write(\"- \"+line)

        # 음식/생활 가이드
        def _fv(v):
            try: return float(v)
            except: return None

        food = []
        alb = _fv(vals.get(\"Albumin (알부민)\"))
        k   = _fv(vals.get(\"K\"))
        hb  = _fv(vals.get(\"Hb\"))
        na  = _fv(vals.get(\"Na\"))
        ca  = _fv(vals.get(\"Ca\"))
        anc = _fv(vals.get(\"ANC\"))

        if alb is not None and alb < 3.5:
            food.append(\"알부민 낮음: **단백질 보충**(살코기·생선·달걀·두부/콩) + **소량씩 자주 식사**, 부종 있으면 **짠 음식 줄이기**.\")
        if hb is not None and hb < 12.0:
            if is_cancer:
                food.append(\"빈혈 경향: **철분 식품**(붉은살코기·간·시금치·콩류) 섭취는 **주치의와 상담 후** 진행, **철분제·비타민 C 보충제는 임의 복용 금지**.\")
            else:
                food.append(\"빈혈 경향: **철분 식품**(붉은살코기·간·시금치·콩류) + **비타민 C**와 함께, 식사 전후 **차/커피는 피하기**.\")
        if k is not None and k < 3.5:
            food.append(\"칼륨 낮음: 바나나·감자·토마토·키위·오렌지 등 **칼륨 식품 보충** *(신장질환/약물은 의료진 지시 우선)*.\")
        if k is not None and k > 5.1:
            food.append(\"칼륨 높음: 바나나·코코넛워터·감자·시금치 등 **고칼륨 식품 과다 섭취 피하기**, **데치기 조리** 활용.\")
        if na is not None and na < 135:
            food.append(\"저나트륨: **물·무당 음료 과다섭취 줄이기**, 전해질 균형 유지(의료진 지시 없는 **무리한 수분제한은 금지**).\")
        if na is not None and na > 145:
            food.append(\"고나트륨: **가공식품·라면·젓갈·국물** 줄이고 **물 자주 마시기**.\")
        if ca is not None and ca < 8.6:
            food.append(\"칼슘 낮음: 우유·요거트·치즈/멸치·뼈째 생선·두부·케일 + **비타민 D** 함께.\")
        if ca is not None and ca > 10.2:
            food.append(\"칼슘 높음: **칼슘 보충제 과다 피하기**, **수분 충분히**.\")
        if anc is not None:
            if anc < 500:
                food.append(\"ANC 매우 낮음(<500): **완전가열 조리·위생 철저**, 생고기/회/반숙란/비살균유/샐러드바 **피하기**.\")
            elif anc < 1000:
                food.append(\"ANC 낮음(500~999): 위생관리·완전가열, **상온 보관 음식/뷔페 피하기**.\")
            elif anc < 1500:
                food.append(\"ANC 경계(1000~1499): **위생 주의**(손씻기·세척·껍질 벗겨 섭취).\" )

        tg=_fv(vals.get(\"TG\")); tc=_fv(vals.get(\"총콜레스테롤\")); hdl=_fv(vals.get(\"HDL\")); ldl=_fv(vals.get(\"LDL\"))
        if tg is not None and tg >= 200:
            food.append(\"중성지방(TG) 높음: 단 음료/과자 제한 · 튀김/버터/마요네즈 등 기름진 음식 줄이기 · 라면/가공식품(짠맛) 줄이기 · 채소/등푸른생선/현미·잡곡/소량 견과류 권장\")
        if tc is not None and tc >= 240:
            food.append(\"총콜레스테롤 높음(≥240): 포화·트랜스지방 줄이기(가공육·튀김·제과) · 가공치즈/크림 줄이기 · 식이섬유(귀리·콩류·과일) 늘리기 · 식물성 스테롤 도움\")
        if tc is not None and 200 <= tc <= 239:
            food.append(\"총콜레스테롤 경계역(200~239): 위 생활수칙을 참고하여 식습관 개선 권고\")
        if hdl is not None and hdl < 40:
            food.append(\"HDL 낮음(<40): 규칙적 유산소·체중조절·채소/통곡물·견과류·생선 섭취 권장\")
        if ldl is not None and ldl >= 160:
            food.append(\"LDL 높음(≥160): 포화지방 제한·식이섬유/식물성 스테롤·등푸른생선 권장\")

        if is_cancer:
            food.append(\"⚠️ 항암 환자: **철분제 + 비타민 C 보충**은 치료/질환에 영향 가능 — **임의 복용 금지, 반드시 주치의와 상담**.\")

        if food:
            st.markdown(\"### 🥗 음식/생활 가이드\")
            seen=set()
            for tip in food:
                if tip not in seen:
                    seen.add(tip); st.markdown(\"- \"+tip)

    st.caption(FOOTER_CAFE); st.markdown(\"> \"+DISCLAIMER)
