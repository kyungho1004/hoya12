# -*- coding: utf-8 -*-
import importlib
def apply():
    try: mod = importlib.import_module("peds_dx_log")
    except Exception: return False, "peds_dx_log not importable"
    if not hasattr(mod, "migrate_legacy_peds_dx_if_needed"):
        if hasattr(mod, "migrate_peds_dx_if_needed"):
            setattr(mod, "migrate_legacy_peds_dx_if_needed", getattr(mod, "migrate_peds_dx_if_needed"))
            return True, "alias injected"
        else:
            return False, "no migrate function found"
    return True, "alias exists"
ok, msg = apply()
STATUS = {"ok": ok, "msg": msg}
