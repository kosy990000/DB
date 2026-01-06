#!/usr/bin/env python3
"""
Extract KEGG Pathway Lists
Parse KGML files and create pathway lists for human and mouse
"""

import xml.etree.ElementTree as ET
from pathlib import Path
import pandas as pd

# Input directories
RAW_DIR = Path("raw/kegg")
KGML_HSA = RAW_DIR / "kgml_hsa"
KGML_MMU = RAW_DIR / "kgml_mmu"

# Output directory
OUTPUT_DIR = Path("processed/Kegg")

# Organism information
ORGANISM_INFO = {
    'hsa': {'taxon_id': '9606', 'species': 'Homo sapiens'},
    'mmu': {'taxon_id': '10090', 'species': 'Mus musculus'}
}


def extract_pathway_info(kgml_file: Path) -> dict:
    """
    Extract pathway information from KGML file

    Args:
        kgml_file: Path to KGML file

    Returns:
        Dictionary with pathway information
    """
    try:
        tree = ET.parse(kgml_file)
        root = tree.getroot()

        # Extract attributes from <pathway> root element
        pathway_id = root.get('name', '')  # e.g., "path:hsa00010"
        pathway_name = root.get('title', '')  # e.g., "Glycolysis / Gluconeogenesis"
        pathway_org = root.get('org', '')  # e.g., "hsa"
        pathway_number = root.get('number', '')  # e.g., "00010"
        pathway_link = root.get('link', '')  # e.g., "https://www.kegg.jp/..."

        # Clean pathway_id (remove "path:" prefix)
        if pathway_id.startswith('path:'):
            pathway_id = pathway_id.replace('path:', '')

        return {
            'pathway_id': pathway_id,
            'pathway_number': pathway_number,
            'organism': pathway_org,
            'pathway_name': pathway_name,
            'link': pathway_link
        }

    except Exception as e:
        print(f"Error parsing {kgml_file.name}: {e}")
        return None


def extract_pathway_list(kgml_dir: Path, organism: str) -> pd.DataFrame:
    """
    Extract pathway list from KGML directory

    Args:
        kgml_dir: Directory containing KGML files
        organism: Organism code (hsa, mmu)

    Returns:
        DataFrame with pathway information
    """
    print(f"\nExtracting pathway list for {organism}...")

    kgml_files = sorted(kgml_dir.glob("*.kgml"))
    print(f"Found {len(kgml_files)} KGML files")

    pathways = []
    for kgml_file in kgml_files:
        info = extract_pathway_info(kgml_file)
        if info:
            pathways.append(info)

    df = pd.DataFrame(pathways)

    # Add taxon_id and species
    if organism in ORGANISM_INFO:
        df['taxon_id'] = ORGANISM_INFO[organism]['taxon_id']
        df['species'] = ORGANISM_INFO[organism]['species']

    # Reorder columns
    columns = ['pathway_id', 'pathway_number', 'organism', 'taxon_id', 'species', 'pathway_name', 'link']
    df = df[columns]

    # Sort by pathway_number
    if 'pathway_number' in df.columns:
        df = df.sort_values('pathway_number')

    print(f"Extracted {len(df)} pathways")

    return df


def main():
    """Main execution function"""
    print("=" * 80)
    print("KEGG Pathway List Extraction")
    print("=" * 80)

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Extract human pathways
    df_hsa = extract_pathway_list(KGML_HSA, 'hsa')
    print(f"✓ Human pathways extracted: {len(df_hsa)}")

    # Extract mouse pathways
    df_mmu = extract_pathway_list(KGML_MMU, 'mmu')
    print(f"✓ Mouse pathways extracted: {len(df_mmu)}")

    # Combine both
    df_combined = pd.concat([df_hsa, df_mmu], ignore_index=True)

    # Save combined file
    output_combined = OUTPUT_DIR / 'pathway_list.csv'
    df_combined.to_csv(output_combined, index=False, encoding='utf-8-sig')
    print(f"\n✓ Saved combined file: {output_combined}")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Human pathways: {len(df_hsa)}")
    print(f"Mouse pathways: {len(df_mmu)}")
    print(f"Total combined: {len(df_combined)}")
    print(f"\nOutput file:")
    print(f"  - {output_combined}")

    # Show sample
    print("\n" + "=" * 80)
    print("Sample - Combined Pathways (first 5 human, first 5 mouse)")
    print("=" * 80)
    sample_hsa = df_combined[df_combined['organism'] == 'hsa'].head(5)
    sample_mmu = df_combined[df_combined['organism'] == 'mmu'].head(5)
    sample = pd.concat([sample_hsa, sample_mmu])
    print(sample[['pathway_id', 'organism', 'taxon_id', 'species', 'pathway_name']].to_string(index=False))

    print("\n" + "=" * 80)
    print("Species distribution")
    print("=" * 80)
    print(df_combined.groupby(['organism', 'taxon_id', 'species']).size().reset_index(name='count'))


if __name__ == '__main__':
    main()
