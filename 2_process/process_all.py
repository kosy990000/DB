#!/usr/bin/env python3
"""Stage 2 orchestrator — process all raw data into CSVs (processed/).

Runs each source's process scripts in dependency order. PubChem is marked
[heavy] (reads ~48GB) and skipped unless --all / explicitly named.

Usage (from project root):
    python 2_process/process_all.py                 # all light sources
    python 2_process/process_all.py --all           # everything incl. heavy
    python 2_process/process_all.py kegg-normalize go-graph   # specific steps
    python 2_process/process_all.py --list          # list step labels

Excluded by design:
    - match_chembl_synonyms.py  (post-load query tool, not a process step)
    - make_drug_bank_xml.py     (incomplete legacy stub; superseded by
                                 1_download/Drugbank/download_drugbank.py)
    - Kegg extract_kgml_types / kgml2PathwayGraph (analysis / alt builder,
                                 not consumed by 3_load)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # project root
from pipeline_lib import run_steps

P = Path(__file__).resolve().parent  # 2_process/

# (label, script, heavy) — ordered. Sources are independent; order within a
# source matters only where a later script reuses an earlier output.
STEPS = [
    ("uniprot",            P / "Uniprot/get_uniprot.py", False),
    ("ncbi",               P / "NCBI/get_ncbi_info.py", False),
    ("reactome",           P / "Reactome/getReactome.py", False),
    ("go-graph",           P / "Go/make_graph.py", False),
    ("go-goa",             P / "Go/process_goa.py", False),
    ("kegg-normalize",     P / "Kegg/normalize_kegg_mapping.py", False),
    ("kegg-pathway-list",  P / "Kegg/extract_pathway_list.py", False),
    ("kegg-edges",         P / "Kegg/parse_kgml_to_edges.py", False),
    ("chembl-compound",    P / "Chembl/get_chembl_compound.py", False),
    ("chembl-target",      P / "Chembl/get_chembl_target.py", False),
    ("chembl-disease",     P / "Chembl/get_chembl_disease.py", False),
    ("chembl-drug-target", P / "Chembl/get_drug_target.py", False),
    ("chembl-comp-disease", P / "Chembl/get_compound_disease.py", False),
    ("chembl-target-go",   P / "Chembl/get_target_go.py", False),
    ("drugbank-drug",      P / "Drugbank/get_drug_information.py", False),
    ("drugbank-drug-target", P / "Drugbank/get_drug_target_information.py", False),
    ("pubchem",            P / "PubChem/get_pubchem_compound.py", True),
]


if __name__ == "__main__":
    # Process steps are largely independent; keep going past failures by default.
    sys.exit(run_steps(STEPS, sys.argv[1:], default_stop_on_error=False))
