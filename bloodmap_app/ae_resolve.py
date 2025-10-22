
# ae_resolve.py
# Robust drug label→key resolution and AE/Checklist getters (shared across app and UI).

def _normalize_label(s: str) -> str:
    if not s:
        return ""
    s = str(s).strip()
    for ch in ["\u3000", "\xa0"]:
        s = s.replace(ch, " ")
    while "  " in s:
        s = s.replace("  ", " ")
    return s

def resolve_key(label_or_key: str) -> str:
    s = _normalize_label(label_or_key)
    if not s:
        return ""
    try:
        from drug_db import key_from_label, ALIAS_FALLBACK
    except Exception:
        def key_from_label(x: str) -> str:
            pos = x.find(" (")
            if pos == -1:
                pos = x.find("(")
            return x[:pos] if pos > 0 else x
        ALIAS_FALLBACK = {}
    k = key_from_label(s)
    if k in {"Ara-C", "시타라빈(Ara-C)"}:
        return "Cytarabine"
    for form in ["Cytarabine (HDAC)", "Cytarabine IV", "Cytarabine SC"]:
        if form in s:
            return form
    if "Cytarabine" in s or "시타라빈" in s:
        return "Cytarabine"
    for ek, ko in (ALIAS_FALLBACK or {}).items():
        if s == ko:
            return ek
    return k

def get_ae(label_or_key: str) -> str:
    try:
        from ae_bridge import ae_map, user_check_map  # noqa: F401
    except Exception:
        ae_map, user_check_map = {}, {}
    k = resolve_key(label_or_key)
    if k in ae_map:
        return ae_map.get(k, "")
    if "Cytarabine" in k and ("Cytarabine" in ae_map):
        return ae_map.get("Cytarabine", "")
    # --- Fallback to PROFILES ---
    try:
        from drug_db import PROFILES
        base = "Cytarabine" if ("Cytarabine" in k or "시타라빈" in k or "Ara-C" in k) else k
        prof = PROFILES.get(base) or PROFILES.get(k)
        if isinstance(prof, dict):
            ae = prof.get("ae")
            if isinstance(ae, str) and ae.strip():
                return ae
    except Exception:
        pass
    return ""

def get_checks(label_or_key: str):
    try:
        from ae_bridge import ae_map, user_check_map  # noqa: F401
    except Exception:
        ae_map, user_check_map = {}, {}
    k = resolve_key(label_or_key)
    if k in user_check_map:
        return user_check_map.get(k, [])
    if "Cytarabine" in k and ("Cytarabine" in user_check_map):
        return user_check_map.get("Cytarabine", [])
    # --- Fallback to USER_CHECK if defined ---
    try:
        from drug_db import USER_CHECK  # optional
        base = "Cytarabine" if ("Cytarabine" in k or "시타라빈" in k or "Ara-C" in k) else k
        items = USER_CHECK.get(base) or USER_CHECK.get(k) or []
        if isinstance(items, (list, tuple)):
            return list(items)
    except Exception:
        pass
    return []
