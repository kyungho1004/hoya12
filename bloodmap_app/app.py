
# -*- coding: utf-8 -*-
"""
피수치 홈페이지 프로젝트 — 최종본 (STRICT LABS)
- lab_diet 연동: UI/데이터/get_guides_by_values
- 식이가이드 기본: **수치 기반만 표시**
- 증상 가이드(ANC 위생/설사/변비/발열)는 **옵션 토글**로만 표시
- '설사 있음' 체크 시에만 설사 가이드 노출
- 보고서: 기본은 수치 기반만, 옵션 체크 시 증상 가이드 병합
- 피수치: 사용자 '이번 세션' 입력 키만 추적하여 보고서에 반영
- autosave/feedback: /tmp 경로, 권한 경고 제거
- onco_map / special_tests 로더 포함
"""

import streamlit as st
from datetime import datetime, timezone, timedelta
from pathlib import Path
import importlib.util, sys, csv, json

# ---------------- Basics ----------------
KST = timezone(timedelta(hours=9))
def kst_now() -> str: return datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S KST")
def wkey(s: str) -> str: return f"k_{s}"

CURRENT_USERS = 140
FEED_PATH = Path("/tmp/bloodmap_feedback.csv")
AUTOSAVE_PATH = Path("/tmp/bloodmap_autosave.json")

# ---------------- Autosave ----------------
ESSENTIAL_KEYS = [
    "labs_dict","labs_entered_keys","bp_summary",
    "onco_group","onco_dx",
    "peds_notes","special_interpretations",
    "selected_agents","onco_warnings",
    "diet_notes","diet_lab_notes","symptom_diet_notes",
    "heme_warning","show_peds_on_home"
]
def restore_state():
    try:
        if AUTOSAVE_PATH.exists():
            data = json.loads(AUTOSAVE_PATH.read_text(encoding="utf-8"))
            for k,v in data.items():
                st.session_state[k] = v
            st.caption(f"자동 복원 완료: {AUTOSAVE_PATH}")
    except Exception as e:
        st.warning(f"자동 복원 실패: {e}")

def autosave_state():
    try:
        data = {k: st.session_state.get(k) for k in ESSENTIAL_KEYS}
        AUTOSAVE_PATH.parent.mkdir(parents=True, exist_ok=True)
        AUTOSAVE_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        try:
            import tempfile
            alt = Path(tempfile.gettempdir()) / "bloodmap_autosave.json"
            alt.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            st.warning(f"/tmp 저장으로 대체됨: {alt} (사유: {e})")
        except Exception as e2:
            if not st.session_state.get("_autosave_err_shown"):
                st.error(f"자동 저장 실패: {e2}")
                st.session_state["_autosave_err_shown"] = True

# ---------------- Helpers ----------------
def _parse_float(x):
    if x is None: return None
    s = str(x).strip().replace(",", "")
    if s == "": return None
    try: return float(s)
    except Exception: return None

def is_heme_cancer():
    g = (st.session_state.get("onco_group") or "").lower()
    d = (st.session_state.get("onco_dx") or "").lower()
    keys = ["혈액","백혈","림프종","다발골수","leuk","lymph","myeloma","cml","aml","all","mds","mpn"]
    return any(k in g for k in keys) or any(k in d for k in keys)

# ---------------- Loaders: onco_map ----------------
def _candidate_onco_paths():
    c = []
    try:
        here = Path(__file__).resolve().parent
        c.append(here / "onco_map.py")
    except Exception:
        pass
    c += [
        Path("/mount/src/hoya12/bloodmap_app/onco_map.py"),
        Path("/mnt/data/onco_map.py"),
        Path.cwd() / "onco_map.py",
        Path("onco_map.py"),
    ]
    out, seen = [], set()
    for p in c:
        s = str(p.resolve()) if p.exists() else str(p)
        if s not in seen:
            seen.add(s); out.append(p)
    return out

def load_onco():
    last_err = None
    for p in _candidate_onco_paths():
        try:
            if not p.exists(): continue
            spec = importlib.util.spec_from_file_location("onco_map", str(p))
            mod = importlib.util.module_from_spec(spec)
            sys.modules["onco_map"] = mod
            spec.loader.exec_module(mod)  # type: ignore
            build = getattr(mod, "build_onco_map", None)
            disp = getattr(mod, "dx_display", None)
            omap = None
            if callable(build): omap = build()
            elif hasattr(mod, "OM"): omap = getattr(mod, "OM")
            elif hasattr(mod, "ONCO_MAP"): omap = getattr(mod, "ONCO_MAP")
            if isinstance(omap, dict) and omap:
                return omap, disp, p
        except Exception as e:
            last_err = e
    return None, None, last_err

# ---------------- Loaders: special_tests ----------------
def _candidate_special_paths():
    c = []
    try:
        here = Path(__file__).resolve().parent
        c.append(here / "special_tests.py")
    except Exception:
        pass
    c += [
        Path("/mount/src/hoya12/bloodmap_app/special_tests.py"),
        Path("/mnt/data/special_tests.py"),
        Path.cwd() / "special_tests.py",
        Path("special_tests.py"),
    ]
    out, seen = [], set()
    for p in c:
        s = str(p.resolve()) if p.exists() else str(p)
        if s not in seen:
            seen.add(s); out.append(p)
    return out

def _load_special_module():
    last_err = None
    for p in _candidate_special_paths():
        try:
            if not p.exists(): continue
            spec = importlib.util.spec_from_file_location("special_tests", str(p))
            mod = importlib.util.module_from_spec(spec)
            sys.modules["special_tests"] = mod
            spec.loader.exec_module(mod)  # type: ignore
            return mod, p
        except Exception as e:
            last_err = e
    return None, last_err

def _call_special_ui(mod):
    for fn in ["special_tests_ui","render_special_tests_ui","build_special_tests_ui","ui"]:
        f = getattr(mod, fn, None)
        if callable(f): return f()
    for name in ["SPECIAL_TESTS","SPECIAL_RESULTS","DATA"]:
        if hasattr(mod, name):
            data = getattr(mod, name)
            if isinstance(data, (list,tuple)): return list(data)
            if isinstance(data, dict):
                out = []
                for k,v in data.items():
                    if isinstance(v,(list,tuple)):
                        for x in v: out.append(f"{k}: {x}")
                    else: out.append(f"{k}: {v}")
                return out
    return None

# ---------------- Loaders: lab_diet ----------------
def _candidate_diet_paths():
    c = []
    try:
        here = Path(__file__).resolve().parent
        c.append(here / "lab_diet.py")
    except Exception:
        pass
    c += [
        Path("/mount/src/hoya12/bloodmap_app/lab_diet.py"),
        Path("/mnt/data/lab_diet.py"),
        Path.cwd() / "lab_diet.py",
        Path("lab_diet.py"),
    ]
    out, seen = [], set()
    for p in c:
        s = str(p.resolve()) if p.exists() else str(p)
        if s not in seen:
            seen.add(s); out.append(p)
    return out

def _load_diet_module():
    last_err = None
    for p in _candidate_diet_paths():
        try:
            if not p.exists(): continue
            spec = importlib.util.spec_from_file_location("lab_diet", str(p))
            mod = importlib.util.module_from_spec(spec)
            sys.modules["lab_diet"] = mod
            spec.loader.exec_module(mod)  # type: ignore
            return mod, p
        except Exception as e:
            last_err = e
    return None, last_err

# ---------------- Built-in diet from labs ----------------

