def render_modular_sections(st, picked_keys=None, DRUG_DB=None):
    
    tab = st.session_state.get("_router_tab", "전체")
    def _show(key: str, label: str) -> bool:
        try:
            return bool(st.session_state.get(key, True)) and (tab in ("전체", label))
        except Exception:
            return True
    
    try:
        ss = st.session_state
        ss["_modular_render"] = True  # mark modular mode
        # AE
        if _show("_show_ae", "AE"):
            try:
                from features.pages.ae import render as _ae
                _ae(st, picked_keys, DRUG_DB)
            except Exception:
                pass
        # Special tests
        if _show("_show_special", "특수검사"):
            try:
                from features.pages.special import render as _sp
                _sp(st)
            except Exception:
                pass
        # Exports cluster
        if _show("_show_exports", "내보내기"):
            try:
                from features.pages.exports import render as _ex
                _ex(st, picked_keys)
            except Exception:
                pass
        # Pediatrics cluster
        if _show("_show_peds", "소아"):
            try:
                from features.pages.peds import render as _peds
                _peds(st)
            except Exception:
                pass
        # Hint for legacy blocks (if they check)
        ss["_ae_main_rendered"] = True
        ss["_stests_rendered"] = True
    except Exception:
        pass
