#!/usr/bin/env python3
"""
Query Drug & Pathway Information by Entrez ID
==============================================
Usage:
    python3 query_by_entrez.py 2056           # EGFR
    python3 query_by_entrez.py 7157           # TP53
    python3 query_by_entrez.py 5594           # MAPK1
"""

import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / 'database' / 'database.db'

def query_gene_info(cursor, entrez_id):
    """Gene 기본 정보"""
    cursor.execute("""
        SELECT entrez_id, gene_symbol, species, taxon_id, description
        FROM ncbi_info
        WHERE entrez_id = ?
    """, (entrez_id,))
    return cursor.fetchone()

def query_drugbank(cursor, entrez_id):
    """DrugBank 약물 정보"""
    cursor.execute("""
        SELECT
            dd.drugbank_id,
            dd.name,
            dd.type,
            dd.groups,
            ddtr.actions,
            ddtr.known_action
        FROM ncbi_info ni
        JOIN uniprot u ON ni.gene_symbol = u.gene_symbol AND ni.taxon_id = u.taxon_id
        JOIN drugbank_targets dt ON u.uniprot_id = dt.uniprot_id
        JOIN drugbank_drug_target_relations ddtr ON dt.uniprot_id = ddtr.uniprot_id
        JOIN drugbank_drugs dd ON ddtr.drugbank_id = dd.drugbank_id
        WHERE ni.entrez_id = ?
        ORDER BY dd.name
    """, (entrez_id,))
    return cursor.fetchall()

def query_chembl(cursor, entrez_id, limit=50):
    """ChEMBL 화합물 정보 (pchembl_value 있는 것만)"""
    cursor.execute("""
        SELECT
            cc.chembl_id,
            cc.name,
            cc.max_phase,
            cdtr.pchembl_value,
            cdtr.standard_type,
            cdtr.standard_value,
            cdtr.standard_unit,
            cdtr.confidence_score
        FROM ncbi_info ni
        JOIN uniprot u ON ni.gene_symbol = u.gene_symbol AND ni.taxon_id = u.taxon_id
        JOIN chembl_target_uniprot_mappings ctum ON u.uniprot_id = ctum.uniprot_id
        JOIN chembl_targets ct ON ctum.target_chembl_id = ct.target_chembl_id
        JOIN chembl_drug_target_relations cdtr ON ct.target_chembl_id = cdtr.target_chembl_id
        JOIN chembl_compounds cc ON cdtr.drug_chembl_id = cc.chembl_id
        WHERE ni.entrez_id = ?
          AND cdtr.pchembl_value IS NOT NULL
        ORDER BY cdtr.pchembl_value DESC
        LIMIT ?
    """, (entrez_id, limit))
    return cursor.fetchall()

def query_kegg_pathways(cursor, entrez_id):
    """KEGG Pathway 정보"""
    cursor.execute("""
        SELECT
            kp.pathway_id,
            kp.pathway_name,
            kp.organism,
            COUNT(DISTINCT ke.edge_id) as edge_count
        FROM ncbi_info ni
        JOIN kegg_genes kg ON ni.entrez_id = kg.entrez_id
        JOIN kegg_nodes kn ON kg.gene_id = kn.node_id
        JOIN kegg_edges ke ON kn.node_id = ke.source_id OR kn.node_id = ke.target_id
        JOIN kegg_pathway kp ON ke.pathway_id = kp.pathway_id
        WHERE ni.entrez_id = ?
        GROUP BY kp.pathway_id, kp.pathway_name, kp.organism
        ORDER BY kp.organism, kp.pathway_id
    """, (entrez_id,))
    return cursor.fetchall()

