"""Central path resolver — loads config.yaml from project root."""
from pathlib import Path
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent

with open(PROJECT_ROOT / "config.yaml") as _f:
    _cfg = yaml.safe_load(_f)


def _p(key_path: str) -> Path:
    keys = key_path.split(".")
    node = _cfg
    for k in keys:
        node = node[k]
    return PROJECT_ROOT / node


# Database
DB_FILE            = _p("database")

# Raw inputs
RAW_CHEMBL_DB      = _p("raw.chembl_db")
RAW_DRUGBANK_XML   = _p("raw.drugbank_xml")
RAW_GO             = _p("raw.go")
RAW_KEGG_MAPPING   = _p("raw.kegg.mapping")
RAW_KEGG_KGML_HSA  = _p("raw.kegg.kgml_hsa")
RAW_KEGG_KGML_MMU  = _p("raw.kegg.kgml_mmu")
RAW_NCBI           = _p("raw.ncbi")
RAW_PUBCHEM        = _p("raw.pubchem")
RAW_REACTOME       = _p("raw.reactome")
RAW_UNIPROT        = _p("raw.uniprot")
RAW_GENE_MAPPING   = _p("raw.gene_mapping")

# Processed outputs
PROC_CHEMBL        = _p("processed.chembl")
PROC_DRUGBANK      = _p("processed.drugbank")
PROC_GENE_MAPPING  = _p("processed.gene_mapping")
PROC_GO            = _p("processed.go")
PROC_KEGG          = _p("processed.kegg")
PROC_NCBI          = _p("processed.ncbi")
PROC_PUBCHEM       = _p("processed.pubchem")
PROC_REACTOME      = _p("processed.reactome")
PROC_UNIPROT       = _p("processed.uniprot")