def _diet_from_labs(labs: dict):
    notes = []
    def f(name):
        try: return _parse_float(labs.get(name))
        except Exception: return None
    def tag(name):
        return _lab_flag_label(name, labs.get(name))
    Na = f("Na"); K=f("K"); Ca=f("Ca"); P=f("P"); Glu=f("Glu")
    Cr=f("Cr"); Tb=f("Tb"); Alb=f("Alb"); UA=f("UA"); Hb=f("Hb")
    # Na
    if Na is not None:
        if Na < 135:
            t = tag("Na")
            notes += [f"{t}: 저나트륨혈증 — 자유수(물) 과다섭취 주의, 수분 섭취는 의료진 지시에 따르기",
                      f"{t}: 국물/수분 많은 음식 과다섭취 피하기"]
        elif Na > 145:
            t = tag("Na")
            notes += [f"{t}: 고나트륨혈증 — 충분한 수분 섭취(의료진 지시), 고염식 피하기"]
    # K
    if K is not None:
        if K < 3.5:
            t = tag("K")
            notes += [f"{t}: 저칼륨혈증 — 바나나·키위·오렌지·감자·고구마 등 칼륨 풍부 식품 추가(약물/기저질환 확인)"]
        elif K > 5.1:
            t = tag("K")
            notes += [f"{t}: 고칼륨혈증 — 바나나·오렌지·토마토·감자·시금치 등 고칼륨 식품 과다 섭취 피하기",
                      f"{t}: 채소는 데쳐서 물 버리기"]
    # Ca
    if Ca is not None:
        if Ca < 8.6:
            t = tag("Ca")
            notes += [f"{t}: 저칼슘 — 칼슘/비타민D 섭취 점검 — 보충제는 의료진과 상의"]
        elif Ca > 10.2:
            t = tag("Ca")
            notes += [f"{t}: 고칼슘 — 칼슘/비타민D 고함량 보충제·강화식품 과다 피하기, 충분한 수분"]
    # P
    if P is not None:
        if P < 2.5:
            t = tag("P")
            notes += [f"{t}: 저인 — 단백질 섭취 상태 점검(육류/달걀/유제품) — 보충제는 상의"]
        elif P > 4.5:
            t = tag("P")
            notes += [f"{t}: 고인 — 탄산음료/가공치즈/가공육 등 인산염 많은 음식 제한"]
    # Glu
    if Glu is not None:
        if Glu > 140:
            t = tag("Glu")
            notes += [f"{t}: 고혈당 경향 — 단순당 줄이고, 정제곡물→현미/잡곡, 식사/간식 규칙화"]
        elif Glu < 70:
            t = tag("Glu")
            notes += [f"{t}: 저혈당 위험 — 규칙적 식사/간식, 빠르게 흡수되는 당 비상 준비"]
    # Cr
    if Cr is not None and Cr > 1.2:
        t = tag("Cr")
        notes += [f"{t}: 신기능 저하 가능 — 염분/칼륨/인 과다 피하기, 단백질은 지시 범위"]
    # Tb
    if Tb is not None and Tb > 1.2:
        t = tag("Tb")
        notes += [f"{t}: 고빌리루빈 — 기름진 음식 과다 피하기, 규칙적 소량 식사; 알코올 금지"]
    # Alb
    if Alb is not None and Alb < 3.5:
        t = tag("Alb")
        notes += [f"{t}: 저알부민 — 단백질/에너지 보충(살코기·달걀·두부·유제품), 작은 끼니 자주"]
    # UA
    if UA is not None and UA > 7.2:
        t = tag("UA")
        notes += [f"{t}: 요산 상승 — 퓨린 많은 음식(내장/멸치/건어물 등) 과다 피하고 수분 충분히"]
    # Hb
    if Hb is not None and Hb < 12.0:
        t = tag("Hb")
        notes += [f"{t}: 빈혈 경향 — 철분 풍부식 + 비타민C 동시 섭취"]
    # de-dup (preserve order)
    out, seen = [], set()
    for n in notes:
        if n not in seen:
            seen.add(n); out.append(n)
    return out


# ---------------- UI: Onco select ----------------
def onco_select_ui():
    st.header("🧬 암종 선택")
    omap, dx_display, info = load_onco()
    if not isinstance(omap, dict) or not omap:
        st.error(f"onco_map.py에서 암 분류를 불러오지 못했습니다. {'에러: '+str(info) if info else ''}")
        g_manual = st.text_input("암 그룹(수동)", value=st.session_state.get("onco_group") or "", key=wkey("onco_g_manual"))
        d_manual = st.text_input("진단(암종, 수동)", value=st.session_state.get("onco_dx") or "", key=wkey("onco_d_manual"))
        if g_manual or d_manual:
            st.session_state["onco_group"] = g_manual.strip() or None
            st.session_state["onco_dx"] = d_manual.strip() or None
            st.success("수동 입력값을 사용합니다.")
        return st.session_state.get("onco_group"), st.session_state.get("onco_dx")
    st.caption(f"onco_map 연결: {info}")
    groups = sorted(list(omap.keys()))
    group = st.selectbox("암 그룹", groups, key=wkey("onco_group"))
    dx_keys = sorted(list(omap.get(group, {}).keys()))
    labels = [(dx_display(group, dx) if dx_display else f"{group} - {dx}") for dx in dx_keys]
    if dx_keys:
        default_dx = st.session_state.get("onco_dx")
        idx_default = dx_keys.index(default_dx) if default_dx in dx_keys else 0
        idx = st.selectbox("진단(암종)", list(range(len(labels))), index=idx_default, format_func=lambda i: labels[i], key=wkey("onco_dx_idx"))
        dx = dx_keys[idx]
        st.session_state["onco_group"], st.session_state["onco_dx"] = group, dx
    else:
        st.warning("해당 그룹에 진단이 없습니다.")
        st.session_state["onco_group"] = group
        st.session_state["onco_dx"] = None
    return st.session_state.get("onco_group"), st.session_state.get("onco_dx")

# ---------------- UI: Special tests ----------------
def render_special_tests():
    st.header("🔬 특수검사")
    try:
        mod, info = _load_special_module()
        if not mod:
            st.error(f"특수검사 모듈을 찾지 못했습니다. {'에러: '+str(info) if info else ''}"); return
        res = _call_special_ui(mod)
        lines = []
        if isinstance(res,(list,tuple)): lines = [str(x) for x in res]
        elif isinstance(res,str): lines = [res]
        st.session_state["special_interpretations"] = lines
        if lines:
            st.markdown("### 특수검사 해석")
            for ln in lines: st.markdown(f"- {ln}")
        st.caption(f"special_tests 연결: {info}")
    except Exception as e:
        st.error(f"특수검사 로드 오류: {e}")

