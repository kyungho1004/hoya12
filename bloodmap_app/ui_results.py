
from typing import Dict, Any, List
import re

# Public API
def render_adverse_effects(st, drug_keys: List[str], db: Dict[str, Dict[str, Any]]):
    if not drug_keys:
        st.caption("선택된 항암제가 없습니다.")
        return

    # 1) 라벨/키 정리
    label_map = {k: db.get(k, {}).get("alias", k) for k in drug_keys}

    # 2) Ara-C 제형 라디오 (혼합 표기 모두 감지)
    def _is_arac_like(name: str) -> bool:
        s = (name or "").lower()
        return ("ara-c" in s) or ("cytarabine" in s) or ("시타라빈" in s)

    def _arac_formulation_picker(st, db: Dict[str, Dict[str, Any]]):
        opts = []
        label_map2 = {"Ara-C IV":"정맥(IV)","Ara-C SC":"피하(SC)","Ara-C HDAC":"고용량(HDAC)"}
        for key in ["Ara-C IV","Ara-C SC","Ara-C HDAC","Cytarabine IV","Cytarabine SC","Cytarabine HDAC"]:
            if key in db:
                opts.append(key if key.startswith("Ara-C") else key.replace("Cytarabine","Ara-C"))
        opts = sorted(set(opts))
        if not opts:
            return None
        return st.radio("Ara-C 제형 선택", opts, format_func=lambda k: label_map2.get(k, k), key="arac_form_pick")

    # 3) 렌더 루프
    for k in drug_keys:
        if _is_arac_like(k):
            pick = _arac_formulation_picker(st, db)
            if pick:
                k = pick

        rec = db.get(k, {})
        alias = rec.get("alias", k)
        st.write(f"- **{alias}**")

        # 요약 AE
        ae = rec.get("ae", "")
        if ae and "부작용 정보 필요" not in ae:
            st.caption(ae)
        else:
            st.caption("요약 부작용 정보가 부족합니다.")

        # 모니터링 칩
        _render_monitoring_chips(st, rec)

        # 쉬운말 상세
        _render_ae_detail(st, rec)

        # Cardio-Guard
        _render_cardio_guard(st, rec)

        st.divider()


def _render_monitoring_chips(st, rec: Dict[str, Any]):
    chips = []
    ae = rec.get("ae","")
    if any(x in ae for x in ["골수억제","호중구","혈소판"]):
        chips.append("🩸 CBC 주기 체크")
    if any(x in ae for x in ["고혈압","단백뇨"]):
        chips.append("🩺 혈압/소변 단백 모니터")
    if any(x in ae for x in ["간효소","간독성","황달"]):
        chips.append("🧪 간기능(LFT) 추적")
    if any(x in ae for x in ["신독성","크레아티닌","혈뇨"]):
        chips.append("🧪 신기능(Cr/eGFR) 추적")
    if any(x in ae for x in ["설사","오심","구토"]):
        chips.append("💧 탈수 주의")
    if "QT" in ae or "QT " in ae:
        chips.append("📈 ECG/QT 체크")

    if chips:
        st.markdown(" ".join([f"<span class='chip'>{c}</span>" for c in chips]), unsafe_allow_html=True)


def _render_ae_detail(st, rec: Dict[str, Any]):
    det = rec.get("ae_detail") if isinstance(rec, dict) else None
    if not isinstance(det, dict) or not det:
        return
    with st.expander("🔎 자세히 보기 (쉽게 설명)", expanded=False):
        def bullet(title, items):
            if not items: return ""
            lis = "".join([f"<li>{x}</li>" for x in items])
            return f"<p><b>{title}</b></p><ul>{lis}</ul>"
        html = ""
        html += bullet("자주 나타나는 증상", det.get("common"))
        html += bullet("중요한 경고 신호", det.get("serious"))
        html += bullet("관리 팁", det.get("tips"))
        html += bullet("바로 연락해야 할 때", det.get("call"))
        if html:
            st.markdown(f"<div class='ae-detail'>{html}</div>", unsafe_allow_html=True)


