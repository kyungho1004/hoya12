#!/usr/bin/env bash
set -euo pipefail

echo "[1/5] Keep 리스트 외 전부 삭제 대상 표시"
# 필수 런타임(명시 보존)
KEEP=( app.py requirements.txt core_utils.py drug_db.py onco_map.py ui_results.py \
       lab_diet.py peds_profiles.py peds_dose.py adult_rules.py special_tests.py pdf_export.py \
       final_drug_coverage.json )

# 옵션 보존(쓰면 유지 / 안 쓰면 아래에서 지움)
OPTIONAL=( config.py branding.py style.css )

# 문서 1개만 남길 기본 선택
DOC_KEEP=README_bundle.md

# ------------- 삭제 후보 수집 -------------
mapfile -t ALL_PY < <(ls -1 *.py 2>/dev/null || true)
mapfile -t ALL_OTHERS < <(ls -1 * 2>/dev/null | grep -vE '\.py$' || true)

# 문서/노트/체크리스트 대거 삭제
DOC_GLOBS=( "README*.md" "README*.txt" "CHANGELOG.txt" "UPDATE_NOTES.txt" "NO_OMISSION_CHECKLIST.txt" "SHORT_CAPTION_README.txt" )
# 매니페스트/패치/디프
PATCH_GLOBS=( "*_manifest.json" "hotfix_*.json" "*.patch" "*.diff" "app.diff" "special_tests_patch.txt" "fix_snippet.txt" )
# 레거시/실험 스크립트
LEGACY=( antipyretic_schedule.py mini_antipyretic_schedule.py mini_schedule.py fever_dose_ui.py \
         meds_auto_helper.py meds_choices_block.py carelog_*.py profile_box*.py report_*.py \
         onco_charts.py onco_table.py onco_map_peds_ext.py peds_dose_override.py peds_dx_log.py \
         interactions.py safety.py safety_flags.py server_hotfix.py selftest.py \
         inject_unified.py patch_*.py feature_sentry.py )
# 실행/배포 쉘
SH_GLOBS=( "run_*.sh" "prod_*.sh" "check_files.sh" )

protect() { for k in "${KEEP[@]}" "${OPTIONAL[@]}" "$DOC_KEEP"; do [[ "$1" == "$k" ]] && return 0; done; return 1; }

echo "[2/5] 문서류 정리(대표 README만 보존: $DOC_KEEP)"
for g in "${DOC_GLOBS[@]}"; do
  for f in $g; do
    [[ "$f" == "$DOC_KEEP" ]] && continue
    [[ -e "$f" ]] && rm -f "$f"
  done
done

echo "[3/5] 매니페스트/패치/디프 제거"
for g in "${PATCH_GLOBS[@]}"; do
  for f in $g; do [[ -e "$f" ]] && rm -f "$f"; done
done

echo "[4/5] 레거시/실험 스크립트 제거"
for f in "${LEGACY[@]}"; do [[ -e "$f" ]] && rm -f "$f"; done

echo "[5/5] 실행/배포 쉘 제거"
for g in "${SH_GLOBS[@]}"; do
  for f in $g; do [[ -e "$f" ]] && rm -f "$f"; done
done

# 기타 .py 중 보존 목록 외 제거(필요 시 주석 처리)
for f in "${ALL_PY[@]}"; do
  if protect "$f"; then :; else
    [[ -e "$f" ]] && rm -f "$f"
  fi
done

# 마지막으로 깔끔한 README 하나 보장
if [[ ! -f "$DOC_KEEP" ]]; then
  echo "# Bloodmap\n\nThis is the minimal runtime bundle." > "$DOC_KEEP"
fi

echo "정리 완료. 변경 요약:"
git status --porcelain || true