# ---------------- UI: Diet (lab_diet + labs only by default) ----------------
def render_diet_guides(context=None, key_prefix: str = ""):
    st.header("🥗 식이가이드")
    # 혈액암 보충제 경고
    if is_heme_cancer():
        st.warning("혈액암 환자는 비타민/철분제 섭취 시 **주의**가 필요합니다. 반드시 **주치의와 상담 후** 복용하세요.")
        st.session_state['heme_warning'] = "혈액암 환자 비타민/철분제 복용은 주치의와 상담 필요"
    else:
        st.session_state['heme_warning'] = None

    # 증상 기반 가이드는 혼선 방지: 기본 비표시(옵션)
    state_key = f"show_symptom_guides_{key_prefix}" if key_prefix else "show_symptom_guides"
    widget_key = wkey(f"{key_prefix}symptom_toggle") if key_prefix else wkey("symptom_toggle")
    st.session_state.setdefault(state_key, False)
    show_symptom = st.checkbox("증상 기반 가이드 표시(설사/변비/발열/위생수칙)", value=st.session_state[state_key], key=widget_key)
    st.session_state[state_key] = show_symptom

    # lab_diet 호출
    ctx = dict(context or {})
    ctx["labs"] = st.session_state.get("labs_dict", {}) or {}
    used_external = False
    mod, info = _load_diet_module()
    if mod:
        # UI 함수 우선
        for fn in ["diet_ui","render_diet_ui","build_diet_ui","ui"]:
            f = getattr(mod, fn, None)
            if callable(f):
                res = f(ctx)
                if isinstance(res,(list,tuple)):
                    st.session_state["diet_notes"] = [str(x) for x in res]
                st.caption(f"lab_diet 연결: {info}")
                used_external = True
                break
        # 데이터 상수
        if not used_external:
            out_lines = []
            for name in ["DIET_GUIDES","GUIDES","DATA"]:
                if hasattr(mod, name):
                    data = getattr(mod, name)
                    if isinstance(data, dict):
                        st.markdown("### 가이드 목록")
                        for k,v in data.items():
                            st.markdown(f"**{k}**")
                            if isinstance(v,(list,tuple)):
                                for x in v: st.markdown(f"- {x}"); out_lines.append(f"{k}: {x}")
                            else:
                                st.markdown(f"- {v}"); out_lines.append(f"{k}: {v}")
                    elif isinstance(data,(list,tuple)):
                        for ln in data: st.markdown(f"- {ln}"); out_lines.append(str(ln))
            if out_lines:
                st.session_state["diet_notes"] = out_lines
                st.caption(f"lab_diet 연결: {info}")
                used_external = True
        # 외부 수치 가이드 병합
        if hasattr(mod, "get_guides_by_values"):
            try:
                ext_notes = getattr(mod, "get_guides_by_values")(ctx["labs"])
                if isinstance(ext_notes,(list,tuple)) and ext_notes:
                    st.markdown("### 수치 기반 식이가이드 (lab_diet)")
                    for x in ext_notes: st.markdown(f"- {x}")
                    base = st.session_state.get("diet_notes", [])
                    st.session_state["diet_notes"] = base + [str(n) for n in ext_notes if str(n) not in base]
                    cur = st.session_state.get("diet_lab_notes") or []
                    st.session_state["diet_lab_notes"] = cur + [str(n) for n in ext_notes if str(n) not in cur]
            except Exception as _e:
                st.caption(f"lab_diet.get_guides_by_values 호출 실패: {_e}")

    # 내장 수치 규칙(항상 표시)
    labs = st.session_state.get("labs_dict", {}) or {}
    lab_notes = _diet_from_labs(labs)
    if lab_notes:
        st.markdown("### 수치 기반 식이가이드")
        for x in lab_notes: st.markdown(f"- {x}")
        base = st.session_state.get("diet_notes", [])
        st.session_state["diet_notes"] = base + [n for n in lab_notes if n not in base]
        cur = st.session_state.get("diet_lab_notes") or []
        st.session_state["diet_lab_notes"] = cur + [n for n in lab_notes if n not in cur]

    # (옵션) 증상 기반: lab_diet 없거나 신호 있을 때만, 토글 ON이어야 표시
    # 폴백 생성 함수
    def _render_diet_fallback(ctx):
        notes = []
        anc = ctx.get("ANC")
        fever = ctx.get("fever")
        constipation = bool(ctx.get("constipation"))
        diarrhea_flag = bool(ctx.get("diarrhea"))
        if anc is not None and anc < 500:
            notes += [
                "ANC낮음: 생야채/날고기·생선 금지, 모든 음식은 충분히 익혀서",
                "ANC낮음: 멸균/살균 제품 위주 섭취, 유통기한/보관 온도 준수",
                "ANC낮음: 과일은 껍질 제거 후 섭취(가능하면 데친 뒤 식혀서)",
                "ANC낮음: 조리 후 2시간 지나면 폐기, 뷔페/회/초밥/생채소 샐러드 금지",
            ]
        if diarrhea_flag:
            notes += [
                "설사: 초기 24시간: 바나나·쌀죽·사과퓨레·토스트(BRAT 변형) 참고",
                "설사: 자주·소량의 미지근한 수분, 탄산/아이스는 피하기",
                "설사: ORS: 처음 1시간 10–20 mL/kg, 이후 설사 1회당 5–10 mL/kg",
            ]
        if constipation:
            notes += [
                "변비: 수분 50–60 mL/kg/일(지시에 따라 조정), 식후 좌변습관 10–15분",
                "변비: 섬유(귀리·보리·사과/배·키위·프룬·고구마·통곡빵·현미·익힌 채소)",
            ]
        if fever and fever != "37.x":
            notes += [
                "발열: 옷 가볍게/실내 시원하게, 해열제 간격(아세트 ≥4h, 이부 ≥6h)",
                "(만약 열이 안잡힐경우 2시간 간격으로 아세트아미노펜 과 이부프로펜을 교차복용해주시고)",
                "(물이나 ors 또는 음료수를 소량씩 자주 먹이시면 해열작용에 도움이됩니다)",
                "(손과 발을 만져서 손발이 따듯하다면 해열제가 작용중이니 30분에서 1시간간격으로 열체크해주시면 도움이됩니다)",
                "(집안 온도는 25에서 26도 사이가 좋으며 미지근한물로 닦아주시면 해열작용에 많은 도움이됩니다)",
            ]
        return notes

    # 신호 확인
    anc = ctx.get("ANC"); fever = ctx.get("fever")
    constipation = bool(ctx.get("constipation"))
    diarrhea_flag = bool(ctx.get("diarrhea"))
    has_signals = (anc is not None and anc < 500) or diarrhea_flag or constipation or (fever and fever != "37.x")

    if show_symptom and has_signals:
        sym_notes = _render_diet_fallback(ctx)
        st.session_state["symptom_diet_notes"] = sym_notes
        if sym_notes:
            st.markdown("### (옵션) 증상 기반 식이가이드")
            for x in sym_notes: st.markdown(f"- {x}")

# ---------------- UI: Labs ----------------
LAB_FIELDS=[
    ("WBC","x10^3/µL"),("Hb","g/dL"),("Plt","x10^3/µL"),("ANC","/µL"),
    ("Ca","mg/dL"),("P","mg/dL"),("Na","mmol/L"),("K","mmol/L"),
    ("Alb","g/dL"),("Glu","mg/dL"),("TP","g/dL"),("AST","U/L"),
    ("ALT","U/L"),("LD","U/L"),("CRP","mg/L"),("Cr","mg/dL"),
    ("UA","mg/dL"),("Tb","mg/dL"),
]
REF_RANGE = {
    "WBC": (4.0,10.0),"Hb":(12.0,16.0),"Plt":(150,400),"ANC":(1500,8000),
    "Ca":(8.6,10.2),"P":(2.5,4.5),"Na":(135,145),"K":(3.5,5.1),
    "Alb":(3.5,5.2),"Glu":(70,140),"TP":(6.0,8.3),"AST":(0,40),
    "ALT":(0,40),"LD":(120,250),"CRP":(0,5),"Cr":(0.5,1.2),
    "UA":(3.5,7.2),"Tb":(0.2,1.2),
}


def _lab_flag_label(name: str, value):
    """Return a label like 'Na 133↓ (135–145)' based on REF_RANGE and value."""
    try:
        v = _parse_float(value)
    except Exception:
        v = None
    if v is None:
        return f"{name} ?"
    lo, hi = REF_RANGE.get(name, (None, None))
    arrow = ""
    if lo is not None and v < lo: arrow = "↓"
    elif hi is not None and v > hi: arrow = "↑"
    ref = ""
    if lo is not None or hi is not None:
        lo_s = "" if lo is None else str(lo)
        hi_s = "" if hi is None else str(hi)
        ref = f" ({lo_s}–{hi_s})"
    return f"{name} {v}{arrow}{ref}"
