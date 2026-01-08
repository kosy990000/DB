#!/usr/bin/env python3
"""
Import Reactome Data to SQLite Database
========================================
processed/Reactome/*.csv → database.db

Usage:
    python3 import_reactome_to_db.py
"""

import sqlite3
import pandas as pd
from pathlib import Path

# ============================================
# 설정: 여기만 수정하세요
# ============================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# 데이터 경로
REACTOME_DIR = BASE_DIR / "processed" / "Reactome"

# DB 파일 경로
DB_FILE = BASE_DIR / "database" / "database.db"

# ============================================

print("="*60)
print("Import Reactome Data to Database")
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
    ('all_pathway.csv', 'reactome_pathway'),

    # 2. 자식 테이블 (FK 참조)
    ('all_pathway_genes.csv', 'reactome_pathway_genes'),
]

# ============================================
# Clear existing Reactome data
# ============================================
print(f"\n[CLEAR] Clearing existing Reactome data...")

TABLES_TO_CLEAR = [
    'reactome_pathway_genes',
    'reactome_pathway',
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

print(f"\n[INFO] Data source: {REACTOME_DIR}")
print(f"[INFO] Tables to import: {len(IMPORT_ORDER)}")

# ============================================
# Import Reactome data
# ============================================
print(f"\n[IMPORT] Importing Reactome data...")

success_count = 0
error_count = 0

for csv_file, table_name in IMPORT_ORDER:
    csv_path = REACTOME_DIR / csv_file

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

REACTOME_TABLES = [
    'reactome_pathway',
    'reactome_pathway_genes',
]

print(f"\n[RESULT] Reactome tables in database:")
for table in REACTOME_TABLES:
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
