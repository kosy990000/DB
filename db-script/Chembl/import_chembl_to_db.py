#!/usr/bin/env python3
"""
Import ChEMBL Data to SQLite Database
======================================
processed/Chembl/*.csv → database.db

Usage:
    python3 import_chembl_to_db.py
"""

import sqlite3
import pandas as pd
from pathlib import Path
from tqdm import tqdm

# ============================================
# 설정: 여기만 수정하세요
# ============================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# 데이터 경로
CHEMBL_DIR = BASE_DIR / "processed" / "Chembl"

# DB 파일 경로
DB_FILE = BASE_DIR / "database" / "database.db"

# ============================================

print("="*60)
print("Import ChEMBL Data to Database")
print("="*60)

# DB 연결
print(f"\n[CONNECT] Connecting to database: {DB_FILE}")
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# Foreign keys 활성화
cursor.execute("PRAGMA foreign_keys = OFF;")  # DELETE 시 FK 체크 비활성화

# Import 순서 (FK 제약조건 고려)
IMPORT_ORDER = [
    # 1. 부모 테이블 (FK 없음)
    ('compound/compounds.csv', 'chembl_compounds'),
    ('target/targets.csv', 'chembl_targets'),
    ('disease/disease.csv', 'chembl_diseases'),

    # 2. 자식 테이블 (FK 참조)
    ('compound/compound_synonyms.csv', 'chembl_synonyms'),
    ('target/target_uniprot_mappings.csv', 'chembl_target_uniprot_mappings'),
    ('target/target_synonyms.csv', 'chembl_target_synonyms'),
    ('compound-disease/compound-disease_information.csv', 'chembl_drug_disease_relations'),
    ('compound-target/compound-target_information.csv', 'chembl_drug_target_relations'),
]

# ============================================
# Clear existing ChEMBL data
# ============================================
print(f"\n[CLEAR] Clearing existing ChEMBL data...")

TABLES_TO_CLEAR = [
    'chembl_drug_target_relations',
    'chembl_drug_disease_relations',
    'chembl_target_synonyms',
    'chembl_target_uniprot_mappings',
    'chembl_synonyms',
    'chembl_diseases',
    'chembl_targets',
    'chembl_compounds',
]

for table in TABLES_TO_CLEAR:
    try:
        cursor.execute(f"DELETE FROM {table};")
        deleted = cursor.rowcount
        if deleted > 0:
            print(f"  [OK] Cleared {table}: {deleted:,} rows deleted")
    except sqlite3.OperationalError:
        # 테이블이 없는 경우 (첫 실행)
        print(f"  [WARN] Table {table} does not exist (will be created)")

conn.commit()
cursor.execute("PRAGMA foreign_keys = ON;")  # FK 체크 재활성화

print(f"\n[INFO] Data source: {CHEMBL_DIR}")
print(f"[INFO] Tables to import: {len(IMPORT_ORDER)}")

# ============================================
# Import ChEMBL data
# ============================================
print(f"\n[IMPORT] Importing ChEMBL data...")

success_count = 0
error_count = 0

for csv_file, table_name in IMPORT_ORDER:
    csv_path = CHEMBL_DIR / csv_file

    if not csv_path.exists():
        print(f"\n  [WARN] File not found: {csv_file} (skipped)")
        error_count += 1
        continue

    print(f"\n  [IMPORT] {csv_file} -> {table_name}")

    try:
        # CSV 읽기
        df = pd.read_csv(csv_path, low_memory=False)
        print(f"     Rows: {len(df):,}")

        # 칼럼명 정리
        df.columns = df.columns.str.replace(' ', '_').str.replace('-', '_').str.lower()

        # standard_units → standard_unit (chembl_drug_target_relations)
        if 'standard_units' in df.columns:
            df.rename(columns={'standard_units': 'standard_unit'}, inplace=True)

        # DB에 insert
        df.to_sql(table_name, conn, if_exists='append', index=False)
        print(f"     [OK] Imported successfully")
        success_count += 1

    except Exception as e:
        print(f"     [ERROR] {e}")
        error_count += 1
        conn.rollback()

conn.commit()

# ============================================
# Verify import
# ============================================
print(f"\n[VERIFY] Verifying import...")

CHEMBL_TABLES = [
    'chembl_compounds',
    'chembl_targets',
    'chembl_diseases',
    'chembl_synonyms',
    'chembl_target_synonyms',
    'chembl_drug_disease_relations',
    'chembl_drug_target_relations',
]

print(f"\n[RESULT] ChEMBL tables in database:")
for table in CHEMBL_TABLES:
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table};")
        count = cursor.fetchone()[0]
        print(f"  - {table:40s} : {count:,} rows")
    except sqlite3.Error:
        print(f"  - {table:40s} : (table not found)")

conn.close()

# ============================================
# Summary
# ============================================
print("\n" + "="*60)
print("Import Summary")
print("="*60)
print(f"[OK] Successfully imported: {success_count} tables")
if error_count > 0:
    print(f"[ERROR] Failed: {error_count} tables")
print("\n" + "="*60)
print("[DONE] Import completed!")
print("="*60)
print(f"\nDatabase: {DB_FILE}")
