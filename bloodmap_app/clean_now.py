
import os, sys, shutil, fnmatch
from pathlib import Path

# Aggressive: delete these folders wholesale if present
FOLDERS = ["data", "fonts", "pages", "utils"]

# Aggressive file globs to remove
GLOBS = [
    "README*.md","README*.txt","CHANGELOG.txt","UPDATE_NOTES.txt","NO_OMISSION_CHECKLIST.txt","SHORT_CAPTION_README.txt",
    "*_manifest.json","hotfix_*.json","*.patch","*.diff","app.diff","special_tests_patch.txt","fix_snippet.txt",
    "run_*.sh","prod_*.sh","check_files.sh",
    # experimental/legacy py
    "antipyretic_schedule.py","mini_antipyretic_schedule.py","mini_schedule.py","fever_dose_ui.py",
    "meds_auto_helper.py","meds_choices_block.py","carelog_*.py","profile_box*.py","report_*.py",
    "onco_charts.py","onco_table.py","onco_map_peds_ext.py","peds_dose_override.py","peds_dx_log.py",
    "interactions.py","safety.py","safety_flags.py","server_hotfix.py","selftest.py","inject_unified.py",
    "patch_*.py","feature_sentry.py","bundle_addons.py","metrics_ref.py","metrics.py","short_caption.py",
    "cancer_support.py","cancer_support_panel.py","shim_peds_alias.py","antipyretic_guard_ref.py",
    "adult.py","fever_dose_ui.py",
]

# Always keep (do NOT delete)
KEEP = {
    "app.py","requirements.txt","core_utils.py","drug_db.py","onco_map.py","ui_results.py",
    "lab_diet.py","peds_profiles.py","peds_dose.py","adult_rules.py","special_tests.py","pdf_export.py",
    "final_drug_coverage.json","config.py","branding.py","style.css","README_bundle.md","__init__.py",
}

def main():
    root = Path(".").resolve()
    if not (root / "app.py").exists():
        print("[ERROR] Run this from the folder where app.py exists.", file=sys.stderr)
        sys.exit(2)

    print("Aggressive clean starting in:", root)

    # 1) delete folders
    for d in FOLDERS:
        p = root / d
        if p.exists():
            try:
                shutil.rmtree(p)
                print("deleted dir:", p)
            except Exception as e:
                print("[WARN] fail dir:", p, e, file=sys.stderr)

    # 2) glob deletes
    for pat in GLOBS:
        for p in root.glob(pat):
            if p.name in KEEP: 
                continue
            try:
                p.unlink()
                print("deleted file:", p)
            except IsADirectoryError:
                try:
                    shutil.rmtree(p)
                    print("deleted dir:", p)
                except Exception as e:
                    print("[WARN] fail dir:", p, e, file=sys.stderr)
            except Exception as e:
                print("[WARN] fail file:", p, e, file=sys.stderr)

    # 3) extra: delete ANY .py not in KEEP EXCEPT the 12 core + optional 4
    for p in root.glob("*.py"):
        if p.name not in KEEP:
            try:
                p.unlink()
                print("deleted extra py:", p)
            except Exception as e:
                print("[WARN] fail extra py:", p, e, file=sys.stderr)

    print("Done. Current dir listing:")
    for item in sorted(root.iterdir(), key=lambda x: x.name.lower()):
        print(" -", item.name)

if __name__ == "__main__":
    main()