def labs_input_ui():
    st.header("🧪 피수치 입력 (사용자 입력만 추적)")
    labs = st.session_state.get("labs_dict", {}).copy()
    entered = set(st.session_state.get("labs_entered_keys", []) or [])
    cols = st.columns(3)
    alerts = []
    for i,(name,unit) in enumerate(LAB_FIELDS):
        with cols[i%3]:
            raw = labs.get(name, "")
            if raw is None or str(raw).strip().lower() == "none": raw = ""
            val = st.text_input(f"{name} ({unit})", value=str(raw), placeholder="숫자 입력", key=wkey(f"lab_{name}"))
            labs[name] = val.strip()
            if val.strip() != "":
                entered.add(name)
                v = _parse_float(val)
                if v is None:
                    st.caption("❌ 숫자 인식 실패")
                elif name in REF_RANGE:
                    lo,hi = REF_RANGE[name]
                    ok = ((lo is None or v>=lo) and (hi is None or v<=hi))
                    st.caption("✅ 참고범위 내" if ok else "⚠️ 참고범위 벗어남")
                    if not ok: alerts.append(f"{name} 비정상: {v}")
            else:
                entered.discard(name)
    st.session_state["labs_dict"] = labs
    st.session_state["labs_entered_keys"] = sorted(list(entered))
    # 즉시 수치 기반 계산 저장
    try:
        st.session_state["diet_lab_notes"] = _diet_from_labs(labs)
    except Exception:
        st.session_state["diet_lab_notes"] = []
    if alerts: st.warning("이상치: " + ", ".join(alerts))
    if entered:
        st.markdown("#### 입력 요약")
        for k in st.session_state["labs_entered_keys"]:
            v = labs.get(k, "")
            if str(v).strip()!="": st.markdown(f"- **{k}**: {v}")
    return labs

# ---------------- UI: BP ----------------
def classify_bp(sbp, dbp):
    if sbp is None or dbp is None: return ("측정값 없음","SBP/DBP를 입력하세요.")
    if sbp>=180 or dbp>=120: return ("🚨 고혈압 위기","즉시 의료기관 평가 권장")
    if sbp>=140 or dbp>=90: return ("2기 고혈압","생활습관 + 약물치료 고려(의료진)")
    if 130<=sbp<=139 or 80<=dbp<=89: return ("1기 고혈압","생활습관 교정 + 위험평가")
    if 120<=sbp<=129 and dbp<80: return ("주의혈압(상승)","염분 제한/운동/체중조절 권장")
    if sbp<120 and dbp<80: return ("정상혈압","유지")
    return ("분류불가","값을 확인하세요.")

def bp_ui():
    st.header("🩺 혈압 체크 (압종분류)")
    c1,c2,c3 = st.columns(3)
    with c1: sbp = st.text_input("SBP (mmHg)", key=wkey("sbp"))
    with c2: dbp = st.text_input("DBP (mmHg)", key=wkey("dbp"))
    with c3: st.caption("기준: ACC/AHA 2017 (단순화)")
    sbp_val = _parse_float(sbp); dbp_val = _parse_float(dbp)
    cat, note = classify_bp(sbp_val, dbp_val)
    st.info(f"분류: **{cat}** — {note}")
    if sbp_val is not None and dbp_val is not None:
        st.session_state["bp_summary"] = f"{cat} (SBP {sbp} / DBP {dbp}) — {note}"
    else:
        st.session_state["bp_summary"] = None
    return cat, note

# ---------------- UI: Peds ----------------
def render_caregiver_notes_peds(*, stool, fever, persistent_vomit, oliguria, cough, nasal, eye, abd_pain, ear_pain, rash, hives, migraine, hfmd, constipation=False, anc_low=None, diarrhea=False):
    st.header("🧒 소아가이드")
    if anc_low is None:
        try:
            anc_val = _parse_float(st.session_state.get("labs_dict", {}).get("ANC"))
            anc_low = (anc_val is not None and anc_val < 500)
        except Exception:
            anc_low = False
    notes=[]
    def bullet(title, body):
        st.markdown(f"**{title}**"); st.markdown(body.strip())
        first = body.strip().splitlines()[0].strip("- ").strip()
        if first: notes.append(f"{title} — {first}")
    if anc_low:
        bullet("🍽️ ANC 낮음(호중구 감소) 식이가이드","""
- **생야채/날고기·생선 금지**, 모든 음식은 **충분히 익혀서**
- **멸균/살균 제품** 위주 섭취, 유통기한·보관 온도 준수
- 과일은 **껍질 제거 후** 섭취(가능하면 데친 뒤 식혀서)
- **조리 후 2시간 지나면 폐기**, **뷔페/회/초밥/생채소 샐러드 금지**
""")
    if diarrhea:
        bullet("💧 설사/장염 의심","""
- 하루 **잦은 묽은 변**이면 장염 가능성
- **ORS**: 처음 1시간 **10–20 mL/kg**, 이후 설사 1회당 **5–10 mL/kg**
- **즉시 진료**: 피 섞인 변, **고열 ≥39℃**, **소변 거의 없음/축 늘어짐**
""")
        bullet("🍽️ 식이가이드(설사)","""
- 초기 24시간: **바나나·쌀죽·사과퓨레·토스트(BRAT 변형)** 참고
- **자주·소량**의 미지근한 수분, 탄산/아이스는 피하기
""")
    if constipation:
        bullet("🚻 변비 대처","""
- **수분**: 대략 체중 **50–60 mL/kg/일**(지시 맞춰 조정)
- **좌변 습관**: 식후 10–15분, 하루 1회 5–10분
""")
    if fever in ["38~38.5","38.5~39","39 이상"]:
        bullet("🌡️ 발열 대처","""
- 옷 가볍게, 실내온도는 25에서 26도 소량의 이나 ors 음료수 를 주시면 많이 도움됩니다.
- 해열제 열이 안잡힐경우 아세트아미노펜 과 이부프로펜은 최소 간격2시간을 유지해주세요.
- **해열제 간격**: 아세트아미노펜 ≥4h, 이부프로펀 ≥6h
""")
    st.session_state["peds_notes"] = notes

# ---------------- Chemo (concise) ----------------
GOOD,WARN,DANGER="🟢","🟡","🚨"
def _b(txt:str)->str: return txt.replace("{GOOD}",GOOD).replace("{WARN}",WARN).replace("{DANGER}",DANGER)
CHEMO_DB={
 "ATRA (Tretinoin, Vesanoid) / 베사노이드":{
  "effects":{"common":["{WARN} 두통/피부건조/지질상승"]},
  "ra_syndrome":{"name":"RA-분화증후군","symptoms":["{DANGER} 발열","{DANGER} 호흡곤란/저산소","{DANGER} 저혈압","{DANGER} 전신부종/체중 급증"]},
  "monitor":["CBC, SpO₂, 체중/부종, 지질"],
 },
 "Cytarabine (Ara-C) / 시타라빈(아라씨)":{
  "routes":{"IV/SC(표준용량)":["{WARN} 발열/구토/설사/구내염","{DANGER} 골수억제","{WARN} 결막염"],
            "HDAC(고용량)":["{DANGER} 소뇌독성(보행/말/글씨체 변화)","{WARN} 각결막염 — 스테로이드 점안"]},
  "monitor":["CBC, 간기능, 신경학적 징후"],
 },
 "MTX (Methotrexate) / 메토트렉세이트":{
  "effects":{"blood":["{DANGER} 골수억제"],"renal":["{DANGER} HD-MTX 신독성/결정뇨"],"pulmonary":["{WARN} MTX 폐렴"]},
  "monitor":["CBC, AST/ALT, Cr/eGFR","HD-MTX: MTX 농도 + 류코보린 + 요알칼리화"],
 },
}

# ---- 암종별 프로토콜 추천 ----

