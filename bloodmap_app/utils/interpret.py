
try:
    from ..util_core import interpret_labs, compare_with_previous, food_suggestions, summarize_meds, abx_summary
except Exception:
    def interpret_labs(vals, extras): return []
    def compare_with_previous(key, cur): return []
    def food_suggestions(vals, place): return []
    def summarize_meds(meds): return [f"- {k}: 입력됨" for k in meds.keys()]
    def abx_summary(extras): return []
