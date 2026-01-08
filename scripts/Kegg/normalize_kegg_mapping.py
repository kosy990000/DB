#!/usr/bin/env python3
"""
KEGG Mapping Data Normalization Script
=======================================
raw/kegg/kegg-mapping/*.csv → processed/kegg/normalized/*.csv

통일된 타입:
- gene: individual gene + gene_group
- compound: cpd:xxx
- map: path:xxx (pathway)
"""

import pandas as pd
import os
from pathlib import Path
import xml.etree.ElementTree as ET
from tqdm import tqdm

# 경로 설정
BASE_DIR = Path(__file__).resolve().parent.parent.parent
RAW_MAPPING_DIR = BASE_DIR / "raw" / "kegg" / "kegg-mapping"
RAW_KGML_HSA_DIR = BASE_DIR / "raw" / "kegg" / "kgml_hsa"
RAW_KGML_MMU_DIR = BASE_DIR / "raw" / "kegg" / "kgml_mmu"
PROCESSED_EDGES_DIR = BASE_DIR / "processed" / "Kegg" / "pathway_edges"
PROCESSED_DIR = BASE_DIR / "processed" / "Kegg" / "normalized"

# 출력 디렉토리 생성
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

print("="*60)
print("KEGG Mapping Data Normalization")
print("="*60)


# ============================================
# 1. Load Raw Data
# ============================================
print("\n📥 Step 1: Loading raw KEGG mapping files...")

hsa_gene_mapping = pd.read_csv(RAW_MAPPING_DIR / "hsa_gene_mapping.csv")
mmu_gene_mapping = pd.read_csv(RAW_MAPPING_DIR / "mmu_gene_mapping.csv")
hsa_kegg_synonyms = pd.read_csv(RAW_MAPPING_DIR / "hsa_kegg_synonyms.csv")
mmu_kegg_synonyms = pd.read_csv(RAW_MAPPING_DIR / "mmu_kegg_synonyms.csv")
compound_mapping = pd.read_csv(RAW_MAPPING_DIR / "compound_mapping.csv")
compound_synonyms = pd.read_csv(RAW_MAPPING_DIR / "compound_synonyms.csv")

print(f"  ✓ hsa_gene_mapping: {len(hsa_gene_mapping):,} rows")
print(f"  ✓ mmu_gene_mapping: {len(mmu_gene_mapping):,} rows")
print(f"  ✓ hsa_kegg_synonyms: {len(hsa_kegg_synonyms):,} rows")
print(f"  ✓ mmu_kegg_synonyms: {len(mmu_kegg_synonyms):,} rows")
print(f"  ✓ compound_mapping: {len(compound_mapping):,} rows")
print(f"  ✓ compound_synonyms: {len(compound_synonyms):,} rows")


# ============================================
# 2. Create kegg_genes table
# ============================================
print("\n🔨 Step 2: Creating kegg_genes table...")

genes = pd.concat([hsa_gene_mapping, mmu_gene_mapping], ignore_index=True)
genes = genes[['gene_id', 'entrez_id', 'organism', 'gene_type', 'chromosome', 'description']]

print(f"  ✓ Total genes: {len(genes):,}")

genes.to_csv(PROCESSED_DIR / "kegg_genes.csv", index=False)
print(f"  ✓ Saved: kegg_genes.csv")


# ============================================
# 3. Create kegg_compounds table
# ============================================
print("\n🔨 Step 3: Creating kegg_compounds table...")

compounds = compound_mapping[['compound_id', 'primary_name', 'description']].copy()

print(f"  ✓ Total compounds: {len(compounds):,}")

compounds.to_csv(PROCESSED_DIR / "kegg_compounds.csv", index=False)
print(f"  ✓ Saved: kegg_compounds.csv")


# ============================================
# 4. Create kegg_gene_synonyms table
# ============================================
print("\n🔨 Step 4: Creating kegg_gene_synonyms table...")

gene_synonyms = pd.concat([
    hsa_kegg_synonyms[['gene_id', 'synonym']],
    mmu_kegg_synonyms[['gene_id', 'synonym']]
], ignore_index=True)

# 중복 제거
gene_synonyms = gene_synonyms.drop_duplicates()

print(f"  ✓ Total gene synonyms: {len(gene_synonyms):,}")

gene_synonyms.to_csv(PROCESSED_DIR / "kegg_gene_synonyms.csv", index=False)
print(f"  ✓ Saved: kegg_gene_synonyms.csv")


# ============================================
# 5. Create kegg_compound_synonyms table
# ============================================
print("\n🔨 Step 5: Creating kegg_compound_synonyms table...")

cpd_synonyms = compound_synonyms[['compound_id', 'synonym']].copy()
cpd_synonyms = cpd_synonyms.drop_duplicates()

print(f"  ✓ Total compound synonyms: {len(cpd_synonyms):,}")

cpd_synonyms.to_csv(PROCESSED_DIR / "kegg_compound_synonyms.csv", index=False)
print(f"  ✓ Saved: kegg_compound_synonyms.csv")


# ============================================
# 6. Extract gene_groups from KGML files
# ============================================
print("\n🔨 Step 6: Extracting gene groups from KGML files...")

