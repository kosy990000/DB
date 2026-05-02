#!/usr/bin/env python3
"""
Compound Search Tool
====================
화합물 이름으로 ChEMBL, PubChem, DrugBank 정보 및 타겟 정보 검색

Usage:
    python3 search_compound.py "aspirin"
    python3 search_compound.py "ibuprofen" --limit 5
"""

import sqlite3
import json
import sys
import argparse
from pathlib import Path

# ============================================
# 설정
# ============================================
BASE_DIR = Path(__file__).resolve().parent.parent
DB_FILE = BASE_DIR / "database" / "database.db"

def search_compound(compound_name, limit=10):
    """
    화합물 이름으로 통합 검색

    Returns:
        dict: {
            'chembl': [...],
            'pubchem': [...],
            'drugbank': [...]
        }
    """
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # dict-like access
    cursor = conn.cursor()

    results = {
        'query': compound_name,
        'chembl': [],
        'pubchem': [],
        'drugbank': []
    }

    # ============================================
    # 1. ChEMBL 검색
    # ============================================
    print(f"\n{'='*60}")
    print(f"[ChEMBL] Searching for '{compound_name}'...")
    print(f"{'='*60}")

    # ChEMBL: 먼저 name으로 검색, 없으면 synonym으로 검색
    chembl_query = """
    SELECT
        c.chembl_id,
        c.name AS compound_name,
        c.max_phase,
        c.first_approval,
        c.smiles,
        c.inchi_key
    FROM chembl_compounds c
    WHERE LOWER(c.name) LIKE LOWER(?)
    LIMIT ?;
    """

    cursor.execute(chembl_query, (f'%{compound_name}%', limit))
    chembl_compounds = cursor.fetchall()

    for compound in chembl_compounds:
        chembl_id = compound['chembl_id']
        compound_data = dict(compound)

        # 타겟 정보 검색
        target_query = """
        SELECT DISTINCT
            t.target_chembl_id,
            t.target_name,
            t.target_type,
            t.species,
            dtr.standard_type,
            dtr.standard_value,
            dtr.standard_unit,
            dtr.pchembl_value
        FROM chembl_drug_target_relations dtr
        JOIN chembl_targets t ON dtr.target_chembl_id = t.target_chembl_id
        WHERE dtr.drug_chembl_id = ?
          AND dtr.pchembl_value IS NOT NULL
        ORDER BY dtr.pchembl_value DESC
        LIMIT 10;
        """

        cursor.execute(target_query, (chembl_id,))
        targets = [dict(row) for row in cursor.fetchall()]
        compound_data['targets'] = targets

        # 질병 정보 검색
        disease_query = """
        SELECT DISTINCT
            d.mesh_id,
            d.mesh_heading AS disease_name,
            ddr.max_phase
        FROM chembl_drug_disease_relations ddr
        JOIN chembl_diseases d ON ddr.mesh_id = d.mesh_id
        WHERE ddr.drug_chembl_id = ?
        ORDER BY ddr.max_phase DESC
        LIMIT 10;
        """

        cursor.execute(disease_query, (chembl_id,))
        diseases = [dict(row) for row in cursor.fetchall()]
        compound_data['diseases'] = diseases

        results['chembl'].append(compound_data)

    print(f"[OK] Found {len(results['chembl'])} ChEMBL compounds")

    # ============================================
    # 2. PubChem 검색
    # ============================================
    print(f"\n{'='*60}")
    print(f"[PubChem] Searching for '{compound_name}'...")
    print(f"{'='*60}")

    # PubChem: title만 검색 (synonym 제외로 속도 향상)
    pubchem_query = """
    SELECT
        c.cid,
        c.title AS compound_name,
        c.smiles,
        c.inchi_key
    FROM pubchem_compounds c
    WHERE LOWER(c.title) LIKE LOWER(?)
    LIMIT ?;
    """

    cursor.execute(pubchem_query, (f'%{compound_name}%', limit))
    pubchem_compounds = [dict(row) for row in cursor.fetchall()]
    results['pubchem'] = pubchem_compounds

    print(f"[OK] Found {len(results['pubchem'])} PubChem compounds")

    # ============================================
    # 3. DrugBank 검색
    # ============================================
    print(f"\n{'='*60}")
    print(f"[DrugBank] Searching for '{compound_name}'...")
    print(f"{'='*60}")

    drugbank_query = """
    SELECT
        d.drugbank_id,
        d.name AS compound_name,
        d.type AS drug_type,
        d.cas_number,
        d.groups,
        d.smiles,
        d.inchi_key,
        d.description
    FROM drugbank_drugs d
    WHERE LOWER(d.name) LIKE LOWER(?)
    LIMIT ?;
    """

    cursor.execute(drugbank_query, (f'%{compound_name}%', limit))
    drugbank_drugs = cursor.fetchall()

    for drug in drugbank_drugs:
        drugbank_id = drug['drugbank_id']
        drug_data = dict(drug)

        # 타겟 정보 검색
        target_query = """
        SELECT DISTINCT
            t.uniprot_id,
            t.gene_symbol,
            t.target_name,
            t.organism,
            dtr.actions,
            dtr.known_action
        FROM drugbank_drug_target_relations dtr
        JOIN drugbank_targets t ON dtr.uniprot_id = t.uniprot_id
        WHERE dtr.drugbank_id = ?
        LIMIT 10;
        """

        cursor.execute(target_query, (drugbank_id,))
        targets = [dict(row) for row in cursor.fetchall()]
        drug_data['targets'] = targets

        results['drugbank'].append(drug_data)

    print(f"[OK] Found {len(results['drugbank'])} DrugBank drugs")

    conn.close()

    return results


