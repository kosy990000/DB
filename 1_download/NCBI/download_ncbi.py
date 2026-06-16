#!/usr/bin/env python3
"""NCBI gene_info Downloader.

Downloads ``gene_info.gz`` into ``raw/NCBI/``. The process step reads the
gzip directly, so the file is kept compressed.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))  # project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))         # 1_download
from paths import RAW_NCBI
from _common import download_file

URL = "https://ftp.ncbi.nih.gov/gene/DATA/gene_info.gz"


def main():
    print("=" * 80)
    print("NCBI gene_info Downloader")
    print("=" * 80)

    RAW_NCBI.mkdir(parents=True, exist_ok=True)
    download_file(URL, RAW_NCBI / "gene_info.gz")

    print(f"\n✓ NCBI data ready in {RAW_NCBI}")


if __name__ == "__main__":
    main()