def _render_cardio_guard(st, rec: Dict[str, Any]):
    name = (rec.get("alias") or "").lower()
    moa  = (rec.get("moa") or "").lower()
    def any_in(s, kws): 
        return any(k in s for k in kws)
    show_anthr = any_in(name, ["doxorubicin","daunorubicin","idarubicin"]) or "anthracycline" in moa
    show_her2  = any_in(name, ["trastuzumab","pertuzumab","t-dm1","deruxtecan"]) or "her2" in moa
    show_qt    = any_in(name, ["vandetanib","selpercatinib","pralsetinib","osimertinib","lapatinib","entrectinib"]) or ("qt" in (rec.get("ae","").lower()))
    show_arac  = any_in(name, ["ara-c hdac","cytarabine hdac"])

    if not (show_anthr or show_her2 or show_qt or show_arac):
        return

    bullets = []
    if show_anthr:
        bullets += [
            "누적 용량 추적(도옥소루비신 환산) — 250–300mg/m²: 경계, 400–450mg/m²: 고위험",
            "LVEF: 기저 및 3개월 간격(센터 프로토콜 우선)",
            "LVEF <50% & 10%p 감소 또는 증상성: 일시중단·평가",
            "증상: 숨가쁨·정좌호흡·야간호흡곤란·말초부종·갑작스런 체중↑ → 즉시 상담",
            "고위험군(이전 흉부방사선, 심질환 등): Dexrazoxane 고려"
        ]
    if show_her2:
        bullets += [
            "Trastuzumab 계열: LVEF 기저 및 주기적(보통 q3mo)",
            "LVEF 저하 또는 심부전 증상 시 보류·심장평가"
        ]
    if show_qt:
        bullets += [
            "QT 연장 위험: 기저 ECG ± 추적, K≥4.0 / Mg≥2.0 유지",
            "동시 QT 연장 약물·저칼륨혈증·저마그네슘혈증 교정",
            "실신·심계항진·어지럼 발생 시 즉시 연락"
        ]
    if show_arac:
        bullets += [
            "Ara-C 고용량(HDAC) 드문 심낭염/심낭삼출: 흉통·호흡곤란 시 즉시 보고",
            "증상 시 ECG/심장효소(Troponin) 평가 고려"
        ]
    html = "<ul>" + "".join(f"<li>{b}</li>" for b in bullets) + "</ul>"
    st.markdown("<div class='cardio-guard'><div class='title'>❤️ Cardio-Guard</div>"+html+"</div>", unsafe_allow_html=True)



# === [PATCH 2025-10-25 KST] Plain-language renderer for AE ===
def _render_ae_plain(st, rec: Dict[str, Any]):
    try:
        txt = rec.get("ae_plain") or rec.get("plain")
        if not txt:
            return
        with st.expander("알기 쉽게 보기", expanded=False):
            # split by '·' or ' / ' or sentences heuristically into bullets
            bullets = []
            raw = txt.replace("—", " - ").replace("/", " / ")
            # naive split
            for seg in raw.split("."):
                seg = seg.strip(" \n\t·-")
                if seg:
                    bullets.append(seg)
            if not bullets:
                bullets = [txt]
            st.markdown("\\n".join([f"- {b}" for b in bullets]))
    except Exception:
        pass
# === [/PATCH] ===



# === [PATCH 2025-10-25 KST] Emergency bullets + care-tip chips renderers ===
def _render_emergency_plain(st, rec: Dict[str, Any]):
    try:
        em = rec.get("plain_emergency") or []
        if not em:
            return
        with st.expander("🚨 응급 연락 기준 (중요)", expanded=False):
            st.markdown("\n".join([f"- {b}" for b in em]))
    except Exception:
        pass

def _render_care_tips_chips(st, rec: Dict[str, Any]):
    try:
        tips = rec.get("care_tips") or []
        if not tips:
            return
        chips = " ".join([f"<span class='chip'>{t}</span>" for t in tips])
        st.markdown(chips, unsafe_allow_html=True)
    except Exception:
        pass

def _ensure_plain_hooks():
    # Try to wrap common card/detail renderers to append our sections post-render
    import inspect
    targets = ["render_drug_card", "render_drug_detail", "render_chemo_card"]
    for name in targets:
        fn = globals().get(name)
        if not callable(fn) or getattr(fn, "_plain_hooked", False):
            continue
        def _wrap(fn):
            def inner(*args, **kwargs):
                res = fn(*args, **kwargs)
                # heuristic to extract rec
                rec = kwargs.get("rec")
                if rec is None and len(args) >= 2 and isinstance(args[1], dict):
                    rec = args[1]
                try:
                    import streamlit as st
                    _render_ae_plain(st, rec)
                    _render_emergency_plain(st, rec)
                    _render_care_tips_chips(st, rec)
                except Exception:
                    pass
                return res
            inner._plain_hooked = True
            return inner
        globals()[name] = _wrap(fn)

try:
    _ensure_plain_hooks()
except Exception:
    pass
# === [/PATCH] ===



# === [PATCH 2025-10-25 KST] Dedupe redirects + Ara-C formulation quick links ===
def _is_redirect_record(rec: Dict[str, Any]) -> bool:
    try:
        return bool(rec.get("redirect_to"))
    except Exception:
        return False

