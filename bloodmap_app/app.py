# -*- coding: utf-8 -*-
import os, sys, traceback
import streamlit as st

PKG_DIR = os.path.dirname(__file__)
if PKG_DIR not in sys.path:
    sys.path.insert(0, PKG_DIR)

from utils import user_key, init_state
from utils.inputs import collect_basic_inputs
from utils.interpret import interpret_labs, status_color, interpret_qual, interpret_quant, diuretic_checks
from utils.reports import build_markdown_report, to_txt, to_pdf
from utils.counter import bump_count
from utils.storage import register_user, append_record, get_records
from data.drugs import list_diagnoses, get_default_drugs, get_targeted, common_antibiotics
from data.drug_info import get_info
from data.foods import foods_for, ANC_LOW_GUIDE

# --- Foods helper ---
def _food_block(labs: dict):
    shown = False
    if labs.get('Albumin', 4.0) < 3.5:
        st.write('### 음식 추천 (알부민 낮음)')
        st.write(', '.join(foods_for('알부민 낮음')))
        shown = True
    if 'K' in labs and labs['K'] < 3.5:
        st.write('### 음식 추천 (칼륨 낮음)')
        st.write(', '.join(foods_for('칼륨 낮음')))
        shown = True
    if 'Hb' in labs and labs['Hb'] < 10:
        st.write('### 음식 추천 (Hb 낮음)')
        st.write(', '.join(foods_for('Hb 낮음')))
        shown = True
    if 'Na' in labs and labs['Na'] < 135:
        st.write('### 음식 추천 (나트륨 낮음)')
        st.write(', '.join(foods_for('나트륨 낮음')))
        shown = True
    if 'Ca' in labs and labs['Ca'] < 8.6:
        st.write('### 음식 추천 (칼슘 낮음)')
        st.write(', '.join(foods_for('칼슘 낮음')))
        shown = True
    if 'ANC' in labs and labs['ANC'] < 500:
        st.info('호중구 낮음 가이드: ' + ' · '.join(ANC_LOW_GUIDE))
        shown = True
    return shown

from data import drugs as drugs_table

APP_NAME = "BloodMap 피수치 가이드 v3.14+ (지침 반영)"
DISCLAIMER = "본 도구는 보호자의 이해를 돕기 위한 참고용 정보이며, 모든 의학적 판단은 의료진의 판단을 따르세요."

# --- UI helpers ---
CSS = """
<style>
.badge{display:inline-block;padding:2px 8px;border-radius:8px;font-size:0.85rem}
.badge.ok{background:#10b98122;color:#10b981;border:1px solid #10b98155}
.badge.warn{background:#f59e0b22;color:#f59e0b;border:1px solid #f59e0b55}
.badge.danger{background:#ef444422;color:#ef4444;border:1px solid #ef444455}
small.muted{color:#9aa}
</style>
"""

def sidebar_user():
    st.sidebar.header("사용자")
    nickname = st.sidebar.text_input("별명")
    pin = st.sidebar.text_input("PIN(4자리)", max_chars=4)
    ukey = user_key(nickname, pin)
    colA, colB = st.sidebar.columns([1,1])
    with colA:
        if st.button("등록/확인", use_container_width=True):
            new = register_user(ukey)
            st.sidebar.success("등록 완료" if new else "이미 등록된 조합입니다(중복 저장 불가).")
    st.sidebar.caption(f"식별키: {ukey}")
    return ukey

