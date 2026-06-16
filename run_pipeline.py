#!/usr/bin/env python3
"""End-to-end pipeline: download -> process -> load.

Runs the three stage orchestrators in order:
    1_download/download_all.py
    2_process/process_all.py
    3_load/load_all.py

Usage (from project root):
    python run_pipeline.py                  # full pipeline, light sources only
    python run_pipeline.py --all            # include heavy sources (ChEMBL, PubChem)
    python run_pipeline.py --stage 2 3      # run only process + load
    python run_pipeline.py --from 2         # run from stage 2 onward
    python run_pipeline.py --keep-going     # don't stop on a failed stage

Notes:
    - Heavy sources (ChEMBL ~30GB, PubChem ~48GB) are skipped unless --all.
    - DrugBank download needs DRUGBANK_EMAIL / DRUGBANK_PASSWORD env vars.
    - Use 'conda run -n DB python run_pipeline.py ...' to run in the env.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

STAGES = {
    1: ("download", ROOT / "1_download/download_all.py"),
    2: ("process",  ROOT / "2_process/process_all.py"),
    3: ("load",     ROOT / "3_load/load_all.py"),
}


def parse_args(argv):
    passthrough = []
    stages = None
    start_from = None
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--stage":
            stages = []
            while i + 1 < len(argv) and argv[i + 1].isdigit():
                stages.append(int(argv[i + 1]))
                i += 1
        elif a == "--from":
            start_from = int(argv[i + 1])
            i += 1
        else:
            passthrough.append(a)
        i += 1
    return stages, start_from, passthrough


def main(argv):
    stages, start_from, passthrough = parse_args(argv)

    if stages is None:
        stages = sorted(STAGES)
    if start_from is not None:
        stages = [s for s in sorted(STAGES) if s >= start_from]

    keep_going = "--keep-going" in passthrough

    print("=" * 80)
    print("RUN PIPELINE")
    print(f"  stages : {stages}")
    print(f"  flags  : {' '.join(passthrough) or '(none)'}")
    print("=" * 80)

    results = {}
    for s in stages:
        name, script = STAGES[s]
        print(f"\n{'=' * 80}\n=== STAGE {s}: {name} ===\n{'=' * 80}")
        rc = subprocess.run([sys.executable, str(script), *passthrough], cwd=str(ROOT))
        ok = rc.returncode == 0
        results[s] = ok
        if not ok and not keep_going:
            print(f"\n✗ Stage {s} ({name}) failed — stopping.", file=sys.stderr)
            break

    print(f"\n{'=' * 80}\nPIPELINE SUMMARY")
    for s in stages:
        if s in results:
            print(f"  {'✓' if results[s] else '✗'} stage {s}: {STAGES[s][0]}")
        else:
            print(f"  - stage {s}: {STAGES[s][0]} (not run)")
    print("=" * 80)
    sys.exit(0 if all(results.get(s) for s in stages) else 1)


if __name__ == "__main__":
    main(sys.argv[1:])
