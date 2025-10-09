
# -*- coding: utf-8 -*-
"""
triage_weights.py
응급도 가중치 코어 로직 + 프리셋
- 점수 범위 0~100 표준화
- 요인과 가중치, 입력 신호로 응급도 지수 계산
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

# 요인 정의(순서 유지)
FACTORS: List[str] = [
    "고열",              # fever
    "호흡곤란",          # respiratory distress
    "탈수 의심",         # dehydration
    "신경학적 이상",     # neuro signs (경련, 의식저하 등)
    "출혈/혈액질환 의심", # bleeding
    "심한 통증",         # severe pain
    "보호자 직감/우려",   # caregiver concern
]

# 기본 프리셋
PRESETS: Dict[str, Dict[str, float]] = {
    "일반 소아": {
        "고열": 1.2, "호흡곤란": 1.6, "탈수 의심": 1.4, "신경학적 이상": 1.8,
        "출혈/혈액질환 의심": 1.6, "심한 통증": 1.2, "보호자 직감/우려": 1.0
    },
    "영아(6개월 미만)": {
        "고열": 1.6, "호흡곤란": 1.6, "탈수 의심": 1.6, "신경학적 이상": 1.8,
        "출혈/혈액질환 의심": 1.6, "심한 통증": 1.2, "보호자 직감/우려": 1.2
    },
    "호흡기 중심": {
        "고열": 1.2, "호흡곤란": 2.0, "탈수 의심": 1.2, "신경학적 이상": 1.6,
        "출혈/혈액질환 의심": 1.2, "심한 통증": 1.0, "보호자 직감/우려": 1.0
    },
    "탈수 의심": {
        "고열": 1.2, "호흡곤란": 1.2, "탈수 의심": 2.0, "신경학적 이상": 1.6,
        "출혈/혈액질환 의심": 1.2, "심한 통증": 1.0, "보호자 직감/우려": 1.0
    },
    "면역저하": {
        "고열": 1.6, "호흡곤란": 1.6, "탈수 의심": 1.4, "신경학적 이상": 1.8,
        "출혈/혈액질환 의심": 1.8, "심한 통증": 1.2, "보호자 직감/우려": 1.2
    },
}

@dataclass
class TriageConfig:
    weights: Dict[str, float] = field(default_factory=lambda: PRESETS["일반 소아"].copy())
    # 각 요인의 "신호 강도" (0~5)
    signals: Dict[str, float] = field(default_factory=lambda: {f: 0.0 for f in FACTORS})
    # 잠금: True면 가중치 편집 불가
    locked: Dict[str, bool] = field(default_factory=lambda: {f: False for f in FACTORS})

    def as_dict(self) -> Dict:
        return {"weights": self.weights, "signals": self.signals, "locked": self.locked}

    @staticmethod
    def from_dict(data: Dict) -> "TriageConfig":
        cfg = TriageConfig()
        for f in FACTORS:
            if "weights" in data and f in data["weights"]:
                cfg.weights[f] = float(data["weights"][f])
            if "signals" in data and f in data["signals"]:
                cfg.signals[f] = float(data["signals"][f])
            if "locked" in data and f in data["locked"]:
                cfg.locked[f] = bool(data["locked"][f])
        return cfg

def normalize_score(raw: float, max_raw: float) -> float:
    """0~100 범위로 표준화"""
    if max_raw <= 0:
        return 0.0
    val = max(0.0, min(100.0, raw / max_raw * 100.0))
    return round(val, 1)

def compute_score(cfg: TriageConfig) -> Tuple[float, Dict[str, float], float]:
    """
    총점, 기여도 dict, 최대가능치 반환
    신호 강도는 0~5, 가중치는 0.5~2.0 범위 권장
    """
    # 최대가능치: 각 요인이 신호 5라고 가정
    max_raw = sum(5.0 * cfg.weights[f] for f in FACTORS)
    contrib = {}
    raw = 0.0
    for f in FACTORS:
        c = cfg.signals[f] * cfg.weights[f]
        contrib[f] = c
        raw += c
    score = normalize_score(raw, max_raw)
    return score, contrib, max_raw

def rank_contributors(contrib: Dict[str, float], topn: int = 3) -> List[Tuple[str, float]]:
    items = sorted(contrib.items(), key=lambda x: x[1], reverse=True)
    return items[:topn]

def get_presets() -> Dict[str, Dict[str, float]]:
    return {k: v.copy() for k, v in PRESETS.items()}