def query_reactome_pathways(cursor, entrez_id):
    """Reactome Pathway 정보"""
    cursor.execute("""
        SELECT
            rp.reactome_pathway_id,
            rp.pathway_name,
            rp.organism
        FROM ncbi_info ni
        JOIN ncbi_ensembl ne ON ni.entrez_id = ne.entrez_id
        JOIN reactome_pathway_genes rpg ON ne.ensembl_id = rpg.ensembl_id
        JOIN reactome_pathway rp ON rpg.reactome_pathway_id = rp.reactome_pathway_id
        WHERE ni.entrez_id = ?
        GROUP BY rp.reactome_pathway_id, rp.pathway_name, rp.organism
        ORDER BY rp.pathway_name
    """, (entrez_id,))
    return cursor.fetchall()

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 query_by_entrez.py <entrez_id>")
        print("\nExamples:")
        print("  python3 query_by_entrez.py 2056   # EGFR")
        print("  python3 query_by_entrez.py 7157   # TP53")
        print("  python3 query_by_entrez.py 5594   # MAPK1")
        sys.exit(1)

    try:
        entrez_id = int(sys.argv[1])
    except ValueError:
        print(f"ERROR: Invalid entrez_id '{sys.argv[1]}'. Must be an integer.")
        sys.exit(1)

    if not DB_PATH.exists():
        print(f"ERROR: Database not found at {DB_PATH}")
        sys.exit(1)

    # Connect to DB
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # 0. Gene Info
    print("="*80)
    print(f"Query Results for Entrez ID: {entrez_id}")
    print("="*80)

    gene_info = query_gene_info(cursor, entrez_id)
    if not gene_info:
        print(f"\nERROR: Entrez ID {entrez_id} not found in database.")
        conn.close()
        sys.exit(1)

    entrez, symbol, species, taxon, desc = gene_info
    print(f"\nGene: {symbol} (Entrez ID: {entrez})")
    print(f"Species: {species} (Taxon: {taxon})")
    print(f"Description: {desc}")

    # 1. DrugBank
    print("\n" + "="*80)
    print("1. DrugBank Drugs")
    print("="*80)
    drugs = query_drugbank(cursor, entrez_id)
    if drugs:
        print(f"Found {len(drugs)} drug(s):\n")
        for drug in drugs:
            drugbank_id, name, dtype, groups, actions, known = drug
            print(f"  [{drugbank_id}] {name}")
            print(f"    Type: {dtype}, Groups: {groups}")
            print(f"    Actions: {actions if actions else 'N/A'}, Known Action: {known}")
            print()
    else:
        print("  No DrugBank drugs found.")

    # 2. ChEMBL
    print("="*80)
    print("2. ChEMBL Compounds (Top 50 by pChEMBL)")
    print("="*80)
    compounds = query_chembl(cursor, entrez_id, limit=50)
    if compounds:
        print(f"Found {len(compounds)} compound(s) with pChEMBL values:\n")
        for comp in compounds[:10]:  # Show top 10
            chembl_id, name, max_phase, pchembl, std_type, std_val, std_unit, conf = comp
            name_str = name if name else "N/A"
            phase_str = f"Phase {int(max_phase)}" if max_phase else "N/A"
            print(f"  [{chembl_id}] {name_str[:40]}")
            print(f"    pChEMBL: {pchembl:.2f}, {phase_str}, Confidence: {conf}")
            if std_type and std_val:
                print(f"    {std_type}: {std_val} {std_unit if std_unit else ''}")
            print()
        if len(compounds) > 10:
            print(f"  ... and {len(compounds) - 10} more compounds")
    else:
        print("  No ChEMBL compounds found with pChEMBL values.")

    # 3. KEGG Pathways
    print("\n" + "="*80)
    print("3. KEGG Pathways")
    print("="*80)
    kegg_pathways = query_kegg_pathways(cursor, entrez_id)
    if kegg_pathways:
        print(f"Found {len(kegg_pathways)} pathway(s):\n")
        for pathway in kegg_pathways:
            pid, pname, organism, edges = pathway
            print(f"  [{pid}] {pname} ({organism}, {edges} edges)")
    else:
        print("  No KEGG pathways found.")

    # 4. Reactome Pathways
    print("\n" + "="*80)
    print("4. Reactome Pathways")
    print("="*80)
    reactome_pathways = query_reactome_pathways(cursor, entrez_id)
    if reactome_pathways:
        print(f"Found {len(reactome_pathways)} pathway(s):\n")
        for pathway in reactome_pathways[:20]:  # Show first 20
            pid, pname, organism = pathway
            print(f"  [{pid}] {pname} ({organism})")
        if len(reactome_pathways) > 20:
            print(f"\n  ... and {len(reactome_pathways) - 20} more pathways")
    else:
        print("  No Reactome pathways found.")

    # Summary
    print("\n" + "="*80)
    print("Summary")
    print("="*80)
    print(f"  DrugBank drugs:     {len(drugs):>5}")
    print(f"  ChEMBL compounds:   {len(compounds):>5}")
    print(f"  KEGG pathways:      {len(kegg_pathways):>5}")
    print(f"  Reactome pathways:  {len(reactome_pathways):>5}")
    print("="*80)

    conn.close()

if __name__ == '__main__':
    main()
