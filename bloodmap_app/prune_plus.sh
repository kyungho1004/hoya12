# Write an extended prune script that also cleans folders like data/, fonts/, pages/, utils/
from pathlib import Path

script = r"""#!/usr/bin/env bash
# prune_plus.sh — extended cleaner for folders and files
# Usage:
#   DRY_RUN=1 bash prune_plus.sh   # preview
#   bash prune_plus.sh             # execute
set -euo pipefail

[[ -f "app.py" ]] || { echo "[ERROR] app.py not found here. Run in project root."; exit 1; }

echo "=== prune_plus.sh (DRY_RUN=${DRY_RUN:-0}) ==="

delete() {
  local target="$1"
  if [[ "${DRY_RUN:-0}" == "1" ]]; then
    echo "DRY-RUN delete: $target"
  else
    if [[ -d "$target" ]]; then
      rm -rf -- "$target"
    else
      rm -f -- "$target"
    fi
    echo "deleted: $target"
  fi
}

# Keep sets (same as previous, minimal runtime)
KEEP=( app.py requirements.txt core_utils.py drug_db.py onco_map.py ui_results.py \
       lab_diet.py peds_profiles.py peds_dose.py adult_rules.py special_tests.py pdf_export.py \
       final_drug_coverage.json )
OPTIONAL=( config.py branding.py style.css )
DOC_KEEP=README_bundle.md

# 0) remove whole folders that are not used by minimal runtime
FOLDER_CANDIDATES=( data fonts pages utils )
for d in "${FOLDER_CANDIDATES[@]}"; do
  [[ -e "$d" ]] && delete "$d"
done

# 1) docs (keep one)
DOC_GLOBS=( "README*.md" "README*.txt" "CHANGELOG.txt" "UPDATE_NOTES.txt" "NO_OMISSION_CHECKLIST.txt" "SHORT_CAPTION_README.txt" )
for g in "${DOC_GLOBS[@]}"; do
  for f in $g; do
    [[ "$f" == "$DOC_KEEP" ]] && continue
    [[ -e "$f" ]] && delete "$f"
  done
done

# 2) manifests/patch/diff
PATCH_GLOBS=( "*_manifest.json" "hotfix_*.json" "*.patch" "*.diff" "app.diff" "special_tests_patch.txt" "fix_snippet.txt" )
for g in "${PATCH_GLOBS[@]}"; do
  for f in $g; do [[ -e "$f" ]] && delete "$f"; done
done

# 3) legacy/experimental py
LEGACY=( antipyretic_schedule.py mini_antipyretic_schedule.py mini_schedule.py fever_dose_ui.py \
         meds_auto_helper.py meds_choices_block.py carelog_*.py profile_box*.py report_*.py \
         onco_charts.py onco_table.py onco_map_peds_ext.py peds_dose_override.py peds_dx_log.py \
         interactions.py safety.py safety_flags.py server_hotfix.py selftest.py \
         inject_unified.py patch_*.py feature_sentry.py bundle_addons.py \
         metrics_ref.py metrics.py profile_box_patch.py profile_box.py report_builder.py \
         report_qr.py report_sections.py cancer_support.py cancer_support_panel.py \
         mini_schedule.py shim_peds_alias.py antipyretic_guard_ref.py meds_auto_helper.py )
for f in "${LEGACY[@]}"; do [[ -e "$f" ]] && delete "$f"; done

# 4) run/prod shell scripts
SH_GLOBS=( "run_*.sh" "prod_*.sh" "check_files.sh" )
for g in "${SH_GLOBS[@]}"; do
  for f in $g; do [[ -e "$f" ]] && delete "$f"; done
done

# 5) prune other .py not in KEEP/OPTIONAL
mapfile -t ALL_PY < <(ls -1 *.py 2>/dev/null || true)
protect() { for k in "${KEEP[@]}" "${OPTIONAL[@]}" "$DOC_KEEP"; do [[ "$1" == "$k" ]] && return 0; done; return 1; }
for f in "${ALL_PY[@]}"; do
  if protect "$f"; then echo "keep: $f"; else delete "$f"; fi
done

# 6) ensure one README
if [[ ! -f "$DOC_KEEP" ]]; then
  if [[ "${DRY_RUN:-0}" == "1" ]]; then
    echo "DRY-RUN write: $DOC_KEEP"
  else
    printf "# Bloodmap\n\nThis is the minimal runtime bundle.\n" > "$DOC_KEEP"
  fi
fi

echo "=== Done ==="
ls -al
"""

path = Path("/mnt/data/prune_plus.sh")
path.write_text(script, encoding="utf-8")
print(str(path))
