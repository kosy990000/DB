#!/usr/bin/env python3
"""Quick database integrity check"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / 'database' / 'database.db'

def main():
    print("="*80)
    print("Quick Database Integrity Check")
    print("="*80)
    print(f"Database: {DB_PATH}\n")

    if not DB_PATH.exists():
        print(f"ERROR: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # 1. List all tables
    print("\n1. Tables in Database:")
    print("-" * 80)
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table'
        AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """)
    tables = [row[0] for row in cursor.fetchall()]
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  {table:40s} : {count:>15,} rows")

    # 2. Check Foreign Key Integrity - ChEMBL Synonyms
    print("\n2. Foreign Key Checks:")
    print("-" * 80)

    checks = [
        ("ChEMBL Synonyms - Orphaned", """
            SELECT COUNT(*) FROM chembl_synonyms cs
            LEFT JOIN chembl_compounds cc ON cs.chembl_id = cc.chembl_id
            WHERE cc.chembl_id IS NULL
        """),
        ("ChEMBL Drug-Disease - Missing Drug", """
            SELECT COUNT(*) FROM chembl_drug_disease_relations cddr
            LEFT JOIN chembl_compounds cc ON cddr.drug_chembl_id = cc.chembl_id
            WHERE cc.chembl_id IS NULL
        """),
        ("ChEMBL Drug-Target - Missing Drug", """
            SELECT COUNT(*) FROM chembl_drug_target_relations cdtr
            LEFT JOIN chembl_compounds cc ON cdtr.drug_chembl_id = cc.chembl_id
            WHERE cc.chembl_id IS NULL
        """),
        ("ChEMBL Drug-Target - Missing Target", """
            SELECT COUNT(*) FROM chembl_drug_target_relations cdtr
            LEFT JOIN chembl_targets ct ON cdtr.target_chembl_id = ct.target_chembl_id
            WHERE ct.target_chembl_id IS NULL
        """),
        ("KEGG Genes - Missing NCBI", """
            SELECT COUNT(*) FROM kegg_genes kg
            LEFT JOIN ncbi_info ni ON kg.entrez_id = ni.entrez_id
            WHERE ni.entrez_id IS NULL
        """),
        ("KEGG Edges - Missing Source Node", """
            SELECT COUNT(*) FROM kegg_edges ke
            LEFT JOIN kegg_nodes kn ON ke.source_id = kn.node_id
            WHERE kn.node_id IS NULL
        """),
        ("KEGG Edges - Missing Target Node", """
            SELECT COUNT(*) FROM kegg_edges ke
            LEFT JOIN kegg_nodes kn ON ke.target_id = kn.node_id
            WHERE kn.node_id IS NULL
        """),
        ("DrugBank Drug-Target - Missing Drug", """
            SELECT COUNT(*) FROM drugbank_drug_target_relations ddtr
            LEFT JOIN drugbank_drugs dd ON ddtr.drugbank_id = dd.drugbank_id
            WHERE dd.drugbank_id IS NULL
        """),
    ]

    total_issues = 0
    for check_name, query in checks:
        try:
            cursor.execute(query)
            count = cursor.fetchone()[0]
            status = "✓ OK" if count == 0 else f"✗ FAIL ({count:,} issues)"
            print(f"  {check_name:50s} : {status}")
            if count > 0:
                total_issues += 1
        except Exception as e:
            print(f"  {check_name:50s} : ERROR - {e}")

    # 3. Check NULL values in NOT NULL columns
    print("\n3. NULL Value Checks (NOT NULL columns):")
    print("-" * 80)

    null_checks = [
        ("Taxon - scientific_name", "SELECT COUNT(*) FROM taxon WHERE scientific_name IS NULL"),
        ("ChEMBL Compounds - chembl_id", "SELECT COUNT(*) FROM chembl_compounds WHERE chembl_id IS NULL"),
        ("ChEMBL Targets - target_name", "SELECT COUNT(*) FROM chembl_targets WHERE target_name IS NULL"),
        ("NCBI Info - gene_symbol", "SELECT COUNT(*) FROM ncbi_info WHERE gene_symbol IS NULL"),
        ("UniProt - gene_symbol", "SELECT COUNT(*) FROM uniprot WHERE gene_symbol IS NULL"),
    ]

    for check_name, query in null_checks:
        try:
            cursor.execute(query)
            count = cursor.fetchone()[0]
            status = "✓ OK" if count == 0 else f"✗ FAIL ({count:,} NULLs)"
            print(f"  {check_name:50s} : {status}")
            if count > 0:
                total_issues += 1
        except Exception as e:
            print(f"  {check_name:50s} : ERROR - {e}")

    # 4. Check Primary Key Duplicates
    print("\n4. Primary Key Duplicate Checks:")
    print("-" * 80)

    pk_checks = [
        ("Taxon - taxon_id", "SELECT COUNT(*) FROM (SELECT taxon_id, COUNT(*) as cnt FROM taxon GROUP BY taxon_id HAVING cnt > 1)"),
        ("ChEMBL Compounds - chembl_id", "SELECT COUNT(*) FROM (SELECT chembl_id, COUNT(*) as cnt FROM chembl_compounds GROUP BY chembl_id HAVING cnt > 1)"),
        ("NCBI Info - entrez_id", "SELECT COUNT(*) FROM (SELECT entrez_id, COUNT(*) as cnt FROM ncbi_info GROUP BY entrez_id HAVING cnt > 1)"),
    ]

    for check_name, query in pk_checks:
        try:
            cursor.execute(query)
            count = cursor.fetchone()[0]
            status = "✓ OK" if count == 0 else f"✗ FAIL ({count:,} duplicates)"
            print(f"  {check_name:50s} : {status}")
            if count > 0:
                total_issues += 1
        except Exception as e:
            print(f"  {check_name:50s} : ERROR - {e}")

    # 5. Index JOIN Integrity
    print("\n5. Index JOIN Integrity Checks:")
    print("-" * 80)

    join_checks = [
        ("UniProt to ChEMBL Target - Unmapped", """
            SELECT COUNT(DISTINCT ctum.uniprot_id)
            FROM chembl_target_uniprot_mappings ctum
            LEFT JOIN uniprot u ON ctum.uniprot_id = u.uniprot_id
            WHERE u.uniprot_id IS NULL
        """),
        ("NCBI to Reactome - Unmapped Ensembl", """
            SELECT COUNT(DISTINCT rpg.ensembl_id)
            FROM reactome_pathway_genes rpg
            LEFT JOIN ncbi_ensembl ne ON rpg.ensembl_id = ne.ensembl_id
            WHERE ne.ensembl_id IS NULL
        """),
    ]

    for check_name, query in join_checks:
        try:
            cursor.execute(query)
            count = cursor.fetchone()[0]
            status = "✓ OK" if count == 0 else f"⚠ WARNING ({count:,} unmapped)"
            print(f"  {check_name:50s} : {status}")
        except Exception as e:
            print(f"  {check_name:50s} : ERROR - {e}")

    # Summary
    print("\n" + "="*80)
    print("Summary:")
    print("="*80)
    print(f"Total tables: {len(tables)}")
    print(f"Total issues found: {total_issues}")

    if total_issues == 0:
        print("\n✅ All critical integrity checks passed!")
    else:
        print(f"\n⚠️  Found {total_issues} integrity issues. Please review above.")

    conn.close()

if __name__ == '__main__':
    main()