CHEMO_PROTOCOLS = {
 "APL": ["ATRA (Tretinoin, Vesanoid) / 베사노이드", "Arsenic Trioxide (ATO) / 삼산화비소", "Doxorubicin (DOX) / 독소루비신", "Idarubicin / 이다루비신", "Daunorubicin / 다우노루비신"],
 "AML": ["Cytarabine (Ara-C) / 시타라빈(아라씨)", "Daunorubicin / 다우노루비신", "Idarubicin / 이다루비신"],
 "ALL": ["Vincristine (VCR) / 빈크리스틴", "MTX (Methotrexate) / 메토트렉세이트", "Mercaptopurine (6-MP) / 6-머캅토퓨린"],
 "CML": ["Imatinib / 이매티닙(글리벡)"],
 "DLBCL": ["Cyclophosphamide (CTX) / 사이클로포스파마이드", "Doxorubicin (DOX) / 독소루비신", "Vincristine (VCR) / 빈크리스틴"],
 "Hodgkin": ["Doxorubicin (DOX) / 독소루비신", "Vincristine (VCR) / 빈크리스틴", "Cyclophosphamide (CTX) / 사이클로포스파마이드"],
 "Colon": ["5-Fluorouracil (5-FU) / 5-플루오로우라실", "Capecitabine (CAP) / 카페시타빈", "Oxaliplatin (L-OHP) / 옥살리플라틴", "Irinotecan (CPT-11) / 이리노테칸", "Bevacizumab / 베바시주맙"],
 "Gastric": ["Capecitabine (CAP) / 카페시타빈", "5-Fluorouracil (5-FU) / 5-플루오로우라실", "Oxaliplatin (L-OHP) / 옥살리플라틴", "Cisplatin (CDDP) / 시스플라틴", "Trastuzumab / 트라스투주맙"],
 "Pancreas": ["Gemcitabine / 젬시타빈", "Nab-Paclitaxel (Abraxane) / 나브-파클리탁셀", "Irinotecan (CPT-11) / 이리노테칸", "Oxaliplatin (L-OHP) / 옥살리플라틴"],
 "Biliary": ["Gemcitabine / 젬시타빈", "Cisplatin (CDDP) / 시스플라틴"],
 "Breast": ["Cyclophosphamide (CTX) / 사이클로포스파마이드", "Doxorubicin (DOX) / 독소루비신", "Paclitaxel / 파클리탁셀", "Docetaxel / 도세탁셀", "Trastuzumab / 트라스투주맙"],
 "NSCLC": ["Cisplatin (CDDP) / 시스플라틴", "Carboplatin (CBDCA) / 카보플라틴", "Pemetrexed / 페메트렉시드", "Paclitaxel / 파클리탁셀", "Docetaxel / 도세탁셀", "Bevacizumab / 베바시주맙"],
 "SCLC": ["Cisplatin (CDDP) / 시스플라틴", "Carboplatin (CBDCA) / 카보플라틴", "Irinotecan (CPT-11) / 이리노테칸"],
 "NPC": ["Cisplatin (CDDP) / 시스플라틴", "5-Fluorouracil (5-FU) / 5-플루오로우라실"],
 "H&N": ["Cisplatin (CDDP) / 시스플라틴", "5-Fluorouracil (5-FU) / 5-플루오로우라실"],
 "Ovary": ["Carboplatin (CBDCA) / 카보플라틴", "Paclitaxel / 파클리탁셀"],
 "Cervix": ["Cisplatin (CDDP) / 시스플라틴", "Paclitaxel / 파클리탁셀"],
 "GIST": ["Imatinib / 이매티닙(글리벡)"],
 "RCC": ["Sunitinib / 수니티닛"],
 "Glioma": ["Temozolomide (TMZ) / 테모졸로마이드"]
}


def suggest_agents_by_onco(group:str, dx:str):
    key = (dx or "").upper()
    gkey = (group or "").upper()
    # direct keyword hit
    for k, agents in CHEMO_PROTOCOLS.items():
        if k in key:
            return agents
    # Korean/aliases
    if any(s in key for s in ["APL","급성 전골수구성"]): return CHEMO_PROTOCOLS["APL"]
    if any(s in key for s in ["AML","급성 골수성"]): return CHEMO_PROTOCOLS["AML"]
    if any(s in key for s in ["ALL","급성 림프구성"]): return CHEMO_PROTOCOLS["ALL"]
    if any(s in key for s in ["CML","만성 골수성"]): return CHEMO_PROTOCOLS["CML"]
    if any(s in key for s in ["DLBCL","NHL","비호지킨"]): return CHEMO_PROTOCOLS["DLBCL"]
    if any(s in key for s in ["HODGKIN","호지킨"]): return CHEMO_PROTOCOLS["Hodgkin"]
    if any(s in key for s in ["COLON","RECT","대장","직장"]): return CHEMO_PROTOCOLS["Colon"]
    if any(s in key for s in ["GASTRIC","위암"]): return CHEMO_PROTOCOLS["Gastric"]
    if any(s in key for s in ["PANCREAS","췌장"]): return CHEMO_PROTOCOLS["Pancreas"]
    if any(s in key for s in ["BILIARY","담도","담낭","담관"]): return CHEMO_PROTOCOLS["Biliary"]
    if any(s in key for s in ["BREAST","유방"]): return CHEMO_PROTOCOLS["Breast"]
    if any(s in key for s in ["NSCLC","비소세포","폐"]): return CHEMO_PROTOCOLS["NSCLC"]
    if any(s in key for s in ["SCLC","소세포"]): return CHEMO_PROTOCOLS["SCLC"]
    if any(s in key for s in ["NPC","비인두"]): return CHEMO_PROTOCOLS["NPC"]
    if any(s in key for s in ["HEAD&NECK","두경부"]): return CHEMO_PROTOCOLS["H&N"]
    if any(s in key for s in ["OVARY","난소"]): return CHEMO_PROTOCOLS["Ovary"]
    if any(s in key for s in ["CERVIX","자궁경부"]): return CHEMO_PROTOCOLS["Cervix"]
    if any(s in key for s in ["GIST"]): return CHEMO_PROTOCOLS["GIST"]
    if any(s in key for s in ["RCC","신세포","신장암"]): return CHEMO_PROTOCOLS["RCC"]
    if any(s in key for s in ["GLIOMA","신경교종","교모세포종","GBM"]): return CHEMO_PROTOCOLS["Glioma"]
    # group fallback
    if "HEMATO" in gkey or "혈액" in (group or ""): 
        if "APL" in gkey: return CHEMO_PROTOCOLS["APL"]
        if "AML" in gkey: return CHEMO_PROTOCOLS["AML"]
        if "ALL" in gkey: return CHEMO_PROTOCOLS["ALL"]
    return []

