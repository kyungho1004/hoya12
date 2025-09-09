def interpret_labs(vals, extras):
    out = []
    for k, v in (vals or {}).items():
        if v is not None and v != "":
            out.append(f"- {k}: {v}")
    return out

def compare_with_previous(nickname_key, current_vals):
    return []

def food_suggestions(vals, anc_place):
    return []

def summarize_meds(meds: dict):
    if not meds:
        return []
    lines = ["입력된 항암제 요약"]
    for k, v in meds.items():
        if isinstance(v, dict):
            if "form" in v and "dose" in v:
                lines.append(f"- {k} ({v['form']}) · {v['dose']}")
            elif "dose_or_tabs" in v:
                lines.append(f"- {k} · {v['dose_or_tabs']}")
            else:
                lines.append(f"- {k}")
        else:
            lines.append(f"- {k}")
    return lines

def abx_summary(abx_dict: dict):
    if not abx_dict:
        return []
    return ["입력된 항생제 요약"] + [f"- {k}: {v}" for k, v in abx_dict.items()]

def _interpret_specials(extra_vals, vals, profile="adult"):
    return []
