#!/usr/bin/env python3
"""UniProt ID-mapping Downloader.

Downloads the human and mouse ID-mapping tables into ``raw/Uniprot/``.
The process step reads the gzip directly, so files are kept compressed.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))  # project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))         # 1_download
from paths import RAW_UNIPROT
from _common import download_file

BASE = "https://ftp.uniprot.org/pub/databases/uniprot/current_release/knowledgebase/idmapping/by_organism"
FILES = {
    "HUMAN_9606_idmapping.dat.gz": f"{BASE}/HUMAN_9606_idmapping.dat.gz",
    "MOUSE_10090_idmapping.dat.gz": f"{BASE}/MOUSE_10090_idmapping.dat.gz",
}


def main():
    print("=" * 80)
    print("UniProt ID-mapping Downloader")
    print("=" * 80)

    RAW_UNIPROT.mkdir(parents=True, exist_ok=True)
    for i, (name, url) in enumerate(FILES.items(), 1):
        print(f"\n[{i}/{len(FILES)}] {name}")
        download_file(url, RAW_UNIPROT / name)

    print(f"\n✓ UniProt data ready in {RAW_UNIPROT}")


if __name__ == "__main__":
    main()