# ---- 추가 항암제 DB (업데이트 병합) ----
EXTRA_CHEMO = {
 "Arsenic Trioxide (ATO) / 삼산화비소":{
  "effects":{"common":["{WARN} 피로/오심","{WARN} QT 연장","{WARN} 저K/저Mg"],"serious":["{DANGER} 분화증후군","{DANGER} 부정맥"]},
  "monitor":["ECG,QTc","K/Mg 보충","체중/부종","CBC"]
 },
 "Daunorubicin / 다우노루비신":{
  "effects":{"cardiac":["{DANGER} 누적 심근독성/심부전"],"blood":["{DANGER} 골수억제"]},
  "monitor":["누적용량","LVEF","CBC"]
 },
 "Idarubicin / 이다루비신":{
  "effects":{"cardiac":["{DANGER} 심독성"],"blood":["{DANGER} 골수억제"]},
  "monitor":["LVEF","CBC","간/신"]
 },
 "Vincristine (VCR) / 빈크리스틴":{
  "effects":{"neuro":["{WARN} 말초신경병증","{WARN} 변비/장폐색"],"dose_limit":["{DANGER} 신경독성 용량제한"]},
  "monitor":["신경학적 증상","변비 예방"]
 },
 "Cyclophosphamide (CTX) / 사이클로포스파마이드":{
  "effects":{"urologic":["{WARN} 출혈성 방광염 — MESNA/수분요법"],"blood":["{DANGER} 골수억제"]},
  "monitor":["CBC","혈뇨","수분섭취"]
 },
 "Doxorubicin (DOX) / 독소루비신":{
  "effects":{"cardiac":["{DANGER} 누적 심근독성"],"blood":["{DANGER} 골수억제"]},
  "monitor":["LVEF","누적용량","CBC"]
 },
 "Cisplatin (CDDP) / 시스플라틴":{
  "effects":{"renal":["{DANGER} 신독성"],"neuro":["{WARN} 말초신경병증"],"oto":["{WARN} 이독성"],"nausea":["{WARN} 고도 구토"]},
  "monitor":["Cr/eGFR","Mg/K","청력","구토예방"]
 },
 "Carboplatin (CBDCA) / 카보플라틴":{
  "effects":{"blood":["{DANGER} 혈소판감소"]},
  "monitor":["CBC(Plt)"]
 },
 "Oxaliplatin (L-OHP) / 옥살리플라틴":{
  "effects":{"neuro":["{WARN} 냉유발 감각이상","{WARN} 누적 말초신경병증"]},
  "monitor":["신경증상"]
 },
 "5-Fluorouracil (5-FU) / 5-플루오로우라실":{
  "effects":{"cardiac":["{WARN} 관상경련"],"gi":["{WARN} 구내염/설사"]},
  "monitor":["구강/장증상"]
 },
 "Capecitabine (CAP) / 카페시타빈":{
  "effects":{"hand_foot":["{WARN} 수족증후군"],"gi":["{WARN} 설사/구내염"]},
  "monitor":["피부관리","용량조절"]
 },
 "Irinotecan (CPT-11) / 이리노테칸":{
  "effects":{"gi":["{DANGER} 급성/지연성 설사 — 아트로핀/로페라미드"],"blood":["{DANGER} 골수억제"]},
  "monitor":["설사 프로토콜","CBC"]
 },
 "Paclitaxel / 파클리탁셀":{
  "effects":{"hypersens":["{WARN} 과민반응 — 전처치"],"neuro":["{WARN} 말초신경병증"]},
  "monitor":["전처치","주입반응"]
 },
 "Docetaxel / 도세탁셀":{
  "effects":{"fluid":["{WARN} 체액저류 — 스테로이드 전처치"],"blood":["{DANGER} 호중구감소증"]},
  "monitor":["전처치 스테로이드","CBC"]
 },
 "Mercaptopurine (6-MP) / 6-머캅토퓨린":{
  "effects":{"hepatic":["{WARN} 간독성/황달"],"blood":["{DANGER} 골수억제"],"genetic":["{WARN} TPMT/NUDT15 변이 시 독성↑"]},
  "monitor":["AST/ALT/Tb","CBC","TPMT/NUDT15"]
 },
 "Pemetrexed / 페메트렉시드":{
  "effects":{"gi":["{WARN} 구내염"],"hemat":["{DANGER} 골수억제"]},
  "monitor":["엽산/B12 보충","덱사 전처치","CBC"]
 },
 "Imatinib / 이매티닙(글리벡)":{
  "effects":{"edema":["{WARN} 말초부종/체중증가"],"hepatic":["{WARN} 간효소상승"]},
  "monitor":["CBC","간기능","부종/체중"]
 },
 "Sunitinib / 수니티닛":{
  "effects":{"htn":["{WARN} 고혈압"],"hand_foot":["{WARN} 수족증후군"],"thyroid":["{WARN} 갑상선 기능저하"]},
  "monitor":["혈압","피부/손발","TSH"]
 }

,
 "Gemcitabine / 젬시타빈":{
  "effects":{"blood":["{DANGER} 골수억제"],"hepatic":["{WARN} 간효소상승"],"pulmonary":["{WARN} 드물게 간질성 폐질환"]},
  "monitor":["CBC","간기능","호흡증상"]
 },
 "Nab-Paclitaxel (Abraxane) / 나브-파클리탁셀":{
  "effects":{"blood":["{DANGER} 호중구감소"],"neuro":["{WARN} 말초신경병증"]},
  "monitor":["CBC","신경증상"]
 },
 "Temozolomide (TMZ) / 테모졸로마이드":{
  "effects":{"blood":["{DANGER} 골수억제"],"gi":["{WARN} 오심/구토"]},
  "monitor":["CBC","감염징후"]
 },
 "Bevacizumab / 베바시주맙":{
  "effects":{"htn":["{WARN} 고혈압"],"bleed":["{WARN} 출혈 위험"],"gi":["{WARN} 위장관 천공(드묾)"]},
  "monitor":["혈압","단백뇨/소변","출혈징후"]
 },
 "Trastuzumab / 트라스투주맙":{
  "effects":{"cardiac":["{WARN} 심기능저하(용혈성 심근병증)"]},
  "monitor":["LVEF","심부전 증상"]
 }
}
try:
    CHEMO_DB.update(EXTRA_CHEMO)
except Exception:
    pass
def render_chemo_adverse_effects(agents, route_map=None):
    st.header("💊 항암제")
    if is_heme_cancer():
        st.warning("혈액암 환자는 비타민/철분제 섭취 시 **주의**가 필요합니다. 반드시 **주치의와 상담 후** 복용하세요.")
        st.session_state['heme_warning'] = "혈액암 환자 비타민/철분제 복용은 주치의와 상담 필요"
    else:
        st.session_state['heme_warning'] = None
    summary=[]
    if not agents:
        st.info("항암제를 선택하면 상세 부작용/모니터링 지침이 표시됩니다."); st.session_state['onco_warnings']=[]; return
    for agent in agents:
        data = CHEMO_DB.get(agent, {}); st.markdown(f"### {agent}")
        if "routes" in data:
            route = (route_map or {}).get(agent) or "IV/SC(표준용량)"
            st.markdown(f"**투여 경로/용량:** {route}")
            for line in data["routes"].get(route, []):
                st.markdown(f"- {_b(line)}")
                if "{DANGER}" in line or "소뇌독성" in line:
                    summary.append(f"{agent} [{route}]: " + _b(line).replace('🟡 ','').replace('🟢 ','').replace('🚨 ',''))
        else:
            effects=data.get("effects",{})
            for section,arr in effects.items():
                with st.expander(section):
                    for ln in arr:
                        st.markdown(f"- {_b(ln)}")
                        if "{DANGER}" in ln:
                            summary.append(f"{agent}: " + _b(ln).replace('🟡 ','').replace('🟢 ','').replace('🚨 ',''))
        if agent.startswith("ATRA") and data.get("ra_syndrome"):
            rs=data["ra_syndrome"]
            with st.expander("⚠️ RA-분화증후군"):
                for s in rs["symptoms"]:
                    st.markdown(f"- {_b(s)}")
                    if "{DANGER}" in s: summary.append("ATRA/RA-증후군: " + _b(s).replace('🚨 ',''))
    st.session_state["onco_warnings"]=list(dict.fromkeys(summary))[:60]

# ---------------- Report ----------------
def build_report():
    parts=[f"# 피수치/가이드 요약\n- 생성시각: {kst_now()}\n- 제작/자문: Hoya/GPT"]
    labs = st.session_state.get("labs_dict",{}) or {}
    keys_entered = st.session_state.get("labs_entered_keys") or []
    lab_items = []
    if keys_entered:
        for k in keys_entered:
            v = labs.get(k, "")
            if str(v).strip() != "": lab_items.append((k, v))
    else:
        for k,v in labs.items():
            if str(v).strip()!="": lab_items.append((k, v))
    if lab_items:
        parts.append("## 피수치")
        for k,v in lab_items: parts.append(f"- {k}: {v}")
    bp=st.session_state.get("bp_summary")
    if bp: parts.append("## 혈압 분류(압종분류)"); parts.append(f"- {bp}")
    g=st.session_state.get("onco_group"); d=st.session_state.get("onco_dx")
    if g or d: parts.append("## 암종 선택"); parts.append(f"- 그룹: {g or '-'} / 진단: {d or '-'}")
    peds=st.session_state.get("peds_notes",[])
    if peds: parts.append("## 소아가이드"); parts.extend([f"- {x}" for x in peds])
    lines=st.session_state.get("special_interpretations",[])
    if lines: parts.append("## 특수검사 해석"); parts.extend([f"- {ln}" for ln in lines])
    # 식이가이드: **수치 기반만 기본 포함**
    diet_lab = st.session_state.get("diet_lab_notes",[]) or []
    if diet_lab:
        parts.append("## 식이가이드")
        for x in diet_lab: parts.append(f"- (수치) {x}")
    # (옵션) 증상 기반 포함
    if st.session_state.get("include_symptom_guides_in_report"):
        symptom = st.session_state.get("symptom_diet_notes", []) or []
        if symptom:
            parts.append("## (옵션) 증상 기반 식이가이드")
            for x in symptom: parts.append(f"- {x}")
    agents=st.session_state.get("selected_agents",[]); warns=st.session_state.get("onco_warnings",[])
    if agents: parts.append("## 항암제(선택)"); parts.extend([f"- {a}" for a in agents])
    if warns: parts.append("## 항암제 부작용 요약(위험)"); parts.extend([f"- {w}" for w in warns])
    hw=st.session_state.get('heme_warning')
    if hw: parts.append("## 복용 주의"); parts.append(f"- {hw}")
    if not any(sec.startswith("##") for sec in parts[1:]): parts.append("## 입력된 데이터가 없어 기본 안내만 표시됩니다.")
    return "\n\n".join(parts)

