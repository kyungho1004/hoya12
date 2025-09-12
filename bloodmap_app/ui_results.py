# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import List, Dict, Tuple, Iterable
import re

# 심각도 규칙 (키워드 기반 하이라이트)
AE_RULES: List[Tuple[str, List[str]]] = [
    ("🚨 위중", [
        "분화증후군","QT","심근독성","폐섬유화","아나필락시","아나필락시스","SJS","스티븐스","독성표피괴사","TEN",
        "혈구감소","범혈구감소","무과립구증","심부전","폐렴","C.? difficile","혈전","출혈","췌장염","간부전",
        "신부전","신부전증","소뇌독성","경련","뇌병증","GI 천공","심실성 부정맥","HBV 재활성화","헤모글로빈 급감"
    ]),
    ("🟧 주의", [
        "신장독성","간독성","고칼륨","저칼륨","저나트륨","저칼슘","고혈압","담즙정체","담즙정체성 간염",
        "적색인자","레드맨","주입반응","말초신경병증","CPK 상승","시신경염","시야","과민반응","감염위험",
        "장천공","당뇨악화","갑상선","혈당상승","탈수","용량 의존"
    ]),
    ("🟡 흔함/경미", [
        "오심","구토","설사","변비","탈모","피로","발진","가려움","미각","두통","현기증","어지러움",
        "점막염","주사부위","홍반"
    ]),
]

def _classify_ae(text: str) -> List[str]:
    if not text: return []
    lines = []
    for tag, kws in AE_RULES:
        for kw in kws:
            if re.search(kw, text, flags=re.I):
                lines.append(tag + " · " + kw)
                break
    return lines

def _get_entry(db: Dict, key: str) -> Dict:
    if not key: return {}
    return db.get(key) or db.get(key.strip("'\"")) or {}

def collect_top_ae_alerts(drug_keys: Iterable[str], db: Dict | None = None) -> List[str]:
    """선택된 약물들 중 중요 경고만 모아 Top 리스트를 반환"""
    from drug_db import DRUG_DB as _DB
    ref = db if isinstance(db, dict) else _DB
    alerts = []
    for k in (drug_keys or []):
        e = _get_entry(ref, k)
        name = e.get("alias") or k
        tags = _classify_ae(e.get("ae",""))
        for t in tags:
            if t.startswith("🚨"):
                alerts.append(f"🚨 {name}: {t.replace('🚨 위중 · ','')}")
    # 중복 제거, 상위 8개까지만
    seen = set(); out = []
    for a in alerts:
        if a not in seen:
            out.append(a); seen.add(a)
    return out[:8]

def render_adverse_effects(st, drug_keys: List[str], db: Dict):
    if not drug_keys:
        st.caption("선택된 약물이 없습니다.")
        return
    for k in drug_keys:
        e = _get_entry(db, k)
        if not isinstance(e, dict) or not e:
            st.write(f"- {k}")
            continue
        name = e.get("alias") or k
        moa  = e.get("moa") or ""
        ae   = e.get("ae") or ""
        tags = _classify_ae(ae)
        # 헤더
        st.markdown(f"**{name}**")
        if moa: st.caption(moa)
        # 강조 배지
        if tags:
            for t in tags:
                if t.startswith("🚨"):
                    st.error(t.replace("🚨 위중 · ","🚨 "))
                elif t.startswith("🟧"):
                    st.warning(t.replace("🟧 주의 · ","🟧 "))
                else:
                    st.info(t.replace("🟡 흔함/경미 · ","🟡 "))
        # 원문 부작용
        if ae:
            st.write("· " + ae)
        st.divider()

def results_only_after_analyze(st) -> bool:
    """원래 함수 유지 가정: 버튼 클릭 후 결과 섹션만 보여주기 위한 게이트"""
    return bool(st.session_state.get("analyzed"))
