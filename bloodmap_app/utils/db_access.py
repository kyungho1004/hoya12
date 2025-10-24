from typing import Iterable

FIELDS_TRY = ("ae","adverse_effects","aes","desc","notes","summary")

def concat_ae_text(drug_db: dict, keys: Iterable[str] | None) -> str:
    parts = []
    if not isinstance(drug_db, dict):
        return ""
    for k in (keys or []):
        v = drug_db.get(k, {})
        if not isinstance(v, dict):
            continue
        for f in FIELDS_TRY:
            t = v.get(f)
            if isinstance(t, str) and t.strip():
                parts.append(t)
    return " ".join(parts)
