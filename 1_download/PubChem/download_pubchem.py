#!/usr/bin/env python3
"""PubChem Compound Extras Downloader.

Downloads the four PubChem "Extras" tables into ``raw/PubChem/`` and
decompresses them (the process step reads the plain, uncompressed files):

  - CID-InChI-Key
  - CID-SMILES
  - CID-Title
  - CID-Synonym-filtered

WARNING: these decompress to ~48GB total. Ensure sufficient disk space.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))  # project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))         # 1_download
from paths import RAW_PUBCHEM
from _common import download_gz

BASE = "https://ftp.ncbi.nlm.nih.gov/pubchem/Compound/Extras"
FILES = [
    "CID-InChI-Key",
    "CID-SMILES",
    "CID-Title",
    "CID-Synonym-filtered",
]


def main():
    print("=" * 80)
    print("PubChem Compound Extras Downloader")
    print("=" * 80)

    RAW_PUBCHEM.mkdir(parents=True, exist_ok=True)

    for i, name in enumerate(FILES, 1):
        print(f"\n[{i}/{len(FILES)}] {name}")
        download_gz(f"{BASE}/{name}.gz", RAW_PUBCHEM / name)

    print(f"\n✓ PubChem data ready in {RAW_PUBCHEM}")


if __name__ == "__main__":
    main()
