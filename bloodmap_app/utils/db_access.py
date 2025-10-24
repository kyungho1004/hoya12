"""
Robust helpers for accessing DRUG_DB safely.
- Field aliasing/normalization
- Nested traversal (dict/list/str)
"""
from __future__ import annotations
from typing import Iterable, Mapping, Any, List

# Canonical targets for adverse-effect related text
FIELDS_TRY = ("ae","adverse_effects","aes","desc","notes","summary")

# Common alias map → canonical key
ALIASES = {
    "adverse-effects": "adverse_effects",
    "adverseEffects": "adverse_effects",
    "adverse": "adverse_effects",
    "a/e": "adverse_effects",
    "description": "desc",
    "note": "notes",
    "summ": "summary",
}

def _canon_key(k: str) -> str:
    k2 = (k or "").strip().lower().replace(" ", "_").replace("-", "_")
    return ALIASES.get(k2, k2)

def _harvest_text_from_value(v: Any, out: List[str]) -> None:
    # Collect strings from nested structures
    if v is None:
        return
    if isinstance(v, str):
        s = v.strip()
        if s:
            out.append(s)
        return
    if isinstance(v, (list, tuple, set)):
        for item in v:
            _harvest_text_from_value(item, out)
        return
    if isinstance(v, Mapping):
        for k, val in v.items():
            _harvest_text_from_value(val, out)
        return
    # ignore other types

def concat_ae_text(drug_db: Mapping[str, Any], keys: Iterable[str] | None) -> str:
    """
    Concatenate adverse-effect-related text fields for selected drug keys.
    - Accepts various schemas thanks to aliasing and nested traversal.
    """
    parts: List[str] = []
    if not isinstance(drug_db, Mapping):
        return ""
    for k in (keys or []):
        v = drug_db.get(k, {})
        if not isinstance(v, Mapping):
            continue
        # Normalize keys into a simple view
        norm = {}
        for fk, fv in v.items():
            norm[_canon_key(str(fk))] = fv
        # Harvest across canonical field candidates
        for target in FIELDS_TRY:
            if target in norm:
                _harvest_text_from_value(norm[target], parts)
    return " ".join(parts)
