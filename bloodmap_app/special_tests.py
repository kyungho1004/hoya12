# special_tests.py  (피수치 프로젝트 · 특수검사 모듈 / 반응형 완벽본)
# - 중복 키/ID 완전 차단: 토글/칩/셀렉트박스 모두 섹션+인덱스 기반 유니크 키
# - 탭 가드만 유지(특수탭 외 렌더 금지), "글로벌 렌더 락" 제거 → 상호작용 즉시 반응
# - 기존 구조를 해치지 않는 "패치" 원칙 준수

from __future__ import annotations
from typing import List, Tuple
import re as _re
import streamlit as st
from contextlib import contextmanager

# 섹션 정의: (표시제목, 섹션ID)
SECTIONS: List[Tuple[str, str]] = [
    ("🟡 소변 검사(시험지)", "urine"),
    ("🟡 소변 현미경(요침사)", "urine_mic"),
    ("🟡 대변 검사(간이)", "stool"),
]

# ---- 키 헬퍼 (idx 인자 포함, 네임스페이스 고정) ----
def _tog_key(name: str, idx: int | None = None) -> str:
    base = f"sp_tog_{name}"
    return f"{base}_{idx}" if idx is not None else base

def _fav_key(name: str, idx: int | None = None) -> str:
    base = f"sp_fav_{name}"
    return f"{base}_{idx}" if idx is not None else base

def _fav_list_key() -> str:
    return "sp_favs"

def _fav_list() -> List[str]:
    return list(st.session_state.get(_fav_list_key(), []))

def _fav_add(sec_id: str) -> None:
    favs = _fav_list()
    if sec_id not in favs:
        favs.append(sec_id)
    st.session_state[_fav_list_key()] = favs

def _fav_remove(sec_id: str) -> None:
    favs = _fav_list()
    if sec_id in favs:
        favs.remove(sec_id)
    st.session_state[_fav_list_key()] = favs

# --- selectbox 자동 키 주입기: 섹션(sec_id)+인덱스(i)+필드슬러그 기반 유니크키 생성 ---
@contextmanager
def _unique_selectbox_keys(sec_id: str, idx: int):
    """
    이 컨텍스트 내부에서 호출되는 st.selectbox는, key가 비어 있으면
    자동으로 sp_sel_{sec_id}_{idx}_{fieldslug} 형태의 유니크 key를 부여한다.
    """
    _orig_selectbox = st.selectbox

    def _sb(label, options, *args, **kwargs):
        if "key" not in kwargs or not kwargs["key"]:
            field = _re.sub(r"[^A-Za-z0-9]+", "_", str(label)).strip("_").lower()
            kwargs["key"] = f"sp_sel_{sec_id}_{idx}_{field}"
        return _orig_selectbox(label, options, *args, **kwargs)

    try:
        st.selectbox = _sb  # type: ignore
        yield
    finally:
        st.selectbox = _orig_selectbox  # type: ignore
# ----------------------------------------------------------------


def special_tests_ui() -> List[str]:
    """
    특수검사 UI를 렌더링하고, 요약 해석 라인 배열을 반환.
    - 탭 가드: _ctx_tab == 'special' 에서만 렌더
    - 모든 위젯 키는 (섹션ID, enumerate 인덱스 i, 필드명) 기반으로 유니크
    - 글로벌 렌더 락 제거(상호작용 즉시 반응)
    """
    lines: List[str] = []

    # ---------- 탭 가드 ----------
    # 특수탭이 아닐 경우 렌더하지 않음(다른 탭에서 딸려다니는 현상 방지)
    if st.session_state.get("_ctx_tab") not in ("special", "t_special"):
        return []

    st.markdown("### 🔬 특수검사")
    st.caption("※ 이 섹션은 보호자용 안내입니다. 결과 해석은 참고용이며, 정확한 진단은 의료진의 판단에 따릅니다.")

    # ----- 즐겨찾기 칩 (선택 섹션 상단 노출) -----
    favs = _fav_list()
    if favs:
        st.write("#### ⭐ 자주 보는 항목")
        chips = st.columns(len(favs))
        for i, sec_id in enumerate(favs):
            with chips[i]:
                st.button(f"#{sec_id}", key=_fav_key(f"chip_{sec_id}", i))
                # 클릭시 토글 ON (세션 스위치)
                st.session_state[_tog_key(sec_id, i)] = True

    st.write("#### 목록")

    # ===== 섹션 루프 =====
    for i, (title, sec_id) in enumerate(SECTIONS):
        # 토글 키(유니크)
        on = st.toggle(
            title,
            key=_tog_key(sec_id, i),
            value=bool(st.session_state.get(_tog_key(sec_id, i), True)),
        )
        # 즐겨찾기 버튼
        cols = st.columns([1, 1, 6])
        with cols[0]:
            if st.button("즐겨찾기 추가", key=_fav_key(f"btn_{sec_id}", i)):
                _fav_add(sec_id)
        with cols[1]:
            if st.button("제거", key=_fav_key(f"btn_rm_{sec_id}", i)):
                _fav_remove(sec_id)

        # 섹션 닫힘이면 다음으로
        if not on:
            continue

        # 이 섹션의 selectbox는 자동으로 유니크 key가 부여되도록 래핑
        with _unique_selectbox_keys(sec_id, i):
            st.divider()
            if sec_id == "urine":
                _render_urine_panel(lines)
            elif sec_id == "urine_mic":
                _render_urine_mic_panel(lines)
            elif sec_id == "stool":
                _render_stool_panel(lines)
            else:
                st.info("준비 중인 항목입니다.")

    # 요약 라인 반환 (보고서 연동용)
    return lines


