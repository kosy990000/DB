#!/usr/bin/env python3
"""
ChEMBL Data Loading Script
"""

import sqlite3
import pandas as pd
from pathlib import Path
import sys


def load_compounds(conn, csv_path):
    """Load compounds from CSV"""
    print(f"\n1. Loading compounds...")

    df = pd.read_csv(csv_path)
    print(f"   Read {len(df):,} rows")

    cursor = conn.cursor()
    inserted = 0

    for _, row in df.iterrows():
        try:
            cursor.execute("""
                INSERT INTO compounds (chembl_id, name, max_phase, first_approval, smiles, inchi_key)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                row['chembl_id'],
                row['name'] if pd.notna(row['name']) else None,
                int(row['max_phase']) if pd.notna(row['max_phase']) else None,
                int(row['first_approval']) if pd.notna(row['first_approval']) else None,
                row['smiles'] if pd.notna(row['smiles']) else None,
                row['inchi_key'] if pd.notna(row['inchi_key']) else None
            ))
            inserted += 1

            if inserted % 100000 == 0:
                print(f"   {inserted:,} compounds...")
                conn.commit()

        except sqlite3.IntegrityError:
            pass

    conn.commit()
    print(f"   ✓ Inserted {inserted:,} compounds")


def load_targets(conn, csv_path):
    """Load targets from CSV"""
    print(f"\n2. Loading targets...")

    df = pd.read_csv(csv_path)
    print(f"   Read {len(df):,} rows")

    cursor = conn.cursor()
    inserted = 0

    for _, row in df.iterrows():
        try:
            cursor.execute("""
                INSERT INTO targets (chembl_target_id, target_name, target_type, organism)
                VALUES (?, ?, ?, ?)
            """, (
                row['target_chembl_id'],
                row['target_name'] if pd.notna(row['target_name']) else None,
                row['target_type'] if pd.notna(row['target_type']) else None,
                row['species'] if pd.notna(row['species']) else None
            ))
            inserted += 1

        except sqlite3.IntegrityError:
            pass

    conn.commit()
    print(f"   ✓ Inserted {inserted:,} targets")


def load_diseases(conn, csv_path):
    """Load diseases from CSV"""
    print(f"\n3. Loading diseases...")

    df = pd.read_csv(csv_path)
    print(f"   Read {len(df):,} rows")

    cursor = conn.cursor()
    inserted = 0

    for _, row in df.iterrows():
        try:
            cursor.execute("""
                INSERT INTO diseases (mesh_id, mesh_heading, efo_id, efo_term)
                VALUES (?, ?, ?, ?)
            """, (
                row['mesh_id'],
                row['mesh_heading'] if pd.notna(row['mesh_heading']) else None,
                row['efo_id'] if pd.notna(row['efo_id']) else None,
                row['efo_term'] if pd.notna(row['efo_term']) else None
            ))
            inserted += 1

        except sqlite3.IntegrityError:
            pass

    conn.commit()
    print(f"   ✓ Inserted {inserted:,} diseases")


def load_compound_disease(conn, csv_path):
    """Load compound-disease relationships"""
    print(f"\n4. Loading compound-disease relationships...")

    df = pd.read_csv(csv_path)
    print(f"   Read {len(df):,} rows")

    cursor = conn.cursor()
    inserted = 0

    for _, row in df.iterrows():
        cursor.execute("SELECT compound_id FROM compounds WHERE chembl_id = ?", (row['drug_chembl_id'],))
        compound_result = cursor.fetchone()
        if not compound_result:
            continue
        compound_id = compound_result[0]

        cursor.execute("SELECT disease_id FROM diseases WHERE mesh_id = ?", (row['mesh_id'],))
        disease_result = cursor.fetchone()
        if not disease_result:
            continue
        disease_id = disease_result[0]

        try:
            cursor.execute("""
                INSERT INTO compound_disease (compound_id, disease_id, max_phase)
                VALUES (?, ?, ?)
            """, (
                compound_id,
                disease_id,
                int(row['max_phase']) if pd.notna(row['max_phase']) else None
            ))
            inserted += 1

        except sqlite3.IntegrityError:
            pass

    conn.commit()
    print(f"   ✓ Inserted {inserted:,} relationships")


def load_compound_target(conn, csv_path):
    """Load compound-target bioactivity"""
    print(f"\n5. Loading compound-target bioactivity...")
    print(f"   WARNING: Large file (7GB+), may take 30+ minutes")

    chunk_size = 100000
    inserted = 0
    cursor = conn.cursor()

    for chunk_num, df_chunk in enumerate(pd.read_csv(csv_path, chunksize=chunk_size), 1):
        print(f"   Chunk {chunk_num} ({len(df_chunk):,} rows)...")

        for _, row in df_chunk.iterrows():
            cursor.execute("SELECT compound_id FROM compounds WHERE chembl_id = ?", (row['drug_chembl_id'],))
            compound_result = cursor.fetchone()
            if not compound_result:
                continue
            compound_id = compound_result[0]

            cursor.execute("SELECT target_id FROM targets WHERE chembl_target_id = ?", (row['target_chembl_id'],))
            target_result = cursor.fetchone()

            if not target_result:
                # Skip if target not found (should load targets first)
                continue

            target_id = target_result[0]

            try:
                cursor.execute("""
                    INSERT INTO compound_target (
                        compound_id, target_id,
                        standard_type, standard_relation, standard_value, standard_units,
                        pchembl_value, confidence_score, assay_description
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    compound_id,
                    target_id,
                    row['standard_type'] if pd.notna(row['standard_type']) else None,
                    row['standard_relation'] if pd.notna(row['standard_relation']) else None,
                    float(row['standard_value']) if pd.notna(row['standard_value']) else None,
                    row['standard_units'] if pd.notna(row['standard_units']) else None,
                    float(row['pchembl_value']) if pd.notna(row['pchembl_value']) else None,
                    int(row['confidence_score']) if pd.notna(row['confidence_score']) else None,
                    row['assay_description'] if pd.notna(row['assay_description']) else None
                ))
                inserted += 1

            except sqlite3.IntegrityError:
                pass

        conn.commit()
        print(f"   Total: {inserted:,}")

    print(f"   ✓ Inserted {inserted:,} bioactivity records")


