
try:
    from ..util_core import render_graphs
except Exception:
    def render_graphs():
        return None
