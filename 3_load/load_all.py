#!/usr/bin/env python3
"""Stage 3 orchestrator — load processed CSVs into the SQLite DB.

Order matters: schema first, then taxon (FK base table), then the
independent sources, then PubChem (heavy) last. SQLite has no concurrent
writes, so steps run strictly sequentially.

Usage (from project root):
    python 3_load/load_all.py                 # all light sources
    python 3_load/load_all.py --all           # everything incl. PubChem
    python 3_load/load_all.py schema taxon ncbi   # specific steps
    python 3_load/load_all.py --list          # list step labels

Stops on the first failure by default (downstream FKs depend on taxon);
pass --keep-going to continue past failures.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # project root
from pipeline_lib import run_steps

P = Path(__file__).resolve().parent  # 3_load/

STEPS = [
    ("schema",   P / "schema/create_schema.py", False),
    ("taxon",    P / "Common/import_taxon_to_db.py", False),
    ("ncbi",     P / "NCBI/import_ncbi_to_db.py", False),
    ("uniprot",  P / "Uniprot/import_uniprot_to_db.py", False),
    ("chembl",   P / "Chembl/import_chembl_to_db.py", False),
    ("drugbank", P / "Drugbank/import_drugbank_to_db.py", False),
    ("go",       P / "Go/import_go_to_db.py", False),
    ("kegg",     P / "Kegg/import_kegg_to_db.py", False),
    ("reactome", P / "Reactome/import_reactome_to_db.py", False),
    ("pubchem",  P / "PubChem/import_pubchem_to_db.py", True),
]


if __name__ == "__main__":
    sys.exit(run_steps(STEPS, sys.argv[1:], default_stop_on_error=True))