def load_synonyms(conn, compound_syn_path, target_syn_path):
    """Load synonyms"""
    print(f"\n6. Loading synonyms...")

    cursor = conn.cursor()
    inserted = 0

    print(f"   Compound synonyms...")
    df_comp_syn = pd.read_csv(compound_syn_path)

    for _, row in df_comp_syn.iterrows():
        cursor.execute("SELECT compound_id FROM compounds WHERE chembl_id = ?", (row['chembl_id'],))
        result = cursor.fetchone()
        if not result:
            continue

        try:
            cursor.execute("""
                INSERT INTO synonyms (entity_type, entity_id, synonym, synonym_type)
                VALUES (?, ?, ?, ?)
            """, (
                'compound',
                result[0],
                row['synonym'] if pd.notna(row['synonym']) else None,
                row['synonym_type'] if pd.notna(row['synonym_type']) else None
            ))
            inserted += 1

        except sqlite3.IntegrityError:
            pass

    conn.commit()

    print(f"   Target synonyms...")
    df_target_syn = pd.read_csv(target_syn_path)

    for _, row in df_target_syn.iterrows():
        cursor.execute("SELECT target_id FROM targets WHERE chembl_target_id = ?", (row['target_chembl_id'],))
        result = cursor.fetchone()
        if not result:
            continue

        try:
            cursor.execute("""
                INSERT INTO synonyms (entity_type, entity_id, synonym, synonym_type)
                VALUES (?, ?, ?, ?)
            """, (
                'target',
                result[0],
                row['synonym'] if pd.notna(row['synonym']) else None,
                row['synonym_type'] if pd.notna(row['synonym_type']) else None
            ))
            inserted += 1

        except sqlite3.IntegrityError:
            pass

    conn.commit()
    print(f"   ✓ Inserted {inserted:,} synonyms")


def main():
    print("="*70)
    print("ChEMBL Data Loading")
    print("="*70)

    SCRIPT_DIR = Path(__file__).parent
    DB_ROOT = SCRIPT_DIR.parent
    DB_DIR = DB_ROOT / "database"
    DB_PATH = DB_DIR / "chembl.db"
    DATA_DIR = DB_ROOT / "processed" / "Chembl"

    if not DB_PATH.exists():
        print(f"\n❌ Database not found: {DB_PATH}")
        print(f"   Run 'create_chembl_schema.py' first")
        sys.exit(1)

    print(f"\nDatabase: {DB_PATH}")
    print(f"Data: {DATA_DIR}\n")

    # CSV paths
    compounds_csv = DATA_DIR / "compound" / "compounds.csv"
    targets_csv = DATA_DIR / "target" / "targets.csv"
    diseases_csv = DATA_DIR / "disease" / "disease.csv"
    compound_disease_csv = DATA_DIR / "compound-disease" / "compound-disease_information.csv"
    compound_target_csv = DATA_DIR / "compound-target" / "compound-target_information.csv"
    compound_syn_csv = DATA_DIR / "compound" / "compound_synonyms.csv"
    target_syn_csv = DATA_DIR / "target" / "target_synonyms.csv"

    conn = sqlite3.connect(DB_PATH)

    try:
        load_compounds(conn, compounds_csv)
        load_targets(conn, targets_csv)
        load_diseases(conn, diseases_csv)
        load_compound_disease(conn, compound_disease_csv)

        # Ask for compound-target (large file)
        if compound_target_csv.exists():
            response = input("\nLoad compound-target data (7GB+, ~30min)? [y/N]: ")
            if response.lower() == 'y':
                load_compound_target(conn, compound_target_csv)
            else:
                print("   Skipped")

        load_synonyms(conn, compound_syn_csv, target_syn_csv)

        print("\n" + "="*70)
        print("✓ Complete!")
        print("="*70)

        cursor = conn.cursor()
        print("\nStatistics:")

        cursor.execute("SELECT COUNT(*) FROM compounds")
        print(f"  Compounds: {cursor.fetchone()[0]:,}")

        cursor.execute("SELECT COUNT(*) FROM targets")
        print(f"  Targets: {cursor.fetchone()[0]:,}")

        cursor.execute("SELECT COUNT(*) FROM diseases")
        print(f"  Diseases: {cursor.fetchone()[0]:,}")

        cursor.execute("SELECT COUNT(*) FROM compound_disease")
        print(f"  Compound-Disease: {cursor.fetchone()[0]:,}")

        cursor.execute("SELECT COUNT(*) FROM compound_target")
        print(f"  Compound-Target: {cursor.fetchone()[0]:,}")

        cursor.execute("SELECT COUNT(*) FROM synonyms")
        print(f"  Synonyms: {cursor.fetchone()[0]:,}")

        print("="*70)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()

    finally:
        conn.close()


if __name__ == "__main__":
    main()
