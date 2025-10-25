RULES = []

# ---- Phase 8 Step 3: Electrolyte & BP numeric-like triggers ----
# NOTE: Regex 기반이라 "숫자 비교"는 엄격 연산이 아닌 패턴 매칭임.
#       흔히 쓰는 표기(예: K<3.0, Na 122, SBP≥180 등)와 용어를 다수 포함.
RULES.extend([
    {
        "name": "전해질-저칼륨(K<3.0)",
        "patterns": [
            r"K\s*(?:<=|<)\s*3(?:\.0)?",              # K<3 or K<3.0
            r"hypokalem",                                  # hypokalemia
            r"칼륨\s*낮|저칼륨",                          # 한글 표현
        ],
        "html": "<span class='explain-chip'>저칼륨: 부정맥 위험 → K 교정·ECG 고려</span>",
    },
    {
        "name": "전해질-고칼륨(K>5.5)",
        "patterns": [
            r"K\s*(?:>=|>)\s*5\.5",                     # K>5.5
            r"hyperkalem",                                  # hyperkalemia
            r"고칼륨",                                      # 한글
        ],
        "html": "<span class='explain-chip'>고칼륨: 심전도 변화·부정맥 → 즉시 연락</span>",
    },
    {
        "name": "전해질-저나트륨(Na<125)",
        "patterns": [
            r"Na\s*(?:<=|<)\s*125",                      # Na<125
            r"hyponatrem",                                  # hyponatremia
            r"저나트륨|나트륨\s*낮",                      # 한글
        ],
        "html": "<span class='explain-chip'>저나트륨: 의식저하·경련 위험 → 즉시 연락</span>",
    },
    {
        "name": "전해질-고나트륨(Na>155)",
        "patterns": [
            r"Na\s*(?:>=|>)\s*155",                      # Na>155
            r"hypernatrem",                                 # hypernatremia
            r"고나트륨",                                    # 한글
        ],
        "html": "<span class='explain-chip'>고나트륨: 탈수·신경증상 → 수분 교정</span>",
    },
    {
        "name": "전해질-저마그네슘(Mg<1.2)",
        "patterns": [
            r"Mg\s*(?:<=|<)\s*1(?:\.2)?",               # Mg<1 or <1.2
            r"hypomagnes",                                  # hypomagnesemia
            r"저마그네슘",                                  # 한글
        ],
        "html": "<span class='explain-chip'>저Mg: QT 연장·부정맥 위험 → Mg 보충</span>",
    },
    {
        "name": "고혈압 위기(SBP≥180/DBP≥120)",
        "patterns": [
            r"SBP\s*(?:>=|≥)\s*180|DBP\s*(?:>=|≥)\s*120",
            r"180/120\+|고혈압\s*위기|hypertensive\s+crisis",
        ],
        "html": "<span class='explain-chip'>고혈압 위기: 응급 • 즉시 연락</span>",
    },
])

# ---- Phase 14: Base explainer rules (oncology terms) ----
from __future__ import annotations
import re

def _rx(s: str) -> str:
    return s

BASE_RULES = [
    {
        "name": "QT 연장",
        "patterns": [
            _rx(r"\bQTc?\b"),
            _rx(r"torsades?\s+de\s+pointes?"),
            _rx(r"QT\s*연장"),
        ],
        "html": "<span class='explain-chip'>QT 연장: 실신·돌연사 위험 ↑ → ECG 추적</span>",
    },
    {
        "name": "손발증후군",
        "patterns": [
            _rx(r"손발\s*증후군"),
            _rx(r"손발증후군"),
            _rx(r"hand[- ]?foot\s*(?:syndrome|reaction)"),
            _rx(r"HFS"),
        ],
        "html": "<span class='explain-chip'>손발증후군: 붉어짐·통증 → 보습·마찰 줄이기</span>",
    },
    {
        "name": "RA/분화 증후군",
        "patterns": [
            _rx(r"RA\s*증후군"),
            _rx(r"분화\s*증후군"),
            _rx(r"differentiation\s+syndrome"),
            _rx(r"ATRA"),
        ],
        "html": "<span class='explain-chip'>RA/분화 증후군: 발열·호흡곤란·부종 → 즉시 연락</span>",
    },
    {
        "name": "심근독성",
        "patterns": [
            _rx(r"심근\s*독성"),
            _rx(r"cardiomyopath"),
            _rx(r"LVEF\s*감소|좌심실\s*구혈률"),
        ],
        "html": "<span class='explain-chip'>심근독성: 호흡곤란/부종/흉통 → 심초음파·심장평가</span>",
    },
    {
        "name": "골수억제",
        "patterns": [
            _rx(r"골수\s*억제"),
            _rx(r"myelosuppression"),
            _rx(r"호중구\s*감소|neutropen"),
        ],
        "html": "<span class='explain-chip'>골수억제: 감염 위험 ↑ → 발열 시 즉시 연락</span>",
    },
]

