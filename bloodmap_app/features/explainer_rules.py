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
