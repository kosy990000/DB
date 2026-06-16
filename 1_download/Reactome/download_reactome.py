#!/usr/bin/env python3
"""Reactome Downloader.

Downloads ``NCBI2Reactome_All_Levels.txt`` (NCBI gene -> Reactome pathway
mapping, all levels) into ``raw/Reactome/``.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))  # project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))         # 1_download
from paths import RAW_REACTOME
from _common import download_file

URL = "https://reactome.org/download/current/NCBI2Reactome_All_Levels.txt"


def main():
    print("=" * 80)
    print("Reactome Downloader")
    print("=" * 80)

    RAW_REACTOME.mkdir(parents=True, exist_ok=True)
    download_file(URL, RAW_REACTOME / "NCBI2Reactome_All_Levels.txt")

    print(f"\n✓ Reactome data ready in {RAW_REACTOME}")


if __name__ == "__main__":
    main()