try:
    RULES  # may exist from previous phases
except NameError:
    RULES = []

# Deduplicate by name while appending BASE_RULES first
def get_rules():
    seen = {r.get("name") for r in BASE_RULES}
    out = list(BASE_RULES)
    for r in RULES:
        if r.get("name") not in seen:
            out.append(r)
            seen.add(r.get("name"))
    return out

def compile_rules():
    compiled = []
    for r in get_rules():
        pats = [re.compile(p, re.I) for p in r.get("patterns", []) if p]
        compiled.append((r.get("name",""), pats, r.get("html","")))
    return compiled
# ---- Phase 20: Expand oncology/AE explainer rules ----
EXTRA_RULES = [
    {
        "name": "전자간증/중증 고혈압",
        "patterns": [
            _rx(r"전자간증|eclampsia|preeclampsia"),
            _rx(r"SBP\s*(?:>=|≥)\s*160|DBP\s*(?:>=|≥)\s*110"),
        ],
        "html": "<span class='explain-chip'>전자간증/중증 고혈압: 응급 • 즉시 연락</span>",
    },
    {
        "name": "갑상선기능저하(TKI 연관)",
        "patterns": [
            _rx(r"갑상선\s*기능저하|hypothyroid"),
            _rx(r"TKI|sunitinib|sorafenib|pazopanib|lenvatinib"),
        ],
        "html": "<span class='explain-chip'>갑상선저하: 피로/부종 → TSH/FT4 확인·보충 고려</span>",
    },
    {
        "name": "메토트렉세이트-구내염/간독성",
        "patterns": [
            _rx(r"메토트렉세이트|methotrexate|MTX"),
            _rx(r"구내염|stomatitis|mucositis|간독성|hepatotox|AST|ALT"),
        ],
        "html": "<span class='explain-chip'>MTX: 구내염·간효소상승 → 용량/중단·모니터링</span>",
    },
]

# Merge without duplicates (by name)
try:
    BASE_RULES  # from previous phase
except NameError:
    BASE_RULES = []

def get_rules():
    base = list(BASE_RULES)
    seen = {r.get("name") for r in base}
    for r in RULES:
        if r.get("name") not in seen:
            base.append(r); seen.add(r.get("name"))
    for r in EXTRA_RULES:
        if r.get("name") not in seen:
            base.append(r); seen.add(r.get("name"))
    return base
EXTRA_RULES += [
    {
        "name": "면역관문억제제(ICI) 관련 이상반응",
        "patterns": [
            _rx(r"면역관문억제|ICI|pembrolizumab|nivolumab|atezolizumab|durvalumab|ipilimumab|cemiplimab"),
            _rx(r"pneumonitis|colitis|hepatitis|hypophysitis|thyroiditis|adrenalitis"),
        ],
        "html": "<span class='explain-chip'>ICI irAE: 폐렴·대장염·간염·내분비 이상 → 즉시 연락·면역억제 고려</span>",
    },
]
EXTRA_RULES += [
    {
        "name": "항생제 관련 설사 / C. difficile",
        "patterns": [
            _rx(r"antibiotic[- ]associated\s+diarrhea|AAD"),
            _rx(r"C\.?\s*diff|Clostridioides|Clostridium\s+difficile"),
            _rx(r"toxins?\s*A|B|GDH"),
        ],
        "html": "<span class='explain-chip'>항생제 관련 설사/C. diff: 수분·격리·검사 상담</span>",
    },
]