def print_results(results):
    """결과를 보기 좋게 출력"""
    print(f"\n{'='*60}")
    print(f"Search Results Summary")
    print(f"{'='*60}")
    print(f"Query: {results['query']}")
    print(f"\nChEMBL: {len(results['chembl'])} compounds")
    print(f"PubChem: {len(results['pubchem'])} compounds")
    print(f"DrugBank: {len(results['drugbank'])} drugs")

    # ChEMBL 상세 정보
    if results['chembl']:
        print(f"\n{'='*60}")
        print(f"ChEMBL Compounds")
        print(f"{'='*60}")
        for i, compound in enumerate(results['chembl'], 1):
            print(f"\n[{i}] {compound['chembl_id']} - {compound['compound_name']}")
            print(f"    Max Phase: {compound['max_phase']}")
            print(f"    First Approval: {compound['first_approval']}")
            print(f"    Targets: {len(compound['targets'])}")
            if compound['targets']:
                print(f"    Top Targets:")
                for target in compound['targets'][:3]:
                    print(f"      - {target['target_name']} (pChEMBL: {target['pchembl_value']})")
            print(f"    Diseases: {len(compound['diseases'])}")
            if compound['diseases']:
                print(f"    Top Diseases:")
                for disease in compound['diseases'][:3]:
                    print(f"      - {disease['disease_name']} (Phase: {disease['max_phase']})")

    # DrugBank 상세 정보
    if results['drugbank']:
        print(f"\n{'='*60}")
        print(f"DrugBank Drugs")
        print(f"{'='*60}")
        for i, drug in enumerate(results['drugbank'], 1):
            print(f"\n[{i}] {drug['drugbank_id']} - {drug['compound_name']}")
            print(f"    Type: {drug['drug_type']}")
            print(f"    Groups: {drug['groups']}")
            print(f"    Targets: {len(drug['targets'])}")
            if drug['targets']:
                print(f"    Top Targets:")
                for target in drug['targets'][:3]:
                    print(f"      - {target['gene_symbol']} ({target['target_name']})")

    # PubChem (간략)
    if results['pubchem']:
        print(f"\n{'='*60}")
        print(f"PubChem Compounds")
        print(f"{'='*60}")
        for i, compound in enumerate(results['pubchem'][:5], 1):
            print(f"[{i}] CID:{compound['cid']} - {compound['compound_name']}")


def main():
    parser = argparse.ArgumentParser(
        description='Search compounds by name in ChEMBL, PubChem, and DrugBank',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 search_compound.py "aspirin"
  python3 search_compound.py "ibuprofen" --limit 5
  python3 search_compound.py "metformin" --output result.json
        """
    )
    parser.add_argument('compound_name', help='Compound name to search')
    parser.add_argument('--limit', type=int, default=10, help='Max results per database (default: 10)')
    parser.add_argument('--output', '-o', help='Output JSON file path')

    args = parser.parse_args()

    # 검색 실행
    results = search_compound(args.compound_name, args.limit)

    # 결과 출력
    print_results(results)

    # JSON 저장
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n[OK] Results saved to: {args.output}")

    print(f"\n{'='*60}")
    print(f"[DONE] Search completed!")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