def parse_gene_group(name_attr):
    """
    Parse KGML entry name attribute
    'hsa:3098 hsa:3099 hsa:3101' → ['hsa:3098', 'hsa:3099', 'hsa:3101']
    """
    genes = name_attr.strip().split()
    return [g for g in genes if g.startswith(('hsa:', 'mmu:'))]

def extract_gene_groups_from_kgml(kgml_dir, organism):
    """Extract gene groups from KGML XML files"""
    gene_groups = set()
    gene_group_members = []

    kgml_files = list(kgml_dir.glob("*.kgml"))

    for kgml_file in tqdm(kgml_files, desc=f"  Parsing {organism} KGML"):
        try:
            tree = ET.parse(kgml_file)
            root = tree.getroot()

            for entry in root.findall('entry'):
                entry_type = entry.get('type')
                name = entry.get('name', '')

                if entry_type == 'gene' and name:
                    genes = parse_gene_group(name)

                    # Gene group (2개 이상)
                    if len(genes) > 1:
                        group_id = '_'.join(genes)
                        gene_groups.add((group_id, organism))

                        for gene_id in genes:
                            gene_group_members.append({
                                'group_id': group_id,
                                'member_gene_id': gene_id
                            })
        except Exception as e:
            print(f"    ⚠ Error parsing {kgml_file.name}: {e}")

    return gene_groups, gene_group_members

# Extract from hsa
hsa_groups = set()
hsa_members = []
if RAW_KGML_HSA_DIR.exists():
    hsa_groups, hsa_members = extract_gene_groups_from_kgml(RAW_KGML_HSA_DIR, 'hsa')
    print(f"  ✓ HSA gene groups: {len(hsa_groups):,}")
    print(f"  ✓ HSA group members: {len(hsa_members):,}")

# Extract from mmu
mmu_groups = set()
mmu_members = []
if RAW_KGML_MMU_DIR.exists():
    mmu_groups, mmu_members = extract_gene_groups_from_kgml(RAW_KGML_MMU_DIR, 'mmu')
    print(f"  ✓ MMU gene groups: {len(mmu_groups):,}")
    print(f"  ✓ MMU group members: {len(mmu_members):,}")

# Combine
all_groups = hsa_groups | mmu_groups
all_members = hsa_members + mmu_members

print(f"  ✓ Total unique gene groups: {len(all_groups):,}")
print(f"  ✓ Total gene group memberships: {len(all_members):,}")


# ============================================
# 7. Create kegg_nodes table
# ============================================
print("\n🔨 Step 7: Creating kegg_nodes table...")

nodes = []

# Individual genes
for _, row in genes.iterrows():
    nodes.append({
        'node_id': row['gene_id'],
        'node_type': 'gene',
        'organism': row['organism']
    })

# Gene groups
for group_id, organism in all_groups:
    nodes.append({
        'node_id': group_id,
        'node_type': 'gene',
        'organism': organism
    })

# Compounds
for _, row in compounds.iterrows():
    nodes.append({
        'node_id': row['compound_id'],
        'node_type': 'compound',
        'organism': None
    })

# Pathways (from processed/Kegg/pathway_list.csv)
pathway_list_file = BASE_DIR / "processed" / "Kegg" / "pathway_list.csv"
if pathway_list_file.exists():
    pathways = pd.read_csv(pathway_list_file)
    for _, row in pathways.iterrows():
        nodes.append({
            'node_id': row['pathway_id'],
            'node_type': 'map',
            'organism': row['organism']
        })
    print(f"  ✓ Added {len(pathways):,} pathways")

nodes_df = pd.DataFrame(nodes)
nodes_df = nodes_df.drop_duplicates(subset=['node_id'])

print(f"  ✓ Total nodes: {len(nodes_df):,}")
print(f"    - genes (individual): {len(genes):,}")
print(f"    - genes (groups): {len(all_groups):,}")
print(f"    - compounds: {len(compounds):,}")
print(f"    - maps: {len(pathways) if pathway_list_file.exists() else 0:,}")

nodes_df.to_csv(PROCESSED_DIR / "kegg_nodes.csv", index=False)
print(f"  ✓ Saved: kegg_nodes.csv")


# ============================================
# 8. Create kegg_gene_group_members table
# ============================================
print("\n🔨 Step 8: Creating kegg_gene_group_members table...")

members_df = pd.DataFrame(all_members)
if len(members_df) > 0:
    members_df = members_df.drop_duplicates()

print(f"  ✓ Total gene group members: {len(members_df):,}")

members_df.to_csv(PROCESSED_DIR / "kegg_gene_group_members.csv", index=False)
print(f"  ✓ Saved: kegg_gene_group_members.csv")


# ============================================
# Summary
# ============================================
print("\n" + "="*60)
print("✅ Normalization completed!")
print("="*60)
print(f"\n📂 Output directory: {PROCESSED_DIR}")
print(f"\nGenerated files:")
print(f"  1. kegg_genes.csv              : {len(genes):,} rows")
print(f"  2. kegg_compounds.csv          : {len(compounds):,} rows")
print(f"  3. kegg_gene_synonyms.csv      : {len(gene_synonyms):,} rows")
print(f"  4. kegg_compound_synonyms.csv  : {len(cpd_synonyms):,} rows")
print(f"  5. kegg_nodes.csv              : {len(nodes_df):,} rows")
print(f"  6. kegg_gene_group_members.csv : {len(members_df):,} rows")