def _render_arac_quicklinks(st, title: str):
    try:
        t = (title or "").lower()
        if "cytarabine" in t or "ara-c" in t:
            st.markdown(
                "[Ara-C HDAC](#) · [Ara-C IV](#) · [Ara-C SC](#)  \n"
                "<span style='font-size:0.9em;opacity:0.8'>고용량(HDAC)은 **점안 스테로이드**와 **소뇌 증상** 모니터가 중요해요.</span>",
                unsafe_allow_html=True
            )
    except Exception:
        pass

# Hook into card renderers to skip redirects and add Ara-C links
def _wrap_with_redirect_and_links(fn):
    def inner(*args, **kwargs):
        # identify rec
        rec = kwargs.get("rec")
        if rec is None and len(args) >= 2 and isinstance(args[1], dict):
            rec = args[1]
        # title for quicklinks
        title = kwargs.get("title") or (args[0] if args and isinstance(args[0], str) else "")
        try:
            import streamlit as st
            if rec and _is_redirect_record(rec):
                # Skip rendering duplicated alias
                return
            _render_arac_quicklinks(st, title or (rec.get("name") if isinstance(rec, dict) else ""))
        except Exception:
            pass
        res = fn(*args, **kwargs)
        return res
    inner._redirect_link_wrapped = True
    return inner

def _install_redirect_link_hooks():
    targets = ["render_drug_card", "render_drug_detail", "render_chemo_card"]
    for name in targets:
        fn = globals().get(name)
        if callable(fn) and not getattr(fn, "_redirect_link_wrapped", False):
            globals()[name] = _wrap_with_redirect_and_links(fn)

try:
    _install_redirect_link_hooks()
except Exception:
    pass
# === [/PATCH] ===



# === [PATCH 2025-10-25 KST] Universal Friendly Sections (easy/emergency/tips/monitor) ===
def _render_chip_row(st, tips):
    try:
        if not tips: 
            return
        chips = " ".join([f"<span style='display:inline-block;padding:4px 8px;margin:2px;border-radius:999px;border:1px solid rgba(0,0,0,0.1);font-size:0.9em'>{st.escape_html(str(t)) if hasattr(st,'escape_html') else str(t)}</span>" for t in tips])
        st.markdown(f"<div style='margin-top:4px'>{chips}</div>", unsafe_allow_html=True)
    except Exception:
        try:
            st.write(", ".join(map(str,tips)))
        except Exception:
            pass

def _render_friendly_sections(st, rec: dict):
    if not isinstance(rec, dict):
        return
    # easy summary
    easy = rec.get("plain") or rec.get("ae_plain") or ""
    emerg = rec.get("plain_emergency") or []
    tips  = rec.get("care_tips") or []
    monitor = rec.get("monitor") or []
    # render only if at least one content exists
    if not (easy or emerg or tips or monitor):
        return
    try:
        with st.expander("알기 쉽게 보기", expanded=bool(easy)):
            if easy:
                st.markdown(easy)
            else:
                st.caption("요약 정보가 준비 중입니다.")
    except Exception:
        if easy:
            st.markdown("**알기 쉽게 보기**")
            st.write(easy)
    # Emergency (force visible if exists)
    if emerg:
        try:
            with st.expander("🚨 응급 연락 기준", expanded=True):
                for line in emerg:
                    st.markdown(f"- {line}")
        except Exception:
            st.markdown("**🚨 응급 연락 기준**")
            for line in emerg:
                st.write(f"- {line}")
    # Care tips
    if tips:
        try:
            with st.expander("자가관리 팁", expanded=False):
                _render_chip_row(st, tips)
        except Exception:
            st.markdown("**자가관리 팁**")
            _render_chip_row(st, tips)
    # Monitor
    if monitor:
        try:
            with st.expander("🩺 모니터", expanded=False):
                for m in monitor:
                    st.markdown(f"- {m}")
        except Exception:
            st.markdown("**🩺 모니터**")
            for m in monitor:
                st.write(f"- {m}")

def _wrap_append_friendly(fn):
    def inner(*args, **kwargs):
        # call original first
        res = fn(*args, **kwargs)
        # infer rec dict from args/kwargs
        rec = kwargs.get("rec")
        if rec is None and len(args) >= 2 and isinstance(args[1], dict):
            rec = args[1]
        try:
            import streamlit as st
            _render_friendly_sections(st, rec or {})
        except Exception:
            pass
        return res
    inner._friendly_appended = True
    return inner

def _install_friendly_hooks():
    targets = ["render_drug_card", "render_drug_detail", "render_chemo_card"]
    for name in targets:
        fn = globals().get(name)
        if callable(fn) and not getattr(fn, "_friendly_appended", False):
            globals()[name] = _wrap_append_friendly(fn)

try:
    _install_friendly_hooks()
except Exception:
    pass
# === [/PATCH] ===
