#!/usr/bin/env python3
"""DrugBank Full Database Downloader.

DrugBank requires a (free for academics) account and an approved license,
so the download is authenticated. Provide credentials via environment
variables:

    export DRUGBANK_EMAIL="you@example.com"
    export DRUGBANK_PASSWORD="..."

This downloads the latest full-database zip and extracts ``full database.xml``
into ``raw/Drugbank/``. The XML cannot be fetched anonymously; if credentials
are missing this script prints instructions and exits.
"""
import io
import os
import sys
import zipfile
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))  # project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))         # 1_download
from paths import RAW_DRUGBANK_XML
from _common import human

URL = "https://go.drugbank.com/releases/latest/downloads/all-full-database"


def main():
    print("=" * 80)
    print("DrugBank Full Database Downloader")
    print("=" * 80)

    if RAW_DRUGBANK_XML.exists():
        print(f"  [skip] {RAW_DRUGBANK_XML.name} already exists "
              f"({human(RAW_DRUGBANK_XML.stat().st_size)})")
        return

    email = os.environ.get("DRUGBANK_EMAIL")
    password = os.environ.get("DRUGBANK_PASSWORD")
    if not email or not password:
        print(
            "\n✗ DrugBank credentials not found.\n"
            "  DrugBank needs an approved account/license; the XML cannot be\n"
            "  downloaded anonymously. Set the credentials and re-run:\n\n"
            "      export DRUGBANK_EMAIL='you@example.com'\n"
            "      export DRUGBANK_PASSWORD='your-password'\n\n"
            "  Or download manually from https://go.drugbank.com/releases/latest\n"
            f"  and place 'full database.xml' at {RAW_DRUGBANK_XML}",
            file=sys.stderr,
        )
        sys.exit(1)

    RAW_DRUGBANK_XML.parent.mkdir(parents=True, exist_ok=True)
    zip_path = RAW_DRUGBANK_XML.parent / "drugbank_all_full_database.zip"

    print("  Authenticating and downloading (this is a large file)...")
    with requests.get(URL, auth=(email, password), stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(zip_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
    print(f"  [done] {zip_path.name} ({human(zip_path.stat().st_size)})")

    print("  Extracting 'full database.xml'...")
    with zipfile.ZipFile(zip_path) as zf:
        member = next((n for n in zf.namelist() if n.lower().endswith(".xml")), None)
        if member is None:
            print(f"✗ No XML found inside {zip_path.name}", file=sys.stderr)
            sys.exit(1)
        with zf.open(member) as src, open(RAW_DRUGBANK_XML, "wb") as dst:
            while True:
                buf = src.read(1024 * 1024)
                if not buf:
                    break
                dst.write(buf)

    zip_path.unlink()
    print(f"\n✓ DrugBank XML ready: {RAW_DRUGBANK_XML} "
          f"({human(RAW_DRUGBANK_XML.stat().st_size)})")


if __name__ == "__main__":
    main()
