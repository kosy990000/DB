#!/usr/bin/env python3
"""
KEGG KGML Parser - Extract Gene-Gene Interactions
Parse KGML files and create edge lists for network analysis
"""

import xml.etree.ElementTree as ET
from pathlib import Path
import pandas as pd
from typing import List, Dict

# Input directories
RAW_DIR = Path("raw/kegg")
KGML_HSA = RAW_DIR / "kgml_hsa"
KGML_MMU = RAW_DIR / "kgml_mmu"

# Output directory
OUTPUT_DIR = Path("processed/Kegg")
OUTPUT_EDGES_DIR = OUTPUT_DIR / "pathway_edges"


def parse_kgml_to_edges(kgml_file: Path) -> List[Dict]:
    """
    Parse KGML file and extract relations as edges

    Args:
        kgml_file: Path to KGML file

    Returns:
        List of edge dictionaries
    """
    tree = ET.parse(kgml_file)
    root = tree.getroot()

    pathway_id = root.get('name', '').replace('path:', '')  # hsa00010
    pathway_name = root.get('title', '')
    organism = root.get('org', '')

    # Build entry_id -> entry info mapping
    entries = {}
    for entry in root.findall("entry"):
        entry_id = entry.get("id")
        entry_type = entry.get("type")
        entry_name = entry.get("name", "")  # e.g., "hsa:5923 hsa:5924"

        entries[entry_id] = {
            'type': entry_type,
            'name': entry_name
        }

    # Extract edges from relations
    edges = []

    for rel in root.findall("relation"):
        entry1_id = rel.get("entry1")
        entry2_id = rel.get("entry2")
        rel_type = rel.get("type")

        # Get source and target info
        if entry1_id not in entries or entry2_id not in entries:
            continue

        source_entry = entries[entry1_id]
        target_entry = entries[entry2_id]

        # Get subtypes
        subtypes = []
        for subtype in rel.findall("subtype"):
            subtype_name = subtype.get("name")
            if subtype_name:
                subtypes.append(subtype_name)

        subtype_str = "; ".join(subtypes) if subtypes else None

        # Process entity names
        # For genes with multiple IDs, join with underscore
        # For other entities, use as-is
        source_name = source_entry['name']
        target_name = target_entry['name']

        if not source_name or not target_name:
            continue

        # If gene type and has multiple IDs, join with underscore
        if source_entry['type'] == 'gene' and ' ' in source_name:
            source_name = source_name.replace(' ', '_')

        if target_entry['type'] == 'gene' and ' ' in target_name:
            target_name = target_name.replace(' ', '_')

        # Create single edge
        edges.append({
            'source': source_name,
            'source_type': source_entry['type'],
            'target': target_name,
            'target_type': target_entry['type'],
            'relation_type': rel_type,
            'relation_subtype': subtype_str,
            'pathway_id': pathway_id,
            'pathway_name': pathway_name,
            'organism': organism
        })

    return edges


def parse_all_kgml(kgml_dir: Path, organism: str) -> int:
    """
    Parse all KGML files in directory and save each as separate CSV

    Args:
        kgml_dir: Directory containing KGML files
        organism: Organism code (hsa, mmu)

    Returns:
        Number of pathways processed
    """
    print(f"\nParsing KGML files for {organism}...")

    kgml_files = sorted(kgml_dir.glob("*.kgml"))
    print(f"Found {len(kgml_files)} KGML files")

    pathway_count = 0
    total_edges = 0

    for kgml_file in kgml_files:
        try:
            edges = parse_kgml_to_edges(kgml_file)
            if edges:
                # Get pathway ID from first edge
                pathway_id = edges[0]['pathway_id']

                # Create DataFrame
                df = pd.DataFrame(edges)

                # Save to separate CSV file
                output_file = OUTPUT_EDGES_DIR / f"{pathway_id}.csv"
                df.to_csv(output_file, index=False, encoding='utf-8-sig')

                pathway_count += 1
                total_edges += len(edges)

                if pathway_count % 50 == 0:
                    print(f"  Processed: {pathway_count}/{len(kgml_files)} pathways, {total_edges} total edges")

        except Exception as e:
            print(f"  Error parsing {kgml_file.name}: {e}")

    print(f"✓ Completed: {pathway_count} pathways, {total_edges} edges")
    return pathway_count


def main():
    """Main execution function"""
    print("=" * 80)
    print("KEGG KGML Parser - Individual Pathway Edge Files")
    print("=" * 80)

    # Create output directories
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_EDGES_DIR.mkdir(parents=True, exist_ok=True)

    # Parse human pathways
    hsa_count = parse_all_kgml(KGML_HSA, 'hsa')

    # Parse mouse pathways
    mmu_count = parse_all_kgml(KGML_MMU, 'mmu')

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Human pathway files: {hsa_count}")
    print(f"Mouse pathway files: {mmu_count}")
    print(f"Total CSV files: {hsa_count + mmu_count}")
    print(f"\nOutput directory: {OUTPUT_EDGES_DIR}")

    # Show sample files
    print("\n" + "=" * 80)
    print("Sample Files")
    print("=" * 80)
    csv_files = sorted(OUTPUT_EDGES_DIR.glob("*.csv"))
    print(f"\nTotal files created: {len(csv_files)}")
    print("\nFirst 10 files:")
    for f in csv_files[:10]:
        print(f"  - {f.name}")

    # Show sample content
    if csv_files:
        sample_file = csv_files[0]
        print(f"\n" + "=" * 80)
        print(f"Sample Content: {sample_file.name}")
        print("=" * 80)
        df_sample = pd.read_csv(sample_file)
        print(f"\nEdges in this pathway: {len(df_sample)}")
        cols = ['source', 'source_type', 'target', 'target_type', 'relation_type', 'relation_subtype']
        print("\nFirst 5 edges:")
        print(df_sample[cols].head().to_string(index=False))


if __name__ == '__main__':
    main()
