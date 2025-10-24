"""
Session helpers and keys in one place.
"""
KW_FLAG = "_bm_kw_done"

def once(st, key: str) -> bool:
    """
    Run-once guard based on st.session_state. Returns True on first call.
    """
    try:
        st.session_state.setdefault(key, False)
        if st.session_state[key]:
            return False
        st.session_state[key] = True
        return True
    except Exception:
        # If session is unavailable, just run
        return True
