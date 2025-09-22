# -*- coding: utf-8 -*-
def run_self_checks():
    res = {}
    try:
        from onco_antipyretic_log import _ko_label_event
        s1 = _ko_label_event({"type":"vomit","ts":"t","kind":"초록(담즙)"})
        s2 = _ko_label_event({"type":"diarrhea","ts":"t","kind":"녹색혈변"})
        res["ko"] = ("구토" in s1) and ("설사" in s2)
    except Exception:
        res["ko"] = False
    try:
        import shim_peds_alias; res["alias"] = shim_peds_alias.STATUS.get("ok", False)
    except Exception:
        res["alias"] = False
    return res
