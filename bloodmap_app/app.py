# app.py — Spec-complete: 5-group diagnosis with KO/EN display, chemo mapping, editable meds, .md export
import datetime as _dt
import streamlit as st

# ---- Safe banner import (package/flat/no-op) ----
try:
    from branding import render_deploy_banner  # flat
except Exception:
    try:
        from .branding import render_deploy_banner  # package
    except Exception:
        def render_deploy_banner(*args, **kwargs):
            return None

st.set_page_config(page_title="Bloodmap", layout="wide")
st.title("Bloodmap")
render_deploy_banner("https://bloodmap.streamlit.app/", "제작: Hoya/GPT · 자문: Hoya/GPT")

# ---------- Helpers ----------
def wkey(name: str) -> str:
    try:
        who = st.session_state.get("key", "guest")
        mode_now = st.session_state.get("mode", "main")
        return f"{mode_now}:{who}:{name}"
    except Exception:
        return name

def enko(en: str, ko: str) -> str:
    return f"{en} / {ko}" if ko else en

# ---------- Groups (list-based, easily extendable) ----------
GROUPS = {
    "🩸 혈액암 (Leukemia)": [
        ("Acute Lymphoblastic Leukemia (ALL)", "급성 림프모구 백혈병"),
        ("Acute Myeloid Leukemia (AML)", "급성 골수성 백혈병"),
        ("Acute Promyelocytic Leukemia (APL)", "급성 전골수성 백혈병"),
        ("Chronic Myeloid Leukemia (CML)", "만성 골수성 백혈병"),
        ("Other Leukemias", "기타 백혈병"),
    ],
    "🧬 림프종 (Lymphoma)": [
        ("Hodgkin Lymphoma", "호지킨 림프종"),
        ("Diffuse Large B-cell Lymphoma (DLBCL)", "미만성 거대 B세포 림프종"),
        ("Burkitt Lymphoma", "버킷 림프종"),
        ("T-lymphoblastic Lymphoma (T-LBL)", "T-림프모구 림프종"),
        ("Anaplastic Large Cell Lymphoma (ALCL)", "역형성 대세포 림프종"),
        ("Primary Mediastinal B-cell Lymphoma (PMBCL)", "원발성 종격동 B세포 림프종"),
        ("Peripheral T-cell Lymphoma (PTCL)", "말초 T세포 림프종"),
        ("Other NHL", "기타 비호지킨 림프종"),
    ],
    "🧠 고형암 (Solid Tumors)": [
        ("Wilms Tumor", "윌름스 종양(신장)"),
        ("Neuroblastoma", "신경모세포종"),
        ("Hepatoblastoma", "간모세포종"),
        ("Retinoblastoma", "망막모세포종"),
        ("Germ Cell Tumor", "생식세포 종양"),
        ("Medulloblastoma", "수모세포종(소뇌)"),
        ("Craniopharyngioma", "두개인두종"),
        ("Other Solid Tumors", "기타 고형 종양"),
    ],
    "🦴 육종 (Sarcoma)": [
        ("Osteosarcoma", "골육종"),
        ("Ewing Sarcoma", "유잉육종"),
        ("Rhabdomyosarcoma", "횡문근육종"),
        ("Other Sarcomas", "기타 연부조직/골 육종"),
    ],
    "🧩 희귀암 및 기타": [
        ("Langerhans Cell Histiocytosis (LCH)", "랜게르한스세포 조직구증"),
        ("Juvenile Myelomonocytic Leukemia (JMML)", "소아 골수단핵구성 백혈병"),
        ("Other Rare", "기타 희귀 아형"),
    ],
}

