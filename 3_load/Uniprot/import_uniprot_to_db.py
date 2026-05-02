#!/usr/bin/env python3
"""
Import UniProt Data to SQLite Database
=======================================
processed/Uniprot/*.csv → database.db

Usage:
    python3 import_uniprot_to_db.py
"""

import sys
import sqlite3
import pandas as pd
from pathlib import Path

# ============================================
# 설정: 여기만 수정하세요
# ============================================

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from paths import DB_FILE, PROC_UNIPROT as UNIPROT_DIR

# ============================================

print("="*60)
print("Import UniProt Data to Database")
print("="*60)

# DB 연결
print(f"\n[CONNECT] Connecting to database: {DB_FILE}")
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# Foreign keys 활성화
cursor.execute("PRAGMA foreign_keys = OFF;")  # DELETE 시 FK 체크 비활성화

# Import 순서 (FK 제약조건 고려)
IMPORT_ORDER = [
    ('uniprot_data_mouse_human.csv', 'uniprot'),
]

# ============================================
# Clear existing UniProt data
# ============================================
print(f"\n[CLEAR] Clearing existing UniProt data...")

TABLES_TO_CLEAR = [
    'uniprot',
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

print(f"\n[INFO] Data source: {UNIPROT_DIR}")
print(f"[INFO] Tables to import: {len(IMPORT_ORDER)}")

# ============================================
# Import UniProt data
# ============================================
print(f"\n[IMPORT] Importing UniProt data...")

success_count = 0
error_count = 0

for csv_file, table_name in IMPORT_ORDER:
    csv_path = UNIPROT_DIR / csv_file

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

UNIPROT_TABLES = [
    'uniprot',
]

print(f"\n[RESULT] UniProt tables in database:")
for table in UNIPROT_TABLES:
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
