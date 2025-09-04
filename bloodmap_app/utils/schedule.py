
try:
    from ..util_core import render_schedule
except Exception:
    def render_schedule(nickname_key): 
        return None