# ---------------- 각 섹션 렌더러 ----------------

def _render_urine_panel(lines: List[str]) -> None:
    """소변 검사(시험지) 간이 입력 + 해석"""
    st.markdown("##### 🧪 소변 검사(시험지)")
    row1 = st.columns(3)
    with row1[0]:
        alb = st.selectbox("Albumin (알부민뇨)", ["없음", "+", "++", "+++"], index=0)
    with row1[1]:
        glu = st.selectbox("Glucose (당)", ["없음", "+", "++", "+++"], index=0)
    with row1[2]:
        ket = st.selectbox("Ketone (케톤)", ["없음", "+", "++", "+++"], index=0)

    row2 = st.columns(3)
    with row2[0]:
        blod = st.selectbox("Blood/Hb (잠혈)", ["없음", "+", "++", "+++"], index=0)
    with row2[1]:
        nit = st.selectbox("Nitrite (니트라이트)", ["음성", "양성"], index=0)
    with row2[2]:
        leu = st.selectbox("Leukocyte esterase (백혈구에스테라제)", ["음성", "양성"], index=0)

    row3 = st.columns(2)
    with row3[0]:
        ph = st.selectbox("pH", [str(v) for v in range(4, 10)], index=2)
    with row3[1]:
        sg = st.selectbox(
            "Specific Gravity (비중)",
            ["1.000", "1.005", "1.010", "1.015", "1.020", "1.025", "1.030"],
            index=2,
        )

    # 간단 해석 (보호자용)
    tips = []
    if alb != "없음":
        tips.append("알부민뇨(+): 단백뇨 의심. **수분 섭취**, **휴식**, 반복 측정 권장.")
    if glu != "없음":
        tips.append("요당(+): 당대사 이상 가능성. 공복·식후 혈당을 의료진과 상의하세요.")
    if ket != "없음":
        tips.append("케톤(+): **탈수/금식/고열** 시 흔함. **수분 보충** 권장.")
    if blod != "없음":
        tips.append("잠혈(+): 운동·월경·감염 등 원인 다양. 재검/현미경 검사 고려.")
    if nit == "양성" or leu == "양성":
        tips.append("니트라이트/백혈구 양성: **요로감염(UTI)** 가능성. 발열·복통·배뇨통 시 진료 필요.")
    if sg in ("1.025", "1.030"):
        tips.append("비중 높음: **농축 소변** 가능성. 수분 섭취를 늘려주세요.")
    if sg == "1.000":
        tips.append("비중 낮음: 과도한 수분 섭취/신기능 이상 의심 시 상담 필요.")

    if tips:
        st.markdown("###### 간단 해석")
        for t in tips:
            st.write(f"- {t}")
            lines.append(f"[소변시험지] {t}")


def _render_urine_mic_panel(lines: List[str]) -> None:
    """소변 현미경(요침사) 간이 입력 + 해석"""
    st.markdown("##### 🔬 소변 현미경(요침사)")
    row = st.columns(3)
    with row[0]:
        rbc = st.selectbox("RBC (적혈구/HPF)", ["0-2", "3-5", "6-10", ">10"], index=0)
    with row[1]:
        wbc = st.selectbox("WBC (백혈구/HPF)", ["0-2", "3-5", "6-10", ">10"], index=0)
    with row[2]:
        cast = st.selectbox("주형(cast)", ["없음", "히알린", "과립", "적혈구/백혈구"], index=0)

    tips = []
    if rbc != "0-2":
        tips.append("적혈구 증가: 현미경적 혈뇨. 운동/감염/결석 등 원인 평가 및 재검 고려.")
    if wbc != "0-2":
        tips.append("백혈구 증가: **염증/감염** 가능성. 발열/배뇨통/빈뇨 등 증상 확인.")
    if cast != "없음":
        tips.append("주형 관찰: **신실질 문제** 가능성. 임상 병합하여 상담 필요.")

    if tips:
        st.markdown("###### 간단 해석")
        for t in tips:
            st.write(f"- {t}")
            lines.append(f"[요침사] {t}")


def _render_stool_panel(lines: List[str]) -> None:
    """대변 검사(간이) 보호자용 입력 + 해석 (정밀 진단 목적 아님)"""
    st.markdown("##### 💩 대변 검사(간이)")
    row = st.columns(3)
    with row[0]:
        ob = st.selectbox("잠혈(OB)", ["음성", "양성"], index=0)
    with row[1]:
        m = st.selectbox("점액", ["없음", "조금", "많음"], index=0)
    with row[2]:
        c = st.selectbox("색(참고)", ["황색", "녹색", "회색/백색", "검은색", "붉은색"], index=0)

    tips = []
    if ob == "양성":
        tips.append("대변 잠혈 양성: 소화관 출혈 가능성. 검진/상담 필요.")
    if c in ("검은색", "붉은색"):
        tips.append("검은/붉은 변: **상/하부 위장관 출혈** 가능성. 증상 동반 시 즉시 진료 필요.")
    if m in ("조금", "많음"):
        tips.append("점액 증가: **염증성 변화** 가능성. 설사·복통 동반 시 상담 권장.")

    if tips:
        st.markdown("###### 간단 해석")
        for t in tips:
            st.write(f"- {t}")
            lines.append(f"[대변] {t}")


# 모듈의 외부 노출
__all__ = [
    "special_tests_ui",
]

