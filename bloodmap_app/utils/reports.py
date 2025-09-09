def build_report(mode, meta, labs, cmp_lines, extra_vals, meds_lines, food_lines, abx_lines):
    parts = ["# BloodMap 간이 보고서",
             f"- 모드: {mode}",
             f"- 메타: {meta}",
             "## 입력 수치"]
    for k, v in (labs or {}).items():
        parts.append(f"- {k}: {v}")
    if cmp_lines:
        parts += ["## 변화 비교", *[f"- {x}" for x in cmp_lines]]
    if meds_lines:
        parts += ["## 항암제 요약", *[f"- {x}" for x in meds_lines]]
    if abx_lines:
        parts += ["## 항생제 요약", *[f"- {x}" for x in abx_lines]]
    if food_lines:
        parts += ["## 음식 가이드", *food_lines]
    return "\n".join(parts)

def md_to_pdf_bytes_fontlocked(_):
    # reportlab 미설치 환경에서 안전하게 실패
    raise FileNotFoundError("reportlab 미설치: PDF 변환은 나중에 환경에서 설치 후 사용하세요.")
