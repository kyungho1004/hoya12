
# ae_resolve.py
# Robust drug label→key resolution and AE/Checklist getters (shared across app and UI).

def _normalize_label(s: str) -> str:
    if not s:
        return ""
    s = str(s).strip()
    # common trims
    for ch in ["\u3000", "\xa0"]:  # ideographic space, nbsp
        s = s.replace(ch, " ")
    while "  " in s:
        s = s.replace("  ", " ")
    return s

def resolve_key(label_or_key: str) -> str:
    """Return canonical key for a display label/alias (very defensive)."""
    s = _normalize_label(label_or_key)
    if not s:
        return ""
    try:
        from drug_db import key_from_label, ALIAS_FALLBACK
    except Exception:
        def key_from_label(x: str) -> str:
            # split on first '(' with or without space
            pos = x.find(" (")
            if pos == -1:
                pos = x.find("(")
            return x[:pos] if pos > 0 else x
        ALIAS_FALLBACK = {}
    # 1) bare extraction
    k = key_from_label(s)
    # 2) special-case Ara-C synonyms
    if k in {"Ara-C", "시타라빈(Ara-C)"}:
        return "Cytarabine"
    # 3) Cytarabine HD/SC/IV keep as-is
    for form in ["Cytarabine (HDAC)", "Cytarabine IV", "Cytarabine SC"]:
        if form in s:
            return form
    # 4) If base contains 'Cytarabine' assume base drug
    if "Cytarabine" in s or "시타라빈" in s:
        return "Cytarabine"
    # 5) If alias map contains this exact display, map back to its English key via reverse search
    if ALIAS_FALLBACK:
        # direct alias lookup
        for ek, ko in ALIAS_FALLBACK.items():
            if s == ko:
                return ek
    return k

def get_ae(label_or_key: str) -> str:
    try:
        from ae_bridge import ae_map, user_check_map  # noqa
    except Exception:
        ae_map, user_check_map = {}, {}
    k = resolve_key(label_or_key)
    # direct hit
    if k in ae_map:
        return ae_map.get(k, "")
    # fallbacks for Cytarabine family
    if "Cytarabine" in k:
        return ae_map.get("Cytarabine", "")
    # final: try base without form
    base = resolve_key(k)
    return ae_map.get(base, "") or ""

def get_checks(label_or_key: str):
    try:
        from ae_bridge import ae_map, user_check_map  # noqa
    except Exception:
        ae_map, user_check_map = {}, {}
    k = resolve_key(label_or_key)
    if k in user_check_map:
        return user_check_map.get(k, [])
    if "Cytarabine" in k:
        return user_check_map.get("Cytarabine", [])
    base = resolve_key(k)
    return user_check_map.get(base, [])