# PDF export (optional fallback using reportlab)
def _find_pdf_export_paths():
    cands = [
        Path("/mount/src/hoya12/bloodmap_app/pdf_export.py"),
        Path("/mnt/data/pdf_export.py"),
        Path.cwd() / "pdf_export.py",
        Path(__file__).resolve().parent / "pdf_export.py",
    ]
    out, seen = [], set()
    for p in cands:
        try: rp = str(p.resolve()) if p.exists() else str(p)
        except Exception: rp = str(p)
        if rp not in seen: seen.add(rp); out.append(p)
    return out

def export_report_pdf(md_text: str) -> bytes:
    # try external
    last_err = None
    for p in _find_pdf_export_paths():
        try:
            if not p.exists(): continue
            spec = importlib.util.spec_from_file_location("pdf_export", str(p))
            mod = importlib.util.module_from_spec(spec)
            sys.modules["pdf_export"] = mod
            spec.loader.exec_module(mod)  # type: ignore
            if hasattr(mod, "export_md_to_pdf"):
                return mod.export_md_to_pdf(md_text)
        except Exception as e:
            last_err = e
    # fallback
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import cm
        import io, textwrap as tw
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        width, height = A4
        x, y = 2*cm, height-2*cm
        c.setFont("Helvetica-Bold", 14); c.drawString(x, y, "피수치/가이드 보고서"); y -= 1*cm
        c.setFont("Helvetica", 10)
        for para in md_text.split("\n\n"):
            for line in tw.wrap(para.replace("\n"," "), 90):
                if y < 2*cm:
                    c.showPage(); y = height-2*cm; c.setFont("Helvetica", 10)
                c.drawString(x, y, line); y -= 0.5*cm
            y -= 0.3*cm
        c.showPage(); c.save()
        return buf.getvalue()
    except Exception as e:
        st.warning(f"PDF 변환 모듈을 찾지 못했습니다. TXT만 제공됩니다. (last error: {last_err or e})")
        return b""

