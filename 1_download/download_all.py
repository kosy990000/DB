#!/usr/bin/env python3
"""Stage 1 orchestrator — download all raw data sources.

Runs each per-source download script in sequence. By default ChEMBL and
PubChem are skipped because they are huge (~30GB / ~48GB); pass them
explicitly or use ``--all`` / ``--with-heavy`` to include them.

Usage (from project root):
    python 1_download/download_all.py                 # all light sources
    python 1_download/download_all.py --all           # everything incl. heavy
    python 1_download/download_all.py kegg go reactome  # only the named ones
    python 1_download/download_all.py --list          # list source names
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

# name -> (script relative to 1_download, is_heavy)
SOURCES = {
    "kegg-mapping": ("Kegg/download_mapping.py", False),
    "kegg-kgml": ("Kegg/download_kgml.py", False),
    "go": ("Go/download_go.py", False),
    "reactome": ("Reactome/download_reactome.py", False),
    "ncbi": ("NCBI/download_ncbi.py", False),
    "uniprot": ("Uniprot/download_uniprot.py", False),
    "drugbank": ("Drugbank/download_drugbank.py", False),  # needs credentials
    "chembl": ("Chembl/download_chembl.py", True),         # ~30GB
    "pubchem": ("PubChem/download_pubchem.py", True),      # ~48GB
}


def run(name):
    rel, _ = SOURCES[name]
    script = HERE / rel
    print(f"\n{'#' * 80}\n# {name}  ({rel})\n{'#' * 80}")
    result = subprocess.run([sys.executable, str(script)])
    return result.returncode == 0


def main(argv):
    if "--list" in argv:
        for name, (rel, heavy) in SOURCES.items():
            tag = "  [heavy]" if heavy else ""
            print(f"  {name:14s} {rel}{tag}")
        return

    include_heavy = "--all" in argv or "--with-heavy" in argv
    named = [a for a in argv if not a.startswith("-")]

    if named:
        unknown = [n for n in named if n not in SOURCES]
        if unknown:
            print(f"Unknown source(s): {', '.join(unknown)}", file=sys.stderr)
            print(f"Valid: {', '.join(SOURCES)}", file=sys.stderr)
            sys.exit(2)
        targets = named
    else:
        targets = [n for n, (_, heavy) in SOURCES.items() if include_heavy or not heavy]

    print(f"Sources to download: {', '.join(targets)}")
    if not include_heavy and not named:
        print("(ChEMBL + PubChem skipped — use --all to include them)")

    results = {}
    for name in targets:
        results[name] = run(name)

    print(f"\n{'=' * 80}\nSUMMARY")
    for name, ok in results.items():
        print(f"  {'✓' if ok else '✗'} {name}")
    print("=" * 80)
    if not all(results.values()):
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
