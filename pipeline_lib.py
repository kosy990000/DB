"""Shared helpers for stage orchestrators (process_all, load_all, run_pipeline).

A "step" is (label, path, heavy) where ``path`` is a script run with the
current Python interpreter from the project root.
"""
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent


def run_step(label, script_path):
    script_path = Path(script_path)
    print(f"\n{'#' * 80}\n# {label}  ({script_path.relative_to(PROJECT_ROOT)})\n{'#' * 80}")
    result = subprocess.run([sys.executable, str(script_path)], cwd=str(PROJECT_ROOT))
    return result.returncode == 0


def run_steps(steps, argv, *, default_stop_on_error=True):
    """Run an ordered list of steps with CLI filtering.

    steps: list of (label, script_path, heavy)
    Flags in argv: --list, --all/--with-heavy, --keep-going, named labels.
    Returns the process exit code (0 = all ok).
    """
    by_label = {label: (label, path, heavy) for label, path, heavy in steps}

    if "--list" in argv:
        for label, path, heavy in steps:
            tag = "  [heavy]" if heavy else ""
            print(f"  {label:24s} {Path(path).relative_to(PROJECT_ROOT)}{tag}")
        return 0

    include_heavy = "--all" in argv or "--with-heavy" in argv
    keep_going = "--keep-going" in argv or not default_stop_on_error
    named = [a for a in argv if not a.startswith("-")]

    if named:
        unknown = [n for n in named if n not in by_label]
        if unknown:
            print(f"Unknown step(s): {', '.join(unknown)}", file=sys.stderr)
            print(f"Valid: {', '.join(by_label)}", file=sys.stderr)
            return 2
        targets = [by_label[n] for n in named]
    else:
        targets = [s for s in steps if include_heavy or not s[2]]

    print(f"Steps to run ({len(targets)}): {', '.join(t[0] for t in targets)}")
    if not include_heavy and not named:
        heavy_labels = [s[0] for s in steps if s[2]]
        if heavy_labels:
            print(f"(skipped heavy: {', '.join(heavy_labels)} — use --all to include)")

    results = {}
    for label, path, _ in targets:
        ok = run_step(label, path)
        results[label] = ok
        if not ok and not keep_going:
            print(f"\n✗ Step '{label}' failed — stopping "
                  f"(use --keep-going to continue past failures).", file=sys.stderr)
            break

    print(f"\n{'=' * 80}\nSUMMARY")
    for label, _, _ in targets:
        if label in results:
            print(f"  {'✓' if results[label] else '✗'} {label}")
        else:
            print(f"  - {label} (not run)")
    print("=" * 80)
    return 0 if results and all(results.values()) and len(results) == len(targets) else 1