# ---------------- Feedback ----------------
def feedback_form():
    st.subheader("🗣️ 피드백 보내기")
    col1,col2 = st.columns([2,1])
    with col1:
        comment = st.text_area("피드백 내용", placeholder="개선 요청, 버그 제보, 추가 기능 등 자유롭게 적어주세요.", key=wkey("fb_comment"))
    with col2:
        rating = st.selectbox("만족도(1~5)", [5,4,3,2,1], index=0, key=wkey("fb_rating"))
        name = st.text_input("이름(선택)", key=wkey("fb_name"))
        email = st.text_input("이메일(선택)", key=wkey("fb_email"))
    if st.button("✉️ 피드백 제출", key=wkey("fb_submit")):
        row = [kst_now(), rating, name, email, comment.replace("\n"," ").strip()]
        try:
            FEED_PATH.parent.mkdir(parents=True, exist_ok=True)
            newfile = not FEED_PATH.exists()
            with FEED_PATH.open("a", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                if newfile: w.writerow(["timestamp_kst","rating","name","email","comment"])
                w.writerow(row)
            st.success("피드백이 저장되었습니다. 감사합니다!")
            st.caption(f"저장 경로: {FEED_PATH}")
        except Exception as e:
            st.error(f"피드백 저장 실패: {e}")

def feedback_stats():
    cnt = 0; avg = None
    try:
        if FEED_PATH.exists():
            import pandas as pd
            df = pd.read_csv(FEED_PATH)
            cnt = len(df.index)
            if "rating" in df.columns:
                try: avg = float(df["rating"].astype(float).mean())
                except Exception: avg = None
    except Exception:
        pass
    cols = st.columns(3)
    with cols[0]: st.metric("현재 사용자 수", f"{CURRENT_USERS} 명")
    with cols[1]: st.metric("누적 피드백", f"{cnt} 건")
    with cols[2]: st.metric("평균 만족도", f"{avg:.1f}" if avg is not None else "-")

# ---------------- Diagnostics ----------------
def diagnostics_panel():
    st.markdown("### 🔧 진단 패널 (경로/모듈 상태)")
    # onco_map
    try:
        omap, dx_display, onco_info = load_onco()
        status = "✅ 로드됨" if isinstance(omap, dict) and omap else "❌ 실패"
        st.write(f"- onco_map: **{status}** — 경로: `{onco_info}`")
    except Exception as e:
        st.write(f"- onco_map: ❌ 오류 — {e}")
    # special_tests
    try:
        mod, sp_info = _load_special_module()
        st.write(f"- special_tests: **{'✅ 로드됨' if mod else '❌ 실패'}** — 경로: `{sp_info}`")
    except Exception as e:
        st.write(f"- special_tests: ❌ 오류 — {e}")
    # lab_diet
    try:
        dmod, dpath = _load_diet_module()
        if dmod:
            attrs = [a for a in ["diet_ui","render_diet_ui","build_diet_ui","ui","get_guides_by_values","DIET_GUIDES","GUIDES","DATA"] if hasattr(dmod,a)]
            st.write(f"- lab_diet: **✅ 로드됨** — 경로: `{dpath}` — 제공 항목: {attrs or '-'}")
        else:
            st.write(f"- lab_diet: ❌ 실패 — 경로: `{dpath}`")
    except Exception as e:
        st.write(f"- lab_diet: ❌ 오류 — {e}")
    # autosave
    try:
        can_write = False
        try:
            AUTOSAVE_PATH.parent.mkdir(parents=True, exist_ok=True)
            test_p = AUTOSAVE_PATH.parent / "_write_test.tmp"
            test_p.write_text("ok", encoding="utf-8")
            can_write = True
            test_p.unlink(missing_ok=True)
        except Exception:
            can_write = False
        st.write(f"- autosave: 경로 `{AUTOSAVE_PATH}` — {'✅ 쓰기 가능' if can_write else '❌ 쓰기 불가'}")
    except Exception as e:
        st.write(f"- autosave: ❌ 오류 — {e}")

# ---------------- App Layout ----------------
st.set_page_config(page_title="피수치 가이드 — 최종본(STRICT LABS)", layout="wide")
restore_state()

st.title("피수치 가이드 — 최종본 (STRICT LABS)")
st.caption("순서: 홈 → 암종 → 항암제 → 피수치 → 특수검사 → 혈압 체크 → 소아가이드 → 보고서")

tabs = st.tabs(["🏠 홈","🧬 암종","💊 항암제","🧪 피수치","🔬 특수검사","🩺 혈압 체크","🧒 소아가이드","📄 보고서"])

with tabs[0]:
    st.subheader("홈")
    feedback_stats()
    st.markdown("---")
    diagnostics_panel()
    st.markdown("---")
    st.markdown("### 소아 가이드 바로가기")
    if st.button("🧒 홈에서 소아 가이드 열기", key=wkey("open_peds_on_home")):
        st.session_state["show_peds_on_home"] = True
    if st.session_state.get("show_peds_on_home"):
        st.info("홈에서 간편하게 소아 가이드를 바로 볼 수 있습니다.")
        c1,c2,c3 = st.columns(3)
        with c1:
            stool = st.selectbox("설사 횟수", ["0~2회","3~4회","5~6회","7회 이상"], key=wkey("home_stool"))
            diarrhea_exp = st.checkbox("설사 있음", key=wkey("home_diarrhea"))
            fever = st.selectbox("최고 체온", ["37.x","38~38.5","38.5~39","39 이상"], key=wkey("home_fever"))
            constipation = st.checkbox("변비", key=wkey("home_constipation"))
        with c2:
            persistent_vomit = st.checkbox("지속 구토", key=wkey("home_vomit"))
            oliguria = st.checkbox("소변량 급감", key=wkey("home_oligo"))
            cough = st.selectbox("기침 정도", ["없음","조금","보통","심함"], key=wkey("home_cough"))
            nasal = st.selectbox("콧물 상태", ["맑음","진득","누런"], key=wkey("home_nasal"))
        with c3:
            eye = st.selectbox("눈 분비물", ["없음","맑음","노랑-농성","양쪽"], key=wkey("home_eye"))
            abd_pain = st.selectbox("복통", ["없음","조금","보통","심함"], key=wkey("home_abd"))
            ear_pain = st.selectbox("귀 통증", ["없음","조금","보통","심함"], key=wkey("home_ear"))
            rash = st.checkbox("피부 발진", key=wkey("home_rash"))
            hives = st.checkbox("두드러기", key=wkey("home_hives"))
            migraine = st.checkbox("두통/편두통", key=wkey("home_migraine"))
            hfmd = st.checkbox("수족구 의심", key=wkey("home_hfmd"))
        render_caregiver_notes_peds(
            stool=st.session_state.get("home_stool"),
            fever=st.session_state.get("home_fever"),
            persistent_vomit=st.session_state.get("home_vomit"),
            oliguria=st.session_state.get("home_oligo"),
            cough=st.session_state.get("home_cough"),
            nasal=st.session_state.get("home_nasal"),
            eye=st.session_state.get("home_eye"),
            abd_pain=st.session_state.get("home_abd"),
            ear_pain=st.session_state.get("home_ear"),
            rash=st.session_state.get("home_rash"),
            hives=st.session_state.get("home_hives"),
            migraine=st.session_state.get("home_migraine"),
            hfmd=st.session_state.get("home_hfmd"),
            constipation=st.session_state.get("home_constipation"),
            diarrhea=st.session_state.get("home_diarrhea"),
        )
    st.markdown("---")
    feedback_form()
    with st.expander("🥗 식이가이드 열기 (lab_diet 연동)"):
        ctx = {
            "ANC": _parse_float(st.session_state.get("labs_dict", {}).get("ANC")) if st.session_state.get("labs_dict") else None,
            "fever": st.session_state.get("home_fever"),
            "constipation": st.session_state.get("home_constipation"),
            "diarrhea": st.session_state.get("home_diarrhea"),
        }
        render_diet_guides(context=ctx, key_prefix="home_")

with tabs[1]:
    onco_select_ui(); autosave_state()

with tabs[2]:
    all_agents = list(CHEMO_DB.keys())
    selected_agents = st.multiselect("항암제", all_agents, key=wkey("agents"))
if st.button("암종 기반 추천 항암제 불러오기", key=wkey("load_proto")):
    g = st.session_state.get("onco_group") or ""
    d = st.session_state.get("onco_dx") or ""
    sug = suggest_agents_by_onco(g, d)
    if sug:
        st.session_state["selected_agents"] = sug
        selected_agents = sug
        st.success("암종 기반 추천을 적용했습니다.")
    else:
        st.info("해당 진단에 대한 추천 항암제가 준비되지 않았습니다.")

    st.session_state["selected_agents"]=selected_agents
    route_map={}
    if "Cytarabine (Ara-C) / 시타라빈(아라씨)" in selected_agents:
        route_map["Cytarabine (Ara-C) / 시타라빈(아라씨)"] = st.selectbox("아라씨 제형/용량", ["IV/SC(표준용량)","HDAC(고용량)"], key=wkey("ara_route"))
    render_chemo_adverse_effects(selected_agents, route_map=route_map); autosave_state()

with tabs[3]:
    labs_input_ui(); autosave_state()

with tabs[4]:
    render_special_tests(); autosave_state()

with tabs[5]:
    bp_ui(); autosave_state()

with tabs[6]:
    c1,c2,c3 = st.columns(3)
    with c1:
        stool = st.selectbox("설사 횟수", ["0~2회","3~4회","5~6회","7회 이상"], key=wkey("stool"))
        diarrhea_exp = st.checkbox("설사 있음", key=wkey("diarrhea"))
        fever = st.selectbox("최고 체온", ["37.x","38~38.5","38.5~39","39 이상"], key=wkey("fever"))
        constipation = st.checkbox("변비", key=wkey("constipation"))
    with c2:
        persistent_vomit = st.checkbox("지속 구토", key=wkey("vomit"))
        oliguria = st.checkbox("소변량 급감", key=wkey("oligo"))
        cough = st.selectbox("기침 정도", ["없음","조금","보통","심함"], key=wkey("cough"))
        nasal = st.selectbox("콧물 상태", ["맑음","진득","누런"], key=wkey("nasal"))
    with c3:
        eye = st.selectbox("눈 분비물", ["없음","맑음","노랑-농성","양쪽"], key=wkey("eye"))
        abd_pain = st.selectbox("복통", ["없음","조금","보통","심함"], key=wkey("abd"))
        ear_pain = st.selectbox("귀 통증", ["없음","조금","보통","심함"], key=wkey("ear"))
        rash = st.checkbox("피부 발진", key=wkey("rash"))
        hives = st.checkbox("두드러기", key=wkey("hives"))
        migraine = st.checkbox("두통/편두통", key=wkey("migraine"))
        hfmd = st.checkbox("수족구 의심", key=wkey("hfmd"))
    render_caregiver_notes_peds(
        stool=stool, fever=fever, persistent_vomit=persistent_vomit, oliguria=oliguria,
        cough=cough, nasal=nasal, eye=eye, abd_pain=abd_pain, ear_pain=ear_pain,
        rash=rash, hives=hives, migraine=migraine, hfmd=hfmd,
        constipation=constipation, diarrhea=diarrhea_exp
    )
    with st.expander("🥗 식이가이드 (lab_diet 연동)"):
        ctx = {
            "ANC": _parse_float(st.session_state.get("labs_dict", {}).get("ANC")) if st.session_state.get("labs_dict") else None,
            "fever": st.session_state.get("fever"),
            "constipation": st.session_state.get("constipation"),
            "diarrhea": st.session_state.get("diarrhea"),
        }
        render_diet_guides(context=ctx, key_prefix="peds_")
    autosave_state()

with tabs[7]:
    st.header("📄 보고서")
    st.checkbox("보고서에 증상 기반 식이가이드 포함", key=wkey("include_symptom_guides_in_report"))
    md = build_report()
    st.code(md, language="markdown")
    st.download_button("📥 보고서(.txt) 다운로드", data=md.encode("utf-8"), file_name="report.txt", mime="text/plain")
    pdf_bytes = export_report_pdf(md)
    if pdf_bytes:
        st.download_button("🖨️ 보고서(.pdf) 다운로드", data=pdf_bytes, file_name="report.pdf", mime="application/pdf")
    else:
        st.warning("PDF 변환 모듈(reportlab 또는 제공된 pdf_export.py)이 동작하지 않아 TXT로만 내보낼 수 있습니다.")
    autosave_state()
