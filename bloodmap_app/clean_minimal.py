
import argparse, os, sys, shutil
from pathlib import Path

KEEP = {
    "app.py","requirements.txt","core_utils.py","drug_db.py","onco_map.py","ui_results.py",
    "lab_diet.py","peds_profiles.py","peds_dose.py","adult_rules.py","special_tests.py","pdf_export.py",
    "final_drug_coverage.json","config.py","branding.py","style.css","README_bundle.md","__init__.py",
}

DOC_PATTERNS = [
    "README*.md","README*.txt","CHANGELOG.txt","UPDATE_NOTES.txt",
    "NO_OMISSION_CHECKLIST.txt","SHORT_CAPTION_README.txt",
]
PATCH_PATTERNS = [
    "*_manifest.json","hotfix_*.json","*.patch","*.diff","app.diff","special_tests_patch.txt","fix_snippet.txt",
]
LEGACY_FILES = [
    "antipyretic_schedule.py","mini_antipyretic_schedule.py","mini_schedule.py","fever_dose_ui.py",
    "meds_auto_helper.py","meds_choices_block.py","carelog_ref.py","carelog_renderer_fix.py","carelog_utils.py",
    "profile_box.py","profile_box_patch.py","report_builder.py","report_qr.py","report_sections.py",
    "onco_charts.py","onco_table.py","onco_map_peds_ext.py","peds_dose_override.py","peds_dx_log.py",
    "interactions.py","safety.py","safety_flags.py","server_hotfix.py","selftest.py","inject_unified.py",
    "patch_indent_any_with.py","patch_indent_fix.py","patch_indent_generic.py","patch_keys_safely.py",
    "feature_sentry.py","bundle_addons.py","metrics_ref.py","metrics.py","short_caption.py","cancer_support.py",
    "cancer_support_panel.py","mini_schedule.py","shim_peds_alias.py","antipyretic_guard_ref.py","meds_auto_helper.py",
    "adult.py","fever_dose_ui.py", "run_app.sh","run_final.sh","run_onco.sh","prod_apply.sh","prod_one_shot_apply.sh",
    "prod_rollback.sh","check_files.sh",
]
FOLDER_CANDIDATES = ["data","fonts","pages","utils"]

def expand_patterns(base: Path, patterns):
    out = set()
    for pat in patterns:
        for p in base.glob(pat):
            out.add(p)
    return out

def plan_deletions(base: Path):
    to_delete = set()

    # 0) folders
    for d in FOLDER_CANDIDATES:
        p = base / d
        if p.exists():
            to_delete.add(p)

    # 1) docs
    to_delete |= expand_patterns(base, DOC_PATTERNS)

    # 2) manifests/patch/diff
    to_delete |= expand_patterns(base, PATCH_PATTERNS)

    # 3) legacy/experimental files
    for name in LEGACY_FILES:
        p = base / name
        if p.exists():
            to_delete.add(p)

    # 4) .py not in KEEP
    for p in base.glob("*.py"):
        if p.name not in KEEP:
            to_delete.add(p)

    # 5) all others except KEEP exact matches
    for p in base.iterdir():
        if p.is_file() and p.name in KEEP:
            continue

    # never delete keep files
    to_delete = {p for p in to_delete if p.name not in KEEP}

    return sorted(to_delete, key=lambda x: (x.is_file(), str(x)))

def run(target: Path, dry: bool):
    if not (target / "app.py").exists():
        print(f"[ERROR] app.py not found in {target}. cd into the project root.", file=sys.stderr)
        sys.exit(2)

    all_targets = []
    # root
    all_targets += plan_deletions(target)
    # optional subfolder "bloodmap_app"
    sub = target / "bloodmap_app"
    if sub.exists() and (sub / "app.py").exists() or sub.exists():
        all_targets += plan_deletions(sub)

    if not all_targets:
        print("Nothing to delete. (Already clean?)")
        return 0

    print("Planned deletions ({} items){}".format(len(all_targets), " [DRY-RUN]" if dry else ""))
    for p in all_targets:
        print(" -", p)

    if dry:
        return 0

    errors = 0
    for p in all_targets:
        try:
            if p.is_dir():
                shutil.rmtree(p, ignore_errors=False)
            else:
                p.unlink()
        except Exception as e:
            errors += 1
            print(f"[WARN] Failed to delete {p}: {e}", file=sys.stderr)

    print("Done with deletions. Errors:", errors)
    return 0 if errors == 0 else 1

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Clean to minimal runtime bundle (cross‑platform).")
    ap.add_argument("--target", default=".", help="Project root (default: .)")
    ap.add_argument("--apply", action="store_true", help="Apply deletions (omit for dry‑run)")
    args = ap.parse_args()
    sys.exit(run(Path(args.target).resolve(), dry=not args.apply))