def render_special_tests():
    st.subheader("특수검사")
    with st.expander("정성검사 (+/++/+++)", expanded=False):
        for name in ["단백뇨", "혈뇨", "요당", "잠혈"]:
            val = st.selectbox(name, ["", "+", "++", "+++"], key=f"qual_{name}")
            if val:
                (n, v, level, hint) = interpret_qual(name, val)
                st.markdown(f"- **{n}**: {v} → <span class='badge {status_color(level)}'>{level}</span> · {hint}", unsafe_allow_html=True)
    with st.expander("정량검사 (숫자입력)", expanded=False):
        qnums = {}
        for (label, key) in [("C3","C3"),("C4","C4"),("TG","TG"),("HDL","HDL"),("LDL","LDL"),
                             ("적혈구","적혈구"),("백혈구","백혈구")]:
            val = st.text_input(f"{label}", key=f"quant_{key}")
            if val.strip():
                try:
                    qnums[key] = float(val)
                except: st.warning(f"{label}: 숫자만 입력")
        if qnums:
            for k, v in qnums.items():
                (n, val, level, hint) = interpret_quant(k, v)
                st.markdown(f"- **{n}**: {val} → <span class='badge {status_color(level)}'>{level}</span> · {hint}", unsafe_allow_html=True)

def cancer_mode(ukey: str):
    st.header("🧬 암 진단 모드")
    from data import drugs as D

    cols = st.columns([1,1,1])
    group = cols[0].selectbox("암 카테고리", ["혈액암", "림프종", "고형암", "육종", "희귀암"])

    # Show diagnosis list next to category (helper text)
    if group == "혈액암":
        cols[0].caption("진단: " + ", ".join(D.list_diagnoses("혈액암")))
    elif group == "림프종":
        cols[0].caption("진단: " + ", ".join(D.list_diagnoses("림프종")))

    # Diagnosis picker (grouped UI for solid)
    if group == "고형암":
        organ = cols[1].selectbox("고형암 분류(장기)", D.list_solid_groups())
        dx_list = D.list_solid_by_group(organ)
        dx = cols[2].selectbox("진단명", dx_list if dx_list else D.list_diagnoses("고형암"))
    else:
        dx = cols[1].selectbox("진단명", D.list_diagnoses(group))
        cols[2].markdown("")

    biomarker = st.text_input("Biomarker(선택): EGFR / ALK / ROS1 / HER2 / RAS WT / BRAF V600E / MSI-H / FGFR2 / RET / NTRK 등")
    st.caption(f"선택: **[{group}] - [{dx}]**")

    # Sections toggles
    show_chemo = st.checkbox("항암제/레짐 보기", value=True)
    show_targ = st.checkbox("표적치료제 보기 (바이오마커 입력 시)", value=False)
    show_abx  = st.checkbox("항생제 보기", value=False)

    # Drugs
    if show_chemo:
        st.subheader("항암제/레짐")
        for d in D.get_default_drugs(group, dx):
            info = get_info(d)
            if info:
                st.markdown(f"- **{info['ko']}** ({d}) · _기전_: {info['moa']} · _주의_: {info['warn']}")
            else:
                st.markdown(f"- {d}")

    if show_targ and biomarker:
        st.subheader("표적치료제 (Biomarker 기반)")
        for d in D.get_targeted(group, dx, biomarker):
            info = get_info(d) or {}
            nm = info.get("ko", d)
            st.markdown(f"- **{nm}** ({d}) · _기전_: {info.get('moa','N/A')} · _주의_: {info.get('warn','N/A')}")

    if show_abx:
        st.subheader("항생제 (암환자에서 자주 사용)")
        for d in D.common_antibiotics():
            st.markdown(f"- {d}")

    # Labs - always visible
    st.subheader("피수치 입력")
    labs = collect_basic_inputs()
    on_diur = st.checkbox("이뇨제 복용 중", value=False)
    items = []
    if labs and st.button('해석하기', key='btn_cancer_interpret', use_container_width=True):
        items = interpret_labs(labs)
        for k, v, level, hint in items:
            st.markdown(f"- **{k}**: {v} → <span class='badge {status_color(level)}'>{level}</span> · {hint}", unsafe_allow_html=True)
        # Diuretic logic
        tips = diuretic_checks(labs, on_diur)
        for t in tips:
            st.warning(t)
        _food_block(labs)

    render_special_tests()

    # Foods (examples)
    if labs.get("Albumin", 4.0) < 3.5:
        st.write("### 음식 추천 (알부민 낮음)")
        st.write(", ".join(foods_for("알부민 낮음")))
    if "ANC" in labs and labs["ANC"] < 500:
        st.info("호중구 낮음 가이드: " + " · ".join(ANC_LOW_GUIDE))

    # Save & report
    if st.button("이번 결과 저장", use_container_width=True) and labs:
        append_record(ukey, labs)
        st.success("저장 완료 (별명+PIN 기준).")
    if items:
        md = build_markdown_report(ukey, items)
        col1, col2, col3 = st.columns(3)
        with col1: st.download_button("보고서(.md)", md, file_name="bloodmap_report.md")
        with col2: st.download_button("보고서(.txt)", md.replace("**","").replace("# ",""), file_name="bloodmap_report.txt")
        with col3:
            try:
                pdf_path = os.path.join(PKG_DIR, "data", "report.pdf")
                path = to_pdf(md, pdf_path)
                with open(path, "rb") as f:
                    st.download_button("보고서(.pdf)", f, file_name="bloodmap_report.pdf")
            except Exception:
                st.caption("PDF: 폰트 미배치 등으로 실패 시 .md/.txt를 사용하세요.")


