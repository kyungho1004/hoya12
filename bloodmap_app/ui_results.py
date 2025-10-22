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

SEV_ORDER = ["🚨 위중", "🟧 주의", "🟡 흔함/경미"]

def _scan_hits(text: str) -> Dict[str, List[str]]:
    hits: Dict[str, List[str]] = {k: [] for k, _ in AE_RULES}
    if not text:
        return hits
    for tag, kws in AE_RULES:
        for kw in kws:
            if re.search(kw, text, flags=re.I):
                if kw not in hits[tag]:
                    hits[tag].append(kw)
    return hits

def _get_entry(db: Dict, key: str) -> Dict:
    # Return entry from DB using label/key/alias robust matching.
    if not key:
        return {}
    try:
        from drug_db import key_from_label, ALIAS_FALLBACK
    except Exception:
        # Fallback minimal
        def key_from_label(x: str) -> str:
            pos = x.find(" (")
            return x[:pos] if pos > 0 else x
        ALIAS_FALLBACK = {}

    # 1) Direct hit or stripped quotes
    v = db.get(key) or db.get(key.strip("'\""))
    if isinstance(v, dict) and v:
        return v

    # 2) Label → canonical key (e.g., "Cytarabine (시타라빈(Ara-C))" → "Cytarabine")
    k2 = key_from_label(key)
    v = db.get(k2) or db.get(k2.lower())
    if isinstance(v, dict) and v:
        return v

    # 3) Alias matching: try Korean alias map and DB alias fields
    alias = ALIAS_FALLBACK.get(k2) or ALIAS_FALLBACK.get(key) or key
    for kk, vv in db.items():
        if isinstance(vv, dict) and (vv.get("alias") == alias or vv.get("alias") == k2):
            return vv

    # 4) Last resort: partial fallback on alias substring
    for kk, vv in db.items():
        if isinstance(vv, dict):
            al = vv.get("alias") or ""
            if al and (al in key or key in al):
                return vv

    return {}

def collect_top_ae_alerts(drug_keys: Iterable[str], db: Dict | None = None) -> List[str]:
    """선택된 약물들 중 중요 경고만 모아 Top 리스트를 반환"""
    from drug_db import DRUG_DB as _DB
    ref = db if isinstance(db, dict) else _DB
    alerts = []
    for k in (drug_keys or []):
        e = _get_entry(ref, k)
        name = e.get("alias") or k
        ae   = e.get("ae","")
        hits = _scan_hits(ae).get("🚨 위중", [])
        if hits:
            alerts.append(f"🚨 {name}: " + ", ".join(hits))
    # 중복 제거, 상위 8개까지만
    seen = set(); out = []
    for a in alerts:
        if a not in seen:
            out.append(a); seen.add(a)
    return out[:8]

def _emit_box(st, severity: str, header: str, body: str):
    msg = f"{header}\n\n{body}" if header else body
    if severity == "🚨 위중":
        st.error(msg)
    elif severity == "🟧 주의":
        st.warning(msg)
    else:
        st.info(msg)

def render_adverse_effects(st, drug_keys: List[str], db: Dict):
    """약물별 부작용을 '색상 박스 안에 본문까지' 넣어서 보여줍니다."""
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

        # 헤더 (약명/기전)
        st.markdown(f"**{name}**")
        if moa:
            st.caption(moa)

        # 하이라이트 스캔
        hits = _scan_hits(ae)
        # 최상위 심각도 선택
        top_sev = next((s for s in SEV_ORDER if hits.get(s)), None)

        if top_sev:
            # 박스 헤더: "🚨 분화증후군 • 🟡 두통" 형태로 전 심각도 요약
            chips = []
            for sev in SEV_ORDER:
                kws = hits.get(sev) or []
                if not kws:
                    continue
                icon = sev.split()[0]  # 이모지
                chips.append(icon + " " + " · ".join(kws))
            header = " / ".join(chips)
            _emit_box(st, top_sev, header, ae)   # ✅ 본문을 박스 안에 넣음
        else:
            # 키워드 매치가 없으면 일반 정보 박스로 통째로 출력
            st.info(ae or "부작용 정보가 등록되어 있지 않습니다.")

        st.divider()

def results_only_after_analyze(st) -> bool:
    """원래 함수 유지 가정: 버튼 클릭 후 결과 섹션만 보여주기 위한 게이트"""
    return bool(st.session_state.get("analyzed"))
