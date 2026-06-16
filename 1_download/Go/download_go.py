#!/usr/bin/env python3
"""Gene Ontology (GO) Downloader.

Downloads into ``raw/Go/``:
  - go-basic.obo   (ontology graph, plain text)
  - goa_human.gaf  (human GO annotations, gunzipped from .gaf.gz)
  - mgi.gaf        (mouse GO annotations, gunzipped from .gaf.gz)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))  # project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))         # 1_download
from paths import RAW_GO
from _common import download_file, download_gz

OBO_URL = "https://purl.obolibrary.org/obo/go/go-basic.obo"
GOA_HUMAN_URL = "https://current.geneontology.org/annotations/goa_human.gaf.gz"
MGI_URL = "https://current.geneontology.org/annotations/mgi.gaf.gz"


def main():
    print("=" * 80)
    print("Gene Ontology (GO) Downloader")
    print("=" * 80)

    RAW_GO.mkdir(parents=True, exist_ok=True)

    print("\n[1/3] go-basic.obo")
    download_file(OBO_URL, RAW_GO / "go-basic.obo")

    print("\n[2/3] goa_human.gaf")
    download_gz(GOA_HUMAN_URL, RAW_GO / "goa_human.gaf")

    print("\n[3/3] mgi.gaf")
    download_gz(MGI_URL, RAW_GO / "mgi.gaf")

    print(f"\n✓ GO data ready in {RAW_GO}")


if __name__ == "__main__":
    main()