# ---------- Chemo map (editable suggestions) ----------
CHEMO_MAP = {
    "Acute Lymphoblastic Leukemia (ALL)": [
        "6-Mercaptopurine (메르캅토퓨린)",
        "Methotrexate (메토트렉세이트)",
        "Cytarabine/Ara-C (시타라빈)",
        "Vincristine (빈크리스틴)",
    ],
    "Acute Promyelocytic Leukemia (APL)": [
        "ATRA (트레티노인/베사노이드)",
        "Arsenic Trioxide (아르세닉 트리옥사이드)",
        "Methotrexate (메토트렉세이트)",
        "6-Mercaptopurine (메르캅토퓨린)",
    ],
    "Acute Myeloid Leukemia (AML)": [
        "Cytarabine/Ara-C (시타라빈)",
        "Daunorubicin (다우노루비신)",
        "Idarubicin (이다루비신)",
    ],
    "Chronic Myeloid Leukemia (CML)": [
        "Imatinib (이마티닙)",
        "Dasatinib (다사티닙)",
        "Nilotinib (닐로티닙)",
    ],
    "Hodgkin Lymphoma": [
        "ABVD (도옥소루비신/블레오마이신/빈블라스틴/다카바진)",
    ],
    "Diffuse Large B-cell Lymphoma (DLBCL)": [
        "R-CHOP (리툭시맙+CHOP)",
        "R-EPOCH (리툭시맙+EPOCH)",
        "Polatuzumab-based (폴라투주맙 조합)",
    ],
    "Burkitt Lymphoma": [
        "CODOX-M/IVAC (코독스-엠/아이백)",
    ],
    "T-lymphoblastic Lymphoma (T-LBL)": [
        "ALL-like Protocols (ALL 유사 프로토콜)",
    ],
    "Anaplastic Large Cell Lymphoma (ALCL)": [
        "CHOP-like (CHOP 유사)",
        "Brentuximab Vedotin (브렌툭시맵 베도틴)",
    ],
    "Primary Mediastinal B-cell Lymphoma (PMBCL)": [
        "DA-R-EPOCH (용량조절형 R-EPOCH)",
    ],
    "Peripheral T-cell Lymphoma (PTCL)": [
        "CHOP-like (CHOP 유사)",
        "Pralatrexate (프랄라트렉세이트)",
    ],
    "Wilms Tumor": [
        "Vincristine (빈크리스틴)",
        "Dactinomycin (닥티노마이신)",
        "Doxorubicin (독소루비신)",
    ],
    "Neuroblastoma": [
        "Cyclophosphamide (사이클로포스파마이드)",
        "Topotecan (토포테칸)",
        "Cisplatin (시스플라틴)",
        "Etoposide (에토포사이드)",
    ],
    "Hepatoblastoma": [
        "Cisplatin (시스플라틴)",
        "Doxorubicin (독소루비신)",
    ],
    "Retinoblastoma": [
        "Carboplatin (카보플라틴)",
        "Etoposide (에토포사이드)",
        "Vincristine (빈크리스틴)",
    ],
    "Germ Cell Tumor": [
        "BEP (블레오마이신/에토포사이드/시스플라틴)",
    ],
    "Medulloblastoma": [
        "Cisplatin (시스플라틴)",
        "Vincristine (빈크리스틴)",
        "Cyclophosphamide (사이클로포스파마이드)",
    ],
    "Craniopharyngioma": [
        "Interferon-α (인터페론 알파)",
        "BRAF/MEK inhibitors (BRAF/MEK 억제제)",
    ],
    "Osteosarcoma": [
        "MAP (메토트렉세이트/독소루비신/시스플라틴)",
    ],
    "Ewing Sarcoma": [
        "VDC/IE (빈크리스틴/독소루비신/사이클로포스파마이드 + 이포스파마이드/에토포사이드)",
    ],
    "Rhabdomyosarcoma": [
        "VAC (빈크리스틴/액티노마이신 D/사이클로포스파마이드)",
    ],
    "Langerhans Cell Histiocytosis (LCH)": [
        "Vinblastine (빈블라스틴)",
        "Prednisone (프레드니손)",
    ],
    "Juvenile Myelomonocytic Leukemia (JMML)": [
        "Azacitidine (아자시티딘)",
        "Stem cell transplant (조혈모세포 이식)",
    ],
}

# ---------- Sidebar (profile) ----------
with st.sidebar:
    st.header("프로필")
    st.session_state["key"] = st.text_input("별명#PIN", value=st.session_state.get("key", "guest"), key=wkey("user_key"))
    st.session_state["mode"] = st.radio("모드", ["일반", "암", "소아"], index=1, key=wkey("mode_sel"))

# ---------- Main: 5 group tabs ----------
tabs = st.tabs(list(GROUPS.keys()))
for i, (grp, dx_list) in enumerate(GROUPS.items()):
    with tabs[i]:
        st.subheader(grp)
        labels = [enko(en, ko) for en, ko in dx_list]
        dx_choice = st.selectbox("진단명을 선택하세요", labels, key=wkey(f"dx_sel_{i}"))
        idx = labels.index(dx_choice)
        en_dx, ko_dx = dx_list[idx]

        st.caption("자동 추천 항암제(수정/추가 가능)")
        suggestions = CHEMO_MAP.get(en_dx, [])
        picked = st.multiselect("항암제를 선택/추가하세요 (영문/한글 병기)", suggestions, default=suggestions, key=wkey(f"meds_{i}"))

        extra = st.text_input("추가 항암제(쉼표로 구분)", key=wkey(f"extra_{i}"))
        if extra.strip():
            more = [x.strip() for x in extra.split(",") if x.strip()]
            # dedup keep order
            seen, merged = set(), []
            for x in picked + more:
                if x not in seen:
                    seen.add(x); merged.append(x)
            picked = merged

        colL, colR = st.columns([1,1])
        with colL:
            if st.button("이 선택을 보고서에 사용", key=wkey(f"use_{i}")):
                st.session_state["report_group"] = grp
                st.session_state["report_dx_en"] = en_dx
                st.session_state["report_dx_ko"] = ko_dx
                st.session_state["report_meds"] = picked
                st.success("보고서에 반영되었습니다.")
        with colR:
            st.write(f"선택 요약: **{enko(en_dx, ko_dx)}** — {', '.join(picked) if picked else '(없음)'}")

# ---------- Report (.md) ----------
st.markdown("---")
st.subheader("📄 보고서 내보내기 (.md)")

def build_report_md() -> str:
    grp = st.session_state.get("report_group")
    en_dx = st.session_state.get("report_dx_en")
    ko_dx = st.session_state.get("report_dx_ko")
    meds = st.session_state.get("report_meds", [])

    if not (grp and en_dx):
        return "# Bloodmap Report\n\n선택된 진단이 없습니다. 상단 탭에서 선택 후 '이 선택을 보고서에 사용'을 눌러주세요.\n"

    lines = []
    lines.append("# Bloodmap Report")
    lines.append(f"**암종 그룹**: {grp}")
    lines.append(f"**진단명**: {enko(en_dx, ko_dx)}")
    lines.append("")
    lines.append("## 항암제 요약")
    if meds:
        for m in meds:
            lines.append(f"- {m}")
    else:
        lines.append("- (선택 항암제 없음)")
    lines.append("")
    lines.append(f"_생성 시각: {_dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_")
    return "\n".join(lines)

md_text = build_report_md()
st.code(md_text, language="markdown")
st.download_button("💾 보고서 .md 다운로드", data=md_text.encode("utf-8"),
                   file_name="bloodmap_report.md", mime="text/markdown", key=wkey("dl_md"))