
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
    "ANC<500",
    "ANC 500–999",
    "발열 38.0–38.4",
    "고열 ≥38.5",
    "혈소판 <20k",
    "중증빈혈 Hb<7",
    "CRP ≥10",
    "HR>130",
    "혈뇨",
    "흑색변",
    "혈변",
    "흉통",
    "호흡곤란",
    "의식저하",
    "소변량 급감",
    "지속 구토",
    "점상출혈",
    "번개두통",
    "시야 이상"
]

# 기본 프리셋
PRESETS: Dict[str, Dict[str, float]] = {
    "기본(Default)": {
        "ANC<500": 1.8,
        "ANC 500–999": 1.4,
        "발열 38.0–38.4": 1.0,
        "고열 ≥38.5": 1.4,
        "혈소판 <20k": 1.6,
        "중증빈혈 Hb<7": 1.6,
        "CRP ≥10": 1.2,
        "HR>130": 1.2,
        "혈뇨": 1.2,
        "흑색변": 1.6,
        "혈변": 1.6,
        "흉통": 1.4,
        "호흡곤란": 1.8,
        "의식저하": 2.0,
        "소변량 급감": 1.4,
        "지속 구토": 1.2,
        "점상출혈": 1.4,
        "번개두통": 1.8,
        "시야 이상": 1.6
    },
    "중증혈소판감소": {
        "ANC<500": 1.4,
        "ANC 500–999": 1.0,
        "발열 38.0–38.4": 1.0,
        "고열 ≥38.5": 1.2,
        "혈소판 <20k": 2.0,
        "중증빈혈 Hb<7": 1.4,
        "CRP ≥10": 1.0,
        "HR>130": 1.0,
        "혈뇨": 1.6,
        "흑색변": 1.8,
        "혈변": 1.8,
        "흉통": 1.2,
        "호흡곤란": 1.4,
        "의식저하": 1.8,
        "소변량 급감": 1.2,
        "지속 구토": 1.0,
        "점상출혈": 1.8,
        "번개두통": 1.4,
        "시야 이상": 1.4
    },
    "발열-호중구감소증": {
        "ANC<500": 2.0,
        "ANC 500–999": 1.6,
        "발열 38.0–38.4": 1.4,
        "고열 ≥38.5": 1.8,
        "혈소판 <20k": 1.2,
        "중증빈혈 Hb<7": 1.2,
        "CRP ≥10": 1.4,
        "HR>130": 1.4,
        "혈뇨": 1.0,
        "흑색변": 1.2,
        "혈변": 1.2,
        "흉통": 1.4,
        "호흡곤란": 1.8,
        "의식저하": 2.0,
        "소변량 급감": 1.4,
        "지속 구토": 1.2,
        "점상출혈": 1.2,
        "번개두통": 1.6,
        "시야 이상": 1.4
    },
    "탈수/신장 우려": {
        "ANC<500": 1.2,
        "ANC 500–999": 1.0,
        "발열 38.0–38.4": 1.0,
        "고열 ≥38.5": 1.2,
        "혈소판 <20k": 1.2,
        "중증빈혈 Hb<7": 1.2,
        "CRP ≥10": 1.0,
        "HR>130": 1.2,
        "혈뇨": 1.6,
        "흑색변": 1.2,
        "혈변": 1.2,
        "흉통": 1.2,
        "호흡곤란": 1.4,
        "의식저하": 1.8,
        "소변량 급감": 1.8,
        "지속 구토": 1.6,
        "점상출혈": 1.0,
        "번개두통": 1.2,
        "시야 이상": 1.2
    }
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
