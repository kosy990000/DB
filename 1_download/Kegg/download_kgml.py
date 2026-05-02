#!/usr/bin/env python3
"""
KEGG KGML File Downloader
Download KGML files for human (hsa) and mouse (mmu) pathways from KEGG REST API
"""

import sys
import requests
import time
from pathlib import Path
from typing import List, Tuple
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from paths import RAW_KEGG_KGML_HSA, RAW_KEGG_KGML_MMU

# KEGG REST API endpoints
KEGG_LIST_URL = "http://rest.kegg.jp/list/pathway/{organism}"
KEGG_GET_URL = "http://rest.kegg.jp/get/{pathway_id}/kgml"

# Organisms
ORGANISMS = {
    'hsa': RAW_KEGG_KGML_HSA,  # Homo sapiens (human)
    'mmu': RAW_KEGG_KGML_MMU   # Mus musculus (mouse)
}


def get_pathway_list(organism: str) -> List[str]:
    """
    Get list of pathway IDs for a given organism

    Args:
        organism: Organism code (hsa, mmu, etc.)

    Returns:
        List of pathway IDs (e.g., ['hsa00010', 'hsa00020', ...])
    """
    url = KEGG_LIST_URL.format(organism=organism)
    print(f"Fetching pathway list for {organism}...")

    response = requests.get(url)
    response.raise_for_status()

    pathway_ids = []
    for line in response.text.strip().split('\n'):
        if line:
            # Format: "path:hsa00010\tGlycolysis / Gluconeogenesis - Homo sapiens (human)"
            pathway_id = line.split('\t')[0].replace('path:', '')
            pathway_ids.append(pathway_id)

    print(f"Found {len(pathway_ids)} pathways for {organism}")
    return pathway_ids


def download_kgml(pathway_id: str, output_dir: Path) -> bool:
    """
    Download KGML file for a pathway

    Args:
        pathway_id: Pathway ID (e.g., 'hsa00010')
        output_dir: Directory to save KGML file

    Returns:
        True if successful, False otherwise
    """
    url = KEGG_GET_URL.format(pathway_id=pathway_id)
    output_file = output_dir / f"{pathway_id}.kgml"

    # Skip if already exists
    if output_file.exists():
        return True

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        # Check if response is valid XML
        if response.text.startswith('<?xml') or response.text.startswith('<pathway'):
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(response.text)
            return True
        else:
            print(f"  ✗ {pathway_id}: Invalid KGML response")
            return False

    except requests.exceptions.RequestException as e:
        print(f"  ✗ {pathway_id}: Error - {e}")
        return False


def download_all_kgml(organism: str, output_dir: Path, delay: float = 0.1) -> Tuple[int, int]:
    """
    Download all KGML files for an organism

    Args:
        organism: Organism code (hsa, mmu)
        output_dir: Output directory
        delay: Delay between requests (seconds)

    Returns:
        Tuple of (successful_count, failed_count)
    """
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get pathway list
    pathway_ids = get_pathway_list(organism)

    # Download each pathway
    successful = 0
    failed = 0

    print(f"\nDownloading KGML files for {organism}...")
    for i, pathway_id in enumerate(pathway_ids, 1):
        if download_kgml(pathway_id, output_dir):
            successful += 1
            if i % 10 == 0:
                print(f"  Progress: {i}/{len(pathway_ids)} ({successful} successful)")
        else:
            failed += 1

        # Rate limiting
        time.sleep(delay)

    print(f"\n✓ {organism}: {successful} successful, {failed} failed")
    return successful, failed


def main():
    """Main execution function"""
    print("=" * 80)
    print("KEGG KGML File Downloader")
    print("=" * 80)

    total_successful = 0
    total_failed = 0

    for organism, output_dir in ORGANISMS.items():
        successful, failed = download_all_kgml(organism, output_dir)
        total_successful += successful
        total_failed += failed
        print()

    print("=" * 80)
    print(f"DOWNLOAD COMPLETE")
    print(f"Total successful: {total_successful}")
    print(f"Total failed: {total_failed}")
    print("=" * 80)

    # Show output directories
    print("\nOutput directories:")
    for organism, output_dir in ORGANISMS.items():
        count = len(list(output_dir.glob("*.kgml"))) if output_dir.exists() else 0
        print(f"  {organism}: {output_dir} ({count} files)")


if __name__ == '__main__':
    main()