def ped_mode(ukey: str):
    st.header("📌 소아 일상/질환 모드")
    w = st.number_input("체중 (kg)", min_value=0.0, step=0.5)
    from data.ped import calc_antipyretic_dose, TEMP_GUIDE
    if w > 0:
        d1 = calc_antipyretic_dose(w, "acetaminophen")
        d2 = calc_antipyretic_dose(w, "ibuprofen")
        st.subheader("해열제 자동 계산")
        st.write(f"- 아세트아미노펜: 1회 권장 **{d1[0]} mg**, 1일 최대 **{d1[1]}회** ({d1[2]})")
        st.write(f"- 이부프로펜: 1회 권장 **{d2[0]} mg**, 1일 최대 **{d2[1]}회** ({d2[2]})")
    st.subheader("체온 구간 가이드")
    for g, txt in TEMP_GUIDE:
        st.markdown(f"- **{g}℃**: {txt}")
    if st.checkbox("피수치 입력 보이기 (토글)"):
        labs = collect_basic_inputs()
        if labs and st.button('해석하기', key='btn_ped_interpret', use_container_width=True):
            items = interpret_labs(labs)
            for k, v, level, hint in items:
                st.markdown(f"- **{k}**: {v} → <span class='badge {status_color(level)}'>{level}</span> · {hint}", unsafe_allow_html=True)
            _food_block(labs)
    st.caption("항암제는 소아 모드에서 숨김 처리됩니다.")

def trends_page(ukey: str):
    import matplotlib.pyplot as plt
    st.header("📈 수치 추이 (별명+PIN 기준)")
    recs = get_records(ukey)
    if not recs:
        st.info("저장된 기록이 없습니다.")
        return
    # Extract series
    keys = ["WBC","Hb","PLT","CRP","ANC"]
    for k in keys:
        vals = []
        for r in recs:
            v = r["labs"].get(k)
            if v is not None:
                vals.append(float(v))
            else:
                vals.append(None)
        if all(v is None for v in vals):
            continue
        xs, ys = [], []
        for i, v in enumerate(vals, start=1):
            if v is not None:
                xs.append(i); ys.append(v)
        fig = plt.figure()
        plt.plot(xs, ys, marker='o')
        plt.title(k)
        plt.xlabel("회차"); plt.ylabel(k)
        st.pyplot(fig)

def main():
    st.set_page_config(page_title=APP_NAME, layout="centered")
    st.markdown(CSS, unsafe_allow_html=True)
    st.title(APP_NAME)
    try:
        bump_count()
    except Exception:
        pass
    ukey = sidebar_user()

    tab1, tab2, tab3 = st.tabs(["소아 (일상/질환)", "암 (진단/치료)", "기록/그래프"])
    with tab1:
        ped_mode(ukey)
    with tab2:
        cancer_mode(ukey)
    with tab3:
        trends_page(ukey)

    st.markdown("> " + DISCLAIMER)

if __name__ == "__main__":
    main()
