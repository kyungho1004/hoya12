
# -*- coding: utf-8 -*-
"""
drug_db_guard — robust loader for chemo/targeted/immuno/abx lists
- Tries drug_db.DRUG_DB first; if empty, loads final_drug_coverage.json from common locations.
- Exposes: load_choices(), display_label_safe(code, meta)
"""

from __future__ import annotations
from typing import Dict, List, Tuple

def display_label_safe(code: str, meta) -> str:
    # meta may be dict with 'ko'/'en' or string
    try:
        if isinstance(meta, dict):
            ko = meta.get("ko") or meta.get("name_ko")
            en = meta.get("en") or meta.get("name_en") or meta.get("name")
            if ko and en:
                return f"{ko} / {en} ({code})"
            if ko:
                return f"{ko} ({code})"
            if en:
                return f"{en} ({code})"
        if isinstance(meta, str):
            return f"{meta} ({code})"
    except Exception:
        pass
    return code

def _read_json(path: str):
    import json
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _first_existing(paths):
    import os
    for p in paths:
        if p and os.path.exists(p):
            return p
    return None

def _fallback_load() -> Dict:
    candidates = [
        "final_drug_coverage.json",
        "data/final_drug_coverage.json",
        "/mnt/data/final_drug_coverage.json",
        os.path.join(os.getcwd(), "final_drug_coverage.json"),
    ]
    p = _first_existing(candidates)
    if not p:
        return {}
    try:
        j = _read_json(p)
        # Expected top-level keys: chemo, targeted, immuno, abx
        return j if isinstance(j, dict) else {}
    except Exception:
        return {}

def load_choices() -> Dict[str, List[Tuple[str, str]]]:
    # Try official module first
    try:
        from drug_db import DRUG_DB, ensure_onco_drug_db, display_label as display_label_official
        ensure_onco_drug_db(DRUG_DB)
        db = DRUG_DB or {}
        def _choices(kind):
            src = db.get(kind) or {}
            return [(c, display_label_official(c, src.get(c))) for c in src.keys()]
        chemo = _choices("chemo")
        tgt   = _choices("targeted") + _choices("immuno")
        abx   = _choices("abx")
        if chemo or tgt or abx:
            return {"chemo": chemo, "tgt": tgt, "abx": abx}
    except Exception:
        pass

    # Fallback to JSON
    j = _fallback_load()
    if not isinstance(j, dict):
        return {"chemo": [], "tgt": [], "abx": []}

    def _c(kind):
        src = j.get(kind) or {}
        return [(c, display_label_safe(c, src.get(c))) for c in src.keys()]

    return {"chemo": _c("chemo"), "tgt": _c("targeted") + _c("immuno"), "abx": _c("abx")}
