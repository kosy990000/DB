#!/usr/bin/env python3
"""ChEMBL SQLite Downloader.

Downloads the ChEMBL SQLite release tarball from the EBI FTP server and
extracts it under ``raw/Chembl/`` so that ``RAW_CHEMBL_DB`` exists.

Note: the SQLite release is very large (~30GB compressed). Make sure there
is enough free disk space before running.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))  # project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))         # 1_download
from paths import RAW_CHEMBL_DB
from _common import download_file, extract_tar, human

# Release must match the version encoded in config.yaml -> raw.chembl_db
RELEASE = "chembl_36"
URL = f"https://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/releases/{RELEASE}/{RELEASE}_sqlite.tar.gz"


def main():
    print("=" * 80)
    print(f"ChEMBL SQLite Downloader ({RELEASE})")
    print("=" * 80)

    if RAW_CHEMBL_DB.exists():
        print(f"  [skip] {RAW_CHEMBL_DB} already exists ({human(RAW_CHEMBL_DB.stat().st_size)})")
        return

    # raw/Chembl  <- extract here; tarball expands to chembl_36/chembl_36_sqlite/chembl_36.db
    extract_root = RAW_CHEMBL_DB.parents[2]
    tarball = extract_root / f"{RELEASE}_sqlite.tar.gz"

    download_file(URL, tarball)
    extract_tar(tarball, extract_root, skip_marker=RAW_CHEMBL_DB)

    if RAW_CHEMBL_DB.exists():
        print(f"\n✓ ChEMBL DB ready: {RAW_CHEMBL_DB} ({human(RAW_CHEMBL_DB.stat().st_size)})")
        # Tarball no longer needed once extracted.
        if tarball.exists():
            tarball.unlink()
            print(f"  [clean] removed {tarball.name}")
    else:
        print(f"\n✗ Expected DB not found after extraction: {RAW_CHEMBL_DB}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
